"""Unit tests for bioRxiv tool."""

import pytest
import respx
from httpx import Response

from src.tools.biorxiv import BioRxivTool
from src.utils.models import Evidence


@pytest.fixture
def mock_biorxiv_response():
    """Mock bioRxiv API response."""
    return {
        "collection": [
            {
                "doi": "10.1101/2024.01.15.24301234",
                "title": "Metformin repurposing for Alzheimer's disease: a systematic review",
                "authors": "Smith, John; Jones, Alice; Brown, Bob",
                "date": "2024-01-15",
                "category": "neurology",
                "abstract": "Background: Metformin has shown neuroprotective effects. "
                "We conducted a systematic review of metformin's potential "
                "for Alzheimer's disease treatment.",
            },
            {
                "doi": "10.1101/2024.01.10.24301111",
                "title": "COVID-19 vaccine efficacy study",
                "authors": "Wilson, C",
                "date": "2024-01-10",
                "category": "infectious diseases",
                "abstract": "This study evaluates COVID-19 vaccine efficacy.",
            },
        ],
        "messages": [{"status": "ok", "count": 2}],
    }


class TestBioRxivTool:
    """Tests for BioRxivTool."""

    def test_tool_name(self):
        """Tool should have correct name."""
        tool = BioRxivTool()
        assert tool.name == "biorxiv"

    def test_default_server_is_medrxiv(self):
        """Default server should be medRxiv for medical relevance."""
        tool = BioRxivTool()
        assert tool.server == "medrxiv"

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_returns_evidence(self, mock_biorxiv_response):
        """Search should return Evidence objects."""
        respx.get(url__startswith="https://api.biorxiv.org/details").mock(
            return_value=Response(200, json=mock_biorxiv_response)
        )

        tool = BioRxivTool()
        results = await tool.search("metformin alzheimer", max_results=5)

        assert len(results) == 1  # Only the matching paper
        assert isinstance(results[0], Evidence)
        assert results[0].citation.source == "biorxiv"
        assert "metformin" in results[0].citation.title.lower()

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_filters_by_keywords(self, mock_biorxiv_response):
        """Search should filter papers by query keywords."""
        respx.get(url__startswith="https://api.biorxiv.org/details").mock(
            return_value=Response(200, json=mock_biorxiv_response)
        )

        tool = BioRxivTool()

        # Search for metformin - should match first paper
        results = await tool.search("metformin")
        assert len(results) == 1
        assert "metformin" in results[0].citation.title.lower()

        # Search for COVID - should match second paper
        results = await tool.search("covid vaccine")
        assert len(results) == 1
        assert "covid" in results[0].citation.title.lower()

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_marks_as_preprint(self, mock_biorxiv_response):
        """Evidence content should note it's a preprint."""
        respx.get(url__startswith="https://api.biorxiv.org/details").mock(
            return_value=Response(200, json=mock_biorxiv_response)
        )

        tool = BioRxivTool()
        results = await tool.search("metformin")

        assert "PREPRINT" in results[0].content
        assert "Not peer-reviewed" in results[0].content

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_empty_results(self):
        """Search should handle empty results gracefully."""
        respx.get(url__startswith="https://api.biorxiv.org/details").mock(
            return_value=Response(200, json={"collection": [], "messages": []})
        )

        tool = BioRxivTool()
        results = await tool.search("xyznonexistent")

        assert results == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_api_error(self):
        """Search should raise SearchError on API failure."""
        from src.utils.exceptions import SearchError

        respx.get(url__startswith="https://api.biorxiv.org/details").mock(
            return_value=Response(500, text="Internal Server Error")
        )

        tool = BioRxivTool()

        with pytest.raises(SearchError):
            await tool.search("metformin")

    def test_extract_terms(self):
        """Should extract meaningful search terms."""
        tool = BioRxivTool()

        terms = tool._extract_terms("metformin for Alzheimer's disease")

        assert "metformin" in terms
        assert "alzheimer" in terms
        assert "disease" in terms
        assert "for" not in terms  # Stop word
        assert "the" not in terms  # Stop word


class TestBioRxivIntegration:
    """Integration tests (marked for separate run)."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        """Test actual API call (requires network)."""
        tool = BioRxivTool(days=30)  # Last 30 days
        results = await tool.search("diabetes", max_results=3)

        # May or may not find results depending on recent papers
        # But we want to ensure the code runs without crashing
        assert isinstance(results, list)
        if results:
            r = results[0]
            assert isinstance(r, Evidence)
            assert r.citation.source == "biorxiv"
