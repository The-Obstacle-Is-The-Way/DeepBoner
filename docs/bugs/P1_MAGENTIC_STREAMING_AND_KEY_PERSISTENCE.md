# Bug Report: Magentic Mode Streaming Spam + API Key Persistence

## Status
- **Date:** 2025-11-29
- **Reporter:** CLI User
- **Priority:** P1 (UX Degradation)
- **Component:** `src/app.py`, `src/orchestrator_magentic.py`

---

## Bug 1: Token-by-Token Streaming Spam

### Symptoms
When running Magentic (Advanced) mode, the UI shows hundreds of individual lines like:
```
📡 STREAMING: Below
📡 STREAMING: is
📡 STREAMING: a
📡 STREAMING: curated
📡 STREAMING: list
...
```

Each token is displayed as a separate streaming event, creating visual spam and making it impossible to read the output until completion.

### Root Cause
**File:** `src/orchestrator_magentic.py:247-254`

```python
elif isinstance(event, MagenticAgentDeltaEvent):
    if event.text:
        return AgentEvent(
            type="streaming",
            message=event.text,  # Single token!
            data={"agent_id": event.agent_id},
            iteration=iteration,
        )
```

Every LLM token emits a `MagenticAgentDeltaEvent`, which creates an `AgentEvent(type="streaming")`.

**File:** `src/app.py:170-180`

```python
async for event in orchestrator.run(message):
    event_md = event.to_markdown()
    response_parts.append(event_md)  # Appends EVERY token

    if event.type == "complete":
        yield event.message
    else:
        yield "\n\n".join(response_parts)  # Yields ALL accumulated tokens
```

For N tokens, this yields N times, each time showing all previous tokens. This is O(N²) string operations and creates massive visual spam.

### Proposed Fix Options

**Option A: Buffer streaming tokens (recommended)**
```python
# In app.py - accumulate streaming tokens, yield periodically
streaming_buffer = ""
last_yield_time = time.time()

async for event in orchestrator.run(message):
    if event.type == "streaming":
        streaming_buffer += event.message
        # Only yield every 500ms or on newline
        if time.time() - last_yield_time > 0.5 or "\n" in event.message:
            yield f"📡 {streaming_buffer}"
            last_yield_time = time.time()
    elif event.type == "complete":
        yield event.message
    else:
        # Non-streaming events
        response_parts.append(event.to_markdown())
        yield "\n\n".join(response_parts)
```

**Option B: Don't yield streaming events at all**
```python
# In app.py - only yield meaningful events
async for event in orchestrator.run(message):
    if event.type == "streaming":
        continue  # Skip token-by-token spam
    # ... rest of logic
```

**Option C: Fix at orchestrator level**
Don't emit `AgentEvent` for every delta - buffer in `_process_event`.

---

## Bug 2: API Key Does Not Persist in Textbox

### Symptoms
1. User opens the "Mode & API Key" accordion
2. User pastes their API key into the password textbox
3. User clicks an example OR clicks elsewhere
4. The API key textbox is now empty - value lost

### Root Cause
**File:** `src/app.py:223-237`

```python
additional_inputs_accordion=additional_inputs_accordion,
additional_inputs=[
    gr.Radio(...),
    gr.Textbox(
        label="🔑 API Key (Optional)",
        type="password",
        # No `value` parameter - defaults to empty
        # No state persistence mechanism
    ),
],
```

Gradio's `ChatInterface` with `additional_inputs` has known issues:
1. Clicking examples resets additional inputs to defaults
2. The accordion state and input values may not persist correctly
3. No explicit state management for the API key

### Proposed Fix Options

**Option A: Use `gr.State` for persistence**
```python
api_key_state = gr.State("")

def research_agent(message, history, mode, api_key, api_key_state):
    # Use api_key_state if api_key is empty
    effective_key = api_key or api_key_state
    ...
    return response, effective_key  # Return to update state
```

**Option B: Use browser localStorage via JavaScript**
```python
demo.load(js="""
    () => {
        const saved = localStorage.getItem('deepboner_api_key');
        if (saved) document.querySelector('input[type=password]').value = saved;
    }
""")
```

**Option C: Environment variable only (remove BYOK textbox)**
Remove the API key input entirely. Require users to set `OPENAI_API_KEY` in HuggingFace Secrets. This is more secure but less user-friendly.

**Option D: Use Gradio LoginButton or HuggingFace OAuth**
Leverage HF's built-in auth and secrets management.

---

## Recommended Priority

1. **Bug 1 (Streaming Spam)**: Fix first - it makes Advanced mode unusable for reading output
2. **Bug 2 (Key Persistence)**: Fix second - annoying but users can re-paste

## Testing Plan

1. Run Advanced mode query, verify no token-by-token spam
2. Paste API key, click example, verify key persists
3. Refresh page, verify key persists (if using localStorage)
4. Run `make check` - all tests pass
