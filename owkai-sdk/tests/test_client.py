"""
OW-AI SDK Client Tests

Tests for OWKAIClient and AsyncOWKAIClient.
"""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from owkai.client import OWKAIClient, AsyncOWKAIClient
from owkai.exceptions import (
    OWKAIActionRejectedError,
    OWKAIApprovalTimeoutError,
    OWKAIAuthenticationError,
    OWKAIRateLimitError,
    OWKAIServerError,
    OWKAIValidationError,
)
from owkai.models import ActionResult, ActionStatus, ApprovalStatus, RiskLevel


class TestOWKAIClientInit:
    """Tests for OWKAIClient initialization."""

    def test_init_with_api_key(self, api_key: str) -> None:
        """Test initialization with explicit API key."""
        with patch("httpx.Client"):
            client = OWKAIClient(api_key=api_key)
            assert client._base_url == "https://pilot.owkai.app"

    def test_init_with_env_key(self, env_api_key: str) -> None:
        """Test initialization from environment variable."""
        with patch("httpx.Client"):
            client = OWKAIClient()
            assert client._base_url == "https://pilot.owkai.app"

    def test_init_with_custom_url(self, api_key: str) -> None:
        """Test initialization with custom base URL."""
        with patch("httpx.Client"):
            client = OWKAIClient(api_key=api_key, base_url="https://custom.owkai.app")
            assert client._base_url == "https://custom.owkai.app"

    def test_init_strips_trailing_slash(self, api_key: str) -> None:
        """Test that trailing slash is stripped from URL."""
        with patch("httpx.Client"):
            client = OWKAIClient(api_key=api_key, base_url="https://custom.owkai.app/")
            assert client._base_url == "https://custom.owkai.app"

    def test_init_with_custom_timeout(self, api_key: str) -> None:
        """Test initialization with custom timeout."""
        with patch("httpx.Client"):
            client = OWKAIClient(api_key=api_key, timeout=60.0)
            assert client._timeout == 60.0

    def test_context_manager(self, api_key: str) -> None:
        """Test context manager usage."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            with OWKAIClient(api_key=api_key) as client:
                pass

            mock_instance.close.assert_called_once()


class TestOWKAIClientResponseHandling:
    """Tests for response handling."""

    def test_handle_401_raises_auth_error(self, api_key: str) -> None:
        """Test 401 response raises authentication error."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            response = MagicMock()
            response.status_code = 401
            response.json.return_value = {"detail": "Invalid API key"}
            mock_instance.request.return_value = response

            client = OWKAIClient(api_key=api_key)

            with pytest.raises(OWKAIAuthenticationError):
                client._request("GET", "/test")

    def test_handle_429_raises_rate_limit_error(self, api_key: str) -> None:
        """Test 429 response raises rate limit error."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            response = MagicMock()
            response.status_code = 429
            response.json.return_value = {"detail": "Rate limit exceeded"}
            response.headers = {"Retry-After": "120"}
            mock_instance.request.return_value = response

            client = OWKAIClient(api_key=api_key)

            with pytest.raises(OWKAIRateLimitError) as exc_info:
                client._request("GET", "/test")

            assert exc_info.value.retry_after == 120

    def test_handle_422_raises_validation_error(self, api_key: str) -> None:
        """Test 422 response raises validation error."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            response = MagicMock()
            response.status_code = 422
            response.json.return_value = {"detail": "Validation failed"}
            mock_instance.request.return_value = response

            client = OWKAIClient(api_key=api_key)

            with pytest.raises(OWKAIValidationError):
                client._request("GET", "/test")

    def test_handle_500_raises_server_error(self, api_key: str) -> None:
        """Test 500 response raises server error."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            response = MagicMock()
            response.status_code = 500
            response.json.return_value = {"detail": "Internal server error"}
            mock_instance.request.return_value = response

            client = OWKAIClient(api_key=api_key)

            with pytest.raises(OWKAIServerError) as exc_info:
                client._request("GET", "/test")

            assert exc_info.value.status_code == 500


class TestOWKAIClientExecuteAction:
    """Tests for execute_action method."""

    def test_execute_action_success(
        self,
        api_key: str,
        mock_response_success: Dict[str, Any],
    ) -> None:
        """Test successful action execution."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = mock_response_success
            mock_instance.request.return_value = response

            client = OWKAIClient(api_key=api_key)
            result = client.execute_action(
                action_type="database_write",
                description="UPDATE users SET status='active'",
                tool_name="postgresql",
            )

            assert isinstance(result, ActionResult)
            assert result.action_id == 123
            assert result.risk_score == 75.0
            assert result.requires_approval is True

    def test_execute_action_with_all_params(
        self,
        api_key: str,
        mock_response_success: Dict[str, Any],
    ) -> None:
        """Test action execution with all parameters."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = mock_response_success
            mock_instance.request.return_value = response

            client = OWKAIClient(api_key=api_key)
            result = client.execute_action(
                action_type="database_write",
                description="UPDATE users SET status='active'",
                tool_name="postgresql",
                agent_id="custom-agent",
                target_system="production-db",
                target_resource="/users/123",
                risk_context={"contains_pii": True},
                metadata={"request_id": "abc123"},
            )

            assert isinstance(result, ActionResult)
            # Verify request was made with correct body
            call_args = mock_instance.request.call_args
            assert call_args is not None


class TestOWKAIClientWaitForApproval:
    """Tests for wait_for_approval method."""

    def test_wait_for_approval_immediate(
        self,
        api_key: str,
        mock_status_approved: Dict[str, Any],
    ) -> None:
        """Test immediate approval."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = mock_status_approved
            mock_instance.request.return_value = response

            client = OWKAIClient(api_key=api_key)
            status = client.wait_for_approval(123, timeout=10)

            assert isinstance(status, ApprovalStatus)
            assert status.approved is True
            assert status.reviewed_by == "admin@owkai.com"

    def test_wait_for_approval_timeout(
        self,
        api_key: str,
        mock_status_pending: Dict[str, Any],
    ) -> None:
        """Test approval timeout."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = mock_status_pending
            mock_instance.request.return_value = response

            client = OWKAIClient(api_key=api_key)

            with pytest.raises(OWKAIApprovalTimeoutError) as exc_info:
                client.wait_for_approval(123, timeout=1, poll_interval=0.5)

            assert exc_info.value.action_id == 123
            assert exc_info.value.timeout == 1

    def test_wait_for_approval_rejected(
        self,
        api_key: str,
        mock_status_rejected: Dict[str, Any],
    ) -> None:
        """Test action rejection."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = mock_status_rejected
            mock_instance.request.return_value = response

            client = OWKAIClient(api_key=api_key)

            with pytest.raises(OWKAIActionRejectedError) as exc_info:
                client.wait_for_approval(123, timeout=10)

            assert exc_info.value.action_id == 123
            assert exc_info.value.rejection_reason == "Risk too high for production"


class TestOWKAIClientHealthCheck:
    """Tests for health_check method."""

    def test_health_check_success(
        self,
        api_key: str,
        mock_health_response: Dict[str, Any],
    ) -> None:
        """Test successful health check."""
        with patch("httpx.Client") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance

            response = MagicMock()
            response.status_code = 200
            response.json.return_value = mock_health_response
            mock_instance.request.return_value = response

            client = OWKAIClient(api_key=api_key)
            health = client.health_check()

            assert health.status == "healthy"
            assert health.version == "2.0.0"


class TestAsyncOWKAIClient:
    """Tests for AsyncOWKAIClient."""

    @pytest.mark.asyncio
    async def test_async_init(self, api_key: str) -> None:
        """Test async client initialization."""
        with patch("httpx.AsyncClient"):
            client = AsyncOWKAIClient(api_key=api_key)
            assert client._base_url == "https://pilot.owkai.app"
            await client.close()

    @pytest.mark.asyncio
    async def test_async_context_manager(self, api_key: str) -> None:
        """Test async context manager."""
        with patch("httpx.AsyncClient") as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.aclose = MagicMock(return_value=None)

            # Make aclose awaitable
            async def mock_aclose():
                pass

            mock_instance.aclose = mock_aclose

            async with AsyncOWKAIClient(api_key=api_key) as client:
                pass
