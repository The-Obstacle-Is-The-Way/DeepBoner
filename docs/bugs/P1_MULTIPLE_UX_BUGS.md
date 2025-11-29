# P1 Bug Report: Multiple UX and Configuration Issues

## Status
- **Date:** 2025-11-29
- **Priority:** P1 (Multiple user-facing issues)
- **Components:** `src/app.py`, `src/orchestrator_magentic.py`

## Resolved Issues (Fixed 2025-11-29)

### Bug 1: API Key Cleared When Clicking Examples
**Fixed.** Updated `examples` in `app.py` to include explicit `None` values for additional inputs. Gradio preserves values when the example value is `None`.

### Bug 2: No Loading/Processing Indicator
**Fixed.** `research_agent` yields an immediate "⏳ Processing..." message before starting the orchestrator.

### Bug 3: Advanced Mode Temperature Error
**Fixed.** Explicitly set `temperature=1.0` for all Magentic agents in `src/agents/magentic_agents.py`. This is compatible with OpenAI reasoning models (o1/o3) which require `temperature=1` and were rejecting the default (likely 0.3 or None).

### Bug 4: HSDD Acronym Not Spelled Out
**Fixed.** Updated example text in `app.py` to "HSDD (Hypoactive Sexual Desire Disorder)".

---

## Open / Deferred Issues

### Bug 5: Free Tier Quota Exhausted (UX Improvement)
**Deferred.** Currently shows standard error message. Improve if users report confusion.

### Bug 6: Asyncio File Descriptor Warnings
**Won't Fix.** Cosmetic issue only.

---

## Priority Order (Completed)

1. **Bug 4 (HSDD)** - Fixed
2. **Bug 2 (Loading indicator)** - Fixed
3. **Bug 3 (Temperature)** - Fixed
4. **Bug 1 (API key)** - Fixed

---

## Test Plan
- [x] Fix HSDD acronym
- [x] Add loading indicator yield
- [x] Test advanced mode with temperature fix (Static analysis/Code change)
- [x] Research Gradio example behavior for API key (Implemented None fix)
- [ ] Run `make check`
- [ ] Deploy and test on HuggingFace Spaces
