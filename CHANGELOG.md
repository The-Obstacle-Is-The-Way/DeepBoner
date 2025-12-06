# Changelog

All notable changes to DeepBoner will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation structure (CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md)
- Technical debt tracking documentation
- Component inventory documentation
- Data models reference documentation

## [0.1.0] - 2025-12-04

### Added
- **Core Research Agent**
  - Search-and-judge loop with multi-tool orchestration
  - PubMed E-utilities API integration
  - ClinicalTrials.gov API integration
  - Europe PMC API integration
  - OpenAlex API integration
  - LLM-based evidence quality assessment (Judge)
  - Research report synthesis with citations

- **Multi-Agent Architecture**
  - Microsoft Agent Framework integration (Magentic)
  - SearchAgent, JudgeAgent, ReportAgent coordination
  - Pydantic AI structured outputs
  - LangGraph workflow state management (experimental)

- **Dual-Backend LLM Support**
  - Free tier: HuggingFace Inference API (Qwen 2.5 7B)
  - Paid tier: OpenAI GPT-5 (auto-detected with API key)
  - Factory pattern for backend selection

- **Evidence Processing**
  - Cross-source deduplication by PMID/DOI
  - ChromaDB + Sentence-Transformers for embeddings
  - LlamaIndex RAG support (premium tier)
  - Citation validation and formatting

- **User Interface**
  - Gradio streaming UI
  - MCP (Model Context Protocol) server integration
  - Claude Desktop tool support

- **Developer Experience**
  - Makefile with common commands
  - Pre-commit hooks (ruff, mypy)
  - Comprehensive test suite (unit, integration, e2e)
  - GitHub Actions CI/CD pipeline
  - Docker support with model pre-loading

- **Documentation**
  - README with quick start guide
  - CLAUDE.md/AGENTS.md for AI agent guidance
  - Architecture documentation with Mermaid diagrams
  - Example scripts for all major features

### Technical Notes

This release represents the completion of Phases 1-14 of the original development plan:

1. Foundation (project structure, TDD setup)
2. PubMed search implementation
3. ClinicalTrials.gov integration
4. Basic orchestrator loop
5. Evidence quality judgment
6. Report synthesis
7. Europe PMC integration
8. Evidence deduplication
9. Advanced search refinement
10. Hypothesis generation
11. Mechanistic pathway analysis
12. LangGraph workflow
13. Microsoft Agent Framework integration
14. Demo submission

### Known Issues

See `docs/technical-debt/` for documented technical debt and known issues.

---

## Release Notes Format

For each release, document:

### Added
New features and capabilities

### Changed
Changes to existing functionality

### Deprecated
Features that will be removed in future versions

### Removed
Features that were removed

### Fixed
Bug fixes

### Security
Security-related changes

---

[Unreleased]: https://github.com/The-Obstacle-Is-The-Way/DeepBoner/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/The-Obstacle-Is-The-Way/DeepBoner/releases/tag/v0.1.0
