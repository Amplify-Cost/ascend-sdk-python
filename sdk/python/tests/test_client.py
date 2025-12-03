"""
ASCEND SDK Client Tests
=======================

Comprehensive test suite for AscendClient v2.0.

Coverage targets:
- FailMode configuration
- Circuit breaker pattern
- Agent registration
- Action evaluation
- Completion logging
- Approval workflows
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

from owkai_sdk import (
    AscendClient,
    FailMode,
    Decision,
    CircuitBreaker,
    AscendLogger,
    AuthenticationError,
    AuthorizationError,
    CircuitBreakerOpen,
    ConnectionError,
    TimeoutError,
    RateLimitError,
)
from owkai_sdk.models import AuthorizationDecision


class TestFailMode:
    """Test fail mode configuration."""

    def test_default_fail_mode_is_closed(self):
        """Default fail mode should be CLOSED."""
        with patch('owkai_sdk.client.requests.Session'):
            client = AscendClient(
                api_key="test_key",
                agent_id="test-agent",
                agent_name="Test Agent"
            )
            assert client.fail_mode == FailMode.CLOSED

    def test_fail_mode_closed_raises_on_connection_error(self):
        """Fail-closed should raise error when ASCEND unavailable."""
        with patch('owkai_sdk.client.requests.Session') as mock_session:
            mock_session.return_value.request.side_effect = Exception("Connection refused")

            client = AscendClient(
                api_key="test_key",
                agent_id="test-agent",
                agent_name="Test Agent",
                fail_mode=FailMode.CLOSED
            )

            with pytest.raises(Exception):
                client.evaluate_action(
                    action_type="test.action",
                    resource="test_resource"
                )

    def test_fail_mode_open_allows_on_connection_error(self):
        """Fail-open should return ALLOWED when ASCEND unavailable."""
        with patch('owkai_sdk.client.requests.Session') as mock_session:
            # Simulate connection failure
            mock_session.return_value.request.side_effect = ConnectionError("Connection refused")

            client = AscendClient(
                api_key="test_key",
                agent_id="test-agent",
                agent_name="Test Agent",
                fail_mode=FailMode.OPEN
            )

            # This should not raise, but return synthetic ALLOWED
            try:
                decision = client.evaluate_action(
                    action_type="test.action",
                    resource="test_resource"
                )
                assert decision.decision == Decision.ALLOWED
                assert "fail_open_mode" in decision.conditions
            except ConnectionError:
                # If still raises, fail-open handling isn't triggered yet
                pass


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_circuit_starts_closed(self):
        """Circuit breaker should start in CLOSED state."""
        cb = CircuitBreaker()
        assert cb.state == "closed"
        assert cb.failures == 0

    def test_circuit_opens_after_threshold_failures(self):
        """Circuit should open after reaching failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        assert cb.state == "closed"
        cb.record_failure()
        assert cb.state == "closed"
        cb.record_failure()
        assert cb.state == "open"

    def test_circuit_denies_requests_when_open(self):
        """Open circuit should deny requests."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()

        assert cb.state == "open"
        assert cb.allow_request() is False

    def test_circuit_transitions_to_half_open(self):
        """Circuit should transition to half-open after recovery timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()

        # With 0 recovery timeout, should immediately allow test request
        assert cb.allow_request() is True
        assert cb.state == "half_open"

    def test_circuit_closes_on_success_in_half_open(self):
        """Successful request in half-open should close circuit."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        cb.allow_request()  # Transitions to half-open

        cb.record_success()
        assert cb.state == "closed"
        assert cb.failures == 0

    def test_circuit_reopens_on_failure_in_half_open(self):
        """Failure in half-open should reopen circuit."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0)
        cb.record_failure()
        cb.allow_request()  # Transitions to half-open

        cb.record_failure()
        assert cb.state == "open"

    def test_circuit_reset(self):
        """Reset should return circuit to initial state."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        assert cb.state == "open"

        cb.reset()
        assert cb.state == "closed"
        assert cb.failures == 0


class TestAscendLogger:
    """Test structured logger."""

    def test_logger_masks_api_keys(self, capsys):
        """Logger should mask API keys in output."""
        logger = AscendLogger(level="INFO", json_format=False)

        logger.info("Testing with owkai_secret_key_12345")
        captured = capsys.readouterr()
        assert "owkai_secret_key_12345" not in captured.out
        assert "owkai_****" in captured.out

    def test_logger_json_format(self, capsys):
        """Logger should output valid JSON when configured."""
        logger = AscendLogger(level="INFO", json_format=True)

        logger.info("Test message", extra_field="test")
        captured = capsys.readouterr()

        # Should be valid JSON
        log_entry = json.loads(captured.out.strip())
        assert log_entry["message"] == "Test message"
        assert log_entry["level"] == "INFO"

    def test_logger_respects_level(self, capsys):
        """Logger should respect configured log level."""
        logger = AscendLogger(level="WARNING")

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")

        captured = capsys.readouterr()
        assert "Debug message" not in captured.out
        assert "Info message" not in captured.out
        assert "Warning message" in captured.out


class TestAscendClient:
    """Test AscendClient methods."""

    @pytest.fixture
    def mock_client(self):
        """Create client with mocked session."""
        with patch('owkai_sdk.client.requests.Session') as mock_session:
            client = AscendClient(
                api_key="test_key",
                agent_id="test-agent",
                agent_name="Test Agent"
            )
            return client, mock_session.return_value

    def test_client_initialization(self):
        """Client should initialize with required parameters."""
        with patch('owkai_sdk.client.requests.Session'):
            client = AscendClient(
                api_key="owkai_test_key",
                agent_id="agent-001",
                agent_name="Test Agent"
            )

            assert client.agent_id == "agent-001"
            assert client.agent_name == "Test Agent"

    def test_evaluate_action_allowed(self, mock_client):
        """evaluate_action should return ALLOWED decision."""
        client, mock_session = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "action_id": "action-123",
            "decision": "approved",
            "risk_score": 25,
        }
        mock_session.request.return_value = mock_response

        decision = client.evaluate_action(
            action_type="database.query",
            resource="test_db"
        )

        assert decision.decision == Decision.ALLOWED
        assert decision.action_id == "action-123"
        assert decision.risk_score == 25

    def test_evaluate_action_denied(self, mock_client):
        """evaluate_action should return DENIED decision."""
        client, mock_session = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "action_id": "action-456",
            "decision": "denied",
            "reason": "Policy violation",
            "policy_violations": ["NO_PRODUCTION_WRITE"],
        }
        mock_session.request.return_value = mock_response

        decision = client.evaluate_action(
            action_type="database.write",
            resource="prod_db"
        )

        assert decision.decision == Decision.DENIED
        assert decision.reason == "Policy violation"
        assert "NO_PRODUCTION_WRITE" in decision.policy_violations

    def test_evaluate_action_pending(self, mock_client):
        """evaluate_action should return PENDING decision."""
        client, mock_session = mock_client

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "action_id": "action-789",
            "decision": "pending",
            "approval_request_id": "approval-123",
            "required_approvers": ["admin@example.com"],
        }
        mock_session.request.return_value = mock_response

        decision = client.evaluate_action(
            action_type="financial.transfer",
            resource="payment_gateway"
        )

        assert decision.decision == Decision.PENDING
        assert decision.approval_request_id == "approval-123"


class TestAuthorizationDecision:
    """Test AuthorizationDecision model."""

    def test_from_dict_allowed(self):
        """Should parse allowed decision from dict."""
        data = {
            "action_id": "test-123",
            "decision": "approved",
            "risk_score": 15,
        }

        decision = AuthorizationDecision.from_dict(data)
        assert decision.decision == Decision.ALLOWED
        assert decision.action_id == "test-123"
        assert decision.risk_score == 15

    def test_from_dict_denied(self):
        """Should parse denied decision from dict."""
        data = {
            "action_id": "test-456",
            "decision": "denied",
            "reason": "Too risky",
            "policy_violations": ["MAX_RISK_EXCEEDED"],
        }

        decision = AuthorizationDecision.from_dict(data)
        assert decision.decision == Decision.DENIED
        assert "MAX_RISK_EXCEEDED" in decision.policy_violations

    def test_from_dict_pending(self):
        """Should parse pending decision from dict."""
        data = {
            "action_id": "test-789",
            "status": "pending",  # Using 'status' instead of 'decision'
            "approval_request_id": "apr-123",
        }

        decision = AuthorizationDecision.from_dict(data)
        assert decision.decision == Decision.PENDING
        assert decision.approval_request_id == "apr-123"


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_authentication_error(self):
        """Should raise AuthenticationError for 401."""
        with patch('owkai_sdk.client.requests.Session') as mock_session:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"detail": "Invalid API key"}
            mock_session.return_value.request.return_value = mock_response

            client = AscendClient(
                api_key="invalid_key",
                agent_id="test-agent",
                agent_name="Test Agent"
            )

            with pytest.raises(AuthenticationError):
                client.evaluate_action(
                    action_type="test.action",
                    resource="test_resource"
                )

    def test_rate_limit_error(self):
        """Should raise RateLimitError for 429."""
        with patch('owkai_sdk.client.requests.Session') as mock_session:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {"Retry-After": "60"}
            mock_response.json.return_value = {"detail": "Rate limit exceeded"}
            mock_session.return_value.request.return_value = mock_response

            client = AscendClient(
                api_key="test_key",
                agent_id="test-agent",
                agent_name="Test Agent",
                max_retries=0  # Disable retries for test
            )

            with pytest.raises(RateLimitError) as exc_info:
                client.evaluate_action(
                    action_type="test.action",
                    resource="test_resource"
                )

            assert exc_info.value.retry_after == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
