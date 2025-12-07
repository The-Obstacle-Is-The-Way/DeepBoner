# SPEC-23: Gradio 6.0 Modernization Audit

**Status:** READY FOR IMPLEMENTATION
**Priority:** P3 (Technical alignment)
**Effort:** 30 minutes
**Dependencies:** SPEC-22 (Progress Bar Removal)

---

## Executive Summary

Audit of `src/app.py` against Gradio 6.0.1 best practices. Identifies parameters we should add or update for full alignment with modern Gradio.

---

## Current State vs Best Practices

| Feature | Current | Best Practice | Action |
|---------|---------|---------------|--------|
| `type` param | Not set (legacy) | `type="messages"` | **ADD** - Uses OpenAI-style message format |
| `fill_height` | Not set | `fill_height=True` | **ADD** - Chat fills vertical space |
| `autoscroll` | Not set | `autoscroll=True` | **ADD** - Auto-scroll to latest message |
| `show_progress` | Not set (minimal) | `show_progress="full"` | **ADD** - Per SPEC-22 |
| `gr.Progress` | Used (broken) | Remove | **REMOVE** - Per SPEC-22 |

---

## Detailed Findings

### 1. Message Format (`type="messages"`)

**Current:** Not specified (uses legacy tuple format)
**Recommended:** `type="messages"`

The `type="messages"` format uses OpenAI-style dictionaries:
```python
{"role": "user" | "assistant", "content": str}
```

This is the modern standard and aligns with our LLM backends.

**Note:** This may require updating how we handle `history` parameter.

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
- [ ] Remove `progress: gr.Progress = gr.Progress()` from `research_agent` signature
- [ ] Remove all `progress(...)` calls in `research_agent`

### SPEC-23 Items
- [ ] Add `show_progress="full"` to `gr.ChatInterface`
- [ ] Add `fill_height=True` to `gr.ChatInterface`
- [ ] Add `autoscroll=True` to `gr.ChatInterface`
- [ ] Evaluate `type="messages"` migration (may require history format changes)

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

### After (Modernized)
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
    fill_height=True,
    autoscroll=True,
    # NOTE: type="messages" requires history format migration - evaluate separately
)
```

---

## Risk Assessment

| Change | Risk | Mitigation |
|--------|------|------------|
| `show_progress="full"` | Low | Native Gradio feature |
| `fill_height=True` | Low | May affect layout, test visually |
| `autoscroll=True` | Low | Native feature, improves UX |
| `type="messages"` | Medium | Requires history format changes - defer if needed |

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
- [GitHub #10407: fill_height with save_history](https://github.com/gradio-app/gradio/issues/10407)
- [GitHub #11109: Autoscroll issue](https://github.com/gradio-app/gradio/issues/11109)
