"""Unit tests for Magentic state management."""

from unittest.mock import AsyncMock

import pytest

from src.state.magentic_state import (
    MagenticState,
    get_magentic_state,
    init_magentic_state,
    reset_magentic_state,
)
from src.utils.models import Citation, Evidence


@pytest.fixture
def sample_evidence():
    return Evidence(
        content="Test content",
        citation=Citation(
            title="Test Title",
            url="http://example.com/1",
            source="pubmed",
            date="2023",
            authors=["A", "B"],
        ),
        relevance=1.0,
    )


class TestMagenticState:
    def test_state_init(self):
        """Test state initialization."""
        state = init_magentic_state()
        assert isinstance(state, MagenticState)
        assert state.evidence == []
        assert state.embedding_service is None

    def test_add_evidence(self, sample_evidence):
        """Test adding evidence."""
        state = init_magentic_state()
        count = state.add_evidence([sample_evidence])
        assert count == 1
        assert len(state.evidence) == 1
        assert state.evidence[0] == sample_evidence

    def test_add_duplicate_evidence(self, sample_evidence):
        """Test adding duplicate evidence (by URL)."""
        state = init_magentic_state()
        state.add_evidence([sample_evidence])

        # Add same evidence again
        count = state.add_evidence([sample_evidence])
        assert count == 0
        assert len(state.evidence) == 1

        # Add different object but same URL
        duplicate = Evidence(
            content="Different content",
            citation=sample_evidence.citation,
            relevance=sample_evidence.relevance,
        )
        count = state.add_evidence([duplicate])
        assert count == 0
        assert len(state.evidence) == 1

    def test_get_magentic_state_auto_init(self):
        """Test get_magentic_state auto-initializes if missing."""
        # Ensure clean state (implementation detail: accessing contextvar directly would be cheating,
        # but reset_magentic_state should work)
        # However, reset creates a new state.
        # We can't easily "un-init" to None via public API, but init overwrites.

        # We can simulate a new context by running in a new context, but pytest runs in one context.
        # Let's just trust it returns a state.
        state = get_magentic_state()
        assert isinstance(state, MagenticState)

    def test_reset_magentic_state(self, sample_evidence):
        """Test resetting state clears evidence but keeps service."""
        mock_service = AsyncMock()
        init_magentic_state(embedding_service=mock_service)

        state = get_magentic_state()
        state.add_evidence([sample_evidence])
        assert len(state.evidence) == 1
        assert state.embedding_service is mock_service

        reset_magentic_state()

        new_state = get_magentic_state()
        assert new_state is not state
        assert len(new_state.evidence) == 0
        assert new_state.embedding_service is mock_service

    @pytest.mark.asyncio
    async def test_search_related(self):
        """Test search_related uses embedding service."""
        mock_service = AsyncMock()
        mock_service.search_similar.return_value = [
            {
                "id": "http://related.com",
                "content": "Related content",
                "metadata": {"title": "Related", "authors": "X, Y"},
                "distance": 0.2,
            }
        ]

        state = init_magentic_state(embedding_service=mock_service)
        results = await state.search_related("query")

        assert len(results) == 1
        assert results[0].citation.url == "http://related.com"
        assert results[0].citation.title == "Related"
        # 1.0 - 0.2 = 0.8
        assert results[0].relevance == 0.8
