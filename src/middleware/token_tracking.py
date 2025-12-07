"""Token tracking middleware for monitoring API usage."""

from collections.abc import Awaitable, Callable

import structlog
from agent_framework._middleware import ChatContext, ChatMiddleware

logger = structlog.get_logger()


class TokenTrackingMiddleware(ChatMiddleware):
    """Tracks token usage across chat requests.

    This middleware logs token usage after each chat completion
    and maintains running totals for the session.

    Usage metrics are logged via structlog for observability.
    """

    def __init__(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0

    async def process(
        self, context: ChatContext, next: Callable[[ChatContext], Awaitable[None]]
    ) -> None:
        """Process request and track token usage."""
        await next(context)

        # Extract usage from response if available
        if context.result is None:
            return

        usage = None

        # Try to get usage from response
        if hasattr(context.result, "usage"):
            usage = context.result.usage
        elif hasattr(context.result, "messages") and context.result.messages:
            # Check first message for usage metadata
            msg = context.result.messages[0]
            if hasattr(msg, "metadata") and msg.metadata:
                usage = msg.metadata.get("usage")

        if usage:
            input_tokens = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
            output_tokens = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)

            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.request_count += 1

            logger.info(
                "Token usage",
                request_input=input_tokens,
                request_output=output_tokens,
                total_input=self.total_input_tokens,
                total_output=self.total_output_tokens,
                total_requests=self.request_count,
            )

    def get_stats(self) -> dict[str, int]:
        """Get cumulative token usage statistics.

        Returns:
            Dictionary with total_input, total_output, and request_count.
        """
        return {
            "total_input": self.total_input_tokens,
            "total_output": self.total_output_tokens,
            "request_count": self.request_count,
        }
