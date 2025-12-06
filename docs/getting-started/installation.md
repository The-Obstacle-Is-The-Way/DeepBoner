# Installation Guide

This guide covers installing DeepBoner for development or local use.

## Prerequisites

### Required
- **Python 3.11+** - Required for type hints and async features
- **uv** - Fast Python package manager ([install guide](https://github.com/astral-sh/uv))
- **Git** - For version control

### Optional
- **Docker** - For containerized deployment
- **OpenAI API key** - For premium features (GPT-5)
- **NCBI API key** - For higher PubMed rate limits

## Quick Install

```bash
# Clone the repository
git clone https://github.com/The-Obstacle-Is-The-Way/DeepBoner.git
cd DeepBoner

# Install all dependencies (including dev tools)
make install
```

This runs `uv sync --all-extras && uv run pre-commit install` behind the scenes.

## Manual Installation

If you prefer not to use `make`:

```bash
# Install uv if not already installed
pip install uv

# Sync all dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

## Optional Dependencies

DeepBoner has optional dependency groups for specific features:

```bash
# Core only (no dev tools)
uv sync

# With development tools
uv sync --extra dev

# With Microsoft Agent Framework (Magentic)
uv sync --extra magentic

# With LlamaIndex RAG support
uv sync --extra rag

# Everything
uv sync --all-extras
```

## Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings:
   ```bash
   # Required for premium features
   OPENAI_API_KEY=sk-your-key-here

   # Optional: Higher PubMed rate limits
   NCBI_API_KEY=your-ncbi-key-here

   # Optional: HuggingFace token for gated models
   HF_TOKEN=hf_your-token-here
   ```

See [Configuration Guide](configuration.md) for all options.

## Verify Installation

Run the quality checks to verify everything works:

```bash
make check
```

This runs:
- Linting (ruff)
- Type checking (mypy)
- Unit tests (pytest)

All checks should pass before you start development.

## Running the Application

Start the Gradio UI:

```bash
uv run python src/app.py
```

Open http://localhost:7860 in your browser.

## Docker Installation

For containerized deployment:

```bash
# Build the image
docker build -t deepboner .

# Run the container
docker run -p 7860:7860 --env-file .env deepboner
```

See [Docker Deployment](../deployment/docker.md) for details.

## Troubleshooting

### Common Issues

**uv not found**
```bash
pip install uv
# or
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Python version mismatch**
```bash
# Check your Python version
python --version

# Should be 3.11 or higher
# Use pyenv to manage versions if needed
```

**Pre-commit hook failures**
```bash
# Run formatting to fix most issues
make format
```

**Import errors after install**
```bash
# Ensure you're using uv run
uv run python -c "import src.app"
```

See [Troubleshooting](troubleshooting.md) for more solutions.

## Next Steps

- [Quickstart Guide](quickstart.md) - Run your first query
- [Configuration Guide](configuration.md) - Configure all options
- [Architecture Overview](../architecture/overview.md) - Understand the system
