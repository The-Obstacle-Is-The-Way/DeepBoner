# Troubleshooting Guide

Common issues and their solutions.

## Installation Issues

### uv not found

**Symptom:** `command not found: uv`

**Solution:**
```bash
# Install uv
pip install uv
# or
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Python version mismatch

**Symptom:** `Python 3.11+ required` or syntax errors

**Solution:**
```bash
# Check version
python --version

# Install Python 3.11+ via pyenv
pyenv install 3.11
pyenv local 3.11
```

### Dependency conflicts

**Symptom:** Package version conflicts during install

**Solution:**
```bash
# Clean install
rm -rf .venv uv.lock
uv sync --all-extras
```

## Runtime Issues

### Slow first query

**Symptom:** First query takes 30+ seconds

**Cause:** Model loading (sentence-transformers) on first use

**Solution:** This is expected. Subsequent queries are faster.

### Rate limit errors

**Symptom:** `RateLimitError` or 429 HTTP status

**Cause:** Too many requests to external APIs

**Solutions:**
1. Add NCBI API key for PubMed:
   ```bash
   NCBI_API_KEY=your-key-here
   ```
2. Wait and retry (rate limits reset)
3. Reduce `MAX_ITERATIONS`

### No search results

**Symptom:** Empty results from searches

**Possible causes:**
- Network issues
- External API downtime
- Query too specific

**Solutions:**
1. Check internet connection
2. Try a broader query
3. Check API status:
   - [PubMed Status](https://www.ncbi.nlm.nih.gov/Status/)
   - [ClinicalTrials.gov](https://clinicaltrials.gov/)

### HuggingFace 500/401 errors

**Symptom:** Internal server errors or auth errors from HuggingFace

**Cause:** Large models (70B+) are routed to unreliable third-party providers

**Solution:** Use default model (Qwen 2.5 7B) which stays on HuggingFace native infrastructure. See CLAUDE.md for details.

### OpenAI API errors

**Symptom:** Authentication errors with OpenAI

**Solutions:**
1. Verify key is valid: https://platform.openai.com/api-keys
2. Check for typos in `.env`
3. Ensure no trailing whitespace
4. Check quota: https://platform.openai.com/usage

### Import errors

**Symptom:** `ModuleNotFoundError` when running

**Solution:**
```bash
# Always use uv run
uv run python src/app.py

# Not this
python src/app.py  # Won't find dependencies
```

### ChromaDB errors

**Symptom:** Embedding or vector store errors

**Solutions:**
```bash
# Clear the database
rm -rf ./chroma_db

# Verify path is writable
ls -la ./
```

## Development Issues

### Pre-commit hook failures

**Symptom:** Commits rejected by pre-commit

**Solution:**
```bash
# Auto-fix formatting
make format

# Check manually
make lint
make typecheck
```

### Type checking errors

**Symptom:** mypy errors on valid code

**Solutions:**
```bash
# Update stubs
uv add --dev types-package-name

# Or add ignore comment (last resort)
# type: ignore[error-code]
```

### Test failures

**Symptom:** Tests pass locally but fail in CI

**Possible causes:**
- Environment differences
- Async timing issues
- Missing test data

**Solutions:**
```bash
# Run exactly like CI
make check

# Run specific test with verbose output
uv run pytest tests/unit/path/test_file.py -v -s
```

## UI Issues

### Gradio not starting

**Symptom:** Application exits immediately or port conflict

**Solutions:**
```bash
# Check if port is in use
lsof -i :7860

# Kill existing process
kill -9 $(lsof -t -i :7860)

# Or use different port
uv run python -c "import gradio; print(gradio.__version__)"
```

### MCP tools not appearing

**Symptom:** Claude Desktop doesn't show DeepBoner tools

**Solutions:**
1. Verify URL: `http://localhost:7860/gradio_api/mcp/`
2. Check Claude Desktop config syntax
3. Restart Claude Desktop after config change
4. Ensure DeepBoner is running

## Deployment Issues

### Docker build fails

**Symptom:** Dockerfile build errors

**Solutions:**
```bash
# Clean build
docker build --no-cache -t deepboner .

# Check disk space
docker system df
docker system prune
```

### Container exits immediately

**Symptom:** Container starts and stops

**Solution:**
```bash
# Check logs
docker logs <container_id>

# Run interactively
docker run -it deepboner bash
```

### HuggingFace Spaces issues

**Symptom:** Space fails to build or run

**Solutions:**
1. Check Spaces logs in HuggingFace UI
2. Verify `requirements.txt` matches `pyproject.toml`
3. Check secrets are set correctly

## Getting More Help

### Enable debug logging

```bash
LOG_LEVEL=DEBUG uv run python src/app.py
```

### Check system info

```bash
uv run python -c "
import sys
print(f'Python: {sys.version}')

import src
print(f'DeepBoner loaded')

from src.utils.config import settings
print(f'OpenAI key: {bool(settings.openai_api_key)}')
print(f'HF key: {bool(settings.hf_token)}')
"
```

### Report an issue

If you can't resolve the issue:

1. Search existing issues: https://github.com/The-Obstacle-Is-The-Way/DeepBoner/issues
2. Create a new issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment info (Python version, OS)
   - Relevant logs (redact API keys)

## Related Documentation

- [Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [SECURITY.md](../../SECURITY.md)
