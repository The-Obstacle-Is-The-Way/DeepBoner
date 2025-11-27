"""Tests for sub-iteration middleware."""

from unittest.mock import AsyncMock

import pytest
from agent_framework import AgentRunResponse, ChatMessage, Role

from src.middleware.sub_iteration import ResearchTeam


@pytest.fixture
def mock_agent():
    agent = AsyncMock()
    agent.name = "MockAgent"
    # Mock response
    response = AgentRunResponse(
        messages=[ChatMessage(role=Role.ASSISTANT, text="I did something.")],
        response_id="1",
    )
    agent.run.return_value = response
    return agent


@pytest.fixture
def mock_judge():
    judge = AsyncMock()
    judge.name = "MockJudge"
    response = AgentRunResponse(
        messages=[ChatMessage(role=Role.ASSISTANT, text="SUFFICIENT")],
        response_id="j1",
    )
    judge.run.return_value = response
    return judge


@pytest.mark.asyncio
async def test_research_team_run(mock_agent, mock_judge):
    team = ResearchTeam(
        name="TestTeam",
        agents=[mock_agent],
        judge=mock_judge,
        max_iterations=2,
    )

    result = await team.run("Task")

    assert "Team TestTeam Output (SUFFICIENT)" in result
    assert "I did something" in result

    # Verify calls
    assert mock_agent.run.call_count >= 1
    assert mock_judge.run.call_count >= 1


@pytest.mark.asyncio
async def test_research_team_continue(mock_agent, mock_judge):
    # Judge says CONTINUE first then SUFFICIENT
    r1 = AgentRunResponse(
        messages=[ChatMessage(role=Role.ASSISTANT, text="CONTINUE")], response_id="j1"
    )
    r2 = AgentRunResponse(
        messages=[ChatMessage(role=Role.ASSISTANT, text="SUFFICIENT")], response_id="j2"
    )
    mock_judge.run.side_effect = [r1, r2]

    team = ResearchTeam(
        name="TestTeam", agents=[mock_agent], judge=mock_judge, max_iterations=3
    )

    await team.run("Task")

    assert mock_agent.run.call_count == 2
    assert mock_judge.run.call_count == 2
