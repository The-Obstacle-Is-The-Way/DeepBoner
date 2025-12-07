# Configuration Reference

> **Last Updated**: 2025-12-06

Complete reference for all configuration options in DeepBoner.

## Configuration System

DeepBoner uses [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) for configuration management.

### Loading Order

1. Default values in code (`src/utils/config.py`)
2. `.env` file in project root
3. Environment variables (highest priority)

### Location

```
/home/user/DeepBoner/
├── .env            # Your configuration (not in git)
├── .env.example    # Template (in git)
└── src/utils/config.py  # Settings class
```

## Settings Class

```python
from src.utils.config import settings

# Access settings
print(settings.max_iterations)
print(settings.has_openai_key)
```

## Configuration Categories

### LLM Configuration

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `llm_provider` | Literal["openai", "huggingface"] | `"openai"` | `LLM_PROVIDER` | LLM backend to use |
| `openai_api_key` | str \| None | None | `OPENAI_API_KEY` | OpenAI API key |
| `openai_model` | str | `"gpt-5"` | `OPENAI_MODEL` | OpenAI model name |
| `huggingface_model` | str \| None | `"Qwen/Qwen2.5-7B-Instruct"` | `HUGGINGFACE_MODEL` | HuggingFace model |
| `hf_token` | str \| None | None | `HF_TOKEN` | HuggingFace API token |

### Embedding Configuration

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `openai_embedding_model` | str | `"text-embedding-3-small"` | `OPENAI_EMBEDDING_MODEL` | OpenAI embeddings model |
| `local_embedding_model` | str | `"all-MiniLM-L6-v2"` | `LOCAL_EMBEDDING_MODEL` | Local sentence-transformers model |

### External Services

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `ncbi_api_key` | str \| None | None | `NCBI_API_KEY` | NCBI API key for PubMed |
| `chroma_db_path` | str | `"./chroma_db"` | `CHROMA_DB_PATH` | ChromaDB storage path |

### Agent Configuration

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `max_iterations` | int | 10 | `MAX_ITERATIONS` | Max search-judge iterations (1-50) |
| `advanced_max_rounds` | int | 5 | `ADVANCED_MAX_ROUNDS` | Max multi-agent rounds (1-20) |
| `advanced_timeout` | float | 600.0 | `ADVANCED_TIMEOUT` | Advanced mode timeout seconds (60-900) |
| `search_timeout` | int | 30 | `SEARCH_TIMEOUT` | Per-search timeout seconds |

### Domain Configuration

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `research_domain` | ResearchDomain | `SEXUAL_HEALTH` | `RESEARCH_DOMAIN` | Research domain focus |

### Logging

| Setting | Type | Default | Env Variable | Description |
|---------|------|---------|--------------|-------------|
| `log_level` | Literal["DEBUG", "INFO", "WARNING", "ERROR"] | `"INFO"` | `LOG_LEVEL` | Logging verbosity |

## Helper Properties

The Settings class provides convenience properties:

```python
settings.has_openai_key      # bool - Is OpenAI key set?
settings.has_huggingface_key # bool - Is HF token set?
settings.has_any_llm_key     # bool - Any LLM key available?
```

## Helper Methods

```python
# Get API key for configured provider
api_key = settings.get_api_key()

# Get OpenAI key (raises ConfigurationError if not set)
openai_key = settings.get_openai_api_key()
```

## Backend Selection Logic

```python
# Automatic backend selection
if settings.has_openai_key:
    # Use OpenAI GPT-5
    client = OpenAIChatClient(api_key=settings.openai_api_key)
else:
    # Use HuggingFace free tier
    client = HuggingFaceChatClient(model=settings.huggingface_model)
```

## Validation

Settings are validated on load:

```python
# These will raise ValidationError
Settings(max_iterations=100)   # Must be 1-50
Settings(log_level="TRACE")    # Invalid level
Settings(advanced_timeout=10)  # Minimum is 60
```

## Example Configurations

### Minimal (Free Tier)

```bash
# .env
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

### Production (Premium)

```bash
# .env
OPENAI_API_KEY=sk-...
NCBI_API_KEY=...
LOG_LEVEL=WARNING
MAX_ITERATIONS=10
ADVANCED_TIMEOUT=300
CHROMA_DB_PATH=/data/chroma
```

### HuggingFace Spaces

Set as Secrets (not Variables) in Space Settings:

```
HF_TOKEN=hf_...
NCBI_API_KEY=...
```

## Programmatic Configuration

Override settings in code (useful for testing):

```python
from src.utils.config import Settings

# Create with overrides
test_settings = Settings(
    max_iterations=3,
    log_level="DEBUG",
    _env_file=None  # Ignore .env
)
```

## Related Documentation

- [Environment Variables](environment-variables.md)
- [Getting Started - Configuration](../getting-started/configuration.md)
- [Troubleshooting](../getting-started/troubleshooting.md)
