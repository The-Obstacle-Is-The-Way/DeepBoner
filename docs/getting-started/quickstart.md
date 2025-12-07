# Quickstart Guide

Get DeepBoner running in 5 minutes.

## Prerequisites

- Python 3.11+ installed
- Repository cloned and dependencies installed (see [Installation](installation.md))

## 1. Start the Application

```bash
# From the repository root
uv run python src/app.py
```

You should see:
```
Running on local URL:  http://127.0.0.1:7860
```

## 2. Open the UI

Navigate to http://localhost:7860 in your browser.

You'll see a chat interface with:
- Input field for research questions
- Optional API key input (for premium features)
- Research results display

## 3. Ask Your First Question

Try one of these example queries:

```
What drugs improve female libido post-menopause?
```

```
Clinical trials for ED alternatives to PDE5 inhibitors?
```

```
Evidence for testosterone therapy in women with HSDD?
```

## 4. Understanding the Output

DeepBoner will:

1. **Search** multiple biomedical databases:
   - PubMed (peer-reviewed literature)
   - ClinicalTrials.gov (active/completed trials)
   - Europe PMC (preprints and papers)
   - OpenAlex (scholarly metadata)

2. **Judge** evidence quality using LLM

3. **Loop** if more evidence is needed

4. **Synthesize** a research report with citations

You'll see status updates as each phase completes.

## 5. Free vs Premium Mode

### Free Mode (No API Key)

- Uses HuggingFace Inference API
- Model: Qwen 2.5 7B Instruct
- Slower but fully functional

### Premium Mode (With OpenAI Key)

- Enter your OpenAI API key in the UI
- Uses GPT-5 for better synthesis
- Faster and more detailed reports

To use premium mode:
1. Get an API key from [OpenAI](https://platform.openai.com)
2. Enter it in the "OpenAI API Key" field
3. Your queries will automatically use GPT-5

## 6. Using MCP Tools

DeepBoner exposes MCP (Model Context Protocol) tools for integration with Claude Desktop and other clients.

### MCP Server URL
```
http://localhost:7860/gradio_api/mcp/
```

### Available Tools
- `search_pubmed` - Search peer-reviewed literature
- `search_clinical_trials` - Search clinical trials
- `search_europepmc` - Search Europe PMC
- `search_all_sources` - Search all sources with deduplication

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "deepboner": {
      "url": "http://localhost:7860/gradio_api/mcp/"
    }
  }
}
```

## Example Scripts

For programmatic usage, see the example scripts:

```bash
# Search demo
uv run python examples/search_demo/run_search.py

# Full orchestrator demo
uv run python examples/orchestrator_demo/run_agent.py

# Multi-agent demo (requires OpenAI key)
uv run python examples/orchestrator_demo/run_magentic.py
```

## Next Steps

- [Configuration Guide](configuration.md) - Customize settings
- [MCP Integration](../deployment/mcp-integration.md) - Set up Claude Desktop
- [Architecture Overview](../architecture/overview.md) - Understand how it works

## Troubleshooting

**Slow first response?**
- First query loads ML models (sentence-transformers)
- Subsequent queries are faster

**No results?**
- Check your internet connection
- External APIs may have rate limits

**Rate limit errors?**
- Add NCBI_API_KEY for higher PubMed limits
- Wait and retry

See [Troubleshooting](troubleshooting.md) for more help.
