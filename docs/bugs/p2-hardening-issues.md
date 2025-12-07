# P2: Hardening Issues

**Date:** 2025-12-06
**Priority:** P2 (Should fix soon)

---

## Issue 1: PubMed JSON Parsing Crash

**Status:** SPEC-20 CREATED
**File:** `src/tools/pubmed.py:88`

The PubMed search tool crashes when the API returns non-JSON responses (maintenance pages, error pages). The JSON parsing happens outside the try/except block.

**Resolution:** See [SPEC-20: PubMed JSON Parsing Fix](../specs/SPEC-20-PUBMED-JSON-FIX.md)

---

## Issue 2: HuggingFace Client Missing Retry Logic

**Status:** SPEC-21 CREATED
**File:** `src/clients/huggingface.py`

The HuggingFaceChatClient has no retry logic for transient errors (429 rate limits, 500 server errors). When the API returns a 429, the entire research workflow crashes.

**Resolution:** See [SPEC-21: Middleware Architecture Refactor](../specs/SPEC-21-MIDDLEWARE-ARCHITECTURE.md)

---

## Issue 3: Misleading Middleware Folder Name

**Status:** SPEC-21 CREATED
**File:** `src/middleware/`

The `src/middleware/` folder contains `SubIterationMiddleware`, which is actually a workflow pattern (team→judge loop), not interceptor middleware. This is confusing and misleading.

**Resolution:** See [SPEC-21: Middleware Architecture Refactor](../specs/SPEC-21-MIDDLEWARE-ARCHITECTURE.md)

---

## Related Documentation

- [SPEC-20: PubMed JSON Parsing Fix](../specs/SPEC-20-PUBMED-JSON-FIX.md)
- [SPEC-21: Middleware Architecture Refactor](../specs/SPEC-21-MIDDLEWARE-ARCHITECTURE.md)
- [P3: MS Framework Gaps](./p3-ms-framework-gaps.md)
