"""
BEHAV-001: Rate Limiter Unit Tests

Tests for per-agent, per-tenant rate limiting service.

Author: Enterprise Security Team
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, UTC

# Import models and service
from models_rate_limits import (
    OrgRateLimitConfig,
    AgentRateLimitOverride,
    RateLimitEvent,
    RateLimitResult
)
from services.agent_rate_limiter import (
    AgentRateLimiter,
    RATE_LIMIT_ENABLED,
    DEFAULT_AGENT_LIMIT_PER_MINUTE,
    DEFAULT_TENANT_LIMIT_PER_MINUTE
)


class TestRateLimitResult:
    """Tests for RateLimitResult dataclass."""

    def test_allowed_result(self):
        """Test allowed result has correct properties."""
        result = RateLimitResult(
            allowed=True,
            current_agent_count=50,
            agent_limit=100,
            current_tenant_count=200,
            tenant_limit=1000
        )

        assert result.allowed is True
        assert result.reason is None
        assert result.retry_after is None

    def test_denied_result(self):
        """Test denied result has correct properties."""
        result = RateLimitResult(
            allowed=False,
            reason="Agent rate limit exceeded",
            retry_after=30,
            limit_type="agent_minute",
            current_agent_count=100,
            agent_limit=100
        )

        assert result.allowed is False
        assert result.reason == "Agent rate limit exceeded"
        assert result.retry_after == 30
        assert result.limit_type == "agent_minute"

    def test_response_headers(self):
        """Test response headers generation."""
        result = RateLimitResult(
            allowed=True,
            current_agent_count=87,
            agent_limit=100,
            current_tenant_count=456,
            tenant_limit=1000
        )

        headers = result.to_response_headers()

        assert headers["X-RateLimit-Limit-Agent"] == "100"
        assert headers["X-RateLimit-Remaining-Agent"] == "13"  # 100 - 87
        assert headers["X-RateLimit-Limit-Tenant"] == "1000"
        assert headers["X-RateLimit-Remaining-Tenant"] == "544"  # 1000 - 456

    def test_error_response(self):
        """Test error response body generation."""
        result = RateLimitResult(
            allowed=False,
            reason="Agent rate limit exceeded (100/min)",
            retry_after=45,
            limit_type="agent_minute",
            current_agent_count=100,
            current_tenant_count=456
        )

        error = result.to_error_response()

        assert error["error"] == "rate_limit_exceeded"
        assert error["message"] == "Agent rate limit exceeded (100/min)"
        assert error["retry_after"] == 45
        assert error["limit_type"] == "agent_minute"
        assert error["current_usage"]["agent_minute"] == 100


class TestOrgRateLimitConfig:
    """Tests for OrgRateLimitConfig model."""

    def test_to_dict(self):
        """Test to_dict serialization."""
        config = OrgRateLimitConfig(
            organization_id=1,
            actions_per_minute=1000,
            agent_actions_per_minute=100,
            enabled=True
        )
        config.updated_at = datetime.now(UTC)

        result = config.to_dict()

        assert result["organization_id"] == 1
        assert result["tenant_limits"]["actions_per_minute"] == 1000
        assert result["agent_defaults"]["actions_per_minute"] == 100
        assert result["enabled"] is True


class TestAgentRateLimitOverride:
    """Tests for AgentRateLimitOverride model."""

    def test_get_effective_limit_with_explicit_override(self):
        """Test explicit limit override takes precedence."""
        override = AgentRateLimitOverride(
            organization_id=1,
            agent_id="test-agent",
            actions_per_minute=500,  # Explicit override
            priority_tier="standard"
        )

        effective = override.get_effective_limit(default_limit=100)
        assert effective == 500  # Uses explicit override

    def test_get_effective_limit_with_tier_multiplier(self):
        """Test priority tier multiplier is applied."""
        override = AgentRateLimitOverride(
            organization_id=1,
            agent_id="critical-agent",
            actions_per_minute=None,  # No explicit override
            priority_tier="critical"  # 5x multiplier
        )

        effective = override.get_effective_limit(default_limit=100)
        assert effective == 500  # 100 * 5.0

    def test_get_effective_limit_elevated_tier(self):
        """Test elevated tier multiplier (2x)."""
        override = AgentRateLimitOverride(
            organization_id=1,
            agent_id="elevated-agent",
            actions_per_minute=None,
            priority_tier="elevated"  # 2x multiplier
        )

        effective = override.get_effective_limit(default_limit=100)
        assert effective == 200  # 100 * 2.0


class TestAgentRateLimiterFailClosed:
    """Tests for fail-closed behavior."""

    @pytest.mark.asyncio
    async def test_fail_closed_on_redis_unavailable(self):
        """Test that rate limiter denies when Redis is unavailable (fail-closed)."""
        mock_db = Mock()

        # Create config that's enabled
        mock_config = OrgRateLimitConfig(
            organization_id=1,
            enabled=True,
            actions_per_minute=1000,
            agent_actions_per_minute=100
        )

        with patch.object(AgentRateLimiter, '_get_org_config', new_callable=AsyncMock) as mock_get_config:
            mock_get_config.return_value = mock_config

            limiter = AgentRateLimiter(mock_db, redis_client=None)
            limiter._redis = None  # Force Redis unavailable

            result = await limiter.check_and_increment(
                org_id=1,
                agent_id="test-agent"
            )

            # Should be denied due to Redis unavailability
            assert result.allowed is False
            assert "unavailable" in result.reason.lower()


class TestRateLimitDisabled:
    """Tests for rate limiting disabled scenarios."""

    @pytest.mark.asyncio
    async def test_allows_when_disabled_globally(self):
        """Test that requests are allowed when rate limiting is disabled."""
        with patch('services.agent_rate_limiter.RATE_LIMIT_ENABLED', False):
            mock_db = Mock()
            limiter = AgentRateLimiter(mock_db)

            result = await limiter.check_and_increment(
                org_id=1,
                agent_id="test-agent"
            )

            assert result.allowed is True
            assert "disabled" in result.reason.lower()


# Run with: pytest tests/test_behav001_rate_limiter.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
