# Exception Hierarchy

> **Last Updated**: 2025-12-06

This document describes all custom exceptions in DeepBoner.

## Location

All exceptions are defined in `src/utils/exceptions.py`.

## Exception Tree

```
Exception (Python builtin)
    └── DeepBonerError (base)
            ├── SearchError
            │       └── RateLimitError
            ├── JudgeError
            ├── ConfigurationError
            ├── EmbeddingError
            ├── LLMError
            │       └── QuotaExceededError
            └── SynthesisError
```

---

## Base Exception

### DeepBonerError

```python
class DeepBonerError(Exception):
    """Base exception for all DeepBoner errors."""
    pass
```

**When to use:** Never directly. Use specific subclasses.

**Catch when:** You want to catch all DeepBoner-related errors.

```python
try:
    result = orchestrator.run(query)
except DeepBonerError as e:
    logger.error(f"Research failed: {e}")
```

---

## Search Exceptions

### SearchError

```python
class SearchError(DeepBonerError):
    """Raised when a search operation fails."""
    pass
```

**When raised:**
- External API returns error status
- Network timeout
- Invalid response format
- No results found (in strict mode)

**Example:**
```python
from src.utils.exceptions import SearchError

if response.status_code != 200:
    raise SearchError(f"PubMed returned {response.status_code}")
```

---

### RateLimitError

```python
class RateLimitError(SearchError):
    """Raised when we hit API rate limits."""
    pass
```

**When raised:**
- HTTP 429 (Too Many Requests)
- PubMed rate limit exceeded
- ClinicalTrials.gov throttling

**Handling:**
```python
from src.utils.exceptions import RateLimitError

try:
    results = pubmed.search(query)
except RateLimitError:
    await asyncio.sleep(60)  # Wait and retry
    results = pubmed.search(query)
```

**Prevention:**
- Add `NCBI_API_KEY` for higher PubMed limits
- Use built-in rate limiter (`src/tools/rate_limiter.py`)

---

## Judge Exceptions

### JudgeError

```python
class JudgeError(DeepBonerError):
    """Raised when the judge fails to assess evidence."""
    pass
```

**When raised:**
- LLM fails to produce valid assessment
- Assessment parsing fails
- Confidence below threshold
- Invalid judge response format

**Example:**
```python
from src.utils.exceptions import JudgeError

if not assessment.details:
    raise JudgeError("Judge produced incomplete assessment")
```

---

## Configuration Exceptions

### ConfigurationError

```python
class ConfigurationError(DeepBonerError):
    """Raised when configuration is invalid."""
    pass
```

**When raised:**
- Required API key missing
- Invalid setting value
- Environment variable malformed
- Conflicting configuration

**Example:**
```python
from src.utils.exceptions import ConfigurationError

def get_api_key(self) -> str:
    if not self.openai_api_key:
        raise ConfigurationError("OPENAI_API_KEY not set")
    return self.openai_api_key
```

---

## Embedding Exceptions

### EmbeddingError

```python
class EmbeddingError(DeepBonerError):
    """Raised when embedding or vector store operations fail."""
    pass
```

**When raised:**
- ChromaDB connection failure
- Sentence-transformers model load failure
- Vector dimension mismatch
- Embedding generation fails

**Example:**
```python
from src.utils.exceptions import EmbeddingError

try:
    embeddings = model.encode(texts)
except Exception as e:
    raise EmbeddingError(f"Embedding failed: {e}")
```

---

## LLM Exceptions

### LLMError

```python
class LLMError(DeepBonerError):
    """Raised when LLM operations fail (API errors, parsing errors, etc.)."""
    pass
```

**When raised:**
- LLM API error
- Response parsing failure
- Invalid model output
- Context length exceeded

---

### QuotaExceededError

```python
class QuotaExceededError(LLMError):
    """Raised when LLM API quota is exceeded (402 errors)."""
    pass
```

**When raised:**
- OpenAI billing limit hit
- HuggingFace rate limit exceeded
- HTTP 402 Payment Required

**Handling:**
```python
from src.utils.exceptions import QuotaExceededError

try:
    response = client.chat_completion(messages)
except QuotaExceededError:
    # Fall back to free tier or notify user
    return fallback_response()
```

---

## Synthesis Exceptions

### SynthesisError

```python
class SynthesisError(DeepBonerError):
    """Raised when report synthesis fails after trying all available models.

    Attributes:
        message: Human-readable error description
        attempted_models: List of model IDs that were tried
        errors: List of error messages from each failed attempt
    """

    def __init__(
        self,
        message: str,
        attempted_models: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.attempted_models = attempted_models or []
        self.errors = errors or []
```

**When raised:**
- All LLM models fail to synthesize report
- Report generation exceeds retry limit

**Example:**
```python
from src.utils.exceptions import SynthesisError

if all_attempts_failed:
    raise SynthesisError(
        "Failed to synthesize report",
        attempted_models=["gpt-5", "gpt-4o"],
        errors=["Rate limit", "Context too long"]
    )
```

**Accessing details:**
```python
try:
    report = synthesize(evidence)
except SynthesisError as e:
    print(f"Failed: {e}")
    print(f"Tried models: {e.attempted_models}")
    print(f"Errors: {e.errors}")
```

---

## Usage Patterns

### Catching Specific Exceptions

```python
from src.utils.exceptions import (
    SearchError,
    RateLimitError,
    JudgeError,
)

try:
    result = orchestrator.run(query)
except RateLimitError:
    # Specific handling for rate limits
    await rate_limiter.wait()
    result = orchestrator.run(query)
except SearchError:
    # General search failure
    return empty_result()
except JudgeError:
    # Judge failed, use default assessment
    return default_assessment()
```

### Exception Chaining

```python
try:
    response = api_call()
except requests.RequestException as e:
    raise SearchError(f"API call failed: {e}") from e
```

### Logging Exceptions

```python
import structlog

logger = structlog.get_logger()

try:
    results = search(query)
except DeepBonerError as e:
    logger.error("operation_failed", error=str(e), exc_info=True)
    raise
```

---

## Best Practices

1. **Use specific exceptions** - Don't raise `DeepBonerError` directly
2. **Include context** - Error messages should explain what failed
3. **Chain exceptions** - Use `from e` to preserve stack trace
4. **Log before re-raising** - Capture context for debugging
5. **Handle at boundaries** - Catch exceptions at API/UI boundaries

---

## Related Documentation

- [Component Inventory](component-inventory.md)
- [Data Models](data-models.md)
- [Troubleshooting](../getting-started/troubleshooting.md)
