"""
ASCEND Lambda Authorizer - Configuration Management
====================================================

GW-005: Centralized configuration with environment variable support.

Environment Variables:
    ASCEND_API_URL: ASCEND platform API URL (required)
    ASCEND_API_KEY: API key for authentication (required)
    ASCEND_ENVIRONMENT: Environment context (default: production)
    ASCEND_CACHE_TTL: Cache TTL in seconds (default: 60)
    ASCEND_TIMEOUT: API timeout in seconds (default: 4)
    LOG_LEVEL: Logging level (default: INFO)

Security:
    - API key should be stored in AWS Secrets Manager or SSM Parameter Store
    - Never log sensitive values
    - FAIL SECURE on missing required config

Compliance: SOC 2 CC6.1, NIST SC-12
Author: ASCEND Platform Engineering
Version: 1.0.0
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, List

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


@dataclass
class AscendConfig:
    """
    ASCEND Lambda Authorizer configuration.

    All sensitive values are loaded from environment variables.
    Missing required values cause immediate failure (FAIL SECURE).
    """
    # Required configuration
    api_url: str = field(default="")
    api_key: str = field(default="")

    # Optional configuration with defaults
    environment: str = field(default="production")
    cache_ttl_seconds: int = field(default=60)
    timeout_seconds: int = field(default=4)  # Lambda authorizer limit is 5s
    log_level: str = field(default="INFO")

    # Feature flags
    cache_enabled: bool = field(default=True)
    metrics_enabled: bool = field(default=True)

    # Request defaults
    default_tool_name: str = field(default="api_gateway")
    default_data_sensitivity: str = field(default="none")

    # Cache configuration
    cache_approved_only: bool = field(default=True)  # Only cache approved decisions

    # Rate limiting (local)
    max_concurrent_requests: int = field(default=100)

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate required configuration values.

        Raises:
            ConfigurationError: If required values are missing
        """
        errors = []

        if not self.api_url:
            errors.append("ASCEND_API_URL is required")

        if not self.api_key:
            errors.append("ASCEND_API_KEY is required")

        if self.timeout_seconds > 5:
            logger.warning(
                f"Timeout {self.timeout_seconds}s exceeds Lambda authorizer limit (5s). "
                "Reducing to 4s to allow for processing overhead."
            )
            self.timeout_seconds = 4

        if self.cache_ttl_seconds < 0:
            errors.append("ASCEND_CACHE_TTL must be non-negative")

        if errors:
            error_msg = f"Configuration validation failed: {'; '.join(errors)}"
            logger.error(f"GW-005 FAIL SECURE: {error_msg}")
            raise ConfigurationError(error_msg)

        # Log configuration (without sensitive values)
        logger.info(
            f"GW-005: Configuration loaded - "
            f"api_url={self._mask_url(self.api_url)}, "
            f"environment={self.environment}, "
            f"cache_ttl={self.cache_ttl_seconds}s, "
            f"timeout={self.timeout_seconds}s"
        )

    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask URL for logging (show domain only)."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}/..."
        except Exception:
            return "***masked***"

    @property
    def api_endpoint(self) -> str:
        """Get the full API endpoint for action submission."""
        base = self.api_url.rstrip('/')
        return f"{base}/api/v1/actions/submit"

    def get_headers(self) -> dict:
        """
        Get headers for ASCEND API requests.

        Returns:
            dict: Request headers including authentication
        """
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "ASCEND-Lambda-Authorizer/1.0.0"
        }


def load_config() -> AscendConfig:
    """
    Load configuration from environment variables.

    Supports loading API key from AWS Secrets Manager if
    ASCEND_API_KEY_SECRET_ARN is set.

    Returns:
        AscendConfig: Validated configuration object

    Raises:
        ConfigurationError: If required configuration is missing
    """
    # Check for Secrets Manager ARN first
    secret_arn = os.environ.get("ASCEND_API_KEY_SECRET_ARN")
    api_key = None

    if secret_arn:
        api_key = _load_secret_from_secrets_manager(secret_arn)

    if not api_key:
        api_key = os.environ.get("ASCEND_API_KEY", "")

    return AscendConfig(
        api_url=os.environ.get("ASCEND_API_URL", ""),
        api_key=api_key,
        environment=os.environ.get("ASCEND_ENVIRONMENT", "production"),
        cache_ttl_seconds=int(os.environ.get("ASCEND_CACHE_TTL", "60")),
        timeout_seconds=int(os.environ.get("ASCEND_TIMEOUT", "4")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
        cache_enabled=os.environ.get("ASCEND_CACHE_ENABLED", "true").lower() == "true",
        metrics_enabled=os.environ.get("ASCEND_METRICS_ENABLED", "true").lower() == "true"
    )


def _load_secret_from_secrets_manager(secret_arn: str) -> Optional[str]:
    """
    Load API key from AWS Secrets Manager.

    Args:
        secret_arn: ARN of the secret

    Returns:
        str: Secret value or None if failed
    """
    try:
        import boto3
        import json

        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_arn)

        # Handle both string and JSON secrets
        secret_string = response.get('SecretString', '')

        try:
            # Try parsing as JSON ({"api_key": "..."})
            secret_data = json.loads(secret_string)
            return secret_data.get('api_key') or secret_data.get('ASCEND_API_KEY')
        except json.JSONDecodeError:
            # Plain string secret
            return secret_string

    except Exception as e:
        logger.warning(f"GW-005: Failed to load secret from Secrets Manager: {e}")
        return None


# Validation helpers
VALID_ENVIRONMENTS = ["production", "staging", "development", "test"]
VALID_DATA_SENSITIVITIES = ["none", "low", "medium", "high", "pii", "high_sensitivity"]


def validate_environment(env: str) -> str:
    """Validate and normalize environment value."""
    env_lower = env.lower().strip()
    if env_lower in VALID_ENVIRONMENTS:
        return env_lower
    logger.warning(f"GW-005: Unknown environment '{env}', defaulting to 'production'")
    return "production"


def validate_data_sensitivity(sensitivity: str) -> str:
    """Validate and normalize data sensitivity value."""
    sens_lower = sensitivity.lower().strip()
    if sens_lower in VALID_DATA_SENSITIVITIES:
        return sens_lower
    logger.warning(f"GW-005: Unknown data sensitivity '{sensitivity}', defaulting to 'none'")
    return "none"
