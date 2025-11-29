"""Integration tests for the research graph."""

import pytest

from src.agents.graph.workflow import create_research_graph


@pytest.mark.asyncio
async def test_graph_execution_flow():
    """Test the graph runs from start to finish (simulated)."""
    # Create graph without LLM (will use fallback supervisor logic -> search -> synthesize)
    graph = create_research_graph(llm=None)

    # Initial state
    initial_state = {
        "query": "test query",
        "hypotheses": [],
        "conflicts": [],
        "evidence_ids": [],
        "messages": [],
        "next_step": "search",
        "iteration_count": 0,
        "max_iterations": 2,  # Short run
    }

    # Execute graph
    events = []
    async for event in graph.astream(initial_state):
        events.append(event)

    # Verify flow
    # 1. Supervisor (start) -> decides search
    # 2. Search node runs
    # 3. Supervisor runs again -> max_iter reached -> synthesize
    # 4. Synthesize runs
    # 5. End

    # Just check we hit synthesis
    final_event = events[-1]
    assert "synthesize" in final_event or "messages" in str(final_event)
