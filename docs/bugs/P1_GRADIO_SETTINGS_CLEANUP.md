# P1: Gradio Settings Panel - Keep or Remove?

**Priority**: P1 (UX improvement)
**Status**: NEEDS DECISION
**Date**: 2025-11-27

---

## Current State

The Gradio UI has a "Settings" accordion containing:

1. **Orchestrator Mode**: simple | magentic
2. **API Key (BYOK)**: User can enter their own key
3. **API Provider**: openai | anthropic

Screenshot shows it takes up vertical space even when collapsed.

---

## The Question

Should we **keep**, **simplify**, or **remove** this settings panel?

---

## Analysis

### Option A: Remove Entirely

**Pros:**
- Cleaner, simpler UI
- Magentic mode is broken anyway (P0 bug)
- 95% of users will use defaults
- Less cognitive load for hackathon judges

**Cons:**
- No BYOK option (users stuck with server's API key or free tier)
- No way to test Magentic mode when fixed

**Code Change:**
```python
# Remove additional_inputs entirely
gr.ChatInterface(
    fn=research_agent,
    examples=[...],
    # No additional_inputs_accordion
    # No additional_inputs
)
```

### Option B: Simplify to Just BYOK

**Pros:**
- Keep useful feature (bring your own key)
- Remove broken Magentic option
- Simpler UI

**Cons:**
- Still has settings panel

**Code Change:**
```python
additional_inputs=[
    gr.Textbox(
        label="🔑 API Key (Optional)",
        placeholder="sk-... or sk-ant-...",
        type="password",
    ),
]
```

### Option C: Keep But Fix Accordion

**Pros:**
- All options available
- Power users can access

**Cons:**
- Magentic is broken
- Adds complexity

**Code Change:**
- Ensure `open=False` works correctly
- Maybe move to footer or separate tab

---

## Recommendation

**For Hackathon**: **Option A (Remove)** or **Option B (BYOK only)**

Reasoning:
1. Magentic mode has a P0 bug - offering it confuses users
2. Simple mode works perfectly
3. Clean UI impresses judges
4. BYOK is the only genuinely useful setting

---

## Decision Needed

- [ ] **Remove all settings** (cleanest)
- [ ] **Keep only BYOK** (useful subset)
- [ ] **Keep all but hide better** (preserve functionality)
- [ ] **Keep as-is** (no change)

---

## Implementation

If removing settings:

**File**: `src/app.py`

```python
# Before (lines 229-249)
additional_inputs_accordion=gr.Accordion(label="⚙️ Settings", open=False),
additional_inputs=[
    gr.Radio(...),  # mode
    gr.Textbox(...),  # api_key
    gr.Radio(...),  # provider
],

# After
# Delete additional_inputs_accordion and additional_inputs
# Update research_agent signature to remove unused params
```

Also update `research_agent()` function signature:
```python
# Before
async def research_agent(message, history, mode, api_key, api_provider):

# After (if removing all settings)
async def research_agent(message, history):
    mode = "simple"  # Hardcode
    api_key = ""
    api_provider = "openai"
```
