"""
OW-AI SDK Test Configuration

Shared fixtures and utilities for the test suite.
"""

import os
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

# Test API key (valid format but fake)
TEST_API_KEY = "owkai_admin_test1234567890abcdef1234567890"
TEST_BASE_URL = "https://test.owkai.app"


@pytest.fixture
def api_key() -> str:
    """Provide test API key."""
    return TEST_API_KEY


@pytest.fixture
def base_url() -> str:
    """Provide test base URL."""
    return TEST_BASE_URL


@pytest.fixture
def env_api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """Set API key via environment variable."""
    monkeypatch.setenv("OWKAI_API_KEY", TEST_API_KEY)
    return TEST_API_KEY


@pytest.fixture
def mock_response_success() -> Dict[str, Any]:
    """Standard successful action response."""
    return {
        "id": 123,
        "agent_id": "test-agent",
        "action_type": "database_write",
        "status": "pending_approval",
        "risk_score": 75.0,
        "risk_level": "high",
        "requires_approval": True,
        "alert_triggered": False,
        "message": "Action submitted successfully",
    }


@pytest.fixture
def mock_status_approved() -> Dict[str, Any]:
    """Approved action status response."""
    return {
        "action_id": 123,
        "status": "approved",
        "approved": True,
        "requires_approval": True,
        "risk_score": 75.0,
        "risk_level": "high",
        "reviewed_by": "admin@owkai.com",
        "reviewed_at": "2025-01-15T10:30:00Z",
        "comments": "Approved for execution",
        "polling_interval_seconds": 30,
    }


@pytest.fixture
def mock_status_pending() -> Dict[str, Any]:
    """Pending action status response."""
    return {
        "action_id": 123,
        "status": "pending_approval",
        "approved": False,
        "requires_approval": True,
        "risk_score": 75.0,
        "risk_level": "high",
        "reviewed_by": None,
        "reviewed_at": None,
        "comments": None,
        "polling_interval_seconds": 30,
    }


@pytest.fixture
def mock_status_rejected() -> Dict[str, Any]:
    """Rejected action status response."""
    return {
        "action_id": 123,
        "status": "rejected",
        "approved": False,
        "requires_approval": True,
        "risk_score": 75.0,
        "risk_level": "high",
        "reviewed_by": "admin@owkai.com",
        "reviewed_at": "2025-01-15T10:30:00Z",
        "comments": "Risk too high for production",
        "polling_interval_seconds": 30,
    }


@pytest.fixture
def mock_health_response() -> Dict[str, Any]:
    """Health check response."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": "2025-01-15T10:30:00Z",
        "services": {
            "database": "operational",
            "cache": "operational",
            "auth": "operational",
        },
    }


class MockResponse:
    """Mock httpx Response."""

    def __init__(
        self,
        status_code: int = 200,
        json_data: Dict[str, Any] = None,
        text: str = "",
        headers: Dict[str, str] = None,
    ):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.headers = headers or {}

    def json(self) -> Dict[str, Any]:
        return self._json_data


@pytest.fixture
def mock_httpx_client():
    """Create mock httpx client."""
    with patch("httpx.Client") as mock:
        yield mock


@pytest.fixture
def mock_httpx_async_client():
    """Create mock async httpx client."""
    with patch("httpx.AsyncClient") as mock:
        yield mock
