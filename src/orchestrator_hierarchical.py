"""Hierarchical orchestrator with research teams."""

from collections.abc import AsyncGenerator
from typing import Any

import structlog

from src.agents.code_execution_agent import CodeExecutorAgent
from src.agents.magentic_agents import (
    create_report_agent,
    create_search_agent,
    create_sub_judge_agent,
)
from src.agents.retrieval_agent import RetrievalAgent
from src.middleware.sub_iteration import ResearchTeam
from src.state import init_magentic_state, reset_magentic_state
from src.utils.models import AgentEvent

logger = structlog.get_logger()


class HierarchicalOrchestrator:
    """Orchestrator that manages research teams."""

    def __init__(self, max_rounds: int = 10) -> None:
        self._max_rounds = max_rounds

    def _init_embedding_service(self) -> Any:
        try:
            from src.services.embeddings import get_embedding_service

            return get_embedding_service()
        except Exception as e:
            logger.warning("Embedding service unavailable", error=str(e))
            return None

    async def run(self, query: str) -> AsyncGenerator[AgentEvent, None]:
        """Run the hierarchical workflow."""
        logger.info("Starting Hierarchical orchestrator", query=query)

        reset_magentic_state()
        service = self._init_embedding_service()
        init_magentic_state(service)

        yield AgentEvent(
            type="started",
            message=f"Starting hierarchical research: {query}",
            iteration=0,
        )

        # Define Teams
        # Search Team: SearchAgent + RetrievalAgent (Context Maker)
        search_team = ResearchTeam(
            name="SearchTeam",
            agents=[create_search_agent(), RetrievalAgent()],
            judge=create_sub_judge_agent(),
            max_iterations=3,
        )

        # Analysis Team: CodeExecutorAgent
        analysis_team = ResearchTeam(
            name="AnalysisTeam",
            agents=[CodeExecutorAgent()],
            judge=create_sub_judge_agent(),
            max_iterations=3,
        )

        iteration = 0

        # Step 1: Search
        yield AgentEvent(
            type="judging",
            message="Manager: dispatching SearchTeam",
            iteration=iteration,
        )
        search_result = await search_team.run(query)
        yield AgentEvent(
            type="search_complete",
            message=f"SearchTeam finished:\n{search_result[:200]}...",
            iteration=iteration + 1,
        )

        # Step 2: Analysis
        iteration += 1
        yield AgentEvent(
            type="judging",
            message="Manager: dispatching AnalysisTeam",
            iteration=iteration,
        )
        analysis_result = await analysis_team.run(f"Analyze these findings:\n{search_result}")
        yield AgentEvent(
            type="hypothesizing",
            message=f"AnalysisTeam finished:\n{analysis_result[:200]}...",
            iteration=iteration + 1,
        )

        # Step 3: Report
        iteration += 1
        yield AgentEvent(
            type="judging",
            message="Manager: dispatching ReportAgent",
            iteration=iteration,
        )
        report_agent = create_report_agent()

        final_context = (
            f"Research Query: {query}\n\nSearch Results:\n{search_result}\n\n"
            f"Analysis Results:\n{analysis_result}"
        )
        response = await report_agent.run(f"Generate final report based on:\n{final_context}")

        report_text = response.messages[-1].text if response.messages else "No report."
        yield AgentEvent(
            type="complete",
            message=report_text,
            iteration=iteration + 1,
        )
