# P0 Blockers: Magentic Mode Implementation

**Date:** November 26, 2025
**Status:** CRITICAL
**Component:** Magentic Orchestration (Phase 5)

This document outlines critical blockers identified during the implementation of the Magentic multi-agent mode. These issues must be resolved to ensure a stable and configurable production deployment.

## 1. Hardcoded OpenAI Models (High Severity)

**Issue:**
The agent factory functions in `src/agents/magentic_agents.py` have hardcoded model IDs (`gpt-4o` and `gpt-4o-mini`).

```python
# src/agents/magentic_agents.py

def create_search_agent(...):
    client = chat_client or OpenAIChatClient(
        model_id="gpt-4o-mini",  # <--- HARDCODED
        api_key=settings.openai_api_key,
    )

def create_judge_agent(...):
    client = chat_client or OpenAIChatClient(
        model_id="gpt-4o",       # <--- HARDCODED
        api_key=settings.openai_api_key,
    )
```

**Impact:**
1.  **Configuration ignored:** The user's `OPENAI_MODEL` setting (from `.env`) is ignored by the agents, only used by the Manager.
2.  **Access Failure:** Users without access to `gpt-4o` (e.g., legacy tiers) cannot run the system, even if they configure `gpt-3.5-turbo` in their env.
3.  **Cost Control:** Users cannot downgrade to cheaper models for development/testing.

**Fix Required:**
Update `src/agents/magentic_agents.py` to use `settings.openai_model` (or a specific agent config) instead of hardcoded strings.

---

## 2. Dependency Source Ambiguity (High Severity)

**Issue:**
The `pyproject.toml` declares a dependency on `agent-framework-core` without specifying a version or path.

```toml
[project.optional-dependencies]
magentic = [
    "agent-framework-core",
]
```

**Impact:**
1.  **PyPI vs. Local Mismatch:** It is unclear if `agent-framework-core` is being pulled from PyPI or the local `reference_repos`. The local reference contains specific `MagenticBuilder` logic that may not be present or identical in a potentially stale PyPI package.
2.  **Deployment Failure:** If the PyPI package is missing or version-mismatched, `pip install .[magentic]` will fail or install a broken version on deployment (e.g., HuggingFace Spaces).

**Fix Required:**
Explicitly define the source of `agent-framework-core`. If relying on the local reference, use a relative path dependency or ensure the correct version is published and pinned.
*Recommendation:* For this repo, since `reference_repos` is included, we should install from the local path in development, but this is hard with standard `pyproject.toml` (path dependencies don't work well for uploads).
*Alternative:* Verify exact PyPI version matches `reference_repos` and pin it.

---

## 3. Missing "Free Tier" for Magentic Mode (Medium Severity)

**Issue:**
Magentic mode is currently hard-locked to OpenAI.

```python
# src/orchestrator_magentic.py
if not settings.openai_api_key:
    raise ConfigurationError("Magentic mode requires OPENAI_API_KEY...")
```

**Impact:**
Users relying on the "Free Tier" (HuggingFace Inference) cannot use the Multi-Agent features. This bifurcates the user experience:
*   **Free User:** Simple linear search (Phase 4).
*   **Paid User:** Advanced multi-agent loop (Phase 5).

**Mitigation:**
This is currently "Working as Designed" due to technical limitations of HF models with tool calling, but it should be clearly documented in the UI (which has been done in `app.py`).

---

## Action Plan

1.  [IMMEDIATE] Refactor `src/agents/magentic_agents.py` to use `settings.openai_model`.
2.  [IMMEDIATE] Verify `agent-framework-core` installation source.
