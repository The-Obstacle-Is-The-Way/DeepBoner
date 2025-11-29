# Bug Report: Magentic Mode Integration Issues

## Status
- **Date:** 2025-11-29
- **Reporter:** CLI User
- **Priority:** P1 (UX Degradation + Deprecation Warnings)
- **Component:** `src/app.py`, `src/orchestrator_magentic.py`, `src/utils/llm_factory.py`
- **Status:** ✅ FIXED (Bug 1 & Bug 2) - 2025-11-29
- **Tests:** 138 passing (136 original + 2 new validation tests)

---

## Bug 1: Token-by-Token Streaming Spam ✅ FIXED

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

### Root Cause (VALIDATED)
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

**File:** `src/app.py:171-192` (BEFORE FIX)

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

### Fix Applied
**File:** `src/app.py:171-197`

Implemented streaming token buffering:
1. Added `streaming_buffer = ""` to accumulate tokens
2. Skip individual streaming events (don't append or yield)
3. Flush buffer only when non-streaming event occurs or at completion
4. Result: One consolidated streaming message instead of N individual ones

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

## Bug 2: API Key Does Not Persist in Textbox ✅ FIXED

### Symptoms
1. User opens the "Mode & API Key" accordion
2. User pastes their API key into the password textbox
3. User clicks an example OR clicks elsewhere
4. The API key textbox is now empty - value lost

### Root Cause (VALIDATED)
**File:** `src/app.py:255-267` (BEFORE FIX)

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

### Fix Applied
**Files Modified:**
1. `src/app.py`
2. `src/utils/llm_factory.py`

**Bug 1 (Streaming Spam):**
- Implemented "smart streaming":
  - Accumulate tokens in `streaming_buffer`
  - Yield updates immediately to show progress (UX improvement)
  - **Crucially**: Do NOT append to the persistent `response_parts` list until the stream segment is complete.
  - This prevents the O(N²) list growth and "new line spam" while keeping the UI responsive.

**Bug 2 (API Key Persistence):**
- **Strategy:** Cleaner Fix (Example List Modification)
  - Instead of complex `gr.State` wiring (which caused context issues), we simply **removed the empty string columns** for `api_key` and `api_key_state` from the `examples` list in `create_demo`.
  - Gradio's behavior is that if an example row has fewer columns than inputs, the remaining inputs (like the API key textbox) are **left unchanged** when the example is clicked.
  - This naturally preserves the user's input without requiring extra state management.
  - The `api_key_state` parameter remains in `research_agent` as a fallback but is largely redundant with this cleaner fix.

**Bug 3 (OpenAIModel Deprecation):** ✅ FIXED
- Replaced all `OpenAIModel` imports with `OpenAIChatModel` in `src/app.py` and `src/utils/llm_factory.py`.

### Test Results
```
uv run pytest tests/ -q
============================= 138 passed in 20.60s =============================
```

**Status:** ✅ All tests passing

### Why This Fix Works

**Bug 1 (Streaming Spam):**
- **Before:** Every token → `append()` to list → `yield` → List grew to size N → O(N²) complexity.
- **After:** Every token → `yield` dynamically constructed string (buffer + history) → List stays size K (number of *events*).
- **Impact:** Smooth streaming, no visual spam, no browser freeze.

**Bug 2 (API Key):**
- **Before:** Example click → Overwrote API Key textbox with `""`.
- **After:** Example click → Updates only `message` and `mode` → API Key textbox untouched.
- **Impact:** User input persists naturally.

### Remaining Work
- **Bug 4 (Asyncio GC errors):** Monitoring only - likely Gradio/HF Spaces issue

