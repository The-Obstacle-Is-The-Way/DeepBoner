# ADR-001: Middleware Architecture Refactor

**Status:** ACCEPTED
**Date:** 2025-12-06
**Decision Makers:** Development Team

---

## Context

The current `src/middleware/` folder is misleadingly named. It contains `SubIterationMiddleware`, which implements a workflow pattern (team→judge loop), not the interceptor middleware pattern used by Microsoft Agent Framework.

Additionally, we're missing proper middleware implementations for:
- Retry logic on transient errors (429, 500, 502, 503, 504)
- Token usage tracking for cost monitoring

---

## Decision

1. **Rename `src/middleware/` to `src/workflows/`** to accurately reflect what it contains
2. **Create new `src/middleware/` with proper MS-pattern middleware:**
   - `RetryMiddleware(ChatMiddleware)` - exponential backoff retry
   - `TokenTrackingMiddleware(ChatMiddleware)` - token usage logging

---

## Consequences

### Positive
- Clearer codebase organization
- Proper use of MS Agent Framework patterns
- HuggingFace 429 crashes will be handled gracefully
- Token usage will be visible for cost monitoring

### Negative
- Requires updating imports in `src/orchestrators/hierarchical.py`
- One-time migration effort

### Neutral
- Aligns with Microsoft Agent Framework conventions

---

## Implementation

See [SPEC-21: Middleware Architecture Refactor](../specs/SPEC-21-MIDDLEWARE-ARCHITECTURE.md) for detailed implementation steps.

---

## References

- Microsoft Agent Framework `_middleware.py`
- [P2 Hardening Issues](../bugs/p2-hardening-issues.md) Issue 2 & 3
