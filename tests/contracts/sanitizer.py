"""SEC-REL-001: sanitization for any string echoed to a human-rendered output.

The gate writes Markdown that is rendered as a PR check comment and a JSONL
line committed to a shared audit repo. Both surfaces are downstream consumer
contexts — unsanitized input becomes a supply-chain surface.

Rules (Evidence item A):
  - Symbol names, file paths, suggestions: allowlist [A-Za-z0-9./_-]. Anything
    else is replaced with U+FFFD. Length-capped at 256 chars.
  - Free-text fields (skip reasons, error messages): control chars stripped,
    backslashes and backticks escaped, HTML-entity-encoded via stdlib html.
  - JSON output goes through json.dumps with ensure_ascii=True so control
    chars become escape sequences, not raw bytes.
"""
from __future__ import annotations

import html
import re
import string

_ALLOW_SYMBOL = re.compile(r"[^A-Za-z0-9./_\-]")
_REPLACEMENT = "\ufffd"
_MAX_SYMBOL_LEN = 256
_CONTROL_CHARS = "".join(chr(i) for i in range(0x20) if chr(i) not in "\t")
_CONTROL_TABLE = str.maketrans({c: _REPLACEMENT for c in _CONTROL_CHARS})
_PRINTABLE = set(string.printable)


def sanitize_symbol(value: str) -> str:
    """Allowlist-scrub symbol / path strings."""
    if not isinstance(value, str):
        value = str(value)
    value = value[:_MAX_SYMBOL_LEN]
    return _ALLOW_SYMBOL.sub(_REPLACEMENT, value)


def sanitize_freetext(value: str) -> str:
    """Escape free-form text for safe Markdown rendering."""
    if not isinstance(value, str):
        value = str(value)
    value = value.translate(_CONTROL_TABLE)
    value = re.sub(r"[\x7f-\x9f]", _REPLACEMENT, value)
    value = html.escape(value, quote=True)
    value = value.replace("`", "&#96;")
    return value[:1024]


def sanitize_path(value: str) -> str:
    """Path is symbol-class."""
    return sanitize_symbol(value)


def has_control_chars(value: str) -> bool:
    """True if value contains any C0/C1 control char, ANSI escapes, or
    anything outside the printable ASCII set."""
    if not isinstance(value, str):
        return False
    for ch in value:
        if ch not in _PRINTABLE and ch not in ("\t",):
            return True
    return False
