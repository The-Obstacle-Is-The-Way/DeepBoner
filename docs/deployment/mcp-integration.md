# MCP Integration Guide

> **Last Updated**: 2025-12-06

This guide covers setting up DeepBoner's MCP (Model Context Protocol) server for integration with Claude Desktop and other MCP clients.

## Overview

DeepBoner exposes an MCP server via Gradio's built-in support. This allows Claude Desktop and other MCP-compatible clients to use DeepBoner's search tools directly.

## MCP Server URL

When DeepBoner is running:

```
http://localhost:7860/gradio_api/mcp/
```

On HuggingFace Spaces:
```
https://mcp-1st-birthday-deepboner.hf.space/gradio_api/mcp/
```

## Available Tools

| Tool | Description |
|------|-------------|
| `search_pubmed` | Search peer-reviewed biomedical literature |
| `search_clinical_trials` | Search ClinicalTrials.gov for active/completed trials |
| `search_europepmc` | Search Europe PMC preprints and papers |
| `search_all_sources` | Search all sources simultaneously with deduplication |

### Tool Signatures

```python
def search_pubmed(query: str, max_results: int = 10) -> list[Evidence]:
    """Search PubMed for biomedical literature."""

def search_clinical_trials(query: str, max_results: int = 10) -> list[Evidence]:
    """Search ClinicalTrials.gov."""

def search_europepmc(query: str, max_results: int = 10) -> list[Evidence]:
    """Search Europe PMC."""

def search_all_sources(query: str, max_results_per_source: int = 10) -> SearchResult:
    """Search all sources with cross-source deduplication."""
```

## Claude Desktop Setup

### 1. Start DeepBoner

```bash
uv run python src/app.py
```

### 2. Configure Claude Desktop

Edit your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add the MCP server:

```json
{
  "mcpServers": {
    "deepboner": {
      "url": "http://localhost:7860/gradio_api/mcp/"
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the new configuration.

### 4. Verify Connection

In Claude Desktop, you should see DeepBoner's tools available. Try:

```
Use the search_pubmed tool to find recent papers on testosterone therapy
```

## Using with HuggingFace Spaces

Point to the deployed Space:

```json
{
  "mcpServers": {
    "deepboner-cloud": {
      "url": "https://mcp-1st-birthday-deepboner.hf.space/gradio_api/mcp/"
    }
  }
}
```

Note: HuggingFace Spaces may sleep after inactivity. The first request will wake the Space (30-60 second delay).

## Tool Implementation

Tools are defined in `src/mcp_tools.py`:

```python
def search_pubmed(query: str, max_results: int = 10) -> list[Evidence]:
    """Search PubMed for biomedical literature.

    Args:
        query: Search query for PubMed
        max_results: Maximum number of results to return

    Returns:
        List of Evidence objects with citations
    """
    tool = PubMedTool()
    result = tool.search(query, max_results=max_results)
    return result.evidence
```

## Adding New Tools

To expose additional tools via MCP:

1. Add the function to `src/mcp_tools.py`:

```python
def search_openalex(query: str, max_results: int = 10) -> list[Evidence]:
    """Search OpenAlex for scholarly metadata."""
    tool = OpenAlexTool()
    result = tool.search(query, max_results=max_results)
    return result.evidence
```

2. Register in Gradio app (`src/app.py`):

The tools are automatically exposed via Gradio's MCP support when added to the interface.

## Troubleshooting

### Tools not appearing in Claude Desktop

1. Verify DeepBoner is running:
   ```bash
   curl http://localhost:7860/gradio_api/mcp/
   ```

2. Check config syntax:
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
   ```

3. Restart Claude Desktop

### Connection refused

- Check DeepBoner is running on port 7860
- Verify no firewall blocking
- Try accessing in browser: http://localhost:7860

### Slow responses

- First query loads ML models
- HuggingFace Space may need to wake up
- External APIs have rate limits

### Authentication errors

MCP server doesn't require authentication for local use. For production:
- Use API gateway
- Implement auth middleware

## Security Considerations

### Local Development

Local MCP server is accessible only from localhost by default.

### Production

For production deployments:

1. **Use HTTPS** - Enable TLS via reverse proxy
2. **Add authentication** - Consider API keys or OAuth
3. **Rate limit** - Prevent abuse
4. **Monitor** - Log tool usage

### Data Privacy

- Search queries are sent to external APIs (PubMed, etc.)
- Review external API privacy policies
- Don't expose sensitive research queries

## Protocol Details

### MCP Protocol Version

DeepBoner uses MCP protocol via Gradio 6.x integration.

### Request/Response Format

Requests follow the MCP specification:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_pubmed",
    "arguments": {
      "query": "testosterone therapy",
      "max_results": 10
    }
  },
  "id": 1
}
```

## Related Documentation

- [Docker Deployment](docker.md)
- [HuggingFace Spaces](huggingface-spaces.md)
- [Component Inventory](../architecture/component-inventory.md)
