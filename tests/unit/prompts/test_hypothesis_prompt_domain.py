"""Tests for hypothesis prompt domain support."""

from src.config.domain import SEXUAL_HEALTH_CONFIG, ResearchDomain
from src.prompts.hypothesis import get_system_prompt


class TestHypothesisPromptDomain:
    def test_get_system_prompt_default(self):
        prompt = get_system_prompt()
        assert SEXUAL_HEALTH_CONFIG.hypothesis_system_prompt in prompt
        assert "Your role is to generate mechanistic hypotheses" in prompt

    def test_get_system_prompt_sexual_health(self):
        prompt = get_system_prompt(ResearchDomain.SEXUAL_HEALTH)
        assert SEXUAL_HEALTH_CONFIG.hypothesis_system_prompt in prompt
        assert "sexual health" in prompt.lower()
        assert "Your role is to generate mechanistic hypotheses" in prompt
