"""
ASCEND SDK Client
=================

Enterprise-grade HTTP client for ASCEND AI Governance API.

Security Standards:
- SOC 2 CC6.1: Access control audit trails
- HIPAA 164.312(e): Encryption in transit
- PCI-DSS 8.2: Secure credential handling
- NIST AI RMF: Risk assessment integration

Version: 2.1.0
"""

import os
import re
import time
import json
import random
import logging
import hashlib
import hmac
import threading
from types import SimpleNamespace
from typing import Optional, Dict, Any, List, Callable, Union
from enum import Enum
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import (
    AgentAction,
    AuthorizationDecision,
    ActionDetails,
    Decision,
    DecisionStatus,
    KillSwitchStatus,
    PolicyEvaluationResult,
    ResourceClassification,
    AuditLogResponse,
    AgentHealthStatus,
    Webhook,
    WebhookTestResult,
    BulkEvaluationResult,
    BulkActionResult,
)
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
from .constants import (
    SDK_VERSION,
    USER_AGENT,
    DEFAULT_API_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_KILL_SWITCH_INTERVAL,
    DEFAULT_HEARTBEAT_INTERVAL,
    MAX_BULK_ACTIONS,
    DEFAULT_BULK_CONCURRENCY,
    API_ENDPOINTS,
)


class FailMode(str, Enum):
    """
    Fail mode configuration for when ASCEND is unreachable.

    CLOSED: Block action if ASCEND unreachable (more secure, recommended)
    OPEN: Allow action if ASCEND unreachable (more available, use with caution)
    """
    CLOSED = "closed"
    OPEN = "open"


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern for resilient API calls.

    Prevents cascading failures by failing fast when the service is down.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0

    @property
    def failures(self) -> int:
        """Current failure count."""
        return self._failure_count

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for recovery timeout."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN

    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return True
        return False

    def reset(self) -> None:
        """Reset circuit breaker to initial closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0


_LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class AscendLogger:
    """
    Structured logger with API key masking.

    Security: Never logs API keys or sensitive credentials.

    Args:
        name: Logger name (default: "ascend_sdk")
        level: Logging level as int or string (e.g., logging.INFO or "INFO")
        json_format: If True, output structured JSON logs. If False, plain text.
    """

    def __init__(
        self,
        name: str = "ascend_sdk",
        level: Union[int, str] = logging.INFO,
        json_format: bool = False,
    ):
        self.logger = logging.getLogger(name)
        self._json_format = json_format

        # Accept level as string or int
        if isinstance(level, str):
            resolved = _LOG_LEVEL_MAP.get(level.upper(), logging.INFO)
        else:
            resolved = level
        self.logger.setLevel(resolved)

        # Add a StreamHandler if json_format and no handlers exist
        if json_format and not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

        self._correlation_id: Optional[str] = None

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for request tracing."""
        self._correlation_id = correlation_id

    def _mask_sensitive(self, data: Any) -> Any:
        """Mask sensitive data like API keys."""
        if isinstance(data, str):
            # Mask API keys (owkai_..., ascend_..., sk_..., Bearer tokens)
            data = re.sub(r'owkai_[a-zA-Z0-9_]+', 'owkai_****', data)
            data = re.sub(r'ascend_[a-zA-Z0-9_]+', 'ascend_****', data)
            data = re.sub(r'sk_[a-zA-Z0-9_]+', 'sk_****', data)
            data = re.sub(r'Bearer [a-zA-Z0-9_\-\.]+', 'Bearer ****', data)
            return data
        elif isinstance(data, dict):
            masked = {}
            for k, v in data.items():
                if k.lower() in ('api_key', 'apikey', 'authorization', 'x-api-key', 'password', 'secret'):
                    masked[k] = '****'
                else:
                    masked[k] = self._mask_sensitive(v)
            return masked
        elif isinstance(data, list):
            return [self._mask_sensitive(item) for item in data]
        return data

    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """Format log message with masking applied to message AND kwargs."""
        # PY-SEC-001: Mask the message string itself
        masked_message = self._mask_sensitive(message)

        if self._json_format:
            log_entry: Dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "logger": "ascend_sdk",
                "message": masked_message,
            }
            if self._correlation_id:
                log_entry["correlation_id"] = self._correlation_id
            for k, v in kwargs.items():
                log_entry[k] = self._mask_sensitive(v)
            return json.dumps(log_entry)
        else:
            parts = [f"[{level}] {masked_message}"]
            if self._correlation_id:
                parts.append(f"correlation_id={self._correlation_id}")
            for k, v in kwargs.items():
                parts.append(f"{k}={self._mask_sensitive(v)}")
            return " ".join(parts)

    def debug(self, message: str, **kwargs: Any) -> None:
        self.logger.debug(self._format_message("DEBUG", message, **kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        self.logger.info(self._format_message("INFO", message, **kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        self.logger.warning(self._format_message("WARNING", message, **kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        self.logger.error(self._format_message("ERROR", message, **kwargs))


# Global logger instance
logger = AscendLogger()


class AscendClient:
    """
    ASCEND AI Governance SDK Client.

    Enterprise-grade client for submitting agent actions
    for authorization and policy enforcement.

    Example:
        client = AscendClient(
            api_key="owkai_live_xxxxx",
            agent_id="my-agent-001",
            agent_name="My AI Agent",
            fail_mode="closed"
        )

        decision = client.evaluate_action(
            action_type="financial.refund",
            resource="stripe_api",
            parameters={"amount": 100}
        )

        if decision.decision == Decision.ALLOWED:
            result = process_refund()
            client.log_action_completed(decision.action_id, result=result)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        api_url: Optional[str] = None,
        environment: str = "production",
        fail_mode: str = "closed",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        enable_circuit_breaker: bool = True,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 30,
        signing_secret: Optional[str] = None,
        debug: bool = False
    ):
        """
        Initialize the ASCEND client.

        Args:
            api_key: Organization API key (or set ASCEND_API_KEY env var)
            agent_id: Unique identifier for this agent
            agent_name: Human-readable agent name
            api_url: API endpoint URL (default: from ASCEND_API_URL env var)
            environment: Deployment environment (production, staging, development)
            fail_mode: Behavior when unreachable - "closed" (block) or "open" (allow)
            timeout: Request timeout in seconds (default: 5s)
            max_retries: Maximum retry attempts (default: 3)
            enable_circuit_breaker: Enable circuit breaker pattern
            circuit_breaker_threshold: Failures before opening circuit
            circuit_breaker_timeout: Seconds before attempting recovery
            signing_secret: Optional HMAC signing secret for request verification
            debug: Enable debug logging

        Raises:
            ValueError: If API key is not provided
            ConfigurationError: If API URL uses HTTP for non-localhost
        """
        # Configuration
        self.api_url = (
            api_url
            or os.getenv("ASCEND_API_URL")
            or os.getenv("OWKAI_API_URL")
            or DEFAULT_API_URL
        ).rstrip("/")

        # PY-SEC-002: TLS enforcement
        url_lower = self.api_url.lower()
        if url_lower.startswith("http://") and not (
            url_lower.startswith("http://localhost")
            or url_lower.startswith("http://127.0.0.1")
            or url_lower.startswith("http://[::1]")
        ):
            raise ConfigurationError(
                f"API URL must use HTTPS for security. "
                f"Got: {self.api_url}. "
                f"Use https:// or http://localhost for local development."
            )

        self.api_key = api_key or os.getenv("ASCEND_API_KEY") or os.getenv("OWKAI_API_KEY")
        self.agent_id = agent_id or os.getenv("ASCEND_AGENT_ID")
        self.agent_name = agent_name or os.getenv("ASCEND_AGENT_NAME") or self.agent_id
        self.environment = environment
        self.fail_mode = FailMode(fail_mode.lower())
        self.timeout = timeout
        self.max_retries = max_retries
        self.signing_secret = signing_secret or os.getenv("ASCEND_SIGNING_SECRET")
        self._debug = debug

        # Validation
        if not self.api_key:
            raise ValueError(
                "API key is required. "
                "Pass api_key parameter or set ASCEND_API_KEY environment variable."
            )

        # Set up logging
        if debug:
            logger.logger.setLevel(logging.DEBUG)
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(message)s'
            )

        # Circuit breaker
        self._circuit_breaker: Optional[CircuitBreaker] = None
        if enable_circuit_breaker:
            self._circuit_breaker = CircuitBreaker(
                failure_threshold=circuit_breaker_threshold,
                recovery_timeout=circuit_breaker_timeout
            )

        # HTTP session with retry logic
        self._session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

        # Default headers (API key masked in logs)
        self._session.headers.update({
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": USER_AGENT,
            "X-SDK-Version": SDK_VERSION,
            "X-Environment": self.environment,
        })

        # Registration state
        self._registered = False
        self._registration_info: Optional[Dict] = None

        # Kill switch state
        self._is_blocked = False
        self._kill_switch_reason: Optional[str] = None
        self._kill_switch_timer: Optional[threading.Timer] = None

        # SDK 2.4.0 — BUG-16 cohort (J3): background heartbeat state
        self._heartbeat_timer: Optional[threading.Timer] = None
        self._heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL

        logger.info(
            "ASCEND Client initialized",
            api_url=self.api_url,
            agent_id=self.agent_id,
            environment=self.environment,
            fail_mode=self.fail_mode.value
        )

    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """Generate HMAC-SHA256 signature for request verification."""
        if not self.signing_secret:
            return ""

        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            self.signing_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return f"v1={signature}"

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for request tracing."""
        import uuid
        return f"asc_{uuid.uuid4().hex[:16]}"

    def _handle_fail_mode(self, error: Exception, action_type: str = None) -> AuthorizationDecision:
        """
        Handle failures according to fail_mode configuration.

        Args:
            error: The exception that occurred
            action_type: Type of action being evaluated

        Returns:
            AuthorizationDecision based on fail_mode

        Raises:
            The original error if fail_mode is CLOSED
        """
        if self.fail_mode == FailMode.OPEN:
            logger.warning(
                "ASCEND unreachable, fail_mode=open, allowing action",
                error=str(error),
                action_type=action_type
            )
            return AuthorizationDecision(
                action_id="fail_open_" + self._generate_correlation_id(),
                decision=Decision.ALLOWED,
                risk_score=0,
                conditions=["fail_open_mode"],
                comments="Auto-approved due to fail_mode=open (ASCEND unreachable)",
                execution_allowed=True,
                metadata={"fail_mode": "open", "error": str(error)}
            )
        else:
            logger.error(
                "ASCEND unreachable, fail_mode=closed, blocking action",
                error=str(error),
                action_type=action_type
            )
            raise error

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make authenticated request to API with retry logic and circuit breaker.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            API response as dictionary

        Raises:
            CircuitBreakerOpen: If circuit breaker is open
            AuthenticationError: On 401 responses
            AuthorizationError: On 403 responses
            RateLimitError: On 429 responses
            ValidationError: On 400/422 responses
            OWKAIError: On other errors
        """
        # Check circuit breaker
        if self._circuit_breaker and not self._circuit_breaker.allow_request():
            raise CircuitBreakerOpen(
                "Circuit breaker is open - ASCEND service appears to be down",
                recovery_time=self._circuit_breaker.recovery_timeout
            )

        url = f"{self.api_url}{endpoint}"
        correlation_id = self._generate_correlation_id()
        logger.set_correlation_id(correlation_id)

        # Prepare headers
        timestamp = datetime.now(timezone.utc).isoformat()
        headers = {
            "X-Correlation-ID": correlation_id,
            "X-Request-Timestamp": timestamp,
        }

        # Add signature if signing secret is configured
        if self.signing_secret and data:
            payload = json.dumps(data, sort_keys=True)
            headers["X-Signature"] = self._generate_signature(payload, timestamp)

        logger.debug(
            f"{method.upper()} {endpoint}",
            correlation_id=correlation_id,
            retry_count=retry_count
        )

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            # Record success for circuit breaker
            if self._circuit_breaker:
                self._circuit_breaker.record_success()

            # Handle specific status codes
            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid or expired API key",
                    details={"status_code": 401}
                )

            if response.status_code == 403:
                error_data = self._safe_json(response)
                raise AuthorizationError(
                    error_data.get("detail", "Access denied"),
                    policy_violations=error_data.get("policy_violations", []),
                    details=error_data
                )

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                if retry_count < self.max_retries:
                    logger.warning(f"Rate limited. Retrying in {retry_after}s...")
                    time.sleep(min(retry_after, 10))
                    return self._request(method, endpoint, data, params, retry_count + 1)
                raise RateLimitError(
                    "Rate limit exceeded",
                    retry_after=retry_after
                )

            if response.status_code in (400, 422):
                error_data = self._safe_json(response)
                raise ValidationError(
                    error_data.get("detail", "Validation failed"),
                    field_errors=error_data.get("errors", {})
                )

            if response.status_code >= 500:
                if self._circuit_breaker:
                    self._circuit_breaker.record_failure()

                if retry_count < self.max_retries:
                    # PY-SEC-003: Exponential backoff with jitter
                    wait_time = (2 ** retry_count) + random.uniform(0, 1)
                    logger.warning(f"Server error. Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    return self._request(method, endpoint, data, params, retry_count + 1)
                raise OWKAIError(
                    "Server error",
                    error_code="SERVER_ERROR",
                    details={"status_code": response.status_code}
                )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            if self._circuit_breaker:
                self._circuit_breaker.record_failure()
            raise TimeoutError(
                f"Request timed out after {self.timeout}s",
                timeout_seconds=self.timeout
            )

        except requests.exceptions.ConnectionError as e:
            if self._circuit_breaker:
                self._circuit_breaker.record_failure()

            if retry_count < self.max_retries:
                # PY-SEC-003: Exponential backoff with jitter
                wait_time = (2 ** retry_count) + random.uniform(0, 1)
                logger.warning(f"Connection failed. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
                return self._request(method, endpoint, data, params, retry_count + 1)
            raise ConnectionError(
                f"Failed to connect to {self.api_url}",
                details={"original_error": str(e)}
            )

    def _safe_json(self, response: Any) -> Dict[str, Any]:
        """Safely parse JSON response."""
        try:
            return response.json()
        except Exception:
            return {"detail": response.text}

    # =========================================================================
    # AGENT REGISTRATION
    # =========================================================================

    def register(
        self,
        agent_type: str = "supervised",
        capabilities: Optional[List[str]] = None,
        allowed_resources: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Register this agent with ASCEND governance platform.

        Args:
            agent_type: Type of agent (supervised, autonomous, mcp_server)
            capabilities: List of capabilities this agent has
            allowed_resources: Resources this agent can access
            metadata: Additional agent metadata

        Returns:
            Registration confirmation with agent details
        """
        if not self.agent_id:
            raise ValueError("agent_id is required for registration")

        data = {
            "agent_id": self.agent_id,
            "display_name": self.agent_name,
            "agent_type": agent_type,
            "environment": self.environment,
            "capabilities": capabilities or [],
            "allowed_resources": allowed_resources or [],
            "sdk_version": SDK_VERSION,
            "metadata": metadata or {}
        }

        try:
            result = self._request("POST", API_ENDPOINTS["register_agent"], data=data)
            self._registered = True
            self._registration_info = result

            logger.info(
                "Agent registered successfully",
                agent_id=self.agent_id,
                trust_level=result.get("trust_level", "unknown")
            )

            return result
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                logger.info("Agent already registered", agent_id=self.agent_id)
                self._registered = True
                return {"status": "already_registered", "agent_id": self.agent_id}
            raise

    # =========================================================================
    # ACTION EVALUATION
    # =========================================================================

    def evaluate_action(
        self,
        action_type: str,
        resource: str,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        resource_id: Optional[str] = None,
        risk_indicators: Optional[Dict[str, Any]] = None,
        wait_for_decision: bool = True,
        timeout: Optional[int] = None,
        # SDK 2.3.0 / FEAT-007: Orchestration linkage (optional).
        orchestration_session_id: Optional[str] = None,
        parent_action_id: Optional[int] = None,
        orchestration_depth: Optional[int] = None,
    ) -> AuthorizationDecision:
        """
        Evaluate an action against ASCEND policies.

        Args:
            action_type: Category.action format (e.g., "financial.refund")
            resource: Resource identifier (e.g., "stripe_api")
            parameters: Action-specific parameters
            context: Additional context for risk scoring
            resource_id: Specific resource instance ID
            risk_indicators: Risk assessment hints
            wait_for_decision: Whether to wait for approval if pending
            timeout: Timeout for waiting (seconds)
            orchestration_session_id: SDK 2.3.0 — link this action to a
                multi-agent orchestration session. Backend groups all actions
                sharing this id for audit + risk propagation (FEAT-007).
            parent_action_id: SDK 2.3.0 — AgentAction.id returned from an
                earlier evaluate_action call that initiated this delegation.
                Server validates same-tenant + session-match (fail-secure 403).
            orchestration_depth: SDK 2.3.0 — delegation depth (0-5). Server
                rejects values outside this range with HTTP 422.

        Returns:
            AuthorizationDecision with decision, risk_score, reason

        Raises:
            ValidationError: If action_type or resource is empty
            KillSwitchError: If kill switch is active
        """
        # Kill switch check
        if self._is_blocked:
            raise KillSwitchError(
                reason=self._kill_switch_reason
            )

        # PY-SEC-004: Input validation before network call
        if not action_type or not isinstance(action_type, str) or not action_type.strip():
            raise ValidationError(
                "action_type is required and must be a non-empty string",
                field_errors={"action_type": "Required field is missing or empty"}
            )
        if not resource or not isinstance(resource, str) or not resource.strip():
            raise ValidationError(
                "resource is required and must be a non-empty string",
                field_errors={"resource": "Required field is missing or empty"}
            )

        # SDK 2.3.0: Client-side guardrail on depth. Server also enforces
        # this cap, but refusing locally saves a round-trip.
        if orchestration_depth is not None and not (0 <= int(orchestration_depth) <= 5):
            raise ValidationError(
                "orchestration_depth must be between 0 and 5",
                field_errors={"orchestration_depth": "Out of range (0..5)"}
            )

        action = AgentAction(
            agent_id=self.agent_id or "unknown",
            agent_name=self.agent_name or "Unknown Agent",
            action_type=action_type,
            resource=resource,
            resource_id=resource_id,
            action_details=parameters,
            context=context,
            risk_indicators=risk_indicators,
            orchestration_session_id=orchestration_session_id,
            parent_action_id=parent_action_id,
            orchestration_depth=orchestration_depth,
        )

        try:
            logger.info(
                "Evaluating action",
                action_type=action_type,
                resource=resource
            )

            response = self._request(
                "POST",
                API_ENDPOINTS["submit_action"],
                data=action.to_dict()
            )

            decision = AuthorizationDecision.from_dict(response)

            # Wait for decision if pending and requested
            if wait_for_decision and decision.decision == Decision.PENDING:
                effective_timeout = timeout or 60
                decision = self.wait_for_decision(
                    decision.action_id,
                    timeout=effective_timeout
                )

            logger.info(
                "Action evaluated",
                action_id=decision.action_id,
                decision=decision.decision.value,
                risk_score=decision.risk_score
            )

            return decision

        except (TimeoutError, ConnectionError, CircuitBreakerOpen) as e:
            return self._handle_fail_mode(e, action_type)

    # =========================================================================
    # FEAT-008 / SDK 2.2.0: MCP ACTION EVALUATION — DEDICATED PIPELINE ENDPOINT
    # =========================================================================
    def evaluate_mcp_action(
        self,
        mcp_server: str,
        namespace: str,
        verb: str,
        resource: str,
        action_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        environment: str = "production",
        tool_name: Optional[str] = None,
        use_mcp_endpoint: bool = True,
    ) -> AuthorizationDecision:
        """
        Evaluate an MCP tool call against ASCEND governance (FEAT-008, SDK 2.2.0).

        When ``use_mcp_endpoint`` is True (default), posts to the dedicated
        ``POST /api/v1/mcp/actions/submit`` endpoint so the call runs through
        EnterpriseRiskPipeline with the MCP branches in CVSS/MITRE/NIST +
        mcp_tool_risk_defaults catalog safety floor.

        When ``use_mcp_endpoint`` is False, falls back to ``evaluate_action``
        (pre-2.2.0 behavior: MCP call is submitted as an AgentAction).

        Args:
            mcp_server: Registered MCP server name
            namespace: MCP namespace (filesystem, network, database, ...)
            verb: MCP verb (read_file, post_request, execute, ...)
            resource: Target resource path/identifier
            action_type: Optional taxonomy label (defaults to "<namespace>.<verb>")
            parameters: Tool arguments (dict)
            context: Additional context (session_id, contains_pii, ...)
            description: Optional description
            environment: "production" | "staging" | "dev"
            tool_name: Optional tool name override
            use_mcp_endpoint: If False, round-trip via evaluate_action (legacy)

        Returns:
            AuthorizationDecision — normalized response shape. allowed=True
            when status=='approved' AND no deny reason.

        Compliance: SOC 2 CC6.1, NIST AC-4/CM-7/IA-5/AC-20, EU AI Act Art. 9
        """
        resolved_action_type = action_type or f"{namespace}.{verb}"

        if not use_mcp_endpoint:
            # Legacy path — pre-2.2.0 behavior
            return self.evaluate_action(
                action_type=resolved_action_type,
                resource=resource,
                parameters=parameters or {},
                context={
                    "mcp_server": mcp_server,
                    "namespace": namespace,
                    "verb": verb,
                    **(context or {}),
                },
                wait_for_decision=False,
            )

        payload = {
            "mcp_server": mcp_server,
            "namespace": namespace,
            "verb": verb,
            "resource": resource,
            "action_type": resolved_action_type,
            "description": description,
            "parameters": parameters or {},
            "context": context or {},
            "environment": environment,
            "tool_name": tool_name,
        }

        try:
            response = self._request(
                "POST",
                "/api/v1/mcp/actions/submit",
                data=payload,
            )

            # Normalize MCP response → AuthorizationDecision shape
            is_denied = (
                response.get("status") == "denied"
                or response.get("success") is False
            )
            if is_denied:
                return AuthorizationDecision(
                    action_id=str(response.get("action_id", "")),
                    decision=Decision.DENIED,
                    reason=response.get("reason", "denied"),
                    risk_score=response.get("risk_score", 100),
                )

            requires_approval = bool(response.get("requires_approval", False))
            status = Decision.PENDING if requires_approval else Decision.ALLOWED
            return AuthorizationDecision(
                action_id=str(response.get("action_id", "")),
                decision=status,
                reason=None,
                risk_score=response.get("risk_score", 0),
            )
        except (TimeoutError, ConnectionError, CircuitBreakerOpen) as e:
            return self._handle_fail_mode(e, resolved_action_type)

    # =========================================================================
    # SDK 2.3.0: FEAT-001B — Link a model to an agent (agent registry update)
    # =========================================================================
    def link_model_to_agent(
        self,
        agent_id: str,
        model_id: int,
    ) -> Dict[str, Any]:
        """
        Link a registered AI/ML model to an agent.

        Thin wrapper over PUT /api/registry/agents/{agent_id} that sets the
        agent's model_id. The server enforces:
          - the model exists and belongs to the caller's organization
          - the model's compliance_status is 'approved' or 'partially_approved'
          - an immutable audit event is recorded (AGENT_MODEL_LINKED)

        Auth: works with API key (admin role) or JWT (admin role).

        Args:
            agent_id: Agent's string identifier (e.g., "agent-001").
            model_id: DeployedModel.id (int) from the ASCEND model registry.

        Returns:
            Raw response dict: {"success": bool, "agent": {...}, "message": str}

        Raises:
            ValidationError: If agent_id or model_id is missing/invalid.
            AuthorizationError: 403 on wrong tenant / unapproved model.
        """
        if not agent_id or not isinstance(agent_id, str) or not agent_id.strip():
            raise ValidationError(
                "agent_id is required and must be a non-empty string",
                field_errors={"agent_id": "Required field is missing or empty"},
            )
        if not isinstance(model_id, int) or model_id < 1:
            raise ValidationError(
                "model_id must be a positive integer",
                field_errors={"model_id": "Must be a positive integer"},
            )

        endpoint = API_ENDPOINTS["agent_update"].format(agent_id=agent_id)
        return self._request("PUT", endpoint, data={"model_id": model_id})

    # =========================================================================
    # SDK 2.3.0: FEAT-005 — Register a supply-chain component
    # =========================================================================
    def register_supply_chain_component(
        self,
        component_id: str,
        component_name: str,
        component_type: str,
        provider: Optional[str] = None,
        version: Optional[str] = None,
        latest_version: Optional[str] = None,
        license_type: Optional[str] = None,
        source_url: Optional[str] = None,
        provenance_verified: bool = False,
        risk_level: str = "medium",
        compliance_notes: Optional[str] = None,
        package_name: Optional[str] = None,
        package_ecosystem: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a new AI supply-chain component with the organization.

        Posts to POST /api/v1/supply-chain/components (FEAT-005). Auth is
        now dual (API key admin OR JWT admin) as of backend SDK 2.3.0
        companion fix.

        Args:
            component_id: Org-unique identifier (<=255 chars).
            component_name: Human-readable name (<=500 chars).
            component_type: Must match one of the backend ComponentType enum
                values (e.g., "model", "library", "dataset", "framework",
                "tool", "service"). Server rejects unknown types.
            provider: Vendor / provider name.
            version: Installed version.
            latest_version: Latest-known upstream version (for drift tracking).
            license_type: SPDX identifier or license name.
            source_url: Upstream source URL.
            provenance_verified: True if supply-chain provenance is verified.
            risk_level: "low" | "medium" | "high" | "critical" (default "medium").
            compliance_notes: Free-form notes for auditors.
            package_name: Package ecosystem package name.
            package_ecosystem: e.g., "pypi", "npm", "maven", "huggingface".

        Returns:
            Raw response dict from the server including the created component.

        Raises:
            ValidationError: Local checks fail.
            AuthorizationError: Caller lacks admin role.
        """
        if not component_id or not isinstance(component_id, str) or not component_id.strip():
            raise ValidationError(
                "component_id is required and must be a non-empty string",
                field_errors={"component_id": "Required field"},
            )
        if not component_name or not isinstance(component_name, str) or not component_name.strip():
            raise ValidationError(
                "component_name is required and must be a non-empty string",
                field_errors={"component_name": "Required field"},
            )
        if not component_type or not isinstance(component_type, str) or not component_type.strip():
            raise ValidationError(
                "component_type is required and must be a non-empty string",
                field_errors={"component_type": "Required field"},
            )

        payload: Dict[str, Any] = {
            "component_id": component_id,
            "component_name": component_name,
            "component_type": component_type,
            "provenance_verified": provenance_verified,
            "risk_level": risk_level,
        }
        # Only include optional fields when set, so we don't clobber server defaults.
        for key, value in (
            ("provider", provider),
            ("version", version),
            ("latest_version", latest_version),
            ("license_type", license_type),
            ("source_url", source_url),
            ("compliance_notes", compliance_notes),
            ("package_name", package_name),
            ("package_ecosystem", package_ecosystem),
        ):
            if value is not None:
                payload[key] = value

        return self._request(
            "POST",
            API_ENDPOINTS["supply_chain_components"],
            data=payload,
        )

    # =========================================================================
    # SDK 2.3.0: SEC-103 — Kill-switch HTTP fallback polling
    # =========================================================================
    def get_pending_commands(
        self,
        agent_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch pending control commands for an agent over HTTP.

        Thin wrapper over GET /api/registry/agents/{agent_id}/commands. Used
        as an HTTP fallback when the SDK cannot (or does not want to) poll
        the per-org SQS queue directly. Returns only commands belonging to
        the caller's organization.

        Args:
            agent_id: Agent identifier. If omitted, uses the client's bound
                agent_id. Broadcast commands (cmd.agent_id=None on the row)
                are included when listing for a specific agent.

        Returns:
            List of command dicts. Each has: command_id, command_type,
            target_type, reason, parameters, status, issued_by, issued_via,
            created_at, expires_at, is_broadcast.

        Raises:
            ValidationError: If no agent_id is available.
            AuthenticationError: API key invalid.
            AuthorizationError: Caller lacks admin role / off-tenant.
        """
        resolved = agent_id or self.agent_id
        if not resolved or not isinstance(resolved, str) or not resolved.strip():
            raise ValidationError(
                "agent_id is required (pass one or set on the client)",
                field_errors={"agent_id": "Required field"},
            )
        endpoint = API_ENDPOINTS["agent_commands"].format(agent_id=resolved)
        response = self._request("GET", endpoint)
        commands = response.get("commands", []) if isinstance(response, dict) else []
        return list(commands)

    def ack_command(
        self,
        command_id: str,
        agent_id: Optional[str] = None,
    ) -> bool:
        """
        Acknowledge a control command (receipt-only).

        POSTs to /api/registry/agents/{agent_id}/commands/{command_id}/ack
        with no body. The server records acknowledgement + writes an
        immutable audit event. Off-tenant / mismatched-agent acks are
        rejected with HTTP 403 (fail-secure — no cross-tenant enumeration).

        Args:
            command_id: The command UUID returned by get_pending_commands
                or received via the SQS message body (command_id field).
            agent_id: Acknowledging agent identifier. Defaults to the
                client's bound agent_id.

        Returns:
            True on success. Raises on 4xx/5xx — caller should catch
            AuthorizationError for 403 fail-secure rejections.

        Raises:
            ValidationError: missing inputs.
            AuthorizationError: off-tenant / wrong agent / unknown command.
        """
        if not command_id or not isinstance(command_id, str) or not command_id.strip():
            raise ValidationError(
                "command_id is required and must be a non-empty string",
                field_errors={"command_id": "Required field"},
            )
        resolved = agent_id or self.agent_id
        if not resolved or not isinstance(resolved, str) or not resolved.strip():
            raise ValidationError(
                "agent_id is required (pass one or set on the client)",
                field_errors={"agent_id": "Required field"},
            )
        endpoint = API_ENDPOINTS["agent_command_ack"].format(
            agent_id=resolved, command_id=command_id,
        )
        response = self._request("POST", endpoint, data={})
        return bool(response.get("success", False)) if isinstance(response, dict) else False

    def get_action_status(self, action_id: str) -> AuthorizationDecision:
        """
        Get the current status of an action.

        Args:
            action_id: The action ID returned from evaluate_action

        Returns:
            Current authorization decision status
        """
        response = self._request(
            "GET",
            f"/api/agent-action/status/{action_id}"
        )
        return AuthorizationDecision.from_dict(response)

    def wait_for_decision(
        self,
        action_id: str,
        timeout: int = 60,
        poll_interval: float = 2.0
    ) -> AuthorizationDecision:
        """
        Wait for an authorization decision.

        Args:
            action_id: The action ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds

        Returns:
            Final authorization decision

        Raises:
            TimeoutError: If decision not received within timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                decision = self.get_action_status(action_id)

                if decision.decision != Decision.PENDING:
                    return decision

                logger.debug(f"Action {action_id} still pending...")
                time.sleep(poll_interval)

            except (TimeoutError, ConnectionError) as e:
                return self._handle_fail_mode(e)

        raise TimeoutError(
            f"Decision not received within {timeout} seconds",
            timeout_seconds=timeout
        )

    # =========================================================================
    # ACTION COMPLETION LOGGING
    # =========================================================================

    def log_action_completed(
        self,
        action_id: str,
        result: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Log that an action was completed successfully.

        Args:
            action_id: The action ID from evaluate_action
            result: Optional result data to log
            duration_ms: How long the action took in milliseconds

        Returns:
            Confirmation of logging
        """
        data: Dict[str, Any] = {
            "action_id": action_id,
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        if result:
            data["result"] = result
        if duration_ms:
            data["duration_ms"] = duration_ms

        try:
            response = self._request(
                "POST",
                API_ENDPOINTS["action_complete"].format(action_id=action_id),
                data=data
            )

            logger.info(
                "Action completion logged",
                action_id=action_id,
                duration_ms=duration_ms
            )

            return response
        except Exception as e:
            logger.warning(
                "Failed to log action completion to API, logged locally",
                action_id=action_id,
                error=str(e)
            )
            return {"logged_locally": True, "error": str(e)}

    def log_action_failed(
        self,
        action_id: str,
        error: Union[Dict[str, Any], str],
        duration_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Log that an action failed.

        Args:
            action_id: The action ID from evaluate_action
            error: Error details (dict or string)
            duration_ms: How long before failure in milliseconds

        Returns:
            Confirmation of logging
        """
        data: Dict[str, Any] = {
            "action_id": action_id,
            "status": "failed",
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "error": error
        }

        if duration_ms:
            data["duration_ms"] = duration_ms

        try:
            response = self._request(
                "POST",
                API_ENDPOINTS["action_fail"].format(action_id=action_id),
                data=data
            )

            logger.info(
                "Action failure logged",
                action_id=action_id,
                error_code=error.get("code") if isinstance(error, dict) else None
            )

            return response
        except Exception as e:
            logger.warning(
                "Failed to log action failure to API, logged locally",
                action_id=action_id,
                error=str(e)
            )
            return {"logged_locally": True, "error": str(e)}

    # =========================================================================
    # APPROVAL STATUS
    # =========================================================================

    def check_approval(self, approval_request_id: str) -> Dict[str, Any]:
        """
        Check the status of an approval request.

        Args:
            approval_request_id: The ID returned when action is pending_approval

        Returns:
            Approval status dict with approved, denied, pending booleans
        """
        response = self._request(
            "GET",
            API_ENDPOINTS["check_approval"].format(approval_request_id=approval_request_id)
        )

        status = response.get("status", "pending")

        return {
            "approved": status == "approved",
            "denied": status == "rejected" or status == "denied",
            "pending": status == "pending",
            "approver": response.get("approved_by") or response.get("rejected_by"),
            "timestamp": response.get("decided_at"),
            "comments": response.get("rejection_reason"),
            "metadata": response
        }

    # =========================================================================
    # WEBHOOK CONFIGURATION
    # =========================================================================

    def configure_webhook(
        self,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Configure webhook for real-time notifications.

        Args:
            url: HTTPS endpoint to receive webhooks
            events: List of event types to subscribe to
            secret: Shared secret for webhook signature verification

        Returns:
            Webhook configuration details

        Raises:
            ValidationError: If URL is not HTTPS or events are invalid
        """
        if not url.startswith("https://"):
            raise ValidationError(
                "Webhook URL must use HTTPS",
                field_errors={"url": "Must start with https://"}
            )

        valid_events = [
            "action.approved", "action.denied", "action.pending",
            "policy.violation", "agent.trust_changed"
        ]

        invalid = [e for e in events if e not in valid_events]
        if invalid:
            raise ValidationError(
                f"Invalid events: {invalid}",
                field_errors={"events": f"Valid events: {valid_events}"}
            )

        data: Dict[str, Any] = {
            "url": url,
            "events": events,
            "agent_id": self.agent_id,
        }

        if secret:
            data["secret"] = secret

        response = self._request(
            "POST",
            API_ENDPOINTS["webhooks_configure"],
            data=data
        )

        logger.info("Webhook configured", url=url, events=events)
        return response

    def list_webhooks(self) -> List[Webhook]:
        """
        List all webhook subscriptions.

        Returns:
            List of Webhook objects
        """
        response = self._request("GET", API_ENDPOINTS["webhooks_list"])
        items = response if isinstance(response, list) else response.get("webhooks", [])
        return [Webhook.from_dict(w) for w in items]

    def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        secret: Optional[str] = None,
    ) -> Webhook:
        """
        Update an existing webhook subscription.

        Args:
            webhook_id: Webhook ID to update
            url: New URL (optional)
            events: New event list (optional)
            secret: New secret (optional)

        Returns:
            Updated Webhook object
        """
        data: Dict[str, Any] = {}
        if url is not None:
            data["url"] = url
        if events is not None:
            data["events"] = events
        if secret is not None:
            data["secret"] = secret

        response = self._request(
            "PUT",
            API_ENDPOINTS["webhooks_update"].format(webhook_id=webhook_id),
            data=data
        )
        return Webhook.from_dict(response)

    def delete_webhook(self, webhook_id: str) -> None:
        """
        Delete a webhook subscription.

        Args:
            webhook_id: Webhook ID to delete
        """
        self._request(
            "DELETE",
            API_ENDPOINTS["webhooks_delete"].format(webhook_id=webhook_id)
        )

    def test_webhook(self, webhook_id: str) -> WebhookTestResult:
        """
        Send a test event to a webhook endpoint.

        Args:
            webhook_id: Webhook ID to test

        Returns:
            WebhookTestResult with success status and response details
        """
        response = self._request(
            "POST",
            API_ENDPOINTS["webhooks_test"].format(webhook_id=webhook_id)
        )
        return WebhookTestResult.from_dict(response)

    # =========================================================================
    # KILL SWITCH
    # =========================================================================

    def start_kill_switch_polling(
        self, interval_seconds: int = DEFAULT_KILL_SWITCH_INTERVAL
    ) -> None:
        """
        Start background polling for kill switch status.

        When the kill switch is active, evaluate_action() will raise
        KillSwitchError instead of making network calls.

        Args:
            interval_seconds: Polling interval in seconds (default: 5)
        """
        self._kill_switch_interval = interval_seconds
        self._poll_kill_switch()

    def stop_kill_switch_polling(self) -> None:
        """Stop background kill switch polling."""
        if self._kill_switch_timer:
            self._kill_switch_timer.cancel()
            self._kill_switch_timer = None

    # =========================================================================
    # SDK 2.4.0 — BUG-16 cohort (J3): background heartbeat scheduler
    #
    # Spawns a daemon thread that calls `heartbeat()` on a configurable
    # interval. Heartbeat failures are swallowed by the canonical method
    # (fire-and-forget semantics are preserved), so the scheduler never
    # crashes the host agent. FailMode.CLOSED is preserved: the scheduler
    # introduces no new network I/O outside `heartbeat()`, which already
    # honors the fail-secure contract.
    # =========================================================================

    def start_heartbeat(
        self,
        interval_seconds: Optional[int] = None,
    ) -> None:
        """
        Start background heartbeat sender on a daemon thread.

        The first heartbeat fires immediately; subsequent heartbeats fire
        every ``interval_seconds``. Daemon-thread guarantees the scheduler
        does not keep the process alive after the main thread exits.
        Calling ``start_heartbeat()`` more than once restarts the scheduler
        with the new interval (prior timer cancelled first).

        Args:
            interval_seconds: Polling interval. Defaults to
                ``DEFAULT_HEARTBEAT_INTERVAL`` (60s) or the instance's
                previously configured interval.

        Fail-secure: heartbeat failures never raise — the scheduler keeps
        running, and the next call will retry.
        """
        if interval_seconds is not None:
            if interval_seconds <= 0:
                raise ValueError(
                    "interval_seconds must be positive; "
                    f"got {interval_seconds}"
                )
            self._heartbeat_interval = interval_seconds

        # Cancel prior scheduler if already running (idempotent restart).
        self.stop_heartbeat()
        self._tick_heartbeat()

    def stop_heartbeat(self) -> None:
        """Stop background heartbeat sender; no-op if not running."""
        if self._heartbeat_timer:
            self._heartbeat_timer.cancel()
            self._heartbeat_timer = None

    def _tick_heartbeat(self) -> None:
        """Internal: send a heartbeat and schedule the next tick.

        Exception contract: heartbeat() itself never raises (fire-and-forget).
        The Timer scheduling below is also wrapped defensively — any failure
        to schedule the next tick must not propagate to the caller.
        """
        try:
            self.heartbeat()
        except Exception:
            # Defense-in-depth: heartbeat() is already fire-and-forget,
            # but we belt-and-suspenders here in case future refactors
            # change that contract. The scheduler must never crash.
            pass

        try:
            self._heartbeat_timer = threading.Timer(
                self._heartbeat_interval,
                self._tick_heartbeat,
            )
            self._heartbeat_timer.daemon = True
            self._heartbeat_timer.start()
        except Exception:
            # If thread scheduling itself fails (e.g., process shutdown
            # in progress), stop cleanly — fail-safe, not fail-loud.
            self._heartbeat_timer = None

    def is_blocked(self) -> bool:
        """Check if the kill switch is currently active."""
        return self._is_blocked

    def _poll_kill_switch(self) -> None:
        """Internal: poll kill switch endpoint and schedule next poll."""
        try:
            response = self._request("GET", API_ENDPOINTS["kill_switch_status"])
            status = KillSwitchStatus.from_dict(response)
            self._is_blocked = status.active
            self._kill_switch_reason = status.reason
        except Exception:
            # Polling failure should not crash the agent
            pass

        # Schedule next poll
        self._kill_switch_timer = threading.Timer(
            self._kill_switch_interval if hasattr(self, '_kill_switch_interval') else DEFAULT_KILL_SWITCH_INTERVAL,
            self._poll_kill_switch
        )
        self._kill_switch_timer.daemon = True
        self._kill_switch_timer.start()

    # =========================================================================
    # POLICY EVALUATION
    # =========================================================================

    def evaluate_policy(
        self,
        action_type: str,
        resource: str,
        risk_score: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> PolicyEvaluationResult:
        """
        Evaluate an action against policies without submitting it.

        Args:
            action_type: Action type to evaluate
            resource: Resource to evaluate against
            risk_score: Optional risk score hint
            context: Optional additional context

        Returns:
            PolicyEvaluationResult with decision and triggered rules
        """
        data: Dict[str, Any] = {
            "action_type": action_type,
            "resource": resource,
        }
        if risk_score is not None:
            data["risk_score"] = risk_score
        if context:
            data["context"] = context

        response = self._request(
            "POST",
            API_ENDPOINTS["evaluate_policy"],
            data=data
        )
        return PolicyEvaluationResult.from_dict(response)

    # =========================================================================
    # RESOURCE CLASSIFICATION
    # =========================================================================

    def get_resource_classification(
        self, resource_type: str
    ) -> Optional[ResourceClassification]:
        """
        Look up classification for a resource type.

        Args:
            resource_type: Resource type to look up

        Returns:
            ResourceClassification if found, None if not found
        """
        try:
            response = self._request(
                "GET",
                API_ENDPOINTS["resource_classifications"],
                params={"resource_type": resource_type}
            )
            items = response if isinstance(response, list) else response.get("classifications", [])
            for item in items:
                if item.get("resource_type") == resource_type:
                    return ResourceClassification.from_dict(item)
            return None
        except OWKAIError as e:
            if hasattr(e, 'details') and e.details.get("status_code") == 404:
                return None
            raise

    # =========================================================================
    # AUDIT TRAIL
    # =========================================================================

    def query_audit_log(
        self, limit: int = 50, offset: int = 0
    ) -> AuditLogResponse:
        """
        Query the audit log.

        Args:
            limit: Maximum entries to return (default: 50)
            offset: Pagination offset (default: 0)

        Returns:
            AuditLogResponse with total count and log entries
        """
        response = self._request(
            "GET",
            API_ENDPOINTS["audit_logs"],
            params={"limit": limit, "offset": offset}
        )
        return AuditLogResponse.from_dict(response)

    # =========================================================================
    # AGENT LIFECYCLE
    # =========================================================================

    def heartbeat(
        self,
        response_time_ms: Optional[int] = None,
        error_rate: Optional[float] = None,
        requests_count: Optional[int] = None,
    ) -> None:
        """
        Send a heartbeat to indicate the agent is alive.

        This method never raises exceptions — heartbeat failure
        must never crash the agent.

        Args:
            response_time_ms: Average response time in ms
            error_rate: Error rate (0.0 - 1.0)
            requests_count: Total requests processed
        """
        try:
            data: Dict[str, Any] = {
                "agent_id": self.agent_id,
                "sdk_version": SDK_VERSION,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if response_time_ms is not None:
                data["response_time_ms"] = response_time_ms
            if error_rate is not None:
                data["error_rate"] = error_rate
            if requests_count is not None:
                data["requests_count"] = requests_count

            self._request("POST", API_ENDPOINTS["heartbeat"], data=data)
        except Exception:
            # Fire and forget — heartbeat failure must never crash agent
            pass

    def deregister(self) -> None:
        """
        Deregister this agent from ASCEND platform.

        Stops kill switch polling if active.
        """
        self.stop_kill_switch_polling()
        self._request(
            "DELETE",
            API_ENDPOINTS["deregister_agent"].format(agent_id=self.agent_id)
        )
        self._registered = False
        logger.info("Agent deregistered", agent_id=self.agent_id)

    def get_agent_status(self) -> AgentHealthStatus:
        """
        Get health status of this agent.

        Returns:
            AgentHealthStatus with status, last heartbeat, metrics
        """
        response = self._request(
            "GET",
            API_ENDPOINTS["agent_status"].format(agent_id=self.agent_id)
        )
        return AgentHealthStatus.from_dict(response)

    # =========================================================================
    # BULK EVALUATION
    # =========================================================================

    def evaluate_actions(
        self,
        actions: List[Dict[str, Any]],
        max_concurrent: int = DEFAULT_BULK_CONCURRENCY,
    ) -> BulkEvaluationResult:
        """
        Evaluate multiple actions concurrently.

        Args:
            actions: List of action dicts, each with action_type and resource
            max_concurrent: Maximum concurrent evaluations (default: 5)

        Returns:
            BulkEvaluationResult with individual results and counts

        Raises:
            ValidationError: If more than 50 actions provided
        """
        if len(actions) > MAX_BULK_ACTIONS:
            raise ValidationError(
                f"Maximum {MAX_BULK_ACTIONS} actions per batch (got {len(actions)})",
                field_errors={"actions": f"Exceeds limit of {MAX_BULK_ACTIONS}"}
            )

        results: List[BulkActionResult] = []

        def _eval_single(action_dict: Dict[str, Any]) -> BulkActionResult:
            action = AgentAction(
                agent_id=self.agent_id or "unknown",
                agent_name=self.agent_name or "Unknown Agent",
                action_type=action_dict.get("action_type", ""),
                resource=action_dict.get("resource", ""),
                resource_id=action_dict.get("resource_id"),
                action_details=action_dict.get("parameters"),
                context=action_dict.get("context"),
                risk_indicators=action_dict.get("risk_indicators"),
            )
            try:
                decision = self.evaluate_action(
                    action_type=action.action_type,
                    resource=action.resource,
                    parameters=action.action_details,
                    context=action.context if isinstance(action.context, dict) else None,
                    resource_id=action.resource_id,
                    risk_indicators=action.risk_indicators if isinstance(action.risk_indicators, dict) else None,
                    wait_for_decision=False,
                )
                return BulkActionResult(
                    action_type=action.action_type,
                    resource=action.resource,
                    decision=decision,
                    error=None,
                    succeeded=True,
                )
            except Exception as e:
                return BulkActionResult(
                    action_type=action.action_type,
                    resource=action.resource,
                    decision=None,
                    error=str(e),
                    succeeded=False,
                )

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {executor.submit(_eval_single, a): a for a in actions}
            for future in as_completed(futures):
                results.append(future.result())

        succeeded_count = sum(1 for r in results if r.succeeded)
        failed_count = sum(1 for r in results if not r.succeeded)

        return BulkEvaluationResult(
            results=results,
            succeeded=succeeded_count,
            failed=failed_count,
            total=len(results),
        )

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def test_connection(self) -> SimpleNamespace:
        """
        Test API connectivity and authentication.

        Returns:
            SimpleNamespace with connection status and API version.
            Supports attribute access: result.connected, result.organization
        """
        try:
            health = self._request("GET", API_ENDPOINTS["health"])
            deployment = self._request("GET", API_ENDPOINTS["deployment_info"])

            return SimpleNamespace(
                connected=True,
                status="connected",
                api_version=deployment.get("version", "unknown"),
                environment=deployment.get("environment", "unknown"),
                organization=getattr(self, "organization_id", None),
                agent_id=self.agent_id,
                fail_mode=self.fail_mode.value,
            )
        except Exception as e:
            return SimpleNamespace(
                connected=False,
                status="error",
                error=str(e),
                organization=None,
                fail_mode=self.fail_mode.value,
            )

    def get_action_details(self, action_id: str) -> ActionDetails:
        """
        Get detailed information about an action including audit trail.
        """
        response = self._request(
            "GET",
            API_ENDPOINTS["action_details"].format(action_id=action_id)
        )
        return ActionDetails.from_dict(response)

    def list_actions(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List recent actions for this agent.
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if self.agent_id:
            params["agent_id"] = self.agent_id

        return self._request(
            "GET",
            API_ENDPOINTS["list_actions"],
            params=params
        )

    def close(self) -> None:
        """Close client session and stop background tasks."""
        self.stop_kill_switch_polling()
        self.stop_heartbeat()
        self._session.close()
        logger.debug("Client session closed")

    def __enter__(self) -> "AscendClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    # =========================================================================
    # SDK 2.4.0 — BUG-16 cohort / DOC-DRIFT-* deprecated method aliases
    #
    # The shims below forward to the canonical method and emit
    # DeprecationWarning ONCE per process per method (gated by the
    # class-level `_deprecation_warned_methods` set). They preserve
    # FailMode.CLOSED by delegating to methods that already honor it.
    # Removed in ascend-ai-sdk 3.0.0.
    # =========================================================================

    def submit_action(
        self,
        action_type_or_action: Any = None,
        resource: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AuthorizationDecision:
        """DEPRECATED (BUG-16): use :meth:`evaluate_action` instead.

        Accepts either the legacy single-arg form ``submit_action(action)``
        where ``action`` is an :class:`~ascend.models.AgentAction` or dict,
        or the modern keyword form matching :meth:`evaluate_action`. The
        shim normalizes both forms and forwards to ``evaluate_action``.
        """
        _emit_method_deprecation(
            "submit_action", "evaluate_action", "BUG-16"
        )

        # Legacy single-arg form: submit_action(action)
        if resource is None and isinstance(action_type_or_action, AgentAction):
            action = action_type_or_action
            return self.evaluate_action(
                action_type=action.action_type,
                resource=getattr(action, "resource", "") or kwargs.get("resource", ""),
                parameters=getattr(action, "parameters", None),
                context=getattr(action, "context", None),
                **{k: v for k, v in kwargs.items() if k != "resource"},
            )
        if resource is None and isinstance(action_type_or_action, dict):
            action = action_type_or_action
            return self.evaluate_action(
                action_type=action.get("action_type", ""),
                resource=action.get("resource", ""),
                parameters=action.get("parameters"),
                context=action.get("context"),
            )

        # Modern kwargs form
        return self.evaluate_action(
            action_type=action_type_or_action,
            resource=resource or "",
            parameters=parameters,
            context=context,
            **kwargs,
        )

    def send_heartbeat(
        self,
        metrics: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """DEPRECATED (DOC-DRIFT-HEARTBEAT): use :meth:`heartbeat` instead.

        Accepts a legacy ``metrics={"response_time_ms": ..., "error_rate": ...}``
        dict OR direct kwargs; forwards to :meth:`heartbeat`. Heartbeat
        semantics are preserved — this shim never raises, matching the
        canonical method's fail-safe contract.
        """
        _emit_method_deprecation(
            "send_heartbeat", "heartbeat", "DOC-DRIFT-HEARTBEAT"
        )
        merged: Dict[str, Any] = {}
        if metrics:
            merged.update(metrics)
        merged.update(kwargs)
        return self.heartbeat(
            response_time_ms=merged.get("response_time_ms"),
            error_rate=merged.get("error_rate"),
            requests_count=merged.get("requests_count"),
        )

    def wait_for_approval(
        self,
        action_id: str,
        timeout: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
        poll_interval: Optional[float] = None,
    ) -> AuthorizationDecision:
        """DEPRECATED (DOC-DRIFT-APPROVAL): use :meth:`wait_for_decision`.

        Accepts legacy ``timeout=`` kwarg (seconds) as well as the canonical
        ``timeout_seconds=``. Forwards to :meth:`wait_for_decision` with
        kwarg normalization.
        """
        _emit_method_deprecation(
            "wait_for_approval", "wait_for_decision", "DOC-DRIFT-APPROVAL"
        )
        resolved_timeout = timeout_seconds if timeout_seconds is not None else timeout
        kwargs: Dict[str, Any] = {}
        if resolved_timeout is not None:
            kwargs["timeout_seconds"] = resolved_timeout
        if poll_interval is not None:
            kwargs["poll_interval"] = poll_interval
        return self.wait_for_decision(action_id, **kwargs)

    def get_agent(self, agent_id: Optional[str] = None) -> AgentHealthStatus:
        """DEPRECATED (DOC-DRIFT-AGENT): use :meth:`get_agent_status`.

        Fail-secure: if ``agent_id`` is provided and does not match the
        client's configured agent identity, raises ValueError to prevent
        cross-agent information disclosure.
        """
        _emit_method_deprecation(
            "get_agent", "get_agent_status", "DOC-DRIFT-AGENT"
        )
        if agent_id is not None and agent_id != self.agent_id:
            raise ValueError(
                f"get_agent(agent_id={agent_id!r}) does not match "
                f"AscendClient.agent_id={self.agent_id!r}. Construct a "
                "separate AscendClient with the desired agent identity."
            )
        return self.get_agent_status()

    def register_agent(
        self,
        agent_id: Optional[str] = None,
        agent_type: str = "supervised",
        capabilities: Optional[List[str]] = None,
        allowed_resources: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """DEPRECATED (DOC-DRIFT-REGISTER): use :meth:`register` instead.

        The legacy call signature accepted ``agent_id`` as a positional
        argument; in the canonical SDK ``agent_id`` is supplied to the
        :class:`AscendClient` constructor. This shim validates that any
        explicit ``agent_id`` matches the client's configured agent_id
        (fail-secure: raises ValueError on mismatch to prevent a caller
        from accidentally registering the wrong identity).
        """
        _emit_method_deprecation(
            "register_agent", "register", "DOC-DRIFT-REGISTER"
        )
        if agent_id is not None and agent_id != self.agent_id:
            # Fail-secure: refuse to register an agent under a different
            # identity than the client was constructed with.
            raise ValueError(
                f"register_agent(agent_id={agent_id!r}) does not match "
                f"AscendClient.agent_id={self.agent_id!r}. Configure "
                "agent_id at client construction and call client.register() "
                "with no agent_id argument."
            )
        return self.register(
            agent_type=agent_type,
            capabilities=capabilities,
            allowed_resources=allowed_resources,
            metadata=metadata,
        )


# Backwards compatibility alias (internal only, not exported)
OWKAIClient = AscendClient


# ============================================================================
# SDK 2.4.0 — BUG-16 cohort: shared deprecation-warning helper
#
# Gates DeprecationWarning to once-per-process per (class, method) pair
# so noisy logs don't mask other warnings in production. `stacklevel=3`
# points the warning at the customer's call site (caller → shim → this).
# ============================================================================
_deprecation_warned_methods: set = set()


def _emit_method_deprecation(old_name: str, new_name: str, tag: str) -> None:
    """Emit DeprecationWarning once per process for a renamed method."""
    key = ("AscendClient", old_name)
    if key in _deprecation_warned_methods:
        return
    _deprecation_warned_methods.add(key)
    import warnings
    warnings.warn(
        f"AscendClient.{old_name}() is deprecated [{tag}]; "
        f"use AscendClient.{new_name}() instead. "
        f"This compat shim will be removed in ascend-ai-sdk 3.0.0.",
        DeprecationWarning,
        stacklevel=3,
    )
