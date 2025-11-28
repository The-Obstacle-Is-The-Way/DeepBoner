"""Search handler - orchestrates multiple search tools."""

import asyncio
from typing import TYPE_CHECKING, cast

import structlog

from src.tools.base import SearchTool
from src.tools.rag_tool import create_rag_tool
from src.utils.exceptions import ConfigurationError, SearchError
from src.utils.models import Evidence, SearchResult, SourceName

if TYPE_CHECKING:
    from src.services.llamaindex_rag import LlamaIndexRAGService
else:
    LlamaIndexRAGService = object

logger = structlog.get_logger()


class SearchHandler:
    """Orchestrates parallel searches across multiple tools."""

    def __init__(
        self,
        tools: list[SearchTool],
        timeout: float = 30.0,
        include_rag: bool = False,
        auto_ingest_to_rag: bool = True,
    ) -> None:
        """
        Initialize the search handler.

        Args:
            tools: List of search tools to use
            timeout: Timeout for each search in seconds
            include_rag: Whether to include RAG tool in searches
            auto_ingest_to_rag: Whether to automatically ingest results into RAG
        """
        self.tools = list(tools)  # Make a copy
        self.timeout = timeout
        self.auto_ingest_to_rag = auto_ingest_to_rag
        self._rag_service: LlamaIndexRAGService | None = None

        if include_rag:
            self.add_rag_tool()

    def add_rag_tool(self) -> None:
        """Add RAG tool to the tools list if available."""
        try:
            rag_tool = create_rag_tool()
            self.tools.append(rag_tool)
            logger.info("RAG tool added to search handler")
        except ConfigurationError:
            logger.warning(
                "RAG tool unavailable, not adding to search handler",
                hint="LlamaIndex dependencies required",
            )
        except Exception as e:
            logger.error("Failed to add RAG tool", error=str(e))

    def _get_rag_service(self) -> "LlamaIndexRAGService | None":
        """Get or create RAG service for ingestion."""
        if self._rag_service is None and self.auto_ingest_to_rag:
            try:
                from src.services.llamaindex_rag import get_rag_service

                # Use local embeddings by default (no API key required)
                # Use in-memory ChromaDB to avoid file system issues
                self._rag_service = get_rag_service(
                    use_openai_embeddings=False,
                    use_in_memory=True,  # Use in-memory for better reliability
                )
                logger.info("RAG service initialized for ingestion with local embeddings")
            except (ConfigurationError, ImportError):
                logger.warning("RAG service unavailable for ingestion")
                return None
        return self._rag_service

    async def execute(self, query: str, max_results_per_tool: int = 10) -> SearchResult:
        """
        Execute search across all tools in parallel.

        Args:
            query: The search query
            max_results_per_tool: Max results from each tool

        Returns:
            SearchResult containing all evidence and metadata
        """
        logger.info("Starting search", query=query, tools=[t.name for t in self.tools])

        # Create tasks for parallel execution
        tasks = [
            self._search_with_timeout(tool, query, max_results_per_tool) for tool in self.tools
        ]

        # Gather results (don't fail if one tool fails)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        all_evidence: list[Evidence] = []
        sources_searched: list[SourceName] = []
        errors: list[str] = []

        for tool, result in zip(self.tools, results, strict=True):
            if isinstance(result, Exception):
                errors.append(f"{tool.name}: {result!s}")
                logger.warning("Search tool failed", tool=tool.name, error=str(result))
            else:
                # Cast result to list[Evidence] as we know it succeeded
                success_result = cast(list[Evidence], result)
                all_evidence.extend(success_result)

                # Cast tool.name to SourceName (centralized type from models)
                tool_name = cast(SourceName, tool.name)
                sources_searched.append(tool_name)
                logger.info("Search tool succeeded", tool=tool.name, count=len(success_result))

        search_result = SearchResult(
            query=query,
            evidence=all_evidence,
            sources_searched=sources_searched,
            total_found=len(all_evidence),
            errors=errors,
        )

        # Ingest evidence into RAG if enabled and available
        if self.auto_ingest_to_rag and all_evidence:
            rag_service = self._get_rag_service()
            if rag_service:
                try:
                    # Filter out RAG-sourced evidence (avoid circular ingestion)
                    evidence_to_ingest = [e for e in all_evidence if e.citation.source != "rag"]
                    if evidence_to_ingest:
                        rag_service.ingest_evidence(evidence_to_ingest)
                        logger.info(
                            "Ingested evidence into RAG",
                            count=len(evidence_to_ingest),
                        )
                except Exception as e:
                    logger.warning("Failed to ingest evidence into RAG", error=str(e))

        return search_result

    async def _search_with_timeout(
        self,
        tool: SearchTool,
        query: str,
        max_results: int,
    ) -> list[Evidence]:
        """Execute a single tool search with timeout."""
        try:
            return await asyncio.wait_for(
                tool.search(query, max_results),
                timeout=self.timeout,
            )
        except TimeoutError as e:
            raise SearchError(f"{tool.name} search timed out after {self.timeout}s") from e
