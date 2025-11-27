"""Tests for new agents."""

from unittest.mock import patch

import pytest
from agent_framework import ChatMessage, Role

from src.agents.code_execution_agent import CodeExecutorAgent
from src.agents.retrieval_agent import RetrievalAgent
from src.state import init_magentic_state
from src.utils.models import Citation, Evidence


@pytest.fixture
def mock_executor():
    with patch("src.agents.code_execution_agent.get_code_executor") as mock:
        yield mock.return_value


@pytest.mark.asyncio
async def test_code_executor_agent(mock_executor):
    mock_executor.execute.return_value = {
        "success": True,
        "stdout": "Output",
        "stderr": "",
        "error": None,
    }

    agent = CodeExecutorAgent()
    response = await agent.run("Run this: ```python print('hi') ```")

    assert "Execution Success" in response.messages[0].text
    assert "Output" in response.messages[0].text
    # Note: Regex extraction allows leading/trailing spaces
    args, _ = mock_executor.execute.call_args
    assert "print('hi')" in args[0]


@pytest.mark.asyncio
async def test_retrieval_agent():
    state = init_magentic_state()
    state.add_evidence(
        [
            Evidence(
                content="C1",
                citation=Citation(
                    title="T1", url="u1", source="pubmed", date="d1", authors=[]
                ),
                relevance=1.0,
            )
        ]
    )

    agent = RetrievalAgent()
    response = await agent.run("Get context")

    assert "Current Context Summary" in response.messages[0].text
    assert "T1" in response.messages[0].text
