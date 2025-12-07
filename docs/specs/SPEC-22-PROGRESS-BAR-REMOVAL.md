# SPEC-22: Progress Bar Removal

**Status:** IMPLEMENTED
**Priority:** P3 (Cosmetic UX fix)
**Effort:** 15 minutes
**PR Scope:** Single file fix

---

## Problem Statement

The `gr.Progress()` bar conflicts with Gradio's `ChatInterface`, causing visual glitches:
- Progress bar "floats" in the middle of chat output
- Text overlaps with progress bar
- Looks unprofessional

**Root Cause:** `gr.Progress()` is designed for `gr.Interface`, not `ChatInterface`. It's a known Gradio limitation.

---

## Current Code (BROKEN)

```python
# src/app.py - research_agent function
async def research_agent(
    message: str,
    history: list[dict[str, Any]],
    domain: str = "sexual_health",
    api_key: str = "",
    api_key_state: str = "",
    progress: gr.Progress = gr.Progress(),  # ← PROBLEM: Causes visual glitches
) -> AsyncGenerator[str, None]:
    ...
    if event.type == "started":
        progress(0, desc="Starting research...")  # ← These cause overlap
    elif event.type == "progress":
        progress(p, desc=event.message)
```

---

## Required Fix

Remove `gr.Progress()` entirely. We already have emoji status messages in chat output.

```python
# src/app.py - Fixed version
async def research_agent(
    message: str,
    history: list[dict[str, Any]],
    domain: str = "sexual_health",
    api_key: str = "",
    api_key_state: str = "",
    # REMOVED: progress: gr.Progress = gr.Progress(),
) -> AsyncGenerator[str, None]:
    ...
    # REMOVED: All progress(...) calls

    # KEEP: Emoji status messages are already being yielded
    # These work great with ChatInterface:
    # yield "⏱️ **PROGRESS**: Round 1/5 (~3m 0s remaining)"
```

---

## Implementation Checklist

- [x] Open `src/app.py`
- [x] Remove `progress: gr.Progress = gr.Progress()` from `research_agent` signature
- [x] Remove all `progress(...)` calls inside `research_agent`
- [x] Verify emoji status yields are still present (they should be)
- [x] Run `uv run python -c "from src.app import create_demo; print('OK')"`
- [x] Run `make check` (lint passes; pre-existing mypy issues unrelated to this change)
- [ ] Test locally: `uv run python src/app.py` and verify no floating progress bar

---

## What We Keep

The emoji status messages in chat output:

```
⏱️ **PROGRESS**: Round 1/5 (~3m 0s remaining)
🔬 **Step 2: SearchAgent** - Searching for evidence...
✅ **COMPLETE**: Research finished in 45 seconds
```

These are yielded directly to chat and work perfectly with `ChatInterface`.

---

## Acceptance Criteria

1. No `gr.Progress()` in `research_agent` function signature
2. No `progress(...)` calls in `research_agent` function body
3. Emoji status messages still appear in chat output
4. No floating/overlapping progress bar in UI
5. `make check` passes

---

## Dependencies

None. This is a standalone cosmetic fix.

---

## Testing

```bash
# Start local server
uv run python src/app.py

# In browser:
# 1. Submit a research query
# 2. Verify NO floating progress bar appears
# 3. Verify emoji status messages DO appear in chat
# 4. Verify chat messages don't have visual glitches
```

---

## Notes

- This is the recommended fix from Gradio's own documentation
- `ChatInterface.show_progress="minimal"` (default) still shows a spinner, which is fine
- If we need a real progress bar later, we'd need to refactor to `gr.Blocks` wrapper
