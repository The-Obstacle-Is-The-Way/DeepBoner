# Testing Guide

> **Last Updated**: 2025-12-06

This guide covers testing strategy, patterns, and best practices for DeepBoner.

## Quick Reference

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific file
uv run pytest tests/unit/utils/test_config.py -v

# Run specific test
uv run pytest tests/unit/utils/test_config.py::TestSettings::test_default -v

# Run by marker
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests only
uv run pytest -m "not slow"    # Skip slow tests
```

## Test Organization

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests (mocked, fast)
│   ├── orchestrators/
│   ├── agents/
│   ├── clients/
│   ├── tools/
│   ├── services/
│   ├── utils/
│   ├── prompts/
│   ├── agent_factory/
│   ├── config/
│   ├── graph/
│   └── mcp/
├── integration/                # Integration tests (real APIs)
└── e2e/                        # End-to-end tests
```

### Directory Mapping

Tests mirror the `src/` structure:
- `src/tools/pubmed.py` → `tests/unit/tools/test_pubmed.py`
- `src/utils/config.py` → `tests/unit/utils/test_config.py`

## Test Markers

### Available Markers

| Marker | Purpose | Example |
|--------|---------|---------|
| `@pytest.mark.unit` | Unit tests (mocked) | Most tests |
| `@pytest.mark.integration` | Real API calls | API testing |
| `@pytest.mark.slow` | Long-running tests | Full pipeline |
| `@pytest.mark.e2e` | End-to-end tests | Complete flows |

### Using Markers

```python
import pytest

@pytest.mark.unit
def test_search_returns_results():
    """Unit test with mocked API."""
    pass

@pytest.mark.integration
def test_pubmed_real_api():
    """Integration test with real PubMed API."""
    pass
```

### Running by Marker

```bash
uv run pytest -m unit              # Only unit tests
uv run pytest -m "not integration" # Skip integration tests
uv run pytest -m "unit or slow"    # Unit OR slow tests
```

## Test Fixtures

### Core Fixtures (conftest.py)

#### `mock_httpx_client`

Mocks httpx for HTTP testing:

```python
def test_pubmed_search(mock_httpx_client):
    mock_httpx_client.get("https://eutils.ncbi.nlm.nih.gov/...").respond(
        200,
        json={"esearchresult": {"idlist": ["12345"]}}
    )

    tool = PubMedTool()
    result = tool.search("test query")
    assert len(result.evidence) > 0
```

#### `mock_llm_response`

Mocks LLM completions:

```python
def test_judge_evaluates(mock_llm_response):
    mock_llm_response("The evidence is sufficient.")

    judge = JudgeAgent()
    assessment = judge.assess(evidence)
    assert assessment.sufficient
```

#### `sample_evidence`

Provides test evidence data:

```python
def test_synthesis(sample_evidence):
    report = synthesizer.create_report(sample_evidence)
    assert report.title
```

### Creating Fixtures

```python
# tests/conftest.py

@pytest.fixture
def mock_search_handler(mocker):
    """Mock SearchHandler for unit tests."""
    handler = mocker.Mock(spec=SearchHandler)
    handler.search_all.return_value = SearchResult(
        query="test",
        evidence=[],
        sources_searched=["pubmed"],
        total_found=0
    )
    return handler
```

## Mocking Patterns

### HTTP Mocking with respx

```python
import respx
from httpx import Response

@pytest.mark.unit
def test_api_call():
    with respx.mock:
        respx.get("https://api.example.com/data").mock(
            return_value=Response(200, json={"result": "ok"})
        )

        result = make_api_call()
        assert result == "ok"
```

### General Mocking with pytest-mock

```python
def test_with_mock(mocker):
    # Mock a function
    mock_func = mocker.patch("src.tools.pubmed.fetch_results")
    mock_func.return_value = {"results": []}

    # Mock a class method
    mocker.patch.object(PubMedTool, "search", return_value=[])

    # Mock a property
    mocker.patch.object(Settings, "has_openai_key", True)
```

### Mocking Async Functions

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_async_search(mocker):
    mock_search = AsyncMock(return_value=[])
    mocker.patch.object(SearchHandler, "search_all", mock_search)

    result = await handler.search_all("query")
    assert result == []
```

## Writing Tests

### Test Structure (AAA Pattern)

```python
def test_search_handler_aggregates_results():
    """Verify search handler combines results from multiple sources."""
    # Arrange
    handler = SearchHandler()
    query = "testosterone therapy"

    # Act
    result = handler.search_all(query)

    # Assert
    assert len(result.evidence) > 0
    assert "pubmed" in result.sources_searched
```

### Test Naming

```python
# Good: Describes behavior
def test_judge_returns_continue_when_evidence_insufficient():
    pass

def test_search_raises_rate_limit_error_on_429():
    pass

# Bad: Vague
def test_judge():
    pass

def test_search_error():
    pass
```

### Testing Exceptions

```python
import pytest
from src.utils.exceptions import SearchError

def test_search_raises_on_api_failure():
    """Verify SearchError is raised when API returns error."""
    with pytest.raises(SearchError) as exc_info:
        search_with_failing_api()

    assert "API returned 500" in str(exc_info.value)
```

### Async Tests

```python
import pytest

@pytest.mark.asyncio
async def test_async_search():
    """Test async search operation."""
    result = await search_handler.search_all("query")
    assert result is not None
```

## Test Data

### Using Factories

```python
# tests/factories.py

def make_evidence(
    content: str = "Test content",
    source: str = "pubmed",
    relevance: float = 0.8
) -> Evidence:
    return Evidence(
        content=content,
        citation=Citation(
            source=source,
            title="Test Paper",
            url="https://test.com",
            date="2024-01-01",
            authors=["Test Author"]
        ),
        relevance=relevance,
        metadata={}
    )
```

### Parameterized Tests

```python
import pytest

@pytest.mark.parametrize("query,expected_count", [
    ("testosterone", 10),
    ("estrogen therapy", 5),
    ("very specific rare condition", 0),
])
def test_search_returns_expected_results(query, expected_count, mock_api):
    result = search(query)
    assert len(result.evidence) == expected_count
```

## Coverage

### Running with Coverage

```bash
# Terminal report
make test-cov

# HTML report
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Coverage Configuration

From `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
omit = ["*/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

### Coverage Targets

| Module | Target | Notes |
|--------|--------|-------|
| `utils/` | 90%+ | Core utilities |
| `tools/` | 80%+ | API wrappers |
| `orchestrators/` | 70%+ | Complex logic |
| `agents/` | 70%+ | LLM-dependent |

## CI Integration

Tests run in GitHub Actions:

```yaml
# .github/workflows/ci.yml
- name: Run Tests
  run: uv run pytest --cov=src --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v4
```

## Best Practices

### Do

- Write tests before implementation (TDD)
- Use descriptive test names
- Test edge cases and error conditions
- Keep tests fast (mock external dependencies)
- Use fixtures for shared setup
- Test one behavior per test

### Don't

- Test implementation details
- Make tests dependent on order
- Use real API keys in tests
- Skip error handling tests
- Leave flaky tests unfixed

## Troubleshooting

### Tests pass locally but fail in CI

1. Check for hardcoded paths
2. Verify timezone handling
3. Look for async timing issues
4. Check environment variables

### Async test hangs

```python
# Add timeout
@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_with_timeout():
    pass
```

### Mock not working

```python
# Ensure correct import path
mocker.patch("src.tools.pubmed.PubMedTool")  # Correct
mocker.patch("tools.pubmed.PubMedTool")       # Wrong
```

---

## Related Documentation

- [Code Style Guide](code-style.md)
- [Contributing Guide](../../CONTRIBUTING.md)
- [Component Inventory](../architecture/component-inventory.md)
