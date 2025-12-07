# SPEC-20: PubMed JSON Parsing Fix

**Status:** READY FOR IMPLEMENTATION
**Priority:** P2 (Critical - causes crashes)
**Effort:** 15 minutes
**PR Scope:** Single file fix

---

## Problem Statement

The PubMed search tool crashes when the API returns non-JSON responses (maintenance pages, error pages). The JSON parsing happens **outside** the try/except block.

**File:** `src/tools/pubmed.py:88`
**Crash Type:** `json.JSONDecodeError`
**User Impact:** Entire research workflow crashes

---

## Current Code (BROKEN)

```python
# src/tools/pubmed.py - Lines ~80-95
try:
    search_resp = await client.get(
        f"{NCBI_BASE_URL}/esearch.fcgi",
        params=search_params,
    )
    search_resp.raise_for_status()
except httpx.HTTPStatusError as e:
    logger.warning("PubMed search failed", status=e.response.status_code)
    return []

# ↓↓↓ THIS IS OUTSIDE THE TRY BLOCK ↓↓↓
search_data = search_resp.json()  # CRASHES HERE on maintenance pages
pmids = search_data.get("esearchresult", {}).get("idlist", [])
```

---

## Required Fix

Move JSON parsing inside try/except and add `JSONDecodeError` handling:

```python
# src/tools/pubmed.py - Fixed version
try:
    search_resp = await client.get(
        f"{NCBI_BASE_URL}/esearch.fcgi",
        params=search_params,
    )
    search_resp.raise_for_status()
    search_data = search_resp.json()  # ← MOVED INSIDE TRY
except httpx.HTTPStatusError as e:
    logger.warning("PubMed search failed", status=e.response.status_code)
    return []
except json.JSONDecodeError as e:
    logger.warning(
        "PubMed returned invalid JSON (possible maintenance page)",
        error=str(e),
        response_preview=search_resp.text[:200] if search_resp else "N/A",
    )
    return []

pmids = search_data.get("esearchresult", {}).get("idlist", [])
```

---

## Implementation Checklist

- [ ] Add `import json` at top of file (if not present)
- [ ] Move `search_resp.json()` inside try block (line ~88)
- [ ] Add `except json.JSONDecodeError` handler
- [ ] Log warning with response preview for debugging
- [ ] Return empty list (graceful degradation)
- [ ] Write unit test: mock response with HTML content
- [ ] Run `make check` (lint + typecheck + test)

---

## Test Case

```python
# tests/unit/tools/test_pubmed.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.tools.pubmed import search_pubmed

@pytest.mark.asyncio
async def test_pubmed_handles_maintenance_page():
    """PubMed should gracefully handle non-JSON responses."""
    # Mock httpx client returning HTML maintenance page
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><body>Service Temporarily Unavailable</body></html>"
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    # Should return empty list, not crash
    result = await search_pubmed("test query", client=mock_client)
    assert result == []
```

---

## Acceptance Criteria

1. `search_pubmed()` returns `[]` when API returns HTML
2. Warning logged with response preview
3. No `JSONDecodeError` propagates to caller
4. All existing tests pass
5. `make check` passes

---

## Dependencies

None. This is a standalone fix.

---

## Notes

- This same pattern may exist in `clinicaltrials.py` and `europepmc.py` - check after this fix
- Do NOT over-engineer. Single fix, single PR.
