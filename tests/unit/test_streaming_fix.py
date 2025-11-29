"""Test that streaming event handling is fixed (no token-by-token spam)."""

from unittest.mock import MagicMock

import pytest

from src.utils.models import AgentEvent


@pytest.mark.asyncio
async def test_streaming_events_are_buffered_not_spammed():
    """
    Verify that streaming events are buffered, not yielded individually.

    This test validates the fix for Bug 1: Token-by-Token Streaming Spam.
    Before the fix, each token would create a separate yield, resulting in O(N²) spam.
    After the fix, streaming tokens are buffered and only yielded once.
    """
    # Import here to avoid circular dependencies
    from src.app import research_agent

    # Mock orchestrator
    mock_orchestrator = MagicMock()

    # Simulate streaming events (like LLM token-by-token output)
    streaming_events = [
        AgentEvent(type="started", message="Starting research", iteration=0),
        AgentEvent(type="streaming", message="This", iteration=1),
        AgentEvent(type="streaming", message=" is", iteration=1),
        AgentEvent(type="streaming", message=" a", iteration=1),
        AgentEvent(type="streaming", message=" test", iteration=1),
        AgentEvent(type="complete", message="Final answer: This is a test", iteration=1),
    ]

    # Create async generator that yields events
    async def mock_run(query):
        for event in streaming_events:
            yield event

    mock_orchestrator.run = mock_run

    # Mock configure_orchestrator to return our mock
    import src.app as app_module

    original_configure = app_module.configure_orchestrator
    app_module.configure_orchestrator = MagicMock(return_value=(mock_orchestrator, "Test Backend"))

    try:
        # Run the research agent
        results = []
        async for result in research_agent("test query", [], mode="simple", api_key=""):
            results.append(result)

        # Verify that we don't have individual streaming events in the output
        # Before fix: Would see "📡 **STREAMING**: This", "📡 **STREAMING**: is", etc.
        # After fix: Should see buffered content only

        # Count how many times we see streaming markers
        streaming_count = sum(1 for r in results if "📡 **STREAMING**:" in r)

        # Should be at most 1 streaming message (buffered), not 4 (one per token)
        assert streaming_count <= 1, (
            f"Expected at most 1 buffered streaming message, got {streaming_count}. "
            f"This indicates token-by-token spam is still happening!"
        )

        # The final result should be the complete message
        assert any("Final answer" in r for r in results), "Missing final complete message"

    finally:
        # Restore original function
        app_module.configure_orchestrator = original_configure


@pytest.mark.asyncio
async def test_api_key_state_parameter_exists():
    """
    Verify that api_key_state parameter was added to research_agent.

    This validates the fix for Bug 2: API Key Persistence.
    """
    import inspect

    from src.app import research_agent

    # Get function signature
    sig = inspect.signature(research_agent)
    params = list(sig.parameters.keys())

    # Verify api_key_state parameter exists
    assert "api_key_state" in params, "api_key_state parameter missing from research_agent"

    # Verify it's after api_key
    api_key_idx = params.index("api_key")
    api_key_state_idx = params.index("api_key_state")
    assert api_key_state_idx > api_key_idx, "api_key_state should come after api_key"
