"""
VAL-001: Shared fixtures for Enterprise Validation Framework

Provides common fixtures used across all validation test stages.
"""

import os
import pytest
import httpx
from typing import Optional


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = os.environ.get("ASCEND_API_URL", "https://pilot.owkai.app")
TEST_TIMEOUT = 30.0  # seconds


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for ASCEND API."""
    return BASE_URL


@pytest.fixture(scope="session")
def api_key() -> str:
    """
    Test API key for validation suite.

    Set via environment variable: ASCEND_TEST_API_KEY
    """
    key = os.environ.get("ASCEND_TEST_API_KEY")
    if not key:
        pytest.skip("ASCEND_TEST_API_KEY environment variable not set")
    return key


@pytest.fixture(scope="session")
def admin_api_key() -> Optional[str]:
    """
    Admin API key for compliance tests.

    Set via environment variable: ASCEND_ADMIN_API_KEY
    """
    return os.environ.get("ASCEND_ADMIN_API_KEY")


@pytest.fixture(scope="session")
def readonly_api_key() -> Optional[str]:
    """
    Read-only API key for RBAC tests.

    Set via environment variable: ASCEND_READONLY_API_KEY
    """
    return os.environ.get("ASCEND_READONLY_API_KEY")


@pytest.fixture
def http_client():
    """Async HTTP client with default timeout."""
    return httpx.AsyncClient(timeout=TEST_TIMEOUT)


@pytest.fixture
def headers(api_key: str) -> dict:
    """Standard headers for API requests."""
    return {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
        "User-Agent": "ASCEND-Validation-Suite/1.0"
    }


@pytest.fixture
def admin_headers(admin_api_key: Optional[str]) -> dict:
    """Admin headers for privileged API requests."""
    if not admin_api_key:
        pytest.skip("ASCEND_ADMIN_API_KEY not set")
    return {
        "X-API-Key": admin_api_key,
        "Content-Type": "application/json",
        "User-Agent": "ASCEND-Validation-Suite/1.0"
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def make_action_payload(
    agent_id: str,
    action_type: str,
    tool_name: str,
    description: str,
    environment: str = "test",
    **extra_context
) -> dict:
    """
    Create a standard action payload for testing.

    Args:
        agent_id: Unique agent identifier
        action_type: Type of action (e.g., "database_read", "llm_prompt")
        tool_name: Name of the tool being used
        description: Human-readable description of the action
        environment: Deployment environment (test, staging, production)
        **extra_context: Additional context fields

    Returns:
        dict: Formatted action payload
    """
    return {
        "agent_id": agent_id,
        "action_type": action_type,
        "tool_name": tool_name,
        "description": description,
        "context": {
            "environment": environment,
            "validation_suite": "VAL-001",
            **extra_context
        }
    }


# =============================================================================
# TEST MARKERS
# =============================================================================

def pytest_configure(config):
    """Register custom markers for validation tests."""
    config.addinivalue_line(
        "markers", "stage1: Functional red-teaming tests"
    )
    config.addinivalue_line(
        "markers", "stage2: Unregistered agent tests"
    )
    config.addinivalue_line(
        "markers", "stage3: Performance validation tests"
    )
    config.addinivalue_line(
        "markers", "stage4: Compliance and audit tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than 30 seconds"
    )
    config.addinivalue_line(
        "markers", "critical: Critical security tests that must pass"
    )
