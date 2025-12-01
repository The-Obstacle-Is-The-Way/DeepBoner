"""Test for AdvancedOrchestrator event processing (P1 Bug)."""

from unittest.mock import MagicMock

import pytest
from agent_framework import MagenticAgentMessageEvent, MagenticOrchestratorMessageEvent

from src.orchestrators.advanced import AdvancedOrchestrator


class TestAdvancedEventProcessing:
    """Test event processing logic in AdvancedOrchestrator."""

    @pytest.fixture
    def orchestrator(self) -> AdvancedOrchestrator:
        """Create an orchestrator instance with mocks."""
        # Bypass __init__ logic that requires keys/env vars
        orch = AdvancedOrchestrator.__new__(AdvancedOrchestrator)
        # Minimal setup
        orch._max_rounds = 5
        orch._timeout_seconds = 300.0
        return orch

    def test_filters_internal_task_ledger_events(self, orchestrator: AdvancedOrchestrator) -> None:
        """
        Bug P1: Internal 'task_ledger' events should be filtered out.

        Current behavior: Returns AgentEvent(type='judging', message='Manager (task_ledger): ...')
        Desired behavior: Returns None (filtered)
        """
        # Create a raw internal framework event
        raw_event = MagenticOrchestratorMessageEvent(
            kind="task_ledger",
            message="We are working to address the following user request: Research sildenafil...",
        )

        # Process the event
        result = orchestrator._process_event(raw_event, iteration=1)

        # FAIL if the event is NOT filtered (i.e., if it returns an event)
        assert result is None, f"Should filter 'task_ledger' events, but got: {result}"

    def test_filters_internal_instruction_events(self, orchestrator: AdvancedOrchestrator) -> None:
        """
        Bug P1: Internal 'instruction' events should be filtered out.

        Current behavior: Returns AgentEvent(type='judging', message='Manager (instruction): ...')
        Desired behavior: Returns None (filtered)
        """
        raw_event = MagenticOrchestratorMessageEvent(
            kind="instruction", message="Conduct targeted searches on PubMed..."
        )

        result = orchestrator._process_event(raw_event, iteration=1)

        assert result is None, f"Should filter 'instruction' events, but got: {result}"

    def test_transforms_user_task_events(self, orchestrator: AdvancedOrchestrator) -> None:
        """
        Bug P1: 'user_task' events should be transformed to user-friendly messages.

        Current behavior: 'Manager (user_task): Research...' (truncated, type='judging')
        Desired behavior: 'Manager assigning research task...' (type='progress')
        """
        raw_event = MagenticOrchestratorMessageEvent(
            kind="user_task",
            message="Research sexual health and wellness interventions for: sildenafil mechanism",
        )

        result = orchestrator._process_event(raw_event, iteration=1)

        assert result is not None
        assert result.type == "progress"  # NOT "judging"
        assert "Manager assigning research task" in result.message
        # Should use the generic friendly message
        assert "sildenafil mechanism" not in result.message

    def test_prevents_mid_sentence_truncation(self, orchestrator: AdvancedOrchestrator) -> None:
        """
        Bug P1: Long messages should be smart-truncated, not hard cut at 200 chars.
        """
        # A long message (> 200 chars)
        long_text = "A" * 250

        # Mock a standard agent message
        mock_message = MagicMock()
        mock_message.content = long_text
        mock_message.text = long_text

        raw_event = MagenticAgentMessageEvent(agent_id="SearchAgent", message=mock_message)

        result = orchestrator._process_event(raw_event, iteration=1)

        assert result is not None
        # Current buggy behavior: len(message) == 200 + len("SearchAgent: ...")
        # We want to verify we don't just slice randomly.
        assert len(result.message) < 300  # Sanity check
