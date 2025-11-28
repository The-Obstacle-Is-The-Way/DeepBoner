# Decision Record: PR #55 Evaluation

**Date**: 2025-11-27
**PR**: [#55 - adds the initial iterative and deep research workflows](https://github.com/The-Obstacle-Is-The-Way/DeepCritical-HFSpace/pull/55)
**Author**: @Josephrp
**Status**: Not merged

## Summary

PR #55 proposed 17,779 additions and 3,440 deletions across 68 files. After objective third-party review by CodeRabbit, the PR was found to have significant quality issues that block the test suite from running.

## CodeRabbit Findings

CodeRabbit's automated review identified **35+ critical issues**:

| Issue | Count | Severity |
|-------|-------|----------|
| Import errors (`AgentResult` doesn't exist in pydantic-ai) | 3 files | Critical - blocks pytest |
| Missing parentheses on method calls | 26 places | Critical |
| Tests calling non-existent methods (`validate()` vs `validate_structure()`) | 3 places | Critical |
| Wrong node ID assertions | 1 place | Critical |
| Broken pytest fixtures (`return` vs `yield`) | 2 places | Critical |

The 3 import errors cause pytest to crash during collection, preventing any tests from running.

## Claims vs Reality

| Claim | Reality |
|-------|---------|
| "nothing is replaced, just added" | `src/orchestrator.py` renamed to `src/legacy_orchestrator.py`; `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` deleted |
| "3 failing tests on a 13k LoC PR is not a major issue" | Those 3 tests crash pytest during collection - entire test suite cannot run |

## Decision

The PR was not merged for the following reasons:

1. **Code was never executed before submission** - Basic import errors indicate no local testing
2. **Parallel architecture, not incremental improvement** - Introduces entirely different orchestration system rather than building on existing working code
3. **Maintenance burden** - Would require maintaining two separate orchestration systems
4. **Existing code labeled "legacy"** - Working, tested code renamed to "legacy" in favor of untested code

## Context

This project is a HuggingFace Spaces hackathon entry. All contributors have direct push access to the HuggingFace Space. Contributors are encouraged to push directly to production when confident in their code, rather than submitting PRs with untested code for others to review and take responsibility for.

## Links

- [PR #55](https://github.com/The-Obstacle-Is-The-Way/DeepCritical-HFSpace/pull/55)
- [CodeRabbit Review](https://github.com/The-Obstacle-Is-The-Way/DeepCritical-HFSpace/pull/55#issuecomment-3587631560)
