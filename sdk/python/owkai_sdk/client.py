"""
ASCEND SDK Client
=================

Enterprise-grade HTTP client for ASCEND AI Governance API.

Security Standards:
- SOC 2 CC6.1: Access control audit trails
- HIPAA 164.312(e): Encryption in transit
- PCI-DSS 8.2: Secure credential handling
- NIST AI RMF: Risk assessment integration

Version: 2.0.0
"""

import os
import time
import json
import logging
import hashlib
import hmac
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from datetime import datetime, timezone
from functools import wraps

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import AgentAction, AuthorizationDecision, ActionDetails, DecisionStatus
from .exceptions import (
    OWKAIError,
    AuthenticationError,
    AuthorizationError,
    TimeoutError,
    RateLimitError,
    ValidationError,
    ConnectionError,
    CircuitBreakerOpen,
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
    def state(self) -> CircuitState:
        """Get current circuit state, checking for recovery timeout."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               time.time() - self._last_failure_time > self.recovery_timeout:
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


class AscendLogger:
    """
    Structured JSON logger with API key masking.

    Security: Never logs API keys or sensitive credentials.
    """

    def __init__(self, name: str = "ascend_sdk", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self._correlation_id: Optional[str] = None

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for request tracing."""
        self._correlation_id = correlation_id

    def _mask_sensitive(self, data: Any) -> Any:
        """Mask sensitive data like API keys."""
        if isinstance(data, str):
            # Mask API keys (owkai_..., sk_..., Bearer tokens)
            import re
            data = re.sub(r'owkai_[a-zA-Z0-9_]+', 'owkai_***MASKED***', data)
            data = re.sub(r'sk_[a-zA-Z0-9_]+', 'sk_***MASKED***', data)
            data = re.sub(r'Bearer [a-zA-Z0-9_\-\.]+', 'Bearer ***MASKED***', data)
            return data
        elif isinstance(data, dict):
            masked = {}
            for k, v in data.items():
                if k.lower() in ('api_key', 'apikey', 'authorization', 'x-api-key', 'password', 'secret'):
                    masked[k] = '***MASKED***'
                else:
                    masked[k] = self._mask_sensitive(v)
            return masked
        elif isinstance(data, list):
            return [self._mask_sensitive(item) for item in data]
        return data

    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """Format log message as JSON."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "logger": "ascend_sdk",
            "message": message,
        }

        if self._correlation_id:
            log_entry["correlation_id"] = self._correlation_id

        # Add extra fields (masked)
        for k, v in kwargs.items():
            log_entry[k] = self._mask_sensitive(v)

        return json.dumps(log_entry)

    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(self._format_message("DEBUG", message, **kwargs))

    def info(self, message: str, **kwargs) -> None:
        self.logger.info(self._format_message("INFO", message, **kwargs))

    def warning(self, message: str, **kwargs) -> None:
        self.logger.warning(self._format_message("WARNING", message, **kwargs))

    def error(self, message: str, **kwargs) -> None:
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
            api_key="sk_live_xxxxx",
            agent_id="my-agent-001",
            agent_name="My AI Agent",
            environment="production",
            fail_mode="closed"
        )

        # Register the agent
        client.register()

        # Evaluate an action
        decision = client.evaluate_action(
            action_type="financial.refund",
            resource="stripe_api",
            parameters={"amount": 100}
        )

        if decision.allowed:
            # Proceed with action
            result = process_refund()
            client.log_action_completed(decision.action_id, result=result)
        else:
            client.log_action_failed(decision.action_id, error={"reason": decision.reason})

    Attributes:
        api_url: Base URL for the ASCEND API
        agent_id: Unique identifier for this agent
        agent_name: Human-readable agent name
        environment: Deployment environment (production, staging, development)
        fail_mode: Behavior when ASCEND is unreachable (closed/open)
        timeout: Request timeout in seconds
    """

    DEFAULT_API_URL = "https://pilot.owkai.app"
    DEFAULT_TIMEOUT = 5  # 5 seconds per requirement
    DEFAULT_MAX_RETRIES = 3
    VERSION = "2.0.0"

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
        """
        # Configuration
        self.api_url = (
            api_url
            or os.getenv("ASCEND_API_URL")
            or os.getenv("OWKAI_API_URL")
            or self.DEFAULT_API_URL
        ).rstrip("/")

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
                format='%(message)s'  # JSON format from AscendLogger
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
            "User-Agent": f"ascend-sdk/{self.VERSION} Python",
            "X-SDK-Version": self.VERSION,
            "X-Environment": self.environment,
        })

        # Registration state
        self._registered = False
        self._registration_info: Optional[Dict] = None

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
                decision=DecisionStatus.AUTO_APPROVED,
                risk_score=0,
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
                    time.sleep(min(retry_after, 10))  # Cap at 10s for UX
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
                    wait_time = 2 ** retry_count  # Exponential backoff
                    logger.warning(f"Server error. Retrying in {wait_time}s...")
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
                wait_time = 2 ** retry_count
                logger.warning(f"Connection failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return self._request(method, endpoint, data, params, retry_count + 1)
            raise ConnectionError(
                f"Failed to connect to {self.api_url}",
                details={"original_error": str(e)}
            )

    def _safe_json(self, response) -> Dict[str, Any]:
        """Safely parse JSON response."""
        try:
            return response.json()
        except:
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

        Creates an agent record, assigns initial trust level, and returns
        registration confirmation.

        Args:
            agent_type: Type of agent (supervised, autonomous, mcp_server)
            capabilities: List of capabilities this agent has
            allowed_resources: Resources this agent can access
            metadata: Additional agent metadata

        Returns:
            Registration confirmation with agent details

        Example:
            client = AscendClient(
                api_key="sk_...",
                agent_id="my-agent",
                agent_name="My AI Agent"
            )

            result = client.register(
                agent_type="supervised",
                capabilities=["data_access", "transaction"],
                allowed_resources=["database", "api"]
            )
            print(f"Registered with trust level: {result['trust_level']}")
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
            "sdk_version": self.VERSION,
            "metadata": metadata or {}
        }

        try:
            result = self._request("POST", "/api/registry/agents", data=data)
            self._registered = True
            self._registration_info = result

            logger.info(
                "Agent registered successfully",
                agent_id=self.agent_id,
                trust_level=result.get("trust_level", "unknown")
            )

            return result
        except Exception as e:
            # Check if already registered (idempotent)
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
        timeout: Optional[int] = None
    ) -> AuthorizationDecision:
        """
        Evaluate an action against ASCEND policies.

        This is the primary method for checking if an action is allowed.

        Args:
            action_type: Category.action format (e.g., "financial.refund", "database.query")
            resource: Resource identifier (e.g., "stripe_api", "production_db")
            parameters: Action-specific parameters
            context: Additional context for risk scoring
            resource_id: Specific resource instance ID
            risk_indicators: Risk assessment hints
            wait_for_decision: Whether to wait for approval if pending
            timeout: Timeout for waiting (seconds)

        Returns:
            AuthorizationDecision with:
            - allowed: Boolean indicating if action is permitted
            - status: "allowed", "denied", or "pending_approval"
            - action_id: Unique ID for audit trail
            - reason: Explanation of decision
            - risk_score: 0-100 risk score
            - approval_request_id: If pending, ID to track approval

        Example:
            decision = client.evaluate_action(
                action_type="financial.refund",
                resource="stripe_api",
                parameters={"amount": 100, "currency": "USD"},
                context={"customer_id": "cust_123"}
            )

            if decision.allowed:
                process_refund()
            elif decision.status == "pending_approval":
                notify_approver(decision.approval_request_id)
            else:
                log_denial(decision.reason)
        """
        action = AgentAction(
            agent_id=self.agent_id or "unknown",
            agent_name=self.agent_name or "Unknown Agent",
            action_type=action_type,
            resource=resource,
            resource_id=resource_id,
            action_details=parameters,
            context=context,
            risk_indicators=risk_indicators
        )

        try:
            logger.info(
                "Evaluating action",
                action_type=action_type,
                resource=resource
            )

            response = self._request(
                "POST",
                "/api/authorization/agent-action",
                data=action.to_dict()
            )

            decision = AuthorizationDecision.from_dict(response)

            # Wait for decision if pending and requested
            if wait_for_decision and decision.decision == DecisionStatus.PENDING:
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

        Polls the API until a decision is made or timeout is reached.

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

                if decision.decision != DecisionStatus.PENDING:
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

        Required for SOC 2 audit trail compliance.

        Args:
            action_id: The action ID from evaluate_action
            result: Optional result data to log
            duration_ms: How long the action took in milliseconds

        Returns:
            Confirmation of logging

        Example:
            decision = client.evaluate_action(...)
            if decision.allowed:
                start = time.time()
                result = execute_action()
                duration = int((time.time() - start) * 1000)
                client.log_action_completed(
                    decision.action_id,
                    result={"status": "success"},
                    duration_ms=duration
                )
        """
        data = {
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
                f"/api/agent-action/{action_id}/complete",
                data=data
            )

            logger.info(
                "Action completion logged",
                action_id=action_id,
                duration_ms=duration_ms
            )

            return response
        except Exception as e:
            # Log locally even if API fails (audit trail backup)
            logger.warning(
                "Failed to log action completion to API, logged locally",
                action_id=action_id,
                error=str(e)
            )
            return {"logged_locally": True, "error": str(e)}

    def log_action_failed(
        self,
        action_id: str,
        error: Dict[str, Any],
        duration_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Log that an action failed.

        Required for SOC 2 audit trail compliance.

        Args:
            action_id: The action ID from evaluate_action
            error: Error details (code, message, etc.)
            duration_ms: How long before failure in milliseconds

        Returns:
            Confirmation of logging

        Example:
            decision = client.evaluate_action(...)
            if decision.allowed:
                try:
                    execute_action()
                except Exception as e:
                    client.log_action_failed(
                        decision.action_id,
                        error={"code": "EXECUTION_ERROR", "message": str(e)}
                    )
        """
        data = {
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
                f"/api/agent-action/{action_id}/fail",
                data=data
            )

            logger.info(
                "Action failure logged",
                action_id=action_id,
                error_code=error.get("code")
            )

            return response
        except Exception as e:
            # Log locally even if API fails (audit trail backup)
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
            Approval status with:
            - approved: Boolean
            - denied: Boolean
            - pending: Boolean
            - approver: Who approved/denied (if decided)
            - timestamp: When decision was made (if decided)
            - comments: Any comments from approver

        Example:
            if decision.status == "pending_approval":
                # Poll for approval
                while True:
                    status = client.check_approval(decision.approval_request_id)
                    if status["approved"]:
                        execute_action()
                        break
                    elif status["denied"]:
                        log_denial(status["comments"])
                        break
                    time.sleep(5)
        """
        response = self._request(
            "GET",
            f"/api/sdk/approval/{approval_request_id}"
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
            events: List of events to subscribe to:
                - "action.approved"
                - "action.denied"
                - "action.pending"
                - "policy.violation"
                - "agent.trust_changed"
            secret: Shared secret for webhook signature verification

        Returns:
            Webhook configuration details

        Example:
            client.configure_webhook(
                url="https://your-app.com/ascend-webhook",
                events=["action.approved", "action.denied", "policy.violation"],
                secret="whsec_your_secret_here"
            )

        Webhook Payload:
            {
                "event": "action.approved",
                "timestamp": "2025-12-03T10:00:00Z",
                "data": {
                    "action_id": "act_123",
                    "agent_id": "agent_001",
                    "approver": "admin@company.com"
                },
                "signature": "v1=abc123..."
            }

        Signature Verification:
            expected = hmac.new(secret, f"{timestamp}.{payload}", sha256).hexdigest()
            if not hmac.compare_digest(f"v1={expected}", signature):
                raise SecurityError("Invalid webhook signature")
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

        data = {
            "url": url,
            "events": events,
            "agent_id": self.agent_id,
        }

        if secret:
            data["secret"] = secret

        response = self._request(
            "POST",
            "/api/webhooks/configure",
            data=data
        )

        logger.info(
            "Webhook configured",
            url=url,
            events=events
        )

        return response

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def test_connection(self) -> Dict[str, Any]:
        """
        Test API connectivity and authentication.

        Returns:
            Dictionary with connection status and API version
        """
        try:
            health = self._request("GET", "/health")
            deployment = self._request("GET", "/api/deployment-info")

            return {
                "status": "connected",
                "api_version": deployment.get("version", "unknown"),
                "environment": deployment.get("environment", "unknown"),
                "agent_id": self.agent_id,
                "fail_mode": self.fail_mode.value
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "fail_mode": self.fail_mode.value
            }

    def get_action_details(self, action_id: str) -> ActionDetails:
        """
        Get detailed information about an action including audit trail.
        """
        response = self._request(
            "GET",
            f"/api/agent-action/{action_id}"
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
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if self.agent_id:
            params["agent_id"] = self.agent_id

        return self._request(
            "GET",
            "/api/agent-activity",
            params=params
        )


# Backwards compatibility alias
OWKAIClient = AscendClient
