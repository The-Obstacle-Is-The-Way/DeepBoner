# Active Bugs

> Last updated: 2025-12-02 (07:30 EST)
>
> **Note:** Completed bug docs archived to `docs/bugs/archive/`
> **See also:** [Code Quality Audit Findings (2025-11-30)](AUDIT_FINDINGS_2025_11_30.md)
> **See also:** [ARCHITECTURE.md](../ARCHITECTURE.md) for unified architecture plan

## P1 - High (ACTIVE)

### HuggingFace Novita Provider 500 Error

**File:** `docs/bugs/P1_HUGGINGFACE_NOVITA_500_ERROR.md`
**Status:** ACTIVE - Upstream Infrastructure Issue

**Problem:** Free tier (no API key) fails with 500 error from Novita provider.

**Cause:** HuggingFace routes Qwen/Qwen2.5-72B-Instruct to Novita (third-party), and Novita is returning 500 errors.

**Fix Options:**
1. Switch to a model hosted natively by HuggingFace
2. Implement fallback model logic
3. Wait for Novita to fix their infrastructure

---

## Resolved Bugs

### ~~P0 - Repr Bug (Display Garbage)~~ FIXED

**File:** `P0_REPR_BUG_ROOT_CAUSE_ANALYSIS.md`, `docs/specs/SPEC_17_ACCUMULATOR_PATTERN.md`
**Found:** 2025-12-01
**Resolved:** 2025-12-02 (PR #117)

- Problem: Free tier showed `<agent_framework._types.ChatMessage object at 0x...>` instead of text
- Root Cause: We were using API incorrectly - reading from `MagenticAgentMessageEvent.message` instead of `MagenticAgentDeltaEvent.text`
- Fix: Implemented **Accumulator Pattern** (SPEC-17) - bypasses the upstream bug by using the API correctly
- Note: Upstream fix (PR #2566) is now moot - we don't need it anymore

### ~~P0 - AIFunction Not JSON Serializable~~ FIXED

**File:** `docs/bugs/P0_AIFUNCTION_NOT_JSON_SERIALIZABLE.md`
**Found:** 2025-12-01
**Resolved:** 2025-12-01

- Problem: `HuggingFaceChatClient` crashed with "Object of type AIFunction is not JSON serializable".
- Fix: Implemented full bi-directional tool support:
    1. **Serialization**: Added `_convert_tools` (AIFunction → OpenAI JSON)
    2. **Parsing (Sync/Async)**: Added `_parse_tool_calls` and streaming accumulator
- Result: Free Tier now supports full function calling capabilities with Qwen2.5-72B.

### ~~P1 - HuggingFace Router 401 Unauthorized~~ FIXED

**File:** `docs/bugs/P1_HUGGINGFACE_ROUTER_401_HYPERBOLIC.md`
**Found:** 2025-12-01
**Resolved:** 2025-12-01

- Problem: 401 errors from HuggingFace Router (Hyperbolic/Novita providers)
- **Actual Root Cause:** HF_TOKEN in `.env` and Spaces secrets was **invalid/expired**
- Fix: Generated new valid HF_TOKEN, updated `.env` and Spaces secrets
- Also switched default model to `Qwen/Qwen2.5-72B-Instruct` for better reliability

### ~~P1 - Advanced Mode Exposes Uninterpretable Chain-of-Thought~~ FIXED

**File:** `docs/bugs/P1_ADVANCED_MODE_UNINTERPRETABLE_CHAIN_OF_THOUGHT.md`
**PR:** [#107](https://github.com/The-Obstacle-Is-The-Way/DeepBoner/pull/107)
**Found:** 2025-12-01
**Resolved:** 2025-12-01

- Problem: Advanced mode exposed raw `task_ledger` and `instruction` events, truncated mid-word.
- Fix: Filtered internal events, transformed `user_task` to progress type, smart sentence-aware truncation.
- Tests: `tests/unit/orchestrators/test_advanced_events.py` (5 tests)
- CodeRabbit review addressed: test markers, edge case handling, truncation test coverage.

### ~~P0 - Advanced Mode Timeout Yields No Synthesis~~ FIXED

**File:** `docs/bugs/P0_ADVANCED_MODE_TIMEOUT_NO_SYNTHESIS.md`
**Found:** 2025-11-30 (Manual Testing)
**Resolved:** 2025-12-01

- Problem: Advanced mode timed out and displayed "Synthesizing..." but no synthesis occurred.
- Root Causes:
  1. Timeout handler yielded misleading message without calling ReportAgent
  2. Factory used wrong setting (`max_iterations=10` instead of `advanced_max_rounds=5`)
  3. Missing `get_context_summary()` in ResearchMemory
- Fix:
  1. Implemented actual synthesis on timeout via ReportAgent invocation
  2. Factory now uses `settings.advanced_max_rounds` (5)
  3. Added `get_context_summary()` to ResearchMemory
- Tests: `tests/unit/orchestrators/test_advanced_timeout.py`
- Key files: `src/orchestrators/advanced.py`, `src/orchestrators/factory.py`, `src/services/research_memory.py`

### ~~P0 - Free Tier Synthesis Incorrectly Uses Server-Side API Keys~~ FIXED (Historical)

**File:** `docs/bugs/P1_SYNTHESIS_BROKEN_KEY_FALLBACK.md`
**PR:** [#103](https://github.com/The-Obstacle-Is-The-Way/DeepBoner/pull/103)
**Found:** 2025-11-30 (Testing)
**Resolved:** 2025-11-30

- Problem: Simple Mode crashed with "OpenAIError" on HuggingFace Spaces.
- Note: This was in the OLD Simple Mode. Now we use Unified Architecture.

### ~~P0 - Synthesis Fails with OpenAIError in Free Mode~~ FIXED (Historical)

**File:** `docs/bugs/P0_SYNTHESIS_PROVIDER_MISMATCH.md`
**Found:** 2025-11-30 (Code Audit)
**Resolved:** 2025-11-30

- Problem: "Simple Mode" (Free Tier) crashed with `OpenAIError`.
- Note: This was in the OLD Simple Mode. Now we use Unified Architecture.

### ~~P0 - Simple Mode Never Synthesizes~~ FIXED (Historical)

**PR:** [#71](https://github.com/The-Obstacle-Is-The-Way/DeepBoner/pull/71) (SPEC_06)
**Commit**: `5cac97d` (2025-11-29)

- Root cause: LLM-as-Judge recommendations were being IGNORED
- Note: This was in the OLD Simple Mode. Now we use Unified Architecture.

### ~~P3 - Magentic Mode Missing Termination Guarantee~~ FIXED

**Commit**: `d36ce3c` (2025-11-29)

- Added `final_event_received` tracking in `orchestrator_magentic.py`
- Added fallback yield for "max iterations reached" scenario
- Verified with `test_magentic_termination.py`

### ~~P0 - Magentic Mode Report Generation~~ FIXED

**Commit**: `9006d69` (2025-11-29)

- Fixed `_extract_text()` to handle various message object formats
- Increased `max_rounds=10` (was 3)
- Added `temperature=1.0` for reasoning model compatibility
- Advanced mode now produces full research reports

### ~~P1 - Streaming Spam + API Key Persistence~~ FIXED

**Commit**: `0c9be4a` (2025-11-29)

- Streaming events now buffered (not token-by-token spam)
- API key persists across example clicks via `gr.State`
- Examples use explicit `None` values to avoid overwriting keys

### ~~P2 - Missing "Thinking" State~~ FIXED

**Commit**: `9006d69` (2025-11-29)

- Added `"thinking"` event type with hourglass icon
- Yields "Multi-agent reasoning in progress..." before blocking workflow call
- Users now see feedback during 2-5 minute initial processing

### ~~P2 - Gradio Example Not Filling Chat Box~~ FIXED

**Commit**: `2ea01fd` (2025-11-29)

- Third example (HSDD) wasn't populating chat box when clicked
- Root cause: Parentheses in `HSDD (Hypoactive Sexual Desire Disorder)`
- Fix: Simplified to `Testosterone therapy for Hypoactive Sexual Desire Disorder?`

### ~~P1 - Gradio Settings Accordion~~ WONTFIX

Decision: Removed nested Blocks, using ChatInterface directly.
Accordion behavior is default Gradio - acceptable for demo.

---

## How to Report Bugs

1. Create `docs/bugs/P{N}_{SHORT_NAME}.md`
2. Include: Symptom, Root Cause, Fix Plan, Test Plan
3. Update this index
4. Priority: P0=blocker, P1=important, P2=UX, P3=edge case
