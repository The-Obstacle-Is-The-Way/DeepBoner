# Architecture Overview

> **Last Updated**: 2025-12-06

This document provides a comprehensive overview of DeepBoner's architecture.

## System Purpose

DeepBoner is an **AI-native sexual health research agent** that autonomously:
1. Searches biomedical databases (PubMed, ClinicalTrials.gov, Europe PMC, OpenAlex)
2. Evaluates evidence quality
3. Synthesizes research reports with citations

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                             │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  Gradio UI   │    │  MCP Server  │    │   Examples   │          │
│  │  (src/app)   │    │(mcp_tools.py)│    │  (scripts)   │          │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘          │
└─────────┼───────────────────┼───────────────────┼───────────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION LAYER                           │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   AdvancedOrchestrator                        │  │
│  │              (Microsoft Agent Framework)                      │  │
│  │                                                               │  │
│  │   ┌─────────┐    ┌─────────┐    ┌─────────┐                  │  │
│  │   │ Search  │ →  │  Judge  │ →  │ Report  │                  │  │
│  │   │  Agent  │    │  Agent  │    │  Agent  │                  │  │
│  │   └─────────┘    └─────────┘    └─────────┘                  │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                  LangGraph Orchestrator                       │  │
│  │                    (Experimental)                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          LLM BACKENDS                                │
│                                                                      │
│  ┌─────────────────────┐         ┌─────────────────────┐           │
│  │    OpenAI Client    │         │  HuggingFace Client │           │
│  │      (GPT-5)        │         │  (Qwen 2.5 7B)      │           │
│  │   Premium Tier      │         │   Free Tier         │           │
│  └─────────────────────┘         └─────────────────────┘           │
│                                                                      │
│           Auto-selected by ClientFactory based on API key           │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SEARCH TOOLS                                 │
│                                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐        │
│  │  PubMed  │  │ClinicalTrials│  │EuropePMC │  │ OpenAlex │        │
│  └──────────┘  └──────────────┘  └──────────┘  └──────────┘        │
│                                                                      │
│              SearchHandler: Parallel scatter-gather                  │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          SERVICES                                    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Embeddings  │  │ LlamaIndex   │  │   Research   │              │
│  │   Service    │  │     RAG      │  │    Memory    │              │
│  │   (local)    │  │  (premium)   │  │   (shared)   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
│                       ChromaDB Vector Store                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Research Loop

The system operates on a **search-and-judge loop**:

```
User Question
      │
      ▼
┌─────────────┐
│   SEARCH    │ ← Query PubMed, ClinicalTrials, Europe PMC, OpenAlex
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   GATHER    │ ← Collect and deduplicate evidence (PMID/DOI)
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────────┐
│    JUDGE    │ ──► │ "Enough evidence?"│
└──────┬──────┘     └────────┬─────────┘
       │                     │
       │    ┌────────────────┴────────────────┐
       │    │                                 │
       ▼    ▼                                 ▼
┌─────────────┐                        ┌─────────────┐
│   REFINE    │ ← NO: Expand query     │ SYNTHESIZE  │ ← YES: Generate report
│   & LOOP    │   and search again     └─────────────┘
└─────────────┘
```

**Break Conditions:**
- Judge approves evidence as sufficient
- Token budget exceeded (50K max)
- Max iterations reached (default 10)

## Framework Integration

DeepBoner combines two AI frameworks:

| Framework | Role | Usage |
|-----------|------|-------|
| **Microsoft Agent Framework** | Multi-agent orchestration | Manager → Agent coordination |
| **Pydantic AI** | Structured outputs | Evidence models, judge assessments |

They work together - Microsoft AF handles the workflow, Pydantic AI handles data validation.

## Dual-Backend Architecture

The system auto-selects LLM backend:

```python
# src/clients/factory.py
def get_chat_client():
    if settings.has_openai_key:
        return OpenAIChatClient(...)  # Premium
    else:
        return HuggingFaceChatClient(...)  # Free
```

| Tier | Backend | Model | Features |
|------|---------|-------|----------|
| Free | HuggingFace | Qwen 2.5 7B | Full functionality, slower |
| Premium | OpenAI | GPT-5 | Full functionality, faster |

**Same orchestration logic** - only the LLM differs.

## Key Components

### Orchestrators (`src/orchestrators/`)

| Component | File | Purpose |
|-----------|------|---------|
| AdvancedOrchestrator | `advanced.py` | Main multi-agent orchestrator |
| OrchestratorFactory | `factory.py` | Backend selection |
| LangGraphOrchestrator | `langgraph_orchestrator.py` | Experimental workflow engine |

### Agents (`src/agents/`)

| Agent | File | Role |
|-------|------|------|
| SearchAgent | `search_agent.py` | Evidence retrieval |
| JudgeAgent | `judge_agent.py` | Evidence evaluation |
| ReportAgent | `report_agent.py` | Report synthesis |
| HypothesisAgent | `hypothesis_agent.py` | Mechanistic pathway analysis |

### Tools (`src/tools/`)

| Tool | File | API |
|------|------|-----|
| PubMed | `pubmed.py` | NCBI E-utilities |
| ClinicalTrials | `clinicaltrials.py` | ClinicalTrials.gov |
| EuropePMC | `europepmc.py` | Europe PMC API |
| OpenAlex | `openalex.py` | OpenAlex API |
| SearchHandler | `search_handler.py` | Parallel orchestration |

### Services (`src/services/`)

| Service | File | Purpose |
|---------|------|---------|
| EmbeddingService | `embeddings.py` | Local embeddings (sentence-transformers) |
| LlamaIndexRAG | `llamaindex_rag.py` | Premium RAG (OpenAI embeddings) |
| ResearchMemory | `research_memory.py` | Shared state across agents |

## Data Flow

1. **User Input** → Gradio UI / MCP Client
2. **Query** → AdvancedOrchestrator
3. **Search** → SearchHandler → [PubMed, ClinicalTrials, EuropePMC, OpenAlex]
4. **Evidence** → Deduplicated by PMID/DOI
5. **Judge** → LLM evaluates sufficiency
6. **Loop or Synthesize** → Based on judge decision
7. **Report** → Structured output with citations
8. **Response** → Back to user

## Configuration

Settings are loaded from environment via Pydantic Settings:

```python
# src/utils/config.py
class Settings(BaseSettings):
    openai_api_key: str | None
    huggingface_model: str = "Qwen/Qwen2.5-7B-Instruct"
    max_iterations: int = 10
    # ...
```

See [Configuration Reference](../reference/configuration.md) for all options.

## Related Documentation

- [Component Inventory](component-inventory.md) - Complete module catalog
- [Data Models](data-models.md) - Pydantic model reference
- [System Registry](system-registry.md) - Service wiring specification
- [Workflow Diagrams](workflow-diagrams.md) - Visual documentation

---

*"Architecturally rock solid."* 🏛️
