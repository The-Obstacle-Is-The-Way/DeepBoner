# Phase 3 Implementation Spec: Judge Vertical Slice

**Goal**: Implement the "Brain" of the agent — evaluating evidence quality.
**Philosophy**: "Structured Output or Bust."

---

## 1. The Slice Definition

This slice covers:
1.  **Input**: A user question + a list of `Evidence` (from Phase 2).
2.  **Process**: 
    - Construct a prompt with the evidence.
    - Call LLM (PydanticAI / OpenAI / Anthropic).
    - Force JSON structured output.
3.  **Output**: A `JudgeAssessment` object.

**Directory**: `src/features/judge/`

---

## 2. Models (`src/features/judge/models.py`)

The output schema must be strict.

```python
from pydantic import BaseModel, Field
from typing import List, Literal

class AssessmentDetails(BaseModel):
    mechanism_score: int = Field(..., ge=0, le=10)
    mechanism_reasoning: str
    candidates_found: List[str]

class JudgeAssessment(BaseModel):
    details: AssessmentDetails
    sufficient: bool
    recommendation: Literal["continue", "synthesize"]
    next_search_queries: List[str]
```

---

## 3. Prompt Engineering (`src/features/judge/prompts.py`)

We treat prompts as code. They should be versioned and clean.

```python
SYSTEM_PROMPT = """You are a drug repurposing research judge.
Evaluate the evidence strictly.
Output JSON only."""

def format_user_prompt(question: str, evidence: List[Evidence]) -> str:
    # ... formatting logic ...
    return prompt
```

---

## 4. TDD Workflow

### Step 1: Mocked LLM Test
We do NOT hit the real LLM in unit tests. We mock the response to ensure our parsing logic works.

Create `tests/unit/features/judge/test_handler.py`.

```python
@pytest.mark.asyncio
async def test_judge_parsing(mocker):
    # Arrange
    mock_llm_response = '{"sufficient": true, ...}'
    mocker.patch("llm_client.generate", return_value=mock_llm_response)
    
    # Act
    handler = JudgeHandler()
    assessment = await handler.assess("q", [])
    
    # Assert
    assert assessment.sufficient is True
```

### Step 2: Implement Handler
Use `pydantic-ai` or a raw client to enforce the schema.

---

## 5. Implementation Checklist

- [ ] Define `JudgeAssessment` models.
- [ ] Write Prompt Templates.
- [ ] Implement `JudgeHandler` with PydanticAI/Instructor pattern.
- [ ] Write tests ensuring JSON parsing handles failures gracefully (retry logic).
- [ ] Verify via `uv run pytest`.
