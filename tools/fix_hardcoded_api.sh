#!/usr/bin/env bash
set -euo pipefail

APPLY=0
ROOT="ow-ai-dashboard/src"

# args: [path] [--apply]
if [[ "${1:-}" != "" && "${1:-}" != "--apply" ]]; then
  ROOT="$1"
fi
if [[ "${1:-}" == "--apply" || "${2:-}" == "--apply" ]]; then
  APPLY=1
fi

if [[ ! -d "$ROOT" && ! -f "$ROOT" ]]; then
  echo "❌ Path not found: $ROOT"
  echo "Usage: $0 [path_to_src_or_file] [--apply]"
  exit 1
fi

echo "🔎 Scanning: $ROOT"
echo "    (js/jsx/ts/tsx only; backups/temp excluded)"
echo

# Build file list (null-delimited for safety)
if [[ -d "$ROOT" ]]; then
  FILES_CMD=(find "$ROOT" \
    -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/dist/*" \
    -not -path "*/build/*" \
    -not -name "*.bak" \
    -not -name "*.backup*" \
    -not -name "*duplicate_backup*" \
    -not -name "*localStorage-backup*" \
    -print0)
else
  FILES_CMD=(printf "%s\0" "$ROOT")
fi

PATTERN_REGEX='https?://(owai-production\.up\.railway\.app|localhost:8000)'
CANDIDATES=()
while IFS= read -r -d '' f; do
  if grep -qE "$PATTERN_REGEX" "$f"; then
    CANDIDATES+=("$f")
  fi
done < <("${FILES_CMD[@]}")

if [[ ${#CANDIDATES[@]} -eq 0 ]]; then
  echo "✅ No hardcoded API bases found in live code."
  exit 0
fi

echo "⚠️  Found ${#CANDIDATES[@]} file(s) with hardcoded API base(s):"
printf ' - %s\n' "${CANDIDATES[@]}"
echo

fix_file () {
  local file="$1"
  local tmp="${file}.tmp.__fix__"
  cp "$file" "$tmp"

  # 1) Replace simple fallbacks like: import.meta.env.VITE_API_URL || "https://..."
  #    Use [|][|] to match literal pipes on BSD sed
  sed -E -i '' \
    -e "s@(import\.meta\.env\.VITE_API_URL[[:space:]]*[|][|][[:space:]]*)'https?://[^']+'@\\1window.location.origin@g" \
    -e "s@(import\.meta\.env\.VITE_API_URL[[:space:]]*[|][|][[:space:]]*)\"https?://[^\"]+\"@\\1window.location.origin@g" \
    "$tmp"

  # 2) Normalize const API_BASE_URL definitions (single/double quotes or localhost)
  sed -E -i '' \
    -e "s@const API_BASE_URL[[:space:]]*=[[:space:]]*import\.meta\.env\.VITE_API_URL[[:space:]]*[|][|][[:space:]]*'https?://[^']+';@const API_BASE_URL = (import.meta?.env?.VITE_API_URL && import.meta.env.VITE_API_URL.trim()) || window.location.origin;@g" \
    -e "s@const API_BASE_URL[[:space:]]*=[[:space:]]*import\.meta\.env\.VITE_API_URL[[:space:]]*[|][|][[:space:]]*\"https?://[^\"]+\";@const API_BASE_URL = (import.meta?.env?.VITE_API_URL && import.meta.env.VITE_API_URL.trim()) || window.location.origin;@g" \
    -e "s@const API_BASE_URL[[:space:]]*=[[:space:]]*import\.meta\.env\.VITE_API_URL[[:space:]]*[|][|][[:space:]]*'http://localhost:8000';@const API_BASE_URL = (import.meta?.env?.VITE_API_URL && import.meta.env.VITE_API_URL.trim()) || window.location.origin;@g" \
    -e "s@const API_BASE_URL[[:space:]]*=[[:space:]]*import\.meta\.env\.VITE_API_URL[[:space:]]*[|][|][[:space:]]*\"http://localhost:8000\";@const API_BASE_URL = (import.meta?.env?.VITE_API_URL && import.meta.env.VITE_API_URL.trim()) || window.location.origin;@g" \
    "$tmp"

  # 3) Template-string fallbacks: `${ import.meta.env.VITE_API_URL || "https://..." }`
  sed -E -i '' \
    -e "s@\`\$\{import\.meta\.env\.VITE_API_URL[[:space:]]*[|][|][[:space:]]*'https?://[^']+'\}\`@\`\${import.meta.env.VITE_API_URL || window.location.origin}\`@g" \
    -e "s@\`\$\{import\.meta\.env\.VITE_API_URL[[:space:]]*[|][|][[:space:]]*\"https?://[^\"]+\"\}\`@\`\${import.meta.env.VITE_API_URL || window.location.origin}\`@g" \
    "$tmp"

  if [[ $APPLY -eq 1 ]]; then
    if ! cmp -s "$file" "$tmp"; then
      echo "✍️  Applying fix to: $file"
      mv "$tmp" "$file"
    else
      rm "$tmp"
    fi
  else
    if ! cmp -s "$file" "$tmp"; then
      echo "——— DIFF: $file ———"
      if command -v git >/dev/null 2>&1; then
        git --no-pager diff --no-index -- "$file" "$tmp" || true
      else
        diff -u "$file" "$tmp" || true
      fi
    fi
    rm "$tmp"
  fi
}

for f in "${CANDIDATES[@]}"; do
  fix_file "$f"
done

if [[ $APPLY -eq 1 ]]; then
  echo
  echo "✅ Done. Hardcoded API bases replaced with enterprise-safe fallback."
else
  echo
  echo "🔐 Dry-run complete. Re-run with '--apply' to write changes:"
  echo "   $0 ${ROOT} --apply"
fi
