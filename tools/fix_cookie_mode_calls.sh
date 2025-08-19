#!/usr/bin/env bash
set -euo pipefail

# fix_cookie_mode_calls.sh – enterprise-safe, targeted cookie-mode fix
# - ONLY rewrites: fetch(`${API_BASE_URL}...`) -> fetchWithAuth(`...`)
# - Removes inline Authorization & getAuthHeaders() usage
# - Cleans empty headers
# - Adds import { fetchWithAuth } ... ONLY if a replacement happened
# - Dry-run by default; use --apply to write changes

ROOT="${1:-}"
APPLY=0
[[ "${2:-}" == "--apply" ]] && APPLY=1

if [[ -z "$ROOT" || ! -d "$ROOT" ]]; then
  echo "❌ Usage: $0 <SRC_DIR> [--apply]" >&2
  exit 1
fi

inplace_sed() {
  local file="$1"; shift
  local sedbin="sed"
  command -v gsed >/dev/null 2>&1 && sedbin="gsed"

  local args=()
  for expr in "$@"; do args+=(-e "$expr"); done

  if [[ "$sedbin" == "gsed" ]]; then
    "$sedbin" -i -E "${args[@]}" "$file"
  else
    "$sedbin" -i '' -E "${args[@]}" "$file"
  fi
}

readarray_candidates() {
  # js/ts/jsx/tsx only; exclude backups/temp; EXCLUDE the helper itself
  find "$ROOT" -type f \( -name '*.js' -o -name '*.jsx' -o -name '*.ts' -o -name '*.tsx' \) \
    | grep -Ev '(backup|duplicate|\.bak|\.tmp|localStorage-backup|\.swp|\.orig|\.rej|\.tmp\.__fix__)' \
    | grep -Ev '/src/utils/fetchWithAuth\.js$'
}

CANDIDATES=()
while IFS= read -r f; do CANDIDATES+=("$f"); done < <(readarray_candidates)

echo "🔎 Scanning: $ROOT"
echo "    (js/jsx/ts/tsx only; backups/temp excluded)"
echo

TOUCH_FILES=()
AMBIGUOUS=()

for f in "${CANDIDATES[@]}"; do
  if grep -q '\${API_BASE_URL}' "$f"; then
    TOUCH_FILES+=("$f"); continue
  fi
  if grep -Eq 'Authorization[[:space:]]*:' "$f" || grep -Eq 'getAuthHeaders\(' "$f"; then
    TOUCH_FILES+=("$f"); continue
  fi
done

if [[ ${#TOUCH_FILES[@]} -eq 0 ]]; then
  echo "✅ Nothing to change."
  exit 0
fi

echo "⚠️  Candidate file(s) to examine:"
printf ' - %s\n' "${TOUCH_FILES[@]}"
echo

fix_file() {
  local file="$1"
  local tmp
  tmp="$(mktemp -t fix_cookie_mode.XXXXXX)"
  cp "$file" "$tmp"

  # Track replacements to decide whether to add import
  local before after replaced=0

  # Count occurrences of fetch(`${API_BASE_URL}
  before="$(grep -o '\`\\?${API_BASE_URL}' "$tmp" || true)"
  local before_cnt=0
  [[ -n "$before" ]] && before_cnt=$(printf "%s\n" "$before" | wc -l | tr -d ' ')

  # 1) fetch(`${API_BASE_URL}...`) → fetchWithAuth(`...`)
  # Keep whitespace after 'fetch' and the remaining template literal.
  local expr_fetch="s|fetch(([[:space:]]*))\`\\\$\\\{API_BASE_URL\\\}|fetchWithAuth\\1\`|g"

  # 2) Remove inline Authorization header usage & getAuthHeaders spreads/calls
  local expr_auth="s|[,{][[:space:]]*[\"']?Authorization[\"']?[[:space:]]*:[[:space:]]*\`?Bearer[^,}]*,?[[:space:]]*||g"
  local expr_spread="s|\\.\\.\\.[[:space:]]*getAuthHeaders\\(\\)[[:space:]]*,?[[:space:]]*||g"
  local expr_headers_call="s|headers[[:space:]]*:[[:space:]]*getAuthHeaders\\(\\)[[:space:]]*,?[[:space:]]*| |g"

  inplace_sed "$tmp" "$expr_fetch" "$expr_auth" "$expr_spread" "$expr_headers_call"

  # Recount for replacements
  after="$(grep -o '\`\\?${API_BASE_URL}' "$tmp" || true)"
  local after_cnt=0
  [[ -n "$after" ]] && after_cnt=$(printf "%s\n" "$after" | wc -l | tr -d ' ')
  if (( after_cnt < before_cnt )); then replaced=1; fi

  # 3) Clean up empty headers objects and dangling commas safely
  #    - headers: { } or headers:{}
  #    - , headers: { } ,
  #    - Ensure we don't break surrounding JSON-ish objects
  local expr_empty_headers1="s|headers[[:space:]]*:[[:space:]]*\\{[[:space:]]*\\}[[:space:]]*,[[:space:]]*| |g"
  local expr_empty_headers2="s|,[[:space:]]*headers[[:space:]]*:[[:space:]]*\\{[[:space:]]*\\}[[:space:]]*| |g"
  local expr_empty_headers3="s|headers[[:space:]]*:[[:space:]]*\\{[[:space:]]*\\}[[:space:]]*| |g"
  # Tidy redundant { , , } patterns possibly introduced (double commas)
  local expr_double_comma="s|,[[:space:]]*,|,|g"

  inplace_sed "$tmp" "$expr_empty_headers1" "$expr_empty_headers2" "$expr_empty_headers3" "$expr_double_comma"

  # 4) If we see fetch(variableUrl, { headers: getAuthHeaders() ... }) leave unchanged (ambiguous)
  if grep -Eq 'fetch\(\s*[a-zA-Z0-9_.$]+\s*,\s*\{[^}]*getAuthHeaders\(' "$tmp"; then
    AMBIGUOUS+=("$file")
    cp "$file" "$tmp"  # revert
    replaced=0
  fi

  # 5) Insert import if a fetch->fetchWithAuth replacement happened AND no existing import
  if (( replaced == 1 )) && \
     ! grep -q "from '../utils/fetchWithAuth'" "$tmp" && \
     ! grep -q "from \"../utils/fetchWithAuth\"" "$tmp" && \
     ! grep -q "from './utils/fetchWithAuth'" "$tmp" && \
     ! grep -q "from \"./utils/fetchWithAuth\"" "$tmp"; then

    local import_line
    if [[ "$file" == *"/components/"* || "$file" == *"/pages/"* ]]; then
      import_line="import { fetchWithAuth } from '../utils/fetchWithAuth';"
    else
      import_line="import { fetchWithAuth } from './utils/fetchWithAuth';"
    fi

    if grep -q '^import ' "$tmp"; then
      awk -v imp="$import_line" '
        BEGIN{added=0}
        NR==1{
          if ($0 ~ /^import /) {print; next}
          else {print imp; print; added=1; next}
        }
        NR>1 && added==0{
          if ($0 ~ /^import /) {print; next}
          else {print imp; print; added=1; next}
        }
        {print}
      ' "$tmp" > "${tmp}.imp" && mv "${tmp}.imp" "$tmp"
    else
      (echo "$import_line"; cat "$tmp") > "${tmp}.imp" && mv "${tmp}.imp" "$tmp"
    fi
  fi

  # 6) Show diff (dry-run) or apply
  if ! cmp -s "$file" "$tmp"; then
    if [[ $APPLY -eq 1 ]]; then
      echo "✍️  Applying fix to: $file"
      cp "$tmp" "$file"
    else
      echo "——— DIFF: $file ———"
      if command -v git >/dev/null 2>&1; then
        git --no-pager diff --no-index -- "$file" "$tmp" || true
      else
        diff -u "$file" "$tmp" || true
      fi
    fi
  fi

  rm -f "$tmp"
}

for f in "${TOUCH_FILES[@]}"; do
  fix_file "$f"
done

if [[ ${#AMBIGUOUS[@]} -gt 0 ]]; then
  echo
  echo "🤔 Ambiguous (left unchanged; review manually):"
  printf ' - %s\n' "${AMBIGUOUS[@]}"
  echo "   Pattern: fetch(variableUrl, { headers: getAuthHeaders() ... })"
fi

echo
if [[ $APPLY -eq 1 ]]; then
  echo "✅ Done. All safe transformations applied."
else
  echo "🔐 Dry-run complete. Re-run with '--apply' to write changes:"
  echo "   $0 ${ROOT} --apply"
fi
