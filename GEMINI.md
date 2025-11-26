# DeepCritical Context

## Project Overview
**DeepCritical** is an AI-native Medical Drug Repurposing Research Agent.
**Goal:** To accelerate the discovery of new uses for existing drugs by intelligently searching biomedical literature (PubMed), evaluating evidence, and hypothesizing potential applications.

**Architecture:**
The project follows a **Vertical Slice Architecture** (Search -> Judge -> Orchestrator) and adheres to **Strict TDD** (Test-Driven Development).

**Current Status:**
- **Phases 1-8:** COMPLETE. Foundation, Search, Judge, UI, Orchestrator, Embeddings, Hypothesis, Report.
- **Phase 9 (Source Cleanup):** COMPLETE. Removed DuckDuckGo web search (unreliable for scientific research).
- **Phase 10-11:** PLANNED. ClinicalTrials.gov and bioRxiv integration.

## Tech Stack & Tooling
- **Language:** Python 3.11 (Pinned)
- **Package Manager:** `uv` (Rust-based, extremely fast)
- **Frameworks:** `pydantic`, `pydantic-ai`, `httpx`, `gradio`
- **Vector DB:** `chromadb` with `sentence-transformers` for semantic search
- **Testing:** `pytest`, `pytest-asyncio`, `respx` (for mocking)
- **Quality:** `ruff` (linting/formatting), `mypy` (strict type checking), `pre-commit`

## Building & Running
We use a `Makefile` to standardize developer commands.

| Command | Description |
| :--- | :--- |
| `make install` | Install dependencies and pre-commit hooks. |
| `make test` | Run unit tests. |
| `make lint` | Run Ruff linter. |
| `make format` | Run Ruff formatter. |
| `make typecheck` | Run Mypy static type checker. |
| `make check` | **The Golden Gate:** Runs lint, typecheck, and test. Must pass before committing. |
| `make clean` | Clean up cache and artifacts. |

## Directory Structure
- `src/`: Source code
  - `utils/`: Shared utilities (`config.py`, `exceptions.py`, `models.py`)
  - `tools/`: Search tools (`pubmed.py`, `base.py`, `search_handler.py`)
  - `services/`: Services (`embeddings.py` - ChromaDB vector store)
  - `agents/`: Magentic multi-agent mode agents
  - `agent_factory/`: Agent definitions (judges, prompts)
- `tests/`: Test suite
  - `unit/`: Isolated unit tests (Mocked)
  - `integration/`: Real API tests (Marked as slow/integration)
- `docs/`: Documentation and Implementation Specs
- `examples/`: Working demos for each phase

## Development Conventions
1.  **Strict TDD:** Write failing tests in `tests/unit/` *before* implementing logic in `src/`.
2.  **Type Safety:** All code must pass `mypy --strict`. Use Pydantic models for data exchange.
3.  **Linting:** Zero tolerance for Ruff errors.
4.  **Mocking:** Use `respx` or `unittest.mock` for all external API calls in unit tests. Real calls go in `tests/integration`.
5.  **Vertical Slices:** Implement features end-to-end (Search -> Judge -> UI) rather than layer-by-layer.
