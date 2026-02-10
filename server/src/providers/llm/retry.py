"""Exponential backoff retry logic for LLM provider calls."""

import asyncio
from typing import TypeVar, Callable, Awaitable

import httpx

T = TypeVar("T")

# Errors that are safe to retry (transient network / server issues)
RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.WriteError,
    httpx.ConnectTimeout,
    httpx.ReadTimeout,
    httpx.PoolTimeout,
    ConnectionError,
    TimeoutError,
    OSError,
)

# HTTP status codes worth retrying
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 529}

# HTTP status codes that should NOT be retried (permanent errors)
NON_RETRYABLE_STATUS_CODES = {401, 402, 403, 404}


def _is_retryable_exception(exc: Exception) -> bool:
    """Determine if an exception is transient and worth retrying."""
    # Direct network errors
    if isinstance(exc, RETRYABLE_EXCEPTIONS):
        return True

    # httpx.HTTPStatusError with retryable status
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS_CODES

    # Generic exceptions wrapping HTTP errors (our providers raise Exception with status info)
    msg = str(exc).lower()
    for code in NON_RETRYABLE_STATUS_CODES:
        if f"({code})" in str(exc):
            return False
    for code in RETRYABLE_STATUS_CODES:
        if f"({code})" in str(exc):
            return True

    # Network-related keywords in the error message
    retryable_keywords = [
        "connect", "timeout", "read error", "connection reset",
        "server disconnected", "overloaded", "rate limit",
    ]
    if any(kw in msg for kw in retryable_keywords):
        return True

    return False


async def retry_with_backoff(
    fn: Callable[..., Awaitable[T]],
    *args: object,
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 16.0,
    **kwargs: object,
) -> T:
    """
    Call an async function with exponential backoff on retryable errors.

    Args:
        fn: Async function to call
        *args: Positional arguments for fn
        max_retries: Maximum number of retry attempts (total calls = max_retries + 1)
        base_delay: Initial delay in seconds (doubles each retry)
        max_delay: Maximum delay cap in seconds
        **kwargs: Keyword arguments for fn

    Returns:
        Result of fn

    Raises:
        The last exception if all retries are exhausted,
        or immediately for non-retryable errors.
    """
    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            last_exception = exc

            if attempt >= max_retries or not _is_retryable_exception(exc):
                raise

            delay = min(base_delay * (2 ** attempt), max_delay)
            print(
                f"[RETRY] Attempt {attempt + 1}/{max_retries + 1} failed: "
                f"{type(exc).__name__}: {exc}. "
                f"Retrying in {delay:.1f}s..."
            )
            await asyncio.sleep(delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    raise RuntimeError("retry_with_backoff exhausted without result")
