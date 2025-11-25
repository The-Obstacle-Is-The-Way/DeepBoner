# Phase 4 Implementation Spec: Orchestrator & UI

**Goal**: Connect the Brain and the Body, then give it a Face.
**Philosophy**: "Streaming is Trust."
**Estimated Effort**: 4-5 hours
**Prerequisite**: Phases 1-3 complete

---

## 1. The Slice Definition

This slice connects:
1. **Orchestrator**: The loop calling `SearchHandler` → `JudgeHandler`.
2. **UI**: Gradio app.

**Files**:
- `src/utils/models.py`: Add Orchestrator models
- `src/orchestrator.py`: Main logic
- `src/app.py`: UI

---

## 2. Models (`src/utils/models.py`)

Add to models file:

```python
from enum import Enum

class AgentState(str, Enum):
    SEARCHING = "searching"
    JUDGING = "judging"
    COMPLETE = "complete"
    ERROR = "error"

class AgentEvent(BaseModel):
    state: AgentState
    message: str
    data: dict[str, Any] | None = None
```

---

## 3. Orchestrator (`src/orchestrator.py`)

```python
"""Main agent orchestrator."""
import structlog
from typing import AsyncGenerator

from src.shared.config import settings
from src.tools.search_handler import SearchHandler
from src.agent_factory.judges import JudgeHandler
from src.utils.models import AgentEvent, AgentState

logger = structlog.get_logger()

class Orchestrator:
    def __init__(self):
        self.search = SearchHandler(...)
        self.judge = JudgeHandler()

    async def run(self, question: str) -> AsyncGenerator[AgentEvent, None]:
        """Run the loop."""
        yield AgentEvent(state=AgentState.SEARCHING, message="Starting...")
        
        # ... while loop implementation ...
        # ... yield events ...
```

---

## 4. UI (`src/app.py`)

```python
"""Gradio UI."""
import gradio as gr
from src.orchestrator import Orchestrator

async def chat(message, history):
    agent = Orchestrator()
    async for event in agent.run(message):
        yield f"**[{event.state.value}]** {event.message}"

# ... gradio blocks setup ...
```

---

## 5. TDD Workflow

### Test File: `tests/unit/test_orchestrator.py`

```python
"""Unit tests for Orchestrator."""
import pytest
from unittest.mock import AsyncMock

class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_run_loop(self, mocker):
        from src.orchestrator import Orchestrator
        
        # Mock handlers
        # ... setup mocks ...
        
        orch = Orchestrator()
        events = [e async for e in orch.run("test")]
        assert len(events) > 0
```

---

## 6. Implementation Checklist

- [ ] Update `src/utils/models.py`
- [ ] Implement `src/orchestrator.py`
- [ ] Implement `src/app.py`
- [ ] Write tests in `tests/unit/test_orchestrator.py`
- [ ] Run `uv run python src/app.py`