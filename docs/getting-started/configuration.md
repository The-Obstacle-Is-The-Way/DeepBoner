# Configuration Guide

DeepBoner uses [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) for configuration, loading values from environment variables and `.env` files.

## Configuration Sources

Settings are loaded in this order (later sources override earlier):

1. Default values in code
2. `.env` file in project root
3. Environment variables

## Quick Setup

```bash
# Copy the template
cp .env.example .env

# Edit with your settings
nano .env  # or your preferred editor
```

## Configuration Categories

### LLM Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_PROVIDER` | string | `"openai"` | LLM provider: `"openai"` or `"huggingface"` |
| `OPENAI_API_KEY` | string | None | OpenAI API key (enables premium mode) |
| `OPENAI_MODEL` | string | `"gpt-5"` | OpenAI model to use |
| `HUGGINGFACE_MODEL` | string | `"Qwen/Qwen2.5-7B-Instruct"` | HuggingFace model for free tier |
| `HF_TOKEN` | string | None | HuggingFace token for gated models |

**Notes:**
- If `OPENAI_API_KEY` is set, OpenAI is used automatically
- Without any key, free HuggingFace tier is used
- See CLAUDE.md for critical notes on HuggingFace model selection

### Embedding Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_EMBEDDING_MODEL` | string | `"text-embedding-3-small"` | OpenAI embedding model (premium RAG) |
| `LOCAL_EMBEDDING_MODEL` | string | `"all-MiniLM-L6-v2"` | Local sentence-transformers model |

### External Services

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `NCBI_API_KEY` | string | None | NCBI API key for higher PubMed rate limits |
| `CHROMA_DB_PATH` | string | `"./chroma_db"` | ChromaDB storage path |

### Agent Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_ITERATIONS` | int | `10` | Maximum search-judge loop iterations (1-50) |
| `ADVANCED_MAX_ROUNDS` | int | `5` | Max coordination rounds for multi-agent mode |
| `ADVANCED_TIMEOUT` | float | `600.0` | Timeout for advanced mode in seconds |
| `SEARCH_TIMEOUT` | int | `30` | Seconds to wait for each search operation |

### Logging

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOG_LEVEL` | string | `"INFO"` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Example Configurations

### Minimal (Free Tier)

```bash
# .env - No keys required
LOG_LEVEL=INFO
MAX_ITERATIONS=5
```

### Development

```bash
# .env
LOG_LEVEL=DEBUG
MAX_ITERATIONS=3
SEARCH_TIMEOUT=15
```

### Production (With OpenAI)

```bash
# .env
OPENAI_API_KEY=sk-your-production-key
NCBI_API_KEY=your-ncbi-key
LOG_LEVEL=WARNING
MAX_ITERATIONS=10
CHROMA_DB_PATH=/data/chroma_db
```

### HuggingFace Spaces

```bash
# Set as Secrets in Space Settings
HF_TOKEN=hf_your-token
NCBI_API_KEY=your-ncbi-key
```

## Backend Selection Logic

The system auto-selects backends based on available keys:

```
Has OPENAI_API_KEY?
  ├── YES → OpenAI GPT-5 (premium)
  └── NO → HuggingFace Qwen 2.5 7B (free)
```

Both backends use the same orchestration logic - only the LLM differs.

## Programmatic Access

Access settings in code:

```python
from src.utils.config import settings

# Check available backends
if settings.has_openai_key:
    print("Premium mode available")

# Get specific settings
print(f"Max iterations: {settings.max_iterations}")
print(f"Log level: {settings.log_level}")
```

## Validation

Settings are validated on load:

```python
from src.utils.config import Settings

# These will raise ValidationError
Settings(max_iterations=100)  # Must be 1-50
Settings(log_level="TRACE")   # Invalid level
```

## Security Notes

- Never commit `.env` files to git
- Use environment variables in production
- API keys are never logged
- See [SECURITY.md](../../SECURITY.md) for full security policy

## Troubleshooting

**Settings not loading?**
- Check file is named `.env` (not `.env.txt`)
- Verify file is in project root
- Check for syntax errors (no spaces around `=`)

**API key not working?**
- Verify key is valid and not expired
- Check for trailing whitespace
- Ensure correct variable name

See [Troubleshooting](troubleshooting.md) for more help.

## Related Documentation

- [Environment Variables Reference](../reference/environment-variables.md)
- [Installation Guide](installation.md)
- [Deployment Guide](../deployment/docker.md)
