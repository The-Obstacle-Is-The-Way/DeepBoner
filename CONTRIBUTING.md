# Contributing to DeepBoner

Thank you for your interest in contributing to DeepBoner! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Documentation](#documentation)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to keep our community welcoming and respectful.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/DeepBoner.git
   cd DeepBoner
   ```

3. **Install dependencies**:
   ```bash
   make install
   # or manually:
   uv sync --all-extras && uv run pre-commit install
   ```

4. **Copy the environment template**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys if needed
   ```

5. **Verify your setup**:
   ```bash
   make check
   ```

## Making Changes

### Branch Naming Convention

- `feature/short-description` - New features
- `fix/short-description` - Bug fixes
- `docs/short-description` - Documentation changes
- `refactor/short-description` - Code refactoring
- `test/short-description` - Test additions/improvements

### Commit Message Format

We follow conventional commit messages:

```
type(scope): short description

Optional longer description explaining the change.

Closes #123
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style (formatting, no logic change)
- `refactor` - Code refactoring
- `test` - Adding/updating tests
- `chore` - Build process, tooling, dependencies

Examples:
```
feat(tools): add OpenAlex API integration
fix(pubmed): handle empty search results gracefully
docs(readme): update quick start instructions
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
uv run pytest tests/unit/utils/test_config.py -v

# Run specific test
uv run pytest tests/unit/utils/test_config.py::TestSettings::test_default_max_iterations -v
```

### Test Markers

- `@pytest.mark.unit` - Unit tests (mocked, fast)
- `@pytest.mark.integration` - Integration tests (real APIs)
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.e2e` - End-to-end tests

### Writing Tests

- **TDD preferred**: Write tests first, then implementation
- **Location**: Place unit tests in `tests/unit/` mirroring `src/` structure
- **Mocking**: Use `respx` for httpx, `pytest-mock` for general mocking
- **Fixtures**: Add reusable fixtures to `tests/conftest.py`

Example test structure:
```python
"""Tests for search handler module."""
import pytest
from src.tools.search_handler import SearchHandler

class TestSearchHandler:
    """Tests for SearchHandler class."""

    @pytest.mark.unit
    def test_parallel_search_returns_results(self, mock_httpx_client):
        """Verify parallel search aggregates results correctly."""
        handler = SearchHandler()
        result = handler.search("test query")
        assert len(result.evidence) > 0
```

## Code Style

### Pre-commit Hooks

Pre-commit hooks run automatically on commit:
- **Ruff** - Linting and formatting
- **MyPy** - Type checking

To run manually:
```bash
make lint      # Check linting
make format    # Auto-format code
make typecheck # Type checking
```

### Style Guidelines

1. **Type hints required** - All functions must have type annotations
2. **Docstrings** - Use Google-style docstrings for public APIs
3. **Line length** - Maximum 100 characters
4. **Imports** - Sorted by isort (handled by ruff)

### Code Quality Rules

We use Ruff with these rule sets:
- `E` - pycodestyle errors
- `F` - pyflakes
- `B` - flake8-bugbear
- `I` - isort
- `N` - pep8-naming
- `UP` - pyupgrade
- `PL` - pylint
- `RUF` - ruff-specific

## Submitting Changes

### Pull Request Process

1. **Ensure tests pass**: `make check`
2. **Update documentation** if adding features
3. **Create PR** against `main` branch
4. **Fill out the PR template** with:
   - Summary of changes
   - Related issues
   - Test plan
5. **Wait for review** - Address any feedback

### PR Checklist

- [ ] Tests added/updated and passing
- [ ] `make check` passes locally
- [ ] Documentation updated (if applicable)
- [ ] Commit messages follow convention
- [ ] No secrets or API keys committed
- [ ] Changes are focused (one concern per PR)

## Documentation

### Where to Document

- **README.md** - User-facing overview and quick start
- **CLAUDE.md** - Developer/AI agent reference
- **docs/** - Detailed documentation
  - `architecture/` - System design
  - `development/` - Developer guides
  - `deployment/` - Deployment instructions
  - `reference/` - API/config reference

### Documentation Standards

- Use clear, concise language
- Include code examples where helpful
- Keep diagrams updated (Mermaid format)
- Link to related documentation

## Getting Help

- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions

## Recognition

Contributors will be recognized in release notes. Thank you for helping make DeepBoner better!

---

*"Peer-reviewed contributions only. We take evidence-based code very seriously."* 🔬
