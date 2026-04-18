"""
SDK 2.3.0 — new client methods:
  - link_model_to_agent (FEAT-001B)
  - register_supply_chain_component (FEAT-005)
  - get_pending_commands (SEC-103)
  - ack_command (SEC-103)

All tests mock AscendClient._request so they're offline, fast, and
dependency-free. They verify endpoint URLs, HTTP verbs, payload shapes,
and client-side validation.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from ascend.client import AscendClient
from ascend.exceptions import ValidationError


def _mk_client(agent_id: str = "agent-001") -> AscendClient:
    """Build an AscendClient without running __init__ (no network)."""
    c = AscendClient.__new__(AscendClient)
    c.agent_id = agent_id
    c.agent_name = "Test Agent"
    c._is_blocked = False
    c._kill_switch_reason = None
    return c


# ============================================================================
# link_model_to_agent
# ============================================================================


class TestLinkModelToAgent:
    def test_happy_path(self):
        c = _mk_client()
        with patch.object(c, "_request") as req:
            req.return_value = {"success": True, "agent": {"id": 1, "model_id": 5}}
            result = c.link_model_to_agent(agent_id="agent-001", model_id=5)
        assert req.call_args[0][0] == "PUT"
        assert req.call_args[0][1] == "/api/registry/agents/agent-001"
        assert req.call_args[1]["data"] == {"model_id": 5}
        assert result["success"] is True

    def test_rejects_empty_agent_id(self):
        c = _mk_client()
        with pytest.raises(ValidationError):
            c.link_model_to_agent(agent_id="", model_id=5)

    def test_rejects_non_positive_model_id(self):
        c = _mk_client()
        with pytest.raises(ValidationError):
            c.link_model_to_agent(agent_id="a", model_id=0)
        with pytest.raises(ValidationError):
            c.link_model_to_agent(agent_id="a", model_id=-1)
        with pytest.raises(ValidationError):
            c.link_model_to_agent(agent_id="a", model_id="5")  # type: ignore[arg-type]


# ============================================================================
# register_supply_chain_component
# ============================================================================


class TestRegisterSupplyChainComponent:
    def test_happy_path_minimal(self):
        c = _mk_client()
        with patch.object(c, "_request") as req:
            req.return_value = {"success": True, "component": {"id": 1}}
            c.register_supply_chain_component(
                component_id="comp-1",
                component_name="Test Library",
                component_type="library",
            )
        assert req.call_args[0][0] == "POST"
        assert req.call_args[0][1] == "/api/v1/supply-chain/components"
        payload = req.call_args[1]["data"]
        assert payload["component_id"] == "comp-1"
        assert payload["component_name"] == "Test Library"
        assert payload["component_type"] == "library"
        assert payload["provenance_verified"] is False
        assert payload["risk_level"] == "medium"
        # Optional fields must NOT be present when unset.
        assert "provider" not in payload
        assert "license_type" not in payload

    def test_happy_path_full_payload(self):
        c = _mk_client()
        with patch.object(c, "_request") as req:
            req.return_value = {"success": True, "component": {"id": 1}}
            c.register_supply_chain_component(
                component_id="comp-2",
                component_name="HuggingFace Model",
                component_type="model",
                provider="HuggingFace",
                version="1.0.0",
                latest_version="1.2.0",
                license_type="Apache-2.0",
                source_url="https://hf.co/foo",
                provenance_verified=True,
                risk_level="high",
                compliance_notes="Reviewed 2026-04-01",
                package_name="transformers",
                package_ecosystem="pypi",
            )
        payload = req.call_args[1]["data"]
        assert payload["provider"] == "HuggingFace"
        assert payload["provenance_verified"] is True
        assert payload["risk_level"] == "high"
        assert payload["package_ecosystem"] == "pypi"

    def test_rejects_empty_required_fields(self):
        c = _mk_client()
        with pytest.raises(ValidationError):
            c.register_supply_chain_component(
                component_id="", component_name="x", component_type="y",
            )
        with pytest.raises(ValidationError):
            c.register_supply_chain_component(
                component_id="x", component_name="", component_type="y",
            )
        with pytest.raises(ValidationError):
            c.register_supply_chain_component(
                component_id="x", component_name="y", component_type="",
            )


# ============================================================================
# get_pending_commands
# ============================================================================


class TestGetPendingCommands:
    def test_happy_path_with_explicit_agent(self):
        c = _mk_client()
        cmds = [{"command_id": "c-1", "command_type": "BLOCK"}]
        with patch.object(c, "_request") as req:
            req.return_value = {"agent_id": "a", "commands": cmds, "count": 1}
            result = c.get_pending_commands(agent_id="a")
        assert req.call_args[0][0] == "GET"
        assert req.call_args[0][1] == "/api/registry/agents/a/commands"
        assert result == cmds

    def test_uses_client_agent_id_when_unset(self):
        c = _mk_client(agent_id="bound-agent")
        with patch.object(c, "_request") as req:
            req.return_value = {"commands": [], "count": 0}
            c.get_pending_commands()
        assert req.call_args[0][1] == "/api/registry/agents/bound-agent/commands"

    def test_rejects_missing_agent_id(self):
        c = _mk_client(agent_id=None)  # no bound id
        with pytest.raises(ValidationError):
            c.get_pending_commands()

    def test_handles_empty_response(self):
        c = _mk_client()
        with patch.object(c, "_request") as req:
            req.return_value = None
            result = c.get_pending_commands(agent_id="a")
        assert result == []


# ============================================================================
# ack_command
# ============================================================================


class TestAckCommand:
    def test_happy_path_empty_body(self):
        c = _mk_client()
        with patch.object(c, "_request") as req:
            req.return_value = {
                "success": True,
                "command_id": "c-1",
                "status": "acknowledged",
            }
            ok = c.ack_command(command_id="c-1", agent_id="a")
        assert req.call_args[0][0] == "POST"
        assert req.call_args[0][1] == "/api/registry/agents/a/commands/c-1/ack"
        # Receipt-only ack -> empty body dict
        assert req.call_args[1]["data"] == {}
        assert ok is True

    def test_returns_false_on_failure(self):
        c = _mk_client()
        with patch.object(c, "_request") as req:
            req.return_value = {"success": False, "command_id": "c-1"}
            assert c.ack_command(command_id="c-1", agent_id="a") is False

    def test_uses_client_agent_id_default(self):
        c = _mk_client(agent_id="bound-agent")
        with patch.object(c, "_request") as req:
            req.return_value = {"success": True}
            c.ack_command(command_id="c-1")
        assert req.call_args[0][1] == (
            "/api/registry/agents/bound-agent/commands/c-1/ack"
        )

    def test_rejects_empty_command_id(self):
        c = _mk_client()
        with pytest.raises(ValidationError):
            c.ack_command(command_id="", agent_id="a")

    def test_rejects_missing_agent_id(self):
        c = _mk_client(agent_id=None)
        with pytest.raises(ValidationError):
            c.ack_command(command_id="c-1")
