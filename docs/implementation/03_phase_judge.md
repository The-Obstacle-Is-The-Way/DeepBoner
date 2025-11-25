# Phase 3 Implementation Spec: Judge Vertical Slice

**Goal**: Implement the "Brain" of the agent — evaluating evidence quality.
**Philosophy**: "Structured Output or Bust."
**Estimated Effort**: 3-4 hours
**Prerequisite**: Phase 2 complete

---

## 1. The Slice Definition

This slice covers:
1. **Input**: Question + List of `Evidence`.
2. **Process**:
   - Construct prompt with evidence.
   - Call LLM (PydanticAI).
   - Parse into `JudgeAssessment`.
3. **Output**: `JudgeAssessment` object.

**Files**:
- `src/utils/models.py`: Add Judge models
- `src/prompts/judge.py`: Prompt templates
- `src/agent_factory/judges.py`: Handler logic

---

## 2. Models (`src/utils/models.py`)

Add these to the existing models file:

```python
class DrugCandidate(BaseModel):
    """A potential drug repurposing candidate."""
    drug_name: str
    original_indication: str
    proposed_indication: str
    mechanism: str
    evidence_strength: Literal["weak", "moderate", "strong"]

class JudgeAssessment(BaseModel):
    """The judge's assessment."""
    sufficient: bool
    recommendation: Literal["continue", "synthesize"]
    reasoning: str
    overall_quality_score: int
    coverage_score: int
    candidates: list[DrugCandidate] = Field(default_factory=list)
    next_search_queries: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
```

---

## 3. Prompts (`src/prompts/judge.py`)

```python
"""Prompt templates for the Judge."""
from typing import List
from src.utils.models import Evidence

JUDGE_SYSTEM_PROMPT = """You are a biomedical research judge..."""

def build_judge_user_prompt(question: str, evidence: List[Evidence]) -> str:
    """Build the user prompt."""
    # ... implementation ...
```

---

## 4. Handler (`src/agent_factory/judges.py`)

```python
"""Judge handler - evaluates evidence quality."""
import structlog
from pydantic_ai import Agent
from tenacity import retry, stop_after_attempt

from src.utils.config import settings
from src.utils.exceptions import JudgeError
from src.utils.models import JudgeAssessment, Evidence
from src.prompts.judge import JUDGE_SYSTEM_PROMPT, build_judge_user_prompt

logger = structlog.get_logger()

# Initialize Agent
judge_agent = Agent(
    model=settings.llm_model,  # e.g. "openai:gpt-4o-mini" or "anthropic:claude-3-haiku"
    result_type=JudgeAssessment,
    system_prompt=JUDGE_SYSTEM_PROMPT,
)

class JudgeHandler:
    """Handles evidence assessment."""

    def __init__(self, agent=None):
        self.agent = agent or judge_agent

    async def assess(self, question: str, evidence: List[Evidence]) -> JudgeAssessment:
        """Assess evidence sufficiency."""
        prompt = build_judge_user_prompt(question, evidence)
        try:
            result = await self.agent.run(prompt)
            return result.data
        except Exception as e:
            raise JudgeError(f"Assessment failed: {e}")
```

---

## 5. TDD Workflow

### Test File: `tests/unit/agent_factory/test_judges.py`

```python
"""Unit tests for JudgeHandler."""
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestJudgeHandler:
    @pytest.mark.asyncio
    async def test_assess_returns_assessment(self, mocker):
        from src.agent_factory.judges import JudgeHandler
        from src.utils.models import JudgeAssessment, Evidence, Citation

        # Mock PydanticAI agent result
        mock_result = MagicMock()
        mock_result.data = JudgeAssessment(
            sufficient=True,
            recommendation="synthesize",
            reasoning="Good",
            overall_quality_score=8,
            coverage_score=8
        )
        
        mock_agent = AsyncMock()
        mock_agent.run = AsyncMock(return_value=mock_result)

        handler = JudgeHandler(agent=mock_agent)
        result = await handler.assess("q", [])
        
        assert result.sufficient is True
```

---

## 6. Implementation Checklist

- [ ] Update `src/utils/models.py` with Judge models
- [ ] Create `src/prompts/judge.py`
- [ ] Implement `src/agent_factory/judges.py`
- [ ] Write tests in `tests/unit/agent_factory/test_judges.py`
- [ ] Run `uv run pytest tests/unit/agent_factory/`

---

## 7. Definition of Done

Phase 3 is **COMPLETE** when:

1. ✅ All unit tests in `tests/unit/agent_factory/` pass.
2. ✅ `JudgeHandler` returns valid `JudgeAssessment` objects.
3. ✅ Structured output is enforced (no raw JSON strings leaked).
4. ✅ Retry/exception handling is covered by tests (mock failures).
5. ✅ Manual REPL sanity check works:

```python
import asyncio
from src.agent_factory.judges import JudgeHandler
from src.utils.models import Evidence, Citation

async def test():
    handler = JudgeHandler()
    evidence = [
        Evidence(
            content="Metformin shows neuroprotective properties...",
            citation=Citation(
                source="pubmed",
                title="Metformin Review",
                url="https://pubmed.ncbi.nlm.nih.gov/123/",
                date="2024",
            ),
        )
    ]
    result = await handler.assess("Can metformin treat Alzheimer's?", evidence)
    print(f"Sufficient: {result.sufficient}")
    print(f"Recommendation: {result.recommendation}")
    print(f"Reasoning: {result.reasoning}")

asyncio.run(test())
```

**Proceed to Phase 4 ONLY after all checkboxes are complete.**
