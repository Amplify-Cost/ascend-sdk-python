"""
ASCEND SDK Constants
====================

Centralized constants for API endpoints, defaults, and configuration.
"""

# SDK version
SDK_VERSION = "2.5.0"
USER_AGENT = f"ascend-sdk/{SDK_VERSION} Python"

# Default configuration
DEFAULT_API_URL = "https://pilot.owkai.app"
DEFAULT_TIMEOUT = 5
DEFAULT_MAX_RETRIES = 3
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_DECISION_TIMEOUT = 60
DEFAULT_KILL_SWITCH_INTERVAL = 5
# SDK 2.4.0 — BUG-16 cohort (J3 / J5): heartbeat scheduler interval.
# Heartbeats run on a daemon thread when start_heartbeat() is invoked.
DEFAULT_HEARTBEAT_INTERVAL = 60

# Bulk evaluation limits
MAX_BULK_ACTIONS = 50
DEFAULT_BULK_CONCURRENCY = 5

# API endpoints
API_ENDPOINTS = {
    # Health / system
    "health": "/health",
    "deployment_info": "/api/deployment-info",

    # Actions (v1)
    "submit_action": "/api/v1/actions/submit",
    "action_status": "/api/v1/actions/{action_id}/status",
    "action_details": "/api/v1/actions/{action_id}",
    "action_complete": "/api/agent-action/{action_id}/complete",
    "action_fail": "/api/agent-action/{action_id}/fail",
    "list_actions": "/api/agent-activity",

    # Agent registry
    "register_agent": "/api/registry/agents",
    "deregister_agent": "/api/registry/agents/{agent_id}",

    # Agent health
    "heartbeat": "/api/agents/health/heartbeat",
    "agent_status": "/api/agents/health/{agent_id}",

    # Kill switch
    "kill_switch_status": "/api/sdk/kill-switch/status",

    # Policies
    "evaluate_policy": "/api/governance/policies/evaluate-realtime",

    # Resource classification
    "resource_classifications": "/api/v1/resource-classifications",

    # Audit
    "audit_logs": "/audit/logs",

    # Approvals
    "check_approval": "/api/sdk/approval/{approval_request_id}",

    # Webhooks
    "webhooks_list": "/api/webhooks",
    "webhooks_configure": "/api/webhooks/configure",
    "webhooks_update": "/api/webhooks/{webhook_id}",
    "webhooks_delete": "/api/webhooks/{webhook_id}",
    "webhooks_test": "/api/webhooks/{webhook_id}/test",

    # SDK 2.3.0: Supply chain component registration (FEAT-005)
    "supply_chain_components": "/api/v1/supply-chain/components",

    # SDK 2.3.0: FEAT-001B agent-to-model wiring (via agent update)
    "agent_update": "/api/registry/agents/{agent_id}",

    # SDK 2.3.0: SEC-103 kill-switch HTTP fallback endpoints
    "agent_commands": "/api/registry/agents/{agent_id}/commands",
    "agent_command_ack": "/api/registry/agents/{agent_id}/commands/{command_id}/ack",

    # ========================================================================
    # SDK 2.5.0 — paired with BACKEND-AUTH-001 dual-auth retrofits
    # ========================================================================

    # MCP server CRUD + lifecycle (G-P1-01) — agent_registry_routes.py
    # Prefix: /api/registry (router at agent_registry_routes.py:73)
    "mcp_servers": "/api/registry/mcp-servers",
    "mcp_server_detail": "/api/registry/mcp-servers/{server_name}",
    "mcp_server_activate": "/api/registry/mcp-servers/{server_name}/activate",
    "mcp_server_deactivate": "/api/registry/mcp-servers/{server_name}/deactivate",

    # MCP discovery + health (authorization_routes.py + discovery_routes.py)
    # `mcp_scan` requires a MCPScanRequest body with source_id; not exposed
    # by SDK 2.5.0 (no clean param-less wrapper). `mcp_scan_network` is the
    # parameter-free network scan that matches the SDK's signature intent.
    "mcp_scan": "/api/discovery/mcp/scan",
    "mcp_scan_results": "/api/discovery/mcp/results",
    "mcp_scan_network": "/api/authorization/mcp-discovery/scan-network",
    "mcp_health_monitor": "/api/authorization/mcp-discovery/health-monitor",
    "mcp_server_status": "/api/authorization/mcp-discovery/server-status",

    # Kill-switch trigger / release (G-P1-02) — spend_control_routes.py
    # Prefix: /api/billing
    "kill_switch_trigger": "/api/billing/kill-switch/{organization_id}/trigger",
    "kill_switch_release": "/api/billing/kill-switch/{organization_id}/release",

    # Orchestration management (G-P1-03) — orchestration_topology_routes.py
    # Prefix: /api/v1/orchestration
    "topology_register": "/api/v1/orchestration/topology",
    "topology_mcp_register": "/api/v1/orchestration/topology/mcp",
    "cascade_kill": "/api/v1/orchestration/cascade-kill/{orchestrator_id}",
    "orchestration_session": "/api/v1/orchestration/sessions/{session_id}",
    "orchestration_session_risk": "/api/v1/orchestration/sessions/{session_id}/risk",
    "orchestration_stats": "/api/v1/orchestration/stats",

    # Output filter (G-P1-04) — output_filter_routes.py
    # Prefix: /api/v1/output-filter (declared in router itself)
    "output_filter_config": "/api/v1/output-filter/config",
    "output_filter_findings": "/api/v1/output-filter/findings",
    "output_filter_findings_for_action": "/api/v1/output-filter/findings/{action_id}",
    "output_filter_scan": "/api/v1/output-filter/scan",

    # Supply chain (G-P1-05) — supply_chain_routes.py
    # Prefix: /api/v1/supply-chain
    "supply_chain_components_list": "/api/v1/supply-chain/components",
    "supply_chain_component": "/api/v1/supply-chain/components/{component_pk}",
    "supply_chain_agent_dependencies": "/api/v1/supply-chain/agents/{agent_pk}/dependencies",
    "supply_chain_impact": "/api/v1/supply-chain/impact/{component_pk}",
    "supply_chain_stats": "/api/v1/supply-chain/stats",
    "supply_chain_cve_sync_status": "/api/v1/supply-chain/sync/status",

    # Alerts polling (no SSE/webhook today — see G-P1-05 note)
    # Prefix: /api/alerts
    "alerts_list": "/api/alerts",
}


# ============================================================================
# SDK 2.4.0 — BUG-16 cohort / DOC-DRIFT-CONSTANTS
#
# ActionType is defined in ascend.models (it's an enum, not a constant),
# but public docs imported it from ascend.constants. Preserved here as a
# lazy re-export with a once-per-process DeprecationWarning. Removed in
# ascend-ai-sdk 3.0.0.
# ============================================================================
_warned_constants_aliases: set = set()


def __getattr__(name: str):
    """Lazy deprecated-alias resolver (PEP 562) for ascend.constants."""
    if name == "ActionType":
        if name not in _warned_constants_aliases:
            import warnings
            warnings.warn(
                "Importing ActionType from ascend.constants is deprecated; "
                "use `from ascend import ActionType` "
                "(or `from ascend.models import ActionType`). "
                "This compat re-export will be removed in ascend-ai-sdk 3.0.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            _warned_constants_aliases.add(name)
        from .models import ActionType
        return ActionType
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
