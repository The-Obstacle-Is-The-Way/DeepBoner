"""Web search tool using DuckDuckGo."""

import structlog
from duckduckgo_search import DDGS

from src.tools.base import SearchTool
from src.utils.exceptions import SearchError
from src.utils.models import Citation, Evidence

logger = structlog.get_logger(__name__)


class WebSearchTool(SearchTool):
    """Tool for searching the web using DuckDuckGo."""

    @property
    def name(self) -> str:
        return "web_search"

    async def search(self, query: str, max_results: int = 10) -> list[Evidence]:
        """Search the web and return evidence."""
        logger.info("executing_web_search", query=query)

        try:
            # DDGS is synchronous, run in executor
            import asyncio

            loop = asyncio.get_running_loop()

            def _do_search():
                # DDGS context manager is recommended
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=max_results))

            results = await loop.run_in_executor(None, _do_search)

            evidence_list = []
            for r in results:
                evidence_list.append(
                    Evidence(
                        content=r.get("body", "") or r.get("snippet", ""),
                        citation=Citation(
                            title=r.get("title", "No Title"),
                            url=r.get("href", ""),
                            source="web",
                            date="n.d.",
                            authors=[],
                        ),
                        relevance=1.0,
                    )
                )

            logger.info("web_search_complete", count=len(evidence_list))
            return evidence_list

        except Exception as e:
            logger.error("web_search_failed", error=str(e))
            # Don't crash if search fails, return empty? Or raise?
            # Base class says Raise SearchError.
            raise SearchError(f"Web search failed: {e}") from e
