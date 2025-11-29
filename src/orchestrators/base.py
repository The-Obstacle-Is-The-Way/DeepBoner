"""Base protocols and shared types for orchestrators.

This module defines the interfaces that orchestrators depend on,
following the Interface Segregation Principle (ISP) and
Dependency Inversion Principle (DIP).
"""

from typing import Protocol

from src.utils.models import Evidence, JudgeAssessment, SearchResult


class SearchHandlerProtocol(Protocol):
    """Protocol for search handler.

    Defines the interface for executing searches across biomedical databases.
    Implementations include SearchHandler (scatter-gather across PubMed,
    ClinicalTrials.gov, Europe PMC).
    """

    async def execute(self, query: str, max_results_per_tool: int = 10) -> SearchResult:
        """Execute a search query.

        Args:
            query: The search query string
            max_results_per_tool: Maximum results to fetch per search tool

        Returns:
            SearchResult containing evidence and metadata
        """
        ...


class JudgeHandlerProtocol(Protocol):
    """Protocol for judge handler.

    Defines the interface for assessing evidence quality and sufficiency.
    Implementations include JudgeHandler (pydantic-ai), HFInferenceJudgeHandler,
    and MockJudgeHandler.
    """

    async def assess(self, question: str, evidence: list[Evidence]) -> JudgeAssessment:
        """Assess whether collected evidence is sufficient.

        Args:
            question: The original research question
            evidence: List of evidence items to assess

        Returns:
            JudgeAssessment with sufficiency determination and next steps
        """
        ...
