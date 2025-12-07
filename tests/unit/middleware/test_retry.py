from unittest.mock import AsyncMock, MagicMock

import pytest

from src.middleware.retry import RetryMiddleware


@pytest.mark.asyncio
async def test_retry_middleware_succeeds_first_try():
    """RetryMiddleware should pass through on success."""
    middleware = RetryMiddleware(max_attempts=3)
    context = MagicMock()
    next_fn = AsyncMock()

    await middleware.process(context, next_fn)

    next_fn.assert_called_once_with(context)


@pytest.mark.asyncio
async def test_retry_middleware_retries_on_429():
    """RetryMiddleware should retry on 429 rate limit."""
    middleware = RetryMiddleware(max_attempts=3, min_wait=0.01)
    context = MagicMock()

    # First two calls fail with 429, third succeeds
    call_count = 0

    async def mock_next(ctx):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            error = Exception("Rate limited")
            error.response = MagicMock(status_code=429)
            raise error

    await middleware.process(context, mock_next)
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_middleware_raises_after_max_attempts():
    """RetryMiddleware should raise after max attempts exhausted."""
    middleware = RetryMiddleware(max_attempts=2, min_wait=0.01)
    context = MagicMock()

    async def always_fails(ctx):
        error = Exception("Always fails")
        error.response = MagicMock(status_code=500)
        raise error

    with pytest.raises(Exception, match="Always fails"):
        await middleware.process(context, always_fails)
