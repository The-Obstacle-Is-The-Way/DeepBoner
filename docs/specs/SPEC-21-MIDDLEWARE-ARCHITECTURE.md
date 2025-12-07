# SPEC-21: Middleware Architecture Refactor

**Status:** READY FOR IMPLEMENTATION
**Priority:** P2 (Architectural hygiene + fixes HuggingFace retry bug)
**Effort:** 2 hours
**PR Scope:** Folder rename + new middleware implementations

---

## Problem Statement

1. **Misleading folder name:** `src/middleware/` contains a workflow (`SubIterationMiddleware`), not interceptor middleware
2. **Missing retry logic:** `HuggingFaceChatClient` has no retry on 429/transient errors (P2 bug)
3. **No token tracking:** Cannot monitor API costs
4. **Not using MS framework patterns:** We use decorators but not `ChatMiddleware` base classes

---

## Current State (WRONG)

```text
src/
├── middleware/                      ← MISLEADING: contains workflow
│   ├── __init__.py
│   ├── sub_iteration.py             ← This is a WORKFLOW, not middleware
│   └── .gitkeep
```

**HuggingFace client has no retry:**
```python
# src/clients/huggingface.py:263-265
except Exception as e:
    logger.error("HuggingFace API error", error=str(e))
    raise  # ← No retry, crashes on 429
```

---

## Target State (CORRECT)

```text
src/
├── workflows/                       ← RENAMED: now accurate
│   ├── __init__.py
│   └── sub_iteration.py
│
├── middleware/                      ← NEW: actual MS-pattern middleware
│   ├── __init__.py
│   ├── retry.py                     ← RetryMiddleware(ChatMiddleware)
│   └── token_tracking.py            ← TokenTrackingMiddleware(ChatMiddleware)
```

---

## Implementation Steps

### Step 1: Rename Folder (5 min)

```bash
# Rename middleware → workflows
git mv src/middleware src/workflows
```

### Step 2: Update Import (5 min)

```python
# src/orchestrators/hierarchical.py - Line ~15
# BEFORE:
from src.middleware.sub_iteration import SubIterationMiddleware, SubIterationTeam

# AFTER:
from src.workflows.sub_iteration import SubIterationMiddleware, SubIterationTeam
```

### Step 3: Create New Middleware Package (10 min)

```python
# src/middleware/__init__.py
"""Microsoft Agent Framework middleware implementations.

These are interceptor-pattern middleware that wrap chat client calls.
They are NOT workflows - see src/workflows/ for orchestration patterns.
"""

from src.middleware.retry import RetryMiddleware
from src.middleware.token_tracking import TokenTrackingMiddleware

__all__ = ["RetryMiddleware", "TokenTrackingMiddleware"]
```

### Step 4: Implement RetryMiddleware (30 min)

```python
# src/middleware/retry.py
"""Retry middleware for chat clients with exponential backoff."""

import asyncio
from typing import Awaitable, Callable

import structlog
from agent_framework._middleware import ChatContext, ChatMiddleware

logger = structlog.get_logger()


class RetryMiddleware(ChatMiddleware):
    """Retries failed chat requests with exponential backoff.

    This middleware intercepts chat client calls and retries on transient
    errors (rate limits, timeouts, server errors).

    Attributes:
        max_attempts: Maximum number of attempts (default: 3)
        min_wait: Minimum wait between retries in seconds (default: 1.0)
        max_wait: Maximum wait between retries in seconds (default: 10.0)
        retryable_status_codes: HTTP status codes to retry (default: 429, 500, 502, 503, 504)
    """

    def __init__(
        self,
        max_attempts: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 10.0,
        retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504),
    ) -> None:
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.retryable_status_codes = retryable_status_codes

    def _is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable."""
        # Check for httpx status errors
        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            return error.response.status_code in self.retryable_status_codes

        # Check for timeout errors
        error_name = type(error).__name__.lower()
        if "timeout" in error_name:
            return True

        # Check for connection errors
        if "connection" in error_name:
            return True

        return False

    def _calculate_wait(self, attempt: int) -> float:
        """Calculate wait time with exponential backoff."""
        wait = self.min_wait * (2 ** attempt)
        return min(wait, self.max_wait)

    async def process(
        self, context: ChatContext, next: Callable[[ChatContext], Awaitable[None]]
    ) -> None:
        """Process the chat request with retry logic."""
        last_error: Exception | None = None

        for attempt in range(self.max_attempts):
            try:
                await next(context)
                return  # Success - exit retry loop

            except Exception as e:
                last_error = e

                if not self._is_retryable(e):
                    logger.warning(
                        "Non-retryable error",
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    raise  # Don't retry non-retryable errors

                if attempt < self.max_attempts - 1:
                    wait_time = self._calculate_wait(attempt)
                    logger.info(
                        "Retrying after error",
                        attempt=attempt + 1,
                        max_attempts=self.max_attempts,
                        wait_seconds=wait_time,
                        error=str(e),
                    )
                    await asyncio.sleep(wait_time)

        # All retries exhausted
        logger.error(
            "All retry attempts failed",
            max_attempts=self.max_attempts,
            last_error=str(last_error),
        )
        if last_error:
            raise last_error
```

### Step 5: Implement TokenTrackingMiddleware (20 min)

```python
# src/middleware/token_tracking.py
"""Token tracking middleware for monitoring API usage."""

from contextvars import ContextVar
from typing import Awaitable, Callable

import structlog
from agent_framework._middleware import ChatContext, ChatMiddleware

logger = structlog.get_logger()

# ContextVar for per-request token tracking
_request_tokens: ContextVar[dict[str, int]] = ContextVar(
    "request_tokens",
    default={"input": 0, "output": 0},
)


class TokenTrackingMiddleware(ChatMiddleware):
    """Tracks token usage across chat requests.

    This middleware logs token usage after each chat completion
    and maintains running totals for the session.

    Usage metrics are logged via structlog for observability.
    """

    def __init__(self) -> None:
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0

    async def process(
        self, context: ChatContext, next: Callable[[ChatContext], Awaitable[None]]
    ) -> None:
        """Process request and track token usage."""
        await next(context)

        # Extract usage from response if available
        if context.result is None:
            return

        usage = None

        # Try to get usage from response
        if hasattr(context.result, "usage"):
            usage = context.result.usage
        elif hasattr(context.result, "messages") and context.result.messages:
            # Check first message for usage metadata
            msg = context.result.messages[0]
            if hasattr(msg, "metadata") and msg.metadata:
                usage = msg.metadata.get("usage")

        if usage:
            input_tokens = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
            output_tokens = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)

            self.total_input_tokens += input_tokens
            self.total_output_tokens += output_tokens
            self.request_count += 1

            logger.info(
                "Token usage",
                request_input=input_tokens,
                request_output=output_tokens,
                total_input=self.total_input_tokens,
                total_output=self.total_output_tokens,
                total_requests=self.request_count,
            )


def get_token_stats() -> dict[str, int]:
    """Get current request's token usage."""
    return _request_tokens.get().copy()
```

### Step 6: Apply Middleware to HuggingFaceChatClient (15 min)

```python
# src/clients/huggingface.py - Update __init__

from src.middleware.retry import RetryMiddleware
from src.middleware.token_tracking import TokenTrackingMiddleware

@use_function_invocation
@use_observability
@use_chat_middleware
class HuggingFaceChatClient(BaseChatClient):
    def __init__(
        self,
        model_id: str | None = None,
        api_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        # Create middleware instances
        middleware = [
            RetryMiddleware(max_attempts=3, min_wait=1.0, max_wait=10.0),
            TokenTrackingMiddleware(),
        ]

        super().__init__(middleware=middleware, **kwargs)
        # ... rest of __init__
```

### Step 7: Update Tests (20 min)

```python
# tests/unit/middleware/test_retry.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.middleware.retry import RetryMiddleware


@pytest.mark.asyncio
async def test_retry_middleware_succeeds_first_try():
    """RetryMiddleware should pass through on success."""
    middleware = RetryMiddleware(max_attempts=3)
    context = MagicMock()
    next_fn = AsyncMock()

    await middleware.process(context, next_fn)

    next_fn.assert_called_once_with(context)


@pytest.mark.asyncio
async def test_retry_middleware_retries_on_429():
    """RetryMiddleware should retry on 429 rate limit."""
    middleware = RetryMiddleware(max_attempts=3, min_wait=0.01)
    context = MagicMock()

    # First two calls fail with 429, third succeeds
    call_count = 0

    async def mock_next(ctx):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            error = Exception("Rate limited")
            error.response = MagicMock(status_code=429)
            raise error

    await middleware.process(context, mock_next)
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_middleware_raises_after_max_attempts():
    """RetryMiddleware should raise after max attempts exhausted."""
    middleware = RetryMiddleware(max_attempts=2, min_wait=0.01)
    context = MagicMock()

    async def always_fails(ctx):
        error = Exception("Always fails")
        error.response = MagicMock(status_code=500)
        raise error

    with pytest.raises(Exception, match="Always fails"):
        await middleware.process(context, always_fails)
```

---

## Implementation Checklist

### Phase 1: Folder Rename
- [ ] `git mv src/middleware src/workflows`
- [ ] Update import in `src/orchestrators/hierarchical.py`
- [ ] Update `src/workflows/__init__.py` docstring
- [ ] Run `make check` - verify no import errors

### Phase 2: Create Middleware Package
- [ ] Create `src/middleware/__init__.py`
- [ ] Create `src/middleware/retry.py` with `RetryMiddleware`
- [ ] Create `src/middleware/token_tracking.py` with `TokenTrackingMiddleware`
- [ ] Run `make check` - verify no syntax errors

### Phase 3: Apply to Client
- [ ] Update `src/clients/huggingface.py` to use middleware
- [ ] Test manually: `uv run python -c "from src.clients.huggingface import HuggingFaceChatClient; print('OK')"`
- [ ] Run `make check`

### Phase 4: Tests
- [ ] Create `tests/unit/middleware/__init__.py`
- [ ] Create `tests/unit/middleware/test_retry.py`
- [ ] Create `tests/unit/middleware/test_token_tracking.py`
- [ ] Run `make test` - all tests pass

### Phase 5: Cleanup
- [ ] Remove `.gitkeep` from `src/workflows/` if present
- [ ] Run full `make check`
- [ ] Commit with message: "refactor: implement proper middleware architecture (SPEC-21)"

---

## Acceptance Criteria

1. `src/middleware/` folder contains actual `ChatMiddleware` implementations
2. `src/workflows/` folder contains `SubIterationMiddleware` (renamed from middleware)
3. `HuggingFaceChatClient` uses `RetryMiddleware` - no more crashes on 429
4. Token usage is logged via `TokenTrackingMiddleware`
5. All existing tests pass
6. `make check` passes
7. No import errors anywhere in codebase

---

## Dependencies

- **SPEC-20** should be done first (simpler, builds confidence)
- Requires `agent-framework-core` package (already installed)

---

## Gotchas & Nuances

1. **MS middleware signature:** The `process` method takes `(context, next)` where `next` is a callable
2. **Middleware order matters:** Retry should be FIRST so it wraps everything
3. **ContextVar for token tracking:** Use ContextVar for per-request isolation
4. **Don't break HierarchicalOrchestrator:** It uses `SubIterationMiddleware` - update import path
5. **BaseChatClient constructor:** Check if it accepts `middleware=` parameter - may need to register differently

---

## Testing the Fix

After implementation, verify 429 handling:

```python
# Manual test
import asyncio
from src.clients.huggingface import HuggingFaceChatClient
from agent_framework import ChatMessage, ChatOptions

async def test():
    client = HuggingFaceChatClient()
    # Make rapid requests to trigger rate limit
    for i in range(10):
        try:
            resp = await client.get_response(
                messages=[ChatMessage(role="user", text="Hello")],
                chat_options=ChatOptions(),
            )
            print(f"Request {i}: OK")
        except Exception as e:
            print(f"Request {i}: {e}")

asyncio.run(test())
```

Should see retry logs instead of immediate crashes.
