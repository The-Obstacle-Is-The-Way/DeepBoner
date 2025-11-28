"""Integration tests for RAG integration using Hugging Face embeddings.

These tests use Hugging Face/local embeddings instead of OpenAI to avoid API key requirements.
Marked with @pytest.mark.integration to skip in unit test runs.
"""

import pytest

from src.services.llamaindex_rag import get_rag_service
from src.tools.rag_tool import create_rag_tool
from src.tools.search_handler import SearchHandler
from src.utils.models import Citation, Evidence


@pytest.mark.integration
@pytest.mark.local_embeddings
class TestRAGServiceIntegrationHF:
    """Integration tests for LlamaIndexRAGService using Hugging Face embeddings."""

    @pytest.mark.asyncio
    async def test_rag_service_ingest_and_retrieve(self):
        """RAG service should ingest and retrieve evidence using HF embeddings."""
        # Use Hugging Face embeddings (no API key required)
        rag_service = get_rag_service(
            collection_name="test_integration_hf",
            use_openai_embeddings=False,
            use_in_memory=True,  # Use in-memory ChromaDB to avoid file system issues
        )

        # Create sample evidence
        evidence_list = [
            Evidence(
                content="Metformin is a first-line treatment for type 2 diabetes. It works by reducing glucose production in the liver and improving insulin sensitivity.",
                citation=Citation(
                    source="pubmed",
                    title="Metformin Mechanism of Action",
                    url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
                    date="2024-01-15",
                    authors=["Smith J", "Johnson M"],
                ),
                relevance=0.9,
            ),
            Evidence(
                content="Recent studies suggest metformin may have neuroprotective effects in Alzheimer's disease models.",
                citation=Citation(
                    source="pubmed",
                    title="Metformin and Neuroprotection",
                    url="https://pubmed.ncbi.nlm.nih.gov/12345679/",
                    date="2024-02-20",
                    authors=["Brown K", "Davis L"],
                ),
                relevance=0.85,
            ),
        ]

        # Ingest evidence
        rag_service.ingest_evidence(evidence_list)

        # Retrieve evidence
        results = rag_service.retrieve("metformin diabetes", top_k=2)

        # Assert
        assert len(results) > 0
        assert any("metformin" in r["text"].lower() for r in results)
        assert all("text" in r for r in results)
        assert all("metadata" in r for r in results)

        # Cleanup
        rag_service.clear_collection()

    @pytest.mark.asyncio
    async def test_rag_service_retrieve_only(self):
        """RAG service should retrieve without requiring OpenAI for synthesis."""
        rag_service = get_rag_service(
            collection_name="test_query_hf",
            use_openai_embeddings=False,
            use_in_memory=True,  # Use in-memory ChromaDB to avoid file system issues
        )

        # Ingest evidence
        evidence_list = [
            Evidence(
                content="Python is a high-level programming language known for its simplicity and readability.",
                citation=Citation(
                    source="pubmed",
                    title="Python Programming",
                    url="https://example.com/python",
                    date="2024",
                    authors=["Author"],
                ),
            )
        ]
        rag_service.ingest_evidence(evidence_list)

        # Retrieve (embedding-only, no LLM synthesis)
        results = rag_service.retrieve("What is Python?", top_k=1)

        assert len(results) > 0
        assert "python" in results[0]["text"].lower()

        # Cleanup
        rag_service.clear_collection()


@pytest.mark.integration
@pytest.mark.local_embeddings
class TestRAGToolIntegrationHF:
    """Integration tests for RAGTool using Hugging Face embeddings."""

    @pytest.mark.asyncio
    async def test_rag_tool_search(self):
        """RAGTool should search RAG service and return Evidence objects."""
        # Create RAG service and ingest evidence
        rag_service = get_rag_service(
            collection_name="test_rag_tool_hf",
            use_openai_embeddings=False,
            use_in_memory=True,  # Use in-memory ChromaDB to avoid file system issues
        )
        evidence_list = [
            Evidence(
                content="Machine learning is a subset of artificial intelligence.",
                citation=Citation(
                    source="pubmed",
                    title="ML Basics",
                    url="https://example.com/ml",
                    date="2024",
                    authors=["ML Expert"],
                ),
            )
        ]
        rag_service.ingest_evidence(evidence_list)

        # Create RAG tool
        tool = create_rag_tool(rag_service=rag_service)

        # Search
        results = await tool.search("machine learning", max_results=5)

        # Assert
        assert len(results) > 0
        assert all(isinstance(e, Evidence) for e in results)
        assert results[0].citation.source == "rag"
        assert (
            "machine learning" in results[0].content.lower()
            or "artificial intelligence" in results[0].content.lower()
        )

        # Cleanup
        rag_service.clear_collection()

    @pytest.mark.asyncio
    async def test_rag_tool_empty_collection(self):
        """RAGTool should return empty list when collection is empty."""
        rag_service = get_rag_service(
            collection_name="test_empty_hf",
            use_openai_embeddings=False,
            use_in_memory=True,  # Use in-memory ChromaDB to avoid file system issues
        )
        rag_service.clear_collection()  # Ensure empty

        tool = create_rag_tool(rag_service=rag_service)
        results = await tool.search("any query")

        assert results == []


@pytest.mark.integration
@pytest.mark.local_embeddings
class TestRAGSearchHandlerIntegrationHF:
    """Integration tests for RAG in SearchHandler using Hugging Face embeddings."""

    @pytest.mark.asyncio
    async def test_search_handler_with_rag(self):
        """SearchHandler should work with RAG tool included."""
        # Setup: Create RAG service and ingest some evidence
        rag_service = get_rag_service(
            collection_name="test_search_handler_hf",
            use_openai_embeddings=False,
            use_in_memory=True,  # Use in-memory ChromaDB to avoid file system issues
        )
        evidence_list = [
            Evidence(
                content="Test evidence for search handler integration.",
                citation=Citation(
                    source="pubmed",
                    title="Test Evidence",
                    url="https://example.com/test",
                    date="2024",
                    authors=["Tester"],
                ),
            )
        ]
        rag_service.ingest_evidence(evidence_list)

        # Create RAG tool with the same service instance to ensure same collection
        rag_tool = create_rag_tool(rag_service=rag_service)

        # Create SearchHandler with the custom RAG tool
        handler = SearchHandler(
            tools=[rag_tool],  # Use our RAG tool with the test's collection
            include_rag=False,  # Don't add another RAG tool (we already added it)
            auto_ingest_to_rag=False,  # Don't auto-ingest (already has data)
        )

        # Execute search
        result = await handler.execute("test evidence", max_results_per_tool=5)

        # Assert
        assert result.total_found > 0
        assert "rag" in result.sources_searched
        assert any(e.citation.source == "rag" for e in result.evidence)

        # Cleanup
        rag_service.clear_collection()
