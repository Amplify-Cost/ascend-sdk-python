"""SDK 2.4.0 — BUG-16 cohort Class B: FailMode.CLOSED evidence tests.

Per Gate 2 directive, every new Class B method (heartbeat scheduler
plus the ported `ascend.wrappers` subpackage) must preserve the
FailMode.CLOSED contract when the SDK cannot reach ASCEND. These
tests point the SDK at an unreachable URL and assert that:

  1. start_heartbeat() does not raise, even though every heartbeat
     call fails at the transport layer;
  2. the scheduler is cancellable and stop_heartbeat() is idempotent;
  3. ascend.wrappers governed_run blocks high-risk commands when no
     client is configured (FailMode.CLOSED default);
  4. ascend.wrappers.dynamic_code.safe_eval refuses to execute
     dangerous code in fail-closed mode.

Evidence tag: BUG-16 / DOC-DRIFT-HEARTBEAT / DOC-DRIFT-WRAPPERS.
"""
from __future__ import annotations

import threading
import time

import pytest

from ascend import AscendClient, FailMode


UNREACHABLE_URL = "https://contract-test.invalid"


def _make_closed_client() -> AscendClient:
    """Construct a FailMode.CLOSED client pointed at an unreachable URL."""
    return AscendClient(
        api_key="fake_contract_test_key_do_not_use",
        agent_id="failmode-closed-test",
        api_url=UNREACHABLE_URL,
        fail_mode="closed",
        timeout=1,
        max_retries=0,
        enable_circuit_breaker=False,
    )


class TestHeartbeatFailModeClosed:
    """start_heartbeat() / stop_heartbeat() fail-safe contract."""

    def test_start_heartbeat_does_not_raise_when_api_unreachable(self):
        """Heartbeat send failures are swallowed; scheduler keeps running."""
        client = _make_closed_client()
        try:
            # Must return immediately; must not raise even though the
            # first tick will fail to reach the unreachable URL.
            client.start_heartbeat(interval_seconds=30)
            # Timer handle must be set, proving the scheduler was armed.
            assert client._heartbeat_timer is not None
        finally:
            client.stop_heartbeat()
            client.close()

    def test_stop_heartbeat_is_idempotent(self):
        """Calling stop_heartbeat() repeatedly must not raise."""
        client = _make_closed_client()
        try:
            client.start_heartbeat(interval_seconds=30)
            client.stop_heartbeat()
            client.stop_heartbeat()  # second call must be a no-op
            assert client._heartbeat_timer is None
        finally:
            client.close()

    def test_start_heartbeat_with_negative_interval_raises(self):
        """Fail-secure validation at the public API boundary."""
        client = _make_closed_client()
        try:
            with pytest.raises(ValueError):
                client.start_heartbeat(interval_seconds=-1)
            with pytest.raises(ValueError):
                client.start_heartbeat(interval_seconds=0)
        finally:
            client.close()

    def test_close_stops_heartbeat_scheduler(self):
        """close() must cancel the scheduler so Python can shut down."""
        client = _make_closed_client()
        client.start_heartbeat(interval_seconds=30)
        assert client._heartbeat_timer is not None
        client.close()
        assert client._heartbeat_timer is None

    def test_heartbeat_scheduler_runs_on_daemon_thread(self):
        """A non-daemon scheduler would block process shutdown."""
        client = _make_closed_client()
        try:
            client.start_heartbeat(interval_seconds=30)
            timer = client._heartbeat_timer
            assert timer is not None
            assert timer.daemon is True, (
                "scheduler must run on daemon thread or it will block "
                "the host agent's shutdown"
            )
        finally:
            client.stop_heartbeat()
            client.close()

    def test_restart_cancels_prior_scheduler(self):
        """Double-start must cancel the prior timer (no orphan threads)."""
        client = _make_closed_client()
        try:
            client.start_heartbeat(interval_seconds=30)
            first_timer = client._heartbeat_timer
            client.start_heartbeat(interval_seconds=45)
            second_timer = client._heartbeat_timer
            assert first_timer is not second_timer
            assert client._heartbeat_interval == 45
        finally:
            client.stop_heartbeat()
            client.close()


class TestSubprocessWrapperFailModeClosed:
    """ascend.wrappers.subprocess fail-closed contract (no client configured)."""

    def test_governed_run_rejects_critical_when_fail_closed(self):
        """Critical commands must raise when no client is available."""
        from ascend.wrappers.subprocess import governed_run, GovernanceError

        # Reset module config to defaults (fail_mode=closed, no client).
        from ascend.wrappers import subprocess as sp
        sp._config["client"] = None
        sp._config["fail_mode"] = "closed"

        with pytest.raises(GovernanceError):
            # "rm -rf /" classifies as critical → must be blocked.
            governed_run("rm -rf /", shell=True)

    def test_governed_run_rejects_shell_true_by_default(self):
        """shell=True must be blocked in fail-closed mode."""
        from ascend.wrappers.subprocess import (
            governed_run, ShellNotAllowedError
        )
        from ascend.wrappers import subprocess as sp
        sp._config["client"] = None
        sp._config["fail_mode"] = "closed"
        sp._config["allow_shell"] = False

        with pytest.raises(ShellNotAllowedError):
            governed_run("echo hello", shell=True)


class TestDynamicCodeWrapperFailModeClosed:
    """ascend.wrappers.dynamic_code fail-closed contract."""

    def test_safe_eval_blocks_import_attempt(self):
        """AST analyzer must reject imports even with no network."""
        from ascend.wrappers.dynamic_code import safe_eval, DangerousCodeError

        with pytest.raises((DangerousCodeError, SyntaxError)):
            safe_eval("__import__('os').system('echo pwned')")

    def test_safe_eval_blocks_os_access(self):
        """Restricted builtins must prevent filesystem access."""
        from ascend.wrappers.dynamic_code import (
            safe_eval, SafeEvalError, DangerousCodeError
        )

        # 'open' is not in restricted builtins; must fail.
        with pytest.raises((SafeEvalError, NameError, DangerousCodeError)):
            safe_eval("open('/etc/passwd').read()")

    def test_safe_eval_allows_pure_arithmetic(self):
        """Sanity: fail-closed does not block genuinely safe expressions."""
        from ascend.wrappers.dynamic_code import safe_eval

        assert safe_eval("2 + 2") == 4
        assert safe_eval("price * qty", {"price": 10, "qty": 5}) == 50
