# Technical Debt Registry

> **Last Updated**: 2025-12-06

This document tracks all known technical debt items in the DeepBoner codebase.

## Summary Dashboard

| Category | Open | In Progress | Resolved |
|----------|------|-------------|----------|
| Architecture | 3 | 0 | 0 |
| Code Quality | 4 | 0 | 0 |
| Testing | 2 | 0 | 0 |
| Documentation | 2 | 0 | 0 |
| Performance | 2 | 0 | 0 |
| Dependencies | 1 | 0 | 0 |
| **Total** | **14** | **0** | **0** |

---

## Architecture

### DEBT-001: Duplicate Agent Guide Files

**Category:** Architecture
**Severity:** Low
**Added:** 2025-12-06
**Status:** Open

**Description:**
CLAUDE.md, AGENTS.md, and GEMINI.md contain ~95% identical content. This violates DRY (Don't Repeat Yourself) and makes maintenance difficult.

**Impact:**
- Changes must be made in 3 places
- Risk of documentation drift
- Confusion about which file is canonical

**Current Workaround:**
Manual synchronization when updating.

**Proposed Solution:**
1. Keep CLAUDE.md as the canonical reference
2. Make AGENTS.md and GEMINI.md symlinks or include-references
3. Or consolidate into single DEVELOPMENT.md

**Effort Estimate:** S

---

### DEBT-002: Reserved but Empty Directories

**Category:** Architecture
**Severity:** Low
**Added:** 2025-12-06
**Status:** Open

**Description:**
`src/database_services/` and `src/retrieval_factory/` exist but are empty placeholders for future features.

**Impact:**
- Confusion about project structure
- Empty imports may cause issues

**Current Workaround:**
Document as "reserved" in component inventory.

**Proposed Solution:**
Either implement the features or remove the directories.

**Effort Estimate:** S

---

### DEBT-003: Experimental LangGraph Orchestrator

**Category:** Architecture
**Severity:** Medium
**Added:** 2025-12-06
**Status:** Open

**Description:**
`src/orchestrators/langgraph_orchestrator.py` is marked as experimental and may not be fully tested or integrated.

**Impact:**
- Unclear which orchestrator is preferred
- May have untested edge cases
- Maintenance burden of two orchestrators

**Current Workaround:**
Default to AdvancedOrchestrator in production.

**Proposed Solution:**
Either promote to production status with full testing, or deprecate and remove.

**Effort Estimate:** M

---

## Code Quality

### DEBT-004: Complex Orchestrator Logic

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

### DEBT-005: Magic Numbers in Code

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

### DEBT-006: Global Singleton Pattern

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

### DEBT-007: ClinicalTrials Uses requests Instead of httpx

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

### DEBT-008: Integration Tests Require Real APIs

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

### DEBT-009: Incomplete E2E Test Coverage

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

### DEBT-010: Outdated Inline Comments

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

### DEBT-011: Missing API Documentation

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

### DEBT-012: Model Loading on First Request

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

### DEBT-013: No Connection Pooling

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

### DEBT-014: Pinned Beta Dependencies

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

*No items resolved yet.*

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
