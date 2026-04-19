"""SEC-REL-001: fail-closed crash test.

Deliberately trips an uncaught exception mid-run. Wrapping CI MUST see a
non-zero exit code. There is no silent-pass, no "partial results OK"
fallback.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))

from tests.contracts import runner, config


def test_force_crash_raises_infra_failure_via_main():
    """CLI entry-point must catch the crash and exit 2."""
    rc = runner.main(["--force-crash", "--no-audit", "--isolated"])
    assert rc == config.EXIT_INFRA_FAILURE


def test_force_crash_via_subprocess_reports_non_zero_exit():
    """True CI simulation: spawn as child process, check exit code."""
    result = subprocess.run(
        [sys.executable, "-m", "tests.contracts.runner",
         "--force-crash", "--no-audit", "--isolated"],
        cwd=str(HERE.parents[2]),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert result.returncode == config.EXIT_INFRA_FAILURE
    assert "SEC-REL-001 infra failure" in result.stderr
    assert "crash-test harness tripped intentionally" in result.stderr


def test_missing_canonical_source_fails_closed(tmp_path, monkeypatch):
    """If a canonical path is missing, the gate must exit 2."""
    from tests.contracts import config as cfg
    monkeypatch.setattr(cfg, "PYTHON_SDK_ROOT", tmp_path / "does-not-exist")

    with pytest.raises(SystemExit) as exc:
        cfg.validate_environment()
    assert exc.value.code == cfg.EXIT_INFRA_FAILURE


def test_planted_key_in_env_fails_closed(tmp_path, monkeypatch):
    """Real-shape key in os.environ must trip the env scanner."""
    monkeypatch.setenv("SOME_SECRET_IN_ENV", "owkai_7bHzR3ReA1QpN8fM9xCqZvL4KvJwXoTg2YdE5uSiP6cVv")
    rc = runner.run(
        extra_paths=[],
        json_out=tmp_path / "r.json",
        md_out=tmp_path / "r.md",
        trigger="self-test-env-leak",
        append_audit=False,
        isolated=True,
    )
    assert rc == config.EXIT_INFRA_FAILURE
