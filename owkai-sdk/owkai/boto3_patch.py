"""
OW-AI SDK boto3 Integration

Enterprise-grade boto3 auto-patching for AWS governance.
Intercepts AWS API calls and routes them through OW-AI authorization.

Features:
- Transparent interception of boto3 calls
- Risk-based authorization decisions
- Automatic approval waiting for high-risk operations
- Zero code changes required in existing AWS code

Example:
    from owkai.boto3_patch import enable_governance

    # Enable OW-AI governance for all boto3 calls
    enable_governance(api_key="owkai_admin_...")

    # Now all boto3 calls are monitored
    import boto3
    s3 = boto3.client('s3')
    s3.delete_bucket(Bucket='production-data')  # Requires approval!

Security:
- All AWS operations logged to audit trail
- High-risk operations require explicit approval
- Emergency bypass available for authorized users
"""

import functools
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Set

from owkai.client import OWKAIClient
from owkai.exceptions import (
    OWKAIActionRejectedError,
    OWKAIApprovalTimeoutError,
    OWKAIError,
)
from owkai.models import ActionStatus, RiskLevel
from owkai.utils.logging import get_logger

# Thread-local storage for governance state
_governance_state = threading.local()


@dataclass
class GovernanceConfig:
    """
    Configuration for boto3 governance.

    Attributes:
        api_key: OW-AI API key for authentication
        base_url: OW-AI API base URL
        risk_threshold: Risk score threshold for requiring approval (0-100)
        auto_approve_below: Auto-approve actions below this risk score
        approval_timeout: Seconds to wait for approval
        bypass_read_only: Skip governance for read-only operations
        enabled_services: Set of AWS services to govern (empty = all)
        disabled_services: Set of AWS services to skip
    """

    api_key: str
    base_url: str = "https://pilot.owkai.app"
    risk_threshold: int = 70
    auto_approve_below: int = 30
    approval_timeout: int = 300
    bypass_read_only: bool = True
    enabled_services: Set[str] = field(default_factory=set)
    disabled_services: Set[str] = field(default_factory=lambda: {"sts"})


# AWS service operation risk classifications
AWS_OPERATION_RISK = {
    # S3 operations
    "s3": {
        "delete_bucket": RiskLevel.CRITICAL,
        "delete_objects": RiskLevel.HIGH,
        "put_bucket_policy": RiskLevel.HIGH,
        "put_bucket_acl": RiskLevel.HIGH,
        "put_object": RiskLevel.MEDIUM,
        "copy_object": RiskLevel.MEDIUM,
        "create_bucket": RiskLevel.MEDIUM,
        "get_object": RiskLevel.LOW,
        "list_objects_v2": RiskLevel.LOW,
        "list_buckets": RiskLevel.LOW,
        "head_object": RiskLevel.LOW,
    },
    # EC2 operations
    "ec2": {
        "terminate_instances": RiskLevel.CRITICAL,
        "modify_instance_attribute": RiskLevel.HIGH,
        "create_security_group": RiskLevel.HIGH,
        "authorize_security_group_ingress": RiskLevel.HIGH,
        "revoke_security_group_ingress": RiskLevel.HIGH,
        "run_instances": RiskLevel.MEDIUM,
        "stop_instances": RiskLevel.MEDIUM,
        "start_instances": RiskLevel.LOW,
        "describe_instances": RiskLevel.LOW,
        "describe_security_groups": RiskLevel.LOW,
    },
    # IAM operations
    "iam": {
        "delete_user": RiskLevel.CRITICAL,
        "delete_role": RiskLevel.CRITICAL,
        "attach_role_policy": RiskLevel.CRITICAL,
        "attach_user_policy": RiskLevel.CRITICAL,
        "create_access_key": RiskLevel.HIGH,
        "update_assume_role_policy": RiskLevel.HIGH,
        "create_user": RiskLevel.HIGH,
        "create_role": RiskLevel.HIGH,
        "list_users": RiskLevel.LOW,
        "get_user": RiskLevel.LOW,
        "list_roles": RiskLevel.LOW,
    },
    # RDS operations
    "rds": {
        "delete_db_instance": RiskLevel.CRITICAL,
        "delete_db_cluster": RiskLevel.CRITICAL,
        "modify_db_instance": RiskLevel.HIGH,
        "create_db_snapshot": RiskLevel.MEDIUM,
        "create_db_instance": RiskLevel.MEDIUM,
        "describe_db_instances": RiskLevel.LOW,
    },
    # Lambda operations
    "lambda": {
        "delete_function": RiskLevel.HIGH,
        "update_function_code": RiskLevel.HIGH,
        "update_function_configuration": RiskLevel.MEDIUM,
        "invoke": RiskLevel.MEDIUM,
        "create_function": RiskLevel.MEDIUM,
        "list_functions": RiskLevel.LOW,
        "get_function": RiskLevel.LOW,
    },
    # DynamoDB operations
    "dynamodb": {
        "delete_table": RiskLevel.CRITICAL,
        "update_table": RiskLevel.HIGH,
        "put_item": RiskLevel.MEDIUM,
        "delete_item": RiskLevel.MEDIUM,
        "update_item": RiskLevel.MEDIUM,
        "scan": RiskLevel.LOW,
        "query": RiskLevel.LOW,
        "get_item": RiskLevel.LOW,
    },
    # SecretsManager operations
    "secretsmanager": {
        "delete_secret": RiskLevel.CRITICAL,
        "put_secret_value": RiskLevel.HIGH,
        "create_secret": RiskLevel.HIGH,
        "get_secret_value": RiskLevel.MEDIUM,
        "list_secrets": RiskLevel.LOW,
    },
    # KMS operations
    "kms": {
        "schedule_key_deletion": RiskLevel.CRITICAL,
        "disable_key": RiskLevel.HIGH,
        "create_key": RiskLevel.HIGH,
        "encrypt": RiskLevel.LOW,
        "decrypt": RiskLevel.MEDIUM,
        "list_keys": RiskLevel.LOW,
    },
}

# Read-only operation patterns
READ_ONLY_PREFIXES = {
    "list_",
    "describe_",
    "get_",
    "head_",
    "batch_get_",
}

_logger = get_logger()


def _get_operation_risk(service: str, operation: str) -> RiskLevel:
    """
    Determine risk level for an AWS operation.

    Args:
        service: AWS service name (e.g., 's3', 'ec2')
        operation: Operation name (e.g., 'delete_bucket')

    Returns:
        RiskLevel classification
    """
    service_risks = AWS_OPERATION_RISK.get(service.lower(), {})
    operation_lower = operation.lower()

    # Check specific operation mapping
    if operation_lower in service_risks:
        return service_risks[operation_lower]

    # Default risk based on operation pattern
    if any(operation_lower.startswith(prefix) for prefix in READ_ONLY_PREFIXES):
        return RiskLevel.LOW

    if operation_lower.startswith("delete_"):
        return RiskLevel.HIGH

    if operation_lower.startswith(("create_", "put_", "update_", "modify_")):
        return RiskLevel.MEDIUM

    return RiskLevel.MEDIUM


def _risk_to_score(risk: RiskLevel) -> int:
    """Convert RiskLevel to numeric score."""
    return {
        RiskLevel.LOW: 25,
        RiskLevel.MEDIUM: 55,
        RiskLevel.HIGH: 85,
        RiskLevel.CRITICAL: 95,
    }.get(risk, 55)


def _is_read_only(operation: str) -> bool:
    """Check if operation is read-only."""
    return any(operation.lower().startswith(prefix) for prefix in READ_ONLY_PREFIXES)


def _create_wrapper(
    original_method: Callable,
    service_name: str,
    operation_name: str,
    config: GovernanceConfig,
    client: OWKAIClient,
) -> Callable:
    """
    Create wrapper function for boto3 operation.

    Intercepts the call, submits for authorization, and
    optionally waits for approval before executing.
    """

    @functools.wraps(original_method)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Check if governance is enabled
        if not getattr(_governance_state, "enabled", False):
            return original_method(*args, **kwargs)

        # Check service filters
        if config.enabled_services and service_name not in config.enabled_services:
            return original_method(*args, **kwargs)

        if service_name in config.disabled_services:
            return original_method(*args, **kwargs)

        # Check read-only bypass
        if config.bypass_read_only and _is_read_only(operation_name):
            _logger.debug(
                f"Bypassing governance for read-only: {service_name}.{operation_name}"
            )
            return original_method(*args, **kwargs)

        # Determine risk
        risk_level = _get_operation_risk(service_name, operation_name)
        risk_score = _risk_to_score(risk_level)

        # Auto-approve low risk
        if risk_score < config.auto_approve_below:
            _logger.debug(
                f"Auto-approved low-risk operation: {service_name}.{operation_name} "
                f"(risk={risk_score})"
            )
            return original_method(*args, **kwargs)

        # Build description
        description = f"AWS {service_name}.{operation_name}"
        if kwargs:
            # Include key parameters (sanitized)
            param_info = []
            for key, value in list(kwargs.items())[:3]:
                if isinstance(value, str) and len(value) < 50:
                    param_info.append(f"{key}={value}")
            if param_info:
                description += f" ({', '.join(param_info)})"

        _logger.info(
            f"Submitting for authorization: {service_name}.{operation_name} "
            f"(risk={risk_score})"
        )

        try:
            # Submit action for authorization
            result = client.execute_action(
                action_type=f"aws_{service_name}_{operation_name}",
                description=description,
                tool_name=f"boto3/{service_name}",
                target_system=f"aws:{service_name}",
                risk_context={
                    "aws_service": service_name,
                    "aws_operation": operation_name,
                    "risk_level": risk_level.value,
                    "parameters": {k: str(v)[:100] for k, v in list(kwargs.items())[:5]},
                },
            )

            # Check if approval is required
            if result.requires_approval and risk_score >= config.risk_threshold:
                _logger.info(
                    f"Waiting for approval: action_id={result.action_id}, "
                    f"risk={result.risk_score}"
                )

                try:
                    status = client.wait_for_approval(
                        result.action_id,
                        timeout=config.approval_timeout,
                    )

                    if status.approved:
                        _logger.info(
                            f"Action approved: {result.action_id} by {status.reviewed_by}"
                        )
                    else:
                        raise OWKAIActionRejectedError(
                            f"AWS operation {service_name}.{operation_name} was rejected",
                            action_id=result.action_id,
                            rejection_reason=status.comments,
                            rejected_by=status.reviewed_by,
                        )

                except OWKAIApprovalTimeoutError:
                    _logger.warning(
                        f"Approval timeout for {service_name}.{operation_name}, "
                        f"blocking operation"
                    )
                    raise OWKAIApprovalTimeoutError(
                        f"AWS operation {service_name}.{operation_name} timed out "
                        f"waiting for approval",
                        action_id=result.action_id,
                        timeout=config.approval_timeout,
                    )

            # Execute the original AWS operation
            return original_method(*args, **kwargs)

        except OWKAIError:
            # Re-raise OW-AI errors
            raise
        except Exception as e:
            # Log unexpected errors but don't block
            _logger.error(
                f"Governance error for {service_name}.{operation_name}: {e}, "
                f"allowing operation"
            )
            return original_method(*args, **kwargs)

    return wrapper


def _patch_boto3_client(
    client_class: type,
    service_name: str,
    config: GovernanceConfig,
    owkai_client: OWKAIClient,
) -> None:
    """
    Patch a boto3 client class to add governance.

    Wraps all public methods with authorization checks.
    """
    # Get all public methods
    for attr_name in dir(client_class):
        if attr_name.startswith("_"):
            continue

        attr = getattr(client_class, attr_name, None)
        if not callable(attr):
            continue

        # Create wrapped version
        wrapped = _create_wrapper(attr, service_name, attr_name, config, owkai_client)
        setattr(client_class, attr_name, wrapped)


_original_client_creator: Optional[Callable] = None


def enable_governance(
    api_key: Optional[str] = None,
    *,
    base_url: str = "https://pilot.owkai.app",
    risk_threshold: int = 70,
    auto_approve_below: int = 30,
    approval_timeout: int = 300,
    bypass_read_only: bool = True,
    enabled_services: Optional[Set[str]] = None,
    disabled_services: Optional[Set[str]] = None,
) -> None:
    """
    Enable OW-AI governance for boto3.

    Patches boto3 to intercept all AWS API calls and route them
    through OW-AI authorization workflows.

    Args:
        api_key: OW-AI API key (or set OWKAI_API_KEY env var)
        base_url: OW-AI API base URL
        risk_threshold: Risk score requiring approval (default: 70)
        auto_approve_below: Auto-approve below this score (default: 30)
        approval_timeout: Seconds to wait for approval (default: 300)
        bypass_read_only: Skip governance for read operations (default: True)
        enabled_services: Only govern these services (empty = all)
        disabled_services: Skip these services (default: {"sts"})

    Example:
        from owkai.boto3_patch import enable_governance

        enable_governance(
            api_key="owkai_admin_...",
            risk_threshold=70,
            auto_approve_below=30
        )

        # Now all boto3 calls are monitored
        import boto3
        s3 = boto3.client('s3')

        # Low risk - auto-approved
        s3.list_buckets()

        # High risk - requires approval
        s3.delete_bucket(Bucket='production-data')
    """
    global _original_client_creator

    try:
        import boto3
        import botocore
    except ImportError:
        raise ImportError(
            "boto3 is not installed. Install with: pip install owkai-sdk[boto3]"
        )

    # Create configuration
    config = GovernanceConfig(
        api_key=api_key or "",
        base_url=base_url,
        risk_threshold=risk_threshold,
        auto_approve_below=auto_approve_below,
        approval_timeout=approval_timeout,
        bypass_read_only=bypass_read_only,
        enabled_services=enabled_services or set(),
        disabled_services=disabled_services or {"sts"},
    )

    # Create OW-AI client
    owkai_client = OWKAIClient(api_key=api_key, base_url=base_url)

    # Store original client creator
    if _original_client_creator is None:
        _original_client_creator = boto3.client

    # Create patched client factory
    def patched_client(service_name: str, *args: Any, **kwargs: Any) -> Any:
        # Create original client
        client = _original_client_creator(service_name, *args, **kwargs)

        # Check if service should be governed
        if config.enabled_services and service_name not in config.enabled_services:
            return client

        if service_name in config.disabled_services:
            return client

        # Wrap client methods
        for attr_name in dir(client):
            if attr_name.startswith("_"):
                continue

            attr = getattr(client, attr_name, None)
            if not callable(attr):
                continue

            # Skip meta and exceptions
            if attr_name in ("meta", "exceptions", "can_paginate", "get_paginator"):
                continue

            wrapped = _create_wrapper(
                attr, service_name, attr_name, config, owkai_client
            )
            setattr(client, attr_name, wrapped)

        return client

    # Apply patch
    boto3.client = patched_client

    # Enable governance state
    _governance_state.enabled = True
    _governance_state.config = config
    _governance_state.client = owkai_client

    _logger.info(
        "boto3 governance enabled",
        risk_threshold=risk_threshold,
        auto_approve_below=auto_approve_below,
    )


def disable_governance() -> None:
    """
    Disable OW-AI governance for boto3.

    Restores original boto3 behavior.
    """
    global _original_client_creator

    if _original_client_creator is not None:
        try:
            import boto3

            boto3.client = _original_client_creator
        except ImportError:
            pass

    _governance_state.enabled = False

    _logger.info("boto3 governance disabled")


def is_governance_enabled() -> bool:
    """Check if boto3 governance is currently enabled."""
    return getattr(_governance_state, "enabled", False)


def get_governance_config() -> Optional[GovernanceConfig]:
    """Get current governance configuration."""
    return getattr(_governance_state, "config", None)
