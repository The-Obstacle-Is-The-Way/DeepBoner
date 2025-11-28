# Writer Agents Usage Examples

This document provides examples of how to use the writer agents in DeepCritical for generating research reports.

## Overview

DeepCritical provides three writer agents for different report generation scenarios:

1. **WriterAgent** - Basic writer for simple reports from findings
2. **LongWriterAgent** - Iterative writer for long-form multi-section reports
3. **ProofreaderAgent** - Finalizes and polishes report drafts

## WriterAgent

The `WriterAgent` generates final reports from research findings. It's used in iterative research flows.

### Basic Usage

```python
from src.agent_factory.agents import create_writer_agent

# Create writer agent
writer = create_writer_agent()

# Generate report
query = "What is the capital of France?"
findings = """
Paris is the capital of France [1].
It is located in the north-central part of the country [2].

[1] https://example.com/france-info
[2] https://example.com/paris-info
"""

report = await writer.write_report(
    query=query,
    findings=findings,
)

print(report)
```

### With Output Length Specification

```python
report = await writer.write_report(
    query="Explain machine learning",
    findings=findings,
    output_length="500 words",
)
```

### With Additional Instructions

```python
report = await writer.write_report(
    query="Explain machine learning",
    findings=findings,
    output_length="A comprehensive overview",
    output_instructions="Use formal academic language and include examples",
)
```

### Integration with IterativeResearchFlow

The `WriterAgent` is automatically used by `IterativeResearchFlow`:

```python
from src.agent_factory.agents import create_iterative_flow

flow = create_iterative_flow(max_iterations=5, max_time_minutes=10)
report = await flow.run(
    query="What is quantum computing?",
    output_length="A detailed explanation",
    output_instructions="Include practical applications",
)
```

## LongWriterAgent

The `LongWriterAgent` iteratively writes report sections with proper citation management. It's used in deep research flows.

### Basic Usage

```python
from src.agent_factory.agents import create_long_writer_agent
from src.utils.models import ReportDraft, ReportDraftSection

# Create long writer agent
long_writer = create_long_writer_agent()

# Create report draft with sections
report_draft = ReportDraft(
    sections=[
        ReportDraftSection(
            section_title="Introduction",
            section_content="Draft content for introduction with [1].",
        ),
        ReportDraftSection(
            section_title="Methods",
            section_content="Draft content for methods with [2].",
        ),
        ReportDraftSection(
            section_title="Results",
            section_content="Draft content for results with [3].",
        ),
    ]
)

# Generate full report
report = await long_writer.write_report(
    original_query="What are the main features of Python?",
    report_title="Python Programming Language Overview",
    report_draft=report_draft,
)

print(report)
```

### Writing Individual Sections

You can also write sections one at a time:

```python
# Write first section
section_output = await long_writer.write_next_section(
    original_query="What is Python?",
    report_draft="",  # No existing draft
    next_section_title="Introduction",
    next_section_draft="Python is a programming language...",
)

print(section_output.next_section_markdown)
print(section_output.references)

# Write second section with existing draft
section_output = await long_writer.write_next_section(
    original_query="What is Python?",
    report_draft="# Report\n\n## Introduction\n\nContent...",
    next_section_title="Features",
    next_section_draft="Python features include...",
)
```

### Integration with DeepResearchFlow

The `LongWriterAgent` is automatically used by `DeepResearchFlow`:

```python
from src.agent_factory.agents import create_deep_flow

flow = create_deep_flow(
    max_iterations=5,
    max_time_minutes=10,
    use_long_writer=True,  # Use long writer (default)
)

report = await flow.run("What are the main features of Python programming language?")
```

## ProofreaderAgent

The `ProofreaderAgent` finalizes and polishes report drafts by removing duplicates, adding summaries, and refining wording.

### Basic Usage

```python
from src.agent_factory.agents import create_proofreader_agent
from src.utils.models import ReportDraft, ReportDraftSection

# Create proofreader agent
proofreader = create_proofreader_agent()

# Create report draft
report_draft = ReportDraft(
    sections=[
        ReportDraftSection(
            section_title="Introduction",
            section_content="Python is a programming language [1].",
        ),
        ReportDraftSection(
            section_title="Features",
            section_content="Python has many features [2].",
        ),
    ]
)

# Proofread and finalize
final_report = await proofreader.proofread(
    query="What is Python?",
    report_draft=report_draft,
)

print(final_report)
```

### Integration with DeepResearchFlow

Use `ProofreaderAgent` instead of `LongWriterAgent`:

```python
from src.agent_factory.agents import create_deep_flow

flow = create_deep_flow(
    max_iterations=5,
    max_time_minutes=10,
    use_long_writer=False,  # Use proofreader instead
)

report = await flow.run("What are the main features of Python?")
```

## Error Handling

All writer agents include robust error handling:

### Handling Empty Inputs

```python
# WriterAgent handles empty findings gracefully
report = await writer.write_report(
    query="Test query",
    findings="",  # Empty findings
)
# Returns a fallback report

# LongWriterAgent handles empty sections
report = await long_writer.write_report(
    original_query="Test",
    report_title="Test Report",
    report_draft=ReportDraft(sections=[]),  # Empty draft
)
# Returns minimal report

# ProofreaderAgent handles empty drafts
report = await proofreader.proofread(
    query="Test",
    report_draft=ReportDraft(sections=[]),
)
# Returns minimal report
```

### Retry Logic

All agents automatically retry on transient errors (timeouts, connection errors):

```python
# Automatically retries up to 3 times on transient failures
report = await writer.write_report(
    query="Test query",
    findings=findings,
)
```

### Fallback Reports

If all retries fail, agents return fallback reports:

```python
# Returns fallback report with query and findings
report = await writer.write_report(
    query="Test query",
    findings=findings,
)
# Fallback includes: "# Research Report\n\n## Query\n...\n\n## Findings\n..."
```

## Citation Validation

### For Markdown Reports

Use the markdown citation validator:

```python
from src.utils.citation_validator import validate_markdown_citations
from src.utils.models import Evidence, Citation

# Collect evidence during research
evidence = [
    Evidence(
        content="Paris is the capital of France",
        citation=Citation(
            source="web",
            title="France Information",
            url="https://example.com/france",
            date="2024-01-01",
        ),
    ),
]

# Generate report
report = await writer.write_report(query="What is the capital of France?", findings=findings)

# Validate citations
validated_report, removed_count = validate_markdown_citations(report, evidence)

if removed_count > 0:
    print(f"Removed {removed_count} invalid citations")
```

### For ResearchReport Objects

Use the structured citation validator:

```python
from src.utils.citation_validator import validate_references

# For ResearchReport objects (from ReportAgent)
validated_report = validate_references(report, evidence)
```

## Custom Model Configuration

All writer agents support custom model configuration:

```python
from pydantic_ai import Model

# Create custom model
custom_model = Model("openai", "gpt-4")

# Use with writer agents
writer = create_writer_agent(model=custom_model)
long_writer = create_long_writer_agent(model=custom_model)
proofreader = create_proofreader_agent(model=custom_model)
```

## Best Practices

1. **Use WriterAgent for simple reports** - When you have findings as a string and need a quick report
2. **Use LongWriterAgent for structured reports** - When you need multiple sections with proper citation management
3. **Use ProofreaderAgent for final polish** - When you have draft sections and need a polished final report
4. **Validate citations** - Always validate citations against collected evidence
5. **Handle errors gracefully** - All agents return fallback reports on failure
6. **Specify output length** - Use `output_length` parameter to control report size
7. **Provide instructions** - Use `output_instructions` for specific formatting requirements

## Integration Examples

### Full Iterative Research Flow

```python
from src.agent_factory.agents import create_iterative_flow

flow = create_iterative_flow(
    max_iterations=5,
    max_time_minutes=10,
)

report = await flow.run(
    query="What is machine learning?",
    output_length="A comprehensive 1000-word explanation",
    output_instructions="Include practical examples and use cases",
)
```

### Full Deep Research Flow with Long Writer

```python
from src.agent_factory.agents import create_deep_flow

flow = create_deep_flow(
    max_iterations=5,
    max_time_minutes=10,
    use_long_writer=True,
)

report = await flow.run("What are the main features of Python programming language?")
```

### Full Deep Research Flow with Proofreader

```python
from src.agent_factory.agents import create_deep_flow

flow = create_deep_flow(
    max_iterations=5,
    max_time_minutes=10,
    use_long_writer=False,  # Use proofreader
)

report = await flow.run("Explain quantum computing basics")
```

## Troubleshooting

### Empty Reports

If you get empty reports, check:
- Input validation logs (agents log warnings for empty inputs)
- LLM API key configuration
- Network connectivity

### Citation Issues

If citations are missing or invalid:
- Use `validate_markdown_citations()` to check citations
- Ensure Evidence objects are properly collected during research
- Check that URLs in findings match Evidence URLs

### Performance Issues

For large reports:
- Use `LongWriterAgent` for better section management
- Consider truncating very long findings (agents do this automatically)
- Use appropriate `max_time_minutes` settings

## See Also

- [Research Flows Documentation](../orchestrator/research_flows.md)
- [Citation Validation](../utils/citation_validation.md)
- [Agent Factory](../agent_factory/agents.md)













