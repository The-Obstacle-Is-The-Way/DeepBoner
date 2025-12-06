"""
Test the Accumulator Pattern for Microsoft Agent Framework event handling.

This tests SPEC-17 (updated for SPEC-18): We use AgentRunUpdateEvent.data.text as the
sole source of streaming content, and ExecutorCompletedEvent as a completion signal.

Event mapping (SPEC-18 migration):
- MagenticAgentDeltaEvent → AgentRunUpdateEvent
- MagenticAgentMessageEvent → ExecutorCompletedEvent
- MagenticFinalResultEvent → WorkflowOutputEvent
"""

import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# --- Create real event classes ---
class MockAgentRunUpdateEvent:
    """Simulates AgentRunUpdateEvent with streaming data."""

    def __init__(self, text: str, author_name: str = "TestAgent"):
        self.data = MagicMock()
        self.data.text = text
        self.data.author_name = author_name


class MockExecutorCompletedEvent:
    """Simulates ExecutorCompletedEvent signaling agent turn completion."""

    def __init__(self, executor_id: str = "TestAgent"):
        self.executor_id = executor_id


class MockWorkflowOutputEvent:
    """Simulates WorkflowOutputEvent."""

    def __init__(self, data=None):
        self.data = data


class MockOrchestratorMessageEvent:
    """Simulates orchestrator message event (formerly MagenticOrchestratorMessageEvent)."""

    def __init__(self, kind: str = "user_task", message: str = "test"):
        from agent_framework import MAGENTIC_EVENT_TYPE_ORCHESTRATOR

        self.type = MAGENTIC_EVENT_TYPE_ORCHESTRATOR
        self.kind = kind
        self.message = MagicMock()
        self.message.text = message


# Pass-through decorators
def mock_use_function_invocation(func=None):
    return func if func else lambda f: f


def mock_use_observability(func=None):
    return func if func else lambda f: f


@pytest.fixture
def mock_agent_framework():
    """
    Mock the agent_framework module structure in sys.modules.
    """
    # Create the mock module structure
    mock_af = types.ModuleType("agent_framework")
    mock_af_openai = types.ModuleType("agent_framework.openai")
    mock_af_middleware = types.ModuleType("agent_framework._middleware")
    mock_af_tools = types.ModuleType("agent_framework._tools")
    mock_af_types = types.ModuleType("agent_framework._types")
    mock_af_observability = types.ModuleType("agent_framework.observability")

    # Populate submodules
    mock_af.openai = mock_af_openai
    mock_af._middleware = mock_af_middleware
    mock_af._tools = mock_af_tools
    mock_af._types = mock_af_types
    mock_af.observability = mock_af_observability

    # Assign our REAL event classes as the module-level types
    mock_af.AgentRunUpdateEvent = MockAgentRunUpdateEvent
    mock_af.ExecutorCompletedEvent = MockExecutorCompletedEvent
    mock_af.WorkflowOutputEvent = MockWorkflowOutputEvent
    mock_af.MagenticOrchestratorMessageEvent = MockOrchestratorMessageEvent
    mock_af.AgentRunResponse = MagicMock
    mock_af.MAGENTIC_EVENT_TYPE_ORCHESTRATOR = "orchestrator_message"
    # P2 Fix: Add constants for metadata filtering
    mock_af.ORCH_MSG_KIND_INSTRUCTION = "instruction"
    mock_af.ORCH_MSG_KIND_TASK_LEDGER = "task_ledger"

    # Mock other classes
    mock_af.MagenticBuilder = MagicMock
    mock_af.ChatAgent = MagicMock
    mock_af.ai_function = MagicMock
    mock_af.BaseChatClient = MagicMock
    mock_af.ToolProtocol = MagicMock
    mock_af.ChatMessage = MagicMock
    mock_af.ChatResponse = MagicMock
    mock_af.ChatResponseUpdate = MagicMock
    mock_af.ChatOptions = MagicMock
    mock_af.FinishReason = MagicMock
    mock_af.Role = MagicMock

    # Populate symbols in submodules
    mock_af_openai.OpenAIChatClient = MagicMock
    mock_af_middleware.use_chat_middleware = MagicMock
    mock_af_tools.use_function_invocation = mock_use_function_invocation
    mock_af_types.FunctionCallContent = MagicMock
    mock_af_types.FunctionResultContent = MagicMock
    mock_af_observability.use_observability = mock_use_observability

    # Patch sys.modules to include our mocks
    with patch.dict(
        sys.modules,
        {
            "agent_framework": mock_af,
            "agent_framework.openai": mock_af_openai,
            "agent_framework._middleware": mock_af_middleware,
            "agent_framework._tools": mock_af_tools,
            "agent_framework._types": mock_af_types,
            "agent_framework.observability": mock_af_observability,
        },
    ):
        yield mock_af


@pytest.fixture(scope="module", autouse=True)
def cleanup_orchestrator_module():
    """
    Ensure src.orchestrators.advanced is restored to a clean state after tests.
    This prevents 'Mock' classes from leaking into other tests via module globals.
    """
    yield
    # After all tests in this module, reload the orchestrator module
    # This will use the REAL agent_framework (since the mock fixture is teardown)
    import src.orchestrators.advanced

    importlib.reload(src.orchestrators.advanced)


@pytest.fixture
def mock_orchestrator(mock_agent_framework):
    """
    Create an AdvancedOrchestrator with all dependencies mocked.
    Relies on reloading the module to pick up the mocked agent_framework.
    """
    # Import locally
    import src.orchestrators.advanced

    # RELOAD to ensure it picks up the mocked agent_framework from sys.modules
    importlib.reload(src.orchestrators.advanced)

    from src.orchestrators.advanced import AdvancedOrchestrator

    with (
        patch("src.orchestrators.advanced.get_chat_client"),
        patch("src.orchestrators.advanced.get_embedding_service_if_available", return_value=None),
        patch("src.orchestrators.advanced.init_magentic_state"),
        patch("src.agents.state.ResearchMemory"),
        patch("src.utils.service_loader.get_embedding_service", return_value=MagicMock()),
    ):
        orch = AdvancedOrchestrator(max_rounds=5)
        yield orch


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accumulator_pattern_scenario_a_standard_text(mock_orchestrator):
    """
    Scenario A: Standard Text Message (P2 Fix)
    Input: Updates ("Hello", " World") -> Completed
    Expected: Streaming events for text, NO completion events (P2 fix silences them)
    """
    # Use "searcher" to map to "SearchAgent"
    events = [
        MockAgentRunUpdateEvent("Hello", author_name="searcher"),
        MockAgentRunUpdateEvent(" World", author_name="searcher"),
        MockExecutorCompletedEvent(executor_id="searcher"),
    ]

    async def mock_stream(*args, **kwargs):
        for event in events:
            yield event

    mock_workflow = MagicMock()
    mock_workflow.run_stream = mock_stream

    with patch.object(mock_orchestrator, "_build_workflow", return_value=mock_workflow):
        generated_events = []
        async for event in mock_orchestrator.run("test query"):
            generated_events.append(event)

    # P2 FIX: ExecutorCompletedEvent is SILENCED - no non-streaming agent events
    # We should have STREAMING events from AgentRunUpdateEvent
    streaming_events = [e for e in generated_events if e.type == "streaming"]
    assert len(streaming_events) >= 1, (
        f"Expected streaming events, got: {[e.type for e in generated_events]}"
    )

    # P2 FIX: No "SearchAgent" completion events should exist (silenced)
    completion_events = [
        e
        for e in generated_events
        if "SearchAgent" in str(e.message)
        and e.type not in ("streaming", "started", "progress", "thinking")
    ]
    assert len(completion_events) == 0, (
        f"P2 Fix: Should NOT emit completion events, got: {[e.message for e in completion_events]}"
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accumulator_pattern_scenario_b_tool_call(mock_orchestrator):
    """
    Scenario B: Tool Call (No Text Deltas) - P2 Fix
    Input: No Deltas -> Completed
    Expected: NO completion events (P2 fix silences ExecutorCompletedEvent)
    """
    # Use "searcher" to map to "SearchAgent"
    events = [
        MockExecutorCompletedEvent(executor_id="searcher"),
    ]

    async def mock_stream(*args, **kwargs):
        for event in events:
            yield event

    mock_workflow = MagicMock()
    mock_workflow.run_stream = mock_stream

    with patch.object(mock_orchestrator, "_build_workflow", return_value=mock_workflow):
        generated_events = []
        async for event in mock_orchestrator.run("test query"):
            generated_events.append(event)

    # P2 FIX: ExecutorCompletedEvent is SILENCED - no agent completion events
    search_events = [
        e
        for e in generated_events
        if "SearchAgent" in str(e.message)
        and e.type not in ("streaming", "started", "progress", "thinking")
    ]

    # P2 Fix: Should have NO completion events (they are silenced)
    assert len(search_events) == 0, (
        f"P2 Fix: Should NOT emit completion events, got: {[e.message for e in search_events]}"
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_accumulator_pattern_buffer_clearing(mock_orchestrator):
    """
    Verify buffer clears between agents (P2 Fix).
    P2 Fix: ExecutorCompletedEvent is silenced, so we verify via streaming events.
    Agent B's streaming should NOT contain Agent A's text.
    """
    # Use "searcher" (SearchAgent) and "judge" (JudgeAgent)
    events = [
        MockAgentRunUpdateEvent("Searcher says hi", author_name="searcher"),
        MockExecutorCompletedEvent(executor_id="searcher"),
        MockAgentRunUpdateEvent("Judge responds", author_name="judge"),
        MockExecutorCompletedEvent(executor_id="judge"),
    ]

    async def mock_stream(*args, **kwargs):
        for event in events:
            yield event

    mock_workflow = MagicMock()
    mock_workflow.run_stream = mock_stream

    with patch.object(mock_orchestrator, "_build_workflow", return_value=mock_workflow):
        generated_events = []
        async for event in mock_orchestrator.run("test query"):
            generated_events.append(event)

    # P2 FIX: ExecutorCompletedEvent is SILENCED
    # Verify via STREAMING events - each agent's stream is separate
    streaming_events = [e for e in generated_events if e.type == "streaming"]

    # Should have streaming events from both agents
    assert len(streaming_events) >= 2, (
        f"Expected streaming events, got: {[e.type for e in generated_events]}"
    )

    # Verify content separation - each streaming event has its own content
    searcher_streams = [e for e in streaming_events if "Searcher" in e.message]
    judge_streams = [e for e in streaming_events if "Judge" in e.message]

    assert len(searcher_streams) >= 1, "Missing searcher streaming events"
    assert len(judge_streams) >= 1, "Missing judge streaming events"

    # Buffer isolation: Judge stream should NOT contain Searcher text
    for judge_event in judge_streams:
        assert "Searcher" not in judge_event.message, "Buffer not cleared between agents!"
