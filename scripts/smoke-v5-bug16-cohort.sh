#!/usr/bin/env bash
# SDK 2.4.0 — BUG-16 cohort · V5 smoke test (clean-stranger Codespace).
#
# Produces the artifacts required by Donald's Day 3 directive:
#   (a) full terminal transcript (this script's stdout+stderr → tee'd)
#   (b) environment fingerprint (uname, python, pip versions + list)
#   (c) the exact pip install command used
#
# Usage (inside Codespace):
#   bash scripts/smoke-v5-bug16-cohort.sh /path/to/ascend_ai_sdk-2.4.0-*.whl \
#     2>&1 | tee /tmp/v5-smoke-transcript.log
#
# Fail-fast. All commands echo before execution for audit.
set -euo pipefail

WHEEL="${1:-}"
if [[ -z "$WHEEL" || ! -f "$WHEEL" ]]; then
  echo "Usage: $0 <path-to-ascend_ai_sdk-2.4.0-*.whl>" >&2
  exit 2
fi

say() { printf '\n=== %s ===\n' "$*"; }

say "V5 smoke test — SDK 2.4.0 BUG-16 cohort"
say "timestamp: $(date -u +%FT%TZ)"

say "Environment fingerprint"
uname -a
which python python3 pip
python --version
pip --version
printf 'HOSTNAME=%s\n' "${HOSTNAME:-unknown}"
printf 'CODESPACES=%s\n' "${CODESPACES:-not-set}"
printf 'PWD=%s\n' "$PWD"
printf 'HOME=%s\n' "$HOME"
printf 'WHEEL=%s\n' "$WHEEL"

say "Fresh venv"
python -m venv /tmp/v5-venv
# shellcheck source=/dev/null
source /tmp/v5-venv/bin/activate
python -m pip install --upgrade pip

say "Pre-install pip list (baseline)"
pip list

say "Install wheel (exact command logged below)"
echo "+ pip install $WHEEL"
pip install "$WHEEL"

say "Post-install pip list"
pip list

say "Installed ascend version (must be 2.4.0)"
python -c 'import ascend, sys; print("ascend", ascend.__version__); sys.exit(0 if ascend.__version__ == "2.4.0" else 1)'

say "Functional smoke test — runs scripts/smoke_v5_functional.py"
python scripts/smoke_v5_functional.py

say "V5 smoke test: ALL CHECKS PASSED"
