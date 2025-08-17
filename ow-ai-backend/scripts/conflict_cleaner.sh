#!/usr/bin/env bash
set -euo pipefail

# Safely remove Git conflict markers from one or more files without changing other code.
# Usage examples:
#   ./scripts/conflict_cleaner.sh --prefer ours ow-ai-backend/main.py
#   ./scripts/conflict_cleaner.sh --prefer theirs ow-ai-backend/main.py
#   ./scripts/conflict_cleaner.sh --ask ow-ai-backend/main.py
#   ./scripts/conflict_cleaner.sh --dry-run ow-ai-backend/main.py
#   ./scripts/conflict_cleaner.sh --list ow-ai-backend/main.py
#   ./scripts/conflict_cleaner.sh --branch fix-conflicts ow-ai-backend/main.py

PREFER="ours"      # ours|theirs|ask
DRY_RUN="false"
LIST_ONLY="false"
BRANCH=""
FILES=()

err() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "• $*"; }
ts() { date +"%Y%m%d-%H%M%S"; }

while (( "$#" )); do
  case "${1:-}" in
    --prefer) shift; PREFER="${1:-}"; [[ "$PREFER" =~ ^(ours|theirs|ask)$ ]] || err "--prefer must be ours|theirs|ask";;
    --ask) PREFER="ask";;
    --dry-run) DRY_RUN="true";;
    --list) LIST_ONLY="true";;
    --branch) shift; BRANCH="${1:-}";;
    -h|--help) cat <<'H'; exit 0
Safely remove Git conflict markers without changing other code.
Options:
  --prefer ours|theirs   Choose which side to keep globally (default: ours)
  --ask                  Interactive per-hunk choice
  --dry-run              Show what would change; do not write
  --list                 List conflict hunks only; do not write
  --branch <name>        Create/switch to a git branch before changes
H
      ;;
    --) shift; break;;
    -* ) err "Unknown option: $1";;
    *  ) FILES+=("$1");;
  esac
  shift
done

[[ ${#FILES[@]} -gt 0 ]] || err "Provide at least one file, e.g. ow-ai-backend/main.py"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || err "Run inside a Git repo."

if [[ -n "$BRANCH" ]]; then
  info "Creating/switching to branch: $BRANCH"
  git checkout -B "$BRANCH"
fi

wip_commit_made="false"
if ! git diff --quiet || ! git diff --cached --quiet; then
  info "Saving WIP changes"
  git add -A
  git commit -m "WIP before conflict cleaning $(ts)" || true
  wip_commit_made="true"
fi

command -v python >/dev/null 2>&1 || err "python not found"

list_hunks() {
  local f="$1"
  local line_no=0 state="copy" ours="" theirs=""
  while IFS='' read -r line || [[ -n "$line" ]]; do
    line_no=$((line_no+1))
    if [[ "$state" == "copy" && "$line" =~ ^<<<<<<<\  ]]; then
      echo "[$f] conflict starts at line $line_no"
      state="in_ours"; ours=""; theirs=""
      continue
    fi
    if [[ "$state" == "in_ours" && "$line" == "=======" ]]; then
      state="in_theirs"; continue
    fi
    if [[ "$state" == "in_ours" ]]; then ours+="$line"$'\n'; continue; fi
    if [[ "$state" == "in_theirs" && "$line" =~ ^>>>>>>> ]]; then
      echo "---- OURS ----"
      printf "%s" "$ours"
      echo "---- THEIRS ----"
      printf "%s" "$theirs"
      echo "---- END CONFLICT ----"
      state="copy"; continue
    fi
    if [[ "$state" == "in_theirs" ]]; then theirs+="$line"$'\n'; continue; fi
  done < "$f"
}

clean_file() {
  local f="$1"
  [[ -f "$f" ]] || err "$f not found"

  if ! grep -qE '^(<<<<<<<|=======|>>>>>>>)' "$f"; then
    info "$f: no conflict markers detected"
    return 0
  fi

  if [[ "$LIST_ONLY" == "true" ]]; then
    list_hunks "$f"
    return 0
  fi

  local backup="backups/$(basename "$f").$(ts).bak"
  mkdir -p backups
  cp "$f" "$backup"
  info "$f: backup saved to $backup"

  if [[ "$PREFER" != "ask" ]]; then
    awk -v prefer="$PREFER" '
      BEGIN { state=0 }
      /^<<<<<<< / { state=1; ours=""; theirs=""; next }
      state==1 && /^=======/ { state=3; next }
      state==1 { ours = ours $0 ORS; next }
      state==3 && /^>>>>>>> / {
        if (prefer=="ours")      printf "%s", ours;
        else if (prefer=="theirs") printf "%s", theirs;
        state=0; next
      }
      state==3 { theirs = theirs $0 ORS; next }
      { if (state==0) print }
    ' "$f" > "$f.cleaned"
  else
    python - "$f" <<'PY'
import sys, pathlib
f = pathlib.Path(sys.argv[1]).read_text().splitlines(True)
out = []
i = 0
while i < len(f):
    line = f[i]
    if line.startswith("<<<<<<< "):
        i += 1
        ours = []
        while i < len(f) and not f[i].startswith("======="):
            ours.append(f[i]); i += 1
        if i == len(f): break
        i += 1
        theirs = []
        while i < len(f) and not f[i].startswith(">>>>>>> "):
            theirs.append(f[i]); i += 1
        if i < len(f) and f[i].startswith(">>>>>>> "): i += 1
        choice = ""
        print("\\n--- CONFLICT HUNK ---", file=sys.stderr)
        print("OURS:\\n" + "".join(ours), file=sys.stderr)
        print("THEIRS:\\n" + "".join(theirs), file=sys.stderr)
        while choice not in ("o","t"):
            choice = input("Choose [o]urs or [t]heirs for this hunk: ").strip().lower()
        out.extend(ours if choice=="o" else theirs)
    else:
        out.append(line); i += 1
open(f"{sys.argv[1]}.cleaned","w").write("".join(out))
PY
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    info "$f (dry-run): cleaned preview below (diff stat)"
    git --no-pager diff --no-index --stat "$f" "$f.cleaned" || true
    rm -f "$f.cleaned"
    return 0
  fi

  mv "$f.cleaned" "$f"

  if grep -qE '^(<<<<<<<|=======|>>>>>>>)' "$f"; then
    err "$f: conflict markers still present after cleaning (see backup: $backup)"
  fi

  if ! python -m py_compile "$f" 2>py.err; then
    echo "❌ Python syntax error detected in $f:"
    cat py.err
    echo "Restoring from backup: $backup"
    cp "$backup" "$f"
    rm -f py.err
    exit 3
  fi
  rm -f py.err

  info "$f: cleaned and syntax-verified"
}

for f in "${FILES[@]}"; do
  clean_file "$f"
done

info "Diff summary:"
git --no-pager diff --stat || true

if [[ "$DRY_RUN" == "false" && "$LIST_ONLY" == "false" ]]; then
  info "Stage & commit when satisfied:"
  echo "  git add ${FILES[*]} && git commit -m \"chore: resolve conflict markers (${PREFER})\""
fi

info "Done."