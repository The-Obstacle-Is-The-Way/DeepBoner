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
    drug_name: str = Field(..., description="Name of the drug")
    original_indication: str = Field(..., description="What the drug was originally approved for")
    proposed_indication: str = Field(..., description="The new proposed use")
    mechanism: str = Field(..., description="Proposed mechanism of action")
    evidence_strength: Literal["weak", "moderate", "strong"] = Field(
        ...,
        description="Strength of supporting evidence"
    )

class JudgeAssessment(BaseModel):
    """The judge's assessment of the collected evidence."""
    sufficient: bool = Field(
        ...,
        description="Is there enough evidence to write a report?"
    )
    recommendation: Literal["continue", "synthesize"] = Field(
        ...,
        description="Should we search more or synthesize a report?"
    )
    reasoning: str = Field(
        ...,
        max_length=500,
        description="Explanation of the assessment"
    )
    overall_quality_score: int = Field(
        ...,
        ge=0,
        le=10,
        description="Overall quality of evidence (0-10)"
    )
    coverage_score: int = Field(
        ...,
        ge=0,
        le=10,
        description="How well does evidence cover the query (0-10)"
    )
    candidates: list[DrugCandidate] = Field(
        default_factory=list,
        description="Drug candidates identified in the evidence"
    )
    next_search_queries: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Suggested follow-up queries if more evidence needed"
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Information gaps identified in current evidence"
    )
```

---

## 3. Prompts (`src/prompts/judge.py`)

```python
"""Prompt templates for the Judge."""
from typing import List
from src.utils.models import Evidence

JUDGE_SYSTEM_PROMPT = """You are a biomedical research quality assessor specializing in drug repurposing.

Your job is to evaluate evidence retrieved from PubMed and web searches, and decide if:
1. There is SUFFICIENT evidence to write a research report
2. More searching is needed to fill gaps

## Evaluation Criteria

### For "sufficient" = True (ready to synthesize):
- At least 3 relevant pieces of evidence
- At least one peer-reviewed source (PubMed)
- Clear mechanism of action identified
- Drug candidates with at least "moderate" evidence strength

### For "sufficient" = False (continue searching):
- Fewer than 3 relevant pieces
- No clear drug candidates identified
- Major gaps in mechanism understanding
- All evidence is low quality

## Output Requirements
- Be STRICT. Only mark sufficient=True if evidence is genuinely adequate
- Always provide reasoning for your decision
- If continuing, suggest SPECIFIC, ACTIONABLE search queries
- Identify concrete gaps, not vague statements

## Important
- You are assessing DRUG REPURPOSING potential
- Focus on: mechanism of action, existing clinical data, safety profile
- Ignore marketing content or non-scientific sources"""

def format_evidence_for_prompt(evidence_list: List[Evidence]) -> str:
    """Format evidence list into a string for the prompt."""
    if not evidence_list:
        return "NO EVIDENCE COLLECTED YET"

    formatted = []
    for i, ev in enumerate(evidence_list, 1):
        formatted.append(f"""
---
Source: {ev.citation.source.upper()}
Title: {ev.citation.title}
Date: {ev.citation.date}
URL: {ev.citation.url}

Content:
{ev.content[:1500]}
---")

    return "\n".join(formatted)

def build_judge_user_prompt(question: str, evidence: List[Evidence]) -> str:
    """Build the user prompt for the judge."""
    evidence_text = format_evidence_for_prompt(evidence)

    return f"""## Research Question
{question}

## Collected Evidence ({len(evidence)} pieces)
{evidence_text}

## Your Task
Assess the evidence above and provide your structured assessment.
If evidence is insufficient, suggest 2-3 specific follow-up search queries."""
```

---

## 4. Handler (`src/agent_factory/judges.py`)

```python
"""Judge handler - evaluates evidence quality."""
import structlog
from typing import List
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.utils.config import settings
from src.utils.exceptions import JudgeError
from src.utils.models import JudgeAssessment, Evidence
from src.prompts.judge import JUDGE_SYSTEM_PROMPT, build_judge_user_prompt

logger = structlog.get_logger()

def get_llm_model():
    """Get the configured LLM model for PydanticAI."""
    if settings.llm_provider == "openai":
        return OpenAIModel(
            settings.llm_model,
            api_key=settings.get_api_key(),
        )
    elif settings.llm_provider == "anthropic":
        return AnthropicModel(
            settings.llm_model,
            api_key=settings.get_api_key(),
        )
    else:
        raise JudgeError(f"Unknown LLM provider: {settings.llm_provider}")

# Initialize Agent
judge_agent = Agent(
    model=get_llm_model(),
    result_type=JudgeAssessment,
    system_prompt=JUDGE_SYSTEM_PROMPT,
)

class JudgeHandler:
    """Handles evidence assessment using LLM."""

    def __init__(self, agent: Agent | None = None):
        """
        Initialize the judge handler.

        Args:
            agent: Optional PydanticAI agent (for testing injection)
        """
        self.agent = agent or judge_agent
        self._call_count = 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        reraise=True,
    )
    async def assess(
        self,
        question: str,
        evidence: List[Evidence],
    ) -> JudgeAssessment:
        """
        Assess the quality and sufficiency of evidence.

        Args:
            question: The original research question
            evidence: List of Evidence objects to assess

        Returns:
            JudgeAssessment with decision and recommendations

        Raises:
            JudgeError: If assessment fails after retries
        """
        logger.info(
            "Starting evidence assessment",
            question=question[:100],
            evidence_count=len(evidence),
        )

        self._call_count += 1

        # Build the prompt
        user_prompt = build_judge_user_prompt(question, evidence)

        try:
            # Run the agent - PydanticAI handles structured output
            result = await self.agent.run(user_prompt)

            # result.data is already a JudgeAssessment (typed!)
            assessment = result.data

            logger.info(
                "Assessment complete",
                sufficient=assessment.sufficient,
                recommendation=assessment.recommendation,
                quality_score=assessment.overall_quality_score,
                candidates_found=len(assessment.candidates),
            )

            return assessment

        except Exception as e:
            logger.error("Judge assessment failed", error=str(e))
            raise JudgeError(f"Failed to assess evidence: {e}") from e
            
    async def should_continue(self, assessment: JudgeAssessment) -> bool:
        """
        Decide if the search loop should continue based on the assessment.
        
        Returns:
            True if we should search more, False if we should stop (synthesize or give up).
        """
        return not assessment.sufficient and assessment.recommendation == "continue"

    @property
    def call_count(self) -> int:
        """Number of LLM calls made (for budget tracking)."""
        return self._call_count
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
        
    @pytest.mark.asyncio
    async def test_should_continue(self, mocker):
        from src.agent_factory.judges import JudgeHandler
        from src.utils.models import JudgeAssessment
        
        handler = JudgeHandler(agent=AsyncMock())
        
        # Continue case
        assess1 = JudgeAssessment(
            sufficient=False,
            recommendation="continue",
            reasoning="Need more",
            overall_quality_score=5,
            coverage_score=5
        )
        assert await handler.should_continue(assess1) is True
        
        # Stop case
        assess2 = JudgeAssessment(
            sufficient=True,
            recommendation="synthesize",
            reasoning="Done",
            overall_quality_score=8,
            coverage_score=8
        )
        assert await handler.should_continue(assess2) is False
```

---

## 6. Implementation Checklist

- [ ] Update `src/utils/models.py` with Judge models
- [ ] Create `src/prompts/judge.py`
- [ ] Implement `src/agent_factory/judges.py`
- [ ] Write tests in `tests/unit/agent_factory/test_judges.py`
- [ ] Run `uv run pytest tests/unit/agent_factory/`

```