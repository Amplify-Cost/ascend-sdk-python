"""
OW-AI Enterprise SDK

Enterprise-grade Python SDK for AI Agent Authorization and Governance.

Features:
- API key authentication with SHA-256 security
- Agent action submission and approval workflows
- Real-time risk assessment integration
- boto3 auto-patching for AWS governance
- Comprehensive audit logging

Compliance:
- SOX, PCI-DSS, HIPAA, GDPR compliant
- NIST SP 800-53 control mapping
- MITRE ATT&CK framework integration

Example:
    from owkai import OWKAIClient

    client = OWKAIClient(api_key="owkai_admin_...")

    # Submit action for approval
    result = client.execute_action(
        action_type="database_write",
        description="UPDATE users SET status='active'",
        tool_name="postgresql"
    )

    # Wait for approval
    if result.requires_approval:
        status = client.wait_for_approval(result.action_id)

Copyright (c) 2025 OW-AI Enterprise
"""

__version__ = "0.1.0"
__author__ = "OW-AI Enterprise"
__email__ = "sdk@owkai.com"

from owkai.client import OWKAIClient, AsyncOWKAIClient
from owkai.models import (
    ActionResult,
    ActionStatus,
    RiskLevel,
    ApprovalStatus,
)
from owkai.exceptions import (
    OWKAIError,
    OWKAIAuthenticationError,
    OWKAIRateLimitError,
    OWKAIApprovalTimeoutError,
    OWKAIActionRejectedError,
    OWKAIValidationError,
    OWKAINetworkError,
)

__all__ = [
    # Version
    "__version__",
    # Clients
    "OWKAIClient",
    "AsyncOWKAIClient",
    # Models
    "ActionResult",
    "ActionStatus",
    "RiskLevel",
    "ApprovalStatus",
    # Exceptions
    "OWKAIError",
    "OWKAIAuthenticationError",
    "OWKAIRateLimitError",
    "OWKAIApprovalTimeoutError",
    "OWKAIActionRejectedError",
    "OWKAIValidationError",
    "OWKAINetworkError",
]
