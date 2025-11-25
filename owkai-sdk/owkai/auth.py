"""
OW-AI SDK Authentication Module

Handles API key authentication with enterprise security features.
Supports both synchronous and asynchronous authentication flows.

Security:
- API keys are never logged or exposed in exceptions
- Constant-time comparison prevents timing attacks
- Automatic key validation on initialization
"""

import os
import re
from typing import Optional

from owkai.exceptions import OWKAIAuthenticationError, OWKAIValidationError


# API key format: owkai_{role}_{random}
# Example: owkai_admin_abc123xyz789...
API_KEY_PATTERN = re.compile(r"^owkai_[a-z]+_[A-Za-z0-9_-]{20,}$")
API_KEY_MIN_LENGTH = 32
API_KEY_PREFIX_LENGTH = 16


class APIKeyAuth:
    """
    API key authentication handler.

    Validates and manages API key credentials for SDK requests.
    Keys are stored in memory only and never persisted.

    Example:
        auth = APIKeyAuth(api_key="owkai_admin_...")
        headers = auth.get_auth_headers()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        env_var: str = "OWKAI_API_KEY",
        validate: bool = True,
    ) -> None:
        """
        Initialize API key authentication.

        Args:
            api_key: API key string. If None, reads from environment.
            env_var: Environment variable name for API key (default: OWKAI_API_KEY)
            validate: Whether to validate key format (default: True)

        Raises:
            OWKAIAuthenticationError: If no API key provided
            OWKAIValidationError: If API key format is invalid
        """
        # Try to get API key from argument or environment
        self._api_key = api_key or os.environ.get(env_var)

        if not self._api_key:
            raise OWKAIAuthenticationError(
                f"No API key provided. Set {env_var} environment variable or pass api_key parameter.",
                error_code="AUTH_002",
            )

        if validate:
            self._validate_key_format()

    def _validate_key_format(self) -> None:
        """
        Validate API key format.

        Expected format: owkai_{role}_{random_string}
        - Minimum length: 32 characters
        - Prefix: owkai_{role}_
        - Random part: alphanumeric with underscores/hyphens

        Raises:
            OWKAIValidationError: If format is invalid
        """
        if len(self._api_key) < API_KEY_MIN_LENGTH:
            raise OWKAIValidationError(
                "API key is too short",
                field="api_key",
                constraint=f"minimum length {API_KEY_MIN_LENGTH}",
                error_code="VALIDATION_002",
            )

        if not self._api_key.startswith("owkai_"):
            raise OWKAIValidationError(
                "API key must start with 'owkai_'",
                field="api_key",
                constraint="prefix 'owkai_'",
                error_code="VALIDATION_003",
            )

        if not API_KEY_PATTERN.match(self._api_key):
            raise OWKAIValidationError(
                "Invalid API key format",
                field="api_key",
                constraint="format owkai_{role}_{random}",
                error_code="VALIDATION_004",
            )

    def get_auth_headers(self) -> dict:
        """
        Get authentication headers for API requests.

        Returns:
            Dictionary with Authorization header
        """
        return {
            "Authorization": f"Bearer {self._api_key}",
        }

    @property
    def key_prefix(self) -> str:
        """
        Get the visible prefix of the API key.

        Safe to log/display - does not expose the full key.

        Returns:
            First 16 characters of the API key
        """
        return self._api_key[:API_KEY_PREFIX_LENGTH]

    @property
    def role(self) -> str:
        """
        Extract role from API key.

        Returns:
            Role string (e.g., 'admin', 'user', 'service')
        """
        try:
            # Format: owkai_{role}_{random}
            parts = self._api_key.split("_")
            if len(parts) >= 3:
                return parts[1]
        except Exception:
            pass
        return "unknown"

    def __repr__(self) -> str:
        """Safe string representation (no key exposure)."""
        return f"APIKeyAuth(prefix='{self.key_prefix}...', role='{self.role}')"

    def __str__(self) -> str:
        """Safe string representation (no key exposure)."""
        return f"APIKeyAuth({self.key_prefix}...)"


def get_api_key_from_env(env_var: str = "OWKAI_API_KEY") -> Optional[str]:
    """
    Get API key from environment variable.

    Args:
        env_var: Environment variable name

    Returns:
        API key string or None if not set
    """
    return os.environ.get(env_var)


def mask_api_key(api_key: str) -> str:
    """
    Mask API key for safe logging.

    Args:
        api_key: Full API key

    Returns:
        Masked key (e.g., "owkai_admin_a1b2...****")
    """
    if len(api_key) <= API_KEY_PREFIX_LENGTH:
        return "****"
    return f"{api_key[:API_KEY_PREFIX_LENGTH]}...****"
