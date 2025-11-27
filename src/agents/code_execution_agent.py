"""Code execution agent using Modal."""

import re
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

from src.tools.code_execution import get_code_executor


class CodeExecutorAgent(BaseAgent):  # type: ignore[misc]
    """Agent that can execute arbitrary Python code in a secure Modal sandbox."""

    def __init__(self, name: str = "CodeExecutorAgent") -> None:
        super().__init__(
            name=name,
            description="Executes Python code in a secure Modal sandbox.",
        )
        self._executor = get_code_executor()

    async def run(
        self,
        messages: str | ChatMessage | list[str] | list[ChatMessage] | None = None,
        *,
        thread: AgentThread | None = None,
        **kwargs: Any,
    ) -> AgentRunResponse:
        """Execute the code found in the message."""
        text = self._extract_text(messages)
        code = self._extract_code_block(text)

        if not code:
            # If no code block, assume the entire text is code if it looks like code?
            # Or just complain.
            return AgentRunResponse(
                messages=[
                    ChatMessage(
                        role=Role.ASSISTANT,
                        text="No Python code block found. Please wrap code in ```python ... ```.",
                    )
                ],
                response_id="execution-failed",
            )

        try:
            # Execute in Modal
            result = self._executor.execute(code, timeout=120)

            output_parts = [f"**Execution {'Success' if result['success'] else 'Failed'}**\n"]

            if result["stdout"]:
                output_parts.append(f"Stdout:\n```\n{result['stdout']}\n```")

            if result["stderr"]:
                output_parts.append(f"Stderr:\n```\n{result['stderr']}\n```")

            if result["error"]:
                output_parts.append(f"Error:\n{result['error']}")

            response_text = "\n\n".join(output_parts)

            return AgentRunResponse(
                messages=[ChatMessage(role=Role.ASSISTANT, text=response_text)],
                response_id=f"execution-{'success' if result['success'] else 'failed'}",
                additional_properties={"execution_result": result},
            )

        except Exception as e:
            return AgentRunResponse(
                messages=[ChatMessage(role=Role.ASSISTANT, text=f"**System Error**: {e!s}")],
                response_id="execution-system-error",
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

    def _extract_text(
        self,
        messages: str | ChatMessage | list[str] | list[ChatMessage] | None,
    ) -> str:
        """Extract text from messages."""
        if isinstance(messages, str):
            return messages
        elif isinstance(messages, ChatMessage):
            return messages.text or ""
        elif isinstance(messages, list):
            for msg in reversed(messages):
                if isinstance(msg, ChatMessage) and msg.role == Role.USER:
                    return msg.text or ""
                elif isinstance(msg, str):
                    return msg
        return ""

    def _extract_code_block(self, text: str) -> str | None:
        """Extract code from markdown code blocks."""
        # Look for python code blocks
        match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1)

        # Look for generic code blocks
        match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1)

        return None
