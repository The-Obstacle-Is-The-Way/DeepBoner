# P2 Bug: Duplicate Report Content in Output

**Date**: 2025-12-03
**Status**: OPEN
**Severity**: P2 (UX - Duplicate content confuses users)
**Component**: `src/orchestrators/advanced.py` + `src/app.py`

---

## Symptom

The final research report appears **twice** in the UI output:
1. First as streaming content (with `📡 **STREAMING**:` prefix)
2. Then again as a complete event (without prefix)

Example:
```
📡 **STREAMING**:
### Summary of Drugs and Mechanisms of Action
...
### Conclusion
Post-menopausal women experiencing libido issues can benefit from...
### Recommendations
- Estrogen Therapy: Effective in enhancing...

Based on the information gathered, we have identified...   <-- DUPLICATE STARTS
### Summary of Drugs and Mechanisms of Action
...
### Conclusion
Post-menopausal women experiencing libido issues can benefit from...
### Recommendations
- Estrogen Therapy: Effective in enhancing...
```

---

## Root Cause Analysis

### Event Flow (Current - Buggy)

```
1. Reporter Agent streams content
   └─ MagenticAgentDeltaEvent × N
      └─ Each yields AgentEvent(type="streaming", message=delta)
      └─ app.py: streaming_buffer += event.message
      └─ User sees: "📡 **STREAMING**: [content building up]"

2. Reporter Agent completes
   └─ MagenticAgentMessageEvent
      └─ Yields truncated completion: "reporter: [first 200 chars]..."
      └─ app.py: flushes streaming_buffer to response_parts

3. Workflow ends
   └─ MagenticFinalResultEvent OR WorkflowOutputEvent
      └─ Contains FULL report content (same as streaming)
      └─ Yields AgentEvent(type="complete", message=FULL_CONTENT)
      └─ app.py: appends event.message to response_parts
      └─ User sees: [SAME CONTENT AGAIN]
```

### Bug Location

**`src/orchestrators/advanced.py` lines 532-552:**
```python
elif isinstance(event, MagenticFinalResultEvent):
    text = self._extract_text(event.message) if event.message else "No result"
    return AgentEvent(
        type="complete",
        message=text,  # <-- FULL content, already streamed
        ...
    )

elif isinstance(event, WorkflowOutputEvent):
    if event.data:
        text = self._extract_text(event.data)
        return AgentEvent(
            type="complete",
            message=text,  # <-- FULL content, already streamed
            ...
        )
```

**`src/app.py` lines 229-232:**
```python
if event.type == "complete":
    response_parts.append(event.message)  # <-- Appends duplicate
    yield "\n\n".join(response_parts)
```

### Why It Happens

1. **Streaming events** yield the full report character-by-character
2. **Final events** (`MagenticFinalResultEvent`, `WorkflowOutputEvent`) contain the same full content
3. **No deduplication** exists between streamed content and final event content
4. **app.py appends both** to the output

---

## Impact

| Aspect | Impact |
|--------|--------|
| UX | Report appears twice, looks buggy |
| Token usage | Renders same content twice |
| Trust | Users may think system is broken |

---

## Proposed Fix Options

### Option 1: Skip Complete Event if Content Matches Streaming (Recommended)

**Location**: `src/app.py` lines 229-232

```python
if event.type == "complete":
    # Skip if content matches what we already streamed
    streaming_content = next(
        (p.replace("📡 **STREAMING**: ", "") for p in response_parts if p.startswith("📡 **STREAMING**:")),
        None
    )
    if streaming_content and event.message.strip() == streaming_content.strip():
        continue  # Skip duplicate
    response_parts.append(event.message)
    yield "\n\n".join(response_parts)
```

**Pros**: Simple, targets exact issue
**Cons**: String comparison may be fragile

### Option 2: Track Streamed Content Hash

**Location**: `src/app.py`

```python
streaming_hash = None
...
if streaming_buffer:
    streaming_hash = hash(streaming_buffer.strip())
    response_parts.append(f"📡 **STREAMING**: {streaming_buffer}")
    streaming_buffer = ""
...
if event.type == "complete":
    if streaming_hash and hash(event.message.strip()) == streaming_hash:
        continue  # Skip duplicate
    response_parts.append(event.message)
```

**Pros**: More robust comparison
**Cons**: Hash collision possible (unlikely)

### Option 3: Don't Emit Complete Event Content from Orchestrator

**Location**: `src/orchestrators/advanced.py` lines 532-552

Replace full content with summary:
```python
elif isinstance(event, MagenticFinalResultEvent):
    return AgentEvent(
        type="complete",
        message="Research complete.",  # Don't repeat content
        data={"iterations": iteration},
        iteration=iteration,
    )
```

**Pros**: Clean separation of streaming vs completion
**Cons**: Loses fallback if streaming failed

### Option 4: Flag-Based Deduplication in Orchestrator

**Location**: `src/orchestrators/advanced.py`

Track if substantial streaming occurred:
```python
has_substantial_streaming = len(current_message_buffer) > 100

# In _process_event for final events:
if has_substantial_streaming:
    return AgentEvent(
        type="complete",
        message="Research complete.",  # Don't repeat
        ...
    )
```

---

## Recommended Fix

**Option 3** is cleanest - the orchestrator should not re-emit content that was already streamed.

**Implementation**:
1. Track `streamed_report_length` in the run loop
2. If substantial content was streamed (>500 chars), emit minimal complete message
3. If no streaming occurred, emit full content as fallback

---

## Files Involved

| File | Role |
|------|------|
| `src/orchestrators/advanced.py:532-552` | Emits duplicate complete events |
| `src/app.py:229-232` | Appends duplicate to output |

---

## Test Plan

1. Run Free Tier query: "What drugs improve female libido post-menopause?"
2. Verify report appears ONCE (with streaming prefix)
3. Verify `complete` event does NOT repeat content
4. Verify fallback works if streaming fails

---

## Related

- **Not related to model quality** - This is a stack bug, not model limitation
- P1 Free Tier fix (PR fix/P1-free-tier) enabled streaming, exposing this bug
