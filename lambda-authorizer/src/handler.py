"""
ASCEND Lambda Authorizer - Main Handler
=======================================

GW-001: Lambda entry point for API Gateway authorization.

This is the main Lambda handler that:
1. Receives API Gateway authorizer events
2. Maps requests to ASCEND action format
3. Calls ASCEND Platform for governance decision
4. Returns IAM policy (Allow/Deny)

Design Principles:
    - FAIL SECURE: Any error results in Deny
    - Fast: <100ms p99 target with caching
    - Observable: Full metrics and logging
    - Stateless: Lambda execution model compatible

Event Types Supported:
    - REQUEST authorizer (REST API)
    - TOKEN authorizer (REST API)
    - HTTP API v2 authorizer

Compliance: SOC 2 CC6.1, NIST AC-3, PCI-DSS 7.1
Author: ASCEND Platform Engineering
Version: 1.0.0
"""

import logging
import time
from typing import Dict, Any

from .config import load_config, ConfigurationError, AscendConfig
from .ascend_client import (
    get_client,
    AscendClient,
    AscendResponse,
    AscendAPIError,
    AscendTimeoutError,
    AscendAuthenticationError
)
from .request_mapper import get_mapper, RequestMapper, MappedRequest, RequestMappingError
from .policy_generator import (
    get_policy_generator,
    get_policy_cache,
    PolicyGenerator,
    PolicyCache,
    AuthorizationPolicy
)
from .cloudwatch import (
    track_authorization,
    AuthorizationMetrics,
    get_structured_logger
)

logger = logging.getLogger(__name__)

# Module-level initialization flag
_initialized = False
_config: AscendConfig = None
_client: AscendClient = None
_mapper: RequestMapper = None
_policy_generator: PolicyGenerator = None
_policy_cache: PolicyCache = None


def _initialize() -> None:
    """
    Initialize components on cold start.

    Called once when Lambda container starts. Subsequent invocations
    reuse initialized components (warm start).
    """
    global _initialized, _config, _client, _mapper, _policy_generator, _policy_cache

    if _initialized:
        return

    logger.info("GW-001: Initializing ASCEND Lambda Authorizer...")
    start_time = time.time()

    try:
        # Load configuration
        _config = load_config()

        # Initialize components
        _client = get_client(_config)
        _mapper = get_mapper(_config.environment)
        _policy_generator = get_policy_generator()
        _policy_cache = get_policy_cache(_config.cache_ttl_seconds)

        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(
            f"GW-001: Initialization complete - "
            f"elapsed={elapsed_ms:.0f}ms, "
            f"cache_ttl={_config.cache_ttl_seconds}s"
        )

        _initialized = True

    except ConfigurationError as e:
        logger.error(f"GW-001 FAIL SECURE: Configuration error - {e}")
        raise
    except Exception as e:
        logger.error(f"GW-001 FAIL SECURE: Initialization failed - {e}")
        raise


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda authorizer entry point.

    Processes API Gateway authorizer events and returns IAM policy
    based on ASCEND Platform governance decision.

    Args:
        event: API Gateway authorizer event
        context: Lambda context object

    Returns:
        dict: API Gateway authorizer response with IAM policy

    Security:
        - FAIL SECURE: Any error returns Deny policy
        - Never logs sensitive data (API keys, tokens)
        - All decisions are audited
    """
    # Generate correlation ID for tracing
    request_id = getattr(context, 'aws_request_id', None) if context else None
    correlation_id = request_id[:8] if request_id else f"req-{int(time.time() * 1000) % 100000}"

    with track_authorization(correlation_id) as metrics:
        try:
            # Initialize on cold start
            _initialize()

            # Map request
            mapped_request = _map_request(event, metrics)

            # Check cache first
            if _config.cache_enabled:
                cached_policy = _check_cache(mapped_request, metrics)
                if cached_policy:
                    return cached_policy.to_response()

            # Call ASCEND Platform
            response = _call_ascend(mapped_request, metrics)

            # Generate policy
            policy = _generate_policy(mapped_request, response, metrics)

            # Cache if approved
            if _config.cache_enabled and response.is_approved:
                _policy_cache.set(mapped_request.cache_key, policy, response)

            return policy.to_response()

        except ConfigurationError as e:
            # Configuration errors should fail fast
            logger.error(f"GW-001 FAIL SECURE: Configuration error - {e}")
            metrics.error = str(e)
            metrics.error_type = "ConfigurationError"
            metrics.status = "error"
            return _create_deny_response(
                event,
                "Authorization service configuration error",
                "CONFIG_ERROR"
            )

        except RequestMappingError as e:
            # Invalid request format
            logger.warning(f"GW-001: Request mapping failed - {e}")
            metrics.error = str(e)
            metrics.error_type = "RequestMappingError"
            metrics.status = "error"
            return _create_deny_response(
                event,
                f"Invalid request: {e}",
                "INVALID_REQUEST"
            )

        except AscendTimeoutError as e:
            # API timeout - FAIL SECURE
            logger.error(f"GW-001 FAIL SECURE: ASCEND API timeout - {e}")
            metrics.error = str(e)
            metrics.error_type = "AscendTimeoutError"
            metrics.status = "error"
            return _create_deny_response(
                event,
                "Authorization service timeout",
                "TIMEOUT"
            )

        except AscendAuthenticationError as e:
            # API key invalid - FAIL SECURE
            logger.error(f"GW-001 FAIL SECURE: ASCEND authentication failed - {e}")
            metrics.error = str(e)
            metrics.error_type = "AscendAuthenticationError"
            metrics.status = "error"
            return _create_deny_response(
                event,
                "Authorization service authentication error",
                "AUTH_ERROR"
            )

        except AscendAPIError as e:
            # Other API errors - FAIL SECURE
            logger.error(f"GW-001 FAIL SECURE: ASCEND API error - {e}")
            metrics.error = str(e)
            metrics.error_type = "AscendAPIError"
            metrics.status = "error"
            return _create_deny_response(
                event,
                "Authorization service error",
                "API_ERROR"
            )

        except Exception as e:
            # Unexpected errors - FAIL SECURE
            logger.error(f"GW-001 FAIL SECURE: Unexpected error - {type(e).__name__}: {e}")
            metrics.error = str(e)
            metrics.error_type = type(e).__name__
            metrics.status = "error"
            return _create_deny_response(
                event,
                "Internal authorization error",
                "INTERNAL_ERROR"
            )


def _map_request(event: Dict[str, Any], metrics: AuthorizationMetrics) -> MappedRequest:
    """
    Map API Gateway event to ASCEND request format.

    Args:
        event: API Gateway event
        metrics: Metrics object to populate

    Returns:
        MappedRequest: Mapped request
    """
    mapped = _mapper.map_event(event)

    # Update metrics
    metrics.agent_id = mapped.agent_id
    metrics.action_type = mapped.action_type

    logger.debug(
        f"GW-001: Request mapped - "
        f"agent={mapped.agent_id}, "
        f"action={mapped.action_type}, "
        f"path={mapped.resource_path}"
    )

    return mapped


def _check_cache(request: MappedRequest, metrics: AuthorizationMetrics) -> AuthorizationPolicy:
    """
    Check cache for existing authorization decision.

    Args:
        request: Mapped request
        metrics: Metrics object to populate

    Returns:
        AuthorizationPolicy if cached, None otherwise
    """
    cached = _policy_cache.get(request.cache_key)

    if cached:
        metrics.cache_hit = True
        metrics.status = cached.context.get("ascend_status", "approved")
        metrics.risk_score = float(cached.context.get("ascend_risk_score", 0))
        logger.info(f"GW-001: Cache hit - {request.cache_key}")
        return cached

    metrics.cache_hit = False
    return None


def _call_ascend(request: MappedRequest, metrics: AuthorizationMetrics) -> AscendResponse:
    """
    Call ASCEND Platform for governance decision.

    Args:
        request: Mapped request
        metrics: Metrics object to populate

    Returns:
        AscendResponse: Platform decision
    """
    start_time = time.time()

    response = _client.submit_action(
        agent_id=request.agent_id,
        action_type=request.action_type,
        description=request.description,
        tool_name=request.tool_name,
        target_system=request.target_system,
        environment=request.environment,
        data_sensitivity=request.data_sensitivity,
        additional_context=request.context
    )

    elapsed_ms = (time.time() - start_time) * 1000

    # Update metrics
    metrics.ascend_action_id = response.id
    metrics.ascend_latency_ms = elapsed_ms
    metrics.status = response.status
    metrics.risk_score = response.risk_score
    metrics.risk_level = response.risk_level

    return response


def _generate_policy(
    request: MappedRequest,
    response: AscendResponse,
    metrics: AuthorizationMetrics
) -> AuthorizationPolicy:
    """
    Generate IAM policy from ASCEND response.

    Decision Logic:
        - status == "approved" → Allow
        - status == "pending_approval" → Deny (needs human review)
        - status == "denied" → Deny
        - Any other status → Deny (FAIL SECURE)

    Args:
        request: Mapped request
        response: ASCEND response
        metrics: Metrics object

    Returns:
        AuthorizationPolicy: Generated policy
    """
    # Only "approved" status results in Allow
    allow = response.is_approved

    policy = _policy_generator.generate_policy(request, response, allow)

    # Log decision
    if allow:
        logger.info(
            f"GW-001: ALLOW - "
            f"agent={request.agent_id}, "
            f"action={response.id}, "
            f"risk={response.risk_score}"
        )
    else:
        logger.info(
            f"GW-001: DENY - "
            f"agent={request.agent_id}, "
            f"status={response.status}, "
            f"risk={response.risk_score}"
        )

    return policy


def _create_deny_response(
    event: Dict[str, Any],
    reason: str,
    error_code: str
) -> Dict[str, Any]:
    """
    Create Deny response for error cases.

    Args:
        event: Original event (to extract method ARN)
        reason: Denial reason
        error_code: Error code

    Returns:
        dict: API Gateway authorizer Deny response
    """
    # Extract method ARN from event
    method_arn = (
        event.get("methodArn") or
        event.get("routeArn") or
        "*"
    )

    # Extract agent ID if possible
    headers = event.get("headers", {})
    if headers:
        headers = {k.lower(): v for k, v in headers.items()}
    agent_id = headers.get("x-ascend-agent-id", "unknown")

    policy = _policy_generator.generate_deny_policy(
        agent_id=agent_id,
        method_arn=method_arn,
        reason=reason,
        error_code=error_code
    )

    return policy.to_response()


# Export for testing
def reset_state() -> None:
    """Reset module state for testing."""
    global _initialized, _config, _client, _mapper, _policy_generator, _policy_cache

    _initialized = False
    _config = None
    _client = None
    _mapper = None
    _policy_generator = None
    _policy_cache = None

    # Reset singleton instances in submodules
    from . import ascend_client, request_mapper, policy_generator

    ascend_client.reset_client()
    request_mapper._mapper_instance = None
    policy_generator._generator_instance = None
    policy_generator._cache_instance = None
