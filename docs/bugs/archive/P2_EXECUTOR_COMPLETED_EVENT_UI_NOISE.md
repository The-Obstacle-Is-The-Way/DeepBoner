# P2 Bug: ExecutorCompletedEvent UI Noise

**Status**: VALIDATED - Ready for Implementation
**Discovered**: 2025-12-05
**Senior Review**: 2025-12-05 (External agent audit confirmed analysis)
**Severity**: P2 (UX noise, confusing but not blocking)
**Component**: `src/orchestrators/advanced.py`

---

## Symptom

After the report synthesis completes, extra events appear in the UI:

```text
📝 **SYNTHESIZING**: Synthesizing research findings...
[...full report content...]

🧠 **JUDGING**: ManagerAgent: Action completed (Tool Call)
⏱️ **PROGRESS**: Step 11: ManagerAgent task completed
```

The "JUDGING" and "PROGRESS" events appear AFTER the report is already displayed, creating confusion.

---

## Root Cause Analysis

### The Misunderstanding

We're treating `ExecutorCompletedEvent` as a **UI event** when it's actually an **internal framework bookkeeping event**.

### Microsoft Agent Framework Design

Looking at `agent_framework/_workflows/_executor.py` (lines 266-281):

```python
# This is auto-emitted by the framework - NOT for UI consumption
with _framework_event_origin():
    completed_event = ExecutorCompletedEvent(self.id, sent_messages if sent_messages else None)
await context.add_event(completed_event)
```

The framework emits `ExecutorCompletedEvent` automatically after every executor handler completes. This includes:
- SearchAgent completing a search
- JudgeAgent completing evaluation
- ReportAgent completing synthesis
- **ManagerAgent completing coordination** (this is the problem)

### What the MS Framework Sample Does

From `samples/getting_started/workflows/orchestration/magentic.py`:

```python
async for event in workflow.run_stream(task):
    if isinstance(event, AgentRunUpdateEvent):
        # Handle streaming with metadata
        props = event.data.additional_properties if event.data else None
        event_type = props.get("magentic_event_type") if props else None
        # ...
    elif isinstance(event, WorkflowOutputEvent):
        # Handle final output
        output = output_messages[-1].text
```

They only handle:
1. `AgentRunUpdateEvent` - for streaming content (with `magentic_event_type` metadata)
2. `WorkflowOutputEvent` - for final output

**They do NOT emit UI events for `ExecutorCompletedEvent`.**

### Our Problematic Code

In `src/orchestrators/advanced.py`:

```python
# Line 348-368: We emit UI events for EVERY ExecutorCompletedEvent
if isinstance(event, ExecutorCompletedEvent):
    state.iteration += 1

    comp_event, prog_event = self._handle_completion_event(...)
    yield comp_event   # <-- WRONG: UI event for internal framework event
    yield prog_event   # <-- WRONG: More noise
```

### Why the Manager Fires a Completion Event

The workflow execution order:
1. ReportAgent streams its output (`AgentRunUpdateEvent`)
2. ReportAgent handler completes → `ExecutorCompletedEvent(reporter)` (we display this)
3. Manager orchestrator handler completes → `ExecutorCompletedEvent(manager)` (we display this too!)
4. `WorkflowOutputEvent` (final)

The Manager is also an executor in the framework. When it finishes coordinating (after ReportAgent returns), it fires its own `ExecutorCompletedEvent`. We're incorrectly emitting UI events for this.

---

## Impact

1. **User Confusion**: Extra "JUDGING: ManagerAgent" events after the report
2. **UX Noise**: Progress events that don't add value
3. **Incorrect Semantics**: Manager completions displayed as agent activity
4. **No Functional Bug**: The workflow completes correctly, just noisy

---

## The Fix

### Stop Emitting UI Events for ExecutorCompletedEvent

Remove UI event emission for `ExecutorCompletedEvent` entirely. Keep internal state tracking only.

**Before (buggy):**

```python
if isinstance(event, ExecutorCompletedEvent):
    state.iteration += 1
    agent_name = getattr(event, "executor_id", "") or "unknown"
    if REPORTER_AGENT_ID in agent_name.lower():
        state.reporter_ran = True

    comp_event, prog_event = self._handle_completion_event(...)
    yield comp_event   # <-- REMOVE: Emits UI noise
    yield prog_event   # <-- REMOVE: Emits UI noise
```

**After (correct):**

```python
if isinstance(event, ExecutorCompletedEvent):
    # Internal state tracking only - NO UI events
    agent_name = getattr(event, "executor_id", "") or "unknown"
    if REPORTER_AGENT_ID in agent_name.lower():
        state.reporter_ran = True
    state.current_message_buffer = ""
    continue  # Skip to next event - do not yield anything
```

**Key changes:**
1. Remove `yield comp_event` and `yield prog_event`
2. Remove `state.iteration += 1` (iteration counter becomes meaningless without UI events)
3. Keep `state.reporter_ran` tracking (needed for fallback synthesis logic)
4. Add `continue` to skip to next event

**Why this is correct:**
- Aligns with MS framework design (their sample ignores `ExecutorCompletedEvent`)
- Eliminates all completion noise including trailing "ManagerAgent" events
- The streaming events (`AgentRunUpdateEvent`) already provide real-time feedback
- `WorkflowOutputEvent` signals completion

### Additional Fix: Add Metadata Filtering to AgentRunUpdateEvent

The senior review identified a gap: we're not filtering `AgentRunUpdateEvent` by `magentic_event_type`.

**Current (incomplete):**

```python
if isinstance(event, AgentRunUpdateEvent):
    if event.data and hasattr(event.data, "text") and event.data.text:
        yield AgentEvent(type="streaming", message=event.data.text)
```

**Should be:**

```python
if isinstance(event, AgentRunUpdateEvent):
    if event.data and hasattr(event.data, "text") and event.data.text:
        # Check metadata to filter internal orchestrator messages
        props = getattr(event.data, "additional_properties", None) or {}
        event_type = props.get("magentic_event_type")
        msg_kind = props.get("orchestrator_message_kind")

        # Filter out internal orchestrator messages (task_ledger, instruction)
        if event_type == MAGENTIC_EVENT_TYPE_ORCHESTRATOR:
            if msg_kind in ("task_ledger", "instruction"):
                continue  # Skip internal coordination messages

        yield AgentEvent(type="streaming", message=event.data.text)
```

**Why this matters:**
- Prevents internal JSON blobs from being displayed
- Filters out raw planning/instruction prompts not meant for users
- Aligns with how MS sample consumes events

---

## Related Code Locations

- `src/orchestrators/advanced.py` line 348-368: ExecutorCompletedEvent handling
- `src/orchestrators/advanced.py` line 437-469: `_handle_completion_event` method
- MS Framework: `python/packages/core/agent_framework/_workflows/_executor.py` line 277-281
- MS Framework: `python/packages/core/agent_framework/_workflows/_magentic.py` line 1962-1976

---

## Related Issues

- P2 Round Counter Semantic Mismatch (FIXED) - Changed display from "Round X/Y" to "Step N"
- This bug explains why step count was confusing - we count internal events too

---

## Framework Event Architecture Deep Dive

### Event Categories in MS Agent Framework

The framework has distinct event categories with different purposes:

#### 1. Workflow Lifecycle Events (Framework-emitted, internal)

| Event | Purpose | UI Relevant? |
|-------|---------|--------------|
| `WorkflowStartedEvent` | Run begins | No |
| `WorkflowStatusEvent` | State transitions (IN_PROGRESS, IDLE, FAILED) | No |
| `WorkflowFailedEvent` | Error with structured details | Maybe (errors) |

#### 2. Superstep Events (Framework-emitted, internal)

| Event | Purpose | UI Relevant? |
|-------|---------|--------------|
| `SuperStepStartedEvent` | Pregel superstep begins | No |
| `SuperStepCompletedEvent` | Pregel superstep ends | No |

#### 3. Executor Events (Framework-emitted automatically, internal)

| Event | Purpose | UI Relevant? |
|-------|---------|--------------|
| `ExecutorInvokedEvent` | Handler starts | No |
| `ExecutorCompletedEvent` | Handler completes | **NO** |
| `ExecutorFailedEvent` | Handler errors | Maybe (errors) |

#### 4. Application Events (User-code emitted via ctx.add_event, UI-facing)

| Event | Purpose | UI Relevant? |
|-------|---------|--------------|
| `AgentRunUpdateEvent` | Streaming content | **YES** |
| `AgentRunEvent` | Complete agent response | Yes |
| `WorkflowOutputEvent` | Final workflow output | **YES** |
| `RequestInfoEvent` | HITL request | Yes |

### Metadata Pattern in AgentRunUpdateEvent

The MS framework uses `additional_properties` in `AgentRunUpdateEvent.data` for classification:

```python
# Orchestrator message
additional_properties={
    "magentic_event_type": "orchestrator_message",
    "orchestrator_message_kind": "user_task" | "task_ledger" | "instruction" | "notice",
    "orchestrator_id": "...",
}

# Agent streaming
additional_properties={
    "magentic_event_type": "agent_delta",
    "agent_id": "searcher" | "judge" | ...,
}
```

### What We Should Handle for UI

1. **`AgentRunUpdateEvent`** with metadata filtering:
   - `magentic_event_type: "agent_delta"` → Display agent streaming
   - `magentic_event_type: "orchestrator_message"` → Filter by `orchestrator_message_kind`:
     - `"user_task"` → Show (task assignment)
     - `"instruction"` → Filter out (internal)
     - `"task_ledger"` → Filter out (internal)
     - `"notice"` → Maybe show (warnings)

2. **`WorkflowOutputEvent`** → Final output

### What We Should NOT Handle for UI

- `ExecutorCompletedEvent` - Internal bookkeeping
- `ExecutorInvokedEvent` - Internal bookkeeping
- `SuperStepStartedEvent/CompletedEvent` - Internal iteration
- `WorkflowStatusEvent` - Internal state machine

---

## Required Import Changes

**Current imports:**

```python
from agent_framework import (
    MAGENTIC_EVENT_TYPE_ORCHESTRATOR,
    AgentRunUpdateEvent,
    ExecutorCompletedEvent,  # Keep for internal tracking
    MagenticBuilder,
    WorkflowOutputEvent,
)
```

**Add these imports for metadata filtering:**

```python
from agent_framework import (
    MAGENTIC_EVENT_TYPE_AGENT_DELTA,  # For agent streaming detection
    ORCH_MSG_KIND_INSTRUCTION,         # Filter internal messages
    ORCH_MSG_KIND_TASK_LEDGER,         # Filter internal messages
)
```

---

## Test Cases

```python
def test_no_executor_completed_events_in_ui():
    """UI should not emit any events from ExecutorCompletedEvent."""
    # Run workflow to completion
    # Collect all yielded AgentEvent objects
    # Assert NONE have type "progress" with "task completed" message
    # Assert NONE have type matching completion patterns
    pass

def test_internal_messages_filtered_from_streaming():
    """Internal orchestrator messages should be filtered from UI stream."""
    # Run workflow and collect all yielded events
    # Assert no events contain "task_ledger" content
    # Assert no events contain raw instruction prompts
    # Assert no JSON blobs in streaming output
    pass

def test_reporter_ran_tracking_still_works():
    """Internal state.reporter_ran should still be set correctly."""
    # Run workflow to completion
    # Verify fallback synthesis is NOT triggered (reporter did run)
    # This ensures we didn't break internal tracking when removing UI events
    pass
```

---

## Why the Free Tier "Works"

The user asked why the free tier seems to work despite expectations. The answer:

1. **The framework handles orchestration** - The MS Agent Framework manages the workflow (planning, progress tracking, agent coordination)
2. **The LLM just provides reasoning** - The model generates text, but the framework decides when to delegate, when to stop, etc.
3. **The "bugs" are in our UI layer** - The orchestration works correctly; we're just displaying internal events

The free tier works because:
- `MagenticBuilder` creates the workflow graph
- `StandardMagenticManager` handles planning and progress evaluation
- The framework routes messages between executors
- The LLM quality affects answer quality, not workflow execution

Our UI noise (trailing events) is a bug in how we consume framework events, not a framework bug.
