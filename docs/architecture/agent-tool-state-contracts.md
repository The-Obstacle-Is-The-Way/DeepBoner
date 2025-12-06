# Agent-Tool-State Contract Registry

> **Status**: Canonical Source of Truth
> **Last Updated**: 2025-12-06
> **Purpose**: Developer reference for multi-agent coordination

This document defines the exact contracts between agents, tools, and shared state. Use this when:
- Adding new agents or tools
- Modifying agent behavior
- Debugging coordination issues
- Understanding "if I change X, what breaks?"

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Agent Contracts](#agent-contracts)
3. [Judge Decision Criteria](#judge-decision-criteria)
4. [Shared State (ResearchMemory)](#shared-state-researchmemory)
5. [Tool Contracts](#tool-contracts)
6. [Event Flow](#event-flow)
7. [Break Conditions](#break-conditions)
8. [Dependency Matrix](#dependency-matrix)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (AdvancedOrchestrator)               │
│                                                                      │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐               │
│  │   Manager   │──▶│   Agents    │──▶│   Memory    │               │
│  │  (Magentic) │   │ (ChatAgent) │   │(ResearchMem)│               │
│  └─────────────┘   └─────────────┘   └─────────────┘               │
│         │                │                   │                      │
│         │                ▼                   ▼                      │
│         │         ┌─────────────┐   ┌─────────────┐                │
│         └────────▶│    Tools    │──▶│  Embeddings │                │
│                   │(@ai_function)│   │  (ChromaDB) │                │
│                   └─────────────┘   └─────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent Inventory

| Agent | File | Role | Tools |
|-------|------|------|-------|
| **SearchAgent** | `magentic_agents.py` | Evidence gathering | search_pubmed, search_clinical_trials, search_preprints |
| **JudgeAgent** | `magentic_agents.py` | Evidence evaluation | None (LLM only) |
| **HypothesisAgent** | `magentic_agents.py` | Mechanism generation | None (LLM only) |
| **ReportAgent** | `magentic_agents.py` | Report synthesis | get_bibliography |
| **RetrievalAgent** | `retrieval_agent.py` | Web search | search_web |

---

## Agent Contracts

### SearchAgent

**Factory**: `create_search_agent(chat_client, domain, api_key) -> ChatAgent`

#### Input
```python
# Manager instruction (string)
"Search for testosterone and libido mechanisms in peer-reviewed literature"
```

#### Output
```python
# ChatMessage with:
message.text = """
Found 15 sources (12 new added to context):
- [Title 1](url): Abstract excerpt...
- [Title 2](url): Abstract excerpt...
"""
message.additional_properties = {
    "evidence": [Evidence.model_dump(), ...]
}
```

#### State Access

| Operation | Key | Type | Description |
|-----------|-----|------|-------------|
| **READ** | `memory.query` | str | Current research question |
| **READ** | `memory.evidence_ids` | list[str] | Existing evidence URLs |
| **WRITE** | `memory._evidence_cache` | dict[str, Evidence] | Caches Evidence objects |
| **WRITE** | `memory.evidence_ids` | list[str] | Appends new URLs |
| **WRITE** | `embedding_service` | VectorDB | Stores embeddings |

#### Side Effects
1. Calls external APIs (PubMed, ClinicalTrials, Europe PMC)
2. Deduplicates via semantic similarity (0.9 threshold)
3. Stores in vector database

#### Error Behavior
- API failure → Returns "No results found for: {query}"
- Rate limit → Raises `RateLimitError` (caught by orchestrator)

---

### JudgeAgent

**Factory**: `create_judge_agent(chat_client, domain, api_key) -> ChatAgent`

#### Input
```python
# Manager instruction with evidence context
"Evaluate if we have sufficient evidence to answer: {query}"
# + Evidence list in context
```

#### Output
```python
# ChatMessage with:
message.text = """
## Assessment
✅ SUFFICIENT EVIDENCE (confidence: 85%). STOP SEARCHING.

### Scores
- Mechanism: 8/10
- Clinical: 7/10

### Reasoning
Strong evidence for testosterone-AR pathway...
"""
message.additional_properties = {
    "assessment": JudgeAssessment.model_dump()
}
```

#### State Access

| Operation | Key | Type | Description |
|-----------|-----|------|-------------|
| **READ** | Evidence from context | list[Evidence] | Passed by Manager |
| **WRITE** | None | - | Read-only evaluation |

#### Side Effects
- None (pure evaluation)

#### Critical Output Signal
- `"✅ SUFFICIENT EVIDENCE"` → Manager delegates to ReportAgent
- `"❌ INSUFFICIENT"` → Manager calls SearchAgent with suggested queries

---

### HypothesisAgent

**Factory**: `create_hypothesis_agent(chat_client, domain, api_key) -> ChatAgent`

#### Input
```python
# Manager instruction
"Generate mechanistic hypotheses for: {query}"
```

#### Output
```python
# ChatMessage with:
message.text = """
## Hypothesis 1 (Confidence: 75%)
**Mechanism**: Testosterone → Androgen Receptor → BDNF → Libido
**Suggested searches**: testosterone BDNF, androgen receptor signaling

## Primary Hypothesis
Testosterone → AR → dopamine release → reward pathway

## Knowledge Gaps
- Dose-response relationship unclear
"""
message.additional_properties = {
    "assessment": HypothesisAssessment.model_dump()
}
```

#### State Access

| Operation | Key | Type | Description |
|-----------|-----|------|-------------|
| **READ** | `memory.query` | str | Research question |
| **READ** | Evidence from context | list[Evidence] | Current evidence |
| **WRITE** | `evidence_store["hypotheses"]` | list | Appends hypotheses |

---

### ReportAgent

**Factory**: `create_report_agent(chat_client, domain, api_key) -> ChatAgent`

#### Input
```python
# Manager instruction
"Generate final research report for: {query}"
```

#### Output
```python
# ChatMessage with:
message.text = ResearchReport.to_markdown()  # Full markdown report
message.additional_properties = {
    "report": ResearchReport.model_dump()
}
```

#### State Access

| Operation | Key | Type | Description |
|-----------|-----|------|-------------|
| **READ** | `memory.get_all_evidence()` | list[Evidence] | All collected evidence |
| **READ** | `evidence_store["hypotheses"]` | list | Generated hypotheses |
| **READ** | `evidence_store["last_assessment"]` | JudgeAssessment | Final assessment |
| **WRITE** | `evidence_store["final_report"]` | ResearchReport | Stores report |

#### Tool: get_bibliography()
```python
@ai_function
def get_bibliography() -> str:
    """Returns formatted reference list from all evidence."""
    evidence = state.memory.get_all_evidence()
    return format_as_references(evidence)
```

---

## Judge Decision Criteria

### Scoring Dimensions

**Mechanism Score (0-10)**

| Score | Meaning |
|-------|---------|
| 0-3 | Minimal mechanism understanding |
| 4-5 | Partial mechanism (some targets identified) |
| 6-7 | Clear mechanism (targets + pathways) |
| 8-9 | Comprehensive (multiple pathways, regulation) |
| 10 | Complete understanding |

**Clinical Evidence Score (0-10)**

| Score | Meaning |
|-------|---------|
| 0-3 | Preclinical only or weak human evidence |
| 4-5 | Some human evidence (small trials, case reports) |
| 6-7 | Strong human evidence (RCTs) |
| 8-9 | Robust (meta-analysis, large RCTs) |
| 10 | Definitive clinical proof |

### Sufficiency Decision

```python
# SUFFICIENT (recommendation="synthesize")
if (
    confidence >= 0.7  # 70%
    and mechanism_score >= 6
    and clinical_evidence_score >= 6
):
    sufficient = True
    recommendation = "synthesize"

# INSUFFICIENT (recommendation="continue")
else:
    sufficient = False
    recommendation = "continue"
    next_search_queries = ["suggested query 1", "suggested query 2"]
```

### JudgeAssessment Model

```python
class JudgeAssessment(BaseModel):
    details: AssessmentDetails
        mechanism_score: int          # 0-10
        mechanism_reasoning: str      # min 10 chars
        clinical_evidence_score: int  # 0-10
        clinical_reasoning: str       # min 10 chars
        drug_candidates: list[str]
        key_findings: list[str]

    sufficient: bool                  # Ready for synthesis?
    confidence: float                 # 0.0-1.0
    recommendation: Literal["continue", "synthesize"]
    next_search_queries: list[str]    # If continue
    reasoning: str                    # min 20 chars
```

---

## Shared State (ResearchMemory)

### Initialization

```python
# Per-query isolation via ContextVar
state = init_magentic_state(query, embedding_service)
# Returns MagenticState wrapping ResearchMemory
```

### Memory Structure

```python
class ResearchMemory:
    query: str                              # Research question
    hypotheses: list[Hypothesis]            # Generated hypotheses
    conflicts: list[Conflict]               # Detected conflicts
    evidence_ids: list[str]                 # URLs (unique keys)
    _evidence_cache: dict[str, Evidence]    # URL -> Evidence
    iteration_count: int                    # Current iteration
    _embedding_service: EmbeddingServiceProtocol
```

### Key Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `store_evidence(evidence)` | `list[str]` | Store with dedup, return new IDs |
| `get_all_evidence()` | `list[Evidence]` | All accumulated evidence |
| `get_relevant_evidence(n)` | `list[Evidence]` | Top N by semantic similarity |
| `get_context_summary()` | `str` | Markdown summary for fallback |
| `add_hypothesis(h)` | `None` | Append hypothesis |
| `get_confirmed_hypotheses()` | `list[Hypothesis]` | Confidence > 0.8 |

### State Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  ResearchMemory initialized (empty)                          │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
SearchAgent ──▶ store_evidence([Evidence]) ──▶ evidence_ids grows
    │
    ▼
JudgeAgent ──▶ reads evidence from context ──▶ returns assessment
    │
    ├─── INSUFFICIENT ──▶ SearchAgent (with next_search_queries)
    │
    └─── SUFFICIENT ──▶ ReportAgent
                              │
                              ▼
                       get_all_evidence() ──▶ ResearchReport
```

---

## Tool Contracts

### search_pubmed

**File**: `src/agents/tools.py`

```python
@ai_function
async def search_pubmed(query: str, max_results: int = 10) -> str:
    """Search PubMed for biomedical research papers."""
```

| Aspect | Value |
|--------|-------|
| External API | NCBI E-utilities |
| Rate Limit | 3/sec (10/sec with NCBI_API_KEY) |
| Output | Formatted string with titles/abstracts |
| Side Effect | Stores Evidence in memory |

### search_clinical_trials

```python
@ai_function
async def search_clinical_trials(query: str, max_results: int = 10) -> str:
    """Search ClinicalTrials.gov for clinical studies."""
```

| Aspect | Value |
|--------|-------|
| External API | ClinicalTrials.gov (uses `requests` not httpx) |
| Rate Limit | Standard HTTP limits |
| Output | Trial status, conditions, interventions |
| Side Effect | Stores Evidence in memory |

### search_preprints

```python
@ai_function
async def search_preprints(query: str, max_results: int = 10) -> str:
    """Search Europe PMC for preprints and papers."""
```

| Aspect | Value |
|--------|-------|
| External API | Europe PMC REST API |
| Output | Papers with PMIDs, DOIs |
| Side Effect | Stores Evidence in memory |

### get_bibliography

```python
@ai_function
def get_bibliography() -> str:
    """Get formatted reference list from all collected evidence."""
```

| Aspect | Value |
|--------|-------|
| External API | None |
| Reads | `memory.get_all_evidence()` |
| Output | Numbered reference list |

### search_web

```python
@ai_function
async def search_web(query: str, max_results: int = 10) -> str:
    """Search web using DuckDuckGo."""
```

| Aspect | Value |
|--------|-------|
| External API | DuckDuckGo |
| Output | Web results with URLs |
| Side Effect | Stores Evidence in memory |

---

## Event Flow

### AgentEvent Types

| Type | When Emitted | Data |
|------|--------------|------|
| `started` | Workflow begins | None |
| `thinking` | Before first agent event | None |
| `searching` | SearchAgent active | agent_id |
| `search_complete` | SearchAgent done | evidence count |
| `judging` | JudgeAgent active | agent_id |
| `judge_complete` | JudgeAgent done | assessment |
| `hypothesizing` | HypothesisAgent active | agent_id |
| `synthesizing` | ReportAgent active | agent_id |
| `streaming` | Real-time text | text, agent_id |
| `complete` | Workflow done | report, iterations |
| `error` | Error occurred | error message |
| `progress` | Status update | status message |

### Typical Sequence

```
1. started → "Starting research..."
2. progress → "Loading embedding service..."
3. thinking → "Multi-agent reasoning..."
4. streaming (searcher) → "Found 15 sources..."
5. streaming (judge) → "✅ SUFFICIENT..."
6. streaming (reporter) → "## Research Report..."
7. complete → Final report
```

---

## Break Conditions

The orchestrator exits when ANY of these occur:

### 1. Judge Approval ✅

```python
if "SUFFICIENT EVIDENCE" in judge_response:
    # Manager delegates to ReportAgent
    # ReportAgent completes → Workflow ends
```

### 2. Max Rounds Reached 🔄

```python
# MagenticBuilder config
max_round_count = 5  # Default

# After 5 manager rounds:
if not reporter_ran:
    # Force fallback synthesis
    async for event in _synthesize_fallback(iteration, "max_rounds"):
        yield event
```

### 3. Timeout ⏱️

```python
try:
    async with asyncio.timeout(settings.advanced_timeout):  # 600s default
        async for event in workflow.run_stream(task):
            yield event
except TimeoutError:
    async for event in _synthesize_fallback(iteration, "timeout"):
        yield event
```

### 4. Token Budget 💾

```python
# Implicit via PydanticAI/LLM client
# ~50K tokens per query (from settings)
# Individual agent calls handle retries
```

---

## Dependency Matrix

### "If I change X, what breaks?"

| Changed Component | Affected Components | Impact |
|-------------------|---------------------|--------|
| **Evidence model** | All agents, Memory, Tools | HIGH - Core data type |
| **JudgeAssessment** | Judge, Orchestrator | HIGH - Decision flow |
| **ResearchMemory** | All agents | HIGH - Shared state |
| **search_pubmed** | SearchAgent | MEDIUM - One tool |
| **get_bibliography** | ReportAgent | MEDIUM - References |
| **AgentEvent** | Orchestrator, UI | MEDIUM - Streaming |
| **EmbeddingService** | Memory, Dedup | MEDIUM - Similarity |
| **Judge thresholds** | Workflow loop count | LOW - Tuning |
| **System prompts** | Agent behavior | LOW - Prompt eng |

### Agent Dependencies

```
SearchAgent
├── REQUIRES: MagenticState, EmbeddingService
├── WRITES TO: ResearchMemory (evidence)
└── NO DEPS ON: Other agents

JudgeAgent
├── REQUIRES: Evidence context (from Manager)
├── WRITES TO: Nothing
└── CONTROLS: SearchAgent (continue) or ReportAgent (synthesize)

HypothesisAgent
├── REQUIRES: Evidence context
├── WRITES TO: evidence_store["hypotheses"]
└── NO DEPS ON: Other agents

ReportAgent
├── REQUIRES: ResearchMemory, hypotheses, assessment
├── READS FROM: All prior state
└── WRITES TO: evidence_store["final_report"]
```

---

## Critical Thresholds

| Threshold | Value | Location | Impact |
|-----------|-------|----------|--------|
| Confidence threshold | 0.7 (70%) | JudgeAssessment | Sufficiency decision |
| Mechanism score threshold | 6 | Judge criteria | Sufficiency decision |
| Clinical score threshold | 6 | Judge criteria | Sufficiency decision |
| Max manager rounds | 5 | AdvancedOrchestrator | Loop termination |
| Max stall count | 3 | MagenticBuilder | Stall detection |
| Dedup similarity | 0.9 | EmbeddingService | Evidence dedup |
| Max evidence for judge | 30 | prompts/judge.py | Context limit |
| Confirmed hypothesis | 0.8 | ResearchMemory | High-confidence filter |
| Timeout | 600s | settings.advanced_timeout | Workflow timeout |

---

## Developer Checklist

When modifying agents:

- [ ] Update this document if contracts change
- [ ] Verify state access (read/write) is correct
- [ ] Check tool side effects
- [ ] Test with `make check`
- [ ] Verify event emission

When adding new agents:

- [ ] Create factory function in `magentic_agents.py`
- [ ] Define input/output contract
- [ ] Document state access
- [ ] Add to Agent Inventory table
- [ ] Update Dependency Matrix

When changing Judge criteria:

- [ ] Update JudgeAssessment model
- [ ] Update Critical Thresholds table
- [ ] Test workflow loop behavior
- [ ] Verify fallback synthesis triggers correctly

---

*This document is the source of truth for multi-agent coordination.*
