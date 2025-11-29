# Phase 11 Implementation Spec: Europe PMC Integration

> **Status**: ✅ COMPLETE
> **Implemented**: `src/tools/europepmc.py`
> **Tests**: `tests/unit/tools/test_europepmc.py`

## Overview

Europe PMC provides access to preprints and peer-reviewed literature through a single, well-designed REST API. This replaces the originally planned bioRxiv integration due to bioRxiv's API limitations (no keyword search).

## Why Europe PMC Over bioRxiv?

### bioRxiv API Limitations (Why We Abandoned It)
- bioRxiv API does NOT support keyword search
- Only supports date-range queries returning all papers
- Would require downloading entire date ranges and filtering client-side
- Inefficient and impractical for our use case

### Europe PMC Advantages
1. **Full keyword search** - Query by any term
2. **Aggregates preprints** - Includes bioRxiv, medRxiv, ChemRxiv content
3. **No authentication required** - Free, open API
4. **34+ preprint servers indexed** - Not just bioRxiv
5. **REST API with JSON** - Easy integration

## API Reference

**Base URL**: `https://www.ebi.ac.uk/europepmc/webservices/rest/search`

**Documentation**: https://europepmc.org/RestfulWebService

### Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `query` | string | Search keywords |
| `resultType` | `core` | Full metadata including abstracts |
| `pageSize` | 1-100 | Results per page |
| `format` | `json` | Response format |

### Example Request

```
GET https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=metformin+alzheimer&resultType=core&pageSize=10&format=json
```

## Implementation

### EuropePMCTool (`src/tools/europepmc.py`)

```python
class EuropePMCTool:
    """
    Search Europe PMC for papers and preprints.

    Europe PMC indexes:
    - PubMed/MEDLINE articles
    - PMC full-text articles
    - Preprints from bioRxiv, medRxiv, ChemRxiv, etc.
    - Patents and clinical guidelines
    """

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    @property
    def name(self) -> str:
        return "europepmc"

    async def search(self, query: str, max_results: int = 10) -> list[Evidence]:
        """Search Europe PMC for papers matching query."""
        # Implementation with retry logic, error handling
```

### Key Features

1. **Preprint Detection**: Automatically identifies preprints via `pubTypeList`
2. **Preprint Marking**: Adds `[PREPRINT - Not peer-reviewed]` prefix to content
3. **Relevance Scoring**: Preprints get 0.75, peer-reviewed get 0.9
4. **URL Resolution**: DOI → PubMed → Europe PMC fallback chain
5. **Retry Logic**: 3 attempts with exponential backoff via tenacity

### Response Mapping

| Europe PMC Field | Evidence Field |
|------------------|----------------|
| `title` | `citation.title` |
| `abstractText` | `content` |
| `doi` | Used for URL |
| `pubYear` | `citation.date` |
| `authorList.author` | `citation.authors` |
| `pubTypeList.pubType` | Determines `citation.source` ("preprint" or "europepmc") |

## Unit Tests

### Test Coverage (`tests/unit/tools/test_europepmc.py`)

| Test | Description |
|------|-------------|
| `test_tool_name` | Verifies tool name is "europepmc" |
| `test_search_returns_evidence` | Basic search returns Evidence objects |
| `test_search_marks_preprints` | Preprints have [PREPRINT] marker and source="preprint" |
| `test_search_empty_results` | Handles empty results gracefully |

### Integration Test

```python
@pytest.mark.integration
async def test_real_api_call():
    """Test actual API returns relevant results."""
    tool = EuropePMCTool()
    results = await tool.search("long covid treatment", max_results=3)
    assert len(results) > 0
```

## SearchHandler Integration

Europe PMC is included in `src/tools/search_handler.py` alongside PubMed and ClinicalTrials:

```python
from src.tools.europepmc import EuropePMCTool

class SearchHandler:
    def __init__(self):
        self.tools = [
            PubMedTool(),
            ClinicalTrialsTool(),
            EuropePMCTool(),  # Preprints + peer-reviewed
        ]
```

## MCP Tools Integration

Europe PMC is exposed via MCP in `src/mcp_tools.py`:

```python
async def search_europepmc(query: str, max_results: int = 10) -> str:
    """Search Europe PMC for preprints and papers."""
    results = await _europepmc.search(query, max_results)
    # Format and return
```

## Verification

```bash
# Run unit tests
uv run pytest tests/unit/tools/test_europepmc.py -v

# Run integration test (real API)
uv run pytest tests/unit/tools/test_europepmc.py -v -m integration
```

## Completion Checklist

- [x] `src/tools/europepmc.py` implemented
- [x] Unit tests in `tests/unit/tools/test_europepmc.py`
- [x] Integration test with real API
- [x] SearchHandler includes EuropePMCTool
- [x] MCP wrapper in `src/mcp_tools.py`
- [x] Preprint detection and marking
- [x] Retry logic with exponential backoff

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    SearchHandler                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ PubMedTool  │  │ClinicalTrials│  │ EuropePMCTool │  │
│  │             │  │    Tool      │  │               │  │
│  │ Peer-review │  │   Trials     │  │  Preprints +  │  │
│  │  articles   │  │   data       │  │  peer-review  │  │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                │                  │          │
│         ▼                ▼                  ▼          │
│    ┌─────────────────────────────────────────────┐     │
│    │              Evidence List                  │     │
│    │  (deduplicated, scored, with citations)     │     │
│    └─────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```
