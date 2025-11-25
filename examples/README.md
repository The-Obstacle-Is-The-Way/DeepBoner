# Examples

Demo scripts for DeepCritical functionality.

## search_demo

Demonstrates Phase 2 search functionality:

```bash
# Run with default query (metformin + Alzheimer's)
uv run python examples/search_demo/run_search.py

# Run with custom query
uv run python examples/search_demo/run_search.py "aspirin heart disease"
```

**What it does:**
- Searches PubMed (biomedical literature)
- Searches DuckDuckGo (web)
- Runs both in parallel (scatter-gather)
- Returns evidence with citations

**Optional:** Set `NCBI_API_KEY` in `.env` for higher PubMed rate limits.
