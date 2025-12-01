"""Unit tests for HFInferenceJudgeHandler.synthesize() method.

These tests verify the CodeRabbit recommendations:
1. Model fallback iteration logic
2. Error handling when all models fail (SynthesisError with context)
3. Return value validation (length checks)
4. Short response rejection behavior
"""

from unittest.mock import MagicMock, patch

import pytest

from src.agent_factory.judges import HFInferenceJudgeHandler
from src.utils.exceptions import SynthesisError


@pytest.mark.unit
class TestHFInferenceJudgeHandlerSynthesize:
    """Tests for HFInferenceJudgeHandler.synthesize() method."""

    @pytest.fixture
    def handler(self) -> HFInferenceJudgeHandler:
        """Create a handler instance for testing."""
        return HFInferenceJudgeHandler()

    @pytest.mark.asyncio
    async def test_synthesize_success_first_model(self, handler: HFInferenceJudgeHandler):
        """Should return narrative from first working model."""
        mock_response = MagicMock()
        content = "This is a synthesized narrative report with sufficient length."
        mock_response.choices = [MagicMock(message=MagicMock(content=content))]

        with patch.object(handler.client, "chat_completion", return_value=mock_response):
            result = await handler.synthesize("system prompt", "user prompt")

        assert result is not None
        assert len(result) > 50
        assert "synthesized narrative" in result

    @pytest.mark.asyncio
    async def test_synthesize_fallback_to_second_model(self, handler: HFInferenceJudgeHandler):
        """Should try second model if first fails."""
        # First call fails, second succeeds
        mock_response_success = MagicMock()
        content = "Fallback model generated this narrative successfully here."
        mock_response_success.choices = [MagicMock(message=MagicMock(content=content))]

        call_count = 0

        def mock_chat_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Model unavailable")
            return mock_response_success

        with patch.object(handler.client, "chat_completion", side_effect=mock_chat_completion):
            result = await handler.synthesize("system", "user")

        assert result is not None
        assert "Fallback model" in result
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_synthesize_all_models_fail_raises_synthesis_error(
        self, handler: HFInferenceJudgeHandler
    ):
        """Should raise SynthesisError with context when all models fail."""
        with patch.object(
            handler.client, "chat_completion", side_effect=Exception("All models down")
        ):
            with pytest.raises(SynthesisError) as exc_info:
                await handler.synthesize("system", "user")

            error = exc_info.value
            assert "All HuggingFace synthesis models failed" in str(error)
            assert len(error.attempted_models) == len(handler.FALLBACK_MODELS)
            assert len(error.errors) == len(handler.FALLBACK_MODELS)
            assert all("All models down" in e for e in error.errors)

    @pytest.mark.asyncio
    async def test_synthesize_rejects_short_responses(self, handler: HFInferenceJudgeHandler):
        """Should skip responses shorter than minimum length and try next model."""
        # First response too short, second is valid
        call_count = 0

        def mock_chat_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = MagicMock()
            if call_count == 1:
                # Too short (under 50 chars)
                mock_response.choices = [MagicMock(message=MagicMock(content="Too short"))]
            else:
                # Valid length
                mock_response.choices = [
                    MagicMock(
                        message=MagicMock(
                            content="This is a valid response with sufficient length for synthesis."
                        )
                    )
                ]
            return mock_response

        with patch.object(handler.client, "chat_completion", side_effect=mock_chat_completion):
            result = await handler.synthesize("system", "user")

        assert result is not None
        assert "valid response" in result
        assert call_count == 2  # First rejected, second accepted

    @pytest.mark.asyncio
    async def test_synthesize_short_responses_counted_as_errors(
        self, handler: HFInferenceJudgeHandler
    ):
        """Short responses should be tracked in errors list."""
        # All responses are too short
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Short"))]

        with patch.object(handler.client, "chat_completion", return_value=mock_response):
            with pytest.raises(SynthesisError) as exc_info:
                await handler.synthesize("system", "user")

            error = exc_info.value
            # Should have error entries for short responses
            assert any("too short" in e.lower() for e in error.errors)

    @pytest.mark.asyncio
    async def test_synthesize_uses_specific_model_if_provided(self):
        """Should use specific model ID if provided at init."""
        handler = HFInferenceJudgeHandler(model_id="custom/model-id")

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="Custom model response with sufficient length for validation."
                )
            )
        ]

        with patch.object(handler.client, "chat_completion", return_value=mock_response) as mock:
            await handler.synthesize("system", "user")

            # Should only try the custom model
            assert mock.call_count == 1
            call_kwargs = mock.call_args[1]
            assert call_kwargs["model"] == "custom/model-id"

    @pytest.mark.asyncio
    async def test_synthesize_specific_model_failure_raises_synthesis_error(self):
        """When specific model fails, should raise SynthesisError with only that model."""
        handler = HFInferenceJudgeHandler(model_id="custom/model-id")

        with patch.object(
            handler.client, "chat_completion", side_effect=Exception("Custom model failed")
        ):
            with pytest.raises(SynthesisError) as exc_info:
                await handler.synthesize("system", "user")

            error = exc_info.value
            assert len(error.attempted_models) == 1
            assert error.attempted_models[0] == "custom/model-id"
