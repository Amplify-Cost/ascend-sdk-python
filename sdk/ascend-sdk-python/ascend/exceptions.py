"""
Ascend AI SDK Exceptions
=========================

Custom exceptions for enterprise-grade error handling.
"""


class AscendError(Exception):
    """Base exception for all Ascend SDK errors."""

    def __init__(self, message: str, status_code: int = None, response: dict = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response or {}


class AuthenticationError(AscendError):
    """
    Raised when API key authentication fails.

    Typical causes:
    - Invalid API key
    - Expired API key
    - Missing API key
    - Revoked API key

    Resolution:
    - Verify ASCEND_API_KEY environment variable
    - Check API key in Ascend console
    - Generate new API key if needed
    """
    pass


class AuthorizationDeniedError(AscendError):
    """
    Raised when an agent action is denied by policy.

    This is NOT an error condition - it's the expected behavior
    when a policy denies an action. The agent should gracefully
    handle this and not retry.

    The response contains the denial reason and policy details.
    """
    pass


class RateLimitError(AscendError):
    """
    Raised when API rate limit is exceeded (HTTP 429).

    The SDK automatically retries with exponential backoff.
    If you receive this error, all retries have been exhausted.

    Resolution:
    - Wait before retrying
    - Check rate limit headers in response
    - Contact Ascend support to increase limits
    """
    pass


class TimeoutError(AscendError):
    """
    Raised when an operation times out.

    This can occur in two scenarios:
    1. Network timeout - request took too long
    2. Decision timeout - no decision within wait period

    For decision timeouts, check the action status later.
    """
    pass


class ValidationError(AscendError):
    """
    Raised when input validation fails.

    Typical causes:
    - Missing required fields
    - Invalid field types
    - Invalid enum values
    - Field value constraints
    """
    pass


class NetworkError(AscendError):
    """
    Raised when network connectivity fails.

    Typical causes:
    - DNS resolution failure
    - Connection refused
    - Network unreachable
    - SSL/TLS certificate verification failure

    Resolution:
    - Check internet connectivity
    - Verify API URL is correct
    - Check firewall/proxy settings
    """
    pass


class ServerError(AscendError):
    """
    Raised when the Ascend API returns a 5xx error.

    This indicates a problem with the Ascend service.
    The SDK automatically retries these errors.

    If persistent, contact Ascend support.
    """
    pass


class NotFoundError(AscendError):
    """
    Raised when a resource is not found (HTTP 404).

    Typical causes:
    - Invalid action_id
    - Action belongs to different organization
    - Resource has been deleted
    """
    pass


class ConflictError(AscendError):
    """
    Raised when a resource conflict occurs (HTTP 409).

    Typical causes:
    - Duplicate resource creation
    - Concurrent modification
    - State transition violation
    """
    pass
