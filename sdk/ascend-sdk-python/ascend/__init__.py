"""
Ascend AI SDK
=============

Official Python SDK for Ascend AI Governance Platform.

Provides enterprise-grade authorization and governance for AI agents.

Quick Start:
    from ascend import AscendClient, AgentAction

    # Initialize client
    client = AscendClient(api_key="ascend_prod_...")

    # Submit action
    action = AgentAction(
        agent_id="my-agent",
        agent_name="My Agent",
        action_type="data_access",
        resource="customer_data"
    )
    result = client.submit_action(action)

    if result.is_approved():
        # Execute action
        print("Approved!")

Using AuthorizedAgent:
    from ascend import AuthorizedAgent

    agent = AuthorizedAgent(
        agent_id="bot-001",
        agent_name="Customer Bot"
    )

    # Execute only if authorized
    data = agent.execute_if_authorized(
        action_type="data_access",
        resource="customer_profile",
        execute_fn=lambda: fetch_data()
    )

Features:
- Banking-level security (SOC 2, HIPAA, PCI-DSS compliant)
- Automatic retry with exponential backoff
- Dual authentication headers (Bearer + X-API-Key)
- Comprehensive error handling
- TLS certificate validation
- Request correlation IDs
- API key masking in logs

Documentation: https://docs.ascendai.app/sdk/python
Support: https://ascendai.app/support
"""

from .client import AscendClient
from .agents import AuthorizedAgent
from .models import AgentAction, ActionResult, ListResult, ConnectionStatus
from .exceptions import (
    AscendError,
    AuthenticationError,
    AuthorizationDeniedError,
    RateLimitError,
    TimeoutError,
    ValidationError,
    NetworkError,
    ServerError,
    NotFoundError,
    ConflictError,
)
from .constants import (
    ActionType,
    DecisionStatus,
    RiskLevel,
    SDK_VERSION,
)

__version__ = SDK_VERSION
__all__ = [
    # Main classes
    "AscendClient",
    "AuthorizedAgent",
    # Models
    "AgentAction",
    "ActionResult",
    "ListResult",
    "ConnectionStatus",
    # Exceptions
    "AscendError",
    "AuthenticationError",
    "AuthorizationDeniedError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
    "NetworkError",
    "ServerError",
    "NotFoundError",
    "ConflictError",
    # Enums
    "ActionType",
    "DecisionStatus",
    "RiskLevel",
]
