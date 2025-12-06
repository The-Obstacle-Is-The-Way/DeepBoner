# Component Inventory

> **Last Updated**: 2025-12-06

This document provides a complete catalog of all components in the DeepBoner codebase.

## Source Code Statistics

| Category | Count |
|----------|-------|
| Python files in `src/` | ~67 |
| Python files in `tests/` | ~76 |
| Total modules | ~143 |

## Directory Structure

```
src/
├── app.py                      # Gradio UI entry point
├── mcp_tools.py                # MCP server tool wrappers
├── orchestrators/              # Research orchestration
├── clients/                    # LLM backend adapters
├── agents/                     # Multi-agent components
├── agent_factory/              # Agent creation
├── tools/                      # Search tool implementations
├── services/                   # Cross-cutting services
├── prompts/                    # LLM prompt templates
├── utils/                      # Shared utilities
├── config/                     # Domain configuration
├── middleware/                 # Processing middleware
└── state/                      # State management
```

---

## Core Entry Points

### `src/app.py`
**Purpose:** Main application entry point

| Component | Type | Description |
|-----------|------|-------------|
| `create_demo()` | Function | Creates Gradio interface |
| `main()` | Function | Application entry point |

**Dependencies:** Gradio, orchestrators, config

### `src/mcp_tools.py`
**Purpose:** MCP (Model Context Protocol) tool wrappers

| Component | Type | Description |
|-----------|------|-------------|
| `search_pubmed()` | Tool | PubMed search wrapper |
| `search_clinical_trials()` | Tool | ClinicalTrials.gov wrapper |
| `search_europepmc()` | Tool | Europe PMC wrapper |
| `search_all_sources()` | Tool | Multi-source search |

---

## Orchestrators (`src/orchestrators/`)

### `advanced.py`
**Purpose:** Main multi-agent orchestrator using Microsoft Agent Framework

| Component | Type | Description |
|-----------|------|-------------|
| `AdvancedOrchestrator` | Class | Primary research orchestrator |
| `run()` | Method | Execute research workflow |
| `_search_phase()` | Method | Search execution |
| `_judge_phase()` | Method | Evidence evaluation |
| `_synthesize_phase()` | Method | Report generation |

**Framework:** Microsoft Agent Framework (agent-framework-core)

### `factory.py`
**Purpose:** Orchestrator selection

| Component | Type | Description |
|-----------|------|-------------|
| `OrchestratorFactory` | Class | Creates appropriate orchestrator |
| `create()` | Method | Factory method |

### `base.py`
**Purpose:** Base orchestrator interface

| Component | Type | Description |
|-----------|------|-------------|
| `BaseOrchestrator` | ABC | Abstract base class |

### `langgraph_orchestrator.py`
**Purpose:** LangGraph-based workflow (experimental)

| Component | Type | Description |
|-----------|------|-------------|
| `LangGraphOrchestrator` | Class | Workflow state machine |

### `hierarchical.py`
**Purpose:** Hierarchical agent coordination

| Component | Type | Description |
|-----------|------|-------------|
| `HierarchicalOrchestrator` | Class | Manager-agent hierarchy |

---

## LLM Clients (`src/clients/`)

### `factory.py`
**Purpose:** Auto-select LLM backend

| Component | Type | Description |
|-----------|------|-------------|
| `get_chat_client()` | Function | Returns appropriate client |

**Selection Logic:**
```python
if settings.has_openai_key:
    return OpenAIChatClient()
else:
    return HuggingFaceChatClient()
```

### `huggingface.py`
**Purpose:** HuggingFace Inference API adapter

| Component | Type | Description |
|-----------|------|-------------|
| `HuggingFaceChatClient` | Class | Free tier LLM client |
| `chat_completion()` | Method | Generate completion |

**Model:** Qwen 2.5 7B Instruct (free tier)

### `base.py`
**Purpose:** Client interface

| Component | Type | Description |
|-----------|------|-------------|
| `BaseChatClient` | ABC | Client interface |

### `providers.py`
**Purpose:** Provider implementations

### `registry.py`
**Purpose:** Provider registration

---

## Agents (`src/agents/`)

### `search_agent.py`
| Component | Type | Description |
|-----------|------|-------------|
| `SearchAgent` | Class | Evidence gathering agent |

### `judge_agent.py`
| Component | Type | Description |
|-----------|------|-------------|
| `JudgeAgent` | Class | Evidence evaluation |

### `judge_agent_llm.py`
| Component | Type | Description |
|-----------|------|-------------|
| `LLMJudgeAgent` | Class | LLM-based judge implementation |

### `report_agent.py`
| Component | Type | Description |
|-----------|------|-------------|
| `ReportAgent` | Class | Report synthesis |

### `retrieval_agent.py`
| Component | Type | Description |
|-----------|------|-------------|
| `RetrievalAgent` | Class | Evidence retrieval coordination |

### `hypothesis_agent.py`
| Component | Type | Description |
|-----------|------|-------------|
| `HypothesisAgent` | Class | Mechanistic hypothesis generation |

### `magentic_agents.py`
| Component | Type | Description |
|-----------|------|-------------|
| Multi-agent mode | Module | Microsoft Agent Framework integration |

### `state.py`
| Component | Type | Description |
|-----------|------|-------------|
| Agent state models | Module | Shared state definitions |

### `tools.py`
| Component | Type | Description |
|-----------|------|-------------|
| Tool bindings | Module | Agent tool configuration |

---

## Graph Workflow (`src/agents/graph/`)

### `workflow.py`
| Component | Type | Description |
|-----------|------|-------------|
| `create_workflow()` | Function | LangGraph workflow builder |

### `nodes.py`
| Component | Type | Description |
|-----------|------|-------------|
| `search_node()` | Function | Search workflow node |
| `judge_node()` | Function | Judge workflow node |
| `report_node()` | Function | Report workflow node |

### `state.py`
| Component | Type | Description |
|-----------|------|-------------|
| `WorkflowState` | Class | LangGraph state schema |

---

## Agent Factory (`src/agent_factory/`)

### `judges.py`
**Purpose:** Evidence quality judgment

| Component | Type | Description |
|-----------|------|-------------|
| `create_judge()` | Function | Judge agent factory |
| `JudgeResult` | Model | Assessment output |

**Framework:** Pydantic AI

### `agents.py`
| Component | Type | Description |
|-----------|------|-------------|
| Agent creation | Module | Factory functions |

---

## Search Tools (`src/tools/`)

### `pubmed.py`
| Component | Type | Description |
|-----------|------|-------------|
| `PubMedTool` | Class | NCBI E-utilities client |
| `search()` | Method | Execute search |

**API:** PubMed E-utilities (eutils.ncbi.nlm.nih.gov)

### `clinicaltrials.py`
| Component | Type | Description |
|-----------|------|-------------|
| `ClinicalTrialsTool` | Class | ClinicalTrials.gov client |
| `search()` | Method | Execute search |

**API:** ClinicalTrials.gov API (uses `requests` due to WAF blocking httpx)

### `europepmc.py`
| Component | Type | Description |
|-----------|------|-------------|
| `EuropePMCTool` | Class | Europe PMC client |
| `search()` | Method | Execute search |

**API:** Europe PMC API

### `openalex.py`
| Component | Type | Description |
|-----------|------|-------------|
| `OpenAlexTool` | Class | OpenAlex client |
| `search()` | Method | Execute search |

**API:** OpenAlex API

### `search_handler.py`
| Component | Type | Description |
|-----------|------|-------------|
| `SearchHandler` | Class | Scatter-gather orchestration |
| `search_all()` | Method | Parallel multi-source search |

### `query_utils.py`
| Component | Type | Description |
|-----------|------|-------------|
| Query utilities | Module | Query refinement and expansion |

### `rate_limiter.py`
| Component | Type | Description |
|-----------|------|-------------|
| `RateLimiter` | Class | API rate limiting |

### `base.py`
| Component | Type | Description |
|-----------|------|-------------|
| `BaseSearchTool` | ABC | Search tool interface |

### `web_search.py`
| Component | Type | Description |
|-----------|------|-------------|
| Web search | Module | DuckDuckGo integration |

---

## Services (`src/services/`)

### `embeddings.py`
| Component | Type | Description |
|-----------|------|-------------|
| `EmbeddingService` | Class | Local embedding service |
| `embed()` | Method | Generate embeddings |
| `deduplicate()` | Method | Cross-source deduplication |

**Stack:** sentence-transformers + ChromaDB

### `llamaindex_rag.py`
| Component | Type | Description |
|-----------|------|-------------|
| `LlamaIndexRAG` | Class | Premium RAG service |

**Stack:** LlamaIndex + OpenAI embeddings + ChromaDB

### `embedding_protocol.py`
| Component | Type | Description |
|-----------|------|-------------|
| `EmbeddingProtocol` | Protocol | Interface for embedding services |

### `research_memory.py`
| Component | Type | Description |
|-----------|------|-------------|
| `ResearchMemory` | Class | Shared research state |

---

## Utilities (`src/utils/`)

### `config.py`
| Component | Type | Description |
|-----------|------|-------------|
| `Settings` | Class | Pydantic Settings configuration |
| `settings` | Instance | Global settings singleton |
| `get_settings()` | Function | Settings factory |
| `configure_logging()` | Function | Logging setup |

### `models.py`
| Component | Type | Description |
|-----------|------|-------------|
| `Evidence` | Model | Evidence with citation |
| `Citation` | Model | Source citation |
| `SearchResult` | Model | Search response |
| `JudgeAssessment` | Model | Judge evaluation |
| `ResearchReport` | Model | Final report |
| `AgentEvent` | Model | UI streaming events |

See [Data Models](data-models.md) for complete documentation.

### `exceptions.py`
| Component | Type | Description |
|-----------|------|-------------|
| `DeepBonerError` | Exception | Base exception |
| `SearchError` | Exception | Search failures |
| `JudgeError` | Exception | Judge failures |
| `ConfigurationError` | Exception | Config errors |
| `RateLimitError` | Exception | Rate limits |

See [Exception Hierarchy](exception-hierarchy.md) for details.

### `service_loader.py`
| Component | Type | Description |
|-----------|------|-------------|
| Service loading | Module | Tiered service selection |

### `citation_validator.py`
| Component | Type | Description |
|-----------|------|-------------|
| Citation validation | Module | URL verification |

### `text_utils.py`
| Component | Type | Description |
|-----------|------|-------------|
| Text utilities | Module | Text processing |

### `parsers.py`
| Component | Type | Description |
|-----------|------|-------------|
| Response parsing | Module | LLM output parsing |

### `dataloaders.py`
| Component | Type | Description |
|-----------|------|-------------|
| Data loading | Module | Data loading utilities |

---

## Configuration (`src/config/`)

### `domain.py`
| Component | Type | Description |
|-----------|------|-------------|
| `ResearchDomain` | Enum | Research domain types |

---

## Prompts (`src/prompts/`)

| File | Purpose |
|------|---------|
| `search.py` | Query refinement prompts |
| `judge.py` | Evidence assessment prompts |
| `hypothesis.py` | Hypothesis generation prompts |
| `synthesis.py` | Evidence synthesis prompts |
| `report.py` | Report generation prompts |

---

## Middleware (`src/middleware/`)

### `sub_iteration.py`
| Component | Type | Description |
|-----------|------|-------------|
| Sub-iteration | Module | Nested iteration logic |

---

## Reserved Directories

These directories exist but are placeholders for future features:

| Directory | Purpose |
|-----------|---------|
| `src/database_services/` | Future database services |
| `src/retrieval_factory/` | Future retrieval configuration |

---

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests (mocked)
│   ├── orchestrators/
│   ├── agents/
│   ├── clients/
│   ├── tools/
│   ├── services/
│   ├── utils/
│   ├── prompts/
│   ├── agent_factory/
│   ├── config/
│   ├── graph/
│   └── mcp/
├── integration/                # Integration tests (real APIs)
└── e2e/                        # End-to-end tests
```

---

## Related Documentation

- [Architecture Overview](overview.md)
- [Data Models](data-models.md)
- [Exception Hierarchy](exception-hierarchy.md)
- [System Registry](system-registry.md)
