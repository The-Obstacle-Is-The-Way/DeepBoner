from unittest.mock import AsyncMock, MagicMock

import pytest

from src.middleware.token_tracking import TokenTrackingMiddleware

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_token_tracking_middleware_counts_tokens():
    """TokenTrackingMiddleware should count tokens from response."""
    middleware = TokenTrackingMiddleware()
    context = MagicMock()

    # Mock response with usage
    context.result.usage = {"input_tokens": 10, "output_tokens": 20}

    next_fn = AsyncMock()

    await middleware.process(context, next_fn)

    assert middleware.total_input_tokens == 10
    assert middleware.total_output_tokens == 20
    assert middleware.request_count == 1


@pytest.mark.asyncio
async def test_token_tracking_middleware_handles_no_usage():
    """TokenTrackingMiddleware should handle response without usage gracefully."""
    middleware = TokenTrackingMiddleware()
    context = MagicMock()
    context.result = MagicMock()
    del context.result.usage  # Ensure usage attr doesn't exist
    context.result.messages = []  # Ensure no messages

    next_fn = AsyncMock()

    await middleware.process(context, next_fn)

    assert middleware.total_input_tokens == 0
    assert middleware.total_output_tokens == 0
    assert middleware.request_count == 0
