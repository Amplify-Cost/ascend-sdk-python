"""
OW-AI SDK Client

Enterprise-grade client for AI Agent Authorization and Governance.
Supports both synchronous and asynchronous operations.

Features:
- API key authentication
- Agent action submission
- Approval workflow polling
- Risk assessment integration
- Comprehensive error handling

Example:
    from owkai import OWKAIClient

    client = OWKAIClient(api_key="owkai_admin_...")

    # Submit action
    result = client.execute_action(
        action_type="database_write",
        description="UPDATE users SET...",
        tool_name="postgresql"
    )

    # Wait for approval
    status = client.wait_for_approval(result.action_id)
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from owkai.auth import APIKeyAuth
from owkai.exceptions import (
    OWKAIActionRejectedError,
    OWKAIApprovalTimeoutError,
    OWKAIAuthenticationError,
    OWKAINetworkError,
    OWKAIRateLimitError,
    OWKAIServerError,
    OWKAIValidationError,
)
from owkai.models import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    ApprovalStatus,
    HealthStatus,
    RiskLevel,
    UsageStatistics,
)
from owkai.utils.logging import SDKLogger, get_logger
from owkai.utils.retry import RetryConfig, with_retry


class OWKAIClient:
    """
    Synchronous OW-AI SDK client.

    Enterprise-grade client for submitting agent actions to the
    OW-AI Authorization Platform and managing approval workflows.

    Attributes:
        base_url: OW-AI API base URL
        timeout: Request timeout in seconds
        retry_config: Configuration for automatic retries

    Example:
        client = OWKAIClient(
            api_key="owkai_admin_...",
            base_url="https://pilot.owkai.app"
        )

        result = client.execute_action(
            action_type="database_write",
            description="UPDATE users SET status='active'",
            tool_name="postgresql",
            target_system="production-db"
        )

        if result.requires_approval:
            status = client.wait_for_approval(result.action_id, timeout=300)
            if status.approved:
                print("Action approved, proceeding with execution")
    """

    DEFAULT_BASE_URL = "https://pilot.owkai.app"
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_USER_AGENT = "owkai-sdk/0.1.0 (Python)"

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        retry_config: Optional[RetryConfig] = None,
        logger: Optional[SDKLogger] = None,
    ) -> None:
        """
        Initialize OW-AI client.

        Args:
            api_key: OW-AI API key. If None, reads from OWKAI_API_KEY env var.
            base_url: API base URL (default: https://pilot.owkai.app)
            timeout: Request timeout in seconds (default: 30)
            retry_config: Retry configuration (default: 3 attempts)
            logger: Custom logger instance

        Raises:
            OWKAIAuthenticationError: If no API key provided
            OWKAIValidationError: If API key format is invalid
        """
        self._auth = APIKeyAuth(api_key)
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._retry_config = retry_config or RetryConfig()
        self._logger = logger or get_logger()

        # Create HTTP client
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={
                "User-Agent": self.DEFAULT_USER_AGENT,
                "Accept": "application/json",
                "Content-Type": "application/json",
                **self._auth.get_auth_headers(),
            },
        )

        self._logger.info(
            "OWKAIClient initialized",
            base_url=self._base_url,
            api_key_prefix=self._auth.key_prefix,
        )

    def __enter__(self) -> "OWKAIClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
        self._logger.debug("OWKAIClient closed")

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle HTTP response and convert to appropriate result or exception.

        Args:
            response: httpx Response object

        Returns:
            Parsed JSON response

        Raises:
            OWKAIAuthenticationError: On 401 responses
            OWKAIRateLimitError: On 429 responses
            OWKAIValidationError: On 422 responses
            OWKAIServerError: On 5xx responses
        """
        # Success responses
        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except Exception:
                return {"status": "success"}

        # Error handling
        try:
            error_data = response.json()
            error_message = error_data.get("detail", str(error_data))
        except Exception:
            error_message = response.text or f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise OWKAIAuthenticationError(
                error_message,
                error_code="AUTH_001",
                details={"status_code": response.status_code},
            )

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise OWKAIRateLimitError(
                error_message,
                retry_after=retry_after,
                error_code="RATE_001",
            )

        if response.status_code == 422:
            raise OWKAIValidationError(
                error_message,
                error_code="VALIDATION_001",
                details={"status_code": response.status_code},
            )

        if response.status_code >= 500:
            raise OWKAIServerError(
                error_message,
                status_code=response.status_code,
                error_code="SERVER_001",
            )

        # Other client errors
        raise OWKAIValidationError(
            error_message,
            error_code="CLIENT_001",
            details={"status_code": response.status_code},
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            json: JSON body for POST/PUT requests
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        @with_retry(self._retry_config)
        def _make_request() -> Dict[str, Any]:
            try:
                response = self._client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                )
                return self._handle_response(response)
            except httpx.NetworkError as e:
                raise OWKAINetworkError(
                    f"Network error: {str(e)}",
                    is_retryable=True,
                )
            except httpx.TimeoutException as e:
                raise OWKAINetworkError(
                    f"Request timeout: {str(e)}",
                    is_retryable=True,
                )

        return _make_request()

    # =========================================================================
    # Agent Action Methods
    # =========================================================================

    def execute_action(
        self,
        action_type: str,
        description: str,
        tool_name: str,
        *,
        agent_id: Optional[str] = None,
        target_system: Optional[str] = None,
        target_resource: Optional[str] = None,
        risk_context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ActionResult:
        """
        Submit an agent action for authorization.

        The action will be processed through the OW-AI platform's
        risk assessment engine and routed to the appropriate
        approval workflow.

        Args:
            action_type: Type of action (e.g., "database_write", "file_access")
            description: Detailed description of what the action will do
            tool_name: Name of the tool/service being used
            agent_id: Unique identifier for the agent (default: from API key)
            target_system: Target system (e.g., "production-db")
            target_resource: Specific resource being accessed
            risk_context: Additional context for risk assessment
            metadata: Custom metadata for audit trail

        Returns:
            ActionResult with action_id, status, and risk assessment

        Example:
            result = client.execute_action(
                action_type="database_write",
                description="UPDATE users SET status='active' WHERE id=123",
                tool_name="postgresql",
                target_system="production-db",
                risk_context={"contains_pii": True}
            )

            print(f"Action ID: {result.action_id}")
            print(f"Risk Score: {result.risk_score}")
            print(f"Requires Approval: {result.requires_approval}")
        """
        # Build request
        request = ActionRequest(
            agent_id=agent_id or f"sdk_{self._auth.key_prefix}",
            action_type=action_type,
            description=description,
            tool_name=tool_name,
            target_system=target_system,
            target_resource=target_resource,
            risk_context=risk_context,
            metadata=metadata,
        )

        self._logger.audit(
            "action_submitted",
            agent_id=request.agent_id,
            action_type=action_type,
            tool_name=tool_name,
        )

        # Submit to API
        response = self._request(
            "POST",
            "/api/authorization/agent-action",
            json=request.model_dump(exclude_none=True),
        )

        result = ActionResult.model_validate(response)

        self._logger.audit(
            "action_processed",
            action_id=result.action_id,
            status=result.status.value,
            risk_score=result.risk_score,
            requires_approval=result.requires_approval,
        )

        return result

    def get_action_status(self, action_id: int) -> ApprovalStatus:
        """
        Get current status of an action.

        Use this for polling approval status or checking
        final state of an action.

        Args:
            action_id: Action ID from execute_action()

        Returns:
            ApprovalStatus with current workflow state

        Example:
            status = client.get_action_status(123)
            if status.approved:
                print("Action approved!")
            elif status.status == ActionStatus.REJECTED:
                print(f"Rejected: {status.comments}")
        """
        response = self._request(
            "GET",
            f"/api/agent-action/status/{action_id}",
        )

        return ApprovalStatus.model_validate(response)

    def wait_for_approval(
        self,
        action_id: int,
        *,
        timeout: int = 300,
        poll_interval: Optional[int] = None,
    ) -> ApprovalStatus:
        """
        Wait for action approval with polling.

        Blocks until the action is approved, rejected, or timeout.
        Uses recommended polling intervals from the API.

        Args:
            action_id: Action ID from execute_action()
            timeout: Maximum seconds to wait (default: 300)
            poll_interval: Override polling interval (default: from API)

        Returns:
            Final ApprovalStatus

        Raises:
            OWKAIApprovalTimeoutError: If timeout exceeded
            OWKAIActionRejectedError: If action was rejected

        Example:
            try:
                status = client.wait_for_approval(action_id, timeout=300)
                print("Action approved!")
            except OWKAIApprovalTimeoutError:
                print("Approval not received in time")
            except OWKAIActionRejectedError as e:
                print(f"Action rejected: {e.rejection_reason}")
        """
        start_time = time.time()

        self._logger.info(
            "Waiting for approval",
            action_id=action_id,
            timeout=timeout,
        )

        while True:
            elapsed = time.time() - start_time

            if elapsed >= timeout:
                raise OWKAIApprovalTimeoutError(
                    f"Approval timeout after {timeout}s",
                    action_id=action_id,
                    timeout=timeout,
                )

            status = self.get_action_status(action_id)

            # Check for final states
            if status.is_final:
                if status.status == ActionStatus.REJECTED:
                    raise OWKAIActionRejectedError(
                        "Action was rejected",
                        action_id=action_id,
                        rejection_reason=status.comments,
                        rejected_by=status.reviewed_by,
                    )

                self._logger.audit(
                    "approval_received",
                    action_id=action_id,
                    status=status.status.value,
                    reviewed_by=status.reviewed_by,
                )
                return status

            # Wait before next poll
            interval = poll_interval or status.polling_interval_seconds
            remaining = timeout - elapsed
            sleep_time = min(interval, remaining)

            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_action_details(self, action_id: int) -> Dict[str, Any]:
        """
        Get full details of an action.

        Returns comprehensive action data including NIST/MITRE
        mappings, CVSS scores, and audit metadata.

        Args:
            action_id: Action ID

        Returns:
            Full action details dictionary
        """
        return self._request("GET", f"/api/agent-action/{action_id}")

    # =========================================================================
    # Health and Status Methods
    # =========================================================================

    def health_check(self) -> HealthStatus:
        """
        Check API health status.

        Returns:
            HealthStatus with service status information
        """
        response = self._request("GET", "/health")
        return HealthStatus.model_validate(response)

    def get_usage_statistics(self, key_id: Optional[int] = None) -> UsageStatistics:
        """
        Get API key usage statistics.

        Args:
            key_id: Specific key ID (default: current key)

        Returns:
            UsageStatistics with request counts and activity
        """
        if key_id:
            response = self._request("GET", f"/api/keys/{key_id}/usage")
        else:
            # List keys to get current key ID, then get usage
            keys_response = self._request("GET", "/api/keys/list")
            if keys_response.get("keys"):
                key_id = keys_response["keys"][0]["id"]
                response = self._request("GET", f"/api/keys/{key_id}/usage")
            else:
                response = {"statistics": {}}

        stats = response.get("statistics", response)
        return UsageStatistics.model_validate(stats)


class AsyncOWKAIClient:
    """
    Asynchronous OW-AI SDK client.

    Async version of OWKAIClient for use with asyncio.
    Provides the same functionality with async/await syntax.

    Example:
        async with AsyncOWKAIClient(api_key="owkai_admin_...") as client:
            result = await client.execute_action(...)
            status = await client.wait_for_approval(result.action_id)
    """

    DEFAULT_BASE_URL = OWKAIClient.DEFAULT_BASE_URL
    DEFAULT_TIMEOUT = OWKAIClient.DEFAULT_TIMEOUT
    DEFAULT_USER_AGENT = OWKAIClient.DEFAULT_USER_AGENT

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        retry_config: Optional[RetryConfig] = None,
        logger: Optional[SDKLogger] = None,
    ) -> None:
        """Initialize async client with same parameters as OWKAIClient."""
        self._auth = APIKeyAuth(api_key)
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._retry_config = retry_config or RetryConfig()
        self._logger = logger or get_logger()

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={
                "User-Agent": self.DEFAULT_USER_AGENT,
                "Accept": "application/json",
                "Content-Type": "application/json",
                **self._auth.get_auth_headers(),
            },
        )

        self._logger.info(
            "AsyncOWKAIClient initialized",
            base_url=self._base_url,
            api_key_prefix=self._auth.key_prefix,
        )

    async def __aenter__(self) -> "AsyncOWKAIClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the async HTTP client."""
        await self._client.aclose()
        self._logger.debug("AsyncOWKAIClient closed")

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response (same logic as sync client)."""
        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except Exception:
                return {"status": "success"}

        try:
            error_data = response.json()
            error_message = error_data.get("detail", str(error_data))
        except Exception:
            error_message = response.text or f"HTTP {response.status_code}"

        if response.status_code == 401:
            raise OWKAIAuthenticationError(error_message, error_code="AUTH_001")

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            raise OWKAIRateLimitError(error_message, retry_after=retry_after)

        if response.status_code == 422:
            raise OWKAIValidationError(error_message, error_code="VALIDATION_001")

        if response.status_code >= 500:
            raise OWKAIServerError(error_message, status_code=response.status_code)

        raise OWKAIValidationError(error_message, error_code="CLIENT_001")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make async HTTP request."""
        try:
            response = await self._client.request(
                method=method,
                url=path,
                json=json,
                params=params,
            )
            return await self._handle_response(response)
        except httpx.NetworkError as e:
            raise OWKAINetworkError(f"Network error: {str(e)}", is_retryable=True)
        except httpx.TimeoutException as e:
            raise OWKAINetworkError(f"Request timeout: {str(e)}", is_retryable=True)

    async def execute_action(
        self,
        action_type: str,
        description: str,
        tool_name: str,
        *,
        agent_id: Optional[str] = None,
        target_system: Optional[str] = None,
        target_resource: Optional[str] = None,
        risk_context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ActionResult:
        """Submit an agent action (async version)."""
        request = ActionRequest(
            agent_id=agent_id or f"sdk_{self._auth.key_prefix}",
            action_type=action_type,
            description=description,
            tool_name=tool_name,
            target_system=target_system,
            target_resource=target_resource,
            risk_context=risk_context,
            metadata=metadata,
        )

        self._logger.audit(
            "action_submitted",
            agent_id=request.agent_id,
            action_type=action_type,
        )

        response = await self._request(
            "POST",
            "/api/authorization/agent-action",
            json=request.model_dump(exclude_none=True),
        )

        result = ActionResult.model_validate(response)

        self._logger.audit(
            "action_processed",
            action_id=result.action_id,
            status=result.status.value,
            risk_score=result.risk_score,
        )

        return result

    async def get_action_status(self, action_id: int) -> ApprovalStatus:
        """Get action status (async version)."""
        response = await self._request("GET", f"/api/agent-action/status/{action_id}")
        return ApprovalStatus.model_validate(response)

    async def wait_for_approval(
        self,
        action_id: int,
        *,
        timeout: int = 300,
        poll_interval: Optional[int] = None,
    ) -> ApprovalStatus:
        """Wait for approval (async version)."""
        import asyncio

        start_time = time.time()

        self._logger.info(
            "Waiting for approval (async)",
            action_id=action_id,
            timeout=timeout,
        )

        while True:
            elapsed = time.time() - start_time

            if elapsed >= timeout:
                raise OWKAIApprovalTimeoutError(
                    f"Approval timeout after {timeout}s",
                    action_id=action_id,
                    timeout=timeout,
                )

            status = await self.get_action_status(action_id)

            if status.is_final:
                if status.status == ActionStatus.REJECTED:
                    raise OWKAIActionRejectedError(
                        "Action was rejected",
                        action_id=action_id,
                        rejection_reason=status.comments,
                        rejected_by=status.reviewed_by,
                    )

                self._logger.audit(
                    "approval_received",
                    action_id=action_id,
                    status=status.status.value,
                )
                return status

            interval = poll_interval or status.polling_interval_seconds
            remaining = timeout - elapsed
            sleep_time = min(interval, remaining)

            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    async def health_check(self) -> HealthStatus:
        """Check API health (async version)."""
        response = await self._request("GET", "/health")
        return HealthStatus.model_validate(response)
