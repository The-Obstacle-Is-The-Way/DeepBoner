"""Custom ChatClient implementation using HuggingFace InferenceClient.

Uses HuggingFace InferenceClient which natively supports function calling,
making this a thin async wrapper rather than a complex implementation.

Reference: https://huggingface.co/docs/huggingface_hub/package_reference/inference_client
"""

import asyncio
from typing import Any

import structlog
from huggingface_hub import InferenceClient

from src.utils.exceptions import ConfigurationError

logger = structlog.get_logger()


class HuggingFaceChatClient:
    """ChatClient implementation using HuggingFace InferenceClient.

    HuggingFace InferenceClient natively supports function calling via
    the 'tools' parameter, making this a simple async wrapper.

    This client is compatible with agent-framework's ChatAgent interface.
    """

    def __init__(
        self,
        model_name: str = "meta-llama/Llama-3.1-8B-Instruct",
        api_key: str | None = None,
        provider: str = "auto",
    ) -> None:
        """Initialize HuggingFace chat client.

        Args:
            model_name: HuggingFace model identifier (e.g., "meta-llama/Llama-3.1-8B-Instruct")
            api_key: Optional HF_TOKEN for gated models. If None, uses environment token.
            provider: Provider name or "auto" for automatic selection.
                     Options: "auto", "cerebras", "together", "sambanova", etc.

        Raises:
            ConfigurationError: If initialization fails
        """
        try:
            # Type ignore: provider can be str but InferenceClient expects Literal
            # We validate it's a valid provider at runtime
            self.client = InferenceClient(
                model=model_name,
                api_key=api_key,
                provider=provider,  # type: ignore[arg-type]
            )
            self.model_name = model_name
            self.provider = provider
            logger.info(
                "Initialized HuggingFace chat client",
                model=model_name,
                provider=provider,
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to initialize HuggingFace InferenceClient: {e}"
            ) from e

    async def chat_completion(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Any:
        """Send chat completion with optional tools.

        HuggingFace InferenceClient natively supports tools parameter!
        This is just an async wrapper around the synchronous API.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                     Format: [{"role": "user", "content": "Hello"}]
            tools: Optional list of tool definitions in OpenAI format.
                  Format: [{"type": "function", "function": {...}}]
            tool_choice: Tool selection strategy.
                        Options: "auto", "none", or {"type": "function", "function": {"name": "tool_name"}}
            temperature: Sampling temperature (0.0 to 2.0). Defaults to 1.0.
            max_tokens: Maximum tokens in response. Defaults to 100.

        Returns:
            ChatCompletionOutput compatible with agent-framework.
            Has .choices attribute with message and tool_calls.

        Raises:
            ConfigurationError: If chat completion fails
        """
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat_completion(
                    messages=messages,
                    tools=tools,  # type: ignore[arg-type]  # ✅ Native support!
                    tool_choice=tool_choice,  # type: ignore[arg-type]  # ✅ Native support!
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
            )

            logger.debug(
                "Chat completion successful",
                model=self.model_name,
                has_tools=bool(tools),
                has_tool_calls=bool(
                    response.choices[0].message.tool_calls
                    if response.choices and response.choices[0].message.tool_calls
                    else None
                ),
            )

            return response

        except Exception as e:
            logger.error(
                "Chat completion failed",
                model=self.model_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ConfigurationError(f"HuggingFace chat completion failed: {e}") from e
