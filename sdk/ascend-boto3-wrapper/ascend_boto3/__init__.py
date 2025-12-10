"""
ASCEND Boto3 Governance Wrapper
================================

Transparent AI governance for AWS SDK operations.

This package provides automatic governance integration for boto3,
enabling policy-based access control for AWS API calls made by AI agents.

Quick Start:
    from ascend_boto3 import enable_governance

    # Enable governance (patches boto3 globally)
    enable_governance(api_key="ascend_prod_xxx")

    # Use boto3 as normal - governance is automatic
    import boto3
    s3 = boto3.client('s3')
    s3.get_object(Bucket='data', Key='file.csv')  # Low risk - auto-approved
    s3.delete_bucket(Bucket='production')  # High risk - requires approval

Kill-Switch (SEC-103/104/105):
    from ascend_boto3.control import AgentControlClient, create_control_client

    # Create control client for real-time kill-switch
    control = create_control_client(organization_id=34, agent_id="my-agent")
    control.start_polling()  # Start background polling

    # Check before operations
    control.assert_not_blocked()  # Raises if blocked

Features:
    - Zero code changes to existing boto3 code
    - Automatic risk classification by AWS operation
    - Policy-based approval routing
    - Full audit trail
    - Configurable bypass for trusted operations
    - Real-time kill-switch via SQS polling (SEC-103)

Risk Levels:
    - LOW (0-44): Read operations (list_*, get_*, describe_*)
    - MEDIUM (45-69): Write operations (put_*, create_*)
    - HIGH (70-84): Destructive operations (delete_*, terminate_*)
    - CRITICAL (85-100): Administrative operations (delete_bucket, delete_stack)

Created: 2025-12-09
Author: OW-kai Corporation
"""

from .wrapper import (
    enable_governance,
    disable_governance,
    GovernanceConfig,
    is_governance_enabled,
)
from .risk_classifier import (
    classify_operation_risk,
    RiskLevel,
    AWS_OPERATION_RISKS,
)
from .control import (
    AgentControlClient,
    create_control_client,
)

__version__ = "1.1.0"  # SEC-103: Added kill-switch support
__author__ = "OW-kai Corporation"
__all__ = [
    # Governance
    "enable_governance",
    "disable_governance",
    "GovernanceConfig",
    "is_governance_enabled",
    # Risk classification
    "classify_operation_risk",
    "RiskLevel",
    "AWS_OPERATION_RISKS",
    # Kill-switch (SEC-103)
    "AgentControlClient",
    "create_control_client",
]
