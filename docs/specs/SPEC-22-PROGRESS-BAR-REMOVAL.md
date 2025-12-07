# SPEC-22: Remove Unsupported gr.Progress from ChatInterface

**Status:** READY FOR IMPLEMENTATION
**Priority:** P3 (Technical debt cleanup)
**Effort:** 15 minutes
**PR Scope:** Single file fix

---

## Executive Summary

We are using `gr.Progress()` with `gr.ChatInterface`, but **Gradio does not support this combination**. This is not a workaround - this is the correct fix to align with Gradio's architecture.

---

## Technical Background

### Gradio's Progress Mechanisms

| Mechanism | Designed For | Works With ChatInterface |
|-----------|--------------|-------------------------|
| `gr.Progress()` | `gr.Interface` | ❌ NO - causes visual glitches |
| `show_progress` param | `ChatInterface` | ✅ YES - built-in spinner/timer |
| Streaming yields | `ChatInterface` | ✅ YES - native support |
| `ChatMessage.metadata.status` | `ChatInterface` | ✅ YES - per-message indicators |

### Why gr.Progress Fails with ChatInterface

1. **GitHub Issue [#5967](https://github.com/gradio-app/gradio/issues/5967)**: "gr.Progress is not integrated with ChatInterface or Chatbots" - closed without resolution (Jan 2024)
2. **Visual symptoms**: Progress bar floats in middle of chat output, overlaps text
3. **Root cause**: `gr.Progress` injects UI into the output component area, but `ChatInterface` manages its own output rendering

### What We Already Have (Working)

Our `research_agent` function already yields semantic status messages:

```python
yield "🧠 **Backend**: Paid API (OpenAI) | **Domain**: Sexual Health"
yield "⏳ **Processing...** Searching PubMed, ClinicalTrials.gov..."
# During orchestration:
yield "⏱️ **PROGRESS**: Round 1/5 (~3m 0s remaining)"
yield "🔬 **Step 2: SearchAgent** - Searching for evidence..."
yield "✅ **COMPLETE**: Research finished"
```

These work perfectly with ChatInterface streaming.

---

## The Fix

### What to Remove

```python
# src/app.py - REMOVE from research_agent signature:
progress: gr.Progress = gr.Progress(),  # noqa: B008

# src/app.py - REMOVE all progress() calls:
progress(0, desc="Starting research...")
progress(0.1, desc="Multi-agent reasoning...")
progress(p, desc=event.message)
```

### What to Add (Optional Enhancement)

```python
# src/app.py - In create_demo(), add show_progress for built-in spinner:
demo = gr.ChatInterface(
    fn=research_agent,
    show_progress="full",  # Shows spinner + runtime timer (Gradio native)
    ...
)
```

---

## Why This Is The Correct Approach (Not A Workaround)

### ❌ What Would Be Over-Engineering

Refactoring from `ChatInterface` to `gr.Blocks` + `gr.Chatbot` just to support `gr.Progress`:

| ChatInterface provides FREE | gr.Blocks would require manual |
|---------------------------|-------------------------------|
| MCP server support | Unknown if compatible |
| Chat history state | Manual `gr.State` management |
| Submit/Stop buttons | Manual button wiring |
| Example handling | Manual click handlers |
| Streaming support | Manual async iteration |
| Accordion for inputs | Manual accordion component |

**Effort**: Days of refactoring + testing
**Benefit**: A progress bar (which we already have via emoji status)
**Verdict**: Not justified

### ✅ What Is Professional Engineering

1. Use `ChatInterface` as designed (high-level, batteries-included)
2. Remove unsupported feature (`gr.Progress`)
3. Rely on supported mechanisms:
   - Streaming status yields (already implemented)
   - `show_progress="full"` (Gradio native)

---

## Implementation Checklist

- [ ] Open `src/app.py`
- [ ] Remove `progress: gr.Progress = gr.Progress()` from `research_agent` signature
- [ ] Remove all `progress(...)` calls (lines 192, 194, 204)
- [ ] Add `show_progress="full"` to `gr.ChatInterface` constructor
- [ ] Verify emoji status yields still present in orchestrator events
- [ ] Run `make check`
- [ ] Test locally: `uv run python src/app.py`

---

## Verification

```bash
# Verify no gr.Progress usage
grep -n "gr.Progress\|progress(" src/app.py

# Should return empty (no matches)
```

### Manual Test
1. Start app: `uv run python src/app.py`
2. Submit a research query
3. Verify:
   - ✅ Gradio spinner appears (top-right timer)
   - ✅ Emoji status messages stream in chat
   - ❌ No floating/overlapping progress bar

---

## Acceptance Criteria

1. No `gr.Progress` in codebase
2. `show_progress="full"` added to ChatInterface
3. Emoji status messages continue working
4. No visual glitches in UI
5. `make check` passes

---

## References

- [Gradio ChatInterface Docs](https://www.gradio.app/docs/gradio/chatinterface)
- [Gradio Progress Bars Guide](https://www.gradio.app/guides/progress-bars)
- [GitHub #5967: Progress bar for ChatInterface](https://github.com/gradio-app/gradio/issues/5967)
