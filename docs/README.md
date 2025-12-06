# DeepBoner Documentation

Welcome to the DeepBoner documentation. This directory contains comprehensive documentation for developers, contributors, and operators.

## Quick Navigation

| Need to... | Go to... |
|------------|----------|
| Get started quickly | [Getting Started](getting-started/installation.md) |
| Understand the architecture | [Architecture Overview](architecture/overview.md) |
| Set up for development | [Development Guide](development/testing.md) |
| Deploy the application | [Deployment Guide](deployment/docker.md) |
| Look up configuration | [Reference](reference/configuration.md) |
| Track technical debt | [Technical Debt](technical-debt/index.md) |

## Documentation Structure

```
docs/
├── README.md                     # This file - documentation index
│
├── getting-started/              # Onboarding documentation
│   ├── installation.md           # Installation guide
│   ├── quickstart.md             # 5-minute quickstart
│   ├── configuration.md          # Configuration guide
│   └── troubleshooting.md        # Common issues and solutions
│
├── architecture/                 # System design documentation
│   ├── overview.md               # High-level architecture
│   ├── system-registry.md        # Service registry (canonical wiring)
│   ├── workflow-diagrams.md      # Visual workflow diagrams
│   ├── component-inventory.md    # Complete component catalog
│   ├── data-models.md            # Pydantic model documentation
│   └── exception-hierarchy.md    # Exception types and handling
│
├── development/                  # Developer guides
│   ├── testing.md                # Testing strategy and patterns
│   ├── code-style.md             # Code style and conventions
│   └── release-process.md        # Release workflow
│
├── deployment/                   # Deployment documentation
│   ├── docker.md                 # Docker deployment
│   ├── huggingface-spaces.md     # HuggingFace Spaces deployment
│   └── mcp-integration.md        # MCP server setup
│
├── technical-debt/               # Known issues and improvements
│   ├── index.md                  # Technical debt overview
│   └── debt-registry.md          # Itemized debt tracking
│
├── reference/                    # API and configuration reference
│   ├── configuration.md          # All configuration options
│   └── environment-variables.md  # Environment variable reference
│
├── bugs/                         # Bug tracking (existing)
│   ├── active-bugs.md
│   └── p3-progress-bar-positioning.md
│
├── decisions/                    # Architecture Decision Records (existing)
│   └── 2025-11-27-pr55-evaluation.md
│
└── future-roadmap/               # Future feature specs (existing)
    └── 16-pubmed-fulltext.md
```

## Documentation Standards

### File Naming
- Use **kebab-case** for all filenames (e.g., `getting-started.md`)
- Keep names descriptive but concise

### Content Guidelines
- Start each document with a clear title and purpose
- Include a table of contents for longer documents
- Use Mermaid diagrams for visual documentation
- Link to related documentation
- Keep content current - update when code changes

### Markdown Conventions
- Use ATX-style headers (`#`, `##`, etc.)
- Code blocks with language specification
- Tables for structured data
- Admonitions for warnings/notes (where supported)

## Key Documents

### For New Developers
1. [Installation](getting-started/installation.md) - Set up your environment
2. [Quickstart](getting-started/quickstart.md) - Run your first query
3. [Architecture Overview](architecture/overview.md) - Understand the system
4. [Testing](development/testing.md) - Run and write tests

### For Contributors
1. [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
2. [Code Style](development/code-style.md) - Style conventions
3. [Testing](development/testing.md) - Testing requirements

### For Operators
1. [Docker Deployment](deployment/docker.md) - Container deployment
2. [HuggingFace Spaces](deployment/huggingface-spaces.md) - Cloud deployment
3. [Configuration Reference](reference/configuration.md) - All options

### For Understanding the Codebase
1. [Component Inventory](architecture/component-inventory.md) - All modules
2. [Data Models](architecture/data-models.md) - Core types
3. [System Registry](architecture/system-registry.md) - Service wiring
4. [Technical Debt](technical-debt/index.md) - Known issues

## Related Documentation

- **[README.md](../README.md)** - Project overview and quick start
- **[CLAUDE.md](../CLAUDE.md)** - AI agent developer reference
- **[CHANGELOG.md](../CHANGELOG.md)** - Release history
- **[SECURITY.md](../SECURITY.md)** - Security policy
- **[CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)** - Community guidelines

## Contributing to Documentation

Documentation is code. Please:

1. Keep docs updated when changing related code
2. Follow the naming and style conventions
3. Test links before committing
4. Add new documents to this index

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full guidelines.

---

*"Well-documented boners only. We take evidence-based documentation very seriously."* 📚
