"""SEC-REL-001: RED/GREEN/YELLOW validation cases.

These are the three contract guarantees the gate makes. If any of these
breaks, the gate is broken.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"

sys.path.insert(0, str(HERE.parents[2]))

from tests.contracts import runner, config


def _run(paths, tmp_path, trigger="self-test"):
    json_out = tmp_path / "report.json"
    md_out = tmp_path / "report.md"
    exit_code = runner.run(
        extra_paths=[pathlib.Path(p) for p in paths],
        json_out=json_out,
        md_out=md_out,
        trigger=trigger,
        append_audit=False,
        isolated=True,
    )
    report = json.loads(json_out.read_text())
    return exit_code, report, md_out.read_text()


def test_RED_bug16_reproduction_flags_submit_action(tmp_path):
    """RED self-test: gate flags a missing AscendClient method.

    Originally asserted against ``submit_action`` (the BUG-16 symbol);
    after SDK 2.4.0 added the deprecated shim, the fixture was updated
    to use ``nonexistent_fictitious_method``, which is guaranteed to
    remain absent so this self-test keeps exercising the gate.
    """
    exit_code, report, md = _run([FIXTURES / "red_bug16_repro.md"], tmp_path)
    fails = [r for r in report if r["status"] == "fail"]
    assert exit_code == config.EXIT_CONTRACT_VIOLATION
    assert any(
        "nonexistent_fictitious_method" in r.get("missing_symbol", "")
        for r in fails
    ), report
    assert any(r.get("file", "").endswith("red_bug16_repro.md") for r in fails)


def test_GREEN_correct_usage_passes_silently(tmp_path):
    exit_code, report, _md = _run([FIXTURES / "green_correct.md"], tmp_path)
    assert exit_code == config.EXIT_OK
    fails = [r for r in report if r["status"] == "fail"]
    assert fails == [], f"unexpected failures: {fails}"
    passes = [r for r in report if r["status"] == "pass"]
    assert len(passes) >= 1


def test_YELLOW_skip_directive_respected(tmp_path):
    exit_code, report, md = _run([FIXTURES / "yellow_skipped.md"], tmp_path)
    assert exit_code == config.EXIT_OK
    skipped = [r for r in report if r["status"] == "skip"]
    assert len(skipped) == 1, report
    assert "pedagogical" in skipped[0]["skip_reason"]
    assert "pedagogical" in md
