# SPEC-23: Gradio 6.0 Modernization Audit

**Status:** IMPLEMENTED
**Priority:** P3 (Technical alignment)
**Effort:** 30 minutes
**Dependencies:** SPEC-22 (Progress Bar Removal)
**Gradio Version:** 6.0.1 (December 2025)
**Last Verified:** 2025-12-07

---

## Executive Summary

Audit of `src/app.py` against Gradio 6.0.1 best practices. Identifies parameters we should add or update for full alignment with modern Gradio.

---

## Gradio Architecture Clarification

### The Three High-Level Classes

| Class | Purpose | Flexibility | Use Case |
|-------|---------|-------------|----------|
| `gr.Blocks` | Low-level building blocks | Most flexible | Custom layouts, multiple components |
| `gr.Interface` | Input → Output wrapper | Medium | ML models, transformations |
| `gr.ChatInterface` | Chat app wrapper | Opinionated | **Chatbots (what we use)** |

### Inheritance Hierarchy

```
gr.Blocks (base)
    ↑
gr.ChatInterface (inherits from Blocks, adds chat-specific features)
```

**Key insight:** `ChatInterface` IS a `Blocks` context internally. We're not mixing different things - we're using the right abstraction for a chat app.

### What ChatInterface Gives Us (For Free)

- Chat history state management
- Submit/Stop buttons
- Streaming support
- Example handling
- `additional_inputs` accordion
- MCP server support (`mcp_server=True`)

### When Would We Need Pure `gr.Blocks`?

Only if we needed:
- Multiple independent chat windows
- Complex multi-panel layouts
- Non-chat components as primary UI

**Verdict:** `ChatInterface` is the correct choice for DeepBoner.

---

## Current State vs Best Practices

| Feature | Current | Best Practice | Action |
|---------|---------|---------------|--------|
| Message format | N/A | OpenAI-style dicts | ✅ **DEFAULT** - Gradio 6.0.1 uses messages format by default |
| `fill_height` | ~~Not set~~ | `fill_height=True` | ✅ **DONE** - Chat fills vertical space |
| `autoscroll` | ~~Not set~~ | `autoscroll=True` | ✅ **DONE** - Auto-scroll to latest message |
| `show_progress` | ~~Not set (minimal)~~ | `show_progress="full"` | ✅ **DONE** - Per SPEC-22 |
| `gr.Progress` | ~~Used (broken)~~ | Remove | ✅ **DONE** - Per SPEC-22 |

---

## Detailed Findings

### 1. Message Format (OpenAI-style)

**Status:** ✅ Default in Gradio 6.0.1

Gradio 6.0.1 uses OpenAI-style dictionaries by default:
```python
{"role": "user" | "assistant", "content": str}
```

This is the modern standard and aligns with our LLM backends.

#### ⚠️ Version-Specific Note: No `type=` Parameter in 6.0.1

**Why online docs may confuse you:**
- Gradio 4.x/5.x had `type="messages"` or `type="tuples"` parameter
- Gradio 6.0.0 **removed** the tuples format entirely ([changelog](https://www.gradio.app/changelog))
- In 6.0.1, there is **no `type` parameter** - messages format is the only format

**Source verification (December 2025):**
```bash
# Check installed signature - no 'type' param exists
uv run python -c "import gradio; import inspect; print([p for p in inspect.signature(gradio.ChatInterface).parameters])"
# Result: ['fn', 'multimodal', 'chatbot', ... ] - no 'type'
```

If you see docs mentioning `type="messages"`, they're from older Gradio versions.

### 2. Fill Height (`fill_height=True`)

**Current:** Not set
**Recommended:** `fill_height=True`

Makes the chat interface fill available vertical space. Better UX on larger screens.

**Known Issue:** [GitHub #10407](https://github.com/gradio-app/gradio/issues/10407) - May conflict with `save_history=True`. We don't use `save_history`, so should be fine.

### 3. Autoscroll (`autoscroll=True`)

**Current:** Not set
**Recommended:** `autoscroll=True`

Ensures chat auto-scrolls to the latest message during streaming. Critical for long research outputs.

---

## Implementation Checklist

### SPEC-22 Items (Do First)
- [x] Remove `progress: gr.Progress = gr.Progress()` from `research_agent` signature
- [x] Remove all `progress(...)` calls in `research_agent`

### SPEC-23 Items
- [x] Add `show_progress="full"` to `gr.ChatInterface`
- [x] Add `fill_height=True` to `gr.ChatInterface`
- [x] Add `autoscroll=True` to `gr.ChatInterface`
- [x] Verify messages format is default (Gradio 6.0.1 - no `type=` param needed)

---

## Code Changes

### Before (Current)
```python
demo = gr.ChatInterface(
    fn=research_agent,
    title="🍆 DeepBoner",
    description=description,
    examples=[...],
    cache_examples=False,
    run_examples_on_click=False,
    additional_inputs_accordion=additional_inputs_accordion,
    additional_inputs=[...],
)
```

### After (Modernized) ✅ IMPLEMENTED
```python
demo = gr.ChatInterface(
    fn=research_agent,
    title="🍆 DeepBoner",
    description=description,
    examples=[...],
    cache_examples=False,
    run_examples_on_click=False,
    additional_inputs_accordion=additional_inputs_accordion,
    additional_inputs=[...],
    # SPEC-22: Use native progress instead of gr.Progress
    show_progress="full",
    # SPEC-23: Modern Gradio 6.0 settings
    # NOTE: Gradio 6.0.1 uses messages format by default (no type= param needed)
    fill_height=True,
    autoscroll=True,
)
```

---

## Risk Assessment

| Change | Risk | Status |
|--------|------|--------|
| `show_progress="full"` | Low | ✅ Implemented |
| `fill_height=True` | Low | ✅ Implemented |
| `autoscroll=True` | Low | ✅ Implemented |
| Messages format | None | ✅ Default in Gradio 6.0.1 - no code change needed |

---

## Verification

```bash
# After changes
make check

# Manual test
uv run python src/app.py
# Verify:
# 1. Chat fills vertical space
# 2. Auto-scrolls during streaming
# 3. Spinner appears (not floating progress bar)
```

---

## References

- [Gradio ChatInterface Docs](https://www.gradio.app/docs/gradio/chatinterface)
- [Gradio 6.0 Changelog](https://www.gradio.app/changelog) - Confirms tuples format removal
- [GitHub #10407: fill_height with save_history](https://github.com/gradio-app/gradio/issues/10407)
- [GitHub #11109: Autoscroll issue](https://github.com/gradio-app/gradio/issues/11109)

---

## Version History

| Date | Change |
|------|--------|
| 2025-12-07 | Initial implementation (SPEC-22 + SPEC-23) |
| 2025-12-07 | Added clarification: no `type=` param in Gradio 6.0.1 (tuples removed) |
