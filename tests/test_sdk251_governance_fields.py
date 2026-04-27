"""
SDK-251 — governance routing fields (mcp_server_name + model_id) on
AgentAction and AscendClient.evaluate_action.

Locks in five contracts:

  CONTRACT 1 — `AgentAction` dataclass exposes both fields, both default
               to None.
  CONTRACT 2 — `AgentAction.to_dict()` emits both at the TOP LEVEL of
               the wire dict (never nested inside action_details or
               context). Both omitted when None / empty.
  CONTRACT 3 — `AgentAction.to_dict()` raises ValidationError if either
               field is set to a non-string or whitespace-only string —
               so the constraint can't be bypassed by constructing the
               dataclass directly.
  CONTRACT 4 — `AscendClient.evaluate_action(...)` accepts both as
               keyword arguments and passes them through to AgentAction.
  CONTRACT 5 — `AscendClient.evaluate_action(...)` raises ValidationError
               at the boundary if either is provided as a non-string or
               whitespace-only string — saves a round-trip vs server
               HTTP 422.
"""

from __future__ import annotations

import pytest

from ascend.exceptions import ValidationError
from ascend.models import AgentAction


# ---------------------------------------------------------------------------
# CONTRACT 1 — fields exist on the dataclass
# ---------------------------------------------------------------------------


class TestContract1FieldsExist:
    def test_mcp_server_name_field_exists_and_defaults_to_none(self):
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
        )
        assert hasattr(action, "mcp_server_name")
        assert action.mcp_server_name is None

    def test_model_id_field_exists_and_defaults_to_none(self):
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
        )
        assert hasattr(action, "model_id")
        assert action.model_id is None


# ---------------------------------------------------------------------------
# CONTRACT 2 — to_dict emits at top level
# ---------------------------------------------------------------------------


class TestContract2ToDictTopLevel:
    def test_omitted_when_none(self):
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
        )
        data = action.to_dict()
        assert "mcp_server_name" not in data
        assert "model_id" not in data

    def test_mcp_server_name_emitted_at_top_level(self):
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
            mcp_server_name="mcp-trade-executor",
        )
        data = action.to_dict()
        assert data.get("mcp_server_name") == "mcp-trade-executor"
        # Must be top-level, NOT nested under action_details or context.
        assert "mcp_server_name" not in (data.get("action_details") or {})
        assert "mcp_server_name" not in (data.get("context") or {})

    def test_model_id_emitted_at_top_level(self):
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
            model_id="claude-3-sonnet",
        )
        data = action.to_dict()
        assert data.get("model_id") == "claude-3-sonnet"
        assert "model_id" not in (data.get("action_details") or {})
        assert "model_id" not in (data.get("context") or {})

    def test_both_emitted_when_both_set(self):
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
            mcp_server_name="mcp-x",
            model_id="model-y",
        )
        data = action.to_dict()
        assert data["mcp_server_name"] == "mcp-x"
        assert data["model_id"] == "model-y"

    def test_whitespace_stripped_on_emit(self):
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
            mcp_server_name="  mcp-x  ",
            model_id="\tmodel-y\n",
        )
        data = action.to_dict()
        assert data["mcp_server_name"] == "mcp-x"
        assert data["model_id"] == "model-y"


# ---------------------------------------------------------------------------
# CONTRACT 3 — to_dict raises on bad inputs (no bypass via direct dataclass)
# ---------------------------------------------------------------------------


class TestContract3ToDictValidation:
    def test_mcp_server_name_whitespace_only_raises(self):
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
            mcp_server_name="   ",
        )
        with pytest.raises(ValidationError):
            action.to_dict()

    def test_model_id_whitespace_only_raises(self):
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
            model_id="\t\n",
        )
        with pytest.raises(ValidationError):
            action.to_dict()

    def test_mcp_server_name_non_string_raises(self):
        # type: ignore[arg-type]  — the test is exactly that the runtime
        # check rejects a non-string even when the type system can't.
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
        )
        action.mcp_server_name = 123  # type: ignore[assignment]
        with pytest.raises(ValidationError):
            action.to_dict()

    def test_model_id_non_string_raises(self):
        action = AgentAction(
            agent_id="a", agent_name="A",
            action_type="x", resource="y",
        )
        action.model_id = ["bad"]  # type: ignore[assignment]
        with pytest.raises(ValidationError):
            action.to_dict()


# ---------------------------------------------------------------------------
# CONTRACT 4 / 5 — evaluate_action passes through + boundary validation
# ---------------------------------------------------------------------------


class TestContract4And5ClientPassthrough:
    """Build a minimal client stub so evaluate_action's network call is
    intercepted; we just need to capture the action.to_dict() payload."""

    def _make_client_stub(self):
        from ascend.client import AscendClient

        captured: dict = {}

        class _StubClient(AscendClient):
            def __init__(self):
                # bypass AscendClient.__init__ which validates an api_key.
                self.api_key = "stub"
                self.agent_id = "agent-001"
                self.agent_name = "stub-agent"
                self._is_blocked = False
                self._kill_switch_reason = None

            def _request(self, method, endpoint, data=None, **_):
                captured["endpoint"] = endpoint
                captured["data"] = data
                return {
                    "decision": "ALLOWED",
                    "action_id": 1,
                    "risk_score": 0,
                }

        return _StubClient(), captured

    def test_kwargs_flow_to_wire_payload(self):
        client, captured = self._make_client_stub()
        client.evaluate_action(
            action_type="execute_trade",
            resource="trading_desk",
            mcp_server_name="mcp-trade-executor",
            model_id="claude-3-sonnet",
            wait_for_decision=False,
        )
        assert captured["data"]["mcp_server_name"] == "mcp-trade-executor"
        assert captured["data"]["model_id"] == "claude-3-sonnet"

    def test_kwargs_omitted_when_unset(self):
        client, captured = self._make_client_stub()
        client.evaluate_action(
            action_type="execute_trade",
            resource="trading_desk",
            wait_for_decision=False,
        )
        # Wire-compat with 2.5.0 — neither key in the body when not provided.
        assert "mcp_server_name" not in captured["data"]
        assert "model_id" not in captured["data"]

    def test_mcp_server_name_empty_raises_at_boundary(self):
        client, _ = self._make_client_stub()
        with pytest.raises(ValidationError):
            client.evaluate_action(
                action_type="execute_trade",
                resource="trading_desk",
                mcp_server_name="   ",
            )

    def test_model_id_empty_raises_at_boundary(self):
        client, _ = self._make_client_stub()
        with pytest.raises(ValidationError):
            client.evaluate_action(
                action_type="execute_trade",
                resource="trading_desk",
                model_id="",
            )

    def test_mcp_server_name_non_string_raises_at_boundary(self):
        client, _ = self._make_client_stub()
        with pytest.raises(ValidationError):
            client.evaluate_action(
                action_type="execute_trade",
                resource="trading_desk",
                mcp_server_name=42,  # type: ignore[arg-type]
            )

    def test_model_id_non_string_raises_at_boundary(self):
        client, _ = self._make_client_stub()
        with pytest.raises(ValidationError):
            client.evaluate_action(
                action_type="execute_trade",
                resource="trading_desk",
                model_id={"bad": "shape"},  # type: ignore[arg-type]
            )


class TestVersion:
    def test_version_is_2_5_1(self):
        import ascend
        assert ascend.__version__ == "2.5.1"
