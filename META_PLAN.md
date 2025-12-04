# META_PLAN: DeepBoner Stabilization Roadmap

**Created**: 2025-12-03
**Status**: Active
**Purpose**: Single source of truth for what to do next before adding features

---

## Executive Summary

**Codebase Health**: PRODUCTION-READY
- 313 tests passing
- No type errors (mypy clean)
- No linting issues (ruff clean)
- 1 open bug (P3 - low priority UX)

**Key Finding**: Architecture is sound. Two high-impact specs are written but not implemented. Documentation is sprawling but mostly accurate.

**Recommendation**: Implement the two pending specs, clean up tech debt, then organize docs.

---

## Current State Assessment

### Documentation Status

| Document | Status | Action |
|----------|--------|--------|
| `docs/STATUS_LLAMAINDEX_INTEGRATION.md` | DONE | Keep as-is |
| `docs/specs/SPEC_13_EVIDENCE_DEDUPLICATION.md` | SPEC DONE, CODE NOT | **Implement** |
| `docs/specs/SPEC_14_CLINICALTRIALS_OUTCOMES.md` | SPEC DONE, CODE NOT | **Implement** |
| `docs/future-roadmap/TOOL_ANALYSIS_CRITICAL.md` | ANALYSIS DONE | Reference for future |
| `docs/ARCHITECTURE.md` | PARTIAL | Expand with diagrams |
| `docs/architecture/system_registry.md` | DONE | Canonical SSOT for wiring |

### Architecture Status

| Component | Status | Notes |
|-----------|--------|-------|
| `src/orchestrators/` | COMPLETE | Factory pattern, protocols |
| `src/clients/` | COMPLETE | OpenAI/HuggingFace working, Anthropic partial (tech debt) |
| `src/tools/` | FUNCTIONAL | Missing deduplication, outcomes extraction |
| `src/agents/` | FUNCTIONAL | All agents wired, some experimental |
| `src/services/` | COMPLETE | Embeddings, RAG, memory all working |

### Open Issues

| Issue | Priority | Effort |
|-------|----------|--------|
| Evidence deduplication (SPEC_13) | HIGH | 3-4 hours |
| ClinicalTrials outcomes (SPEC_14) | HIGH | 2-3 hours |
| Remove Anthropic wiring (P3) | P3 | 1 hour |
| Expand ARCHITECTURE.md | MEDIUM | 2 hours |
| P3 Progress Bar positioning | P3 | 30 min |

---

## The Next 5 Steps

### Step 1: Implement SPEC_13 - Evidence Deduplication
**Priority**: HIGH | **Effort**: 3-4 hours | **Impact**: 30-50% token savings

Currently, PubMed/Europe PMC/OpenAlex return duplicate papers. This wastes tokens and confuses the judge.

**Files to modify**:
- `src/tools/search_handler.py` - Add `extract_paper_id()` and dedup logic
- `src/tools/openalex.py` - Extract PMID from metadata
- `tests/unit/tools/test_search_handler.py` - Add dedup tests

**Spec**: `docs/specs/SPEC_13_EVIDENCE_DEDUPLICATION.md`

---

### Step 2: Implement SPEC_14 - ClinicalTrials Outcomes
**Priority**: HIGH | **Effort**: 2-3 hours | **Impact**: Critical efficacy data

Currently, we don't extract outcome measures or results status from trials.

**Files to modify**:
- `src/tools/clinicaltrials.py` - Add OutcomesModule, HasResults fields
- `tests/unit/tools/test_clinicaltrials.py` - Add outcome tests

**Spec**: `docs/specs/SPEC_14_CLINICALTRIALS_OUTCOMES.md`

---

### Step 3: Remove Anthropic Tech Debt
**Priority**: P3 | **Effort**: 1 hour | **Impact**: Code clarity

Anthropic is partially wired but NOT supported (no embeddings API). Creates confusion.

**Files to modify**:
- `src/utils/config.py` - Remove ANTHROPIC_API_KEY handling
- `src/clients/factory.py` - Remove Anthropic case
- `src/agent_factory/judges.py` - Remove Anthropic references
- `CLAUDE.md` - Update documentation

**Doc**: `docs/future-roadmap/P3_REMOVE_ANTHROPIC_PARTIAL_WIRING.md`

---

### Step 4: Documentation Consolidation
**Priority**: MEDIUM | **Effort**: 2 hours | **Impact**: Developer clarity

Create single canonical architecture doc with:
- System flow diagram
- Component interaction map
- Error handling patterns
- Deployment topology

**Output**: Expanded `docs/ARCHITECTURE.md`

---

### Step 5: Create Implementation Status Matrix
**Priority**: LOW | **Effort**: 1 hour | **Impact**: Project tracking

Update `docs/index.md` or create `docs/IMPLEMENTATION_STATUS.md` with:
- Phase completion tracking (14 phases)
- Post-hackathon roadmap status
- Clear DONE vs TODO markers

---

## What NOT To Do (Yet)

1. **Add new features** - Stabilize first
2. **Add new LLM providers** - OpenAI/HuggingFace cover all use cases
3. **Build Neo4j knowledge graph** - Overkill for current needs
4. **Implement full-text retrieval** - Phase 15+ (after stabilization)
5. **Add MeSH term expansion** - Phase 15+ (optimization)

---

## Documentation Sprawl Analysis

**Total docs**: 91 markdown files in `docs/`

**Organization**:
```
docs/
├── architecture/      # Canonical architecture docs (4 files)
├── brainstorming/     # Ideas, not commitments (6 files)
├── bugs/              # Active bugs + archive (25+ files)
├── decisions/         # ADRs from Nov 2025 (2 files)
├── development/       # Dev guides (1 file)
├── future-roadmap/    # Deferred work (5 files)
├── guides/            # User guides (1 file)
├── implementation/    # Phase docs 1-14 (15 files)
├── specs/             # Feature specs (4 files)
├── ARCHITECTURE.md    # High-level overview
└── index.md           # Entry point
```

**Recommendation**: Structure is fine. Main issue is SPEC_13/SPEC_14 not implemented despite detailed specs.

---

## Success Criteria

After completing Steps 1-5:

- [ ] Evidence deduplication reduces duplicate papers by 80%+
- [ ] ClinicalTrials shows outcome measures and results status
- [ ] No Anthropic references in codebase
- [ ] ARCHITECTURE.md has flow diagrams
- [ ] All 14 implementation phases marked DONE/TODO

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-03 | Implement specs before doc cleanup | Specs are ready, high impact |
| 2025-12-03 | Remove Anthropic over adding Gemini | Tech debt cleanup > new features |
| 2025-12-03 | Defer full-text retrieval | Stabilize core first |

---

## References

- `docs/architecture/system_registry.md` - Decorator/marker/tool wiring SSOT
- `docs/bugs/ACTIVE_BUGS.md` - Current bug tracking
- `CLAUDE.md` - Development commands and patterns
