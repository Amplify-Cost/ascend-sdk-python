"""
OW-AI Enterprise SDK for Python
================================

Enterprise-grade authorization SDK for AI agent governance.

Quick Start:
    from owkai_sdk import OWKAIClient, AuthorizedAgent

    # Initialize client
    client = OWKAIClient(api_key="your-api-key")

    # Create authorized agent
    agent = AuthorizedAgent("agent-001", "My AI Agent", client)

    # Request authorization
    decision = await agent.request_authorization(
        action_type="data_access",
        resource="customer_data"
    )

Security Standards:
    - SOC 2 Type II Compliant
    - PCI-DSS 8.3 (MFA)
    - HIPAA 164.312 (Audit)
    - NIST 800-63B (Authentication)

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "OW-AI Enterprise"

from .client import OWKAIClient
from .agent import AuthorizedAgent
from .models import AgentAction, ActionType, DecisionStatus, RiskLevel
from .exceptions import (
    OWKAIError,
    AuthenticationError,
    AuthorizationError,
    TimeoutError,
    RateLimitError,
    ValidationError
)

__all__ = [
    "OWKAIClient",
    "AuthorizedAgent",
    "AgentAction",
    "ActionType",
    "DecisionStatus",
    "RiskLevel",
    "OWKAIError",
    "AuthenticationError",
    "AuthorizationError",
    "TimeoutError",
    "RateLimitError",
    "ValidationError"
]
