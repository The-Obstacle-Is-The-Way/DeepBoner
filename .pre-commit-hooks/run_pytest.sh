#!/bin/bash
# Cross-platform pytest runner for pre-commit
# Uses uv if available, otherwise falls back to pytest

if command -v uv >/dev/null 2>&1; then
    uv run pytest "$@"
else
    echo "Warning: uv not found, using system pytest (may have missing dependencies)"
    pytest "$@"
fi





