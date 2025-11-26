"""Unit tests for ClinicalTrials.gov tool."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.tools.clinicaltrials import ClinicalTrialsTool
from src.utils.exceptions import SearchError
from src.utils.models import Evidence


@pytest.fixture
def mock_clinicaltrials_response() -> dict:
    """Mock ClinicalTrials.gov API response."""
    return {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT04098666",
                        "briefTitle": "Metformin in Alzheimer's Dementia Prevention",
                    },
                    "statusModule": {
                        "overallStatus": "Recruiting",
                        "startDateStruct": {"date": "2020-01-15"},
                    },
                    "descriptionModule": {
                        "briefSummary": "This study evaluates metformin for Alzheimer's prevention."
                    },
                    "designModule": {"phases": ["PHASE2"]},
                    "conditionsModule": {"conditions": ["Alzheimer Disease", "Dementia"]},
                    "armsInterventionsModule": {
                        "interventions": [{"name": "Metformin", "type": "Drug"}]
                    },
                }
            }
        ]
    }


class TestClinicalTrialsTool:
    """Tests for ClinicalTrialsTool."""

    def test_tool_name(self) -> None:
        """Tool should have correct name."""
        tool = ClinicalTrialsTool()
        assert tool.name == "clinicaltrials"

    @pytest.mark.asyncio
    async def test_search_returns_evidence(self, mock_clinicaltrials_response: dict) -> None:
        """Search should return Evidence objects."""
        with patch("src.tools.clinicaltrials.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_clinicaltrials_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            tool = ClinicalTrialsTool()
            results = await tool.search("metformin alzheimer", max_results=5)

            assert len(results) == 1
            assert isinstance(results[0], Evidence)
            assert results[0].citation.source == "clinicaltrials"
            assert "NCT04098666" in results[0].citation.url
            assert "Metformin" in results[0].citation.title

    @pytest.mark.asyncio
    async def test_search_extracts_phase(self, mock_clinicaltrials_response: dict) -> None:
        """Search should extract trial phase."""
        with patch("src.tools.clinicaltrials.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_clinicaltrials_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            tool = ClinicalTrialsTool()
            results = await tool.search("metformin alzheimer")

            assert "PHASE2" in results[0].content

    @pytest.mark.asyncio
    async def test_search_extracts_status(self, mock_clinicaltrials_response: dict) -> None:
        """Search should extract trial status."""
        with patch("src.tools.clinicaltrials.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_clinicaltrials_response
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            tool = ClinicalTrialsTool()
            results = await tool.search("metformin alzheimer")

            assert "Recruiting" in results[0].content

    @pytest.mark.asyncio
    async def test_search_empty_results(self) -> None:
        """Search should handle empty results gracefully."""
        with patch("src.tools.clinicaltrials.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"studies": []}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            tool = ClinicalTrialsTool()
            results = await tool.search("nonexistent query xyz")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_api_error(self) -> None:
        """Search should raise SearchError on API failure."""
        with patch("src.tools.clinicaltrials.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
            mock_get.return_value = mock_response

            tool = ClinicalTrialsTool()

            with pytest.raises(SearchError):
                await tool.search("metformin alzheimer")


class TestClinicalTrialsIntegration:
    """Integration tests (marked for separate run)."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_call(self) -> None:
        """Test actual API call (requires network)."""
        tool = ClinicalTrialsTool()
        results = await tool.search("metformin diabetes", max_results=3)

        assert len(results) > 0
        assert all(isinstance(r, Evidence) for r in results)
        assert all(r.citation.source == "clinicaltrials" for r in results)
