# Technical Debt Registry

> **Last Updated**: 2025-12-12

This document tracks all known technical debt items in the DeepBoner codebase.

## Summary Dashboard

| Category | Open | In Progress | Resolved |
|----------|------|-------------|----------|
| Architecture | 0 | 0 | 2 |
| Code Quality | 4 | 0 | 0 |
| Testing | 2 | 0 | 0 |
| Documentation | 2 | 0 | 0 |
| Performance | 2 | 0 | 0 |
| Dependencies | 1 | 0 | 0 |
| **Total** | **11** | **0** | **2** |

---

## Code Quality

### DEBT-003: Complex Orchestrator Logic

**Category:** Code Quality
**Severity:** Medium
**Added:** 2025-12-06
**Status:** Open

**Description:**
`src/orchestrators/advanced.py` has complex branching logic that required disabling pylint rules (PLR0912, PLR0913).

**Impact:**
- Difficult to understand and maintain
- Higher bug risk
- Harder to test comprehensively

**Current Workaround:**
Suppressed linter warnings with explicit ignores.

**Proposed Solution:**
Refactor into smaller, focused methods. Consider command pattern for orchestration steps.

**Effort Estimate:** L

---

### DEBT-004: Magic Numbers in Code

**Category:** Code Quality
**Severity:** Low
**Added:** 2025-12-06
**Status:** Open

**Description:**
Some statistical constants and thresholds are hardcoded (e.g., p-values, score thresholds), requiring PLR2004 ignore.

**Impact:**
- Difficult to tune parameters
- Magic numbers obscure intent

**Current Workaround:**
Documented with comments where used.

**Proposed Solution:**
Move to configuration or constants module with documentation.

**Effort Estimate:** S

---

### DEBT-005: Global Singleton Pattern

**Category:** Code Quality
**Severity:** Low
**Added:** 2025-12-06
**Status:** Open

**Description:**
Settings uses a singleton pattern (`settings = get_settings()`), requiring PLW0603 ignore.

**Impact:**
- Harder to test with different configurations
- Global state can cause issues

**Current Workaround:**
Test fixtures override settings.

**Proposed Solution:**
Consider dependency injection for settings, especially in tests.

**Effort Estimate:** M

---

### DEBT-006: ClinicalTrials Uses requests Instead of httpx

**Category:** Code Quality
**Severity:** Low
**Added:** 2025-12-06
**Status:** Open

**Description:**
`src/tools/clinicaltrials.py` uses `requests` library while rest of codebase uses `httpx` because ClinicalTrials.gov WAF blocks httpx.

**Impact:**
- Inconsistent HTTP client usage
- Two libraries for same purpose

**Current Workaround:**
Documented in code comments and pyproject.toml.

**Proposed Solution:**
1. Investigate httpx headers/options that work with WAF
2. Or accept this as necessary divergence and document

**Effort Estimate:** M

---

## Testing

### DEBT-007: Integration Tests Require Real APIs

**Category:** Testing
**Severity:** Medium
**Added:** 2025-12-06
**Status:** Open

**Description:**
Integration tests marked with `@pytest.mark.integration` make real API calls, which can be slow and flaky.

**Impact:**
- Slow CI runs
- Flaky tests due to network issues
- Rate limit risks

**Current Workaround:**
Integration tests are not run in CI by default.

**Proposed Solution:**
1. Use VCR-style recording for reproducible tests
2. Set up isolated test environment
3. Better mock infrastructure for external APIs

**Effort Estimate:** L

---

### DEBT-008: Incomplete E2E Test Coverage

**Category:** Testing
**Severity:** Medium
**Added:** 2025-12-06
**Status:** Open

**Description:**
End-to-end tests exist but don't cover all user scenarios, especially error paths.

**Impact:**
- Production bugs may not be caught in testing
- Edge cases untested

**Current Workaround:**
Manual testing before releases.

**Proposed Solution:**
Expand E2E test suite with more scenarios, especially:
- Error handling
- Rate limit recovery
- Multiple iterations

**Effort Estimate:** L

---

## Documentation

### DEBT-009: Outdated Inline Comments

**Category:** Documentation
**Severity:** Low
**Added:** 2025-12-06
**Status:** Open

**Description:**
Some code comments may reference old architecture or removed features from rapid hackathon development.

**Impact:**
- Confusion when reading code
- Comments don't match implementation

**Current Workaround:**
None - requires manual review.

**Proposed Solution:**
Systematic review of comments during code review process.

**Effort Estimate:** M

---

### DEBT-010: Missing API Documentation

**Category:** Documentation
**Severity:** Low
**Added:** 2025-12-06
**Status:** Open

**Description:**
No formal API documentation (e.g., Sphinx-generated) for public interfaces.

**Impact:**
- Developers must read source code
- Hard to know public vs internal APIs

**Current Workaround:**
Docstrings in code serve as documentation.

**Proposed Solution:**
Consider generating API docs with Sphinx or mkdocs.

**Effort Estimate:** M

---

## Performance

### DEBT-011: Model Loading on First Request

**Category:** Performance
**Severity:** Low
**Added:** 2025-12-06
**Status:** Open

**Description:**
Sentence-transformers model is loaded on first query, causing slow initial response.

**Impact:**
- First query takes 30+ seconds
- Poor user experience on first use

**Current Workaround:**
Docker pre-downloads the model during build.

**Proposed Solution:**
1. Pre-warm model on application startup
2. Or accept cold start with loading indicator

**Effort Estimate:** S

---

### DEBT-012: No Connection Pooling

**Category:** Performance
**Severity:** Low
**Added:** 2025-12-06
**Status:** Open

**Description:**
External API calls may not fully utilize connection pooling.

**Impact:**
- Slower requests due to connection overhead
- Higher latency under load

**Current Workaround:**
httpx AsyncClient provides some pooling.

**Proposed Solution:**
Audit and optimize connection handling for external APIs.

**Effort Estimate:** S

---

## Dependencies

### DEBT-013: Pinned Beta Dependencies

**Category:** Dependencies
**Severity:** Medium
**Added:** 2025-12-06
**Status:** Open

**Description:**
`agent-framework-core==1.0.0b*` is a beta release, pinned to avoid breaking changes.

**Impact:**
- May miss bug fixes and improvements
- Beta software may have stability issues

**Current Workaround:**
Version pinning with explicit documentation.

**Proposed Solution:**
1. Monitor for stable release
2. Upgrade and test when 1.0.0 releases
3. Add integration tests specific to agent framework

**Effort Estimate:** M

---

## Resolved Items

### DEBT-001: Reserved but Empty Directories ✅

**Category:** Architecture
**Severity:** Low
**Added:** 2025-12-06
**Resolved:** 2025-12-12
**Status:** Resolved

**Description:**
`src/database_services/` and `src/retrieval_factory/` existed as empty placeholders for future features.

**Resolution:**
Removed the empty directories. The Microsoft Agent Framework provides pluggable memory modules (Redis, Pinecone, Qdrant, etc.) that supersede any custom implementation needs. Future persistence requirements can use the framework's built-in capabilities.

**PR:** Technical debt cleanup

---

### DEBT-002: Experimental LangGraph Orchestrator ✅

**Category:** Architecture
**Severity:** Medium
**Added:** 2025-12-06
**Resolved:** 2025-12-12
**Status:** Resolved

**Description:**
`src/orchestrators/langgraph_orchestrator.py` was marked as experimental and deprecated.

**Resolution:**
Removed the LangGraph orchestrator and all related code:
- Deleted `src/orchestrators/langgraph_orchestrator.py`
- Deleted `src/agents/graph/` directory (nodes.py, workflow.py, state.py)
- Deleted `src/agents/retrieval_agent.py` (dead code, never wired - see #134)
- Deleted `src/tools/web_search.py` (dead code)
- Removed LangGraph/LangChain dependencies from pyproject.toml
- Moved `Hypothesis` and `Conflict` models from graph/state.py to utils/models.py (these were shared domain models)

The Microsoft Agent Framework's workflow capabilities (graph-based workflows with streaming, checkpointing, human-in-the-loop) supersede what LangGraph was providing. AdvancedOrchestrator is now the sole orchestrator implementation.

**PR:** Technical debt cleanup

---

## How to Update This Registry

### Adding Items

1. Create new section with next DEBT-XXX number
2. Fill in all fields
3. Update summary dashboard

### Resolving Items

1. Change status to "Resolved"
2. Add resolution notes
3. Move to "Resolved Items" section
4. Update summary dashboard

### Review Schedule

- Weekly: Triage new items
- Sprint: Plan debt reduction
- Monthly: Review progress
