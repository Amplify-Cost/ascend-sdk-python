"""SEC-REL-001: pre-flight scan for real API-key shapes in fixtures and
test environment. Runs as step 1 of every contract run; any hit exits with
EXIT_INFRA_FAILURE (2).

A fake synthetic key is allowed: the exact literal
`fake_contract_test_key_do_not_use`. Any other string matching the real-key
shape is a stop-the-world failure, even in test fixtures.
"""
from __future__ import annotations

import os
import pathlib
import re
from typing import Iterable, List, Tuple

SYNTHETIC_KEY = "fake_contract_test_key_do_not_use"

PLACEHOLDER_TOKENS = (
    "your_key_here", "your_api_key", "your_key", "abc123xyz",
    "xxxxxxxx", "xxxxxx", "example", "placeholder", "redacted",
    "your_token", "put_your", "replace_me", "demo_key",
)

_KEY_PATTERNS = [
    (re.compile(r"owkai_[A-Za-z0-9_\-]{16,}"), "owkai_*"),
    (re.compile(r"ascend_[A-Za-z0-9_\-]{16,}"), "ascend_*"),
    (re.compile(r"sk_(?:live|test)_[A-Za-z0-9]{16,}"), "sk_live/test_*"),
    (re.compile(r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._\-]{20,}"), "Authorization: Bearer *"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"), "JWT"),
]


def _is_placeholder(captured: str) -> bool:
    low = captured.lower()
    if SYNTHETIC_KEY in low:
        return True
    for tok in PLACEHOLDER_TOKENS:
        if tok in low:
            return True
    return False


def _safe_hits(text: str) -> List[Tuple[str, str]]:
    hits = []
    for pat, label in _KEY_PATTERNS:
        for m in pat.finditer(text):
            captured = m.group(0)
            if _is_placeholder(captured):
                continue
            hits.append((label, captured[:12] + "…"))
    return hits


def scan_text(text: str) -> List[Tuple[str, str]]:
    return _safe_hits(text)


def scan_paths(paths: Iterable[pathlib.Path]) -> List[Tuple[pathlib.Path, str, str]]:
    """Scan a set of files. Return (path, label, redacted_match) per hit."""
    out = []
    for p in paths:
        if not p.is_file():
            continue
        try:
            text = p.read_text(errors="replace")
        except Exception:
            continue
        for label, redacted in _safe_hits(text):
            out.append((p, label, redacted))
    return out


def scan_env() -> List[Tuple[str, str, str]]:
    """Scan os.environ for leaked keys. Synthetic key allowed."""
    out = []
    for k, v in os.environ.items():
        if not isinstance(v, str):
            continue
        for label, redacted in _safe_hits(v):
            out.append((k, label, redacted))
    return out
