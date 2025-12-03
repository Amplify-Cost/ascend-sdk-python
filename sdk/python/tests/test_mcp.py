"""
ASCEND MCP Governance Tests
===========================

Test suite for MCP governance decorator.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from owkai_sdk import AscendClient, Decision
from owkai_sdk.mcp import (
    mcp_governance,
    require_governance,
    high_risk_action,
    MCPGovernanceConfig,
    MCPGovernanceMiddleware,
)
from owkai_sdk.exceptions import AuthorizationError, TimeoutError
from owkai_sdk.models import AuthorizationDecision


class TestMCPGovernance:
    """Test MCP governance decorator."""

    @pytest.fixture
    def mock_client(self):
        """Create mock AscendClient."""
        client = Mock(spec=AscendClient)
        client.evaluate_action = Mock()
        client.log_action_completed = Mock()
        client.log_action_failed = Mock()
        return client

    @pytest.fixture
    def allowed_decision(self):
        """Create allowed decision."""
        return AuthorizationDecision(
            action_id="action-123",
            decision=Decision.ALLOWED,
            risk_score=25,
            reason="Allowed by policy",
            policy_violations=[],
            conditions=[],
            approval_request_id=None,
            required_approvers=[],
            expires_at=None,
            metadata={}
        )

    @pytest.fixture
    def denied_decision(self):
        """Create denied decision."""
        return AuthorizationDecision(
            action_id="action-456",
            decision=Decision.DENIED,
            risk_score=85,
            reason="Policy violation",
            policy_violations=["NO_PRODUCTION_WRITE"],
            conditions=[],
            approval_request_id=None,
            required_approvers=[],
            expires_at=None,
            metadata={}
        )

    @pytest.fixture
    def pending_decision(self):
        """Create pending decision."""
        return AuthorizationDecision(
            action_id="action-789",
            decision=Decision.PENDING,
            risk_score=60,
            reason="Requires approval",
            policy_violations=[],
            conditions=[],
            approval_request_id="approval-123",
            required_approvers=["admin@example.com"],
            expires_at=None,
            metadata={}
        )

    def test_decorator_allows_execution_when_allowed(self, mock_client, allowed_decision):
        """Should execute function when action is allowed."""
        mock_client.evaluate_action.return_value = allowed_decision

        @mcp_governance(mock_client, action_type="test.action", resource="test")
        def test_function(x: int, y: int) -> int:
            return x + y

        result = test_function(2, 3)

        assert result == 5
        mock_client.evaluate_action.assert_called_once()
        mock_client.log_action_completed.assert_called_once()

    def test_decorator_raises_when_denied(self, mock_client, denied_decision):
        """Should raise AuthorizationError when action is denied."""
        mock_client.evaluate_action.return_value = denied_decision

        @mcp_governance(mock_client, action_type="test.action", resource="test")
        def test_function() -> str:
            return "should not execute"

        with pytest.raises(AuthorizationError) as exc_info:
            test_function()

        assert "Policy violation" in str(exc_info.value)
        mock_client.log_action_completed.assert_not_called()

    def test_decorator_logs_failure_on_execution_error(self, mock_client, allowed_decision):
        """Should log failure when function raises exception."""
        mock_client.evaluate_action.return_value = allowed_decision

        @mcp_governance(mock_client, action_type="test.action", resource="test")
        def test_function():
            raise ValueError("Something went wrong")

        with pytest.raises(ValueError):
            test_function()

        mock_client.log_action_failed.assert_called_once()

    def test_require_governance_is_alias(self, mock_client, allowed_decision):
        """require_governance should work as alias for mcp_governance."""
        mock_client.evaluate_action.return_value = allowed_decision

        @require_governance(mock_client, "test.action", "test")
        def test_function() -> str:
            return "success"

        result = test_function()
        assert result == "success"

    def test_high_risk_action_sets_flags(self, mock_client, allowed_decision):
        """high_risk_action should set risk_level and require_human_approval in context."""
        mock_client.evaluate_action.return_value = allowed_decision

        @high_risk_action(mock_client, "dangerous.action", "sensitive_resource")
        def dangerous_function() -> str:
            return "done"

        dangerous_function()

        call_kwargs = mock_client.evaluate_action.call_args[1]
        # CRIT-001 FIX: risk_level and require_human_approval are now in context dict
        context = call_kwargs.get("context", {})
        assert context.get("risk_level") == "high"
        assert context.get("require_human_approval") is True


class TestMCPGovernanceConfig:
    """Test MCPGovernanceConfig options."""

    def test_default_config_values(self):
        """Should have sensible defaults."""
        config = MCPGovernanceConfig()

        assert config.wait_for_approval is True
        assert config.approval_timeout_seconds == 300
        assert config.approval_poll_interval_seconds == 5
        assert config.raise_on_denial is True
        assert config.log_all_decisions is True

    def test_custom_config_values(self):
        """Should accept custom values."""
        config = MCPGovernanceConfig(
            wait_for_approval=False,
            approval_timeout_seconds=600,
            raise_on_denial=False,
        )

        assert config.wait_for_approval is False
        assert config.approval_timeout_seconds == 600
        assert config.raise_on_denial is False

    def test_denial_callback(self):
        """Should call on_denied callback when action denied."""
        callback = Mock()
        config = MCPGovernanceConfig(on_denied=callback)

        client = Mock(spec=AscendClient)
        client.evaluate_action.return_value = AuthorizationDecision(
            action_id="test",
            decision=Decision.DENIED,
            reason="Denied",
            policy_violations=[],
            conditions=[],
            required_approvers=[],
            metadata={}
        )

        @mcp_governance(client, "test.action", "test", config=config)
        def test_function():
            return "should not execute"

        try:
            test_function()
        except AuthorizationError:
            pass

        callback.assert_called_once()


class TestMCPGovernanceMiddleware:
    """Test MCPGovernanceMiddleware."""

    def test_middleware_wraps_functions(self):
        """Should wrap functions and track them."""
        client = Mock(spec=AscendClient)
        client.evaluate_action.return_value = AuthorizationDecision(
            action_id="test",
            decision=Decision.ALLOWED,
            policy_violations=[],
            conditions=[],
            required_approvers=[],
            metadata={}
        )

        middleware = MCPGovernanceMiddleware(client)

        def query_db(sql: str) -> str:
            return f"executed: {sql}"

        def write_file(path: str) -> str:
            return f"wrote: {path}"

        wrapped_query = middleware.govern("database.query", "db")(query_db)
        wrapped_write = middleware.govern("file.write", "/var")(write_file)

        assert "query_db" in middleware.governed_tools or "anonymous" in middleware.governed_tools
        assert len(middleware.governed_tools) == 2

    def test_middleware_default_config(self):
        """Should apply default config to all wrapped functions."""
        client = Mock(spec=AscendClient)
        default_config = MCPGovernanceConfig(
            wait_for_approval=False,
            log_all_decisions=False,
        )

        middleware = MCPGovernanceMiddleware(client, default_config)

        # The middleware stores the default config
        assert middleware.default_config.wait_for_approval is False


class TestAsyncSupport:
    """Test async function support."""

    @pytest.fixture
    def mock_async_client(self):
        """Create mock client for async tests."""
        client = Mock(spec=AscendClient)
        client.evaluate_action = Mock(return_value=AuthorizationDecision(
            action_id="async-123",
            decision=Decision.ALLOWED,
            policy_violations=[],
            conditions=[],
            required_approvers=[],
            metadata={}
        ))
        client.log_action_completed = Mock()
        return client

    @pytest.mark.asyncio
    async def test_async_function_support(self, mock_async_client):
        """Should support async functions."""
        @mcp_governance(mock_async_client, "async.action", "resource")
        async def async_function(value: int) -> int:
            await asyncio.sleep(0.01)  # Simulate async work
            return value * 2

        result = await async_function(5)
        assert result == 10
        mock_async_client.evaluate_action.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
