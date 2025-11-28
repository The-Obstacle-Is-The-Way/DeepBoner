"""RAG tool for semantic search within collected evidence.

Implements SearchTool protocol to enable RAG as a search option in the research workflow.
"""

from typing import TYPE_CHECKING, Any

import structlog

from src.utils.exceptions import ConfigurationError
from src.utils.models import Citation, Evidence, SourceName

if TYPE_CHECKING:
    from src.services.llamaindex_rag import LlamaIndexRAGService

logger = structlog.get_logger()


class RAGTool:
    """Search tool that uses LlamaIndex RAG for semantic search within collected evidence.

    Wraps LlamaIndexRAGService to implement the SearchTool protocol.
    Returns Evidence objects from RAG retrieval results.
    """

    def __init__(self, rag_service: "LlamaIndexRAGService | None" = None) -> None:
        """
        Initialize RAG tool.

        Args:
            rag_service: Optional RAG service instance. If None, will be lazy-initialized.
        """
        self._rag_service = rag_service
        self.logger = logger

    @property
    def name(self) -> str:
        """Return the tool name."""
        return "rag"

    def _get_rag_service(self) -> "LlamaIndexRAGService":
        """
        Get or create RAG service instance.

        Returns:
            LlamaIndexRAGService instance

        Raises:
            ConfigurationError: If RAG service cannot be initialized
        """
        if self._rag_service is None:
            try:
                from src.services.llamaindex_rag import get_rag_service

                # Use local embeddings by default (no API key required)
                # Use in-memory ChromaDB to avoid file system issues
                self._rag_service = get_rag_service(
                    use_openai_embeddings=False,
                    use_in_memory=True,  # Use in-memory for better reliability
                )
                self.logger.info("RAG service initialized with local embeddings")
            except (ConfigurationError, ImportError) as e:
                self.logger.error("Failed to initialize RAG service", error=str(e))
                raise ConfigurationError(
                    "RAG service unavailable. Check LlamaIndex dependencies are installed."
                ) from e

        return self._rag_service

    async def search(self, query: str, max_results: int = 10) -> list[Evidence]:
        """
        Search RAG system and return evidence.

        Args:
            query: The search query string
            max_results: Maximum number of results to return

        Returns:
            List of Evidence objects from RAG retrieval

        Note:
            Returns empty list on error (does not raise exceptions).
        """
        try:
            rag_service = self._get_rag_service()
        except ConfigurationError:
            self.logger.warning("RAG service unavailable, returning empty results")
            return []

        try:
            # Retrieve documents from RAG
            retrieved_docs = rag_service.retrieve(query, top_k=max_results)

            if not retrieved_docs:
                self.logger.info("No RAG results found", query=query[:50])
                return []

            # Convert retrieved documents to Evidence objects
            evidence_list: list[Evidence] = []
            for doc in retrieved_docs:
                try:
                    evidence = self._doc_to_evidence(doc)
                    evidence_list.append(evidence)
                except Exception as e:
                    self.logger.warning(
                        "Failed to convert document to evidence",
                        error=str(e),
                        doc_text=doc.get("text", "")[:50],
                    )
                    continue

            self.logger.info(
                "RAG search completed",
                query=query[:50],
                results=len(evidence_list),
            )
            return evidence_list

        except Exception as e:
            self.logger.error("RAG search failed", error=str(e), query=query[:50])
            # Return empty list on error (graceful degradation)
            return []

    def _doc_to_evidence(self, doc: dict[str, Any]) -> Evidence:
        """
        Convert RAG document to Evidence object.

        Args:
            doc: Document dict with keys: text, score, metadata

        Returns:
            Evidence object

        Raises:
            ValueError: If document is missing required fields
        """
        text = doc.get("text", "")
        if not text:
            raise ValueError("Document missing text content")

        metadata = doc.get("metadata", {})
        score = doc.get("score", 0.0)

        # Extract citation information from metadata
        source: SourceName = "rag"  # RAG is the source
        title = metadata.get("title", "Untitled")
        url = metadata.get("url", "")
        date = metadata.get("date", "Unknown")
        authors_str = metadata.get("authors", "")
        authors = [a.strip() for a in authors_str.split(",") if a.strip()] if authors_str else []

        # Create citation
        citation = Citation(
            source=source,
            title=title[:500],  # Enforce max length
            url=url,
            date=date,
            authors=authors,
        )

        # Create evidence with relevance score (normalize score to 0-1 if needed)
        relevance = min(max(float(score), 0.0), 1.0) if score else 0.0

        return Evidence(
            content=text,
            citation=citation,
            relevance=relevance,
        )


def create_rag_tool(
    rag_service: "LlamaIndexRAGService | None" = None,
) -> RAGTool:
    """
    Factory function to create a RAG tool.

    Args:
        rag_service: Optional RAG service instance. If None, will be lazy-initialized.

    Returns:
        Configured RAGTool instance

    Raises:
        ConfigurationError: If RAG service cannot be initialized and rag_service is None
    """
    try:
        return RAGTool(rag_service=rag_service)
    except Exception as e:
        logger.error("Failed to create RAG tool", error=str(e))
        raise ConfigurationError(f"Failed to create RAG tool: {e}") from e
