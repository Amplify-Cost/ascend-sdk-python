"""SDK 2.7.1 — wait_for_decision surfaces HITL escalation (EP-003).

When an action is escalated to a senior approver the backend returns
status="escalated" (which maps to Decision.PENDING). The SDK must keep
waiting (it's still pending a human decision) but surface the escalation to
the caller exactly once — via an on_escalated callback if provided, else a
WARNING.
"""
import logging
from unittest.mock import MagicMock

from ascend import AscendClient
from ascend.models import AuthorizationDecision, Decision


def _client():
    c = AscendClient(
        api_key="test-key",
        agent_id="agent-1",
        agent_name="Agent 1",
        api_url="https://example.invalid",
        fail_mode="closed",
    )
    c._session = MagicMock()  # no real network
    return c


def _decision(status):
    return AuthorizationDecision.from_dict({"status": status, "action_id": "1"})


def test_on_escalated_callback_fires_once_and_wait_continues():
    client = _client()
    # two escalated polls (still pending) then a final approved decision
    client.get_action_status = MagicMock(
        side_effect=[_decision("escalated"), _decision("escalated"), _decision("approved")]
    )
    calls = []
    decision = client.wait_for_decision(
        "1",
        timeout=10,
        poll_interval=0.0,
        on_escalated=lambda action_id, d: calls.append((action_id, d.raw_status)),
    )
    # wait did NOT raise/return early — it continued through escalation and
    # returned the final approved decision
    assert decision.raw_status == "approved"
    assert decision.decision == Decision.ALLOWED
    # callback fired EXACTLY ONCE despite two escalated polls
    assert calls == [("1", "escalated")]


def test_escalated_logs_warning_when_no_callback(caplog):
    client = _client()
    client.get_action_status = MagicMock(
        side_effect=[_decision("escalated"), _decision("approved")]
    )
    with caplog.at_level(logging.WARNING):
        decision = client.wait_for_decision("1", timeout=10, poll_interval=0.0)
    assert decision.raw_status == "approved"
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert sum("escalated to senior approver" in m for m in warnings) == 1
