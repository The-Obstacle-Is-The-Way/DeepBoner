# Senior Agent Audit Request: DeepBoner Codebase Bug Hunt

**Date**: 2025-11-28
**Requesting Agent**: Claude (Opus)
**Purpose**: Comprehensive bug audit and verification of P0_CRITICAL_BUGS.md

---

## Your Mission

You are a senior software engineer performing a comprehensive audit of the DeepBoner codebase. Your goals:

1. **VERIFY** the 4 bugs documented in `docs/bugs/P0_CRITICAL_BUGS.md` are accurately described
2. **FIND** any additional bugs (P0-P4) that could affect the demo
3. **TRACE** the complete code paths for Simple and Advanced modes
4. **IDENTIFY** any silent failures, race conditions, or edge cases

---

## Context: What DeepBoner Does

DeepBoner is a Gradio-based biomedical research agent that:
1. Takes a research question from user
2. Searches PubMed, ClinicalTrials.gov, Europe PMC
3. Uses an LLM "judge" to evaluate if evidence is sufficient
4. Either loops for more evidence or synthesizes a final report

**Two Modes**:
- **Simple**: Linear orchestrator with search → judge → report loop
- **Advanced**: Magentic multi-agent with SearchAgent, JudgeAgent, HypothesisAgent, ReportAgent

**Three Backend Options**:
- Free tier: HuggingFace Inference API (Llama/Mistral)
- OpenAI: User-provided or env var key
- Anthropic: User-provided or env var key (Simple mode only)

---

## Files to Audit (Priority Order)

### Critical Path Files:
1. `src/app.py` - Gradio UI, entry point, key routing
2. `src/orchestrator.py` - Simple mode main loop
3. `src/orchestrator_factory.py` - Mode selection and orchestrator creation
4. `src/orchestrator_magentic.py` - Advanced mode implementation
5. `src/services/embeddings.py` - Deduplication singleton (KNOWN BUG)
6. `src/agent_factory/judges.py` - LLM judge handlers (HF, OpenAI, Anthropic)

### Supporting Files:
7. `src/tools/search_handler.py` - Parallel search orchestration
8. `src/tools/pubmed.py` - PubMed API integration
9. `src/tools/clinicaltrials.py` - ClinicalTrials.gov API
10. `src/tools/europepmc.py` - Europe PMC API
11. `src/agents/magentic_agents.py` - Agent factories (KNOWN BUG: hardcoded env key)
12. `src/utils/config.py` - Settings and configuration
13. `src/utils/models.py` - Data models (Evidence, Citation, etc.)

---

## Known Bugs to Verify

### Bug 1: Free Tier LLM Quota Exhausted
**Claim**: HuggingFace Inference returns 402, all 3 fallback models fail
**Verify**:
- Check `src/agent_factory/judges.py` class `HFInferenceJudgeHandler`
- Trace the fallback chain: Llama → Mistral → Zephyr
- Confirm what happens when ALL fail (does it return default "continue"?)
- Check if the error message reaches the user or is swallowed

### Bug 2: Evidence Counter Shows 0 After Dedup
**Claim**: `_deduplicate_and_rank()` can return empty list, losing all evidence
**Verify**:
- Check `src/orchestrator.py` lines 97-114 and 219
- Trace what happens if `embeddings.deduplicate()` returns `[]`
- Is there defensive handling? Does exception handler catch this?
- Could this be a race condition in async code?

### Bug 3: API Key Not Passed to Advanced Mode
**Claim**: User's API key from Gradio is never passed to MagenticOrchestrator
**Verify**:
- Trace: `app.py:research_agent()` → `configure_orchestrator()` → `orchestrator_factory.py`
- Check if `user_api_key` is passed to `create_orchestrator()`
- Check if `MagenticOrchestrator.__init__()` receives a key
- Check `src/agents/magentic_agents.py` - do agents use `settings.openai_api_key`?

### Bug 4: Singleton EmbeddingService Cross-Session Pollution
**Claim**: ChromaDB collection persists across requests, causing false duplicates
**Verify**:
- Check `src/services/embeddings.py` singleton pattern
- Is `_embedding_service` ever reset?
- What happens to ChromaDB collection between Gradio requests?
- Could this cause "Found 20 new sources (0 total)"?

---

## Additional Bug Categories to Search For

### A. Error Handling Gaps
- [ ] Silent `except: pass` blocks
- [ ] Exceptions logged but not re-raised
- [ ] Missing error messages to user
- [ ] Swallowed API errors

### B. Async/Concurrency Issues
- [ ] Race conditions in parallel searches
- [ ] Shared mutable state across async calls
- [ ] Missing `await` keywords
- [ ] Event loop blocking (sync code in async context)

### C. API Integration Bugs
- [ ] Missing rate limiting
- [ ] Hardcoded timeouts that are too short
- [ ] XML/JSON parsing failures not handled
- [ ] Empty response handling

### D. State Management Issues
- [ ] Global singletons that should be session-scoped
- [ ] Gradio state not properly isolated between users
- [ ] Memory leaks from accumulated data

### E. Configuration Bugs
- [ ] Missing env var defaults
- [ ] Type mismatches in settings
- [ ] Hardcoded values that should be configurable

### F. UI/UX Bugs
- [ ] Streaming not working properly
- [ ] Progress messages misleading
- [ ] Examples not matching actual functionality
- [ ] Error messages not user-friendly

---

## Output Format

Please produce a report with:

### 1. Verification of Known Bugs
For each of the 4 bugs in P0_CRITICAL_BUGS.md:
- **CONFIRMED** or **INCORRECT** or **PARTIALLY CORRECT**
- Exact file:line references
- Any corrections or additional details

### 2. New Bugs Found
For each new bug:
```
## Bug N: [Title]
**Priority**: P0/P1/P2/P3/P4
**File**: path/to/file.py:line
**Symptoms**: What the user sees
**Root Cause**: Technical explanation
**Code**:
```python
# The buggy code
```
**Fix**:
```python
# The corrected code
```
```

### 3. Code Quality Concerns
Any patterns that aren't bugs but could cause issues:
- Technical debt
- Missing tests for critical paths
- Unclear error handling

### 4. Recommended Fix Order
Prioritized list of what to fix first for a working demo.

---

## Commands to Help Your Investigation

```bash
# Run the tests
make check

# Test search works
uv run python -c "
import asyncio
from src.tools.pubmed import PubMedTool
async def test():
    tool = PubMedTool()
    results = await tool.search('female libido', 5)
    print(f'Found {len(results)} results')
asyncio.run(test())
"

# Test HF inference (will show 402 if quota exhausted)
uv run python -c "
from huggingface_hub import InferenceClient
client = InferenceClient()
try:
    resp = client.chat_completion(
        messages=[{'role': 'user', 'content': 'Hi'}],
        model='meta-llama/Llama-3.1-8B-Instruct',
        max_tokens=10
    )
    print(resp)
except Exception as e:
    print(f'Error: {e}')
"

# Test full orchestrator (simple mode)
uv run python -c "
import asyncio
from src.app import configure_orchestrator
async def test():
    orch, backend = configure_orchestrator(use_mock=True, mode='simple')
    print(f'Backend: {backend}')
    async for event in orch.run('test query'):
        print(f'{event.type}: {event.message[:50] if event.message else \"\"}'[:60])
asyncio.run(test())
"

# Check for hardcoded API keys (security)
grep -r "sk-" src/ --include="*.py" | grep -v "sk-..." | grep -v "sk-ant-..."

# Find all singletons
grep -r "_.*: .* | None = None" src/ --include="*.py"

# Find all except blocks
grep -rn "except.*:" src/ --include="*.py" | head -50
```

---

## Important Notes

1. **DO NOT fix bugs** - just document them
2. **Be thorough** - check edge cases and error paths
3. **Be specific** - include file:line references
4. **Be skeptical** - verify claims in P0_CRITICAL_BUGS.md independently
5. **Think like a user** - what would break the demo experience?

The hackathon deadline is approaching. We need a working demo. Your audit will determine what gets fixed first.

---

## Deliverable

A comprehensive markdown report that:
1. Confirms or corrects the 4 known bugs
2. Lists any new bugs found (with priority)
3. Recommends the optimal fix order
4. Can be saved as `docs/bugs/SENIOR_AUDIT_RESULTS.md`
