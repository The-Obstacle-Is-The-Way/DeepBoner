# Phase 2 Implementation Spec: Search Vertical Slice

**Goal**: Implement the "Eyes and Ears" of the agent — retrieving real biomedical data.
**Philosophy**: "Real data, mocked connections."
**Estimated Effort**: 3-4 hours
**Prerequisite**: Phase 1 complete

---

## 1. The Slice Definition

This slice covers:
1. **Input**: A string query (e.g., "metformin Alzheimer's disease").
2. **Process**:
   - Fetch from PubMed (E-utilities API).
   - Fetch from Web (DuckDuckGo).
   - Normalize results into `Evidence` models.
3. **Output**: A list of `Evidence` objects.

**Files**:
- `src/utils/models.py`: Data models
- `src/tools/pubmed.py`: PubMed implementation
- `src/tools/websearch.py`: DuckDuckGo implementation
- `src/tools/search_handler.py`: Orchestration

---

## 2. Models (`src/utils/models.py`)

> **Note**: All models go in `src/utils/models.py` to avoid circular imports.

```python
"""Data models for DeepCritical."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Literal, List, Any
from datetime import date


class Citation(BaseModel):
    """A citation to a source document."""

    source: Literal["pubmed", "web"] = Field(description="Where this came from")
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(description="URL to the source")
    date: str = Field(description="Publication date (YYYY-MM-DD or 'Unknown')")
    authors: list[str] = Field(default_factory=list)

    @property
    def formatted(self) -> str:
        """Format as a citation string."""
        author_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            author_str += " et al."
        return f"{author_str} ({self.date}). {self.title}. {self.source.upper()}"


class Evidence(BaseModel):
    """A piece of evidence retrieved from search."""

    content: str = Field(min_length=1, description="The actual text content")
    citation: Citation
    relevance: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score 0-1")

    class Config:
        frozen = True  # Immutable after creation


class SearchResult(BaseModel):
    """Result of a search operation."""

    query: str
    evidence: list[Evidence]
    sources_searched: list[Literal["pubmed", "web"]]
    total_found: int
    errors: list[str] = Field(default_factory=list)
```

---

## 3. Tool Protocol (`src/tools/__init__.py`)

```python
"""Search tools package."""
from typing import Protocol, List
from src.utils.models import Evidence


class SearchTool(Protocol):
    """Protocol defining the interface for all search tools."""

    @property
    def name(self) -> str:
        """Human-readable name of this tool."""
        ...

    async def search(self, query: str, max_results: int = 10) -> List[Evidence]:
        """Execute a search and return evidence."""
        ...
```

---

## 4. Implementations

### PubMed Tool (`src/tools/pubmed.py`)

```python
"""PubMed search tool using NCBI E-utilities."""
import asyncio
import httpx
import xmltodict
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.exceptions import SearchError, RateLimitError
from src.utils.models import Evidence, Citation


class PubMedTool:
    """Search tool for PubMed/NCBI."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    RATE_LIMIT_DELAY = 0.34  # ~3 requests/sec without API key

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self._last_request_time = 0.0

    @property
    def name(self) -> str:
        return "pubmed"

    async def _rate_limit(self) -> None:
        """Enforce NCBI rate limiting."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    # ... (rest of implementation same as previous, ensuring imports match) ...
```

### DuckDuckGo Tool (`src/tools/websearch.py`)

```python
"""Web search tool using DuckDuckGo."""
from typing import List
from duckduckgo_search import DDGS

from src.utils.exceptions import SearchError
from src.utils.models import Evidence, Citation


class WebTool:
    """Search tool for general web search via DuckDuckGo."""

    def __init__(self):
        pass

    @property
    def name(self) -> str:
        return "web"

    async def search(self, query: str, max_results: int = 10) -> List[Evidence]:
        """Search DuckDuckGo and return evidence."""
        # ... (implementation same as previous) ...
```

### Search Handler (`src/tools/search_handler.py`)

```python
"""Search handler - orchestrates multiple search tools."""
import asyncio
from typing import List
import structlog

from src.utils.exceptions import SearchError
from src.utils.models import Evidence, SearchResult
from src.tools import SearchTool

logger = structlog.get_logger()

class SearchHandler:
    """Orchestrates parallel searches across multiple tools."""
    
    # ... (implementation same as previous, imports corrected) ...
```

---

## 5. TDD Workflow

### Test File: `tests/unit/tools/test_search.py`

```python
"""Unit tests for search tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestWebTool:
    """Tests for WebTool."""

    @pytest.mark.asyncio
    async def test_search_returns_evidence(self, mocker):
        from src.tools.websearch import WebTool

        mock_results = [{"title": "Test", "href": "url", "body": "content"}]
        
        # MOCK THE CORRECT IMPORT PATH
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=None)
        mock_ddgs.text = MagicMock(return_value=mock_results)

        mocker.patch("src.tools.websearch.DDGS", return_value=mock_ddgs)

        tool = WebTool()
        results = await tool.search("query")
        assert len(results) == 1
```

---

## 6. Implementation Checklist

- [ ] Add models to `src/utils/models.py`
- [ ] Create `src/tools/__init__.py` (Protocol)
- [ ] Implement `src/tools/pubmed.py`
- [ ] Implement `src/tools/websearch.py`
- [ ] Implement `src/tools/search_handler.py`
- [ ] Write tests in `tests/unit/tools/test_search.py`
- [ ] Run `uv run pytest tests/unit/tools/`