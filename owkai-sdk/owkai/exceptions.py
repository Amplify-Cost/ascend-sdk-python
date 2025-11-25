"""
OW-AI SDK Exception Classes

Enterprise-grade exception hierarchy for comprehensive error handling.
All exceptions are designed to be informative without leaking sensitive data.

Security:
- No API keys or tokens in exception messages
- No internal system paths exposed
- Safe for logging and monitoring systems
"""

from typing import Optional


class OWKAIError(Exception):
    """
    Base exception for all OW-AI SDK errors.

    All SDK exceptions inherit from this class, allowing for broad
    exception catching when needed.

    Example:
        try:
            client.execute_action(...)
        except OWKAIError as e:
            logger.error(f"OW-AI SDK error: {e}")
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        """
        Initialize OWKAIError.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (e.g., "AUTH_001")
            details: Additional context (sanitized, no sensitive data)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def to_dict(self) -> dict:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class OWKAIAuthenticationError(OWKAIError):
    """
    Authentication failed.

    Raised when:
    - API key is invalid or malformed
    - API key has been revoked
    - API key has expired
    - Insufficient permissions for requested operation

    Example:
        try:
            client = OWKAIClient(api_key="invalid_key")
            client.execute_action(...)
        except OWKAIAuthenticationError:
            print("Please check your API key")
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        *,
        error_code: str = "AUTH_001",
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class OWKAIRateLimitError(OWKAIError):
    """
    Rate limit exceeded.

    Raised when the API key has exceeded its rate limit quota.
    Contains retry_after information for implementing backoff.

    Attributes:
        retry_after: Seconds to wait before retrying

    Example:
        try:
            client.execute_action(...)
        except OWKAIRateLimitError as e:
            time.sleep(e.retry_after)
            # Retry the request
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: int = 60,
        error_code: str = "RATE_001",
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
        self.retry_after = retry_after

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message} (retry after {self.retry_after}s)"


class OWKAIApprovalTimeoutError(OWKAIError):
    """
    Approval timeout exceeded.

    Raised when wait_for_approval() times out before receiving
    an approval or rejection decision.

    Attributes:
        action_id: The action ID that timed out
        timeout: The timeout value that was exceeded

    Example:
        try:
            status = client.wait_for_approval(action_id, timeout=300)
        except OWKAIApprovalTimeoutError as e:
            print(f"Action {e.action_id} not approved within {e.timeout}s")
    """

    def __init__(
        self,
        message: str = "Approval timeout exceeded",
        *,
        action_id: Optional[int] = None,
        timeout: Optional[int] = None,
        error_code: str = "APPROVAL_001",
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
        self.action_id = action_id
        self.timeout = timeout

    def __str__(self) -> str:
        parts = [f"[{self.error_code}] {self.message}"]
        if self.action_id:
            parts.append(f"action_id={self.action_id}")
        if self.timeout:
            parts.append(f"timeout={self.timeout}s")
        return " ".join(parts)


class OWKAIActionRejectedError(OWKAIError):
    """
    Action was rejected.

    Raised when an action is explicitly rejected by an approver.
    Contains the rejection reason for audit and debugging.

    Attributes:
        action_id: The rejected action ID
        rejection_reason: Reason provided by the approver
        rejected_by: Email of the rejecting approver

    Example:
        try:
            status = client.wait_for_approval(action_id)
        except OWKAIActionRejectedError as e:
            print(f"Action rejected: {e.rejection_reason}")
            print(f"Rejected by: {e.rejected_by}")
    """

    def __init__(
        self,
        message: str = "Action was rejected",
        *,
        action_id: Optional[int] = None,
        rejection_reason: Optional[str] = None,
        rejected_by: Optional[str] = None,
        error_code: str = "REJECTED_001",
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
        self.action_id = action_id
        self.rejection_reason = rejection_reason
        self.rejected_by = rejected_by

    def __str__(self) -> str:
        parts = [f"[{self.error_code}] {self.message}"]
        if self.rejection_reason:
            parts.append(f"reason='{self.rejection_reason}'")
        return " ".join(parts)


class OWKAIValidationError(OWKAIError):
    """
    Request validation failed.

    Raised when request parameters fail validation before
    being sent to the API.

    Attributes:
        field: The field that failed validation
        constraint: The validation constraint that was violated

    Example:
        try:
            client.execute_action(action_type="")  # Empty not allowed
        except OWKAIValidationError as e:
            print(f"Invalid {e.field}: {e.constraint}")
    """

    def __init__(
        self,
        message: str = "Validation failed",
        *,
        field: Optional[str] = None,
        constraint: Optional[str] = None,
        error_code: str = "VALIDATION_001",
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
        self.field = field
        self.constraint = constraint

    def __str__(self) -> str:
        if self.field:
            return f"[{self.error_code}] {self.message}: {self.field}"
        return f"[{self.error_code}] {self.message}"


class OWKAINetworkError(OWKAIError):
    """
    Network communication error.

    Raised when there's a network-level failure communicating
    with the OW-AI API.

    Attributes:
        is_retryable: Whether the request should be retried

    Example:
        try:
            client.execute_action(...)
        except OWKAINetworkError as e:
            if e.is_retryable:
                # Implement retry logic
                pass
    """

    def __init__(
        self,
        message: str = "Network error",
        *,
        is_retryable: bool = True,
        error_code: str = "NETWORK_001",
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
        self.is_retryable = is_retryable


class OWKAIServerError(OWKAIError):
    """
    Server-side error.

    Raised when the OW-AI API returns a 5xx error.
    Generally indicates a temporary issue that may resolve with retry.

    Attributes:
        status_code: HTTP status code (500, 502, 503, etc.)
        is_retryable: Whether the request should be retried
    """

    def __init__(
        self,
        message: str = "Server error",
        *,
        status_code: int = 500,
        is_retryable: bool = True,
        error_code: str = "SERVER_001",
        details: Optional[dict] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)
        self.status_code = status_code
        self.is_retryable = is_retryable

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message} (HTTP {self.status_code})"
