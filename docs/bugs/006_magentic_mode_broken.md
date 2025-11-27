# Bug 006: Magentic Mode Deeply Broken

**Date:** November 26, 2025
**Severity:** HIGH
**Status:** Open (Low Priority - Simple Mode Works)

## 1. The Problem

Magentic mode (`mode="magentic"`) is **non-functional**. When enabled:
- Workflow hangs indefinitely (observed in local testing)
- No events are yielded to the UI
- API calls may be made but responses are not processed

## 2. Root Cause Analysis

### 2.1 Architecture Complexity

```
┌─────────────────────────────────────────────────────────────────┐
│ MagenticOrchestrator                                             │
│                                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │ SearchAgent │    │ HypothesisAg│    │ JudgeAgent  │          │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘          │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           MagenticBuilder Standard Manager               │    │
│  │           (OpenAIChatClient orchestration)               │    │
│  │                                                          │    │
│  │   - Decides which agent to call                          │    │
│  │   - Parses agent responses                               │    │
│  │   - Loops until "final result"                           │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

The issue is in the **Standard Manager** layer from `agent-framework-core`:
- It uses an LLM to decide which agent to call next
- The LLM response parsing is fragile
- The loop can stall or hang if parsing fails

### 2.2 Specific Issues

| Issue | Location | Impact |
|-------|----------|--------|
| OpenAI-only | `orchestrator_magentic.py:103` | Can't use Anthropic |
| Manager parsing | `agent-framework` library | Hangs on malformed responses |
| No timeout | `MagenticBuilder` | Workflow runs forever |
| Round limits insufficient | `max_round_count=10` | Still hangs within rounds |

### 2.3 Observed Behavior

```bash
# Test magentic mode
uv run python -c "
from src.orchestrator_factory import create_orchestrator
...
orch = create_orchestrator(mode='magentic')
async for event in orch.run('metformin alzheimer'):
    print(event.type)
"

# Result: Hangs indefinitely after "started" event
# No search, no judge, no completion
```

## 3. Technical Deep Dive

### 3.1 The Manager's Role

The `MagenticBuilder.with_standard_manager()` creates an LLM-powered router:

```python
# From orchestrator_magentic.py lines 94-111
MagenticBuilder()
    .participants(
        searcher=search_agent,
        hypothesizer=hypothesis_agent,
        judge=judge_agent,
        reporter=report_agent,
    )
    .with_standard_manager(
        chat_client=OpenAIChatClient(
            model_id=settings.openai_model,
            api_key=settings.openai_api_key
        ),
        max_round_count=self._max_rounds,  # 10
        max_stall_count=3,
        max_reset_count=2,
    )
```

The manager:
1. Receives the task
2. Calls OpenAI to decide: "Which agent should handle this?"
3. Parses response to extract agent name
4. Calls that agent
5. Receives result
6. Calls OpenAI again: "What next?"
7. Repeat until "final result"

### 3.2 Where It Breaks

The manager's LLM parsing expects specific response formats. If OpenAI returns:
- Unexpected JSON structure → parse error → stall
- Agent name with typo → agent not found → reset
- Verbose explanation → extraction fails → hang

### 3.3 The Event Processing

```python
# orchestrator_magentic.py lines 178-191
async for event in workflow.run_stream(task):
    agent_event = self._process_event(event, iteration)
    if agent_event:
        # Events are processed but may never arrive
        yield agent_event
```

If `workflow.run_stream()` never yields events (manager stuck), the UI sees nothing.

## 4. Why Simple Mode Works

Simple mode bypasses all of this:

```python
# orchestrator.py
while iteration < self.config.max_iterations:
    # Direct calls - no LLM routing
    search_results = await self.search.execute(query)
    assessment = await self.judge.assess(query, evidence)

    if assessment.sufficient:
        return synthesis
    else:
        continue  # Deterministic loop
```

No LLM-powered routing. No parsing. No hangs.

## 5. Fix Options

### Option A: Abandon Magentic (Recommended)

Simple mode + HFInferenceJudgeHandler provides:
- Free AI analysis
- Reliable execution
- No complex dependencies

Mark magentic as "experimental" or remove entirely.

### Option B: Fix the Manager (Hard)

1. Add timeout to `workflow.run_stream()`
2. Implement custom manager without LLM routing
3. Use deterministic agent selection
4. Add better error handling in event processing

### Option C: Replace agent-framework (Medium)

Use a different multi-agent framework:
- LangGraph
- AutoGen
- Custom implementation

## 6. Recommendation

**Do not use magentic mode for the hackathon.**

Simple mode with HFInferenceJudgeHandler:
- Works reliably
- Provides real AI analysis
- No extra dependencies
- No API routing issues

## 7. Files Involved

```
src/orchestrator_magentic.py   ← Main orchestrator (broken)
src/agents/search_agent.py     ← Works in isolation
src/agents/judge_agent.py      ← Works in isolation
src/agents/hypothesis_agent.py ← Works in isolation
src/agents/report_agent.py     ← Works in isolation
```

The agents themselves work. The **manager** coordination is broken.

## 8. Verification

To verify this bug still exists:

```bash
# This should hang
uv run python -c "
import asyncio
from src.app import configure_orchestrator

orch, name = configure_orchestrator(mode='magentic', use_mock=False)
print(f'Backend: {name}')

async def test():
    async for event in orch.run('test query'):
        print(event.type)

asyncio.run(test())
"
```

Expected: Hangs after "started"
Working: Would show search_complete, judge_complete, etc.
