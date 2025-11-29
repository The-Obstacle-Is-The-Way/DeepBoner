# P0 Bug Report: Gradio Example Caching Crash

## Status
- **Date:** 2025-11-29
- **Priority:** P0 CRITICAL (Production Down)
- **Component:** `src/app.py:131`
- **Environment:** HuggingFace Spaces (Python 3.11, Gradio)

## Error Message

```text
AttributeError: 'NoneType' object has no attribute 'strip'
```

## Full Stack Trace

```text
File "/app/src/app.py", line 131, in research_agent
    user_api_key = (api_key.strip() or api_key_state.strip()) or None
                    ^^^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'
```

## Root Cause Analysis

### The Trigger
Gradio's example caching mechanism runs the `research_agent` function during startup to pre-cache example outputs. This happens at:

```text
File "/usr/local/lib/python3.11/site-packages/gradio/helpers.py", line 509, in _start_caching
    await self.cache()
```

### The Problem
Our examples only provide values for 2 of the 4 function parameters:

```python
examples=[
    ["What is the evidence for testosterone therapy in women with HSDD?", "simple"],
    ["Promising drug candidates for endometriosis pain management", "simple"],
]
```

These map to `[message, mode]` but **NOT** to `api_key` or `api_key_state`.

When Gradio runs the function for caching, it passes `None` for the unprovided parameters:

```python
async def research_agent(
    message: str,           # ✅ Provided by example
    history: list[...],     # ✅ Empty list default
    mode: str = "simple",   # ✅ Provided by example
    api_key: str = "",      # ❌ Becomes None during caching!
    api_key_state: str = "" # ❌ Becomes None during caching!
) -> AsyncGenerator[...]:
```

### The Crash
Line 131 attempts to call `.strip()` on `None`:

```python
user_api_key = (api_key.strip() or api_key_state.strip()) or None
#               ^^^^^^^^^^^^^
#               NoneType has no attribute 'strip'
```

## Gradio Warning (Ignored)

Gradio actually warned us about this:

```text
UserWarning: Examples will be cached but not all input components have
example values. This may result in an exception being thrown by your function.
```

## Solution

### Option A: Defensive None Handling (Recommended)
Add None guards before calling `.strip()`:

```python
# Handle None values from Gradio example caching
api_key_str = api_key or ""
api_key_state_str = api_key_state or ""
user_api_key = (api_key_str.strip() or api_key_state_str.strip()) or None
```

### Option B: Disable Example Caching
Set `cache_examples=False` in ChatInterface:

```python
gr.ChatInterface(
    fn=research_agent,
    examples=[...],
    cache_examples=False,  # Disable caching
)
```

This avoids the crash but loses the UX benefit of pre-cached examples.

### Option C: Provide Full Example Values
Include all 4 columns in examples:

```python
examples=[
    ["What is the evidence...", "simple", "", ""],  # [msg, mode, api_key, state]
]
```

This is verbose and exposes internal state to users.

## Recommendation

**Option A** is the cleanest fix. It:
1. Maintains cached examples for fast UX
2. Handles edge cases defensively
3. Doesn't expose internal state in examples

## Pre-Merge Checklist

- [ ] Fix applied to `src/app.py`
- [ ] Unit test added for None parameter handling
- [ ] `make check` passes
- [ ] Test locally with `uv run python -m src.app`
- [ ] Verify example caching works without crash
- [ ] Deploy to HuggingFace Spaces
- [ ] Verify Space starts without error

## Lessons Learned

1. Always test Gradio apps with example caching enabled locally before deploying
2. Gradio's "partial examples" feature passes `None` for missing columns
3. Default parameter values (`str = ""`) are ignored when Gradio explicitly passes `None`
4. The Gradio warning about missing example values should be treated as an error
