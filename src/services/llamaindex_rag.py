"""LlamaIndex RAG service for evidence retrieval and indexing.

Requires optional dependencies: uv sync --extra modal
"""

from typing import Any

import structlog

from src.utils.config import settings
from src.utils.exceptions import ConfigurationError
from src.utils.models import Evidence

logger = structlog.get_logger()


class LlamaIndexRAGService:
    """RAG service using LlamaIndex with ChromaDB vector store.

    Supports multiple embedding providers:
    - OpenAI embeddings (requires OPENAI_API_KEY)
    - Local sentence-transformers (no API key required)
    - Hugging Face embeddings (uses local sentence-transformers)

    Supports multiple LLM providers for query synthesis:
    - HuggingFace LLM (preferred, requires HF_TOKEN or HUGGINGFACE_API_KEY)
    - OpenAI LLM (fallback, requires OPENAI_API_KEY)
    - None (embedding-only mode, no query synthesis)

    Note:
        HuggingFace is the default LLM provider. OpenAI is used as fallback
        if HuggingFace LLM is not available or no HF token is configured.
    """

    def __init__(
        self,
        collection_name: str = "deepcritical_evidence",
        persist_dir: str | None = None,
        embedding_model: str | None = None,
        similarity_top_k: int = 5,
        use_openai_embeddings: bool | None = None,
        use_in_memory: bool = False,
    ) -> None:
        """
        Initialize LlamaIndex RAG service.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_dir: Directory to persist ChromaDB data
            embedding_model: Embedding model name (defaults based on provider)
            similarity_top_k: Number of top results to retrieve
            use_openai_embeddings: Force OpenAI embeddings (None = auto-detect)
            use_in_memory: Use in-memory ChromaDB client (useful for tests)
        """
        # Import dependencies and store references
        deps = self._import_dependencies()
        self._chromadb = deps["chromadb"]
        self._Document = deps["Document"]
        self._Settings = deps["Settings"]
        self._StorageContext = deps["StorageContext"]
        self._VectorStoreIndex = deps["VectorStoreIndex"]
        self._VectorIndexRetriever = deps["VectorIndexRetriever"]
        self._ChromaVectorStore = deps["ChromaVectorStore"]
        huggingface_embedding = deps["huggingface_embedding"]
        huggingface_llm = deps["huggingface_llm"]
        openai_embedding = deps["OpenAIEmbedding"]
        openai_llm = deps["OpenAI"]

        # Store basic configuration
        self.collection_name = collection_name
        self.persist_dir = persist_dir or settings.chroma_db_path
        self.similarity_top_k = similarity_top_k
        self.use_in_memory = use_in_memory

        # Configure embeddings and LLM
        use_openai = use_openai_embeddings if use_openai_embeddings is not None else False
        self._configure_embeddings(
            use_openai, embedding_model, huggingface_embedding, openai_embedding
        )
        self._configure_llm(huggingface_llm, openai_llm)

        # Initialize ChromaDB and index
        self._initialize_chromadb()

    def _import_dependencies(self) -> dict[str, Any]:
        """Import LlamaIndex dependencies and return as dict."""
        try:
            import chromadb
            from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
            from llama_index.core.retrievers import VectorIndexRetriever
            from llama_index.embeddings.openai import OpenAIEmbedding
            from llama_index.llms.openai import OpenAI
            from llama_index.vector_stores.chroma import ChromaVectorStore

            # Try to import Hugging Face embeddings (may not be available in all versions)
            try:
                from llama_index.embeddings.huggingface import (
                    HuggingFaceEmbedding as _HuggingFaceEmbedding,  # type: ignore[import-untyped]
                )

                huggingface_embedding = _HuggingFaceEmbedding
            except ImportError:
                huggingface_embedding = None  # type: ignore[assignment]

            # Try to import Hugging Face Inference API LLM (for API-based models)
            # This is preferred over local HuggingFaceLLM for query synthesis
            try:
                from llama_index.llms.huggingface_api import (
                    HuggingFaceInferenceAPI as _HuggingFaceInferenceAPI,  # type: ignore[import-untyped]
                )

                huggingface_llm = _HuggingFaceInferenceAPI
            except ImportError:
                # Fallback to local HuggingFaceLLM if API version not available
                try:
                    from llama_index.llms.huggingface import (
                        HuggingFaceLLM as _HuggingFaceLLM,  # type: ignore[import-untyped]
                    )

                    huggingface_llm = _HuggingFaceLLM
                except ImportError:
                    huggingface_llm = None  # type: ignore[assignment]

            return {
                "chromadb": chromadb,
                "Document": Document,
                "Settings": Settings,
                "StorageContext": StorageContext,
                "VectorStoreIndex": VectorStoreIndex,
                "VectorIndexRetriever": VectorIndexRetriever,
                "ChromaVectorStore": ChromaVectorStore,
                "OpenAIEmbedding": OpenAIEmbedding,
                "OpenAI": OpenAI,
                "huggingface_embedding": huggingface_embedding,
                "huggingface_llm": huggingface_llm,
            }
        except ImportError as e:
            raise ImportError(
                "LlamaIndex dependencies not installed. Run: uv sync --extra modal"
            ) from e

    def _configure_embeddings(
        self,
        use_openai_embeddings: bool,
        embedding_model: str | None,
        huggingface_embedding: Any,
        openai_embedding: Any,
    ) -> None:
        """Configure embedding model."""
        if use_openai_embeddings:
            if not settings.openai_api_key:
                raise ConfigurationError("OPENAI_API_KEY required for OpenAI embeddings")
            self.embedding_model = embedding_model or settings.openai_embedding_model
            self._Settings.embed_model = openai_embedding(
                model=self.embedding_model,
                api_key=settings.openai_api_key,
            )
        else:
            model_name = embedding_model or settings.huggingface_embedding_model
            self.embedding_model = model_name
            if huggingface_embedding is not None:
                self._Settings.embed_model = huggingface_embedding(model_name=model_name)
            else:
                self._Settings.embed_model = self._create_sentence_transformer_embedding(model_name)

    def _create_sentence_transformer_embedding(self, model_name: str) -> Any:
        """Create sentence-transformer embedding wrapper."""
        from sentence_transformers import SentenceTransformer

        try:
            from llama_index.embeddings.base import (
                BaseEmbedding,  # type: ignore[import-untyped]
            )
        except ImportError:
            from llama_index.core.embeddings import (
                BaseEmbedding,  # type: ignore[import-untyped]
            )

        class SentenceTransformerEmbedding(BaseEmbedding):  # type: ignore[misc]
            """Simple wrapper for sentence-transformers."""

            def __init__(self, model_name: str):
                super().__init__()
                self._model = SentenceTransformer(model_name)

            def _get_query_embedding(self, query: str) -> list[float]:
                result = self._model.encode(query).tolist()
                return list(result)  # type: ignore[no-any-return]

            def _get_text_embedding(self, text: str) -> list[float]:
                result = self._model.encode(text).tolist()
                return list(result)  # type: ignore[no-any-return]

            async def _aget_query_embedding(self, query: str) -> list[float]:
                return self._get_query_embedding(query)

            async def _aget_text_embedding(self, text: str) -> list[float]:
                return self._get_text_embedding(text)

        return SentenceTransformerEmbedding(model_name)

    def _configure_llm(self, huggingface_llm: Any, openai_llm: Any) -> None:
        """Configure LLM for query synthesis."""
        if huggingface_llm is not None and (settings.hf_token or settings.huggingface_api_key):
            model_name = settings.huggingface_model or "meta-llama/Llama-3.1-8B-Instruct"
            token = settings.hf_token or settings.huggingface_api_key

            # Check if it's HuggingFaceInferenceAPI (API-based) or HuggingFaceLLM (local)
            llm_class_name = (
                huggingface_llm.__name__
                if hasattr(huggingface_llm, "__name__")
                else str(huggingface_llm)
            )

            if "InferenceAPI" in llm_class_name:
                # Use HuggingFace Inference API (supports token parameter)
                try:
                    self._Settings.llm = huggingface_llm(
                        model_name=model_name,
                        token=token,
                    )
                except Exception as e:
                    # If model is not available via inference API, log warning and continue without LLM
                    logger.warning(
                        "Failed to initialize HuggingFace Inference API LLM",
                        model=model_name,
                        error=str(e),
                    )
                    logger.info("Continuing without LLM - query synthesis will be unavailable")
                    self._Settings.llm = None
                    return
            else:
                # Use local HuggingFaceLLM (doesn't support token, uses model_name and tokenizer_name)
                self._Settings.llm = huggingface_llm(
                    model_name=model_name,
                    tokenizer_name=model_name,
                )
            logger.info("Using HuggingFace LLM for query synthesis", model=model_name)
        elif settings.openai_api_key:
            self._Settings.llm = openai_llm(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
            )
            logger.info("Using OpenAI LLM for query synthesis", model=settings.openai_model)
        else:
            logger.warning("No LLM API key available - query synthesis will be unavailable")
            self._Settings.llm = None

    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB client, collection, and index."""
        if self.use_in_memory:
            # Use in-memory client for tests (avoids file system issues)
            self.chroma_client = self._chromadb.Client()
        else:
            # Use persistent client for production
            self.chroma_client = self._chromadb.PersistentClient(path=self.persist_dir)

        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(self.collection_name)
            logger.info("loaded_existing_collection", name=self.collection_name)
        except Exception:
            self.collection = self.chroma_client.create_collection(self.collection_name)
            logger.info("created_new_collection", name=self.collection_name)

        # Initialize vector store and index
        self.vector_store = self._ChromaVectorStore(chroma_collection=self.collection)
        self.storage_context = self._StorageContext.from_defaults(vector_store=self.vector_store)

        # Try to load existing index, or create empty one
        try:
            self.index = self._VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context,
            )
            logger.info("loaded_existing_index")
        except Exception:
            self.index = self._VectorStoreIndex([], storage_context=self.storage_context)
            logger.info("created_new_index")

    def ingest_evidence(self, evidence_list: list[Evidence]) -> None:
        """
        Ingest evidence into the vector store.

        Args:
            evidence_list: List of Evidence objects to ingest
        """
        if not evidence_list:
            logger.warning("no_evidence_to_ingest")
            return

        # Convert Evidence objects to LlamaIndex Documents
        documents = []
        for evidence in evidence_list:
            metadata = {
                "source": evidence.citation.source,
                "title": evidence.citation.title,
                "url": evidence.citation.url,
                "date": evidence.citation.date,
                "authors": ", ".join(evidence.citation.authors),
            }

            doc = self._Document(
                text=evidence.content,
                metadata=metadata,
                doc_id=evidence.citation.url,  # Use URL as unique ID
            )
            documents.append(doc)

        # Insert documents into index
        try:
            for doc in documents:
                self.index.insert(doc)
            logger.info("ingested_evidence", count=len(documents))
        except Exception as e:
            logger.error("failed_to_ingest_evidence", error=str(e))
            raise

    def ingest_documents(self, documents: list[Any]) -> None:
        """
        Ingest raw LlamaIndex Documents.

        Args:
            documents: List of LlamaIndex Document objects
        """
        if not documents:
            logger.warning("no_documents_to_ingest")
            return

        try:
            for doc in documents:
                self.index.insert(doc)
            logger.info("ingested_documents", count=len(documents))
        except Exception as e:
            logger.error("failed_to_ingest_documents", error=str(e))
            raise

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Query string
            top_k: Number of results to return (defaults to similarity_top_k)

        Returns:
            List of retrieved documents with metadata and scores
        """
        k = top_k or self.similarity_top_k

        # Create retriever
        retriever = self._VectorIndexRetriever(
            index=self.index,
            similarity_top_k=k,
        )

        try:
            # Retrieve nodes
            nodes = retriever.retrieve(query)

            # Convert to dict format
            results = []
            for node in nodes:
                results.append(
                    {
                        "text": node.node.get_content(),
                        "score": node.score,
                        "metadata": node.node.metadata,
                    }
                )

            logger.info("retrieved_documents", query=query[:50], count=len(results))
            return results

        except Exception as e:
            logger.error("failed_to_retrieve", error=str(e), query=query[:50])
            raise  # Re-raise to allow callers to distinguish errors from empty results

    def query(self, query_str: str, top_k: int | None = None) -> str:
        """
        Query the RAG system and get a synthesized response.

        Args:
            query_str: Query string
            top_k: Number of results to use (defaults to similarity_top_k)

        Returns:
            Synthesized response string

        Raises:
            ConfigurationError: If no LLM API key is available for query synthesis
        """
        if not self._Settings.llm:
            raise ConfigurationError(
                "LLM API key required for query synthesis. Set HF_TOKEN, HUGGINGFACE_API_KEY, or OPENAI_API_KEY. "
                "Alternatively, use retrieve() for embedding-only search."
            )

        k = top_k or self.similarity_top_k

        # Create query engine
        query_engine = self.index.as_query_engine(
            similarity_top_k=k,
        )

        try:
            response = query_engine.query(query_str)
            logger.info("generated_response", query=query_str[:50])
            return str(response)

        except Exception as e:
            logger.error("failed_to_query", error=str(e), query=query_str[:50])
            raise  # Re-raise to allow callers to handle errors explicitly

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            self.chroma_client.delete_collection(self.collection_name)
            self.collection = self.chroma_client.create_collection(self.collection_name)
            self.vector_store = self._ChromaVectorStore(chroma_collection=self.collection)
            self.storage_context = self._StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            self.index = self._VectorStoreIndex([], storage_context=self.storage_context)
            logger.info("cleared_collection", name=self.collection_name)
        except Exception as e:
            logger.error("failed_to_clear_collection", error=str(e))
            raise


def get_rag_service(
    collection_name: str = "deepcritical_evidence",
    **kwargs: Any,
) -> LlamaIndexRAGService:
    """
    Get or create a RAG service instance.

    Args:
        collection_name: Name of the ChromaDB collection
        **kwargs: Additional arguments for LlamaIndexRAGService
            Defaults to use_openai_embeddings=False (local embeddings)

    Returns:
        Configured LlamaIndexRAGService instance

    Note:
        By default, uses local embeddings (sentence-transformers) which require
        no API keys. Set use_openai_embeddings=True to use OpenAI embeddings.
    """
    # Default to local embeddings if not explicitly set
    if "use_openai_embeddings" not in kwargs:
        kwargs["use_openai_embeddings"] = False
    return LlamaIndexRAGService(collection_name=collection_name, **kwargs)
