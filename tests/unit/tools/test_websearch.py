"""Tests for WebSearchTool."""

from unittest.mock import MagicMock, patch

import pytest

from src.tools.websearch import WebSearchTool


@pytest.mark.asyncio
async def test_websearch_tool():
    tool = WebSearchTool()
    assert tool.name == "web_search"

    with patch("src.tools.websearch.DDGS") as mock_ddgs:
        # Mock context manager
        mock_instance = MagicMock()
        mock_ddgs.return_value.__enter__.return_value = mock_instance

        mock_instance.text.return_value = [
            {"title": "T1", "href": "http://u1", "body": "C1"},
            {"title": "T2", "href": "http://u2", "body": "C2"},
        ]

        results = await tool.search("query", 2)

        assert len(results) == 2
        assert results[0].citation.title == "T1"
        assert results[0].content == "C1"
        assert results[0].citation.url == "http://u1"
        assert results[0].citation.source == "web"
