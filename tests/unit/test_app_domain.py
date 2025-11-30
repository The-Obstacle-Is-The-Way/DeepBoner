"""Tests for App domain support."""

from unittest.mock import ANY, MagicMock, patch

from src.app import configure_orchestrator, research_agent
from src.config.domain import ResearchDomain


class TestAppDomain:
    @patch("src.app.create_orchestrator")
    @patch("src.app.JudgeHandler")
    def test_configure_orchestrator_passes_domain(self, mock_judge, mock_create):
        configure_orchestrator(use_mock=False, mode="simple", domain=ResearchDomain.SEXUAL_HEALTH)

        mock_judge.assert_called_with(model=ANY, domain=ResearchDomain.SEXUAL_HEALTH)
        mock_create.assert_called_with(
            search_handler=ANY,
            judge_handler=ANY,
            config=ANY,
            mode="simple",
            api_key=ANY,
            domain=ResearchDomain.SEXUAL_HEALTH,
        )

    @patch("src.app.configure_orchestrator")
    async def test_research_agent_passes_domain(self, mock_config):
        # Mock orchestrator
        mock_orch = MagicMock()
        mock_orch.run.return_value = []  # Async iterator?

        # To mock async generator
        async def async_gen(*args):
            if False:
                yield  # Make it a generator

        mock_orch.run = async_gen

        mock_config.return_value = (mock_orch, "Test Backend")

        # Consume the generator from research_agent
        gen = research_agent(
            message="query", history=[], mode="simple", domain=ResearchDomain.SEXUAL_HEALTH
        )

        async for _ in gen:
            pass

        mock_config.assert_called_with(
            use_mock=False, mode="simple", user_api_key=None, domain=ResearchDomain.SEXUAL_HEALTH
        )
