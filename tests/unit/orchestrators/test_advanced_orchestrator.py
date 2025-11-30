import os
from unittest.mock import patch

import pytest

from src.orchestrators.advanced import AdvancedOrchestrator


@pytest.mark.unit
class TestAdvancedOrchestratorConfig:
    """Tests for configuration options."""

    def test_default_max_rounds_is_five(self) -> None:
        """Default max_rounds should be 5 for faster demos."""
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("src.orchestrators.advanced.check_magentic_requirements"),
        ):
            # Clear any existing env var
            os.environ.pop("ADVANCED_MAX_ROUNDS", None)
            orch = AdvancedOrchestrator()
            assert orch._max_rounds == 5

    def test_max_rounds_from_env(self) -> None:
        """max_rounds should be configurable via environment."""
        with (
            patch.dict(os.environ, {"ADVANCED_MAX_ROUNDS": "3"}),
            patch("src.orchestrators.advanced.check_magentic_requirements"),
        ):
            orch = AdvancedOrchestrator()
            assert orch._max_rounds == 3

    def test_explicit_max_rounds_overrides_env(self) -> None:
        """Explicit parameter should override environment."""
        with (
            patch.dict(os.environ, {"ADVANCED_MAX_ROUNDS": "3"}),
            patch("src.orchestrators.advanced.check_magentic_requirements"),
        ):
            orch = AdvancedOrchestrator(max_rounds=7)
            assert orch._max_rounds == 7

    def test_timeout_default_is_five_minutes(self) -> None:
        """Default timeout should be 300s (5 min) for faster failure."""
        with patch("src.orchestrators.advanced.check_magentic_requirements"):
            orch = AdvancedOrchestrator()
            assert orch._timeout_seconds == 300.0

    def test_invalid_env_rounds_falls_back_to_default(self) -> None:
        """Invalid ADVANCED_MAX_ROUNDS should fall back to 5."""
        with (
            patch.dict(os.environ, {"ADVANCED_MAX_ROUNDS": "not_a_number"}),
            patch("src.orchestrators.advanced.check_magentic_requirements"),
        ):
            orch = AdvancedOrchestrator()
            assert orch._max_rounds == 5

    def test_zero_env_rounds_clamps_to_one(self) -> None:
        """ADVANCED_MAX_ROUNDS=0 should clamp to 1."""
        with (
            patch.dict(os.environ, {"ADVANCED_MAX_ROUNDS": "0"}),
            patch("src.orchestrators.advanced.check_magentic_requirements"),
        ):
            orch = AdvancedOrchestrator()
            assert orch._max_rounds == 1

    def test_negative_env_rounds_clamps_to_one(self) -> None:
        """Negative ADVANCED_MAX_ROUNDS should clamp to 1."""
        with (
            patch.dict(os.environ, {"ADVANCED_MAX_ROUNDS": "-5"}),
            patch("src.orchestrators.advanced.check_magentic_requirements"),
        ):
            orch = AdvancedOrchestrator()
            assert orch._max_rounds == 1
