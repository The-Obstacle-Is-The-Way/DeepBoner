# P0 BUG: Simple Mode Ignores Forced Synthesis from HF Inference Failures

**Status**: OPEN - **Needs patch in simple.py**
**Priority**: P0 (Demo-blocking)
**Discovered**: 2025-12-01
**Affected Component**: `src/orchestrators/simple.py`
**GitHub Issue**: [#113](https://github.com/The-Obstacle-Is-The-Way/DeepBoner/issues/113)

---

## ⚠️ CRITICAL CLARIFICATION: Simple Mode is NOT Being Deleted

> **SIMPLE MODE MUST BE KEPT** as the free-tier fallback.
>
> The previous decision to "delete Simple Mode and unify on Advanced Mode" was **PREMATURE**.
> Advanced Mode + HuggingFace has an upstream bug (#2562) that breaks the display.
>
> **Correct approach:**
> - ✅ **KEEP** Simple Mode as the default for free-tier users (no API key)
> - ✅ **FIX** this bug by patching `_should_synthesize()` in simple.py
> - ✅ **USE** Advanced Mode only when paid API key is available
> - ❌ **DO NOT DELETE** Simple Mode until upstream bug is fixed AND verified

---

## Problem Statement

When HuggingFace Inference API fails 3 consecutive times, the `HFInferenceJudgeHandler` correctly returns a "forced synthesis" assessment with `sufficient=True, recommendation="synthesize"`. However, **Simple Mode's `_should_synthesize()` method ignores this signal** because of overly strict code-enforced thresholds.

### Observed Behavior

```
✅ JUDGE_COMPLETE: Assessment: synthesize (confidence: 10%)
🔄 LOOPING: Gathering more evidence...  ← BUG: Should have synthesized!
```

The orchestrator loops **10 full iterations** despite the judge repeatedly saying "synthesize" after iteration 4.

### Expected Behavior

When `HFInferenceJudgeHandler._create_forced_synthesis_assessment()` returns:
- `sufficient=True`
- `recommendation="synthesize"`

The orchestrator should **immediately synthesize**, regardless of score thresholds.

---

## Root Cause Analysis

### The Forced Synthesis Assessment (judges.py:514-549)

```python
def _create_forced_synthesis_assessment(self, question, evidence):
    return JudgeAssessment(
        details=AssessmentDetails(
            mechanism_score=0,        # ← Problem 1: Score is 0
            clinical_evidence_score=0, # ← Problem 2: Score is 0
            drug_candidates=["AI analysis required..."],
            key_findings=findings,
        ),
        sufficient=True,              # ← Correct: Says sufficient
        confidence=0.1,               # ← Problem 3: Too low for emergency
        recommendation="synthesize",  # ← Correct: Says synthesize
        ...
    )
```

### The _should_synthesize Logic (simple.py:159-216)

```python
def _should_synthesize(self, assessment, iteration, max_iterations, evidence_count):
    combined_score = mechanism_score + clinical_evidence_score  # = 0

    # Priority 1: Judge approved - BUT REQUIRES combined_score >= 10!
    if assessment.sufficient and assessment.recommendation == "synthesize":
        if combined_score >= 10:  # ← 0 >= 10 is FALSE!
            return True, "judge_approved"

    # Priority 2-5: All require scores or drug candidates we don't have

    # Priority 6: Emergency synthesis
    if is_late_iteration and evidence_count >= 30 and confidence >= 0.5:
        #                                          ↑ 0.1 >= 0.5 is FALSE!
        return True, "emergency_synthesis"

    return False, "continue_searching"  # ← Always ends up here!
```

### The Bug

1. **Priority 1 has wrong precondition**: It checks `combined_score >= 10` even when the judge explicitly says "synthesize". The score check should be skipped when it's a forced/error recovery synthesis.

2. **Priority 6 confidence threshold is too high**: 0.5 confidence is reasonable for "emergency" synthesis, but forced synthesis from API failures uses 0.1 confidence to indicate low quality—this should still trigger synthesis.

---

## Impact

- **User sees**: 10 iterations of "Gathering more evidence" with 0% confidence
- **Final output**: Partial synthesis with "Max iterations reached"
- **Time wasted**: ~2-3 minutes of useless API calls
- **UX**: Extremely confusing - user sees "synthesize" but system keeps searching

---

## Proposed Fix

### ✅ Option A: Patch Simple Mode (APPROVED)

Patch `_should_synthesize()` to respect forced synthesis signals:

```python
# src/orchestrators/simple.py
def _should_synthesize(self, assessment, iteration, max_iterations, evidence_count):
    # NEW: Priority 0 - Forced synthesis from error recovery
    # When judge explicitly says "synthesize" with forced=True, DO IT
    if assessment.sufficient and assessment.recommendation == "synthesize":
        if getattr(assessment, 'forced', False):
            return True, "forced_synthesis"

    combined_score = mechanism_score + clinical_evidence_score

    # Rest of existing logic...
```

### ~~Option B: SPEC_16 Unification~~ (DEFERRED)

The original plan was to delete Simple Mode and unify on Advanced Mode. **This was PREMATURE**.

**Why it failed:**
1. Advanced Mode + HuggingFace has upstream bug (#2562) - repr garbage output
2. Simple Mode was deleted BEFORE verifying Advanced+HF worked
3. No fallback exists for free-tier users

**Correct order:**
1. ✅ Keep Simple Mode as free-tier fallback
2. ✅ Patch this bug in simple.py
3. ⏳ Wait for upstream #2562 fix
4. ⏳ THEN consider unification (maybe)

---

## Files to KEEP

| File | Lines | Reason |
|------|-------|--------|
| `src/orchestrators/simple.py` | 778 | **KEEP** - Free tier fallback |
| `src/tools/search_handler.py` | 219 | **KEEP** - Required by Simple Mode |

## Files Already Created (for future unification)

| File | Lines | Purpose |
|------|-------|---------|
| `src/clients/__init__.py` | ~10 | Package exports |
| `src/clients/factory.py` | ~50 | `get_chat_client()` factory |
| `src/clients/huggingface.py` | ~150 | `HuggingFaceChatClient` adapter |

**These are useful for Advanced Mode + HuggingFace, but Simple Mode is still needed.**

---

## Acceptance Criteria (Simple Mode Patch)

- [ ] `_should_synthesize()` respects forced synthesis signals
- [ ] Add `forced` attribute to `JudgeAssessment` in error recovery
- [ ] No more "continue_searching" loops when HF fails
- [ ] Simple Mode remains the default for free-tier users
- [ ] Simple Mode works correctly on HuggingFace Spaces

---

## Test Case (SPEC_16 Verification)

```python
@pytest.mark.asyncio
async def test_unified_architecture_handles_hf_failures():
    """
    After SPEC_16: Free tier uses Advanced Mode with HuggingFace backend.
    When HF fails, Manager agent should trigger synthesis via ReportAgent.

    This test replaces the old Simple Mode test because:
    - simple.py is DELETED
    - Advanced Mode handles termination via Manager agent signals
    - No _should_synthesize() thresholds to bypass
    """
    from unittest.mock import patch, MagicMock
    from src.orchestrators.advanced import AdvancedOrchestrator
    from src.clients.factory import get_chat_client

    # Verify factory returns HuggingFace client when no OpenAI key
    with patch("src.utils.config.settings") as mock_settings:
        mock_settings.has_openai_key = False
        mock_settings.has_gemini_key = False
        mock_settings.has_huggingface_key = True

        client = get_chat_client()
        assert "HuggingFace" in type(client).__name__

    # Verify AdvancedOrchestrator accepts HuggingFace client
    # (The actual termination is handled by Manager agent respecting
    #  "SUFFICIENT EVIDENCE" signals per SPEC_15)
```

---

## Related Issues & Specs

| Reference | Type | Relationship |
|-----------|------|--------------|
| [SPEC_16](../specs/SPEC_16_UNIFIED_CHAT_CLIENT_ARCHITECTURE.md) | Spec | **THE FIX** - Unified architecture eliminates this bug |
| [SPEC_15](../specs/SPEC_15_ADVANCED_MODE_PERFORMANCE.md) | Spec | Manager agent termination logic (already implemented) |
| [Issue #105](https://github.com/The-Obstacle-Is-The-Way/DeepBoner/issues/105) | GitHub | Deprecate Simple Mode |
| [Issue #109](https://github.com/The-Obstacle-Is-The-Way/DeepBoner/issues/109) | GitHub | Simplify Provider Architecture |
| [Issue #110](https://github.com/The-Obstacle-Is-The-Way/DeepBoner/issues/110) | GitHub | Remove Anthropic Support |
| PR #71 (SPEC_06) | PR | Added `_should_synthesize()` - now causes this bug |
| Commit 5e761eb | Commit | Added `_create_forced_synthesis_assessment()` |

---

## References

- `src/orchestrators/simple.py:159-216` - `_should_synthesize()` method
- `src/agent_factory/judges.py:514-549` - `_create_forced_synthesis_assessment()`
- `src/agent_factory/judges.py:477-512` - `_create_quota_exhausted_assessment()`
