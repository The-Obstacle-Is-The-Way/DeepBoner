"""Retry middleware for chat clients with exponential backoff."""

import asyncio
import random
from collections.abc import Awaitable, Callable

import structlog
from agent_framework._middleware import ChatContext, ChatMiddleware

logger = structlog.get_logger()


class RetryMiddleware(ChatMiddleware):
    """Retries failed chat requests with exponential backoff.

    This middleware intercepts chat client calls and retries on transient
    errors (rate limits, timeouts, server errors).

    Attributes:
        max_attempts: Maximum number of attempts (default: 3)
        min_wait: Minimum wait between retries in seconds (default: 1.0)
        max_wait: Maximum wait between retries in seconds (default: 10.0)
        retryable_status_codes: HTTP status codes to retry (default: 429, 500, 502, 503, 504)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 10.0,
        retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504),
    ) -> None:
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.retryable_status_codes = retryable_status_codes

    def _is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable."""
        # Check for httpx status errors
        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            return error.response.status_code in self.retryable_status_codes

        # Check for timeout errors
        error_name = type(error).__name__.lower()
        if "timeout" in error_name:
            return True

        # Check for connection errors
        if "connection" in error_name:
            return True

        return False

    def _calculate_wait(self, attempt: int) -> float:
        """Calculate wait time with exponential backoff and jitter."""
        wait = self.min_wait * (2**attempt)
        wait = min(wait, self.max_wait)
        # Add jitter (±25%) to avoid thundering herd
        jitter = wait * 0.25 * (2 * random.random() - 1)
        return float(max(self.min_wait, wait + jitter))

    async def process(
        self, context: ChatContext, next: Callable[[ChatContext], Awaitable[None]]
    ) -> None:
        """Process the chat request with retry logic."""
        last_error: Exception | None = None

        for attempt in range(self.max_attempts):
            try:
                await next(context)
                return  # Success - exit retry loop

            except Exception as e:
                last_error = e

                if not self._is_retryable(e):
                    logger.warning(
                        "Non-retryable error",
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    raise  # Don't retry non-retryable errors

                if attempt < self.max_attempts - 1:
                    wait_time = self._calculate_wait(attempt)
                    logger.info(
                        "Retrying after error",
                        attempt=attempt + 1,
                        max_attempts=self.max_attempts,
                        wait_seconds=wait_time,
                        error=str(e),
                    )
                    await asyncio.sleep(wait_time)

        # All retries exhausted
        logger.error(
            "All retry attempts failed",
            max_attempts=self.max_attempts,
            last_error=str(last_error),
        )
        if last_error:
            raise last_error
