"""Unit tests for tool interactions with MagenticState."""

from unittest.mock import AsyncMock, patch

import pytest

from src.agents.tools import search_pubmed
from src.state.magentic_state import init_magentic_state, get_magentic_state
from src.utils.models import Citation, Evidence


@pytest.fixture
def mock_evidence():
    return Evidence(
        content="Test content",
        citation=Citation(
            title="Test Title",
            url="http://example.com/tool_test",
            source="pubmed",
            date="2023",
            authors=["A", "B"],
        ),
        relevance=1.0,
    )


class TestToolsState:
    """Tests that tools update the shared state."""

    @pytest.mark.asyncio
    async def test_search_pubmed_updates_state(self, mock_evidence):
        """Test search_pubmed adds results to state."""
        # Initialize state
        state = init_magentic_state()
        assert len(state.evidence) == 0

        # Mock the underlying tool to return evidence
        with patch("src.agents.tools._pubmed") as mock_tool:
            mock_tool.search = AsyncMock(return_value=[mock_evidence])

            # Call the tool function (which is wrapped by @ai_function)
            result = await search_pubmed("query", 10)

            # Verify result string contains info
            assert "Found 1 results" in result

            # Verify state was updated
            updated_state = get_magentic_state()
            assert len(updated_state.evidence) == 1
            assert updated_state.evidence[0].citation.url == mock_evidence.citation.url

    @pytest.mark.asyncio
    async def test_search_pubmed_uses_embedding_service(self, mock_evidence):
        """Test search_pubmed uses embedding service for dedup/related if available."""
        # Mock embedding service
        mock_service = AsyncMock()
        mock_service.deduplicate = AsyncMock(return_value=[mock_evidence])
        mock_service.search_similar = AsyncMock(return_value=[])

        state = init_magentic_state(embedding_service=mock_service)

        with patch("src.agents.tools._pubmed") as mock_tool:
            mock_tool.search = AsyncMock(return_value=[mock_evidence])

            await search_pubmed("query", 10)

            # Verify deduplicate was called
            mock_service.deduplicate.assert_awaited_once()
            # Verify search_similar was called
            mock_service.search_similar.assert_awaited_once()
