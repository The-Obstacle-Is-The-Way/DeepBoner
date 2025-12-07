# Code Style Guide

> **Last Updated**: 2025-12-06

This guide covers code style conventions and tooling for DeepBoner.

## Quick Reference

```bash
# Auto-format code
make format

# Check linting
make lint

# Type check
make typecheck

# Run all checks
make check
```

## Tooling

### Ruff (Linting & Formatting)

Configuration in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes
    "B",    # flake8-bugbear
    "I",    # isort
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "PL",   # pylint
    "RUF",  # ruff-specific
]
```

### MyPy (Type Checking)

Configuration in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
disallow_untyped_defs = true
warn_return_any = true
```

### Pre-commit Hooks

Hooks run automatically on commit:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
```

## Python Style

### Type Hints

All functions must have type annotations:

```python
# Good
def search(query: str, limit: int = 10) -> list[Evidence]:
    """Search for evidence."""
    pass

# Bad
def search(query, limit=10):
    pass
```

Use modern type hint syntax (Python 3.11+):

```python
# Good
def process(items: list[str] | None) -> dict[str, int]:
    pass

# Avoid (old syntax)
from typing import List, Dict, Optional
def process(items: Optional[List[str]]) -> Dict[str, int]:
    pass
```

### Docstrings

Use Google-style docstrings for public APIs:

```python
def search_pubmed(query: str, max_results: int = 10) -> SearchResult:
    """Search PubMed for biomedical literature.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return.

    Returns:
        SearchResult containing evidence and metadata.

    Raises:
        SearchError: If the API call fails.
        RateLimitError: If rate limit is exceeded.
    """
    pass
```

### Class Documentation

```python
class SearchHandler:
    """Orchestrates parallel searches across multiple sources.

    This handler implements a scatter-gather pattern to query
    multiple biomedical databases simultaneously.

    Attributes:
        sources: List of enabled search sources.
        timeout: Timeout for each search in seconds.

    Example:
        handler = SearchHandler()
        result = handler.search_all("testosterone therapy")
    """

    def __init__(self, sources: list[str] | None = None) -> None:
        """Initialize the search handler.

        Args:
            sources: Optional list of sources to enable.
                    Defaults to all sources.
        """
        pass
```

### Imports

Imports are sorted by isort (via ruff):

```python
# Standard library
import asyncio
from datetime import datetime
from typing import Any

# Third-party
import httpx
from pydantic import BaseModel

# Local
from src.utils.config import settings
from src.utils.exceptions import SearchError
```

### Line Length

Maximum 100 characters. Break long lines:

```python
# Good - break at logical points
result = very_long_function_name(
    first_argument=value1,
    second_argument=value2,
    third_argument=value3,
)

# Good - string continuation
message = (
    "This is a very long message that needs to be "
    "split across multiple lines for readability."
)
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `SearchHandler` |
| Functions | snake_case | `search_pubmed` |
| Variables | snake_case | `max_results` |
| Constants | UPPER_SNAKE | `MAX_ITERATIONS` |
| Private | leading underscore | `_internal_method` |
| Type vars | PascalCase | `T`, `ConfigT` |

### Exceptions

Custom exceptions in `src/utils/exceptions.py`:

```python
from src.utils.exceptions import SearchError

# Raising
raise SearchError(f"API returned {status_code}")

# With cause
try:
    response = client.get(url)
except httpx.HTTPError as e:
    raise SearchError(f"Request failed: {e}") from e
```

## Pydantic Models

### Model Definition

```python
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    """A piece of evidence from search."""

    content: str = Field(min_length=1, description="The evidence text")
    relevance: float = Field(ge=0.0, le=1.0, default=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}  # Make immutable
```

### Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    max_iterations: int = Field(default=10, ge=1, le=50)
```

## Async Code

### Async Functions

```python
async def search_async(query: str) -> SearchResult:
    """Async search implementation."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return parse_response(response)
```

### Concurrent Execution

```python
async def search_all(query: str) -> list[SearchResult]:
    """Search all sources concurrently."""
    tasks = [
        search_pubmed(query),
        search_clinicaltrials(query),
        search_europepmc(query),
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

## Comments

### When to Comment

```python
# Good: Explain WHY, not WHAT
# PubMed rate limits without API key - add delay to avoid 429
await asyncio.sleep(0.34)

# Bad: Obvious comment
# Increment counter
counter += 1
```

### TODO Comments

```python
# TODO(username): Description of what needs to be done
# TODO: Short-term fix, proper solution needs X
```

## Ignored Rules

Some rules are disabled for good reasons:

```toml
ignore = [
    "PLR0913",  # Too many arguments (agents need many params)
    "PLR0912",  # Too many branches (complex orchestrator logic)
    "PLR2004",  # Magic values (statistical constants)
    "PLW0603",  # Global statement (singleton pattern)
    "PLC0415",  # Lazy imports for optional dependencies
]
```

## File Organization

### Module Structure

```python
"""Module docstring explaining purpose."""

# Imports (sorted)
import ...

# Constants
MAX_RESULTS = 100

# Type definitions
ResultType = dict[str, Any]

# Classes
class MyClass:
    pass

# Functions
def my_function():
    pass

# Module-level code (minimize)
if __name__ == "__main__":
    main()
```

### Package Structure

```
src/tools/
├── __init__.py    # Public exports
├── base.py        # Base classes
├── pubmed.py      # PubMed implementation
├── clinicaltrials.py
└── search_handler.py
```

## Code Review Checklist

Before submitting a PR:

- [ ] All functions have type hints
- [ ] Public APIs have docstrings
- [ ] `make check` passes
- [ ] No hardcoded credentials
- [ ] Error cases are handled
- [ ] Tests cover new code

---

## Related Documentation

- [Testing Guide](testing.md)
- [Contributing Guide](../../CONTRIBUTING.md)
- [Architecture Overview](../architecture/overview.md)
