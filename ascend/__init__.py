"""
ASCEND SDK for Python
=====================

Enterprise-grade authorization SDK for AI agent governance.

Quick Start (v2.1):
    from ascend import AscendClient, FailMode

    client = AscendClient(
        api_key="owkai_...",
        agent_id="agent-001",
        agent_name="My AI Agent",
        fail_mode=FailMode.CLOSED
    )

    decision = client.evaluate_action(
        action_type="data_access",
        resource="customer_data",
        parameters={"query": "SELECT * FROM customers"}
    )

    if decision.decision == Decision.ALLOWED:
        result = execute_query()
        client.log_action_completed(decision.action_id, result)

MCP Integration:
    from ascend import AscendClient
    from ascend.mcp import mcp_governance

    @mcp_server.tool()
    @mcp_governance(client, action_type="database.query", resource="prod_db")
    async def query_database(sql: str):
        return db.execute(sql)

Security Standards:
    - SOC 2 Type II Compliant (CC6.1)
    - PCI-DSS 8.3 (MFA), 8.2 (API Key Management)
    - HIPAA 164.312(e) (Transmission Security)
    - NIST AI RMF (Govern, Map, Measure, Manage)
    - NIST 800-63B (Authentication)

Version: 2.3.0
"""

__version__ = "2.3.0"
__author__ = "ASCEND by OW-AI"

# Core client (v2.1)
from .client import AscendClient, FailMode, CircuitBreaker, AscendLogger

# Legacy client alias (v1.0 - deprecated)
from .client import OWKAIClient

# Agent wrapper
from .agent import AuthorizedAgent

# Models
from .models import (
    AgentAction,
    ActionType,
    DecisionStatus,
    RiskLevel,
    AuthorizationDecision,
    Decision,
    KillSwitchStatus,
    PolicyEvaluationResult,
    ResourceClassification,
    AuditEvent,
    AuditLogResponse,
    AgentHealthStatus,
    Webhook,
    WebhookTestResult,
    BulkActionResult,
    BulkEvaluationResult,
)

# Exceptions
from .exceptions import (
    OWKAIError,
    AuthenticationError,
    AuthorizationError,
    TimeoutError,
    RateLimitError,
    ValidationError,
    ConnectionError,
    CircuitBreakerOpen,
    ConfigurationError,
    KillSwitchError,
)

# MCP Governance
from .mcp import (
    mcp_governance,
    require_governance,
    high_risk_action,
    MCPGovernanceConfig,
    MCPGovernanceMiddleware,
    MCPKillSwitchConsumer,
)

__all__ = [
    # Core client (v2.1)
    "AscendClient",
    "FailMode",
    "CircuitBreaker",
    "AscendLogger",

    # Legacy (deprecated)
    "OWKAIClient",

    # Agent
    "AuthorizedAgent",

    # Models
    "AgentAction",
    "ActionType",
    "DecisionStatus",
    "RiskLevel",
    "AuthorizationDecision",
    "Decision",
    "KillSwitchStatus",
    "PolicyEvaluationResult",
    "ResourceClassification",
    "AuditEvent",
    "AuditLogResponse",
    "AgentHealthStatus",
    "Webhook",
    "WebhookTestResult",
    "BulkActionResult",
    "BulkEvaluationResult",

    # Exceptions
    "OWKAIError",
    "AuthenticationError",
    "AuthorizationError",
    "TimeoutError",
    "RateLimitError",
    "ValidationError",
    "ConnectionError",
    "CircuitBreakerOpen",
    "ConfigurationError",
    "KillSwitchError",

    # MCP Governance
    "mcp_governance",
    "require_governance",
    "high_risk_action",
    "MCPGovernanceConfig",
    "MCPGovernanceMiddleware",
    "MCPKillSwitchConsumer",
]
