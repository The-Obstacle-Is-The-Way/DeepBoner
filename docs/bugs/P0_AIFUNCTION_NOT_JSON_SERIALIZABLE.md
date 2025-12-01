# P0 Bug: AIFunction Not JSON Serializable (Free Tier Broken)

**Severity**: P0 (Critical) - Free Tier cannot perform research
**Status**: Open
**Discovered**: 2025-12-01
**Reporter**: Production user via HuggingFace Spaces

## Symptom

Every search round fails with:
```
📚 SEARCH_COMPLETE: searcher: Agent searcher: Error processing request -
Object of type AIFunction is not JSON serializable
```

Research never completes. Users see 5 rounds of the same error.

## Root Cause

### The Problem

In `src/clients/huggingface.py` lines 82-103:

```python
# Extract tool configuration
tools = chat_options.tools if chat_options.tools else None  # AIFunction objects!
...
call_fn = partial(
    self._client.chat_completion,
    messages=hf_messages,
    tools=tools,  # <-- RAW AIFunction objects passed here
    ...
)
```

The `chat_options.tools` contains `AIFunction` objects from Microsoft's agent-framework.
When `requests` tries to serialize these for the HTTP request, it fails:
```
TypeError: Object of type AIFunction is not JSON serializable
```

### Why This Happens

1. Microsoft's agent-framework defines tools as `AIFunction` objects
2. `ChatAgent` with tools passes them via `chat_options.tools`
3. Our `HuggingFaceChatClient` forwards them directly to `InferenceClient.chat_completion()`
4. `requests.post()` internally calls `json.dumps()` on the request body
5. `AIFunction` has no `__json__()` method or isn't a dict → TypeError

### The Warning We Ignored

The agent framework already warned us:
```
[WARNING] The provided chat client does not support function invoking,
this might limit agent capabilities.
```

## Impact

| Component | Impact |
|-----------|--------|
| Free Tier (HuggingFace) | **COMPLETELY BROKEN** |
| Advanced Mode without API key | **Cannot do research** |
| Paid Tier (OpenAI) | Unaffected (OpenAI handles AIFunction) |

## Proposed Solutions

### Option 1: Disable Tools for HuggingFace (QUICK FIX)

Pass `tools=None` to disable function calling entirely:

```python
# src/clients/huggingface.py

async def _inner_get_response(self, ...):
    hf_messages = self._convert_messages(messages)

    # QUICK FIX: Disable tools - HuggingFace free tier doesn't reliably support them
    # The agents will use natural language instructions instead
    tools = None  # Was: chat_options.tools if chat_options.tools else None
    hf_tool_choice = None
    ...
```

**Pros**:
- 5-minute fix
- No serialization errors
- Agents still work via natural language instructions

**Cons**:
- Agents can't use structured tool calls
- Less precise than function calling
- Qwen2.5-72B DOES support function calling (we're not using it)

### Option 2: Convert AIFunction to JSON Schema (PROPER FIX)

Serialize `AIFunction` objects to OpenAI-compatible tool format:

```python
def _convert_tools(self, tools: list[Any] | None) -> list[dict[str, Any]] | None:
    """Convert AIFunction objects to JSON-serializable tool definitions."""
    if not tools:
        return None

    json_tools = []
    for tool in tools:
        if hasattr(tool, 'to_dict'):
            # AIFunction.to_dict() returns JSON-serializable dict
            json_tools.append(tool.to_dict())
        elif hasattr(tool, 'schema'):
            # Alternative: use schema property
            json_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.schema,
                }
            })
        else:
            # Fallback: skip unknown tool types
            logger.warning(f"Skipping non-serializable tool: {type(tool)}")

    return json_tools if json_tools else None
```

**Pros**:
- Proper function calling with Qwen2.5
- Structured tool invocation
- Better agent capabilities

**Cons**:
- More complex
- Need to handle tool call responses
- May require testing with different HF models

### Option 3: Hybrid Approach (RECOMMENDED)

Try to convert tools, fall back to None if it fails:

```python
def _convert_tools(self, tools: list[Any] | None) -> list[dict[str, Any]] | None:
    """Attempt to convert tools to JSON, disable if conversion fails."""
    if not tools:
        return None

    try:
        json_tools = []
        for tool in tools:
            if hasattr(tool, 'to_dict'):
                json_tools.append(tool.to_dict())
            elif isinstance(tool, dict):
                json_tools.append(tool)
        return json_tools if json_tools else None
    except Exception as e:
        logger.warning(f"Tool conversion failed, disabling function calling: {e}")
        return None
```

## Recommended Fix

**Immediate (P0)**: Option 1 - Disable tools with `tools=None`
**Follow-up**: Option 3 - Implement proper conversion with fallback

## Call Stack Trace

```
User Query (HuggingFace Spaces)
    ↓
src/app.py:research_agent()
    ↓
src/orchestrators/advanced.py:AdvancedOrchestrator.run()
    ↓
agent_framework.MagenticBuilder.run_stream()
    ↓
agent_framework.ChatAgent (SearchAgent with tools=[search_pubmed, ...])
    ↓
src/clients/huggingface.py:HuggingFaceChatClient._inner_get_response()
    → chat_options.tools contains AIFunction objects
    ↓
huggingface_hub.InferenceClient.chat_completion(tools=tools)
    ↓
requests.post(json={..., "tools": [AIFunction, ...]})
    ↓
json.dumps() → TypeError: Object of type AIFunction is not JSON serializable
```

## Testing

```bash
# Reproduce locally (remove OpenAI key)
unset OPENAI_API_KEY
uv run python -c "
import asyncio
from src.orchestrators.advanced import AdvancedOrchestrator

async def test():
    orch = AdvancedOrchestrator(max_rounds=2)
    async for event in orch.run('testosterone benefits'):
        print(f'[{event.type}] {event.message[:50]}...')

asyncio.run(test())
"

# Expected: TypeError: Object of type AIFunction is not JSON serializable
# After fix: Should complete without serialization errors
```

## References

- [Microsoft Agent Framework - AIFunction](https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.aifunction)
- [HuggingFace Chat Completion API](https://huggingface.co/docs/api-inference/en/tasks/chat-completion)
- [Qwen Function Calling](https://qwen.readthedocs.io/en/latest/framework/function_call.html)
- [huggingface_hub chat_completion](https://github.com/huggingface/huggingface_hub/releases/tag/v0.22.0)
