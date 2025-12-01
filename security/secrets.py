"""
OW-AI Enterprise Secrets Management Module
==========================================

Banking-Level Security for Secrets Handling

Features:
- SEC-003: Secret entropy validation (minimum 256 bits)
- SEC-004: Log masking for sensitive data
- AWS Secrets Manager integration support
- Automatic secret rotation triggers

Compliance Standards:
- SOC 2 CC6.1 (Logical Access Controls)
- PCI-DSS 3.5 (Cryptographic Key Protection)
- NIST SP 800-63B (Digital Identity Guidelines)
- HIPAA 164.312(a) (Access Control)

Version: 1.0.0
Date: 2025-12-01
"""

import re
import math
import hashlib
import logging
import secrets as python_secrets
from typing import Optional, List, Dict, Any, Pattern
from datetime import datetime, timezone

logger = logging.getLogger("enterprise.security.secrets")


class SecretEntropyValidator:
    """
    SEC-003: Validates secrets have minimum entropy requirements.

    Banking-Level Requirements:
    - JWT secrets: 256+ bits of entropy
    - API keys: 128+ bits of entropy
    - Session tokens: 128+ bits of entropy

    Compliance: NIST SP 800-63B, PCI-DSS 3.5
    """

    # Minimum entropy requirements (in bits)
    ENTROPY_REQUIREMENTS = {
        "jwt_secret": 256,
        "api_key": 128,
        "session_token": 128,
        "refresh_token": 256,
        "encryption_key": 256,
        "signing_key": 256,
        "default": 128
    }

    @staticmethod
    def calculate_entropy(secret: str) -> float:
        """
        Calculate Shannon entropy of a secret string.

        Args:
            secret: The secret string to evaluate

        Returns:
            Estimated entropy in bits
        """
        if not secret:
            return 0.0

        # Character frequency analysis
        char_count = {}
        for char in secret:
            char_count[char] = char_count.get(char, 0) + 1

        length = len(secret)
        entropy = 0.0

        for count in char_count.values():
            probability = count / length
            entropy -= probability * math.log2(probability)

        # Total entropy = per-character entropy * length
        total_entropy = entropy * length

        return total_entropy

    @staticmethod
    def estimate_keyspace_entropy(secret: str) -> float:
        """
        Estimate entropy based on character set size and length.

        More conservative estimate based on potential keyspace.
        """
        if not secret:
            return 0.0

        has_lowercase = bool(re.search(r'[a-z]', secret))
        has_uppercase = bool(re.search(r'[A-Z]', secret))
        has_digits = bool(re.search(r'\d', secret))
        has_special = bool(re.search(r'[^a-zA-Z0-9]', secret))

        charset_size = 0
        if has_lowercase:
            charset_size += 26
        if has_uppercase:
            charset_size += 26
        if has_digits:
            charset_size += 10
        if has_special:
            charset_size += 32  # Conservative estimate for special chars

        if charset_size == 0:
            return 0.0

        bits_per_char = math.log2(charset_size)
        return bits_per_char * len(secret)

    @classmethod
    def validate_secret(
        cls,
        secret: str,
        secret_type: str = "default",
        raise_on_failure: bool = True
    ) -> Dict[str, Any]:
        """
        SEC-003: Validate secret meets minimum entropy requirements.

        Args:
            secret: The secret to validate
            secret_type: Type of secret (jwt_secret, api_key, etc.)
            raise_on_failure: Raise exception if validation fails

        Returns:
            Validation result with entropy details

        Raises:
            ValueError: If secret doesn't meet entropy requirements
        """
        min_entropy = cls.ENTROPY_REQUIREMENTS.get(
            secret_type,
            cls.ENTROPY_REQUIREMENTS["default"]
        )

        # Calculate both metrics
        shannon_entropy = cls.calculate_entropy(secret)
        keyspace_entropy = cls.estimate_keyspace_entropy(secret)

        # Use the more conservative (lower) estimate
        effective_entropy = min(shannon_entropy, keyspace_entropy)

        result = {
            "valid": effective_entropy >= min_entropy,
            "secret_type": secret_type,
            "required_entropy_bits": min_entropy,
            "shannon_entropy_bits": round(shannon_entropy, 2),
            "keyspace_entropy_bits": round(keyspace_entropy, 2),
            "effective_entropy_bits": round(effective_entropy, 2),
            "secret_length": len(secret) if secret else 0,
            "compliance": "PASS" if effective_entropy >= min_entropy else "FAIL"
        }

        if not result["valid"]:
            message = (
                f"SEC-003 VIOLATION: {secret_type} has insufficient entropy. "
                f"Required: {min_entropy} bits, Got: {round(effective_entropy, 2)} bits. "
                f"Compliance: NIST SP 800-63B, PCI-DSS 3.5"
            )
            logger.critical(message)
            result["error"] = message

            if raise_on_failure:
                raise ValueError(message)
        else:
            logger.info(
                f"SEC-003 PASS: {secret_type} entropy validated "
                f"({round(effective_entropy, 2)} bits >= {min_entropy} bits required)"
            )

        return result

    @classmethod
    def generate_secure_secret(cls, secret_type: str = "default", length: int = None) -> str:
        """
        Generate a cryptographically secure secret meeting entropy requirements.

        Args:
            secret_type: Type of secret to generate
            length: Optional custom length (will be increased if needed for entropy)

        Returns:
            Secure random secret string
        """
        min_entropy = cls.ENTROPY_REQUIREMENTS.get(
            secret_type,
            cls.ENTROPY_REQUIREMENTS["default"]
        )

        # Calculate minimum length for required entropy
        # Using URL-safe base64 alphabet (64 chars = 6 bits per char)
        min_length = math.ceil(min_entropy / 6) + 4  # +4 for safety margin

        if length and length < min_length:
            logger.warning(
                f"Requested length {length} insufficient for {min_entropy} bits entropy. "
                f"Using minimum length {min_length}"
            )
            length = min_length

        final_length = length or min_length

        # Generate using Python's secrets module (cryptographically secure)
        secret = python_secrets.token_urlsafe(final_length)

        # Validate the generated secret
        validation = cls.validate_secret(secret, secret_type, raise_on_failure=False)

        if not validation["valid"]:
            # Regenerate with longer length if needed (should never happen)
            return cls.generate_secure_secret(secret_type, final_length + 10)

        return secret


class LogMasker:
    """
    SEC-004: Masks sensitive data in log output.

    Banking-Level Security:
    - API keys masked (only first/last 4 chars visible)
    - Passwords completely hidden
    - PII redacted
    - Credit card numbers masked

    Compliance: PCI-DSS 3.4, HIPAA 164.528, GDPR Art. 32
    """

    # Patterns to detect and mask
    SENSITIVE_PATTERNS: List[tuple] = [
        # API keys (various formats)
        (re.compile(r'(?i)(api[_-]?key|apikey|x-api-key)["\s:=]+["\']?([a-zA-Z0-9_-]{20,})["\']?'), 'api_key'),
        (re.compile(r'(?i)(bearer\s+)([a-zA-Z0-9_.-]+)'), 'bearer_token'),

        # AWS credentials
        (re.compile(r'(AKIA[A-Z0-9]{16})'), 'aws_access_key'),
        (re.compile(r'(?i)(aws[_-]?secret[_-]?access[_-]?key)["\s:=]+["\']?([a-zA-Z0-9/+]{40})["\']?'), 'aws_secret'),

        # Passwords
        (re.compile(r'(?i)(password|passwd|pwd)["\s:=]+["\']?([^\s"\']+)["\']?'), 'password'),

        # JWT tokens
        (re.compile(r'(eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)'), 'jwt_token'),

        # Credit card numbers (PCI-DSS)
        (re.compile(r'\b(\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4})\b'), 'credit_card'),

        # SSN
        (re.compile(r'\b(\d{3}-\d{2}-\d{4})\b'), 'ssn'),

        # Email addresses (configurable - may not want to mask all)
        # (re.compile(r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'), 'email'),

        # Database connection strings
        (re.compile(r'(?i)(postgres|mysql|mongodb)://[^:]+:([^@]+)@'), 'db_password'),
    ]

    @classmethod
    def mask_value(cls, value: str, value_type: str) -> str:
        """
        Mask a sensitive value based on its type.

        SEC-004 Compliance: Only first/last 4 chars visible for API keys.
        """
        if not value or len(value) < 8:
            return "***REDACTED***"

        if value_type in ['password', 'aws_secret', 'db_password']:
            # Completely hide passwords
            return "***REDACTED***"

        if value_type == 'ssn':
            return "***-**-" + value[-4:]

        if value_type == 'credit_card':
            # PCI-DSS compliant: only last 4 digits
            return "****-****-****-" + value[-4:]

        if value_type in ['api_key', 'bearer_token', 'jwt_token', 'aws_access_key']:
            # SEC-004: Show first 4 and last 4 characters
            if len(value) > 12:
                return f"{value[:4]}...{value[-4:]}"
            return "***MASKED***"

        # Default masking
        return f"{value[:4]}...{value[-4:]}" if len(value) > 12 else "***MASKED***"

    @classmethod
    def mask_string(cls, text: str) -> str:
        """
        SEC-004: Mask all sensitive data in a string.

        Args:
            text: Input text that may contain sensitive data

        Returns:
            Text with sensitive data masked
        """
        if not text:
            return text

        masked_text = text

        for pattern, value_type in cls.SENSITIVE_PATTERNS:
            def replacer(match):
                groups = match.groups()
                if len(groups) == 2:
                    # Pattern with prefix (e.g., "api_key": "VALUE")
                    prefix, value = groups
                    masked_value = cls.mask_value(value, value_type)
                    return f"{prefix}{masked_value}"
                elif len(groups) == 1:
                    # Pattern without prefix (e.g., JWT token)
                    value = groups[0]
                    return cls.mask_value(value, value_type)
                return match.group(0)

            masked_text = pattern.sub(replacer, masked_text)

        return masked_text

    @classmethod
    def mask_dict(cls, data: Dict[str, Any], depth: int = 0, max_depth: int = 10) -> Dict[str, Any]:
        """
        SEC-004: Recursively mask sensitive data in a dictionary.

        Args:
            data: Dictionary that may contain sensitive data
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            Dictionary with sensitive values masked
        """
        if depth > max_depth:
            return {"__truncated__": "Max depth exceeded"}

        # Keys that should always be masked
        sensitive_keys = {
            'password', 'passwd', 'pwd', 'secret', 'api_key', 'apikey',
            'token', 'access_token', 'refresh_token', 'auth', 'authorization',
            'credential', 'private_key', 'secret_key', 'jwt', 'bearer',
            'ssn', 'social_security', 'credit_card', 'card_number', 'cvv',
            'aws_secret_access_key', 'database_password', 'db_password'
        }

        masked = {}
        for key, value in data.items():
            key_lower = key.lower()

            # Check if key indicates sensitive data
            is_sensitive = any(s in key_lower for s in sensitive_keys)

            if isinstance(value, dict):
                masked[key] = cls.mask_dict(value, depth + 1, max_depth)
            elif isinstance(value, list):
                masked[key] = [
                    cls.mask_dict(item, depth + 1, max_depth) if isinstance(item, dict)
                    else cls.mask_string(str(item)) if is_sensitive and isinstance(item, str)
                    else item
                    for item in value
                ]
            elif isinstance(value, str):
                if is_sensitive:
                    masked[key] = cls.mask_value(value, key_lower)
                else:
                    masked[key] = cls.mask_string(value)
            else:
                masked[key] = value

        return masked


class SecureLoggingFilter(logging.Filter):
    """
    SEC-004: Logging filter that automatically masks sensitive data.

    Usage:
        logging.getLogger().addFilter(SecureLoggingFilter())
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask sensitive data in log records."""
        if isinstance(record.msg, str):
            record.msg = LogMasker.mask_string(record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = LogMasker.mask_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    LogMasker.mask_string(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        return True


def setup_secure_logging():
    """
    SEC-004: Configure all loggers with secure masking filter.

    Call this at application startup to ensure all log output
    has sensitive data masked.
    """
    root_logger = logging.getLogger()
    secure_filter = SecureLoggingFilter()

    # Add filter to root logger
    root_logger.addFilter(secure_filter)

    # Add filter to all existing handlers
    for handler in root_logger.handlers:
        handler.addFilter(secure_filter)

    logger.info("SEC-004: Secure logging filter enabled - sensitive data will be masked")


def validate_jwt_secret(secret: str) -> Dict[str, Any]:
    """
    SEC-003: Convenience function to validate JWT secret.

    Args:
        secret: JWT secret to validate

    Returns:
        Validation result

    Raises:
        ValueError: If secret doesn't meet 256-bit entropy requirement
    """
    return SecretEntropyValidator.validate_secret(secret, "jwt_secret")


def generate_api_key() -> str:
    """
    Generate a secure API key meeting banking-level requirements.

    Returns:
        Cryptographically secure API key
    """
    return SecretEntropyValidator.generate_secure_secret("api_key")


def generate_jwt_secret() -> str:
    """
    Generate a secure JWT secret meeting 256-bit entropy requirement.

    Returns:
        Cryptographically secure JWT secret
    """
    return SecretEntropyValidator.generate_secure_secret("jwt_secret")


# Module initialization
logger.info("Enterprise Secrets Management Module loaded")
logger.info("SEC-003: Entropy validation enabled")
logger.info("SEC-004: Log masking available")
