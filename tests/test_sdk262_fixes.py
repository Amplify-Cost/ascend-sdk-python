"""
SDK-262 — three independent fixes for 2.6.2.

  1. BUG-02-04/05 — `_request()` governance-violation 403 path returned
     an `AuthorizationDecision` instance, breaking downstream
     `from_dict()` calls with `AttributeError`. Path now returns a dict.

  2. Kill-switch fail-secure — `_poll_kill_switch()` previously
     swallowed every exception with `except Exception: pass`, leaving
     `_is_blocked = False` permanently on any auth or network failure.
     Now logs warnings, counts consecutive failures, and after 3 in a
     row sets `_is_blocked = True` (fail-secure). On a successful
     poll the counter resets.

  3. Decision enum vocabulary — wire values `auto_approved` and
     `executed` previously collapsed silently to `Decision.PENDING`.
     New `AUTO_APPROVED` and `EXECUTED` enum values map to ALLOWED
     in `from_dict()`.

Plus a version sentinel: 2.6.2.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import ascend
from ascend import FailMode
from ascend.client import AscendClient
from ascend.models import AuthorizationDecision, Decision


def _fake_response(status_code: int, body):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = {}
    resp.json.return_value = body
    resp.text = json.dumps(body) if not isinstance(body, str) else body
    return resp


def _client():
    return AscendClient(
        api_key="owkai_test_key_AAAAAAAAAAAAAAAA",
        api_url="https://test.local",
        agent_id="test-agent",
        fail_mode=FailMode.OPEN,
    )


# ---------------------------------------------------------------------------
# CONTRACT 1 — BUG-02-04/05 governance 403 returns dict (not dataclass)
# ---------------------------------------------------------------------------


class TestContract1Bug020405DoubleParse:
    def test_governance_403_does_not_raise_attribute_error(self):
        """Pre-fix: AuthorizationDecision.from_dict(<dataclass>) raised
        AttributeError. Post-fix: the 403 path returns a dict that
        from_dict parses cleanly."""
        body = {
            "detail": {
                "error": "MCP server governance violation",
                "detail": "MCP server is not registered.",
                "mcp_server_name": "unregistered-xyz",
                "correlation_id": "test-001",
            }
        }
        client = _client()
        client._session = MagicMock()
        client._session.request.return_value = _fake_response(403, body)

        result = client.evaluate_action(
            action_type="tool_call",
            resource="crm",
            wait_for_decision=False,
        )
        # The smoking gun before the fix:
        # `AttributeError: 'AuthorizationDecision' object has no attribute 'get'`
        # would have been raised inside from_dict. Reaching here means
        # the contract is restored.
        assert isinstance(result, AuthorizationDecision)
        assert result.decision == Decision.DENIED

    def test_governance_403_status_accessible(self):
        body = {
            "detail": {
                "error": "Model governance violation",
                "detail": "Model not registered.",
                "model_id": "gpt-4-prod",
                "correlation_id": "test-002",
            }
        }
        client = _client()
        client._session = MagicMock()
        client._session.request.return_value = _fake_response(403, body)

        result = client.evaluate_action(
            action_type="model_inference",
            resource="inference_engine",
            wait_for_decision=False,
        )
        assert result.status == "denied"

    def test_governance_403_reason_accessible(self):
        body = {
            "detail": {
                "error": "MCP server governance violation",
                "detail": "MCP server is not registered. Register first.",
                "mcp_server_name": "x",
                "correlation_id": "c",
            }
        }
        client = _client()
        client._session = MagicMock()
        client._session.request.return_value = _fake_response(403, body)

        result = client.evaluate_action(
            action_type="tool_call",
            resource="x",
            wait_for_decision=False,
        )
        assert "not registered" in (result.reason or "").lower()

    def test_request_returns_dict_not_dataclass(self):
        """Lower-level: confirm `_request()` itself now returns a dict
        on the 403 governance path. The contract is `_request → dict`."""
        body = {
            "detail": {
                "error": "MCP governance violation",
                "detail": "Unregistered.",
                "correlation_id": "c",
            }
        }
        client = _client()
        client._session = MagicMock()
        client._session.request.return_value = _fake_response(403, body)
        out = client._request("POST", "/test", data={})
        assert isinstance(out, dict), (
            f"_request must return dict on 403 governance path, got "
            f"{type(out).__name__}"
        )
        assert out["decision"] == "denied"
        assert out["status"] == "denied"


# ---------------------------------------------------------------------------
# CONTRACT 2 — Kill-switch fail-secure on consecutive polling failures
# ---------------------------------------------------------------------------


class TestContract2KillSwitchFailSecure:
    def _failing_request(self, *_args, **_kwargs):
        from ascend.exceptions import AuthenticationError
        raise AuthenticationError("Authentication required")

    def test_one_failure_does_not_block(self):
        client = _client()
        # Cancel the timer the moment _poll_kill_switch creates one,
        # so the test doesn't run in the background.
        with patch.object(client, "_request", side_effect=self._failing_request):
            client._poll_kill_switch()
        if client._kill_switch_timer:
            client._kill_switch_timer.cancel()
        assert client._kill_switch_failure_count == 1
        assert client._is_blocked is False

    def test_three_failures_fail_secure_blocks(self):
        client = _client()
        with patch.object(client, "_request", side_effect=self._failing_request):
            client._poll_kill_switch()
            if client._kill_switch_timer:
                client._kill_switch_timer.cancel()
            client._poll_kill_switch()
            if client._kill_switch_timer:
                client._kill_switch_timer.cancel()
            client._poll_kill_switch()
            if client._kill_switch_timer:
                client._kill_switch_timer.cancel()
        assert client._kill_switch_failure_count >= 3
        assert client._is_blocked is True
        assert "fail-secure" in (client._kill_switch_reason or "").lower()

    def test_successful_poll_resets_counter(self):
        client = _client()
        # Two failures, then one success.
        ok_response = {"blocked": False, "reason": None}

        def request_side_effects():
            yield from [
                self._failing_request,  # call 1
                self._failing_request,  # call 2
            ]

        # First two calls fail.
        with patch.object(client, "_request", side_effect=self._failing_request):
            client._poll_kill_switch()
            if client._kill_switch_timer:
                client._kill_switch_timer.cancel()
            client._poll_kill_switch()
            if client._kill_switch_timer:
                client._kill_switch_timer.cancel()
        assert client._kill_switch_failure_count == 2

        # Third call succeeds.
        with patch.object(client, "_request", return_value=ok_response):
            client._poll_kill_switch()
            if client._kill_switch_timer:
                client._kill_switch_timer.cancel()
        assert client._kill_switch_failure_count == 0
        assert client._is_blocked is False

    def test_recovery_after_failsecure_block(self):
        """After 3 failures + fail-secure block, a successful poll
        must let the agent unblock again — this is the auto-recovery
        path that distinguishes fail-secure from a hard kill."""
        client = _client()
        with patch.object(client, "_request", side_effect=self._failing_request):
            for _ in range(3):
                client._poll_kill_switch()
                if client._kill_switch_timer:
                    client._kill_switch_timer.cancel()
        assert client._is_blocked is True

        # Endpoint comes back healthy with blocked=False.
        with patch.object(
            client, "_request", return_value={"blocked": False, "reason": None}
        ):
            client._poll_kill_switch()
            if client._kill_switch_timer:
                client._kill_switch_timer.cancel()
        assert client._kill_switch_failure_count == 0
        assert client._is_blocked is False

    def test_evaluate_action_warns_when_polling_not_started(self, caplog):
        """If the customer integration never calls
        start_kill_switch_polling(), evaluate_action must log a
        warning so operators know the safety net is inactive."""
        client = _client()
        client._session = MagicMock()
        client._session.request.return_value = _fake_response(
            200, {"decision": "allowed", "action_id": "1", "risk_score": 0}
        )

        with caplog.at_level(logging.WARNING):
            client.evaluate_action(
                action_type="x",
                resource="y",
                wait_for_decision=False,
            )

        warning_text = " ".join(r.getMessage() for r in caplog.records)
        assert "kill-switch" in warning_text.lower()
        assert "polling was never started" in warning_text.lower()

    def test_start_polling_flips_the_flag(self, caplog):
        """After start_kill_switch_polling() is called, evaluate_action
        must NOT emit the polling-not-started warning."""
        client = _client()
        client._session = MagicMock()
        client._session.request.return_value = _fake_response(
            200, {"blocked": False, "reason": None}
        )

        # Start polling and immediately cancel the timer so the
        # background thread doesn't keep firing.
        client.start_kill_switch_polling(interval_seconds=60)
        if client._kill_switch_timer:
            client._kill_switch_timer.cancel()
        assert client._kill_switch_polling_started is True

        # Now evaluate_action should NOT emit the warning.
        client._session.request.return_value = _fake_response(
            200, {"decision": "allowed", "action_id": "1", "risk_score": 0}
        )
        with caplog.at_level(logging.WARNING):
            client.evaluate_action(
                action_type="x", resource="y", wait_for_decision=False
            )
        warning_text = " ".join(r.getMessage() for r in caplog.records)
        assert "polling was never started" not in warning_text.lower()


# ---------------------------------------------------------------------------
# CONTRACT 3 — Decision enum expansion
# ---------------------------------------------------------------------------


class TestContract3DecisionEnumExpansion:
    def test_auto_approved_enum_value(self):
        assert Decision.AUTO_APPROVED.value == "auto_approved"

    def test_executed_enum_value(self):
        assert Decision.EXECUTED.value == "executed"

    def test_auto_approved_wire_maps_to_allowed(self):
        ad = AuthorizationDecision.from_dict(
            {"status": "auto_approved", "action_id": "1"}
        )
        assert ad.decision == Decision.ALLOWED, (
            f"Wire 'auto_approved' should map to Decision.ALLOWED "
            f"(it means policy approved without human review); "
            f"got {ad.decision}"
        )

    def test_executed_wire_maps_to_allowed(self):
        ad = AuthorizationDecision.from_dict(
            {"status": "executed", "action_id": "1"}
        )
        assert ad.decision == Decision.ALLOWED, (
            f"Wire 'executed' should map to Decision.ALLOWED "
            f"(it means approved AND carried out); "
            f"got {ad.decision}"
        )

    def test_pending_approval_still_maps_to_pending(self):
        """Regression guard for SDK-261 RT-4 — pending_approval is
        the canonical backend pending value and must not get reclassed
        into ALLOWED."""
        ad = AuthorizationDecision.from_dict(
            {"status": "pending_approval", "action_id": "1"}
        )
        assert ad.decision == Decision.PENDING

    def test_escalated_maps_to_pending(self):
        ad = AuthorizationDecision.from_dict(
            {"status": "escalated", "action_id": "1"}
        )
        assert ad.decision == Decision.PENDING

    def test_timeout_maps_to_pending(self):
        ad = AuthorizationDecision.from_dict(
            {"status": "timeout", "action_id": "1"}
        )
        assert ad.decision == Decision.PENDING

    def test_requires_modification_maps_to_pending(self):
        ad = AuthorizationDecision.from_dict(
            {"status": "requires_modification", "action_id": "1"}
        )
        assert ad.decision == Decision.PENDING

    def test_status_property_for_auto_approved_returns_approved(self):
        """Callers comparing `result.status == 'approved'` should
        match for AUTO_APPROVED — the canonical CWG vocabulary."""
        ad = AuthorizationDecision.from_dict(
            {"status": "auto_approved", "action_id": "1"}
        )
        assert ad.status == "approved"

    def test_status_property_for_executed_returns_approved(self):
        ad = AuthorizationDecision.from_dict(
            {"status": "executed", "action_id": "1"}
        )
        assert ad.status == "approved"

    def test_raw_status_preserves_wire_value_auto_approved(self):
        """The wire-level vocabulary is preserved on .raw_status so
        callers who care about the distinction still have it."""
        ad = AuthorizationDecision.from_dict(
            {"status": "auto_approved", "action_id": "1"}
        )
        assert ad.raw_status == "auto_approved"

    def test_raw_status_preserves_wire_value_executed(self):
        ad = AuthorizationDecision.from_dict(
            {"status": "executed", "action_id": "1"}
        )
        assert ad.raw_status == "executed"


# ---------------------------------------------------------------------------
# CONTRACT 4 — version sentinel
# ---------------------------------------------------------------------------


class TestContract4Version:
    def test_version_is_2_6_2(self):
        assert ascend.__version__ == "2.7.0"

    def test_constants_version_matches(self):
        from ascend.constants import SDK_VERSION
        assert SDK_VERSION == "2.7.0"
