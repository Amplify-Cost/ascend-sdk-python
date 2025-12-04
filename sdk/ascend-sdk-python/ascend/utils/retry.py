"""
Retry utilities with exponential backoff.

Enterprise-grade retry logic for transient failures.
"""

import time
import logging
from typing import Callable, Any, Set, TypeVar
from functools import wraps

from ..exceptions import RateLimitError, ServerError, NetworkError
from ..constants import DEFAULT_MAX_RETRIES, DEFAULT_RETRY_BACKOFF_FACTOR, RETRY_STATUS_CODES

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_RETRY_BACKOFF_FACTOR,
    retry_status_codes: Set[int] = RETRY_STATUS_CODES
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Retries on:
    - Network errors (connection, timeout)
    - Server errors (500, 502, 503, 504)
    - Rate limit errors (429)

    Does NOT retry on:
    - Authentication errors (401, 403)
    - Validation errors (400, 422)
    - Not found errors (404)
    - Authorization denied (business logic, not transient)

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        retry_status_codes: HTTP status codes to retry

    Example:
        @retry_with_backoff(max_retries=3)
        def make_api_call():
            return requests.get("https://api.example.com")
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except (NetworkError, ServerError, RateLimitError) as e:
                    last_exception = e

                    # Don't retry if we've exhausted attempts
                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exhausted for {func.__name__}: {e}"
                        )
                        raise

                    # Calculate backoff delay: 1s, 2s, 4s, 8s...
                    delay = backoff_factor ** attempt

                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                        f"after {delay:.1f}s delay: {e}"
                    )

                    time.sleep(delay)

                except Exception as e:
                    # Don't retry on non-retryable errors
                    logger.debug(f"Non-retryable error in {func.__name__}: {e}")
                    raise

            # Should never reach here, but satisfy type checker
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry logic error")

        return wrapper

    return decorator


def should_retry(status_code: int, retry_status_codes: Set[int] = RETRY_STATUS_CODES) -> bool:
    """
    Determine if an HTTP status code should be retried.

    Args:
        status_code: HTTP status code
        retry_status_codes: Set of status codes to retry

    Returns:
        True if should retry, False otherwise
    """
    return status_code in retry_status_codes
