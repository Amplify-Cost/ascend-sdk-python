"""
SDK 2.5.0 — Enterprise Management Surface tests.

Covers G-P1-01..05 method wrappers (MCP CRUD, kill-switch trigger/release,
orchestration, output filter, supply chain) and G-P2-01 promoted typed
fields on AuthorizationDecision.

Strategy:
  - Source-level + endpoint-constant checks (catch breakage that would
    silently mis-route a call).
  - Mock-based behaviour tests (assert _request is called with the
    expected verb, URL, and payload — no live HTTP).
  - Validation tests (each guard raises ValidationError on bad input
    BEFORE any network call — fail-fast contract).
  - AuthorizationDecision: typed fields populated AND metadata
    back-compat preserved (zero breaking change rule).
"""

from __future__ import annotations

import inspect
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from ascend import AscendClient
from ascend.constants import API_ENDPOINTS, SDK_VERSION
from ascend.exceptions import ValidationError
from ascend.models import AuthorizationDecision, Decision


# ---------------------------------------------------------------------------
# Version + endpoint constants
# ---------------------------------------------------------------------------

class TestVersionAndEndpoints:
    def test_sdk_version_bumped(self):
        # SDK-251 bumped 2.5.0 → 2.5.1 (additive: model_id +
        # mcp_server_name kwargs on evaluate_action). The 2.5.0
        # enterprise-method surface this file covers is unchanged.
        assert SDK_VERSION == "2.5.1"

    @pytest.mark.parametrize("key,expected", [
        ("mcp_servers", "/api/registry/mcp-servers"),
        ("mcp_server_detail", "/api/registry/mcp-servers/{server_name}"),
        ("mcp_server_activate", "/api/registry/mcp-servers/{server_name}/activate"),
        ("mcp_server_deactivate", "/api/registry/mcp-servers/{server_name}/deactivate"),
        ("mcp_scan_network", "/api/authorization/mcp-discovery/scan-network"),
        ("mcp_health_monitor", "/api/authorization/mcp-discovery/health-monitor"),
        ("kill_switch_trigger", "/api/billing/kill-switch/{organization_id}/trigger"),
        ("kill_switch_release", "/api/billing/kill-switch/{organization_id}/release"),
        ("topology_register", "/api/v1/orchestration/topology"),
        ("topology_mcp_register", "/api/v1/orchestration/topology/mcp"),
        ("cascade_kill", "/api/v1/orchestration/cascade-kill/{orchestrator_id}"),
        ("orchestration_session", "/api/v1/orchestration/sessions/{session_id}"),
        ("orchestration_session_risk", "/api/v1/orchestration/sessions/{session_id}/risk"),
        ("orchestration_stats", "/api/v1/orchestration/stats"),
        ("output_filter_config", "/api/v1/output-filter/config"),
        ("output_filter_findings", "/api/v1/output-filter/findings"),
        ("output_filter_findings_for_action", "/api/v1/output-filter/findings/{action_id}"),
        ("output_filter_scan", "/api/v1/output-filter/scan"),
        ("supply_chain_components_list", "/api/v1/supply-chain/components"),
        ("supply_chain_stats", "/api/v1/supply-chain/stats"),
        ("supply_chain_impact", "/api/v1/supply-chain/impact/{component_pk}"),
        ("supply_chain_cve_sync_status", "/api/v1/supply-chain/sync/status"),
        ("alerts_list", "/api/alerts"),
    ])
    def test_endpoint_constant_present(self, key: str, expected: str):
        assert API_ENDPOINTS[key] == expected


# ---------------------------------------------------------------------------
# Method-presence / signature
# ---------------------------------------------------------------------------

NEW_METHODS = (
    # G-P1-01 MCP (8)
    "register_mcp_server", "list_mcp_servers", "get_mcp_server",
    "activate_mcp_server", "deactivate_mcp_server", "delete_mcp_server",
    "scan_mcp_network", "get_mcp_health",
    # G-P1-02 kill-switch (2)
    "trigger_kill_switch", "release_kill_switch",
    # G-P1-03 orchestration (5)
    "register_topology", "register_mcp_topology", "cascade_kill",
    "get_orchestration_session", "get_orchestration_stats",
    # G-P1-04 output filter (4)
    "get_output_filter_config", "get_output_findings",
    "get_output_findings_for_action", "scan_output",
    # G-P1-05 supply chain (5)
    "list_supply_chain_components", "get_supply_chain_stats",
    "get_supply_chain_impact", "get_cve_sync_status",
    "get_supply_chain_alerts",
)


class TestMethodPresence:
    @pytest.mark.parametrize("method", NEW_METHODS)
    def test_method_exists_on_client(self, method: str):
        assert hasattr(AscendClient, method), (
            f"AscendClient.{method} missing — SDK 2.5.0 spec requires it"
        )
        assert callable(getattr(AscendClient, method))


# ---------------------------------------------------------------------------
# Behaviour: assert _request called with the right verb + URL + payload
# ---------------------------------------------------------------------------

def _client_with_mock() -> AscendClient:
    """Build a minimally-initialized client with _request stubbed out."""
    with patch("ascend.client.AscendClient._request") as _:
        c = AscendClient(
            api_key="test-key",
            agent_id="test-agent",
            agent_name="Test Agent",
            api_url="https://test.local",
        )
    # Replace _request with a fresh MagicMock for assertions.
    c._request = MagicMock(return_value={"ok": True})
    return c


class TestMCPMethods:
    def test_register_mcp_server_posts_to_correct_url_with_required_fields(self):
        c = _client_with_mock()
        c.register_mcp_server(server_name="srv-a", display_name="A", governance_enabled=True)
        call = c._request.call_args
        assert call.args[0] == "POST"
        assert call.args[1] == "/api/registry/mcp-servers"
        body = call.kwargs["data"]
        assert body["server_name"] == "srv-a"
        assert body["display_name"] == "A"
        assert body["governance_enabled"] is True
        assert body["transport_type"] == "stdio"

    def test_register_mcp_server_omits_unset_optionals(self):
        c = _client_with_mock()
        c.register_mcp_server(server_name="srv-b")
        body = c._request.call_args.kwargs["data"]
        for k in ("display_name", "description", "server_url",
                  "connection_config", "auto_approve_tools",
                  "blocked_tools", "tool_risk_overrides"):
            assert k not in body, f"unset optional {k} should not be sent"

    @pytest.mark.parametrize("bad", ["", "   ", None])
    def test_register_mcp_server_rejects_empty_name(self, bad):
        c = _client_with_mock()
        with pytest.raises(ValidationError):
            c.register_mcp_server(server_name=bad)
        c._request.assert_not_called()

    def test_list_mcp_servers_uses_get(self):
        c = _client_with_mock()
        c.list_mcp_servers()
        assert c._request.call_args.args == ("GET", "/api/registry/mcp-servers")

    def test_get_mcp_server_substitutes_name(self):
        c = _client_with_mock()
        c.get_mcp_server("srv-x")
        assert c._request.call_args.args == ("GET", "/api/registry/mcp-servers/srv-x")

    def test_activate_posts_no_body(self):
        c = _client_with_mock()
        c.activate_mcp_server("srv-x")
        assert c._request.call_args.args == ("POST", "/api/registry/mcp-servers/srv-x/activate")

    def test_deactivate_with_reason_sends_body(self):
        c = _client_with_mock()
        c.deactivate_mcp_server("srv-x", reason="incident response")
        call = c._request.call_args
        assert call.args == ("POST", "/api/registry/mcp-servers/srv-x/deactivate")
        assert call.kwargs["data"] == {"reason": "incident response"}

    def test_deactivate_without_reason_sends_no_data(self):
        c = _client_with_mock()
        c.deactivate_mcp_server("srv-x")
        call = c._request.call_args
        assert call.args == ("POST", "/api/registry/mcp-servers/srv-x/deactivate")
        assert call.kwargs["data"] is None

    def test_delete_mcp_server_uses_delete(self):
        c = _client_with_mock()
        c.delete_mcp_server("srv-x")
        assert c._request.call_args.args == ("DELETE", "/api/registry/mcp-servers/srv-x")

    def test_scan_mcp_network_uses_scan_network_endpoint(self):
        c = _client_with_mock()
        c.scan_mcp_network()
        # Must NOT hit /api/discovery/mcp/scan (which requires source_id body)
        assert c._request.call_args.args == ("POST", "/api/authorization/mcp-discovery/scan-network")

    def test_get_mcp_health_uses_health_monitor(self):
        c = _client_with_mock()
        c.get_mcp_health()
        assert c._request.call_args.args == ("GET", "/api/authorization/mcp-discovery/health-monitor")


class TestKillSwitch:
    def test_trigger_posts_with_org_id_substitution(self):
        c = _client_with_mock()
        c.trigger_kill_switch(organization_id=44, reason="incident triage SOC ticket #4451")
        call = c._request.call_args
        assert call.args == ("POST", "/api/billing/kill-switch/44/trigger")
        assert call.kwargs["data"] == {"reason": "incident triage SOC ticket #4451"}

    def test_release_posts_with_org_id_substitution(self):
        c = _client_with_mock()
        c.release_kill_switch(organization_id=44, reason="all clear after incident response")
        call = c._request.call_args
        assert call.args == ("POST", "/api/billing/kill-switch/44/release")
        assert call.kwargs["data"]["reason"].startswith("all clear")

    @pytest.mark.parametrize("bad", ["", "too short", "x" * 9])
    def test_trigger_rejects_short_reason_client_side(self, bad):
        c = _client_with_mock()
        with pytest.raises(ValidationError, match="at least 10 characters"):
            c.trigger_kill_switch(organization_id=44, reason=bad)
        c._request.assert_not_called()

    @pytest.mark.parametrize("bad", [0, -1, "44", 1.5])
    def test_trigger_rejects_invalid_org_id(self, bad):
        c = _client_with_mock()
        with pytest.raises(ValidationError):
            c.trigger_kill_switch(organization_id=bad, reason="legitimate reason here")
        c._request.assert_not_called()

    def test_release_rejects_short_reason_client_side(self):
        c = _client_with_mock()
        with pytest.raises(ValidationError, match="at least 10 characters"):
            c.release_kill_switch(organization_id=44, reason="short")


class TestOrchestration:
    def test_register_topology_validates_workers(self):
        c = _client_with_mock()
        with pytest.raises(ValidationError, match="1..20"):
            c.register_topology("orch", [])
        with pytest.raises(ValidationError, match="1..20"):
            c.register_topology("orch", ["a"] * 21)
        c._request.assert_not_called()

    def test_register_topology_rejects_duplicates(self):
        c = _client_with_mock()
        with pytest.raises(ValidationError, match="[Dd]uplicate"):
            c.register_topology("orch", ["w1", "w1", "w2"])
        c._request.assert_not_called()

    def test_register_topology_happy_path(self):
        c = _client_with_mock()
        c.register_topology("orch", ["w1", "w2"])
        call = c._request.call_args
        assert call.args == ("POST", "/api/v1/orchestration/topology")
        assert call.kwargs["data"] == {
            "orchestrator_agent_id": "orch",
            "worker_agent_ids": ["w1", "w2"],
        }

    def test_register_mcp_topology_rejects_non_int(self):
        c = _client_with_mock()
        with pytest.raises(ValidationError, match="integer"):
            c.register_mcp_topology("orch", ["1", "2"])
        c._request.assert_not_called()

    def test_register_mcp_topology_rejects_duplicates(self):
        c = _client_with_mock()
        with pytest.raises(ValidationError, match="[Dd]uplicate"):
            c.register_mcp_topology("orch", [1, 1, 2])

    def test_register_mcp_topology_happy_path(self):
        c = _client_with_mock()
        c.register_mcp_topology("orch", [21, 22])
        call = c._request.call_args
        assert call.args == ("POST", "/api/v1/orchestration/topology/mcp")
        assert call.kwargs["data"] == {
            "orchestrator_agent_id": "orch",
            "mcp_server_ids": [21, 22],
        }

    def test_cascade_kill_default_dry_run_true(self):
        """SAFETY: caller must explicitly opt-in to execute. Defaults to dry_run."""
        c = _client_with_mock()
        c.cascade_kill("orch-1", reason="SOC incident IR-9912 — investigating")
        call = c._request.call_args
        assert call.args == ("POST", "/api/v1/orchestration/cascade-kill/orch-1")
        # confirm == not dry_run; default dry_run=True ⇒ confirm=False
        assert call.kwargs["data"]["confirm"] is False

    def test_cascade_kill_explicit_execute(self):
        c = _client_with_mock()
        c.cascade_kill("orch-1", reason="confirmed compromise — execute", dry_run=False)
        assert c._request.call_args.kwargs["data"]["confirm"] is True

    @pytest.mark.parametrize("bad_reason", ["", "  ", None])
    def test_cascade_kill_rejects_empty_reason(self, bad_reason):
        c = _client_with_mock()
        with pytest.raises(ValidationError):
            c.cascade_kill("orch-1", reason=bad_reason)
        c._request.assert_not_called()

    def test_get_orchestration_session_substitutes_id(self):
        c = _client_with_mock()
        c.get_orchestration_session("sess-abc-123")
        assert c._request.call_args.args == (
            "GET", "/api/v1/orchestration/sessions/sess-abc-123"
        )

    def test_get_orchestration_stats_uses_correct_endpoint(self):
        c = _client_with_mock()
        c.get_orchestration_stats()
        assert c._request.call_args.args == ("GET", "/api/v1/orchestration/stats")


class TestOutputFilter:
    def test_get_config_uses_get(self):
        c = _client_with_mock()
        c.get_output_filter_config()
        assert c._request.call_args.args == ("GET", "/api/v1/output-filter/config")

    def test_get_findings_with_filters(self):
        c = _client_with_mock()
        c.get_output_findings(limit=25, offset=10, category="pii", severity="HIGH")
        call = c._request.call_args
        assert call.args == ("GET", "/api/v1/output-filter/findings")
        assert call.kwargs["params"] == {
            "limit": 25, "offset": 10, "category": "pii", "severity": "HIGH"
        }

    @pytest.mark.parametrize("bad_limit", [0, -1, 101, 1000])
    def test_get_findings_rejects_invalid_limit(self, bad_limit):
        c = _client_with_mock()
        with pytest.raises(ValidationError):
            c.get_output_findings(limit=bad_limit)
        c._request.assert_not_called()

    def test_get_findings_for_action_substitutes_id(self):
        c = _client_with_mock()
        c.get_output_findings_for_action(123)
        assert c._request.call_args.args == ("GET", "/api/v1/output-filter/findings/123")

    @pytest.mark.parametrize("bad", [0, -1, "1", 1.5])
    def test_get_findings_for_action_rejects_invalid_id(self, bad):
        c = _client_with_mock()
        with pytest.raises(ValidationError):
            c.get_output_findings_for_action(bad)
        c._request.assert_not_called()

    def test_scan_output_required_body(self):
        c = _client_with_mock()
        c.scan_output(content="contains SSN 123-45-6789", agent_id="agent-x", action_id=456)
        call = c._request.call_args
        assert call.args == ("POST", "/api/v1/output-filter/scan")
        assert call.kwargs["data"] == {
            "content": "contains SSN 123-45-6789",
            "agent_id": "agent-x",
            "action_id": 456,
        }

    def test_scan_output_rejects_missing_agent_id(self):
        c = _client_with_mock()
        with pytest.raises(ValidationError):
            c.scan_output(content="x", agent_id="")
        c._request.assert_not_called()


class TestSupplyChain:
    def test_list_components_default_params(self):
        c = _client_with_mock()
        c.list_supply_chain_components()
        call = c._request.call_args
        assert call.args == ("GET", "/api/v1/supply-chain/components")
        params = call.kwargs["params"]
        assert params["active_only"] is True
        assert params["limit"] == 100
        assert params["offset"] == 0
        assert "component_type" not in params  # unset filter not sent

    def test_list_components_with_filters(self):
        c = _client_with_mock()
        c.list_supply_chain_components(
            component_type="library", risk_level="HIGH",
            has_vulnerabilities=True, active_only=False,
            limit=50, offset=25,
        )
        params = c._request.call_args.kwargs["params"]
        assert params["component_type"] == "library"
        assert params["risk_level"] == "HIGH"
        assert params["has_vulnerabilities"] is True
        assert params["active_only"] is False
        assert params["limit"] == 50

    def test_get_stats(self):
        c = _client_with_mock()
        c.get_supply_chain_stats()
        assert c._request.call_args.args == ("GET", "/api/v1/supply-chain/stats")

    def test_get_impact_substitutes_pk(self):
        c = _client_with_mock()
        c.get_supply_chain_impact(42)
        assert c._request.call_args.args == ("GET", "/api/v1/supply-chain/impact/42")

    @pytest.mark.parametrize("bad", [0, -1, "1", 1.5])
    def test_impact_rejects_invalid_id(self, bad):
        c = _client_with_mock()
        with pytest.raises(ValidationError):
            c.get_supply_chain_impact(bad)

    def test_cve_sync_status(self):
        c = _client_with_mock()
        c.get_cve_sync_status()
        assert c._request.call_args.args == ("GET", "/api/v1/supply-chain/sync/status")

    def test_alerts_polling_filters_by_type(self):
        c = _client_with_mock()
        c.get_supply_chain_alerts(limit=20, acknowledged=False)
        call = c._request.call_args
        assert call.args == ("GET", "/api/alerts")
        assert call.kwargs["params"]["type"] == "supply_chain_cve"
        assert call.kwargs["params"]["limit"] == 20
        assert call.kwargs["params"]["acknowledged"] is False


# ---------------------------------------------------------------------------
# B6 — AuthorizationDecision typed fields + back-compat
# ---------------------------------------------------------------------------

@pytest.fixture
def live_response_payload() -> Dict[str, Any]:
    """Mirrors a real action_submit response from rev 954 (post-G-P0-01/02)."""
    return {
        "action_id": 5095,
        "status": "pending_approval",
        "decision": "pending",
        "risk_score": 49,
        "risk_level": "medium",
        "cvss_score": 4.3,
        "cvss_severity": "MEDIUM",
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:N/A:N",
        "mitre_tactic": "Execution",
        "mitre_technique": "T1059",
        "nist_control": "SI-3",
        "nist_description": "Malicious Code Protection",
        "code_analysis": {"analyzed": True, "blocked": False},
        "prompt_security": {"analyzed": True, "blocked": False},
        "mcp_governance": {
            "server_registered": True, "server_active": True,
            "governance_enabled": True, "tool_blocked": False,
            "server_name": "dogfood-sim001-test",
        },
        "model_governance": {
            "registry_checked": False,
            "reason": "No model_id provided and agent has no linked model",
        },
        "processing_time_ms": 1602,
        "alert_triggered": False,
        "alert_id": None,
        "workflow_id": None,
        "policy_decision": "require_approval",
        "matched_policies": 0,
        "matched_smart_rules": 0,
        "output_scan_result": "not_scanned",
        "output_findings_count": None,
        "correlation_id": "action_20260427_015057_3248b818",
        "thresholds": {
            "auto_approve_below": 50, "max_risk_threshold": 80,
            "agent_type": "supervised", "is_registered": True,
        },
        "metadata": {"existing_caller_key": "must-survive"},
    }


class TestAuthorizationDecisionPromotedFields:
    def test_typed_fields_populated(self, live_response_payload):
        d = AuthorizationDecision.from_dict(live_response_payload)
        assert d.cvss_score == 4.3
        assert d.cvss_severity == "MEDIUM"
        assert d.cvss_vector.startswith("CVSS:3.1/")
        assert d.mitre_tactic == "Execution"
        assert d.mitre_technique == "T1059"
        assert d.nist_control == "SI-3"
        assert d.nist_description == "Malicious Code Protection"
        assert d.processing_time_ms == 1602
        assert d.alert_triggered is False
        assert d.policy_decision == "require_approval"
        assert d.matched_policies == 0
        assert d.matched_smart_rules == 0
        assert d.output_scan_result == "not_scanned"
        assert d.correlation_id == "action_20260427_015057_3248b818"
        assert d.thresholds["auto_approve_below"] == 50

    def test_mcp_and_model_governance_populated(self, live_response_payload):
        d = AuthorizationDecision.from_dict(live_response_payload)
        assert d.mcp_governance["server_name"] == "dogfood-sim001-test"
        assert d.mcp_governance["server_registered"] is True
        assert d.mcp_governance["server_active"] is True
        assert d.model_governance["registry_checked"] is False

    def test_metadata_back_compat_preserved(self, live_response_payload):
        """ZERO BREAKING CHANGE: pre-2.5.0 callers reading metadata still work."""
        d = AuthorizationDecision.from_dict(live_response_payload)
        # Existing metadata keys preserved untouched
        assert d.metadata["existing_caller_key"] == "must-survive"
        # New typed fields ALSO mirrored into metadata so old callers
        # who used decision.metadata["cvss_score"] keep working.
        assert d.metadata["cvss_score"] == 4.3
        assert d.metadata["mcp_governance"]["server_name"] == "dogfood-sim001-test"
        assert d.metadata["correlation_id"] == "action_20260427_015057_3248b818"

    def test_caller_metadata_value_not_clobbered_by_promotion(self):
        """If caller's metadata already has cvss_score with a different value,
        the original wins — promotion does not overwrite explicit metadata."""
        payload = {
            "action_id": "1", "decision": "allowed",
            "cvss_score": 4.3,
            "metadata": {"cvss_score": 9.9},
        }
        d = AuthorizationDecision.from_dict(payload)
        assert d.cvss_score == 4.3              # typed field = top-level
        assert d.metadata["cvss_score"] == 9.9  # metadata caller value wins

    def test_action_id_coerced_to_string_when_int(self):
        """Submit returns int id; dataclass field is str → coerce safely."""
        d = AuthorizationDecision.from_dict({"action_id": 5095, "decision": "pending"})
        assert d.action_id == "5095"
        assert isinstance(d.action_id, str)

    def test_missing_promoted_fields_are_none(self):
        """A minimal payload (no governance fields) yields None on those attrs."""
        d = AuthorizationDecision.from_dict({"action_id": "x", "decision": "allowed"})
        assert d.cvss_score is None
        assert d.mcp_governance is None
        assert d.model_governance is None
        assert d.correlation_id is None
        # Decision still resolves
        assert d.decision == Decision.ALLOWED

    def test_decision_mapping_preserved(self):
        """Pre-2.5.0 decision-mapping rules continue to work."""
        # legacy "approved" → ALLOWED
        d = AuthorizationDecision.from_dict({"action_id": "x", "status": "approved"})
        assert d.decision == Decision.ALLOWED
        # legacy "denied" → DENIED
        d = AuthorizationDecision.from_dict({"action_id": "x", "decision": "denied"})
        assert d.decision == Decision.DENIED


# ---------------------------------------------------------------------------
# Source-level guards (catch silent regressions)
# ---------------------------------------------------------------------------

class TestSourceGuards:
    def test_cascade_kill_default_is_dry_run(self):
        sig = inspect.signature(AscendClient.cascade_kill)
        assert sig.parameters["dry_run"].default is True, (
            "SAFETY: cascade_kill must default dry_run=True to prevent "
            "accidental mass-blocking"
        )

    def test_kill_switch_methods_validate_reason_length(self):
        for method_name in ("trigger_kill_switch", "release_kill_switch"):
            src = inspect.getsource(getattr(AscendClient, method_name))
            assert "len(reason) < 10" in src, (
                f"{method_name} must enforce min reason length client-side"
            )

    def test_topology_register_caps_at_20_workers(self):
        src = inspect.getsource(AscendClient.register_topology)
        assert "1 <= len(worker_agent_ids) <= 20" in src

    def test_no_method_swallows_exceptions(self):
        """SDK 2.5.0 methods must surface exceptions, not silently return."""
        for name in NEW_METHODS:
            method = getattr(AscendClient, name)
            src = inspect.getsource(method)
            # Methods may raise ValidationError but must not have bare
            # `except Exception: pass` style swallowing.
            assert "except Exception:\n        pass" not in src, (
                f"{name} appears to swallow exceptions silently"
            )
