"""Tests for Hierarchical Orchestrator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.orchestrator_hierarchical import HierarchicalOrchestrator


@pytest.mark.asyncio
async def test_hierarchical_orchestrator_flow():
    with (
        patch("src.orchestrator_hierarchical.create_search_agent"),
        patch("src.orchestrator_hierarchical.RetrievalAgent"),
        patch("src.orchestrator_hierarchical.create_sub_judge_agent"),
        patch("src.orchestrator_hierarchical.CodeExecutorAgent"),
        patch("src.orchestrator_hierarchical.create_report_agent") as mock_create_report,
        patch("src.orchestrator_hierarchical.ResearchTeam") as MockTeam,
        patch("src.orchestrator_hierarchical.init_magentic_state"),
        patch("src.orchestrator_hierarchical.reset_magentic_state"),
    ):

        # Mock Teams running
        mock_team_instance = AsyncMock()
        MockTeam.return_value = mock_team_instance
        mock_team_instance.run.side_effect = ["Search Done", "Analysis Done"]

        # Mock Report Agent
        mock_report_agent = AsyncMock()
        mock_response = MagicMock()
        mock_response.messages = [MagicMock(text="Final Report")]
        mock_report_agent.run.return_value = mock_response
        mock_create_report.return_value = mock_report_agent

        orch = HierarchicalOrchestrator()
        events = []
        async for event in orch.run("query"):
            events.append(event)

        assert len(events) > 0
        assert events[-1].type == "complete"
        assert events[-1].message == "Final Report"

        # Verify team runs
        assert mock_team_instance.run.call_count == 2
