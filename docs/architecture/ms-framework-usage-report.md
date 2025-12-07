# Microsoft Agent Framework Usage Report

**Date:** 2025-12-06
**Framework Version:** agent-framework-core==1.0.0b251204

---

## What We Use From MS Framework (pip installed)

### Core Classes
- `BaseChatClient` - Base class for chat clients
- `ChatMessage`, `ChatRole` - Message types
- `ChatOptions` - Request configuration
- `ChatAgent` - Agent base class

### Decorators (Applied to HuggingFaceChatClient)
- `@use_function_invocation` - Enables tool/function calling
- `@use_observability` - Adds OTEL tracing hooks
- `@use_chat_middleware` - Enables middleware pipeline

### Middleware Base Classes (Available but NOT yet used)
- `ChatMiddleware` - Intercepts chat client requests
- `AgentMiddleware` - Intercepts agent invocations
- `FunctionMiddleware` - Intercepts tool calls

---

## What We Hand-Roll (Custom Implementation)

### Orchestration
- `AdvancedOrchestrator` - Main research workflow
- `HierarchicalOrchestrator` - Team-based orchestration
- `SubIterationMiddleware` - Team→judge loop (workflow, not middleware)

### Clients
- `HuggingFaceChatClient` - Adapter for HuggingFace Inference API
- Client factory with auto-detection

### Tools
- `PubMedTool`, `ClinicalTrialsTool`, `EuropePMCTool`
- `SearchHandler` - Scatter-gather orchestration

### Services
- `EmbeddingService` - Local sentence-transformers
- `LlamaIndexRAG` - Premium OpenAI embeddings
- `ResearchMemory` - Research state management

---

## Gap Analysis

| Component | MS Framework Has | DeepBoner Has | Status |
|-----------|------------------|---------------|--------|
| Chat Middleware | `ChatMiddleware` base | Uses decorator only | SPEC-21 |
| Retry Logic | N/A (left to user) | None | SPEC-21 |
| Token Tracking | OTEL histograms | None | SPEC-21 |
| Thread State | `AgentThread` serialization | `ResearchMemory` (no serialization) | P3 |
| Observability | Full OTEL | structlog only | P3 |

---

## Recommendations

1. **Implement `RetryMiddleware`** using MS `ChatMiddleware` base class
2. **Implement `TokenTrackingMiddleware`** for cost visibility
3. **Rename `src/middleware/`** to avoid confusion with MS patterns

See [SPEC-21](../specs/SPEC-21-MIDDLEWARE-ARCHITECTURE.md) for implementation details.
