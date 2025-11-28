"""Long writer agent for iteratively writing report sections.

Converts the folder/long_writer_agent.py implementation to use Pydantic AI.
"""

import re
from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from src.agent_factory.judges import get_model
from src.utils.exceptions import ConfigurationError
from src.utils.models import ReportDraft

logger = structlog.get_logger()


# LongWriterOutput model for structured output
class LongWriterOutput(BaseModel):
    """Output from the long writer agent for a single section."""

    next_section_markdown: str = Field(
        description="The final draft of the next section in markdown format"
    )
    references: list[str] = Field(
        description="A list of URLs and their corresponding reference numbers for the section"
    )

    model_config = {"frozen": True}


# System prompt for the long writer agent
SYSTEM_PROMPT = f"""
You are an expert report writer tasked with iteratively writing each section of a report. 
Today's date is {datetime.now().strftime("%Y-%m-%d")}.
You will be provided with:
1. The original research query
2. A final draft of the report containing the table of contents and all sections written up until this point (in the first iteration there will be no sections written yet)
3. A first draft of the next section of the report to be written

OBJECTIVE:
1. Write a final draft of the next section of the report with numbered citations in square brackets in the body of the report
2. Produce a list of references to be appended to the end of the report

CITATIONS/REFERENCES:
The citations should be in numerical order, written in numbered square brackets in the body of the report.
Separately, a list of all URLs and their corresponding reference numbers will be included at the end of the report.
Follow the example below for formatting.

LongWriterOutput(
    next_section_markdown="The company specializes in IT consulting [1]. It operates in the software services market which is expected to grow at 10% per year [2].",
    references=["[1] https://example.com/first-source-url", "[2] https://example.com/second-source-url"]
)

GUIDELINES:
- You can reformat and reorganize the flow of the content and headings within a section to flow logically, but DO NOT remove details that were included in the first draft
- Only remove text from the first draft if it is already mentioned earlier in the report, or if it should be covered in a later section per the table of contents
- Ensure the heading for the section matches the table of contents
- Format the final output and references section as markdown
- Do not include a title for the reference section, just a list of numbered references

Only output JSON. Follow the JSON schema for LongWriterOutput. Do not output anything else.
"""


class LongWriterAgent:
    """
    Agent that iteratively writes report sections with proper citations.

    Uses Pydantic AI to generate structured LongWriterOutput for each section.
    """

    def __init__(self, model: Any | None = None) -> None:
        """
        Initialize the long writer agent.

        Args:
            model: Optional Pydantic AI model. If None, uses config default.
        """
        self.model = model or get_model()
        self.logger = logger

        # Initialize Pydantic AI Agent
        self.agent = Agent(
            model=self.model,
            output_type=LongWriterOutput,
            system_prompt=SYSTEM_PROMPT,
            retries=3,
        )

    async def write_next_section(
        self,
        original_query: str,
        report_draft: str,
        next_section_title: str,
        next_section_draft: str,
    ) -> LongWriterOutput:
        """
        Write the next section of the report.

        Args:
            original_query: The original research query
            report_draft: Current report draft (all sections written so far)
            next_section_title: Title of the section to write
            next_section_draft: Draft content for the next section

        Returns:
            LongWriterOutput with formatted section and references

        Raises:
            ConfigurationError: If writing fails
        """
        # Input validation
        if not original_query or not original_query.strip():
            self.logger.warning("Empty query provided, using default")
            original_query = "Research query"

        if not next_section_title or not next_section_title.strip():
            self.logger.warning("Empty section title provided, using default")
            next_section_title = "Section"

        if next_section_draft is None:
            next_section_draft = ""

        if report_draft is None:
            report_draft = ""

        # Truncate very long inputs
        max_draft_length = 30000
        if len(report_draft) > max_draft_length:
            self.logger.warning(
                "Report draft too long, truncating",
                original_length=len(report_draft),
            )
            report_draft = report_draft[:max_draft_length] + "\n\n[Content truncated]"

        if len(next_section_draft) > max_draft_length:
            self.logger.warning(
                "Section draft too long, truncating",
                original_length=len(next_section_draft),
            )
            next_section_draft = next_section_draft[:max_draft_length] + "\n\n[Content truncated]"

        self.logger.info(
            "Writing next section",
            section_title=next_section_title,
            query=original_query[:100],
        )

        user_message = f"""
<ORIGINAL QUERY>
{original_query}
</ORIGINAL QUERY>

<CURRENT REPORT DRAFT>
{report_draft or "No draft yet"}
</CURRENT REPORT DRAFT>

<TITLE OF NEXT SECTION TO WRITE>
{next_section_title}
</TITLE OF NEXT SECTION TO WRITE>

<DRAFT OF NEXT SECTION>
{next_section_draft}
</DRAFT OF NEXT SECTION>
"""

        # Retry logic for transient failures
        max_retries = 3
        last_exception: Exception | None = None

        for attempt in range(max_retries):
            try:
                # Run the agent
                result = await self.agent.run(user_message)
                output = result.output

                # Validate output
                if not output or not isinstance(output, LongWriterOutput):
                    raise ValueError("Invalid output format")

                if not output.next_section_markdown or not output.next_section_markdown.strip():
                    self.logger.warning("Empty section generated, using fallback")
                    raise ValueError("Empty section generated")

                self.logger.info(
                    "Section written",
                    section_title=next_section_title,
                    references_count=len(output.references),
                    attempt=attempt + 1,
                )

                return output

            except (TimeoutError, ConnectionError) as e:
                # Transient errors - retry
                last_exception = e
                if attempt < max_retries - 1:
                    self.logger.warning(
                        "Transient error, retrying",
                        error=str(e),
                        attempt=attempt + 1,
                        max_retries=max_retries,
                    )
                    continue
                else:
                    self.logger.error("Max retries exceeded for transient error", error=str(e))
                    break

            except Exception as e:
                # Non-transient errors - don't retry
                last_exception = e
                self.logger.error(
                    "Section writing failed",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                break

        # Return fallback section if all attempts failed
        self.logger.error(
            "Section writing failed after all attempts",
            error=str(last_exception) if last_exception else "Unknown error",
        )
        return LongWriterOutput(
            next_section_markdown=f"## {next_section_title}\n\n{next_section_draft}",
            references=[],
        )

    async def write_report(
        self,
        original_query: str,
        report_title: str,
        report_draft: ReportDraft,
    ) -> str:
        """
        Write the final report by iteratively writing each section.

        Args:
            original_query: The original research query
            report_title: Title of the report
            report_draft: ReportDraft with all sections

        Returns:
            Complete markdown report string

        Raises:
            ConfigurationError: If writing fails
        """
        # Input validation
        if not original_query or not original_query.strip():
            self.logger.warning("Empty query provided, using default")
            original_query = "Research query"

        if not report_title or not report_title.strip():
            self.logger.warning("Empty report title provided, using default")
            report_title = "Research Report"

        if not report_draft or not report_draft.sections:
            self.logger.warning("Empty report draft provided, returning minimal report")
            return f"# {report_title}\n\n## Query\n{original_query}\n\n*No sections available.*"

        self.logger.info(
            "Writing full report",
            report_title=report_title,
            sections_count=len(report_draft.sections),
        )

        # Initialize the final draft with title and table of contents
        final_draft = (
            f"# {report_title}\n\n## Table of Contents\n\n"
            + "\n".join(
                [
                    f"{i + 1}. {section.section_title}"
                    for i, section in enumerate(report_draft.sections)
                ]
            )
            + "\n\n"
        )
        all_references: list[str] = []

        for section in report_draft.sections:
            # Write each section
            next_section_output = await self.write_next_section(
                original_query,
                final_draft,
                section.section_title,
                section.section_content,
            )

            # Reformat references and update section markdown
            section_markdown, all_references = self._reformat_references(
                next_section_output.next_section_markdown,
                next_section_output.references,
                all_references,
            )

            # Reformat section headings
            section_markdown = self._reformat_section_headings(section_markdown)

            # Add to final draft
            final_draft += section_markdown + "\n\n"

        # Add final references
        final_draft += "## References:\n\n" + "  \n".join(all_references)

        self.logger.info("Full report written", length=len(final_draft))

        return final_draft

    def _reformat_references(
        self,
        section_markdown: str,
        section_references: list[str],
        all_references: list[str],
    ) -> tuple[str, list[str]]:
        """
        Reformat references: re-number, de-duplicate, and update markdown.

        Args:
            section_markdown: Markdown content with inline references [1], [2]
            section_references: List of references for this section
            all_references: Accumulated references from previous sections

        Returns:
            Tuple of (updated markdown, updated all_references)
        """

        # Convert reference lists to maps (URL -> ref_num)
        def convert_ref_list_to_map(ref_list: list[str]) -> dict[str, int]:
            ref_map: dict[str, int] = {}
            for ref in ref_list:
                try:
                    # Parse "[1] https://example.com" format
                    parts = ref.split("]", 1)
                    if len(parts) == 2:
                        ref_num = int(parts[0].strip("["))
                        url = parts[1].strip()
                        ref_map[url] = ref_num
                except (ValueError, IndexError):
                    logger.warning("Invalid reference format", ref=ref)
                    continue
            return ref_map

        section_ref_map = convert_ref_list_to_map(section_references)
        report_ref_map = convert_ref_list_to_map(all_references)
        section_to_report_ref_map: dict[int, int] = {}

        report_urls = set(report_ref_map.keys())
        ref_count = max(report_ref_map.values() or [0])

        # Map section references to report references
        for url, section_ref_num in section_ref_map.items():
            if url in report_urls:
                # URL already exists - reuse its reference number
                section_to_report_ref_map[section_ref_num] = report_ref_map[url]
            else:
                # New URL - assign next reference number
                ref_count += 1
                section_to_report_ref_map[section_ref_num] = ref_count
                all_references.append(f"[{ref_count}] {url}")

        # Replace reference numbers in markdown
        def replace_reference(match: re.Match[str]) -> str:
            ref_num = int(match.group(1))
            mapped_ref_num = section_to_report_ref_map.get(ref_num)
            if mapped_ref_num:
                return f"[{mapped_ref_num}]"
            return ""

        updated_markdown = re.sub(r"\[(\d+)\]", replace_reference, section_markdown)

        return updated_markdown, all_references

    def _reformat_section_headings(self, section_markdown: str) -> str:
        """
        Reformat section headings to be consistent (level-2 for main heading).

        Args:
            section_markdown: Markdown content with headings

        Returns:
            Updated markdown with adjusted heading levels
        """
        if not section_markdown.strip():
            return section_markdown

        # Find first heading level
        first_heading_match = re.search(r"^(#+)\s", section_markdown, re.MULTILINE)
        if not first_heading_match:
            return section_markdown

        # Calculate level adjustment needed (target is level 2)
        first_heading_level = len(first_heading_match.group(1))
        level_adjustment = 2 - first_heading_level

        def adjust_heading_level(match: re.Match[str]) -> str:
            hashes = match.group(1)
            content = match.group(2)
            new_level = max(2, len(hashes) + level_adjustment)
            return "#" * new_level + " " + content

        # Apply heading adjustment
        return re.sub(r"^(#+)\s(.+)$", adjust_heading_level, section_markdown, flags=re.MULTILINE)


def create_long_writer_agent(model: Any | None = None) -> LongWriterAgent:
    """
    Factory function to create a long writer agent.

    Args:
        model: Optional Pydantic AI model. If None, uses settings default.

    Returns:
        Configured LongWriterAgent instance

    Raises:
        ConfigurationError: If required API keys are missing
    """
    try:
        if model is None:
            model = get_model()

        return LongWriterAgent(model=model)

    except Exception as e:
        logger.error("Failed to create long writer agent", error=str(e))
        raise ConfigurationError(f"Failed to create long writer agent: {e}") from e
