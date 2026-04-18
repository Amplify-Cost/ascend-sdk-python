"""
ASCEND MCP Governance Integration
=================================

Enterprise-grade decorator for integrating ASCEND governance
with MCP (Model Context Protocol) server tools.

Usage:
    from owkai_sdk import AscendClient
    from owkai_sdk.mcp import mcp_governance

    ascend = AscendClient(api_key="...", agent_id="...", agent_name="...")

    @mcp_server.tool()
    @mcp_governance(ascend, action_type="database.query", resource="production_db")
    async def query_database(sql: str):
        return db.execute(sql)

Compliance: SOC 2 CC6.1, HIPAA 164.312(e), PCI-DSS 8.2, NIST AI RMF
"""

from functools import wraps
from typing import Optional, Dict, Any, Callable, Union, List
import asyncio
import time
import logging
import traceback

from .client import AscendClient
from .models import AuthorizationDecision, Decision
from .exceptions import (
    AuthorizationError,
    CircuitBreakerOpen,
    TimeoutError as AscendTimeoutError,
    ConnectionError as AscendConnectionError
)

logger = logging.getLogger("owkai_sdk.mcp")


class MCPGovernanceConfig:
    """Configuration for MCP governance behavior."""

    def __init__(
        self,
        # Approval handling
        wait_for_approval: bool = True,
        approval_timeout_seconds: int = 300,
        approval_poll_interval_seconds: int = 5,

        # Context enrichment
        include_tool_name: bool = True,
        include_arguments: bool = True,
        include_caller_info: bool = True,

        # Error handling
        raise_on_denial: bool = True,
        log_all_decisions: bool = True,

        # Custom callbacks
        on_approval_required: Optional[Callable] = None,
        on_denied: Optional[Callable] = None,
        on_allowed: Optional[Callable] = None,
        on_timeout: Optional[Callable] = None
    ):
        self.wait_for_approval = wait_for_approval
        self.approval_timeout_seconds = approval_timeout_seconds
        self.approval_poll_interval_seconds = approval_poll_interval_seconds
        self.include_tool_name = include_tool_name
        self.include_arguments = include_arguments
        self.include_caller_info = include_caller_info
        self.raise_on_denial = raise_on_denial
        self.log_all_decisions = log_all_decisions
        self.on_approval_required = on_approval_required
        self.on_denied = on_denied
        self.on_allowed = on_allowed
        self.on_timeout = on_timeout


# Default configuration
DEFAULT_CONFIG = MCPGovernanceConfig()


def mcp_governance(
    client: AscendClient,
    action_type: str,
    resource: str,
    config: Optional[MCPGovernanceConfig] = None,
    # Override options
    risk_level: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    require_human_approval: bool = False
) -> Callable:
    """
    Decorator for MCP server tools to enforce ASCEND governance.

    This decorator wraps MCP tool functions to:
    1. Evaluate authorization before execution
    2. Block denied actions
    3. Handle pending approvals (wait or reject)
    4. Log completion/failure after execution
    5. Handle errors gracefully based on fail_mode

    Args:
        client: AscendClient instance for governance calls
        action_type: Type of action (e.g., "database.query", "file.write")
        resource: Resource being accessed (e.g., "production_db", "/etc/config")
        config: Optional MCPGovernanceConfig for custom behavior
        risk_level: Override risk level (low/medium/high/critical)
        metadata: Additional metadata to include in authorization request
        require_human_approval: Force human approval even if policy allows

    Returns:
        Decorated function with governance enforcement

    Example:
        @mcp_server.tool()
        @mcp_governance(
            ascend,
            action_type="database.write",
            resource="production_db",
            risk_level="high",
            require_human_approval=True
        )
        async def delete_records(table: str, where_clause: str):
            return db.execute(f"DELETE FROM {table} WHERE {where_clause}")

    Compliance: SOC 2 CC6.1, NIST AC-3, PCI-DSS 7.1
    """
    cfg = config or DEFAULT_CONFIG

    def decorator(func: Callable) -> Callable:
        # Determine if function is async
        is_async = asyncio.iscoroutinefunction(func)
        tool_name = func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _governed_execution(
                func, args, kwargs, is_async,
                client, action_type, resource, cfg,
                tool_name, risk_level, metadata, require_human_approval
            )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Run async governance in sync context
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    _governed_execution(
                        func, args, kwargs, is_async,
                        client, action_type, resource, cfg,
                        tool_name, risk_level, metadata, require_human_approval
                    )
                )
            finally:
                loop.close()

        # Return appropriate wrapper
        if is_async:
            return async_wrapper
        return sync_wrapper

    return decorator


async def _governed_execution(
    func: Callable,
    args: tuple,
    kwargs: dict,
    is_async: bool,
    client: AscendClient,
    action_type: str,
    resource: str,
    config: MCPGovernanceConfig,
    tool_name: str,
    risk_level: Optional[str],
    metadata: Optional[Dict[str, Any]],
    require_human_approval: bool
) -> Any:
    """Execute a function with ASCEND governance enforcement."""

    start_time = time.time()
    action_id = None
    decision = None

    try:
        # Build context for authorization request
        context = _build_context(
            tool_name, args, kwargs, config, metadata,
            risk_level=risk_level,
            require_human_approval=require_human_approval
        )

        # Build parameters from function arguments
        parameters = _extract_parameters(args, kwargs, func)

        # Request authorization
        logger.info(f"MCP Governance: Evaluating {action_type} on {resource}")

        decision = client.evaluate_action(
            action_type=action_type,
            resource=resource,
            parameters=parameters,
            context=context,
            wait_for_decision=False  # We handle approval waiting ourselves
        )

        action_id = decision.action_id

        if config.log_all_decisions:
            logger.info(
                f"MCP Governance: Decision={decision.decision.value}, "
                f"action_id={action_id}, risk_score={decision.risk_score}"
            )

        # Handle decision
        if decision.decision == Decision.DENIED:
            return await _handle_denied(
                decision, config, action_type, resource, tool_name
            )

        elif decision.decision == Decision.PENDING:
            decision = await _handle_pending(
                client, decision, config, action_type, resource, tool_name
            )

            # Re-check after approval wait
            if decision.decision == Decision.DENIED:
                return await _handle_denied(
                    decision, config, action_type, resource, tool_name
                )
            elif decision.decision == Decision.PENDING:
                # Still pending after timeout
                return await _handle_approval_timeout(
                    decision, config, action_type, resource, tool_name
                )

        # ALLOWED - Execute the function
        if config.on_allowed:
            await _call_callback(config.on_allowed, decision, tool_name)

        # Execute the tool function
        try:
            if is_async:
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Log successful completion
            duration_ms = int((time.time() - start_time) * 1000)
            if action_id:
                try:
                    client.log_action_completed(
                        action_id=action_id,
                        result={"success": True, "has_result": result is not None},
                        duration_ms=duration_ms
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log action completion: {log_error}")

            return result

        except Exception as exec_error:
            # Log failed execution
            duration_ms = int((time.time() - start_time) * 1000)
            if action_id:
                try:
                    client.log_action_failed(
                        action_id=action_id,
                        error=str(exec_error),
                        duration_ms=duration_ms
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log action failure: {log_error}")

            raise

    except (AscendConnectionError, AscendTimeoutError, CircuitBreakerOpen) as e:
        # Handle ASCEND service unavailability
        logger.error(f"MCP Governance: ASCEND unavailable - {e}")

        # Fail mode is handled by client.evaluate_action, but if we get here
        # it means fail_mode=closed, so we should raise
        raise AuthorizationError(
            message=f"ASCEND governance service unavailable: {e}",
            error_code="GOVERNANCE_UNAVAILABLE",
            details={
                "action_type": action_type,
                "resource": resource,
                "tool_name": tool_name,
                "original_error": str(e)
            }
        )

    except AuthorizationError:
        # Re-raise authorization errors
        raise

    except Exception as e:
        # Unexpected errors
        logger.error(f"MCP Governance: Unexpected error - {e}\n{traceback.format_exc()}")
        raise


async def _handle_denied(
    decision: AuthorizationDecision,
    config: MCPGovernanceConfig,
    action_type: str,
    resource: str,
    tool_name: str
) -> None:
    """Handle a denied authorization decision."""

    logger.warning(
        f"MCP Governance: DENIED - {action_type} on {resource} "
        f"(tool: {tool_name}, reason: {decision.reason})"
    )

    if config.on_denied:
        await _call_callback(config.on_denied, decision, tool_name)

    if config.raise_on_denial:
        raise AuthorizationError(
            message=f"Action denied: {decision.reason}",
            error_code="MCP_ACTION_DENIED",
            policy_violations=decision.policy_violations,
            risk_score=decision.risk_score,
            details={
                "action_type": action_type,
                "resource": resource,
                "tool_name": tool_name,
                "action_id": decision.action_id,
                "required_approvers": decision.required_approvers
            }
        )

    return None


async def _handle_pending(
    client: AscendClient,
    decision: AuthorizationDecision,
    config: MCPGovernanceConfig,
    action_type: str,
    resource: str,
    tool_name: str
) -> AuthorizationDecision:
    """Handle a pending approval decision."""

    logger.info(
        f"MCP Governance: PENDING approval - {action_type} on {resource} "
        f"(tool: {tool_name}, approval_id: {decision.approval_request_id})"
    )

    if config.on_approval_required:
        await _call_callback(config.on_approval_required, decision, tool_name)

    if not config.wait_for_approval:
        # Don't wait - return pending decision
        logger.info("MCP Governance: Not waiting for approval (config.wait_for_approval=False)")
        return decision

    # Poll for approval status
    approval_id = decision.approval_request_id
    if not approval_id:
        logger.error("MCP Governance: No approval_request_id in pending decision")
        return decision

    start_time = time.time()
    timeout = config.approval_timeout_seconds
    poll_interval = config.approval_poll_interval_seconds

    logger.info(
        f"MCP Governance: Waiting up to {timeout}s for approval "
        f"(polling every {poll_interval}s)"
    )

    while (time.time() - start_time) < timeout:
        await asyncio.sleep(poll_interval)

        try:
            status = client.check_approval(approval_id)

            # check_approval returns {"approved": bool, "denied": bool, "pending": bool, ...}
            if status.get("approved"):
                logger.info(f"MCP Governance: Approval GRANTED for {approval_id}")
                return AuthorizationDecision(
                    decision=Decision.ALLOWED,
                    action_id=decision.action_id,
                    reason="Approved by human reviewer",
                    risk_score=decision.risk_score,
                    policy_violations=[],
                    conditions=decision.conditions,
                    approval_request_id=approval_id,
                    required_approvers=[],
                    expires_at=decision.expires_at,
                    metadata={"approved_by": status.get("approver")}
                )

            elif status.get("denied"):
                logger.info(f"MCP Governance: Approval REJECTED for {approval_id}")
                return AuthorizationDecision(
                    decision=Decision.DENIED,
                    action_id=decision.action_id,
                    reason=status.get("comments", "Rejected by human reviewer"),
                    risk_score=decision.risk_score,
                    policy_violations=decision.policy_violations,
                    conditions=[],
                    approval_request_id=approval_id,
                    required_approvers=[],
                    expires_at=None,
                    metadata={"rejected_by": status.get("approver")}
                )

            # Still pending
            elapsed = int(time.time() - start_time)
            logger.debug(f"MCP Governance: Still pending after {elapsed}s")

        except Exception as e:
            logger.warning(f"MCP Governance: Error checking approval status: {e}")

    # Timeout reached
    logger.warning(
        f"MCP Governance: Approval timeout ({timeout}s) for {approval_id}"
    )
    return decision


async def _handle_approval_timeout(
    decision: AuthorizationDecision,
    config: MCPGovernanceConfig,
    action_type: str,
    resource: str,
    tool_name: str
) -> None:
    """Handle approval timeout."""

    if config.on_timeout:
        await _call_callback(config.on_timeout, decision, tool_name)

    raise AscendTimeoutError(
        message=f"Approval timeout for action: {action_type} on {resource}",
        error_code="APPROVAL_TIMEOUT",
        timeout_seconds=config.approval_timeout_seconds,
        details={
            "tool_name": tool_name,
            "action_id": decision.action_id,
            "approval_request_id": decision.approval_request_id
        }
    )


def _build_context(
    tool_name: str,
    args: tuple,
    kwargs: dict,
    config: MCPGovernanceConfig,
    additional_metadata: Optional[Dict[str, Any]],
    risk_level: Optional[str] = None,
    require_human_approval: bool = False
) -> Dict[str, Any]:
    """Build context dictionary for authorization request."""

    context = {
        "source": "mcp_server",
        "governance_version": "2.0.0"
    }

    if config.include_tool_name:
        context["tool_name"] = tool_name

    if config.include_arguments:
        # Sanitize arguments (remove sensitive data)
        context["arguments"] = _sanitize_arguments(args, kwargs)

    if additional_metadata:
        context["metadata"] = additional_metadata

    # Add risk level and approval requirements to context
    if risk_level:
        context["risk_level"] = risk_level

    if require_human_approval:
        context["require_human_approval"] = True

    return context


def _extract_parameters(
    args: tuple,
    kwargs: dict,
    func: Callable
) -> Dict[str, Any]:
    """Extract parameters from function arguments."""

    import inspect

    parameters = {}

    # Get function signature
    try:
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        # Map positional args
        for i, arg in enumerate(args):
            if i < len(param_names):
                parameters[param_names[i]] = _serialize_value(arg)

        # Add keyword args
        for key, value in kwargs.items():
            parameters[key] = _serialize_value(value)

    except Exception:
        # Fallback if signature inspection fails
        parameters["args"] = [_serialize_value(a) for a in args]
        parameters["kwargs"] = {k: _serialize_value(v) for k, v in kwargs.items()}

    return parameters


def _serialize_value(value: Any) -> Any:
    """Serialize a value for JSON, handling special types."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    else:
        # Convert to string representation
        return f"<{type(value).__name__}>"


def _sanitize_arguments(args: tuple, kwargs: dict) -> Dict[str, Any]:
    """Sanitize arguments to remove potentially sensitive data."""

    SENSITIVE_KEYS = {
        "password", "secret", "token", "api_key", "apikey",
        "auth", "credential", "private_key", "access_token"
    }

    def sanitize_dict(d: dict) -> dict:
        result = {}
        for key, value in d.items():
            if any(s in key.lower() for s in SENSITIVE_KEYS):
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = sanitize_dict(value)
            elif isinstance(value, str) and len(value) > 100:
                result[key] = f"{value[:50]}...[truncated]"
            else:
                result[key] = _serialize_value(value)
        return result

    return {
        "positional_count": len(args),
        "keyword_args": sanitize_dict(kwargs)
    }


async def _call_callback(
    callback: Callable,
    decision: AuthorizationDecision,
    tool_name: str
) -> None:
    """Call a callback function, handling both sync and async."""

    try:
        if asyncio.iscoroutinefunction(callback):
            await callback(decision, tool_name)
        else:
            callback(decision, tool_name)
    except Exception as e:
        logger.warning(f"MCP Governance: Callback error - {e}")


# Convenience decorator for common patterns
def require_governance(
    client: AscendClient,
    action_type: str,
    resource: str,
    **kwargs
) -> Callable:
    """
    Simplified decorator alias for mcp_governance.

    Example:
        @require_governance(ascend, "file.write", "/etc/config")
        def write_config(content: str):
            ...
    """
    return mcp_governance(client, action_type, resource, **kwargs)


def high_risk_action(
    client: AscendClient,
    action_type: str,
    resource: str,
    **kwargs
) -> Callable:
    """
    Decorator for high-risk actions that require human approval.

    Example:
        @high_risk_action(ascend, "database.delete", "production_db")
        async def drop_table(table_name: str):
            ...
    """
    return mcp_governance(
        client,
        action_type,
        resource,
        risk_level="high",
        require_human_approval=True,
        **kwargs
    )


class MCPGovernanceMiddleware:
    """
    Middleware class for applying governance to multiple MCP tools.

    Example:
        middleware = MCPGovernanceMiddleware(ascend_client)

        @mcp_server.tool()
        @middleware.govern("database.query", "production_db")
        async def query(sql: str):
            ...

        @mcp_server.tool()
        @middleware.govern("file.read", "/var/log")
        async def read_logs(path: str):
            ...
    """

    def __init__(
        self,
        client: AscendClient,
        default_config: Optional[MCPGovernanceConfig] = None
    ):
        self.client = client
        self.default_config = default_config or DEFAULT_CONFIG
        self._governed_tools: List[str] = []

    def govern(
        self,
        action_type: str,
        resource: str,
        config: Optional[MCPGovernanceConfig] = None,
        **kwargs
    ) -> Callable:
        """Apply governance to a tool."""

        def decorator(func: Callable) -> Callable:
            self._governed_tools.append(func.__name__)
            return mcp_governance(
                self.client,
                action_type,
                resource,
                config=config or self.default_config,
                **kwargs
            )(func)

        return decorator

    @property
    def governed_tools(self) -> List[str]:
        """List of tools with governance applied."""
        return self._governed_tools.copy()


# =============================================================================
# FEAT-008 / SDK 2.2.0: MCP Kill-Switch Consumer
# =============================================================================


class MCPKillSwitchConsumer:
    """
    FEAT-008: In-process tracker of MCP kill-switch state for governed tools.

    The ASCEND backend publishes kill-switch commands to an SNS topic with
    message attribute ``target_type=mcp_server``. A per-org SQS queue
    filters by ``organization_id``. This consumer receives those messages
    (via an injected poller callback or direct ``apply_message``) and
    maintains an in-memory blocklist keyed by MCP server name.

    Usage:
        consumer = MCPKillSwitchConsumer()
        # Whatever SQS poll loop the app already runs:
        for msg in sqs_messages:
            consumer.apply_message(msg)
        # Decorator checks:
        if consumer.is_blocked("production_fs"):
            raise AuthorizationError(...)

    Design:
        - Pure Python, no AWS dependency (poll loop is owned by the host).
        - Thread-unsafe by default; callers should wrap in a lock if needed.
        - Fail-secure: malformed messages are ignored (no state change).

    Compliance: SOC 2 CC6.2, NIST IR-4, EU AI Act Art. 15
    """

    def __init__(self) -> None:
        self._blocked_servers: set = set()
        self._blocked_config_ids: set = set()

    def apply_message(self, message: Dict[str, Any]) -> None:
        """Apply a kill-switch message payload to local state.

        Expected shape matches what backend ``agent_control_service``
        publishes: target_type, target_mcp_server_config_id, command_type,
        mcp_server (display name if provided in parameters), parameters.
        """
        try:
            target_type = message.get("target_type") or "agent"
            if target_type != "mcp_server":
                return
            command_type = (message.get("command_type") or "").upper()
            cfg_id = message.get("target_mcp_server_config_id")
            params = message.get("parameters") or {}
            server_name = params.get("mcp_server") or message.get("mcp_server")

            if command_type == "BLOCK":
                if cfg_id is not None:
                    self._blocked_config_ids.add(cfg_id)
                if server_name:
                    self._blocked_servers.add(server_name)
                logger.warning(
                    f"FEAT-008 MCP kill-switch BLOCK received: "
                    f"server={server_name}, cfg_id={cfg_id}"
                )
            elif command_type == "UNBLOCK":
                if cfg_id is not None:
                    self._blocked_config_ids.discard(cfg_id)
                if server_name:
                    self._blocked_servers.discard(server_name)
                logger.info(
                    f"FEAT-008 MCP kill-switch UNBLOCK received: "
                    f"server={server_name}, cfg_id={cfg_id}"
                )
        except Exception as e:
            # Fail-secure: never raise out of message application
            logger.error(f"FEAT-008: MCPKillSwitchConsumer.apply_message error: {e}")

    def is_blocked(
        self,
        mcp_server: Optional[str] = None,
        mcp_server_config_id: Optional[int] = None,
    ) -> bool:
        """Return True if the given MCP server is currently kill-switched."""
        if mcp_server and mcp_server in self._blocked_servers:
            return True
        if mcp_server_config_id is not None and mcp_server_config_id in self._blocked_config_ids:
            return True
        return False

    def reset(self) -> None:
        """Clear all blocked state. Intended for tests + manual recovery."""
        self._blocked_servers.clear()
        self._blocked_config_ids.clear()

    @property
    def blocked_servers(self) -> List[str]:
        """List of blocked MCP server names (snapshot copy)."""
        return list(self._blocked_servers)


# Export all public APIs
__all__ = [
    "mcp_governance",
    "require_governance",
    "high_risk_action",
    "MCPGovernanceConfig",
    "MCPGovernanceMiddleware",
    "MCPKillSwitchConsumer",
    "DEFAULT_CONFIG"
]
