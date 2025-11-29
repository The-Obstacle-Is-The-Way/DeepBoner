# UI Simplification: Remove Anthropic Provider

**Issues**: #52, #53
**Priority**: P1 - UX improvement for hackathon demo
**Estimated Time**: 30 minutes

---

## Problem

The current UI has confusing BYOK (Bring Your Own Key) settings:

1. **Provider dropdown is misleading** - Shows "openai" but actually uses free tier when no key
2. **Examples table shows useless columns** - API Key (empty), Provider (ignored)
3. **Anthropic doesn't work with Advanced mode** - Only OpenAI has `agent-framework` support

## Solution

Remove `api_provider` dropdown entirely. Auto-detect provider from key prefix.

---

## Implementation

### File: `src/app.py`

#### 1. Update `configure_orchestrator()` signature

```python
# BEFORE
def configure_orchestrator(
    use_mock: bool = False,
    mode: str = "simple",
    user_api_key: str | None = None,
    api_provider: str = "openai",  # REMOVE THIS
) -> tuple[Any, str]:

# AFTER
def configure_orchestrator(
    use_mock: bool = False,
    mode: str = "simple",
    user_api_key: str | None = None,
) -> tuple[Any, str]:
```

#### 2. Auto-detect provider from key prefix

```python
# Inside configure_orchestrator, replace provider logic with:
if user_api_key:
    # Auto-detect provider from key prefix
    if user_api_key.startswith("sk-ant-"):
        # Anthropic key
        anthropic_provider = AnthropicProvider(api_key=user_api_key)
        model = AnthropicModel(settings.anthropic_model, provider=anthropic_provider)
        backend_info = "Paid API (Anthropic)"
    elif user_api_key.startswith("sk-"):
        # OpenAI key
        openai_provider = OpenAIProvider(api_key=user_api_key)
        model = OpenAIModel(settings.openai_model, provider=openai_provider)
        backend_info = "Paid API (OpenAI)"
    else:
        raise ValueError("Invalid API key format. Expected sk-... (OpenAI) or sk-ant-... (Anthropic)")

    judge_handler = JudgeHandler(model=model)
```

#### 3. Update `research_agent()` signature

```python
# BEFORE
async def research_agent(
    message: str,
    history: list[dict[str, Any]],
    mode: str = "simple",
    api_key: str = "",
    api_provider: str = "openai",  # REMOVE THIS
) -> AsyncGenerator[str, None]:

# AFTER
async def research_agent(
    message: str,
    history: list[dict[str, Any]],
    mode: str = "simple",
    api_key: str = "",
) -> AsyncGenerator[str, None]:
```

#### 4. Update warning message for Advanced mode

```python
# BEFORE
if mode == "advanced" and not (has_openai or (has_user_key and api_provider == "openai")):

# AFTER
is_openai_key = user_api_key and user_api_key.startswith("sk-") and not user_api_key.startswith("sk-ant-")
if mode == "advanced" and not (has_openai or is_openai_key):
    yield (
        "⚠️ **Advanced mode requires OpenAI API key.** "
        "Anthropic keys only work in Simple mode. Falling back to Simple.\\n\\n"
    )
    mode = "simple"
```

#### 5. Simplify examples (remove provider column)

```python
# BEFORE
examples=[
    ["What drugs improve female libido post-menopause?", "simple", "", "openai"],
    ["Clinical trials for erectile dysfunction alternatives to PDE...", "simple", "", "openai"],
    ["Evidence for testosterone therapy in women with HSDD?", "simple", "", "openai"],
]

# AFTER
examples=[
    ["What drugs improve female libido post-menopause?", "simple", ""],
    ["Clinical trials for ED alternatives to PDE5 inhibitors?", "simple", ""],
    ["Evidence for testosterone therapy in women with HSDD?", "simple", ""],
]
```

#### 6. Remove provider from additional_inputs

```python
# BEFORE
additional_inputs=[
    gr.Radio(
        choices=["simple", "advanced"],
        value="simple",
        label="Orchestrator Mode",
        ...
    ),
    gr.Textbox(
        label="🔑 API Key (Optional - BYOK)",
        ...
    ),
    gr.Radio(  # REMOVE THIS ENTIRE BLOCK
        choices=["openai", "anthropic"],
        value="openai",
        label="API Provider",
        ...
    ),
]

# AFTER
additional_inputs=[
    gr.Radio(
        choices=["simple", "advanced"],
        value="simple",
        label="Orchestrator Mode",
        info="Simple: Works with free tier | Advanced: Requires OpenAI key",
    ),
    gr.Textbox(
        label="🔑 API Key (Optional)",
        placeholder="sk-... (OpenAI) or sk-ant-... (Anthropic)",
        type="password",
        info="Leave empty for free tier (Llama 3.1). Auto-detects provider from key.",
    ),
]
```

#### 7. Update accordion label

```python
additional_inputs_accordion=gr.Accordion(
    label="⚙️ Settings (Free tier works without API key)",
    open=False
),
```

---

## Testing

### Manual Tests
1. **No key**: Should use free tier (HuggingFace Inference)
2. **OpenAI key**: Should detect and use OpenAI
3. **Anthropic key**: Should detect and use Anthropic in Simple mode
4. **Anthropic key + Advanced**: Should warn and fallback to Simple

### Unit Test Updates
- Update `tests/unit/test_app_smoke.py` if it checks additional_inputs count

---

## Definition of Done

- [ ] `api_provider` parameter removed from both functions
- [ ] Auto-detection logic works for both key types
- [ ] Examples table only shows 2 columns (query, mode)
- [ ] Accordion label updated
- [ ] Placeholder text shows key formats
- [ ] Advanced mode warning works with auto-detection
- [ ] All existing tests pass

---

## Related
- Issue #52: UI Polish - Examples table confusion
- Issue #53: API Provider Simplification
