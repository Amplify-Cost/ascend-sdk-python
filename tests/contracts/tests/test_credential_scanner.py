"""SEC-REL-001: credential scanner positive/negative tests.

Evidence requirement: plant a fake key that matches the real-key shape,
assert the scanner exits 2 (EXIT_INFRA_FAILURE) and no markdown report is
rendered. Separately assert placeholders do NOT trip the scanner.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))

from tests.contracts import credential_scanner, runner, config


PLANTED_REAL_SHAPE = "owkai_Q7fPx2KmJw8BvN4Rc6Hq5TgLy1Mz0Vd3"  # not a real key
PLACEHOLDER = "ascend_prod_your_key_here"
SYNTHETIC = credential_scanner.SYNTHETIC_KEY


def test_scanner_catches_planted_real_shape_key():
    hits = credential_scanner.scan_text(f"key = {PLANTED_REAL_SHAPE}")
    assert len(hits) == 1, hits
    assert hits[0][0] == "owkai_*"


def test_scanner_allows_placeholder():
    hits = credential_scanner.scan_text(f"key = {PLACEHOLDER}")
    assert hits == []


def test_scanner_allows_synthetic_key():
    hits = credential_scanner.scan_text(f"key = {SYNTHETIC}")
    assert hits == []


def test_scanner_catches_jwt():
    jwt = "eyJabc1234567890.eyJdef1234567890.signature_xyz987"
    hits = credential_scanner.scan_text(jwt)
    assert len(hits) == 1, hits
    assert hits[0][0] == "JWT"


def test_scanner_catches_aws_access_key():
    hits = credential_scanner.scan_text("AKIA7BQMPLK2RS9CT4FG")
    assert len(hits) == 1
    assert hits[0][0] == "AWS access key"


def test_runner_exits_infra_failure_when_planted_key_in_fixture(tmp_path):
    fixture = tmp_path / "planted.md"
    fixture.write_text(f"""# planted key

```python
api_key = "{PLANTED_REAL_SHAPE}"
```
""")
    exit_code = runner.run(
        extra_paths=[fixture],
        json_out=tmp_path / "r.json",
        md_out=tmp_path / "r.md",
        trigger="self-test-planted-key",
        append_audit=False,
        isolated=True,
    )
    assert exit_code == config.EXIT_INFRA_FAILURE


def test_redaction_in_hit_output():
    """Hit should NOT echo the full key; only a 12-char prefix."""
    hits = credential_scanner.scan_text(PLANTED_REAL_SHAPE + " extra")
    for _, redacted in hits:
        assert len(redacted) <= 13
        assert PLANTED_REAL_SHAPE not in redacted
