"""Retry logic with exponential backoff for transient failures.

This module provides retry functionality with configurable exponential backoff
for handling transient failures in database and LLM operations.
"""

import asyncio
import logging
from typing import Any, Callable, TypeVar

from asyncpg.exceptions import (
    ConnectionDoesNotExistError,
    ConnectionFailureError,
    PostgresConnectionError,
    TooManyConnectionsError,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default retriable exceptions for asyncpg
DEFAULT_RETRIABLE_EXCEPTIONS = (
    ConnectionDoesNotExistError,
    ConnectionFailureError,
    PostgresConnectionError,
    TooManyConnectionsError,
    asyncio.TimeoutError,
    OSError,  # Network-related errors
)


class RetryConfig:
    """Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts (including initial attempt).
        initial_delay: Initial delay in seconds before first retry.
        backoff_factor: Multiplier for delay between retries (exponential backoff).
        max_delay: Maximum delay in seconds between retries.
        retriable_exceptions: Tuple of exception types that should trigger retries.

    Example:
        >>> config = RetryConfig(
        ...     max_attempts=3,
        ...     initial_delay=1.0,
        ...     backoff_factor=2.0,
        ...     max_delay=30.0,
        ...     retriable_exceptions=(ConnectionError, TimeoutError),
        ... )
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        retriable_exceptions: tuple[type[Exception], ...] = DEFAULT_RETRIABLE_EXCEPTIONS,
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts (default: 3).
            initial_delay: Initial delay in seconds (default: 1.0).
            backoff_factor: Exponential backoff multiplier (default: 2.0).
            max_delay: Maximum delay cap in seconds (default: 60.0).
            retriable_exceptions: Tuple of exception types to retry on.
        """
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if initial_delay < 0:
            raise ValueError("initial_delay must be non-negative")
        if backoff_factor < 1:
            raise ValueError("backoff_factor must be at least 1")
        if max_delay < initial_delay:
            raise ValueError("max_delay must be >= initial_delay")

        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.retriable_exceptions = retriable_exceptions


async def retry_with_backoff(
    func: Callable[..., T],
    config: RetryConfig,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Execute a function with exponential backoff retry logic.

    This function attempts to execute the provided async function, retrying
    on retriable exceptions with exponential backoff delays.

    Args:
        func: Async function to execute.
        config: Retry configuration.
        *args: Positional arguments to pass to func.
        **kwargs: Keyword arguments to pass to func.

    Returns:
        The return value of func if successful.

    Raises:
        The last exception encountered if all retry attempts fail.

    Example:
        >>> config = RetryConfig(max_attempts=3, initial_delay=1.0)
        >>> result = await retry_with_backoff(
        ...     my_async_function,
        ...     config,
        ...     arg1, arg2,
        ...     kwarg1=value1
        ... )
    """
    last_exception: Exception | None = None
    delay = config.initial_delay

    for attempt in range(1, config.max_attempts + 1):
        try:
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Log success if this wasn't the first attempt
            if attempt > 1:
                logger.info(
                    f"Operation succeeded on attempt {attempt}/{config.max_attempts}",
                    extra={"attempt": attempt, "max_attempts": config.max_attempts},
                )
            
            return result

        except config.retriable_exceptions as e:
            last_exception = e
            
            # Check if we have more attempts left
            if attempt < config.max_attempts:
                logger.warning(
                    f"Retriable error on attempt {attempt}/{config.max_attempts}: {e!s}",
                    extra={
                        "attempt": attempt,
                        "max_attempts": config.max_attempts,
                        "error_type": type(e).__name__,
                        "retry_delay": delay,
                    },
                )
                
                # Wait before retrying
                await asyncio.sleep(delay)
                
                # Calculate next delay with exponential backoff
                delay = min(delay * config.backoff_factor, config.max_delay)
            else:
                # No more retries left
                logger.error(
                    f"All {config.max_attempts} attempts failed",
                    extra={
                        "attempts": config.max_attempts,
                        "error_type": type(e).__name__,
                        "error": str(e),
                    },
                )

        except Exception as e:
            # Non-retriable exception - fail immediately
            logger.error(
                f"Non-retriable error on attempt {attempt}: {e!s}",
                extra={
                    "attempt": attempt,
                    "error_type": type(e).__name__,
                },
            )
            raise

    # All retries exhausted, raise the last exception
    if last_exception:
        raise last_exception
    
    # This should never happen, but satisfy type checker
    raise RuntimeError("Retry logic error: no exception but no success")


def with_retry(config: RetryConfig | None = None):
    """Decorator to add retry logic to async functions.

    This decorator wraps an async function with retry logic using the
    provided configuration.

    Args:
        config: Retry configuration. If None, uses default configuration.

    Returns:
        Decorator function.

    Example:
        >>> @with_retry(RetryConfig(max_attempts=3))
        ... async def fetch_data():
        ...     # Function that might fail transiently
        ...     return await db.query(...)
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_with_backoff(func, config, *args, **kwargs)

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


class RetryableOperation:
    """Context manager for retry operations with custom exception handling.

    This class provides a context manager interface for operations that need
    retry logic with custom exception handling and cleanup.

    Example:
        >>> async with RetryableOperation(
        ...     config=RetryConfig(max_attempts=3),
        ...     operation_name="database_query"
        ... ) as retry:
        ...     result = await retry.execute(my_async_function, arg1, arg2)
    """

    def __init__(
        self,
        config: RetryConfig,
        operation_name: str | None = None,
    ):
        """Initialize retryable operation context.

        Args:
            config: Retry configuration.
            operation_name: Optional name for logging purposes.
        """
        self.config = config
        self.operation_name = operation_name or "operation"
        self.attempt = 0
        self.last_error: Exception | None = None

    async def __aenter__(self):
        """Enter the async context."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context."""
        # Context manager cleanup if needed
        return False

    async def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute function with retry logic.

        Args:
            func: Async function to execute.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.

        Returns:
            Result of func.

        Raises:
            Exception if all retries fail.
        """
        return await retry_with_backoff(func, self.config, *args, **kwargs)
