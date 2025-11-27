"""Retrieval agent for context preparation."""

from collections.abc import AsyncIterable
from typing import Any

from agent_framework import (
    AgentRunResponse,
    AgentRunResponseUpdate,
    AgentThread,
    BaseAgent,
    ChatMessage,
    Role,
)

from src.state import get_magentic_state


class RetrievalAgent(BaseAgent):  # type: ignore[misc]
    """Agent that retrieves and organizes context from the shared state."""

    def __init__(self, name: str = "RetrievalAgent") -> None:
        super().__init__(
            name=name,
            description="Retrieves relevant context from shared state.",
        )

    async def run(
        self,
        messages: str | ChatMessage | list[str] | list[ChatMessage] | None = None,
        *,
        thread: AgentThread | None = None,
        **kwargs: Any,
    ) -> AgentRunResponse:
        """Retrieve context."""
        state = get_magentic_state()

        # Summarize evidence
        if not state.evidence:
             return AgentRunResponse(
                messages=[ChatMessage(role=Role.ASSISTANT, text="No evidence in context.")],
                response_id="retrieval-empty",
            )

        summary = [f"**Current Context Summary ({len(state.evidence)} items)**\n"]
        for i, ev in enumerate(state.evidence, 1):
             summary.append(f"{i}. **{ev.citation.title}**")
             summary.append(f"   Source: {ev.citation.source} | Date: {ev.citation.date}")
             summary.append(f"   Summary: {ev.content[:200]}...")
             summary.append("")

        return AgentRunResponse(
            messages=[ChatMessage(role=Role.ASSISTANT, text="\n".join(summary))],
            response_id="retrieval-success",
        )

    async def run_stream(
        self,
        messages: str | ChatMessage | list[str] | list[ChatMessage] | None = None,
        *,
        thread: AgentThread | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentRunResponseUpdate]:
        """Streaming wrapper."""
        result = await self.run(messages, thread=thread, **kwargs)
        yield AgentRunResponseUpdate(messages=result.messages, response_id=result.response_id)
