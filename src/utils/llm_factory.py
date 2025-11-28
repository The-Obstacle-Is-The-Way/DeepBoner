"""Centralized LLM client factory.

This module provides factory functions for creating LLM clients,
ensuring consistent configuration and clear error messages.

Agent-Framework Chat Clients:
- HuggingFace InferenceClient: Native function calling support via 'tools' parameter
- OpenAI ChatClient: Native function calling support (original implementation)
- Both can be used with agent-framework's ChatAgent

Pydantic AI Models:
- Default provider is HuggingFace (free tier, no API key required for public models)
- OpenAI and Anthropic are available as fallback options
- All providers use Pydantic AI's unified interface
"""

from typing import TYPE_CHECKING, Any

from src.utils.config import settings
from src.utils.exceptions import ConfigurationError

if TYPE_CHECKING:
    from agent_framework.openai import OpenAIChatClient

    from src.utils.huggingface_chat_client import HuggingFaceChatClient


def get_magentic_client() -> "OpenAIChatClient":
    """
    Get the OpenAI client for Magentic agents (legacy function).

    Note: This function is kept for backward compatibility.
    For new code, use get_chat_client_for_agent() which supports
    both OpenAI and HuggingFace.

    Raises:
        ConfigurationError: If OPENAI_API_KEY is not set

    Returns:
        Configured OpenAIChatClient for Magentic agents
    """
    # Import here to avoid requiring agent-framework for simple mode
    from agent_framework.openai import OpenAIChatClient

    api_key = settings.get_openai_api_key()

    return OpenAIChatClient(
        model_id=settings.openai_model,
        api_key=api_key,
    )


def get_huggingface_chat_client() -> "HuggingFaceChatClient":
    """
    Get HuggingFace chat client for agent-framework.

    HuggingFace InferenceClient natively supports function calling,
    making it compatible with agent-framework's ChatAgent.

    Returns:
        Configured HuggingFaceChatClient

    Raises:
        ConfigurationError: If initialization fails
    """
    from src.utils.huggingface_chat_client import HuggingFaceChatClient

    model_name = settings.huggingface_model or "meta-llama/Llama-3.1-8B-Instruct"
    api_key = settings.hf_token or settings.huggingface_api_key

    return HuggingFaceChatClient(
        model_name=model_name,
        api_key=api_key,
        provider="auto",  # Auto-select best provider
    )


def get_chat_client_for_agent() -> Any:
    """
    Get appropriate chat client for agent-framework based on configuration.

    Supports:
    - HuggingFace InferenceClient (if HF_TOKEN available, preferred for free tier)
    - OpenAI ChatClient (if OPENAI_API_KEY available, fallback)

    Returns:
        ChatClient compatible with agent-framework (HuggingFaceChatClient or OpenAIChatClient)

    Raises:
        ConfigurationError: If no suitable client can be created
    """
    # Prefer HuggingFace if available (free tier)
    if settings.has_huggingface_key:
        return get_huggingface_chat_client()

    # Fallback to OpenAI if available
    if settings.has_openai_key:
        return get_magentic_client()

    # If neither available, try HuggingFace without key (public models)
    try:
        return get_huggingface_chat_client()
    except Exception:
        pass

    raise ConfigurationError(
        "No chat client available. Set HF_TOKEN or OPENAI_API_KEY for agent-framework mode."
    )


def get_pydantic_ai_model() -> Any:
    """
    Get the appropriate model for pydantic-ai based on configuration.

    Uses the configured LLM_PROVIDER to select between HuggingFace, OpenAI, and Anthropic.
    Defaults to HuggingFace if provider is not specified or unknown.
    This is used by simple mode components (JudgeHandler, etc.)

    Returns:
        Configured pydantic-ai model
    """
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.models.huggingface import HuggingFaceModel
    from pydantic_ai.models.openai import OpenAIChatModel as OpenAIModel
    from pydantic_ai.providers.anthropic import AnthropicProvider
    from pydantic_ai.providers.huggingface import HuggingFaceProvider
    from pydantic_ai.providers.openai import OpenAIProvider

    if settings.llm_provider == "huggingface":
        model_name = settings.huggingface_model or "meta-llama/Llama-3.1-8B-Instruct"
        hf_provider = HuggingFaceProvider(api_key=settings.hf_token)
        return HuggingFaceModel(model_name, provider=hf_provider)

    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY not set for pydantic-ai")
        provider = OpenAIProvider(api_key=settings.openai_api_key)
        return OpenAIModel(settings.openai_model, provider=provider)

    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ConfigurationError("ANTHROPIC_API_KEY not set for pydantic-ai")
        anthropic_provider = AnthropicProvider(api_key=settings.anthropic_api_key)
        return AnthropicModel(settings.anthropic_model, provider=anthropic_provider)

    # Default to HuggingFace if provider is unknown or not specified
    model_name = settings.huggingface_model or "meta-llama/Llama-3.1-8B-Instruct"
    hf_provider = HuggingFaceProvider(api_key=settings.hf_token)
    return HuggingFaceModel(model_name, provider=hf_provider)


def check_magentic_requirements() -> None:
    """
    Check if Magentic/agent-framework mode requirements are met.

    Note: HuggingFace InferenceClient now supports function calling natively,
    so this check is relaxed. We prefer HuggingFace if available, fallback to OpenAI.

    Raises:
        ConfigurationError: If no suitable client can be created
    """
    # Try to get a chat client - will raise if none available
    try:
        get_chat_client_for_agent()
    except ConfigurationError as e:
        raise ConfigurationError(
            "Agent-framework mode requires HF_TOKEN or OPENAI_API_KEY. "
            "HuggingFace is preferred (free tier with function calling support). "
            "Use mode='simple' for other LLM providers."
        ) from e


def check_simple_mode_requirements() -> None:
    """
    Check if simple mode requirements are met.

    Simple mode supports HuggingFace (default), OpenAI, and Anthropic.
    HuggingFace can work without an API key for public models.

    Raises:
        ConfigurationError: If no LLM is available (only if explicitly required)
    """
    # HuggingFace can work without API key for public models, so we don't require it
    # This allows simple mode to work out of the box
    pass
