# Tech Debt & Bug Fix Specs

**Status:** AWAITING SENIOR REVIEW
**Created:** 2025-12-06

---

## Overview

These specs consolidate all identified bugs, tech debt, and architectural issues into phased, implementable work packages. Each spec is designed to be a single PR with TDD, SOLID, DRY, Gang of Four principles.

**Implementation Order:** SPEC-20 → SPEC-21 → SPEC-22

---

## Spec Index

| Spec | Title | Priority | Effort | Status |
|------|-------|----------|--------|--------|
| [SPEC-20](./SPEC-20-PUBMED-JSON-FIX.md) | PubMed JSON Parsing Fix | P2 | 15 min | READY |
| [SPEC-21](./SPEC-21-MIDDLEWARE-ARCHITECTURE.md) | Middleware Architecture Refactor | P2 | 2 hours | READY |
| [SPEC-22](./SPEC-22-PROGRESS-BAR-REMOVAL.md) | Progress Bar Removal | P3 | 15 min | READY |

**Total Effort:** ~2.5 hours

---

## Why This Order?

### SPEC-20 First (15 min)
- Quickest win
- Fixes a real crash bug
- Builds confidence before larger refactor
- Single file, single PR

### SPEC-21 Second (2 hours)
- The big architectural fix
- Renames confusing folder
- Implements proper MS framework patterns
- Fixes HuggingFace retry bug THE RIGHT WAY
- Adds token tracking

### SPEC-22 Last (15 min)
- Cosmetic only
- Can be deferred if needed
- Easy cleanup

---

## What These Specs Consolidate

These specs replace the scattered documentation in:

| Old Location | Now Covered By |
|--------------|----------------|
| `docs/bugs/p2-hardening-issues.md` Issue 1 | SPEC-20 |
| `docs/bugs/p2-hardening-issues.md` Issue 2 | SPEC-21 |
| `docs/architecture/adr-001-middleware-refactor.md` | SPEC-21 |
| `docs/bugs/p3-progress-bar-positioning.md` | SPEC-22 |

---

## What's NOT In These Specs (Deferred P3)

The following are documented but deferred for later:

1. **OpenTelemetry observability** - Nice to have, not blocking
2. **Thread state serialization** - Nice to have, not blocking
3. **ResearchMemory locks** - Not a bug today (sequential execution)
4. **Error path cleanup** - Minor resource leakage, GC handles it
5. **Per-tool configuration** - Nice to have
6. **Context provider lifecycle** - Nice to have

These remain documented in `docs/bugs/p3-ms-framework-gaps.md` for future work.

---

## Implementation Protocol

For each spec:

1. **Read the spec** - Understand the problem and solution
2. **TDD** - Write failing test first
3. **Implement** - Minimal code to pass tests
4. **Run `make check`** - Lint + typecheck + test
5. **Commit** - Single commit per spec
6. **PR** - One PR per spec with spec number in title

---

## Commit Message Format

```
fix: PubMed JSON parsing (SPEC-20)

Moves JSON parsing inside try/except block to handle API
maintenance pages gracefully. Adds JSONDecodeError handling.

Fixes: production crash on PubMed maintenance pages
```

```
refactor: middleware architecture (SPEC-21)

- Renames src/middleware → src/workflows (accurate naming)
- Creates proper src/middleware with ChatMiddleware implementations
- Implements RetryMiddleware (fixes HuggingFace 429 crashes)
- Implements TokenTrackingMiddleware (enables cost monitoring)
```

```
fix: remove progress bar overlap (SPEC-22)

Removes gr.Progress() from research_agent function.
Gradio's Progress is incompatible with ChatInterface.
Emoji status messages in chat output are retained.
```

---

## Senior Review Checklist

Before implementation, please verify:

- [ ] SPEC-20: Fix approach is correct (move into try/except)
- [ ] SPEC-21: MS middleware pattern is used correctly
- [ ] SPEC-21: RetryMiddleware implementation follows framework conventions
- [ ] SPEC-21: Folder rename won't break anything else
- [ ] SPEC-22: Removing gr.Progress() is the right fix (vs CSS hack)
- [ ] Order of implementation makes sense
- [ ] Nothing critical is missing from these specs

---

## After Implementation

Once all specs are implemented:

1. Archive old docs:
   - `docs/bugs/p2-hardening-issues.md` → Mark as RESOLVED
   - `docs/architecture/adr-001-middleware-refactor.md` → Delete or archive
   - `docs/bugs/p3-progress-bar-positioning.md` → Mark as RESOLVED

2. Update `docs/bugs/active-bugs.md` to reflect completed fixes

3. Consider v0.2.0 release with these fixes
