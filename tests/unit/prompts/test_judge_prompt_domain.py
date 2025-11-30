"""Tests for judge prompt domain support."""

from src.config.domain import SEXUAL_HEALTH_CONFIG, ResearchDomain
from src.prompts.judge import format_user_prompt, get_scoring_prompt, get_system_prompt


class TestJudgePromptDomain:
    def test_get_system_prompt_default(self):
        prompt = get_system_prompt()
        assert SEXUAL_HEALTH_CONFIG.judge_system_prompt in prompt
        assert "Your task is to SCORE evidence" in prompt

    def test_get_system_prompt_sexual_health(self):
        prompt = get_system_prompt(ResearchDomain.SEXUAL_HEALTH)
        assert SEXUAL_HEALTH_CONFIG.judge_system_prompt in prompt
        assert "sexual health" in prompt.lower()
        assert "Your task is to SCORE evidence" in prompt

    def test_get_scoring_prompt_default(self):
        prompt = get_scoring_prompt()
        assert SEXUAL_HEALTH_CONFIG.judge_scoring_prompt == prompt

    def test_format_user_prompt_default(self):
        prompt = format_user_prompt("query", [])
        assert SEXUAL_HEALTH_CONFIG.judge_scoring_prompt in prompt
        assert "sexual health" in prompt.lower()

    def test_format_user_prompt_with_domain(self):
        prompt = format_user_prompt("query", [], domain=ResearchDomain.SEXUAL_HEALTH)
        assert SEXUAL_HEALTH_CONFIG.judge_scoring_prompt in prompt
        assert "sexual health" in prompt.lower()
