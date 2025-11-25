"""
OW-AI SDK Authentication Tests

Tests for API key authentication module.
"""

import os

import pytest

from owkai.auth import APIKeyAuth, get_api_key_from_env, mask_api_key
from owkai.exceptions import OWKAIAuthenticationError, OWKAIValidationError


class TestAPIKeyAuth:
    """Tests for APIKeyAuth class."""

    def test_init_with_valid_key(self, api_key: str) -> None:
        """Test initialization with valid API key."""
        auth = APIKeyAuth(api_key)
        assert auth.key_prefix == api_key[:16]
        assert auth.role == "admin"

    def test_init_with_env_var(self, env_api_key: str) -> None:
        """Test initialization from environment variable."""
        auth = APIKeyAuth()
        assert auth.key_prefix == env_api_key[:16]

    def test_init_no_key_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing API key raises error."""
        monkeypatch.delenv("OWKAI_API_KEY", raising=False)
        with pytest.raises(OWKAIAuthenticationError) as exc_info:
            APIKeyAuth()
        assert "AUTH_002" in str(exc_info.value)

    def test_init_short_key_raises_error(self) -> None:
        """Test that short API key raises validation error."""
        with pytest.raises(OWKAIValidationError) as exc_info:
            APIKeyAuth("owkai_admin_short")
        assert "too short" in str(exc_info.value)

    def test_init_invalid_prefix_raises_error(self) -> None:
        """Test that invalid prefix raises error."""
        with pytest.raises(OWKAIValidationError) as exc_info:
            APIKeyAuth("invalid_admin_test1234567890abcdef1234567890")
        assert "must start with 'owkai_'" in str(exc_info.value)

    def test_init_invalid_format_raises_error(self) -> None:
        """Test that invalid format raises error."""
        with pytest.raises(OWKAIValidationError) as exc_info:
            APIKeyAuth("owkai_123_test1234567890abcdef1234567890")
        assert "Invalid API key format" in str(exc_info.value)

    def test_get_auth_headers(self, api_key: str) -> None:
        """Test auth headers generation."""
        auth = APIKeyAuth(api_key)
        headers = auth.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {api_key}"

    def test_key_prefix_property(self, api_key: str) -> None:
        """Test key_prefix property."""
        auth = APIKeyAuth(api_key)
        assert len(auth.key_prefix) == 16
        assert auth.key_prefix == api_key[:16]

    def test_role_property_admin(self, api_key: str) -> None:
        """Test role extraction for admin key."""
        auth = APIKeyAuth(api_key)
        assert auth.role == "admin"

    def test_role_property_user(self) -> None:
        """Test role extraction for user key."""
        user_key = "owkai_user_test1234567890abcdef1234567890"
        auth = APIKeyAuth(user_key)
        assert auth.role == "user"

    def test_role_property_service(self) -> None:
        """Test role extraction for service key."""
        service_key = "owkai_service_test1234567890abcdef1234567890"
        auth = APIKeyAuth(service_key)
        assert auth.role == "service"

    def test_repr_safe(self, api_key: str) -> None:
        """Test that repr doesn't expose full key."""
        auth = APIKeyAuth(api_key)
        repr_str = repr(auth)
        assert api_key not in repr_str
        assert "..." in repr_str

    def test_str_safe(self, api_key: str) -> None:
        """Test that str doesn't expose full key."""
        auth = APIKeyAuth(api_key)
        str_str = str(auth)
        assert api_key not in str_str
        assert "..." in str_str

    def test_skip_validation(self) -> None:
        """Test skipping validation."""
        # This would normally fail validation
        auth = APIKeyAuth("any_string_works_here", validate=False)
        assert auth.key_prefix == "any_string_works"


class TestGetAPIKeyFromEnv:
    """Tests for get_api_key_from_env function."""

    def test_returns_key_when_set(self, env_api_key: str) -> None:
        """Test returns key from environment."""
        result = get_api_key_from_env()
        assert result == env_api_key

    def test_returns_none_when_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test returns None when env var not set."""
        monkeypatch.delenv("OWKAI_API_KEY", raising=False)
        result = get_api_key_from_env()
        assert result is None

    def test_custom_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test custom environment variable name."""
        custom_key = "owkai_custom_test1234567890abcdef1234567890"
        monkeypatch.setenv("MY_CUSTOM_KEY", custom_key)
        result = get_api_key_from_env("MY_CUSTOM_KEY")
        assert result == custom_key


class TestMaskAPIKey:
    """Tests for mask_api_key function."""

    def test_masks_full_key(self, api_key: str) -> None:
        """Test masking a full API key."""
        masked = mask_api_key(api_key)
        assert api_key not in masked
        assert "****" in masked
        assert masked.startswith(api_key[:16])

    def test_masks_short_key(self) -> None:
        """Test masking a short key."""
        masked = mask_api_key("short")
        assert masked == "****"

    def test_masks_exact_prefix_length(self) -> None:
        """Test masking key exactly prefix length."""
        masked = mask_api_key("1234567890123456")
        assert masked == "****"
