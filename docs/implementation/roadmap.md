# Implementation Roadmap: DeepCritical (Vertical Slices)

**Philosophy:** AI-Native Engineering, Vertical Slice Architecture, TDD, Modern Tooling (2025).

This roadmap defines the execution strategy to deliver **DeepCritical** effectively. We reject "overplanning" in favor of **ironclad, testable vertical slices**. Each phase delivers a fully functional slice of end-to-end value.

---

## 🛠️ The 2025 "Gucci" Tooling Stack

We are using the bleeding edge of Python engineering to ensure speed, safety, and developer joy.

| Category | Tool | Why? |
|----------|------|------|
| **Package Manager** | **`uv`** | Rust-based, 10-100x faster than pip/poetry. Manages python versions, venvs, and deps. |
| **Linting/Format** | **`ruff`** | Rust-based, instant. Replaces black, isort, flake8. |
| **Type Checking** | **`mypy`** | Strict static typing. Run via `uv run mypy`. |
| **Testing** | **`pytest`** | The standard. |
| **Test Plugins** | **`pytest-sugar`** | Instant feedback, progress bars. "Gucci" visuals. |
| **Test Plugins** | **`pytest-asyncio`** | Essential for our async agent loop. |
| **Test Plugins** | **`pytest-cov`** | Coverage reporting to ensure TDD adherence. |
| **Git Hooks** | **`pre-commit`** | Enforce ruff/mypy before commit. |

---

## 🏗️ Architecture: Vertical Slices

Instead of horizontal layers (e.g., "Building the Database Layer"), we build **Vertical Slices**.
Each slice implements a feature from **Entry Point (UI/API) -> Logic -> Data/External**.

### Directory Structure (Feature-First)

```
src/
├── app.py                  # Entry point
├── shared/                 # Shared utilities (logging, config, base classes)
│   ├── config.py
│   └── observability.py
└── features/               # Vertical Slices
    ├── search/             # Slice: Executing Searches
    │   ├── handlers.py
    │   ├── tools.py
    │   └── models.py
    ├── judge/              # Slice: Assessing Quality
    │   ├── handlers.py
    │   ├── prompts.py
    │   └── models.py
    └── report/             # Slice: Synthesizing Output
        ├── handlers.py
        └── models.py
```

---

## 🚀 Phased Execution Plan

### **Phase 1: Foundation & Tooling (Day 1)**
*Goal: A rock-solid, CI-ready environment with `uv` and `pytest` configured.*
- [ ] Initialize `pyproject.toml` with `uv`.
- [ ] Configure `ruff` (strict) and `mypy` (strict).
- [ ] Set up `pytest` with sugar and coverage.
- [ ] Implement `shared/config.py` (Configuration Slice).
- **Deliverable**: A repo that passes CI with `uv run pytest`.

### **Phase 2: The "Search" Vertical Slice (Day 2)**
*Goal: Agent can receive a query and get raw results from PubMed/Web.*
- [ ] **TDD**: Write test for `SearchHandler`.
- [ ] Implement `features/search/tools.py` (PubMed + DuckDuckGo).
- [ ] Implement `features/search/handlers.py` (Orchestrates tools).
- **Deliverable**: Function that takes "long covid" -> returns `List[Evidence]`.

### **Phase 3: The "Judge" Vertical Slice (Day 3)**
*Goal: Agent can decide if evidence is sufficient.*
- [ ] **TDD**: Write test for `JudgeHandler` (Mocked LLM).
- [ ] Implement `features/judge/prompts.py` (Structured outputs).
- [ ] Implement `features/judge/handlers.py` (LLM interaction).
- **Deliverable**: Function that takes `List[Evidence]` -> returns `JudgeAssessment`.

### **Phase 4: The "Loop" & UI Slice (Day 4)**
*Goal: End-to-End User Value.*
- [ ] Implement the `Orchestrator` (Connects Search + Judge loops).
- [ ] Build `features/ui/` (Gradio with Streaming).
- **Deliverable**: Working DeepCritical Agent on HuggingFace.

---

## 📜 Spec Documents

1. **[Phase 1 Spec: Foundation](01_phase_foundation.md)**
2. **[Phase 2 Spec: Search Slice](02_phase_search.md)**
3. **[Phase 3 Spec: Judge Slice](03_phase_judge.md)**
4. **[Phase 4 Spec: UI & Loop](04_phase_ui.md)**

*Start by reading Phase 1 Spec to initialize the repo.*
