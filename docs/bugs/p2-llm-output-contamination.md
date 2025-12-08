# P2 Bug: LLM Output Contamination (`.ToDecimal` Hallucination)

**Severity**: P2 (Medium - affects output quality)
**Status**: IMPLEMENTED (2025-12-08)
**Discovered**: 2025-12-07
**Reporter**: User observation during live demo
**Affected Tier**: Free Tier (HuggingFace / Qwen 2.5 7B)
**Resolution**: Added `src/utils/sanitize.py` with regex-based output filtering

## Symptom

Random C# method-like tokens (`.ToDecimal`) appear in research output:

```
Focus on:
- Identifying specific molecular targets
- Understanding mechanism of action
- Finding clinical evidence supporting hypotheses

The final output should be a structured research report.

.ToDecimal    <-- GARBAGE TOKEN
Based on the search results from PubMed...
```

And again at the end of synthesis:
```
...ensure effective and safe treatment approaches.

.ToDecimal /// can we deeply serach for any other bugs...    <-- GARBAGE FOLLOWED BY USER INPUT LEAK
```

## Root Cause Analysis

### 1. LLM Hallucination

`.ToDecimal` is a C# method (`Convert.ToDecimal()`). Qwen 2.5 7B was trained on code datasets that include C# - occasionally garbage tokens from training data leak into output.

This is **NOT** a code bug - it's a model behavior issue.

### 2. No Output Sanitization

Currently, streaming output flows directly from LLM → UI with no filtering:

```python
# src/orchestrators/advanced.py:348-356
text = getattr(event.data, "text", None)
if text:
    state.current_message_buffer += text
    yield AgentEvent(
        type="streaming",
        message=text,  # Raw LLM output - no sanitization
        data={"agent_id": author},
        iteration=state.iteration,
    )
```

### 3. Streaming Accumulation

```python
# src/app.py:195-201
if event.type == "streaming":
    streaming_buffer += event.message  # Accumulates raw tokens
    current_parts = [*response_parts, f"📡 **STREAMING**: {streaming_buffer}"]
    yield "\\n\\n".join(current_parts)
```

## Evidence

| Pattern | Source | Frequency |
|---------|--------|-----------|
| `.ToDecimal` | C# `Convert.ToDecimal()` | Observed 2x in single session |
| Potential others | `.ToString`, `.Parse`, etc. | Not yet observed |

## Impact

| Aspect | Impact |
|--------|--------|
| Functionality | None - research completes |
| Output Quality | Unprofessional garbage in results |
| User Trust | Reduces confidence in AI quality |
| Reproducibility | Non-deterministic (temperature > 0) |

## Affected Configuration

- **Model**: `Qwen/Qwen2.5-7B-Instruct` (Free Tier)
- **Provider**: HuggingFace Inference API
- **Temperature**: 0.7 (default)
- **Paid Tier (OpenAI)**: NOT observed - GPT-5 is more robust

## Proposed Solutions

### Option 1: Regex Filter for Known Garbage (RECOMMENDED)

Add a sanitization layer for known hallucination patterns:

```python
import re

# Known garbage patterns from smaller LLMs
GARBAGE_PATTERNS = [
    r'^\.[A-Z][a-zA-Z]+$',  # .ToDecimal, .ToString, .Parse
    r'^<\|[a-z_]+\|>$',     # <|endoftext|>, <|im_end|>
    r'^#{1,6}\s*$',          # Empty markdown headers
]

def sanitize_llm_output(text: str) -> str:
    """Remove known LLM garbage tokens."""
    lines = text.split('\\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        is_garbage = any(re.match(p, stripped) for p in GARBAGE_PATTERNS)
        if not is_garbage:
            cleaned.append(line)
    return '\\n'.join(cleaned)
```

**Pros**:
- Simple, targeted fix
- Low risk of false positives
- Can expand pattern list as needed

**Cons**:
- Reactive (add patterns as discovered)
- Doesn't fix root cause (model quality)

### Option 2: Lower Temperature

Reduce temperature from 0.7 to 0.3 for more deterministic output:

```python
# src/clients/huggingface.py
temperature = chat_options.temperature if chat_options.temperature is not None else 0.3
```

**Pros**:
- Reduces hallucination probability
- Simple config change

**Cons**:
- Less creative/varied output
- May affect research quality

### Option 3: Use Larger Model (Long-term)

Switch Free Tier to a larger, more robust model when available on HuggingFace native infrastructure.

**Current Constraint**: Models > 30B get routed to unreliable third-party providers (see `CLAUDE.md`).

### Option 4: Post-Processing Cleanup

Add final cleanup step before yielding `complete` event:

```python
def _clean_final_output(self, content: str) -> str:
    """Clean up LLM output before final display."""
    # Remove isolated garbage tokens
    content = re.sub(r'\\n\\s*\\.[A-Z][a-zA-Z]+\\s*\\n', '\\n', content)
    return content.strip()
```

## Recommended Fix

**Option 1 (Regex Filter)** - minimal risk, immediate improvement.

Implement in `src/orchestrators/advanced.py` at the streaming event emission point.

## Implementation Plan

1. Add `src/utils/sanitize.py` with `sanitize_llm_output()` function
2. Call sanitizer in `advanced.py` before yielding streaming events
3. Add unit tests for known garbage patterns
4. Monitor logs for new patterns to add

## Testing

```bash
# Run research query and check output
uv run python src/app.py

# Submit: "What drugs improve female libido post-menopause?"
# Verify: No .ToDecimal or similar garbage in output
```

## Related Issues

- **Training Data Contamination**: Common in smaller LLMs trained on mixed datasets
- **Token Boundary Issues**: Sometimes occurs at chunk boundaries during streaming
- **Not a Bug in Our Code**: This is model behavior, not software defect

## References

- [Qwen 2.5 Model Card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [LLM Hallucination Patterns](https://arxiv.org/abs/2311.05232)
- Similar issues in other projects using smaller LLMs

## Version Info

- DeepBoner: v0.1.0+
- Gradio: 6.0.1
- HuggingFace Client: huggingface_hub
- Qwen Model: Qwen2.5-7B-Instruct
