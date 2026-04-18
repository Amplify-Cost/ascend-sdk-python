"""
SDK 2.3.0 — orchestration pass-through tests.

Verifies:
  - AgentAction serializes the 3 new fields only when set
  - evaluate_action forwards orchestration kwargs into the payload
  - evaluate_action client-side rejects depth outside 0..5
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ascend.client import AscendClient
from ascend.exceptions import ValidationError
from ascend.models import AgentAction


class TestAgentActionOrchestrationFields:
    def test_fields_default_none(self):
        a = AgentAction(
            agent_id="a-1",
            agent_name="A",
            action_type="do",
            resource="r",
        )
        d = a.to_dict()
        assert "orchestration_session_id" not in d
        assert "parent_action_id" not in d
        assert "orchestration_depth" not in d

    def test_fields_round_trip_when_set(self):
        a = AgentAction(
            agent_id="a-1",
            agent_name="A",
            action_type="do",
            resource="r",
            orchestration_session_id="sess-42",
            parent_action_id=99,
            orchestration_depth=2,
        )
        d = a.to_dict()
        assert d["orchestration_session_id"] == "sess-42"
        assert d["parent_action_id"] == 99
        assert d["orchestration_depth"] == 2

    def test_zero_depth_is_serialized(self):
        """depth=0 is a meaningful value (root action), must be sent."""
        a = AgentAction(
            agent_id="a-1",
            agent_name="A",
            action_type="do",
            resource="r",
            orchestration_depth=0,
        )
        assert a.to_dict()["orchestration_depth"] == 0


class TestEvaluateActionOrchestrationForwarding:
    def _client(self):
        c = AscendClient.__new__(AscendClient)
        # Minimal required state
        c.agent_id = "agent-001"
        c.agent_name = "Test Agent"
        c._is_blocked = False
        c._kill_switch_reason = None
        return c

    def test_forwards_orchestration_kwargs(self):
        c = self._client()
        with patch.object(c, "_request") as mock_req:
            mock_req.return_value = {
                "action_id": "x",
                "decision": "allowed",
                "risk_score": 10,
            }
            c.evaluate_action(
                action_type="data_access",
                resource="db",
                orchestration_session_id="sess-a",
                parent_action_id=123,
                orchestration_depth=3,
                wait_for_decision=False,
            )
            payload = mock_req.call_args[1]["data"]
            assert payload["orchestration_session_id"] == "sess-a"
            assert payload["parent_action_id"] == 123
            assert payload["orchestration_depth"] == 3

    def test_depth_out_of_range_raises_before_network(self):
        c = self._client()
        with patch.object(c, "_request") as mock_req:
            with pytest.raises(ValidationError):
                c.evaluate_action(
                    action_type="x", resource="y",
                    orchestration_depth=6, wait_for_decision=False,
                )
            mock_req.assert_not_called()

    def test_negative_depth_rejected(self):
        c = self._client()
        with patch.object(c, "_request"):
            with pytest.raises(ValidationError):
                c.evaluate_action(
                    action_type="x", resource="y",
                    orchestration_depth=-1, wait_for_decision=False,
                )

    def test_depth_none_allowed(self):
        c = self._client()
        with patch.object(c, "_request") as mock_req:
            mock_req.return_value = {
                "action_id": "x", "decision": "allowed", "risk_score": 1,
            }
            c.evaluate_action(
                action_type="x", resource="y",
                orchestration_depth=None, wait_for_decision=False,
            )
            payload = mock_req.call_args[1]["data"]
            assert "orchestration_depth" not in payload
