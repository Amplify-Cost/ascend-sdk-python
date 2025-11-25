"""
OW-AI SDK Retry Utilities

Enterprise-grade retry logic with exponential backoff.
Designed for reliability in distributed systems.

Features:
- Configurable retry attempts and delays
- Exponential backoff with jitter
- Selective retry based on exception type
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Optional, Set, Type, TypeVar

from owkai.exceptions import (
    OWKAIError,
    OWKAINetworkError,
    OWKAIRateLimitError,
    OWKAIServerError,
)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay between retries in seconds (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Whether to add random jitter (default: True)
        retryable_exceptions: Exception types to retry on
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Set[Type[Exception]] = field(
        default_factory=lambda: {
            OWKAINetworkError,
            OWKAIServerError,
            OWKAIRateLimitError,
            ConnectionError,
            TimeoutError,
        }
    )

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.

        Uses exponential backoff with optional jitter.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base ** attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter (0-25% of delay)
        if self.jitter:
            jitter_amount = delay * 0.25 * random.random()
            delay += jitter_amount

        return delay

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if a request should be retried.

        Args:
            exception: The exception that was raised
            attempt: Current attempt number (0-indexed)

        Returns:
            True if should retry, False otherwise
        """
        # Check attempt count
        if attempt >= self.max_attempts - 1:
            return False

        # Check if exception is retryable
        for exc_type in self.retryable_exceptions:
            if isinstance(exception, exc_type):
                # Special handling for rate limit
                if isinstance(exception, OWKAIRateLimitError):
                    return True
                # Check is_retryable attribute if present
                if hasattr(exception, "is_retryable"):
                    return exception.is_retryable
                return True

        return False


def with_retry(
    config: Optional[RetryConfig] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for synchronous retry logic.

    Example:
        @with_retry(RetryConfig(max_attempts=5))
        def make_request():
            return client.get("/api/data")
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not config.should_retry(e, attempt):
                        raise

                    # Handle rate limit with specific retry-after
                    if isinstance(e, OWKAIRateLimitError):
                        delay = e.retry_after
                    else:
                        delay = config.calculate_delay(attempt)

                    time.sleep(delay)

            # Should not reach here, but raise last exception if we do
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry exhausted without exception")

        return wrapper

    return decorator


def async_with_retry(
    config: Optional[RetryConfig] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for asynchronous retry logic.

    Example:
        @async_with_retry(RetryConfig(max_attempts=5))
        async def make_request():
            return await client.get("/api/data")
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not config.should_retry(e, attempt):
                        raise

                    # Handle rate limit with specific retry-after
                    if isinstance(e, OWKAIRateLimitError):
                        delay = e.retry_after
                    else:
                        delay = config.calculate_delay(attempt)

                    await asyncio.sleep(delay)

            # Should not reach here, but raise last exception if we do
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry exhausted without exception")

        return wrapper

    return decorator
