# Identified Bugs & Stability Issues

The following issues were identified during a code audit and should be addressed to stabilize the codebase.

## P1: Orchestrator Crash on Initialization Failure
**Location:** `src/orchestrators/advanced.py` in `AdvancedOrchestrator.run`
**Description:** The `init_magentic_state` call (which initializes `ResearchMemory` and potentially the `EmbeddingService`) is located *outside* the main `try...except` block in the `run` method.
**Impact:** If the embedding service fails to initialize (e.g., memory issues, missing dependencies, transient errors), the exception will propagate up and crash the orchestrator generator without yielding an error event to the UI. The user will see a hang or a generic server error instead of a helpful message.
**Fix:** Move `init_magentic_state` inside the `try` block.

## P2: Judge Diversity Selection Ineffective
**Location:** `src/prompts/judge.py` in `select_evidence_for_judge`
**Description:** The function `select_evidence_for_judge` calls `select_diverse_evidence` but fails to pass the `embedding_service`. The `embeddings` argument defaults to `None`.
**Impact:** The diversity selection algorithm (MMR) is never used because it requires the embedding service. The system falls back to simple relevance sorting, reducing the quality of evidence selected for the judge, especially for broad queries.
**Fix:** Retrieve `embedding_service` from `MagenticState` (if initialized) and pass it to `select_diverse_evidence`.

## P3: Embedding Service Race Condition
**Location:** `src/services/embeddings.py` in `_get_shared_model`
**Description:** The global `_shared_model` initialization is not thread-safe.
**Impact:** If multiple requests trigger the first initialization simultaneously, the heavy `SentenceTransformer` model might be loaded multiple times concurrently, wasting CPU/RAM.
**Fix:** Use a thread lock (e.g., `threading.Lock`) around the model initialization.

## P3: LLM Provider Configuration Ignored
**Location:** `src/clients/registry.py` and `src/clients/factory.py`
**Description:** The `LLM_PROVIDER` environment variable (mapped to `settings.llm_provider`) is effectively ignored because `AdvancedOrchestrator` passes `provider=None` to `get_chat_client`. The factory logic prioritizes API key presence over the configured provider name.
**Impact:** If a user explicitly sets `LLM_PROVIDER=openai` but provides no API key (expecting an error), the system silently falls back to HuggingFace. This can be confusing for configuration debugging.
**Fix:** Ensure `get_chat_client` respects `settings.llm_provider` when `provider` arg is None, or clarify precedence in documentation.

## P4: Invalid Default OpenAI Model
**Location:** `src/utils/config.py`
**Description:** The default `openai_model` is set to `"gpt-5"`.
**Impact:** This model does not currently exist in the public OpenAI API. Users using the default configuration with a valid key will likely receive a "model not found" error.
**Fix:** Change default to `"gpt-4o"`.
