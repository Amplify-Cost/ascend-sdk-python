"""
ASCEND SDK Exception Classes
=============================

Enterprise-grade exception handling with detailed error context.
"""

from typing import Optional, Dict, Any


class OWKAIError(Exception):
    """Base exception for all OW-AI SDK errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class AuthenticationError(OWKAIError):
    """
    Raised when authentication fails.

    Possible causes:
    - Invalid API key
    - Expired credentials
    - API key not authorized for organization
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class AuthorizationError(OWKAIError):
    """
    Raised when an action is denied.

    Contains details about why the action was denied
    and any policy violations.
    """

    def __init__(
        self,
        message: str = "Action not authorized",
        error_code: str = "AUTHZ_DENIED",
        policy_violations: Optional[list] = None,
        risk_score: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if policy_violations:
            details["policy_violations"] = policy_violations
        if risk_score is not None:
            details["risk_score"] = risk_score

        super().__init__(message, error_code, details)
        self.policy_violations = policy_violations or []
        self.risk_score = risk_score


class TimeoutError(OWKAIError):
    """
    Raised when an operation times out.

    This can occur when:
    - API request exceeds timeout
    - Waiting for approval decision exceeds timeout
    """

    def __init__(
        self,
        message: str = "Operation timed out",
        error_code: str = "TIMEOUT",
        timeout_seconds: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds

        super().__init__(message, error_code, details)
        self.timeout_seconds = timeout_seconds


class RateLimitError(OWKAIError):
    """
    Raised when rate limit is exceeded.

    Contains information about when to retry.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: str = "RATE_LIMIT",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if retry_after:
            details["retry_after_seconds"] = retry_after

        super().__init__(message, error_code, details)
        self.retry_after = retry_after


class ValidationError(OWKAIError):
    """
    Raised when input validation fails.

    Contains details about which fields failed validation.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
        field_errors: Optional[Dict[str, str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if field_errors:
            details["field_errors"] = field_errors

        super().__init__(message, error_code, details)
        self.field_errors = field_errors or {}


class ConnectionError(OWKAIError):
    """
    Raised when connection to API fails.
    """

    def __init__(
        self,
        message: str = "Failed to connect to OW-AI API",
        error_code: str = "CONNECTION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class CircuitBreakerOpen(OWKAIError):
    """
    Raised when circuit breaker is open due to repeated failures.

    The circuit breaker prevents cascading failures by failing fast
    when the ASCEND service appears to be down.
    """

    def __init__(
        self,
        message: str = "Circuit breaker is open - service appears to be down",
        error_code: str = "CIRCUIT_OPEN",
        recovery_time: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if recovery_time:
            details["recovery_time_seconds"] = recovery_time

        super().__init__(message, error_code, details)
        self.recovery_time = recovery_time


class ConfigurationError(OWKAIError):
    """
    Raised when SDK configuration is invalid.

    Examples: HTTP URL for non-localhost, missing required config.
    """

    def __init__(
        self,
        message: str = "Invalid SDK configuration",
        error_code: str = "CONFIG_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class KillSwitchError(OWKAIError):
    """
    Raised when the kill switch is active and all actions are blocked.
    """

    def __init__(
        self,
        message: str = "Kill switch is active - all actions are blocked",
        error_code: str = "KILL_SWITCH_ACTIVE",
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if reason:
            details["reason"] = reason

        super().__init__(message, error_code, details)
        self.reason = reason
