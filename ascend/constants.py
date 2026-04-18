"""
ASCEND SDK Constants
====================

Centralized constants for API endpoints, defaults, and configuration.
"""

# SDK version
SDK_VERSION = "2.3.0"
USER_AGENT = f"ascend-sdk/{SDK_VERSION} Python"

# Default configuration
DEFAULT_API_URL = "https://pilot.owkai.app"
DEFAULT_TIMEOUT = 5
DEFAULT_MAX_RETRIES = 3
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_DECISION_TIMEOUT = 60
DEFAULT_KILL_SWITCH_INTERVAL = 5

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
}
