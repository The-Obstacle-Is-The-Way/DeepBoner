# Phase 6 Implementation Spec: Embeddings & Semantic Search

**Goal**: Add vector search for semantic evidence retrieval.
**Philosophy**: "Find what you mean, not just what you type."
**Prerequisite**: Phase 5 complete (Magentic working)

---

## 1. Why Embeddings?

Current limitation: **Keyword-only search misses semantically related papers.**

Example problem:
- User searches: "metformin alzheimer"
- PubMed returns: Papers with exact keywords
- MISSED: Papers about "AMPK activation neuroprotection" (same mechanism, different words)

With embeddings:
- Embed the query AND all evidence
- Find semantically similar papers even without keyword match
- Deduplicate by meaning, not just URL

---

## 2. Architecture

### Current (Phase 5)
```
Query → SearchAgent → PubMed/Web (keyword) → Evidence
```

### Phase 6
```
Query → Embed(Query) → SearchAgent
                          ├── PubMed/Web (keyword) → Evidence
                          └── VectorDB (semantic) → Related Evidence
                                    ↑
                          Evidence → Embed → Store
```

### Shared Context Enhancement
```python
# Current
evidence_store = {"current": []}

# Phase 6
evidence_store = {
    "current": [],           # Raw evidence
    "embeddings": {},        # URL -> embedding vector
    "vector_index": None,    # ChromaDB collection
}
```

---

## 3. Technology Choice

### ChromaDB (Recommended)
- **Free**, open-source, local-first
- No API keys, no cloud dependency
- Supports sentence-transformers out of the box
- Perfect for hackathon (no infra setup)

### Embedding Model
- `sentence-transformers/all-MiniLM-L6-v2` (fast, good quality)
- Or `BAAI/bge-small-en-v1.5` (better quality, still fast)

---

## 4. Implementation

### 4.1 Dependencies

Add to `pyproject.toml`:
```toml
[project.optional-dependencies]
embeddings = [
    "chromadb>=0.4.0",
    "sentence-transformers>=2.2.0",
]
```

### 4.2 Embedding Service (`src/services/embeddings.py`)

```python
"""Embedding service for semantic search."""
from typing import List
import chromadb
from sentence_transformers import SentenceTransformer

class EmbeddingService:
    """Handles text embedding and vector storage."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = SentenceTransformer(model_name)
        self._client = chromadb.Client()  # In-memory for hackathon
        self._collection = self._client.create_collection(
            name="evidence",
            metadata={"hnsw:space": "cosine"}
        )

    def embed(self, text: str) -> List[float]:
        """Embed a single text."""
        return self._model.encode(text).tolist()

    def add_evidence(self, evidence_id: str, content: str, metadata: dict) -> None:
        """Add evidence to vector store."""
        embedding = self.embed(content)
        self._collection.add(
            ids=[evidence_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[content]
        )

    def search_similar(self, query: str, n_results: int = 5) -> List[dict]:
        """Find semantically similar evidence."""
        query_embedding = self.embed(query)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return [
            {"id": id, "content": doc, "metadata": meta, "distance": dist}
            for id, doc, meta, dist in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            )
        ]

    def deduplicate(self, new_evidence: List, threshold: float = 0.9) -> List:
        """Remove semantically duplicate evidence."""
        unique = []
        for evidence in new_evidence:
            similar = self.search_similar(evidence.content, n_results=1)
            if not similar or similar[0]["distance"] > (1 - threshold):
                unique.append(evidence)
                self.add_evidence(
                    evidence_id=evidence.citation.url,
                    content=evidence.content,
                    metadata={"source": evidence.citation.source}
                )
        return unique
```

### 4.3 Enhanced SearchAgent (`src/agents/search_agent.py`)

Update SearchAgent to use embeddings:

```python
class SearchAgent(BaseAgent):
    def __init__(
        self,
        search_handler: SearchHandlerProtocol,
        evidence_store: dict,
        embedding_service: EmbeddingService | None = None,  # NEW
    ):
        # ... existing init ...
        self._embeddings = embedding_service

    async def run(self, messages, *, thread=None, **kwargs) -> AgentRunResponse:
        # ... extract query ...

        # Execute keyword search
        result = await self._handler.execute(query, max_results_per_tool=10)

        # Semantic deduplication (NEW)
        if self._embeddings:
            unique_evidence = self._embeddings.deduplicate(result.evidence)

            # Also search for semantically related evidence
            related = self._embeddings.search_similar(query, n_results=5)
            # Add related evidence not already in results
            # ... merge logic ...

        # ... rest of method ...
```

### 4.4 Semantic Expansion in Orchestrator

The MagenticOrchestrator can use embeddings to expand queries:

```python
# In task instruction
task = f"""Research drug repurposing opportunities for: {query}

The system has semantic search enabled. When evidence is found:
1. Related concepts will be automatically surfaced
2. Duplicates are removed by meaning, not just URL
3. Use the surfaced related concepts to refine searches
"""
```

---

## 5. Directory Structure After Phase 6

```
src/
├── services/                   # NEW
│   ├── __init__.py
│   └── embeddings.py           # EmbeddingService
├── agents/
│   ├── search_agent.py         # Updated with embeddings
│   └── judge_agent.py
└── ...
```

---

## 6. Tests

### 6.1 Unit Tests (`tests/unit/services/test_embeddings.py`)

```python
"""Unit tests for EmbeddingService."""
import pytest
from src.services.embeddings import EmbeddingService

class TestEmbeddingService:
    def test_embed_returns_vector(self):
        """Embedding should return a float vector."""
        service = EmbeddingService()
        embedding = service.embed("metformin diabetes")
        assert isinstance(embedding, list)
        assert len(embedding) > 0
        assert all(isinstance(x, float) for x in embedding)

    def test_similar_texts_have_close_embeddings(self):
        """Semantically similar texts should have similar embeddings."""
        service = EmbeddingService()
        e1 = service.embed("metformin treats diabetes")
        e2 = service.embed("metformin is used for diabetes treatment")
        e3 = service.embed("the weather is sunny today")

        # Cosine similarity helper
        from numpy import dot
        from numpy.linalg import norm
        cosine = lambda a, b: dot(a, b) / (norm(a) * norm(b))

        # Similar texts should be closer
        assert cosine(e1, e2) > cosine(e1, e3)

    def test_add_and_search(self):
        """Should be able to add evidence and search for similar."""
        service = EmbeddingService()
        service.add_evidence(
            evidence_id="test1",
            content="Metformin activates AMPK pathway",
            metadata={"source": "pubmed"}
        )

        results = service.search_similar("AMPK activation drugs", n_results=1)
        assert len(results) == 1
        assert "AMPK" in results[0]["content"]
```

---

## 7. Definition of Done

Phase 6 is **COMPLETE** when:

1. `EmbeddingService` implemented with ChromaDB
2. SearchAgent uses embeddings for deduplication
3. Semantic search surfaces related evidence
4. All unit tests pass
5. Integration test shows improved recall (finds related papers)

---

## 8. Value Delivered

| Before (Phase 5) | After (Phase 6) |
|------------------|-----------------|
| Keyword-only search | Semantic + keyword search |
| URL-based deduplication | Meaning-based deduplication |
| Miss related papers | Surface related concepts |
| Exact match required | Fuzzy semantic matching |

**Real example improvement:**
- Query: "metformin alzheimer"
- Before: Only papers mentioning both words
- After: Also finds "AMPK neuroprotection", "biguanide cognitive", etc.
