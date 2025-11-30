import os
from unittest.mock import patch

import pytest

from src.orchestrators.advanced import AdvancedOrchestrator


@pytest.mark.unit
class TestAdvancedOrchestratorConfig:
    """Tests for configuration options."""

    def test_default_max_rounds_is_five(self) -> None:
        """Default max_rounds should be 5 for faster demos."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing env var
            os.environ.pop("ADVANCED_MAX_ROUNDS", None)
            orch = AdvancedOrchestrator.__new__(AdvancedOrchestrator)
            orch.__init__()
            assert orch._max_rounds == 5

    def test_max_rounds_from_env(self) -> None:
        """max_rounds should be configurable via environment."""
        with patch.dict(os.environ, {"ADVANCED_MAX_ROUNDS": "3"}):
            orch = AdvancedOrchestrator.__new__(AdvancedOrchestrator)
            orch.__init__()
            assert orch._max_rounds == 3

    def test_explicit_max_rounds_overrides_env(self) -> None:
        """Explicit parameter should override environment."""
        with patch.dict(os.environ, {"ADVANCED_MAX_ROUNDS": "3"}):
            orch = AdvancedOrchestrator.__new__(AdvancedOrchestrator)
            orch.__init__(max_rounds=7)
            assert orch._max_rounds == 7

    def test_timeout_default_is_five_minutes(self) -> None:
        """Default timeout should be 300s (5 min) for faster failure."""
        orch = AdvancedOrchestrator.__new__(AdvancedOrchestrator)
        orch.__init__()
        assert orch._timeout_seconds == 300.0
