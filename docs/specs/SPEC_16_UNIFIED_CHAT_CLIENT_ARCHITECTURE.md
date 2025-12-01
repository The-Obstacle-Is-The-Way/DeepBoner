# SPEC_16: Unified Chat Client Architecture

**Status**: Proposed
**Priority**: P1 (Architectural Simplification)
**Issue**: Updates [#105](https://github.com/The-Obstacle-Is-The-Way/DeepBoner/issues/105)
**Created**: 2025-12-01

## Summary

Eliminate the Simple Mode / Advanced Mode parallel universe by implementing a pluggable `ChatClient` architecture. This allows the multi-agent framework to work with ANY LLM provider (OpenAI, HuggingFace, Anthropic, etc.) through a single, unified codebase.

## Problem Statement

### Current Architecture: Two Parallel Universes

```
User Query
    │
    ├── Has API Key? ──Yes──→ Advanced Mode (400 lines)
    │                         └── Microsoft Agent Framework
    │                         └── OpenAIChatClient (hardcoded)
    │
    └── No API Key? ──────────→ Simple Mode (761 lines)
                                └── While-loop orchestration
                                └── Pydantic AI + HuggingFace
```

**Problems:**
1. **Double Maintenance**: 1,161 lines across two systems
2. **Feature Drift**: New features must be implemented twice
3. **Bug Duplication**: Same bugs appear in both systems
4. **Testing Burden**: Two test suites, two CI paths
5. **Cognitive Load**: Developers must understand both patterns

### Root Cause Analysis

The issue #105 stated: "Microsoft Agent Framework's OpenAIChatClient only speaks OpenAI API format."

**This is FALSE.** Upon investigation:

```python
# Microsoft Agent Framework provides:
from agent_framework import BaseChatClient, ChatClientProtocol

# Abstract methods to implement:
frozenset({'_inner_get_response', '_inner_get_streaming_response'})
```

The framework IS designed for pluggable clients. We just never implemented alternatives.

## Proposed Solution: ChatClientFactory

### Architecture After Implementation

```
User Query
    │
    └──→ Advanced Mode (unified)
         └── Microsoft Agent Framework
         └── ChatClientFactory:
             ├── OpenAIChatClient (API key present)
             ├── AnthropicChatClient (Anthropic key)
             └── HuggingFaceChatClient (free fallback)
```

### New Files

```
src/
├── clients/
│   ├── __init__.py
│   ├── base.py              # Re-export BaseChatClient
│   ├── factory.py           # ChatClientFactory
│   ├── huggingface.py       # HuggingFaceChatClient (~200 lines)
│   └── anthropic.py         # AnthropicChatClient (~200 lines) [future]
```

### ChatClientFactory Implementation

```python
# src/clients/factory.py
from agent_framework import BaseChatClient
from agent_framework.openai import OpenAIChatClient

from src.utils.config import settings

def get_chat_client(
    provider: str | None = None,
    api_key: str | None = None,
) -> BaseChatClient:
    """
    Factory for creating chat clients.

    Auto-detection priority:
    1. Explicit provider parameter
    2. OpenAI key (highest quality)
    3. Anthropic key
    4. HuggingFace (free fallback)

    Args:
        provider: Force specific provider ("openai", "anthropic", "huggingface")
        api_key: Override API key for the provider

    Returns:
        Configured BaseChatClient instance
    """
    if provider == "openai" or (provider is None and settings.has_openai_key):
        return OpenAIChatClient(
            model_id=settings.openai_model,
            api_key=api_key or settings.openai_api_key,
        )

    if provider == "anthropic" or (provider is None and settings.has_anthropic_key):
        from src.clients.anthropic import AnthropicChatClient
        return AnthropicChatClient(
            model_id=settings.anthropic_model,
            api_key=api_key or settings.anthropic_api_key,
        )

    # Free fallback
    from src.clients.huggingface import HuggingFaceChatClient
    return HuggingFaceChatClient(
        model_id="meta-llama/Llama-3.1-70B-Instruct",
    )
```

### HuggingFaceChatClient Implementation

```python
# src/clients/huggingface.py
from collections.abc import AsyncIterable
from typing import Any

from agent_framework import (
    BaseChatClient,
    ChatMessage,
    ChatResponse,
    ChatResponseUpdate,
    TextContent,
    FunctionCallContent,
)
from huggingface_hub import InferenceClient

class HuggingFaceChatClient(BaseChatClient):
    """
    HuggingFace Inference adapter for Microsoft Agent Framework.

    Enables multi-agent orchestration using free HuggingFace models
    like Llama 3.1 70B Instruct (supports function calling).
    """

    def __init__(
        self,
        model_id: str = "meta-llama/Llama-3.1-70B-Instruct",
        api_key: str | None = None,
    ):
        self._model_id = model_id
        self._client = InferenceClient(model=model_id, token=api_key)

    def service_url(self) -> str:
        return "https://api-inference.huggingface.co"

    async def _inner_get_response(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        """Convert and call HuggingFace, return ChatResponse."""
        # Convert ChatMessage[] to HuggingFace format
        hf_messages = self._convert_messages_to_hf(messages)

        # Handle tools/function calling if present
        tools = kwargs.get("tools")
        hf_tools = self._convert_tools_to_hf(tools) if tools else None

        # Call HuggingFace API
        response = await self._client.chat_completion(
            messages=hf_messages,
            tools=hf_tools,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
        )

        # Convert response back to ChatResponse
        return self._convert_response_from_hf(response)

    async def _inner_get_streaming_response(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> AsyncIterable[ChatResponseUpdate]:
        """Streaming version of response generation."""
        hf_messages = self._convert_messages_to_hf(messages)

        async for chunk in self._client.chat_completion(
            messages=hf_messages,
            stream=True,
            **kwargs,
        ):
            yield self._convert_chunk_from_hf(chunk)

    def _convert_messages_to_hf(self, messages: list[ChatMessage]) -> list[dict]:
        """Convert Agent Framework messages to HuggingFace format."""
        result = []
        for msg in messages:
            hf_msg = {"role": msg.role.value}

            # Extract text content
            if msg.text:
                hf_msg["content"] = str(msg.text)
            elif msg.contents:
                # Handle multi-part content
                hf_msg["content"] = " ".join(
                    str(c.text) for c in msg.contents
                    if hasattr(c, "text")
                )

            # Handle function calls
            if any(isinstance(c, FunctionCallContent) for c in (msg.contents or [])):
                hf_msg["tool_calls"] = [
                    self._convert_function_call(c)
                    for c in msg.contents
                    if isinstance(c, FunctionCallContent)
                ]

            result.append(hf_msg)
        return result

    def _convert_tools_to_hf(self, tools) -> list[dict] | None:
        """Convert Agent Framework tools to HuggingFace format."""
        if not tools:
            return None

        hf_tools = []
        for tool in tools:
            if hasattr(tool, "to_dict"):
                # ToolProtocol objects
                hf_tools.append({
                    "type": "function",
                    "function": tool.to_dict(),
                })
            elif callable(tool):
                # ai_function decorated functions
                hf_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.__name__,
                        "description": tool.__doc__ or "",
                        "parameters": getattr(tool, "__schema__", {}),
                    }
                })
        return hf_tools or None

    def _convert_response_from_hf(self, response) -> ChatResponse:
        """Convert HuggingFace response to ChatResponse."""
        choice = response.choices[0]
        message = choice.message

        contents = []

        # Text content
        if message.content:
            contents.append(TextContent(text=message.content))

        # Function/tool calls
        if message.tool_calls:
            for tc in message.tool_calls:
                contents.append(FunctionCallContent(
                    call_id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments,
                ))

        return ChatResponse(
            text=message.content,
            model_id=self._model_id,
            finish_reason={"type": choice.finish_reason},
        )
```

### Changes to Advanced Orchestrator

```python
# src/orchestrators/advanced.py

# BEFORE (hardcoded):
from agent_framework.openai import OpenAIChatClient

class AdvancedOrchestrator:
    def __init__(self, ...):
        self._chat_client = OpenAIChatClient(...)

# AFTER (factory):
from src.clients.factory import get_chat_client

class AdvancedOrchestrator:
    def __init__(self, chat_client=None, provider=None, api_key=None, ...):
        self._chat_client = chat_client or get_chat_client(
            provider=provider,
            api_key=api_key,
        )
```

## Files to Delete After Implementation

| File | Lines | Reason |
|------|-------|--------|
| `src/orchestrators/simple.py` | 761 | Replaced by unified Advanced Mode |
| `src/tools/search_handler.py` | ~150 | Manager agent handles orchestration |
| `src/agent_factory/judges.py` (JudgeHandler) | ~200 | JudgeAgent replaces this |

**Total deletion: ~1,100 lines**
**Total addition: ~400 lines (new clients)**
**Net: -700 lines, single architecture**

## Migration Plan

### Phase 1: Implement HuggingFaceChatClient
- [ ] Create `src/clients/` package
- [ ] Implement `HuggingFaceChatClient` with function calling
- [ ] Write unit tests for message/tool conversion
- [ ] Test with simple queries (no multi-agent)

### Phase 2: Integrate into Advanced Mode
- [ ] Create `ChatClientFactory`
- [ ] Update `AdvancedOrchestrator` to use factory
- [ ] Update `magentic_agents.py` to accept any `BaseChatClient`
- [ ] Test full multi-agent flow with HuggingFace

### Phase 3: Deprecate Simple Mode
- [ ] Add deprecation warning to Simple Mode
- [ ] Update factory.py to only return AdvancedOrchestrator
- [ ] Update UI to remove mode selection (auto-detect only)
- [ ] Run full regression tests

### Phase 4: Remove Simple Mode
- [ ] Delete `simple.py`
- [ ] Delete `search_handler.py`
- [ ] Remove JudgeHandler classes
- [ ] Archive to `docs/archive/` for reference
- [ ] Update all tests

## Risks and Mitigations

### Risk 1: HuggingFace Rate Limits
**Problem**: Free tier may throttle multi-agent flows (5-10 LLM calls per query)
**Mitigation**:
- Add exponential backoff with retries
- Cache manager decisions where possible
- Consider paid HF Pro ($9/month) for demo

### Risk 2: Function Calling Quality
**Problem**: Llama 3.1 70B function calling may be less reliable than GPT-5
**Mitigation**:
- Add validation/retry on malformed tool calls
- Fall back to text parsing if JSON fails
- Test extensively before removing Simple Mode

### Risk 3: Response Format Differences
**Problem**: HuggingFace responses may have subtle format differences
**Mitigation**:
- Comprehensive conversion functions
- Unit tests covering edge cases
- Integration tests with real API

## Success Criteria

1. **Single Codebase**: No more Simple/Advanced split
2. **Zero API Key Demo**: HuggingFace Spaces works without user API key
3. **Quality Parity**: Free tier produces comparable research reports
4. **Maintainability**: One test suite, one bug tracker, one feature path

## Full Stack Analysis

### Files Requiring Changes (Category 1: Core)

| File | Refs | Change |
|------|------|--------|
| `src/orchestrators/advanced.py` | 8 | `OpenAIChatClient` → `get_chat_client()` |
| `src/agents/magentic_agents.py` | 12 | Type: `OpenAIChatClient` → `BaseChatClient` |
| `src/agents/retrieval_agent.py` | 4 | Same pattern |
| `src/agents/code_executor_agent.py` | 4 | Same pattern |
| `src/utils/llm_factory.py` | 8 | Merge into `clients/factory.py` |

### Files to Delete (Category 2: Simple Mode)

| File | Lines | Reason |
|------|-------|--------|
| `src/orchestrators/simple.py` | 761 | Replaced by unified system |
| `src/agent_factory/judges.py` (handlers) | ~200 | JudgeAgent replaces |
| `src/tools/search_handler.py` | ~150 | Manager agent replaces |

### Files Unchanged (Category 3: Embeddings)

Embedding services are a **separate concern**:
- `src/services/llamaindex_rag.py` - Premium tier (OpenAI embeddings)
- `src/services/embeddings.py` - Free tier (local sentence-transformers)

Both work today. No changes needed.

### Config Toggle (Future Enhancement)

After implementation, providers can be toggled via config:

```bash
# .env
CHAT_PROVIDER=huggingface  # "openai", "anthropic", "huggingface", "auto"
```

Or at runtime:
```python
orchestrator = AdvancedOrchestrator(provider="huggingface")
orchestrator = AdvancedOrchestrator(provider="openai", api_key="sk-...")
```

This enables:
1. **A/B testing** different providers
2. **Cost optimization** (switch to cheaper provider)
3. **Graceful degradation** (fallback chain)
4. **Kill switch** (disable specific provider)

## References

- Microsoft Agent Framework: `agent_framework.BaseChatClient`
- HuggingFace Inference: `huggingface_hub.InferenceClient`
- Llama 3.1 Function Calling: [HuggingFace Docs](https://huggingface.co/docs/transformers/main/chat_templating#tool-use--function-calling)
- Issue #105: Deprecate Simple Mode
