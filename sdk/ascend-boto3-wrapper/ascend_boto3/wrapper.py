"""
Boto3 Governance Wrapper
=========================

Patches boto3 to add transparent governance for AWS SDK operations.

This module monkey-patches boto3's client factory to intercept
AWS API calls and route them through Ascend governance.

Usage:
    from ascend_boto3 import enable_governance

    # Enable governance globally
    enable_governance(api_key="ascend_prod_xxx")

    # All subsequent boto3 calls go through governance
    import boto3
    s3 = boto3.client('s3')
    s3.delete_bucket(Bucket='my-bucket')  # Requires approval

Created: 2025-12-09
"""

import os
import logging
import functools
from typing import Optional, Dict, Any, Callable, Set
from dataclasses import dataclass, field

from .risk_classifier import classify_operation_risk, RiskLevel

logger = logging.getLogger(__name__)

# Track governance state
_governance_enabled = False
_original_client_factory = None
_config: Optional["GovernanceConfig"] = None


@dataclass
class GovernanceConfig:
    """
    Configuration for boto3 governance wrapper.

    Attributes:
        api_key: Ascend API key for authentication
        base_url: Ascend API base URL
        agent_id: Identifier for this agent (auto-generated if not provided)
        agent_name: Human-readable agent name
        auto_approve_low_risk: Auto-approve LOW risk operations (default: True)
        auto_approve_medium_risk: Auto-approve MEDIUM risk operations (default: False)
        timeout: Request timeout in seconds
        bypass_services: Set of services to bypass governance (e.g., {"cloudwatch"})
        bypass_operations: Set of operations to bypass (e.g., {"s3.list_buckets"})
        dry_run: Log governance decisions without enforcing (default: False)
    """
    api_key: str
    base_url: str = "https://pilot.owkai.app"
    agent_id: Optional[str] = None
    agent_name: str = "AWS Boto3 Agent"
    auto_approve_low_risk: bool = True
    auto_approve_medium_risk: bool = False
    timeout: int = 30
    bypass_services: Set[str] = field(default_factory=set)
    bypass_operations: Set[str] = field(default_factory=set)
    dry_run: bool = False

    def __post_init__(self):
        if not self.agent_id:
            import uuid
            self.agent_id = f"boto3-agent-{uuid.uuid4().hex[:8]}"

        # Normalize bypass sets
        self.bypass_services = {s.lower() for s in self.bypass_services}
        self.bypass_operations = {o.lower() for o in self.bypass_operations}


def _should_bypass(service: str, operation: str, config: GovernanceConfig) -> bool:
    """Check if operation should bypass governance."""
    service = service.lower()
    operation = operation.lower()
    full_op = f"{service}.{operation}"

    if service in config.bypass_services:
        logger.debug(f"Bypassing governance for service: {service}")
        return True

    if full_op in config.bypass_operations:
        logger.debug(f"Bypassing governance for operation: {full_op}")
        return True

    return False


def _evaluate_governance(
    service: str,
    operation: str,
    params: Dict[str, Any],
    config: GovernanceConfig
) -> Dict[str, Any]:
    """
    Evaluate operation through Ascend governance.

    Returns:
        dict with keys:
            - approved: bool
            - action_id: str (if submitted)
            - risk_score: int
            - risk_level: str
            - reason: str
    """
    risk_score, risk_level = classify_operation_risk(service, operation, params)

    # Check auto-approve rules
    if risk_level == RiskLevel.LOW and config.auto_approve_low_risk:
        return {
            "approved": True,
            "action_id": None,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "reason": "Auto-approved (low risk)"
        }

    if risk_level == RiskLevel.MEDIUM and config.auto_approve_medium_risk:
        return {
            "approved": True,
            "action_id": None,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "reason": "Auto-approved (medium risk)"
        }

    # Submit to Ascend for governance decision
    try:
        # Import SDK here to avoid circular dependency
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        try:
            from ascend import AscendClient, AgentAction
        except ImportError:
            # SDK not installed - use direct API call
            return _evaluate_via_api(service, operation, params, config, risk_score, risk_level)

        client = AscendClient(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )

        action = AgentAction(
            agent_id=config.agent_id,
            agent_name=config.agent_name,
            action_type="aws_api_call",
            resource=f"{service}:{operation}",
            resource_id=_extract_resource_id(service, operation, params),
            action_details={
                "service": service,
                "operation": operation,
                "params": _sanitize_params(params),
                "risk_score": risk_score,
                "risk_level": risk_level.value,
            }
        )

        result = client.submit_action(action)

        return {
            "approved": result.is_approved(),
            "action_id": result.action_id,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "reason": result.reason or f"Risk level: {risk_level.value}"
        }

    except Exception as e:
        logger.error(f"Governance evaluation failed: {e}")
        # Fail closed for high/critical risk
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return {
                "approved": False,
                "action_id": None,
                "risk_score": risk_score,
                "risk_level": risk_level.value,
                "reason": f"Governance evaluation failed: {e}"
            }
        # Fail open for low/medium risk
        return {
            "approved": True,
            "action_id": None,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "reason": f"Governance unavailable, auto-approved (low/medium risk)"
        }


def _evaluate_via_api(
    service: str,
    operation: str,
    params: Dict[str, Any],
    config: GovernanceConfig,
    risk_score: int,
    risk_level: RiskLevel
) -> Dict[str, Any]:
    """Evaluate via direct API call when SDK not available."""
    import requests

    try:
        response = requests.post(
            f"{config.base_url}/api/v1/actions/submit",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "X-API-Key": config.api_key,
                "Content-Type": "application/json"
            },
            json={
                "agent_id": config.agent_id,
                "agent_name": config.agent_name,
                "action_type": f"{service}.{operation}",
                "description": f"Boto3 {service}.{operation} operation",
                "tool_name": service,
                "parameters": _sanitize_params(params),
                "risk_score": risk_score,
            },
            timeout=config.timeout
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "approved": data.get("status") == "approved",
                "action_id": str(data.get("id")),
                "risk_score": risk_score,
                "risk_level": risk_level.value,
                "reason": data.get("summary", "")
            }
        else:
            raise Exception(f"API returned {response.status_code}")

    except Exception as e:
        logger.error(f"Direct API evaluation failed: {e}")
        raise


def _extract_resource_id(service: str, operation: str, params: Dict[str, Any]) -> Optional[str]:
    """Extract resource identifier from operation parameters."""
    # Common resource ID parameter names
    id_params = [
        "Bucket", "Key", "TableName", "QueueUrl", "TopicArn",
        "FunctionName", "InstanceId", "InstanceIds", "DBInstanceIdentifier",
        "RoleName", "UserName", "PolicyArn", "SecretId", "KeyId",
        "StackName", "ClusterIdentifier"
    ]

    for param in id_params:
        if param in params:
            value = params[param]
            if isinstance(value, list):
                return ",".join(str(v) for v in value[:3])  # Limit list length
            return str(value)

    return None


def _sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive data from parameters for logging."""
    sensitive_keys = {
        "Password", "Secret", "Token", "Key", "Credentials",
        "AccessKey", "SecretKey", "SessionToken", "AuthToken"
    }

    sanitized = {}
    for key, value in params.items():
        if any(sensitive in key for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_params(value)
        else:
            sanitized[key] = value

    return sanitized


def _create_governed_method(
    original_method: Callable,
    service_name: str,
    operation_name: str
) -> Callable:
    """Create a governed wrapper for a boto3 method."""

    @functools.wraps(original_method)
    def governed_method(*args, **kwargs):
        global _config

        if not _config:
            return original_method(*args, **kwargs)

        # Check bypass rules
        if _should_bypass(service_name, operation_name, _config):
            return original_method(*args, **kwargs)

        # Evaluate governance
        result = _evaluate_governance(service_name, operation_name, kwargs, _config)

        log_msg = (
            f"[Ascend Governance] {service_name}.{operation_name} - "
            f"Risk: {result['risk_level']} ({result['risk_score']}) - "
            f"{'APPROVED' if result['approved'] else 'DENIED'}"
        )

        if result['approved']:
            logger.info(log_msg)
            if not _config.dry_run:
                return original_method(*args, **kwargs)
            else:
                logger.info(f"[DRY RUN] Would execute: {service_name}.{operation_name}")
                return None
        else:
            logger.warning(log_msg)
            raise PermissionError(
                f"Operation {service_name}.{operation_name} denied by Ascend governance. "
                f"Reason: {result['reason']}. "
                f"Action ID: {result.get('action_id')}"
            )

    return governed_method


def _create_governed_client(original_client):
    """Wrap a boto3 client with governance."""
    service_name = original_client.meta.service_model.service_name

    # Get all method names
    for method_name in dir(original_client):
        if method_name.startswith('_'):
            continue

        method = getattr(original_client, method_name)
        if callable(method) and hasattr(method, '__name__'):
            try:
                governed = _create_governed_method(method, service_name, method_name)
                setattr(original_client, method_name, governed)
            except Exception as e:
                logger.debug(f"Could not wrap {service_name}.{method_name}: {e}")

    return original_client


def enable_governance(
    api_key: Optional[str] = None,
    base_url: str = "https://pilot.owkai.app",
    agent_id: Optional[str] = None,
    agent_name: str = "AWS Boto3 Agent",
    auto_approve_low_risk: bool = True,
    auto_approve_medium_risk: bool = False,
    bypass_services: Optional[Set[str]] = None,
    bypass_operations: Optional[Set[str]] = None,
    dry_run: bool = False,
    **kwargs
) -> None:
    """
    Enable Ascend governance for boto3 operations.

    This patches boto3's client factory to add governance checks
    to all AWS API calls.

    Args:
        api_key: Ascend API key (or set ASCEND_API_KEY env var)
        base_url: Ascend API URL
        agent_id: Unique identifier for this agent
        agent_name: Human-readable agent name
        auto_approve_low_risk: Auto-approve low risk operations
        auto_approve_medium_risk: Auto-approve medium risk operations
        bypass_services: Services to skip governance (e.g., {"cloudwatch"})
        bypass_operations: Operations to skip (e.g., {"s3.list_buckets"})
        dry_run: Log decisions without enforcing

    Example:
        enable_governance(
            api_key="ascend_prod_xxx",
            bypass_services={"cloudwatch", "logs"},
            auto_approve_low_risk=True
        )
    """
    global _governance_enabled, _original_client_factory, _config

    if _governance_enabled:
        logger.warning("Governance already enabled")
        return

    # Get API key from environment if not provided
    api_key = api_key or os.getenv("ASCEND_API_KEY")
    if not api_key:
        raise ValueError(
            "API key required. Pass api_key parameter or set ASCEND_API_KEY env var."
        )

    _config = GovernanceConfig(
        api_key=api_key,
        base_url=base_url,
        agent_id=agent_id,
        agent_name=agent_name,
        auto_approve_low_risk=auto_approve_low_risk,
        auto_approve_medium_risk=auto_approve_medium_risk,
        bypass_services=bypass_services or set(),
        bypass_operations=bypass_operations or set(),
        dry_run=dry_run,
    )

    # Patch boto3
    try:
        import boto3
        from botocore.client import ClientCreator

        _original_client_factory = ClientCreator.create_client

        def governed_create_client(self, *args, **kwargs):
            client = _original_client_factory(self, *args, **kwargs)
            return _create_governed_client(client)

        ClientCreator.create_client = governed_create_client
        _governance_enabled = True

        logger.info(
            f"Ascend governance enabled for boto3 "
            f"(agent_id={_config.agent_id}, dry_run={dry_run})"
        )

    except ImportError as e:
        raise ImportError(f"boto3 not installed: {e}")


def disable_governance() -> None:
    """
    Disable Ascend governance for boto3 operations.

    Restores original boto3 client factory.
    """
    global _governance_enabled, _original_client_factory, _config

    if not _governance_enabled:
        logger.warning("Governance not enabled")
        return

    try:
        from botocore.client import ClientCreator

        if _original_client_factory:
            ClientCreator.create_client = _original_client_factory

        _governance_enabled = False
        _original_client_factory = None
        _config = None

        logger.info("Ascend governance disabled for boto3")

    except ImportError:
        pass


def is_governance_enabled() -> bool:
    """Check if governance is currently enabled."""
    return _governance_enabled
