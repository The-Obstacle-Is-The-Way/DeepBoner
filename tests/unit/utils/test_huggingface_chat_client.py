"""Unit tests for HuggingFaceChatClient."""

from unittest.mock import MagicMock, patch

import pytest

from src.utils.exceptions import ConfigurationError
from src.utils.huggingface_chat_client import HuggingFaceChatClient


@pytest.mark.unit
class TestHuggingFaceChatClient:
    """Unit tests for HuggingFaceChatClient."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        with patch("src.utils.huggingface_chat_client.InferenceClient") as mock_client:
            client = HuggingFaceChatClient()
            assert client.model_name == "meta-llama/Llama-3.1-8B-Instruct"
            assert client.provider == "auto"
            mock_client.assert_called_once_with(
                model="meta-llama/Llama-3.1-8B-Instruct",
                api_key=None,
                provider="auto",
            )

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        with patch("src.utils.huggingface_chat_client.InferenceClient") as mock_client:
            client = HuggingFaceChatClient(
                model_name="meta-llama/Llama-3.1-70B-Instruct",
                api_key="hf_test_token",
                provider="together",
            )
            assert client.model_name == "meta-llama/Llama-3.1-70B-Instruct"
            assert client.provider == "together"
            mock_client.assert_called_once_with(
                model="meta-llama/Llama-3.1-70B-Instruct",
                api_key="hf_test_token",
                provider="together",
            )

    def test_init_failure(self):
        """Test initialization failure handling."""
        with patch(
            "src.utils.huggingface_chat_client.InferenceClient",
            side_effect=Exception("Connection failed"),
        ):
            with pytest.raises(ConfigurationError, match="Failed to initialize"):
                HuggingFaceChatClient()

    @pytest.mark.asyncio
    async def test_chat_completion_basic(self):
        """Test basic chat completion without tools."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    role="assistant",
                    content="Hello! How can I help you?",
                    tool_calls=None,
                ),
            ),
        ]

        with patch("src.utils.huggingface_chat_client.InferenceClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = HuggingFaceChatClient()
            messages = [{"role": "user", "content": "Hello"}]

            # Mock run_in_executor to call the lambda directly
            async def mock_run_in_executor(executor, func, *args):
                return func()

            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = mock_run_in_executor

                response = await client.chat_completion(messages=messages)

                assert response == mock_response
                mock_client.chat_completion.assert_called_once_with(
                    messages=messages,
                    tools=None,
                    tool_choice=None,
                    temperature=None,
                    max_tokens=None,
                )

    @pytest.mark.asyncio
    async def test_chat_completion_with_tools(self):
        """Test chat completion with function calling tools."""
        mock_tool_call = MagicMock()
        mock_tool_call.function.name = "search_pubmed"
        mock_tool_call.function.arguments = '{"query": "metformin", "max_results": 10}'

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    role="assistant",
                    content=None,
                    tool_calls=[mock_tool_call],
                ),
            ),
        ]

        with patch("src.utils.huggingface_chat_client.InferenceClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = HuggingFaceChatClient()
            messages = [{"role": "user", "content": "Search for metformin"}]
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "search_pubmed",
                        "description": "Search PubMed",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                                "max_results": {"type": "integer"},
                            },
                        },
                    },
                },
            ]

            # Mock run_in_executor to call the lambda directly
            async def mock_run_in_executor(executor, func, *args):
                return func()

            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = mock_run_in_executor

                response = await client.chat_completion(
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.3,
                    max_tokens=500,
                )

                assert response == mock_response
                mock_client.chat_completion.assert_called_once_with(
                    messages=messages,
                    tools=tools,  # ✅ Native support!
                    tool_choice="auto",
                    temperature=0.3,
                    max_tokens=500,
                )

    @pytest.mark.asyncio
    async def test_chat_completion_error_handling(self):
        """Test error handling in chat completion."""
        with patch("src.utils.huggingface_chat_client.InferenceClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat_completion.side_effect = Exception("API error")
            mock_client_class.return_value = mock_client

            client = HuggingFaceChatClient()
            messages = [{"role": "user", "content": "Hello"}]

            # Mock run_in_executor to propagate the exception
            async def mock_run_in_executor(executor, func, *args):
                return func()

            with patch("asyncio.get_running_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = mock_run_in_executor

                with pytest.raises(ConfigurationError, match="HuggingFace chat completion failed"):
                    await client.chat_completion(messages=messages)
