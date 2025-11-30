# SPEC_11: Narrow Scope to Sexual Health Only

## Problem Statement

DeepBoner has an **identity crisis**. Despite being branded as a "pro-sexual deep research agent" (the name is literally "DeepBoner"), the codebase currently supports three domains:

1. **GENERAL** - Generic research (default!)
2. **DRUG_REPURPOSING** - Drug repurposing research
3. **SEXUAL_HEALTH** - Sexual health research

This happened because Issue #75 recommended "general purpose with domain presets", but that was the **wrong decision** for this project's identity.

### Evidence of the Problem

**Current examples in Gradio UI:**
```python
examples=[
    ["What drugs improve female libido post-menopause?", "simple", "sexual_health", ...],
    ["Metformin mechanism for Alzheimer's?", "simple", "general", ...],  # <-- NOT SEXUAL HEALTH!
    ["Clinical trials for PDE5 inhibitors alternatives?", "advanced", "sexual_health", ...],
]
```

**Default domain is "general":**
```python
value="general",  # <-- WRONG! Should be sexual_health
```

## The Decision

**DeepBoner IS a Sexual Health Research Specialist (Option B from Issue #75)**

Reasons:
1. **Brand identity**: "DeepBoner" is unmistakably sexual health themed
2. **Hackathon differentiation**: A focused niche beats generic competition
3. **Prompt quality**: Domain-specific prompts are more effective
4. **Simplicity**: Less code, less confusion

## Implementation Plan

### Phase 1: Simplify Domain Enum

**File: `src/config/domain.py`**

```python
# BEFORE
class ResearchDomain(str, Enum):
    GENERAL = "general"
    DRUG_REPURPOSING = "drug_repurposing"
    SEXUAL_HEALTH = "sexual_health"

DEFAULT_DOMAIN = ResearchDomain.GENERAL

# AFTER
class ResearchDomain(str, Enum):
    SEXUAL_HEALTH = "sexual_health"

DEFAULT_DOMAIN = ResearchDomain.SEXUAL_HEALTH
```

**Also remove:**
- `GENERAL_CONFIG`
- `DRUG_REPURPOSING_CONFIG`
- Their entries in `DOMAIN_CONFIGS`

### Phase 2: Update Gradio Examples

**File: `src/app.py`**

Replace examples with 3 sexual-health-only queries:

```python
examples=[
    [
        "What drugs improve female libido post-menopause?",
        "simple",
        "sexual_health",
        None,
        None,
    ],
    [
        "Testosterone therapy for hypoactive sexual desire disorder?",
        "simple",
        "sexual_health",
        None,
        None,
    ],
    [
        "Clinical trials for PDE5 inhibitors alternatives?",
        "advanced",
        "sexual_health",
        None,
        None,
    ],
],
```

### Phase 3: Simplify or Remove Domain Dropdown

**Option A: Remove dropdown entirely**
- Remove the `gr.Dropdown` for domain selection
- Hardcode `domain="sexual_health"` in the function

**Option B: Keep but simplify** (recommended for backwards compat)
- Only show `["sexual_health"]` in choices
- Default to `"sexual_health"`
- Keeps the parameter in case we want to add domains later

```python
gr.Dropdown(
    choices=["sexual_health"],  # Only one choice
    value="sexual_health",
    label="Research Domain",
    info="Specialized for sexual health research",
    visible=False,  # Hide since there's only one option
),
```

### Phase 4: Update Tests

Update domain-related tests to only test SEXUAL_HEALTH:

```python
# BEFORE
def test_get_domain_config_general():
    config = get_domain_config(ResearchDomain.GENERAL)
    assert config.name == "General Research"

# AFTER
def test_get_domain_config_default():
    config = get_domain_config()
    assert config.name == "Sexual Health Research"
```

### Phase 5: Update Documentation

- `CLAUDE.md`: Update description to focus on sexual health
- `README.md`: Update if needed
- Remove references to "drug repurposing" or "general" modes

## Files to Modify

| File | Changes |
|------|---------|
| `src/config/domain.py` | Remove GENERAL, DRUG_REPURPOSING; change DEFAULT_DOMAIN |
| `src/app.py` | Update examples; simplify/hide domain dropdown |
| `src/utils/config.py` | Change default `research_domain` field |
| `tests/unit/config/test_domain.py` | Update to test only SEXUAL_HEALTH |
| `tests/unit/utils/test_config_domain.py` | Update enum tests |
| `tests/unit/test_app_domain.py` | Update to use SEXUAL_HEALTH |
| `CLAUDE.md` | Update project description |

## Example Queries (All Sexual Health)

1. **Female libido**: "What drugs improve female libido post-menopause?"
2. **Low desire**: "Testosterone therapy for hypoactive sexual desire disorder?"
3. **ED alternatives**: "Clinical trials for PDE5 inhibitors alternatives?"

Alternative options:
- "Flibanserin mechanism of action and efficacy?"
- "Bremelanotide for hypoactive sexual desire disorder?"
- "PT-141 clinical trial results?"
- "Natural supplements for erectile dysfunction?"

## Success Criteria

- [ ] Only `SEXUAL_HEALTH` domain exists in enum
- [ ] Default domain is `SEXUAL_HEALTH`
- [ ] All 3 Gradio examples are sexual health queries
- [ ] Domain dropdown is hidden or removed
- [ ] All tests pass with 227+ tests
- [ ] No references to "Metformin for Alzheimer's" or "general" domain

## Related Issues

- #75 (CLOSED) - Domain Identity Crisis (original issue, wrong recommendation)
- #76 (CLOSED) - Hardcoded prompts (implemented but too general)
- #85 (OPEN) - Report lacks narrative synthesis (next priority)
