# Bug Investigation: Invalid Default LLM Models

## Status
- **Date:** 2025-11-29
- **Reporter:** CLI User
- **Component:** `src/utils/config.py`
- **Priority:** High (Magentic Mode Blocker)
- **Resolution:** FIXED

## Issue Description
The user encountered a 403 error when running in Magentic mode:
`Error code: 403 - {'error': {'message': 'Project ... does not have access to model gpt-5', ... 'code': 'model_not_found'}}`

## Root Cause Analysis
OpenAI deprecated the base `gpt-5` model. Tier 5 accounts now have access to:
- `gpt-5.1` (current flagship)
- `gpt-5-mini`
- `gpt-5-nano`
- `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`
- `o3`, `o4-mini`

The base `gpt-5` is NO LONGER available via API.

## Solution Implemented
Updated `src/utils/config.py` to use:
- `openai_model`: `gpt-5.1` (the actual current model)
- `anthropic_model`: `claude-sonnet-4-5-20250929` (unchanged)

## Verification
- `tests/unit/agent_factory/test_judges_factory.py` updated and passed.
- User confirmed Tier 5 access to `gpt-5.1` via OpenAI dashboard.
