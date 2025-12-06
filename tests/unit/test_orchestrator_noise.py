from unittest.mock import MagicMock

import pytest
from agent_framework import (
    MAGENTIC_EVENT_TYPE_ORCHESTRATOR,
    ORCH_MSG_KIND_INSTRUCTION,
    ORCH_MSG_KIND_TASK_LEDGER,
    AgentRunUpdateEvent,
    ExecutorCompletedEvent,
)

from src.orchestrators.advanced import REPORTER_AGENT_ID, AdvancedOrchestrator


async def _empty_async_generator(query):
    """Empty async generator for mocking _init_workflow_events."""
    return
    yield  # Makes this an async generator that yields nothing


@pytest.mark.unit
@pytest.mark.asyncio
async def test_executor_completed_event_is_silenced():
    """Verify ExecutorCompletedEvent produces NO UI events."""
    orchestrator = AdvancedOrchestrator()

    # Mock the workflow build to return our custom event stream
    mock_workflow = MagicMock()

    # Create a stream of events: Start -> ExecutorCompleted -> End
    async def event_stream(task):
        # 1. Completion event (should be ignored)
        yield ExecutorCompletedEvent(executor_id="ManagerAgent", data=None)
        # 2. Reporter completion (should set flag but yield nothing)
        yield ExecutorCompletedEvent(executor_id=REPORTER_AGENT_ID, data=None)

    mock_workflow.run_stream = event_stream
    orchestrator._build_workflow = MagicMock(return_value=mock_workflow)

    # Mock init services to avoid side effects
    orchestrator._init_workflow_events = _empty_async_generator
    orchestrator._init_embedding_service = MagicMock(return_value=None)
    orchestrator._create_task_prompt = MagicMock(return_value="task")

    events = []
    async for event in orchestrator.run("query"):
        events.append(event)

    # Assertions
    # We should have NO "progress" events with "task completed" message
    for event in events:
        if event.type == "progress":
            assert "task completed" not in event.message
        # We should have NO "judging" events from the manager completion
        if event.type == "judging":
            assert "ManagerAgent" not in event.message


@pytest.mark.unit
@pytest.mark.asyncio
async def test_internal_messages_are_filtered():
    """Verify internal task_ledger/instruction messages are filtered."""
    orchestrator = AdvancedOrchestrator()
    mock_workflow = MagicMock()

    async def event_stream(task):
        # 1. Task Ledger (Should be skipped)
        ledger_update = AgentRunUpdateEvent(executor_id="Manager", data=MagicMock())
        ledger_update.data.text = '{"some": "json"}'
        ledger_update.data.additional_properties = {
            "magentic_event_type": MAGENTIC_EVENT_TYPE_ORCHESTRATOR,
            "orchestrator_message_kind": ORCH_MSG_KIND_TASK_LEDGER,
        }
        yield ledger_update

        # 2. Instruction (Should be skipped)
        instruction = AgentRunUpdateEvent(executor_id="Manager", data=MagicMock())
        instruction.data.text = "Internal instruction to agent"
        instruction.data.additional_properties = {
            "magentic_event_type": MAGENTIC_EVENT_TYPE_ORCHESTRATOR,
            "orchestrator_message_kind": ORCH_MSG_KIND_INSTRUCTION,
        }
        yield instruction

        # 3. Normal agent message (SHOULD pass through)
        # The streaming block filters task_ledger/instruction but passes agent content.
        normal_msg = AgentRunUpdateEvent(executor_id="Searcher", data=MagicMock())
        normal_msg.data.text = "I found something"
        normal_msg.data.author_name = "Searcher"
        normal_msg.data.additional_properties = {}
        yield normal_msg

    mock_workflow.run_stream = event_stream
    orchestrator._build_workflow = MagicMock(return_value=mock_workflow)

    orchestrator._init_workflow_events = _empty_async_generator
    orchestrator._init_embedding_service = MagicMock(return_value=None)
    orchestrator._create_task_prompt = MagicMock(return_value="task")

    events = []
    async for event in orchestrator.run("query"):
        events.append(event)

    # Assertions
    # 1. Verify we got the normal message
    streaming_messages = [e.message for e in events if e.type == "streaming"]
    assert "I found something" in streaming_messages

    # 2. Verify we did NOT get the internal messages
    all_messages = [e.message for e in events]
    # The JSON from task_ledger should be filtered
    assert not any('{"some": "json"}' in msg for msg in all_messages)
    # The instruction text should be filtered
    assert not any("Internal instruction to agent" in msg for msg in all_messages)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_reporter_ran_tracking_still_works():
    """Verify internal state.reporter_ran is set correctly even though UI events are silenced."""
    orchestrator = AdvancedOrchestrator()
    mock_workflow = MagicMock()

    async def event_stream(task):
        # Reporter completion event - should set internal flag
        yield ExecutorCompletedEvent(executor_id=REPORTER_AGENT_ID, data=None)

    mock_workflow.run_stream = event_stream
    orchestrator._build_workflow = MagicMock(return_value=mock_workflow)

    orchestrator._init_workflow_events = _empty_async_generator
    orchestrator._init_embedding_service = MagicMock(return_value=None)
    orchestrator._create_task_prompt = MagicMock(return_value="task")

    # Run the workflow
    events = []
    async for event in orchestrator.run("query"):
        events.append(event)

    # The key assertion: No "synthesis" fallback should have been triggered
    # If reporter_ran was NOT set, we'd see a fallback synthesis event
    fallback_events = [
        e for e in events if e.type == "synthesis" or "fallback" in e.message.lower()
    ]
    assert len(fallback_events) == 0, (
        f"Fallback synthesis triggered - reporter_ran tracking broken: {fallback_events}"
    )
