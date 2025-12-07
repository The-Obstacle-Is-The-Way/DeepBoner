# Data Models Reference

> **Last Updated**: 2025-12-06

This document describes all Pydantic models used in DeepBoner.

## Location

All core models are defined in `src/utils/models.py`.

## Type Definitions

### SourceName

```python
SourceName = Literal["pubmed", "clinicaltrials", "europepmc", "preprint", "openalex", "web"]
```

Centralized source type. Add new sources here when integrating new databases.

---

## Core Models

### Citation

Represents a citation to a source document.

```python
class Citation(BaseModel):
    source: SourceName          # Where this came from
    title: str                  # Title (1-500 chars)
    url: str                    # URL to source
    date: str                   # Publication date (YYYY-MM-DD or 'Unknown')
    authors: list[str]          # Author list

    MAX_AUTHORS_IN_CITATION: ClassVar[int] = 3

    @property
    def formatted(self) -> str:
        """Format as citation string."""
```

**Example:**
```python
citation = Citation(
    source="pubmed",
    title="Effects of testosterone on female libido",
    url="https://pubmed.ncbi.nlm.nih.gov/12345678",
    date="2024-01-15",
    authors=["Smith J", "Jones A", "Brown B"]
)
print(citation.formatted)
# "Smith J, Jones A, Brown B (2024-01-15). Effects of testosterone..."
```

---

### Evidence

A piece of evidence retrieved from search.

```python
class Evidence(BaseModel):
    content: str                # The actual text content (min 1 char)
    citation: Citation          # Source citation
    relevance: float            # Relevance score 0-1
    metadata: dict[str, Any]    # Additional metadata

    model_config = {"frozen": True}  # Immutable
```

**Metadata fields** (source-dependent):
- `cited_by_count` - Citation count
- `concepts` - Subject concepts
- `is_open_access` - OA status
- `pmid` - PubMed ID
- `doi` - Digital Object Identifier

**Example:**
```python
evidence = Evidence(
    content="The study found significant improvement...",
    citation=citation,
    relevance=0.85,
    metadata={"pmid": "12345678", "cited_by_count": 42}
)
```

---

### SearchResult

Result of a search operation.

```python
class SearchResult(BaseModel):
    query: str                      # Original query
    evidence: list[Evidence]        # Retrieved evidence
    sources_searched: list[SourceName]  # Which sources were queried
    total_found: int                # Total matches
    errors: list[str]               # Any errors encountered
```

---

## Assessment Models

### AssessmentDetails

Detailed assessment of evidence quality by the Judge.

```python
class AssessmentDetails(BaseModel):
    mechanism_score: int            # 0-10: How well explained
    mechanism_reasoning: str        # Explanation (min 10 chars)
    clinical_evidence_score: int    # 0-10: Clinical strength
    clinical_reasoning: str         # Explanation (min 10 chars)
    drug_candidates: list[str]      # Specific drugs mentioned
    key_findings: list[str]         # Key findings
```

---

### JudgeAssessment

Complete assessment from the Judge.

```python
class JudgeAssessment(BaseModel):
    details: AssessmentDetails
    sufficient: bool                # Is evidence sufficient?
    confidence: float               # 0-1 confidence
    recommendation: Literal["continue", "synthesize"]
    next_search_queries: list[str]  # If continue, what to search
    reasoning: str                  # Overall reasoning (min 20 chars)
```

**Decision Logic:**
- `recommendation="continue"` → More evidence needed, loop back
- `recommendation="synthesize"` → Ready to generate report

---

## Event Models

### AgentEvent

Event emitted by orchestrator for UI streaming.

```python
class AgentEvent(BaseModel):
    type: Literal[
        "started",
        "thinking",
        "searching",
        "search_complete",
        "judging",
        "judge_complete",
        "looping",
        "synthesizing",
        "complete",
        "error",
        "streaming",
        "hypothesizing",
        "analyzing",
        "analysis_complete",
        "progress",
    ]
    message: str
    data: Any = None
    timestamp: datetime
    iteration: int = 0

    def to_markdown(self) -> str:
        """Format event as markdown with emoji."""
```

**Event Types:**
| Type | Icon | Meaning |
|------|------|---------|
| `started` | 🚀 | Research started |
| `thinking` | ⏳ | Processing |
| `searching` | 🔍 | Searching databases |
| `search_complete` | 📚 | Search finished |
| `judging` | 🧠 | Evaluating evidence |
| `judge_complete` | ✅ | Judgment done |
| `looping` | 🔄 | Refining query |
| `synthesizing` | 📝 | Generating report |
| `complete` | 🎉 | Research complete |
| `error` | ❌ | Error occurred |
| `progress` | ⏱️ | Progress update |

---

## Hypothesis Models

### MechanismHypothesis

A scientific hypothesis about drug mechanism.

```python
class MechanismHypothesis(BaseModel):
    drug: str                       # Drug being studied
    target: str                     # Molecular target
    pathway: str                    # Biological pathway
    effect: str                     # Downstream effect
    confidence: float               # 0-1 confidence
    supporting_evidence: list[str]  # Supporting PMIDs/URLs
    contradicting_evidence: list[str]
    search_suggestions: list[str]

    def to_search_queries(self) -> list[str]:
        """Generate queries to test hypothesis."""
```

---

### HypothesisAssessment

Assessment of evidence against hypotheses.

```python
class HypothesisAssessment(BaseModel):
    hypotheses: list[MechanismHypothesis]
    primary_hypothesis: MechanismHypothesis | None
    knowledge_gaps: list[str]
    recommended_searches: list[str]
```

---

## Report Models

### ReportSection

A section of the research report.

```python
class ReportSection(BaseModel):
    title: str
    content: str
    citations: list[str] = []   # Reserved for inline citations
```

---

### ResearchReport

Structured scientific report (final output).

```python
class ResearchReport(BaseModel):
    title: str
    executive_summary: str          # 100-1000 chars
    research_question: str

    methodology: ReportSection
    hypotheses_tested: list[dict[str, Any]]

    mechanistic_findings: ReportSection
    clinical_findings: ReportSection

    drug_candidates: list[str]
    limitations: list[str]
    conclusion: str

    references: list[dict[str, str]]

    # Metadata
    sources_searched: list[str]
    total_papers_reviewed: int
    search_iterations: int
    confidence_score: float         # 0-1

    def to_markdown(self) -> str:
        """Render report as markdown."""
```

**Reference Format:**
```python
{
    "title": "Paper title",
    "authors": "Smith J et al.",
    "source": "pubmed",
    "date": "2024-01-15",
    "url": "https://..."
}
```

---

## Configuration Models

### OrchestratorConfig

Configuration for the orchestrator.

```python
class OrchestratorConfig(BaseModel):
    max_iterations: int = 10        # 1-20
    max_results_per_tool: int = 10  # 1-50
    search_timeout: float = 30.0    # 5-120 seconds
```

---

## Model Relationships

```
SearchResult
    └── Evidence[]
           └── Citation

JudgeAssessment
    └── AssessmentDetails

ResearchReport
    ├── ReportSection (methodology)
    ├── ReportSection (mechanistic_findings)
    ├── ReportSection (clinical_findings)
    └── HypothesisAssessment
           └── MechanismHypothesis[]
```

---

## Validation Notes

All models use Pydantic v2 with:

- **Field constraints** - `ge=0`, `le=1` for scores, `min_length` for strings
- **Frozen models** - Evidence is immutable (`frozen=True`)
- **Default factories** - Lists default to `[]` via `default_factory=list`

---

## Related Documentation

- [Component Inventory](component-inventory.md)
- [Exception Hierarchy](exception-hierarchy.md)
- [Architecture Overview](overview.md)
