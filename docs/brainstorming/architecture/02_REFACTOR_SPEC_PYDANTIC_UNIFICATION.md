# Architectural Specification: Pydantic AI Unification & Magentic Removal
**Date:** November 27, 2025
**Status:** APPROVED FOR IMPLEMENTATION
**Objective:** Unify the agentic architecture on a single framework (`pydantic_ai`), enabling native Hugging Face support, removing technical debt, and eliminating the dependency on Microsoft's Agent Framework ("Magentic").

---

## 1. Executive Summary

**Current State:**
The system runs on a dual-stack architecture:
1.  **Core:** Custom orchestrator using `pydantic_ai` (for OpenAI/Anthropic) + brittle manual parsing (for Hugging Face).
2.  **Extension:** `magentic` mode using `agent-framework-core` for multi-agent flows (requires OpenAI).

**Target State:**
A single, unified architecture where `pydantic_ai` handles all agentic interactions across all providers (OpenAI, Anthropic, Hugging Face).
*   **Primary Benefit:** Zero-cost multi-agent execution via native Hugging Face support.
*   **Secondary Benefit:** massive code reduction (~300 lines deleted) and removal of a heavy dependency.

---

## 2. Pre-Conditions

1.  **Current Feature Branch**: `feat/rate-limiting` must be merged to `dev` to secure the rate-limiting wins.
2.  **New Branch**: All refactoring work happens on `refactor/pydantic-unification`.

---

## 3. Dependency Changes (`pyproject.toml`)

### 3.1. Removals
We will remove the `magentic` optional dependency group entirely.
*   Remove: `agent-framework-core`
*   Remove: `magentic` (the package name in `project.optional-dependencies`)

### 3.2. Updates
*   **Core**: Ensure `pydantic-ai` is pinned to the version supporting `HuggingFaceModel` (v0.0.14+ or latest).
*   **Env**: `huggingface-hub` remains a dependency (used by Pydantic AI internally).

---

## 4. Component Refactoring Plan

### 4.1. The Great Purge (Deletions)
The following files are effectively dead code in the new architecture and will be deleted:
*   `src/orchestrator_magentic.py`: The secondary orchestrator.
*   `src/agents/magentic_agents.py`: The Magentic-specific agent definitions.
*   `tests/unit/test_magentic_fix.py`: Legacy tests for the old framework.

### 4.2. The Judge Handler (`src/agent_factory/judges.py`)
**Current:** Contains logic branching: `JudgeHandler` (Pydantic) vs `HFInferenceJudgeHandler` (Manual Regex/JSON).
**New:** Single `JudgeHandler` class using polymorphism.

**Implementation Detail:**
```python
# conceptual signature
class JudgeHandler:
    def __init__(self, model_provider: str, model_name: str):
        self.model = self._create_model(model_provider, model_name)
        self.agent = Agent(self.model, result_type=JudgeAssessment)

    def _create_model(self, provider, name):
        if provider == "openai":
            return OpenAIModel(name)
        elif provider == "anthropic":
            return AnthropicModel(name)
        elif provider == "huggingface":
            # THE KEY FIX: Native structured output support
            return HuggingFaceModel(name) 
```

### 4.3. The Orchestrator Factory (`src/orchestrator_factory.py`)
**Current:** Returns either `SimpleOrchestrator` or `MagenticOrchestrator` based on string mode.
**New:** Returns only `Orchestrator` (formerly SimpleOrchestrator).
*   Remove `mode` parameter.
*   Remove factory pattern if it becomes a single-line pass-through (optional, might keep for future extensibility).

### 4.4. The Orchestrator (`src/orchestrator.py`)
**Current:** "Simple" orchestrator.
**New:** The *Only* Orchestrator.
*   Rename class `SimpleOrchestrator` -> `DeepCriticalOrchestrator`.
*   Verify that it properly instantiates the refactored `JudgeHandler`.

---

## 5. Migration of "Magentic" Features

The "Magentic" mode had one key feature: **Chat-based Iteration**.
We will port this capability to the Pydantic AI architecture if strictly needed, but for the MVP of this refactor, we stick to the robust "Search -> Judge" loop.

*Note: The current Pydantic AI implementation in `orchestrator.py` is already capable of the core loop. The "multi-agent" complexity of Magentic was largely unnecessary overhead for this specific use case.*

---

## 6. Testing Strategy

### 6.1. Unit Tests
*   **Location:** `tests/unit/agent_factory/test_judges.py`
*   **Mocking:** We must mock `pydantic_ai.models.huggingface.HuggingFaceModel` to return dummy responses without hitting the API.
*   **Goal:** Verify that `JudgeHandler` correctly instantiates a generic Pydantic AI agent regardless of the provider.

### 6.2. Integration Tests (Live)
*   **Location:** `tests/integration/test_live_providers.py` (New or modified)
*   **Goal:** Run a *real* generic judge request against a free Hugging Face model (e.g., `Qwen/Qwen2.5-72B-Instruct` or `meta-llama/Llama-3.1-70B-Instruct`).
*   **Success Criteria:** The agent returns a valid `JudgeAssessment` Pydantic object, NOT a raw string.

---

## 7. Step-by-Step Execution Plan

1.  **Clean Slate**: Merge `feat/rate-limiting` -> `dev`.
2.  **Branch**: Checkout `refactor/pydantic-unification`.
3.  **Purge**: Delete the files listed in 4.1.
4.  **Dep Management**: Update `pyproject.toml` to remove magentic. Run `uv sync`.
5.  **Refactor Judge**: Rewrite `src/agent_factory/judges.py` to use `HuggingFaceModel`.
6.  **Refactor Factory**: Simplify `src/orchestrator_factory.py`.
7.  **Fix Tests**: Update tests to match the new class names/structures.
8.  **Verify**: Run `make check` (Lint, Type, Test).
9.  **Demo**: Create `examples/free_tier_demo.py` proving the system runs without OpenAI.

---

## 8. Risks & Mitigation

*   **Risk:** `HuggingFaceModel` might have limitations on very small free-tier models (context window, instruction following).
*   **Mitigation:** Default to known high-quality free models (`Llama-3.1-70B`, `Qwen-2.5-72B`) in the configuration.

*   **Risk:** Pydantic AI API changes (it is beta).
*   **Mitigation:** Pin exact version in `pyproject.toml`.
