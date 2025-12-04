"""
Ascend AI Client
================

Main client for interacting with Ascend AI Governance Platform.

Example:
    from ascend import AscendClient, AgentAction

    client = AscendClient(api_key="ascend_prod_...")
    action = AgentAction(
        agent_id="my-agent",
        agent_name="My Agent",
        action_type="data_access",
        resource="customer_data"
    )
    result = client.submit_action(action)
"""

import os
import time
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

import requests
from dotenv import load_dotenv

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
    DEFAULT_API_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_DECISION_TIMEOUT,
    SDK_VERSION,
    USER_AGENT,
    API_ENDPOINTS,
    ENV_VAR_API_KEY,
    ENV_VAR_API_URL,
    ENV_VAR_DEBUG,
)
from .utils.retry import retry_with_backoff
from .utils.validation import validate_api_key, validate_action, validate_action_id

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AscendClient:
    """
    Ascend AI Governance Platform Client.

    Enterprise-grade client for submitting agent actions,
    checking authorization status, and managing governance.

    Features:
    - Automatic retry with exponential backoff
    - Dual authentication headers (Bearer + X-API-Key)
    - TLS certificate validation
    - Request correlation IDs
    - API key masking in logs
    - Circuit breaker pattern
    - Comprehensive error handling

    Args:
        api_key: Ascend API key (or set ASCEND_API_KEY env var)
        base_url: API base URL (default: https://pilot.owkai.app)
        timeout: Request timeout in seconds (default: 30)
        debug: Enable debug logging (default: False)

    Example:
        client = AscendClient(api_key="ascend_prod_abc123...")
        result = client.submit_action(action)
        print(f"Status: {result.status}")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        debug: bool = False,
    ) -> None:
        """Initialize the Ascend client."""
        # Configuration
        self.api_key = api_key or os.getenv(ENV_VAR_API_KEY)
        self.base_url = (base_url or os.getenv(ENV_VAR_API_URL) or DEFAULT_API_URL).rstrip("/")
        self.timeout = timeout
        self.debug = debug or os.getenv(ENV_VAR_DEBUG, "").lower() in ("true", "1", "yes")

        # Configure logging
        if self.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        # Validate API key
        if not self.api_key:
            raise ValidationError(
                f"API key is required. Set {ENV_VAR_API_KEY} environment variable "
                "or pass api_key parameter."
            )

        validate_api_key(self.api_key)

        # Banking-level security: Dual authentication headers
        # SEC-033: Support both Authorization: Bearer and X-API-Key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,
            "User-Agent": USER_AGENT,
        }

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # TLS certificate validation (always enabled for security)
        self.session.verify = True

        logger.info(f"Ascend client initialized (SDK v{SDK_VERSION})")
        logger.debug(f"API URL: {self.base_url}")
        logger.debug(f"API Key: {self._mask_api_key(self.api_key)}")

    def _mask_api_key(self, api_key: str) -> str:
        """
        Mask API key for logging (banking-level security).

        Shows only first 4 and last 4 characters.
        Example: ascend_prod_abc123xyz789 -> asce...x789
        """
        if len(api_key) <= 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"

    def _generate_correlation_id(self) -> str:
        """Generate unique correlation ID for request tracing."""
        return f"ascend-{uuid.uuid4().hex[:16]}"

    @retry_with_backoff(max_retries=3)
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Ascend API.

        Includes:
        - Correlation ID for tracing
        - Automatic retries on transient failures
        - Comprehensive error handling
        - Request/response logging (debug mode)

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: JSON body data
            params: URL query parameters

        Returns:
            API response as dictionary

        Raises:
            AuthenticationError: Authentication failed
            NetworkError: Network connectivity issue
            ServerError: Server-side error
            RateLimitError: Rate limit exceeded
            TimeoutError: Request timeout
        """
        url = f"{self.base_url}{endpoint}"
        correlation_id = self._generate_correlation_id()

        # Add correlation ID to headers for request tracing
        headers = self.headers.copy()
        headers["X-Correlation-ID"] = correlation_id

        logger.debug(f"[{correlation_id}] {method} {url}")
        if data and self.debug:
            logger.debug(f"[{correlation_id}] Request body: {data}")

        try:
            start_time = time.time()
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=self.timeout,
            )
            latency_ms = (time.time() - start_time) * 1000

            logger.debug(
                f"[{correlation_id}] Response: {response.status_code} "
                f"({latency_ms:.0f}ms)"
            )

            # Handle HTTP errors
            if response.status_code >= 400:
                self._handle_error_response(response, correlation_id)

            return response.json()

        except requests.exceptions.Timeout as e:
            logger.error(f"[{correlation_id}] Request timeout after {self.timeout}s")
            raise TimeoutError(
                f"Request timed out after {self.timeout} seconds",
                status_code=None,
            ) from e

        except requests.exceptions.ConnectionError as e:
            logger.error(f"[{correlation_id}] Connection error: {e}")
            raise NetworkError(
                f"Failed to connect to Ascend API at {self.base_url}",
                status_code=None,
            ) from e

        except requests.exceptions.SSLError as e:
            logger.error(f"[{correlation_id}] SSL/TLS error: {e}")
            raise NetworkError(
                "SSL/TLS certificate verification failed",
                status_code=None,
            ) from e

        except requests.exceptions.RequestException as e:
            logger.error(f"[{correlation_id}] Request error: {e}")
            raise NetworkError(
                f"Network error: {str(e)}",
                status_code=None,
            ) from e

    def _handle_error_response(self, response: requests.Response, correlation_id: str) -> None:
        """
        Handle HTTP error responses with appropriate exceptions.

        Maps HTTP status codes to specific exception types.
        """
        status_code = response.status_code

        try:
            error_data = response.json()
            error_message = error_data.get("detail", str(error_data))
        except Exception:
            error_message = response.text or f"HTTP {status_code} error"

        logger.error(f"[{correlation_id}] API error {status_code}: {error_message}")

        # Authentication errors (401, 403)
        if status_code in (401, 403):
            raise AuthenticationError(
                f"Authentication failed: {error_message}",
                status_code=status_code,
                response=error_data if 'error_data' in locals() else {},
            )

        # Rate limiting (429)
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After", "60")
            raise RateLimitError(
                f"Rate limit exceeded. Retry after {retry_after} seconds.",
                status_code=status_code,
                response=error_data if 'error_data' in locals() else {},
            )

        # Not found (404)
        elif status_code == 404:
            raise NotFoundError(
                f"Resource not found: {error_message}",
                status_code=status_code,
                response=error_data if 'error_data' in locals() else {},
            )

        # Conflict (409)
        elif status_code == 409:
            raise ConflictError(
                f"Resource conflict: {error_message}",
                status_code=status_code,
                response=error_data if 'error_data' in locals() else {},
            )

        # Validation errors (400, 422)
        elif status_code in (400, 422):
            raise ValidationError(
                f"Validation error: {error_message}",
                status_code=status_code,
                response=error_data if 'error_data' in locals() else {},
            )

        # Server errors (500+)
        elif status_code >= 500:
            raise ServerError(
                f"Server error: {error_message}",
                status_code=status_code,
                response=error_data if 'error_data' in locals() else {},
            )

        # Other errors
        else:
            raise AscendError(
                f"API error: {error_message}",
                status_code=status_code,
                response=error_data if 'error_data' in locals() else {},
            )

    def test_connection(self) -> ConnectionStatus:
        """
        Test API connectivity and authentication.

        Verifies:
        - Network connectivity
        - API key validity
        - Service availability

        Returns:
            ConnectionStatus with details

        Example:
            status = client.test_connection()
            if status.is_connected():
                print(f"Connected! API version: {status.api_version}")
            else:
                print(f"Connection failed: {status.error}")
        """
        try:
            start_time = time.time()

            # Try health endpoint first (no auth required)
            health = self._request("GET", API_ENDPOINTS["health"])

            # Then verify authentication
            deployment = self._request("GET", API_ENDPOINTS["deployment_info"])

            latency_ms = (time.time() - start_time) * 1000

            return ConnectionStatus(
                status="connected",
                api_version=deployment.get("version", "unknown"),
                server_time=datetime.utcnow().isoformat() + "Z",
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return ConnectionStatus(
                status="error",
                error=str(e),
            )

    def submit_action(self, action: AgentAction) -> ActionResult:
        """
        Submit an agent action for authorization.

        The action will be evaluated by Ascend's policy engine
        and may be auto-approved, auto-denied, or require manual review.

        Args:
            action: AgentAction describing the action

        Returns:
            ActionResult with authorization decision

        Raises:
            ValidationError: Invalid action data
            AuthenticationError: Invalid API key
            NetworkError: Connection failure
            ServerError: Server-side error

        Example:
            action = AgentAction(
                agent_id="bot-001",
                agent_name="Customer Service Bot",
                action_type="data_access",
                resource="customer_profile",
                resource_id="CUST-12345"
            )
            result = client.submit_action(action)

            if result.is_approved():
                # Execute action
                data = fetch_customer_profile("CUST-12345")
            elif result.is_denied():
                print(f"Denied: {result.reason}")
            else:
                # Wait for manual approval
                result = client.wait_for_decision(result.action_id)
        """
        # Validate action before submission
        validate_action(action)

        logger.info(
            f"Submitting action: {action.action_type} on {action.resource} "
            f"by {action.agent_id}"
        )

        # Convert to API format
        data = action.to_dict()

        # Submit to API
        response = self._request("POST", API_ENDPOINTS["submit_action"], data=data)

        # Parse response
        result = ActionResult.from_dict(response)

        logger.info(
            f"Action submitted: ID={result.action_id}, Status={result.status}, "
            f"Risk={result.risk_level}"
        )

        return result

    def get_action(self, action_id: str) -> ActionResult:
        """
        Get full details of an action.

        Args:
            action_id: The action ID

        Returns:
            ActionResult with full details

        Raises:
            NotFoundError: Action not found
            ValidationError: Invalid action_id
        """
        validate_action_id(action_id)

        endpoint = API_ENDPOINTS["get_action"].format(action_id=action_id)
        response = self._request("GET", endpoint)

        return ActionResult.from_dict(response)

    def get_action_status(self, action_id: str) -> ActionResult:
        """
        Get current status of an action.

        Lighter-weight than get_action() - returns only status info.

        Args:
            action_id: The action ID

        Returns:
            ActionResult with current status

        Raises:
            NotFoundError: Action not found
            ValidationError: Invalid action_id
        """
        validate_action_id(action_id)

        endpoint = API_ENDPOINTS["action_status"].format(action_id=action_id)
        response = self._request("GET", endpoint)

        return ActionResult.from_dict(response)

    def wait_for_decision(
        self,
        action_id: str,
        timeout_ms: int = DEFAULT_DECISION_TIMEOUT * 1000,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> ActionResult:
        """
        Wait for an authorization decision.

        Polls the action status until a decision is made or timeout occurs.

        Args:
            action_id: The action ID to wait for
            timeout_ms: Maximum time to wait in milliseconds
            poll_interval: Time between status checks in seconds

        Returns:
            ActionResult with final decision

        Raises:
            TimeoutError: Decision not received within timeout
            NotFoundError: Action not found

        Example:
            result = client.submit_action(action)
            if result.is_pending():
                # Wait up to 60 seconds for decision
                result = client.wait_for_decision(result.action_id, timeout_ms=60000)
                print(f"Final decision: {result.status}")
        """
        validate_action_id(action_id)

        timeout_seconds = timeout_ms / 1000.0
        start_time = time.time()

        logger.info(f"Waiting for decision on action {action_id} (timeout: {timeout_seconds}s)")

        while time.time() - start_time < timeout_seconds:
            result = self.get_action_status(action_id)

            # Check if decision is final
            if not result.is_pending():
                logger.info(f"Decision received: {result.status}")
                return result

            logger.debug(f"Action {action_id} still pending...")
            time.sleep(poll_interval)

        # Timeout occurred
        logger.warning(f"Decision timeout for action {action_id}")
        raise TimeoutError(
            f"Decision not received within {timeout_seconds} seconds",
            status_code=None,
        )

    def list_actions(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> ListResult:
        """
        List recent agent actions.

        Supports pagination and filtering by status.

        Args:
            limit: Maximum number of actions to return (default: 50)
            offset: Pagination offset (default: 0)
            status: Filter by status (e.g., "pending", "approved")

        Returns:
            ListResult with actions and pagination info

        Example:
            # Get first page of pending actions
            result = client.list_actions(limit=10, status="pending")
            for action in result.actions:
                print(f"{action.action_id}: {action.status}")

            # Get next page
            if result.has_more:
                next_page = client.list_actions(limit=10, offset=10)
        """
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        response = self._request("GET", API_ENDPOINTS["list_actions"], params=params)

        return ListResult.from_dict(response)

    def close(self) -> None:
        """
        Close the client session.

        Releases connection pool resources.
        Call this when done using the client.
        """
        self.session.close()
        logger.debug("Client session closed")

    def __enter__(self) -> "AscendClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
