# P2 Bug Report: Advanced Mode Missing "Thinking" State

## Status
- **Date:** 2025-11-29
- **Priority:** P2 (UX polish, not blocking functionality)
- **Component:** `src/orchestrator_magentic.py`, `src/app.py`

---

## Symptoms

User experience in **Advanced (Magentic) mode**:
1. Click example or submit query
2. See: `🚀 **STARTED**: Starting research (Magentic mode)...`
3. **2+ minutes of nothing** (no spinner, no progress, no indication work is happening)
4. Eventually see: `🧠 **JUDGING**: Manager (user_task)...`

**User perception:** "Is it frozen? Did it crash?"

### Container Logs Confirm Work IS Happening
```
14:54:22 [info] Starting Magentic orchestrator query='...'
14:54:22 [info] Embedding service enabled
... 2+ MINUTES OF SILENCE (agent-framework doing internal LLM calls) ...
14:56:38 [info] Creating orchestrator mode=advanced
```

The silence is because `workflow.run_stream()` doesn't yield events during its setup phase.

---

## Root Cause Analysis

### Current Flow (`src/orchestrator_magentic.py`)
```python
async def run(self, query: str) -> AsyncGenerator[AgentEvent, None]:
    # 1. Immediately yields "started"
    yield AgentEvent(type="started", message=f"Starting research (Magentic mode): {query}")

    # 2. Setup (fast, no yield needed)
    embedding_service = self._init_embedding_service()
    init_magentic_state(embedding_service)
    workflow = self._build_workflow()

    # 3. GAP: workflow.run_stream() blocks for 2+ minutes before first event
    async for event in workflow.run_stream(task):  # <-- THE BOTTLENECK
        yield self._process_event(event)
```

The `agent-framework`'s `workflow.run_stream()` is calling OpenAI's API, building the manager prompt, coordinating agents, etc. **It doesn't yield events during this setup phase**.

---

## Gold Standard UX (What We'd Want)

### Gradio's Native Thinking Support

Per [Gradio Chatbot Docs](https://www.gradio.app/docs/gradio/chatbot):

> "The Gradio Chatbot can natively display intermediate thoughts and tool usage in a collapsible accordion next to a chat message. This makes it perfect for creating UIs for LLM agents and chain-of-thought (CoT) or reasoning demos."

**Features available:**
- `gr.ChatMessage` with `metadata={"status": "pending"}` shows spinner
- `metadata={"title": "Thinking...", "status": "pending"}` creates collapsible accordion
- Nested thoughts via `id` and `parent_id`
- `duration` metadata shows time spent

**Example from Gradio docs:**
```python
import gradio as gr

def chat_fn(message, history):
    # Yield thinking state with spinner
    yield gr.ChatMessage(
        role="assistant",
        metadata={"title": "🧠 Thinking...", "status": "pending"}
    )

    # Do work...

    # Update with completed thought
    yield gr.ChatMessage(
        role="assistant",
        content="Analysis complete",
        metadata={"title": "🧠 Thinking...", "status": "done", "duration": 5.2}
    )

    yield "Here's the final answer..."
```

---

## Why This is Complex for DeepBoner

### Constraint 1: ChatInterface Returns Strings
Our `research_agent()` yields plain strings:
```python
yield "🧠 **Backend**: {backend_name}\n\n"
yield "⏳ **Processing...** Searching PubMed...\n"
yield "\n\n".join(response_parts)
```

Converting to `gr.ChatMessage` objects would require refactoring the entire response pipeline.

### Constraint 2: Agent-Framework is the Bottleneck
The 2-minute gap is inside `workflow.run_stream(task)`, which is the `agent-framework` library. We can't inject yields into a third-party library's blocking call.

### Constraint 3: ChatInterface vs Blocks
`gr.ChatInterface` is a convenience wrapper. The full `gr.ChatMessage` metadata features work best with raw `gr.Blocks` + `gr.Chatbot` components.

---

## Options

### Option A: Yield "Thinking" Before Blocking Call (Recommended)
**Effort:** 5 minutes
**Impact:** Users see *something* while waiting

```python
# In src/orchestrator_magentic.py
async def run(self, query: str) -> AsyncGenerator[AgentEvent, None]:
    yield AgentEvent(type="started", message=f"Starting research (Magentic mode): {query}")

    # NEW: Yield thinking state before the blocking call
    yield AgentEvent(
        type="thinking",  # New event type
        message="🧠 Agents are reasoning... This may take 2-5 minutes for complex queries.",
        iteration=0,
    )

    # ... rest of setup ...

    async for event in workflow.run_stream(task):
        yield self._process_event(event)
```

**Pros:**
- Simple, doesn't require Gradio changes
- Works with current string-based approach
- Sets user expectations ("2-5 minutes")

**Cons:**
- No spinner/animation (static text)
- Doesn't show real-time progress during the gap

### Option B: Use `gr.ChatMessage` with Metadata (Major Refactor)
**Effort:** 2-4 hours
**Impact:** Full gold-standard UX

Would require:
1. Changing `research_agent()` to yield `gr.ChatMessage` objects
2. Adding thinking states with `metadata={"status": "pending"}`
3. Updating all event handlers to produce proper ChatMessage objects

### Option C: Heartbeat/Polling (Over-Engineering)
**Effort:** 4+ hours
**Impact:** Spinner during blocking call

Create a background task that yields "still working..." every 10 seconds while waiting for the agent-framework. Requires:
- `asyncio.create_task()` for heartbeat
- Task cancellation when real events arrive
- Proper cleanup

**Verdict:** Over-engineering for a demo.

### Option D: Accept the Limitation (Document It)
**Effort:** 0
**Impact:** None (users still confused)

Just document that Advanced mode takes 2-5 minutes and users should wait.

---

## Recommendation

**Implement Option A** - Add a "thinking" yield before the blocking call.

It's:
1. Minimal code change (5 minutes)
2. Sets user expectations clearly
3. Doesn't require Gradio refactoring
4. Better than silence

---

## Implementation Plan

### Step 1: Add "thinking" Event Type
```python
# In src/utils/models.py
class AgentEvent(BaseModel):
    type: Literal[
        "started", "thinking", "searching", ...  # Add "thinking"
    ]
```

### Step 2: Yield Thinking Event in Magentic Orchestrator
```python
# In src/orchestrator_magentic.py, run() method
yield AgentEvent(
    type="thinking",
    message="🧠 Multi-agent reasoning in progress... This may take 2-5 minutes.",
    iteration=0,
)
```

### Step 3: Handle in App
```python
# In src/app.py, research_agent()
if event.type == "thinking":
    yield f"⏳ {event.message}"
```

---

## Test Plan

- [ ] Add `"thinking"` to AgentEvent type literals
- [ ] Add yield before `workflow.run_stream()`
- [ ] Handle in app.py
- [ ] `make check` passes
- [ ] Manual test: Advanced mode shows "reasoning in progress" message
- [ ] Deploy to HuggingFace, verify UX improvement

---

## References

- [Gradio ChatInterface Docs](https://www.gradio.app/docs/gradio/chatinterface)
- [Gradio Chatbot Metadata](https://www.gradio.app/docs/gradio/chatbot)
- [Agents and Tool Usage Guide](https://www.gradio.app/guides/agents-and-tool-usage)
- [GitHub Issue: Streaming text not working](https://github.com/gradio-app/gradio/issues/11443)
