"""SEC-REL-001 Evidence item A — log injection / unicode sanitization.

Plant a fixture with hostile inputs (ANSI escapes, unicode control chars,
Markdown syntax injection, HTML tags in symbol names). Run the gate. Assert
every echoed field in the Markdown report is neutralized: no raw control
characters, no unescaped Markdown/HTML, symbol-class fields contain only
[A-Za-z0-9./_-].
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))

from tests.contracts import runner, sanitizer, config

HOSTILE_SYMBOL = "evil\u001b[31mRED\u001b[0m"
HOSTILE_MD = "](http://evil) <script>alert(1)</script>"


def _hostile_fixture_md() -> str:
    return f"""# hostile fixture

```python
from ascend import AscendClient

client = AscendClient(
    api_key="fake_contract_test_key_do_not_use",
    api_url="https://contract-test.invalid",
)
client.{HOSTILE_SYMBOL}_method()
```

<!-- contract-test: skip reason="skip reason injection attempt {HOSTILE_MD}" -->
```python
nothing_to_see()
```
"""


def test_unicode_sanitization_in_symbol_echoes(tmp_path):
    fixture = tmp_path / "hostile.md"
    fixture.write_text(_hostile_fixture_md())

    json_out = tmp_path / "report.json"
    md_out = tmp_path / "report.md"
    exit_code = runner.run(
        extra_paths=[fixture],
        json_out=json_out,
        md_out=md_out,
        trigger="self-test-injection",
        append_audit=False,
        isolated=True,
    )

    assert exit_code in (config.EXIT_CONTRACT_VIOLATION, config.EXIT_OK)

    md_text = md_out.read_text()
    assert "\x1b" not in md_text, "ANSI escape leaked into markdown report"
    assert "\u001b" not in md_text
    for i in range(0x20):
        if chr(i) in ("\n", "\t"):
            continue
        assert chr(i) not in md_text, f"control char U+{i:04X} leaked"

    assert "<script>" not in md_text, "unescaped HTML in markdown"

    report = json.loads(json_out.read_text())
    for rec in report:
        for key in ("missing_symbol", "file", "lang"):
            if key in rec and rec[key]:
                val = rec[key]
                assert sanitizer._ALLOW_SYMBOL.search(val) is None or \
                       "\ufffd" in val, (
                           f"symbol-class field {key!r}={val!r} "
                           f"contains non-allowlisted chars"
                       )


def test_sanitize_symbol_replaces_control_chars():
    out = sanitizer.sanitize_symbol(HOSTILE_SYMBOL)
    assert "\x1b" not in out
    assert "[31m" not in out or "\ufffd" in out
    assert "\ufffd" in out


def test_sanitize_freetext_escapes_markdown_and_html():
    out = sanitizer.sanitize_freetext("](http://evil) <script>alert(1)</script>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_sanitize_freetext_strips_control_chars():
    out = sanitizer.sanitize_freetext("hello\x1b[31mworld\x00")
    assert "\x1b" not in out
    assert "\x00" not in out


def test_has_control_chars_detects_ansi():
    assert sanitizer.has_control_chars("\x1b[31m")
    assert sanitizer.has_control_chars("text\x00nul")
    assert not sanitizer.has_control_chars("clean ascii text")
