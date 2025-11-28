"""Integration tests for agent-framework with HuggingFace ChatClient.

These tests verify that agent-framework works correctly with HuggingFace
InferenceClient, including function calling support.

Marked with @pytest.mark.huggingface and @pytest.mark.integration.
"""

import os

import pytest

# Skip all tests if agent_framework not installed (optional dep)
pytest.importorskip("agent_framework")

from src.agents.magentic_agents import (
    create_hypothesis_agent,
    create_judge_agent,
    create_report_agent,
    create_search_agent,
)
from src.utils.huggingface_chat_client import HuggingFaceChatClient
from src.utils.llm_factory import get_chat_client_for_agent, get_huggingface_chat_client


@pytest.mark.integration
@pytest.mark.huggingface
class TestHuggingFaceAgentFramework:
    """Integration tests for agent-framework with HuggingFace."""

    @pytest.fixture
    def hf_client(self):
        """Create HuggingFace chat client for testing."""
        api_key = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            pytest.skip("HF_TOKEN required for HuggingFace integration tests")
        return HuggingFaceChatClient(
            model_name="meta-llama/Llama-3.1-8B-Instruct",
            api_key=api_key,
            provider="auto",
        )

    @pytest.mark.asyncio
    async def test_huggingface_chat_client_basic(self, hf_client):
        """Test basic chat completion with HuggingFace client."""
        import asyncio

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, world!' and nothing else."},
        ]

        # Add timeout to prevent hanging
        response = await asyncio.wait_for(
            hf_client.chat_completion(messages=messages, max_tokens=50),
            timeout=60.0,  # 60 second timeout
        )

        assert response is not None
        assert hasattr(response, "choices")
        assert len(response.choices) > 0
        assert response.choices[0].message.role == "assistant"
        assert response.choices[0].message.content is not None
        assert "hello" in response.choices[0].message.content.lower()

    @pytest.mark.asyncio
    async def test_huggingface_chat_client_with_tools(self, hf_client):
        """Test function calling with HuggingFace client."""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Use tools when appropriate.",
            },
            {
                "role": "user",
                "content": "Search PubMed for information about metformin and Alzheimer's disease.",
            },
        ]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_pubmed",
                    "description": "Search PubMed for biomedical research papers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search keywords",
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum results to return",
                                "default": 10,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
        ]

        import asyncio

        # Add timeout to prevent hanging
        response = await asyncio.wait_for(
            hf_client.chat_completion(
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=200,
            ),
            timeout=120.0,  # 120 second timeout for function calling
        )

        assert response is not None
        assert hasattr(response, "choices")
        assert len(response.choices) > 0

        # Check if tool calls are present (may or may not be, depending on model)
        message = response.choices[0].message
        if message.tool_calls:
            # Model decided to use tools
            assert len(message.tool_calls) > 0
            tool_call = message.tool_calls[0]
            assert hasattr(tool_call, "function")
            assert tool_call.function.name == "search_pubmed"

    @pytest.mark.asyncio
    async def test_search_agent_with_huggingface(self, hf_client):
        """Test SearchAgent with HuggingFace client."""
        agent = create_search_agent(chat_client=hf_client)

        # Test that agent is created successfully
        assert agent is not None
        assert agent.name == "SearchAgent"
        assert agent.chat_client == hf_client

    @pytest.mark.asyncio
    async def test_judge_agent_with_huggingface(self, hf_client):
        """Test JudgeAgent with HuggingFace client."""
        agent = create_judge_agent(chat_client=hf_client)

        assert agent is not None
        assert agent.name == "JudgeAgent"
        assert agent.chat_client == hf_client

    @pytest.mark.asyncio
    async def test_hypothesis_agent_with_huggingface(self, hf_client):
        """Test HypothesisAgent with HuggingFace client."""
        agent = create_hypothesis_agent(chat_client=hf_client)

        assert agent is not None
        assert agent.name == "HypothesisAgent"
        assert agent.chat_client == hf_client

    @pytest.mark.asyncio
    async def test_report_agent_with_huggingface(self, hf_client):
        """Test ReportAgent with HuggingFace client."""
        agent = create_report_agent(chat_client=hf_client)

        assert agent is not None
        assert agent.name == "ReportAgent"
        assert agent.chat_client == hf_client
        # ReportAgent should have tools
        assert len(agent.tools) > 0

    @pytest.mark.asyncio
    async def test_get_chat_client_for_agent_prefers_huggingface(self):
        """Test that factory function prefers HuggingFace when available."""
        # This test verifies the factory logic
        # If HF_TOKEN is available, it should return HuggingFace client
        if os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY"):
            client = get_chat_client_for_agent()
            assert isinstance(client, HuggingFaceChatClient)
        else:
            # Skip if no HF token available
            pytest.skip("HF_TOKEN not available for testing")

    @pytest.mark.asyncio
    async def test_get_huggingface_chat_client(self):
        """Test HuggingFace chat client factory function."""
        client = get_huggingface_chat_client()
        assert isinstance(client, HuggingFaceChatClient)
        assert client.model_name is not None
