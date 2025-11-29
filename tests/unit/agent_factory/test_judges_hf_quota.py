"""Unit tests for HFInferenceJudgeHandler Quota Logic."""

from unittest.mock import patch

import pytest

from src.agent_factory.judges import HFInferenceJudgeHandler
from src.utils.models import Citation, Evidence


@pytest.mark.unit
class TestHFInferenceJudgeHandlerQuota:
    """Tests for HFInferenceJudgeHandler Quota handling."""

    @pytest.mark.asyncio
    async def test_assess_quota_exhausted(self):
        """Test that quota exhaustion triggers fallback extraction."""
        handler = HFInferenceJudgeHandler()

        # Create some dummy evidence
        evidence = [
            Evidence(
                content="Content 1",
                citation=Citation(
                    source="pubmed", title="Important Drug A Findings", url="u1", date="d1"
                ),
            ),
            Evidence(
                content="Content 2",
                citation=Citation(
                    source="pubmed", title="Clinical Trial of Drug B", url="u2", date="d2"
                ),
            ),
        ]

        # Mock _call_with_retry to raise a Quota error
        with patch.object(
            handler, "_call_with_retry", side_effect=Exception("402 Payment Required")
        ):
            result = await handler.assess("question", evidence)

            # Check that it caught the error and stopped
            assert result.sufficient is True
            assert "Free Tier Quota Exceeded" in result.reasoning

            # CRITICAL: Check that it extracted findings from titles
            assert "Important Drug A Findings" in result.details.key_findings
            assert "Clinical Trial of Drug B" in result.details.key_findings
            assert result.details.drug_candidates == ["Upgrade to paid API for drug extraction."]
