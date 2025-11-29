# Bug Investigation: Invalid Default LLM Models

## Status
- **Date:** 2025-11-29
- **Reporter:** CLI User
- **Component:** `src/utils/config.py`
- **Priority:** High (Magentic Mode Blocker)
- **Resolution:** FIXED

## Issue Description
The user encountered a 403 error when running in Magentic mode:
`Error code: 403 - {'error': {'message': 'Project ... does not have access to model gpt-5.1', ... 'code': 'model_not_found'}}`

This indicates the application is trying to use `gpt-5.1`, which the user's API key did not have access to (likely a beta/gated model).

## Root Cause Analysis
The default config used `gpt-5.1` (beta/preview) and `claude-sonnet-4-5-20250929`.
Initial remediation mistakenly downgraded these to 2024 models (`gpt-4o`).
Web search confirmed that in November 2025:
- `claude-sonnet-4-5-20250929` IS valid.
- `gpt-5.1` exists but access is restricted (leading to 403).
- `gpt-5` (August 2025) is the stable flagship.

## Solution Implemented
Updated `src/utils/config.py` to use:
- `anthropic_model`: `claude-sonnet-4-5-20250929` (Restored correct Nov 2025 model)
- `openai_model`: `gpt-5` (Changed from 5.1 to 5 to ensure stability/access).

## Verification
- `tests/unit/agent_factory/test_judges_factory.py` updated and passed.