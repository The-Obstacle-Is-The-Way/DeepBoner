# Environment Variables Reference

> **Last Updated**: 2025-12-06

Complete reference for all environment variables used by DeepBoner.

## Quick Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | No* | - | OpenAI API key |
| `HF_TOKEN` | No | - | HuggingFace token |
| `NCBI_API_KEY` | No | - | NCBI/PubMed API key |
| `LLM_PROVIDER` | No | `openai` | LLM backend |
| `MAX_ITERATIONS` | No | `10` | Max search iterations |
| `LOG_LEVEL` | No | `INFO` | Logging level |

*At least one of OPENAI_API_KEY or HF_TOKEN is needed for full functionality.

## LLM Configuration

### OPENAI_API_KEY

OpenAI API key for premium features.

```bash
OPENAI_API_KEY=sk-proj-xxxx
```

- **Format:** Starts with `sk-` or `sk-proj-`
- **Source:** https://platform.openai.com/api-keys
- **Effect:** Enables OpenAI GPT-5 as the LLM backend

### ANTHROPIC_API_KEY

Anthropic API key (reserved for future use).

```bash
ANTHROPIC_API_KEY=sk-ant-xxxx
```

### LLM_PROVIDER

Explicitly select LLM provider.

```bash
LLM_PROVIDER=openai    # Use OpenAI
LLM_PROVIDER=huggingface  # Use HuggingFace
```

- **Default:** `openai`
- **Note:** Auto-detection uses OPENAI_API_KEY presence

### OPENAI_MODEL

OpenAI model name.

```bash
OPENAI_MODEL=gpt-5
OPENAI_MODEL=gpt-4o
```

- **Default:** `gpt-5`

### HUGGINGFACE_MODEL

HuggingFace model for free tier.

```bash
HUGGINGFACE_MODEL=Qwen/Qwen2.5-7B-Instruct
```

- **Default:** `Qwen/Qwen2.5-7B-Instruct`
- **Warning:** Large models (70B+) route to unreliable third-party providers

### HF_TOKEN

HuggingFace API token.

```bash
HF_TOKEN=hf_xxxx
```

- **Source:** https://huggingface.co/settings/tokens
- **Effect:** Enables gated models and higher rate limits

## Embedding Configuration

### OPENAI_EMBEDDING_MODEL

OpenAI embedding model for premium RAG.

```bash
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
```

- **Default:** `text-embedding-3-small`
- **Requires:** `OPENAI_API_KEY`

### LOCAL_EMBEDDING_MODEL

Local sentence-transformers model.

```bash
LOCAL_EMBEDDING_MODEL=all-MiniLM-L6-v2
LOCAL_EMBEDDING_MODEL=all-mpnet-base-v2
```

- **Default:** `all-MiniLM-L6-v2`
- **Note:** Downloaded on first use

## External Services

### NCBI_API_KEY

NCBI API key for higher PubMed rate limits.

```bash
NCBI_API_KEY=xxxx
```

- **Source:** https://www.ncbi.nlm.nih.gov/account/settings/
- **Effect:** 10 requests/second instead of 3

### CHROMA_DB_PATH

ChromaDB storage location.

```bash
CHROMA_DB_PATH=./chroma_db
CHROMA_DB_PATH=/data/vectors
```

- **Default:** `./chroma_db`
- **Note:** Directory is created if it doesn't exist

## Agent Configuration

### MAX_ITERATIONS

Maximum search-judge loop iterations.

```bash
MAX_ITERATIONS=10
MAX_ITERATIONS=5   # Faster but less thorough
MAX_ITERATIONS=20  # More thorough
```

- **Default:** `10`
- **Range:** `1` to `50`

### ADVANCED_MAX_ROUNDS

Maximum multi-agent coordination rounds.

```bash
ADVANCED_MAX_ROUNDS=5
```

- **Default:** `5`
- **Range:** `1` to `20`

### ADVANCED_TIMEOUT

Timeout for advanced mode in seconds.

```bash
ADVANCED_TIMEOUT=600   # 10 minutes
ADVANCED_TIMEOUT=300   # 5 minutes
```

- **Default:** `600.0`
- **Range:** `60.0` to `900.0`

### SEARCH_TIMEOUT

Per-search operation timeout in seconds.

```bash
SEARCH_TIMEOUT=30
```

- **Default:** `30`

## Logging

### LOG_LEVEL

Logging verbosity.

```bash
LOG_LEVEL=DEBUG    # Verbose
LOG_LEVEL=INFO     # Normal
LOG_LEVEL=WARNING  # Errors and warnings
LOG_LEVEL=ERROR    # Errors only
```

- **Default:** `INFO`

## Gradio Configuration

### GRADIO_SERVER_NAME

Server bind address.

```bash
GRADIO_SERVER_NAME=0.0.0.0  # All interfaces
GRADIO_SERVER_NAME=127.0.0.1  # Localhost only
```

- **Default:** Set in Dockerfile for containers

### GRADIO_SERVER_PORT

Server port.

```bash
GRADIO_SERVER_PORT=7860
```

- **Default:** `7860`

## Python Configuration

### PYTHONPATH

Python module search path.

```bash
PYTHONPATH=/app
```

- **Note:** Set automatically in Docker

## .env File Format

```bash
# Comments start with #
KEY=value           # No quotes needed for simple values
KEY="value"         # Quotes for values with spaces
KEY='value'         # Single quotes also work

# Empty lines are ignored

# Multi-line values not supported - use single line
```

## Security Notes

1. **Never commit .env files** - They're in .gitignore
2. **Use secrets for production** - HuggingFace Secrets, Docker secrets
3. **Rotate keys regularly** - Especially for production
4. **Limit permissions** - Use read-only keys where possible

## Validation

Variables are validated on application startup:

```python
# Invalid values raise ValidationError
MAX_ITERATIONS=100  # Error: must be 1-50
LOG_LEVEL=TRACE     # Error: invalid level
```

## Debugging

Check loaded configuration:

```bash
LOG_LEVEL=DEBUG uv run python -c "
from src.utils.config import settings
print(f'Provider: {settings.llm_provider}')
print(f'Has OpenAI: {settings.has_openai_key}')
print(f'Has HF: {settings.has_huggingface_key}')
print(f'Max Iterations: {settings.max_iterations}')
"
```

## Related Documentation

- [Configuration Reference](configuration.md)
- [Getting Started - Configuration](../getting-started/configuration.md)
- [Deployment - Docker](../deployment/docker.md)
