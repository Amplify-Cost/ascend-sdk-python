"""
Tests for AscendClient
======================

Basic tests for the Ascend SDK client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ascend import (
    AscendClient,
    AgentAction,
    ActionResult,
    ValidationError,
    AuthenticationError,
)


def test_client_initialization():
    """Test client initialization."""
    with patch.dict("os.environ", {"ASCEND_API_KEY": "ascend_test_abc123"}):
        client = AscendClient()
        assert client.api_key == "ascend_test_abc123"
        assert client.base_url == "https://pilot.owkai.app"
        assert client.timeout == 30


def test_client_missing_api_key():
    """Test client raises error when API key is missing."""
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValidationError) as exc_info:
            AscendClient()
        assert "API key is required" in str(exc_info.value)


def test_client_custom_base_url():
    """Test client with custom base URL."""
    client = AscendClient(
        api_key="ascend_test_abc123",
        base_url="https://staging.owkai.app"
    )
    assert client.base_url == "https://staging.owkai.app"


def test_api_key_masking():
    """Test API key masking in logs."""
    client = AscendClient(api_key="ascend_test_abc123xyz789")
    masked = client._mask_api_key("ascend_test_abc123xyz789")
    assert masked == "asce...x789"


def test_agent_action_validation():
    """Test AgentAction validation."""
    from ascend.utils.validation import validate_action

    # Valid action
    action = AgentAction(
        agent_id="bot-001",
        agent_name="Test Bot",
        action_type="data_access",
        resource="database"
    )
    validate_action(action)  # Should not raise

    # Invalid action - missing agent_id
    with pytest.raises(ValidationError):
        invalid_action = AgentAction(
            agent_id="",
            agent_name="Test Bot",
            action_type="data_access",
            resource="database"
        )
        validate_action(invalid_action)


def test_action_result_parsing():
    """Test ActionResult parsing from API response."""
    api_response = {
        "id": 123,
        "status": "approved",
        "risk_score": 45.5,
        "risk_level": "medium",
        "summary": "Action approved by policy",
        "created_at": "2025-12-04T10:00:00Z"
    }

    result = ActionResult.from_dict(api_response)

    assert result.action_id == "123"
    assert result.status == "approved"
    assert result.is_approved() is True
    assert result.is_denied() is False
    assert result.risk_score == 45.5
    assert result.risk_level == "medium"


def test_submit_action_mock():
    """Test submit_action with mocked API."""
    with patch.dict("os.environ", {"ASCEND_API_KEY": "ascend_test_abc123"}):
        client = AscendClient()

        # Mock the _request method
        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = {
                "id": 456,
                "status": "approved",
                "risk_level": "low"
            }

            action = AgentAction(
                agent_id="bot-001",
                agent_name="Test Bot",
                action_type="query",
                resource="database"
            )

            result = client.submit_action(action)

            assert result.action_id == "456"
            assert result.status == "approved"
            assert mock_request.called


def test_correlation_id_generation():
    """Test correlation ID generation."""
    with patch.dict("os.environ", {"ASCEND_API_KEY": "ascend_test_abc123"}):
        client = AscendClient()
        corr_id = client._generate_correlation_id()

        assert corr_id.startswith("ascend-")
        assert len(corr_id) == 23  # ascend- (7) + 16 hex chars


def test_context_manager():
    """Test client as context manager."""
    with patch.dict("os.environ", {"ASCEND_API_KEY": "ascend_test_abc123"}):
        with AscendClient() as client:
            assert client.api_key == "ascend_test_abc123"
        # Should close session automatically


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
