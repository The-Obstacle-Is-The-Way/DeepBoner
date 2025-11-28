"""Writer agent for generating final reports from findings.

Converts the folder/writer_agent.py implementation to use Pydantic AI.
"""

from datetime import datetime
from typing import Any

import structlog
from pydantic_ai import Agent

from src.agent_factory.judges import get_model
from src.utils.exceptions import ConfigurationError

logger = structlog.get_logger()


# System prompt for the writer agent
SYSTEM_PROMPT = f"""
You are a senior researcher tasked with comprehensively answering a research query. 
Today's date is {datetime.now().strftime("%Y-%m-%d")}.
You will be provided with the original query along with research findings put together by a research assistant.
Your objective is to generate the final response in markdown format.
The response should be as lengthy and detailed as possible with the information provided, focusing on answering the original query.
In your final output, include references to the source URLs for all information and data gathered. 
This should be formatted in the form of a numbered square bracket next to the relevant information, 
followed by a list of URLs at the end of the response, per the example below.

EXAMPLE REFERENCE FORMAT:
The company has XYZ products [1]. It operates in the software services market which is expected to grow at 10% per year [2].

References:
[1] https://example.com/first-source-url
[2] https://example.com/second-source-url

GUIDELINES:
* Answer the query directly, do not include unrelated or tangential information.
* Adhere to any instructions on the length of your final response if provided in the user prompt.
* If any additional guidelines are provided in the user prompt, follow them exactly and give them precedence over these system instructions.
"""


class WriterAgent:
    """
    Agent that generates final reports from research findings.

    Uses Pydantic AI to generate markdown reports with citations.
    """

    def __init__(self, model: Any | None = None) -> None:
        """
        Initialize the writer agent.

        Args:
            model: Optional Pydantic AI model. If None, uses config default.
        """
        self.model = model or get_model()
        self.logger = logger

        # Initialize Pydantic AI Agent (no structured output - returns markdown text)
        self.agent = Agent(
            model=self.model,
            system_prompt=SYSTEM_PROMPT,
            retries=3,
        )

    async def write_report(
        self,
        query: str,
        findings: str,
        output_length: str = "",
        output_instructions: str = "",
    ) -> str:
        """
        Write a final report from findings.

        Args:
            query: The original research query
            findings: All findings collected during research
            output_length: Optional description of desired output length
            output_instructions: Optional additional instructions

        Returns:
            Markdown formatted report string

        Raises:
            ConfigurationError: If writing fails
        """
        # Input validation
        if not query or not query.strip():
            self.logger.warning("Empty query provided, using default")
            query = "Research query"

        if findings is None:
            self.logger.warning("None findings provided, using empty string")
            findings = "No findings available."

        # Truncate very long inputs to prevent context overflow
        max_findings_length = 50000  # ~12k tokens
        if len(findings) > max_findings_length:
            self.logger.warning(
                "Findings too long, truncating",
                original_length=len(findings),
                truncated_length=max_findings_length,
            )
            findings = findings[:max_findings_length] + "\n\n[Content truncated due to length]"

        self.logger.info("Writing final report", query=query[:100], findings_length=len(findings))

        length_str = (
            f"* The full response should be approximately {output_length}.\n"
            if output_length
            else ""
        )
        instructions_str = f"* {output_instructions}" if output_instructions else ""
        guidelines_str = (
            ("\n\nGUIDELINES:\n" + length_str + instructions_str).strip("\n")
            if length_str or instructions_str
            else ""
        )

        user_message = f"""
Provide a response based on the query and findings below with as much detail as possible. {guidelines_str}

QUERY: {query}

FINDINGS:
{findings}
"""

        # Retry logic for transient failures
        max_retries = 3
        last_exception: Exception | None = None

        for attempt in range(max_retries):
            try:
                # Run the agent
                result = await self.agent.run(user_message)
                report = result.output

                # Validate output
                if not report or not report.strip():
                    self.logger.warning("Empty report generated, using fallback")
                    raise ValueError("Empty report generated")

                self.logger.info("Report written", length=len(report), attempt=attempt + 1)

                return report

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
                    "Report writing failed", error=str(e), error_type=type(e).__name__
                )
                break

        # Return fallback report if all attempts failed
        self.logger.error(
            "Report writing failed after all attempts",
            error=str(last_exception) if last_exception else "Unknown error",
        )
        # Truncate findings in fallback if too long
        fallback_findings = findings[:500] + "..." if len(findings) > 500 else findings
        return (
            f"# Research Report\n\n"
            f"## Query\n{query}\n\n"
            f"## Findings\n{fallback_findings}\n\n"
            f"*Note: Report generation encountered an error. This is a fallback report.*"
        )


def create_writer_agent(model: Any | None = None) -> WriterAgent:
    """
    Factory function to create a writer agent.

    Args:
        model: Optional Pydantic AI model. If None, uses settings default.

    Returns:
        Configured WriterAgent instance

    Raises:
        ConfigurationError: If required API keys are missing
    """
    try:
        if model is None:
            model = get_model()

        return WriterAgent(model=model)

    except Exception as e:
        logger.error("Failed to create writer agent", error=str(e))
        raise ConfigurationError(f"Failed to create writer agent: {e}") from e
