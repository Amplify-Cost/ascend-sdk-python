"""
SEC-BYOK: Custom exceptions for BYOK encryption service.

These exceptions implement FAIL SECURE pattern:
- When encryption key issues occur, operations are BLOCKED
- No fallback that bypasses customer key when BYOK is configured
"""


class BYOKError(Exception):
    """Base exception for all BYOK-related errors."""
    pass


class KeyAccessDenied(BYOKError):
    """
    Raised when customer's CMK access is denied.

    This typically means:
    - Customer revoked ASCEND's access to the key
    - Key policy was modified
    - Key was disabled

    FAIL SECURE: When this occurs, all encryption/decryption operations
    for this tenant are blocked until access is restored.
    """
    pass


class EncryptionError(BYOKError):
    """
    Raised for encryption/decryption errors.

    This includes:
    - KMS API errors
    - Invalid ciphertext
    - Algorithm mismatches

    FAIL SECURE: Operations are blocked on error.
    """
    pass


class DataAccessBlocked(BYOKError):
    """
    Raised when data access is blocked due to encryption key issues.

    This is the FAIL SECURE response when:
    - BYOK is configured but key status is not 'active'
    - CMK access is revoked
    - Key is in error state

    The data exists but cannot be read until key access is restored.
    """
    pass


class KeyNotConfigured(BYOKError):
    """
    Raised when attempting BYOK operations without a configured key.

    This is NOT a security error - it means the tenant hasn't set up BYOK.
    Operations should fall back to platform default encryption.
    """
    pass


class KeyValidationFailed(BYOKError):
    """
    Raised when CMK validation fails during registration or health check.

    This means ASCEND cannot perform required operations on the customer's CMK.
    Common causes:
    - Incorrect key policy
    - Missing permissions
    - Key disabled or deleted
    """
    pass


class DEKGenerationFailed(BYOKError):
    """
    Raised when Data Encryption Key generation fails.

    This typically indicates a KMS issue or permission problem.
    """
    pass


class KeyRotationFailed(BYOKError):
    """
    Raised when key rotation operation fails.

    This can occur during:
    - Manual rotation via API
    - Automatic rotation detection
    """
    pass
