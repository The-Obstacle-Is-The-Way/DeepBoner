# Reference Repositories

This directory contains reference implementations that inform our architecture. These repos are **git-ignored** and should be cloned locally.

## Clone Commands

```bash
cd reference_repos

# PydanticAI Research Agent (Brave Search + Agent patterns)
git clone --depth 1 https://github.com/coleam00/PydanticAI-Research-Agent.git pydanticai-research-agent
rm -rf pydanticai-research-agent/.git

# PubMed MCP Server (Production-grade, TypeScript)
git clone --depth 1 https://github.com/cyanheads/pubmed-mcp-server.git pubmed-mcp-server
rm -rf pubmed-mcp-server/.git

# Microsoft AutoGen (Multi-agent orchestration)
git clone --depth 1 https://github.com/microsoft/autogen.git autogen-microsoft
rm -rf autogen-microsoft/.git

# Claude Agent SDK (Anthropic's agent framework)
git clone --depth 1 https://github.com/anthropics/claude-agent-sdk-python.git claude-agent-sdk
rm -rf claude-agent-sdk/.git
```

## What Each Repo Provides

| Repository | Key Patterns | Reference In Docs |
|------------|--------------|-------------------|
| **pydanticai-research-agent** | @agent.tool decorator, Brave Search, dependency injection | Section 16 |
| **pubmed-mcp-server** | PubMed E-utilities, MCP server patterns, research agent | Section 16 |
| **autogen-microsoft** | Multi-agent orchestration, reflect_on_tool_use | Sections 14, 15 |
| **claude-agent-sdk** | @tool decorator, hooks system, in-process MCP | Sections 14, 15 |

## Quick Reference Files

### PydanticAI Research Agent
- `agents/research_agent.py` - Agent with @agent.tool pattern
- `tools/brave_search.py` - Brave Search implementation
- `models/research_models.py` - Pydantic models

### PubMed MCP Server
- `src/mcp-server/tools/pubmedSearchArticles/` - PubMed search
- `src/mcp-server/tools/pubmedResearchAgent/` - Research orchestrator
- `src/services/NCBI/` - NCBI E-utilities client

### AutoGen
- `python/packages/autogen-agentchat/` - Agent patterns
- `python/packages/autogen-core/` - Core abstractions

### Claude Agent SDK
- `src/claude_agent_sdk/client.py` - SDK client
- `examples/mcp_calculator.py` - @tool decorator example
