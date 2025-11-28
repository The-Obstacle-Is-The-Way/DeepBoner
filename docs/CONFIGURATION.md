# Configuration Guide

## Overview

DeepCritical uses **Pydantic Settings** for centralized configuration management. All settings are defined in `src/utils/config.py` and can be configured via environment variables or a `.env` file.

## Quick Start

1. Copy the example environment file (if available) or create a `.env` file in the project root
2. Set at least one LLM API key (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
3. Optionally configure other services as needed

## Configuration System

### How It Works

- **Settings Class**: `Settings` class in `src/utils/config.py` extends `BaseSettings` from `pydantic_settings`
- **Environment File**: Automatically loads from `.env` file (if present)
- **Environment Variables**: Reads from environment variables (case-insensitive)
- **Type Safety**: Strongly-typed fields with validation
- **Singleton Pattern**: Global `settings` instance for easy access

### Usage

```python
from src.utils.config import settings

# Check if API keys are available
if settings.has_openai_key:
    # Use OpenAI
    pass

# Access configuration values
max_iterations = settings.max_iterations
web_search_provider = settings.web_search_provider
```

## Required Configuration

### At Least One LLM Provider

You must configure at least one LLM provider:

**OpenAI:**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5.1
```

**Anthropic:**
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

## Optional Configuration

### Embedding Configuration

```bash
# Embedding Provider: "openai", "local", or "huggingface"
EMBEDDING_PROVIDER=local

# OpenAI Embedding Model (used by LlamaIndex RAG)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Local Embedding Model (sentence-transformers)
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2

# HuggingFace Embedding Model
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### HuggingFace Configuration

```bash
# HuggingFace API Token (for inference API)
HUGGINGFACE_API_KEY=your_huggingface_api_key_here
# Or use HF_TOKEN (alternative name)

# Default HuggingFace Model ID
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

### Web Search Configuration

```bash
# Web Search Provider: "serper", "searchxng", "brave", "tavily", or "duckduckgo"
# Default: "duckduckgo" (no API key required)
WEB_SEARCH_PROVIDER=duckduckgo

# Serper API Key (for Google search via Serper)
SERPER_API_KEY=your_serper_api_key_here

# SearchXNG Host URL
SEARCHXNG_HOST=http://localhost:8080

# Brave Search API Key
BRAVE_API_KEY=your_brave_api_key_here

# Tavily API Key
TAVILY_API_KEY=your_tavily_api_key_here
```

### PubMed Configuration

```bash
# NCBI API Key (optional, for higher rate limits: 10 req/sec vs 3 req/sec)
NCBI_API_KEY=your_ncbi_api_key_here
```

### Agent Configuration

```bash
# Maximum iterations per research loop
MAX_ITERATIONS=10

# Search timeout in seconds
SEARCH_TIMEOUT=30

# Use graph-based execution for research flows
USE_GRAPH_EXECUTION=false
```

### Budget & Rate Limiting Configuration

```bash
# Default token budget per research loop
DEFAULT_TOKEN_LIMIT=100000

# Default time limit per research loop (minutes)
DEFAULT_TIME_LIMIT_MINUTES=10

# Default iterations limit per research loop
DEFAULT_ITERATIONS_LIMIT=10
```

### RAG Service Configuration

```bash
# ChromaDB collection name for RAG
RAG_COLLECTION_NAME=deepcritical_evidence

# Number of top results to retrieve from RAG
RAG_SIMILARITY_TOP_K=5

# Automatically ingest evidence into RAG
RAG_AUTO_INGEST=true
```

### ChromaDB Configuration

```bash
# ChromaDB storage path
CHROMA_DB_PATH=./chroma_db

# Whether to persist ChromaDB to disk
CHROMA_DB_PERSIST=true

# ChromaDB server host (for remote ChromaDB, optional)
# CHROMA_DB_HOST=localhost

# ChromaDB server port (for remote ChromaDB, optional)
# CHROMA_DB_PORT=8000
```

### External Services

```bash
# Modal Token ID (for Modal sandbox execution)
MODAL_TOKEN_ID=your_modal_token_id_here

# Modal Token Secret
MODAL_TOKEN_SECRET=your_modal_token_secret_here
```

### Logging Configuration

```bash
# Log Level: "DEBUG", "INFO", "WARNING", or "ERROR"
LOG_LEVEL=INFO
```

## Configuration Properties

The `Settings` class provides helpful properties for checking configuration:

```python
from src.utils.config import settings

# Check API key availability
settings.has_openai_key          # bool
settings.has_anthropic_key       # bool
settings.has_huggingface_key     # bool
settings.has_any_llm_key         # bool

# Check service availability
settings.modal_available         # bool
settings.web_search_available    # bool
```

## Environment Variables Reference

### Required (at least one LLM)
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - At least one LLM provider key

### Optional LLM Providers
- `DEEPSEEK_API_KEY` (Phase 2)
- `OPENROUTER_API_KEY` (Phase 2)
- `GEMINI_API_KEY` (Phase 2)
- `PERPLEXITY_API_KEY` (Phase 2)
- `HUGGINGFACE_API_KEY` or `HF_TOKEN`
- `AZURE_OPENAI_ENDPOINT` (Phase 2)
- `AZURE_OPENAI_DEPLOYMENT` (Phase 2)
- `AZURE_OPENAI_API_KEY` (Phase 2)
- `AZURE_OPENAI_API_VERSION` (Phase 2)
- `LOCAL_MODEL_URL` (Phase 2)

### Web Search
- `WEB_SEARCH_PROVIDER` (default: "duckduckgo")
- `SERPER_API_KEY`
- `SEARCHXNG_HOST`
- `BRAVE_API_KEY`
- `TAVILY_API_KEY`

### Embeddings
- `EMBEDDING_PROVIDER` (default: "local")
- `HUGGINGFACE_EMBEDDING_MODEL` (optional)

### RAG
- `RAG_COLLECTION_NAME` (default: "deepcritical_evidence")
- `RAG_SIMILARITY_TOP_K` (default: 5)
- `RAG_AUTO_INGEST` (default: true)

### ChromaDB
- `CHROMA_DB_PATH` (default: "./chroma_db")
- `CHROMA_DB_PERSIST` (default: true)
- `CHROMA_DB_HOST` (optional)
- `CHROMA_DB_PORT` (optional)

### Budget
- `DEFAULT_TOKEN_LIMIT` (default: 100000)
- `DEFAULT_TIME_LIMIT_MINUTES` (default: 10)
- `DEFAULT_ITERATIONS_LIMIT` (default: 10)

### Other
- `LLM_PROVIDER` (default: "openai")
- `NCBI_API_KEY` (optional)
- `MODAL_TOKEN_ID` (optional)
- `MODAL_TOKEN_SECRET` (optional)
- `MAX_ITERATIONS` (default: 10)
- `LOG_LEVEL` (default: "INFO")
- `USE_GRAPH_EXECUTION` (default: false)

## Validation

Settings are validated on load using Pydantic validation:

- **Type checking**: All fields are strongly typed
- **Range validation**: Numeric fields have min/max constraints
- **Literal validation**: Enum fields only accept specific values
- **Required fields**: API keys are checked when accessed via `get_api_key()`

## Error Handling

Configuration errors raise `ConfigurationError`:

```python
from src.utils.config import settings
from src.utils.exceptions import ConfigurationError

try:
    api_key = settings.get_api_key()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Future Enhancements (Phase 2)

The following configurations are planned for Phase 2:

1. **Additional LLM Providers**: DeepSeek, OpenRouter, Gemini, Perplexity, Azure OpenAI, Local models
2. **Model Selection**: Reasoning/main/fast model configuration
3. **Service Integration**: Migrate `folder/llm_config.py` to centralized config

See `CONFIGURATION_ANALYSIS.md` for the complete implementation plan.













