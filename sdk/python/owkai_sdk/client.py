"""
OW-AI SDK Client
================

Enterprise-grade HTTP client for OW-AI Authorization API.
"""

import os
import time
import logging
from typing import Optional, Dict, Any, List

import requests

from .models import AgentAction, AuthorizationDecision, ActionDetails, DecisionStatus
from .exceptions import (
    OWKAIError,
    AuthenticationError,
    AuthorizationError,
    TimeoutError,
    RateLimitError,
    ValidationError,
    ConnectionError
)

logger = logging.getLogger("owkai_sdk")


class OWKAIClient:
    """
    OW-AI Authorization Center SDK Client.

    Enterprise-grade client for submitting agent actions
    for authorization and policy enforcement.

    Example:
        client = OWKAIClient(api_key="your-api-key")

        # Test connection
        status = client.test_connection()

        # Submit action
        action = AgentAction(
            agent_id="agent-001",
            agent_name="My Agent",
            action_type="data_access",
            resource="customer_data"
        )
        response = client.submit_action(action)

    Attributes:
        api_url: Base URL for the OW-AI API
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts for transient failures
    """

    DEFAULT_API_URL = "https://pilot.owkai.app"
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        organization_slug: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        debug: bool = False
    ):
        """
        Initialize the OW-AI client.

        Args:
            api_url: API endpoint URL (default: from OWKAI_API_URL env var)
            api_key: Organization API key (default: from OWKAI_API_KEY env var)
            organization_slug: Organization identifier (default: from OWKAI_ORG_SLUG)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            debug: Enable debug logging

        Raises:
            ValueError: If API key is not provided
        """
        self.api_url = (
            api_url
            or os.getenv("OWKAI_API_URL")
            or self.DEFAULT_API_URL
        )
        self.api_key = api_key or os.getenv("OWKAI_API_KEY")
        self.organization_slug = organization_slug or os.getenv("OWKAI_ORG_SLUG")
        self.timeout = timeout
        self.max_retries = max_retries

        if debug:
            logger.setLevel(logging.DEBUG)
            logging.basicConfig(level=logging.DEBUG)

        if not self.api_key:
            raise ValueError(
                "API key is required. "
                "Pass api_key parameter or set OWKAI_API_KEY environment variable."
            )

        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "owkai-sdk/1.0.0 Python"
        })

        logger.info(f"OW-AI Client initialized for {self.api_url}")

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make authenticated request to API with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            API response as dictionary

        Raises:
            AuthenticationError: On 401 responses
            AuthorizationError: On 403 responses
            RateLimitError: On 429 responses
            ValidationError: On 400/422 responses
            OWKAIError: On other errors
        """
        url = f"{self.api_url}{endpoint}"
        logger.debug(f"{method.upper()} {url}")

        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )

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
                    time.sleep(retry_after)
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
            raise TimeoutError(
                f"Request timed out after {self.timeout}s",
                timeout_seconds=self.timeout
            )

        except requests.exceptions.ConnectionError as e:
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

    def test_connection(self) -> Dict[str, Any]:
        """
        Test API connectivity and authentication.

        Returns:
            Dictionary with connection status and API version

        Example:
            status = client.test_connection()
            if status["status"] == "connected":
                print(f"Connected to API v{status['api_version']}")
        """
        try:
            health = self._request("GET", "/health")
            deployment = self._request("GET", "/api/deployment-info")

            return {
                "status": "connected",
                "api_version": deployment.get("version", "unknown"),
                "environment": deployment.get("environment", "unknown"),
                "organization": self.organization_slug
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def submit_action(self, action: AgentAction) -> AuthorizationDecision:
        """
        Submit an agent action for authorization.

        Args:
            action: AgentAction object describing the action

        Returns:
            AuthorizationDecision with action_id and initial status

        Example:
            action = AgentAction(
                agent_id="agent-001",
                agent_name="Financial Advisor",
                action_type="transaction",
                resource="customer_account"
            )
            decision = client.submit_action(action)
        """
        logger.info(f"Submitting action: {action.action_type} on {action.resource}")

        response = self._request(
            "POST",
            "/api/authorization/agent-action",
            data=action.to_dict()
        )

        decision = AuthorizationDecision.from_dict(response)
        logger.info(f"Action submitted: {decision.action_id} - Status: {decision.decision.value}")

        return decision

    def get_action_status(self, action_id: str) -> AuthorizationDecision:
        """
        Get the current status of an action.

        Args:
            action_id: The action ID returned from submit_action

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
            decision = self.get_action_status(action_id)

            if decision.decision != DecisionStatus.PENDING:
                return decision

            logger.debug(f"Action {action_id} still pending...")
            time.sleep(poll_interval)

        raise TimeoutError(
            f"Decision not received within {timeout} seconds",
            timeout_seconds=timeout
        )

    def get_action_details(self, action_id: str) -> ActionDetails:
        """
        Get detailed information about an action.

        Includes full audit trail and metadata.

        Args:
            action_id: The action ID

        Returns:
            Full action details including audit trail
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
        status: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List recent agent actions.

        Args:
            limit: Maximum number of actions to return
            offset: Pagination offset
            status: Filter by status (pending, approved, denied)
            agent_id: Filter by agent ID

        Returns:
            Dictionary with actions list and pagination info
        """
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if agent_id:
            params["agent_id"] = agent_id

        return self._request(
            "GET",
            "/api/agent-activity",
            params=params
        )

    def approve_action(
        self,
        action_id: str,
        comments: Optional[str] = None
    ) -> AuthorizationDecision:
        """
        Approve a pending action (requires admin privileges).

        Args:
            action_id: The action ID to approve
            comments: Optional approval comments

        Returns:
            Updated authorization decision
        """
        response = self._request(
            "POST",
            f"/api/authorization/authorize/{action_id}",
            data={
                "approved": True,
                "comments": comments or "Approved via SDK"
            }
        )
        return AuthorizationDecision.from_dict(response)

    def deny_action(
        self,
        action_id: str,
        reason: str
    ) -> AuthorizationDecision:
        """
        Deny a pending action (requires admin privileges).

        Args:
            action_id: The action ID to deny
            reason: Reason for denial

        Returns:
            Updated authorization decision
        """
        response = self._request(
            "POST",
            f"/api/authorization/authorize/{action_id}",
            data={
                "approved": False,
                "comments": reason
            }
        )
        return AuthorizationDecision.from_dict(response)
