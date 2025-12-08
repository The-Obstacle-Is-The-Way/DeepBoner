"""Unit tests for LLM output sanitization.

Tests verify that known garbage patterns are filtered while
legitimate medical/research text passes through unchanged.

Reference: docs/bugs/p2-llm-output-contamination.md
"""

import pytest

from src.utils.sanitize import (
    is_garbage_token,
    sanitize_complete_output,
    sanitize_streaming_text,
)

pytestmark = pytest.mark.unit


class TestSanitizeStreamingText:
    """Tests for streaming chunk sanitization."""

    def test_removes_todecimal_token(self):
        """Should remove .ToDecimal (the original reported bug)."""
        assert sanitize_streaming_text(".ToDecimal") == ""

    def test_removes_tostring_token(self):
        """Should remove other C# method-like tokens."""
        assert sanitize_streaming_text(".ToString") == ""
        assert sanitize_streaming_text(".Parse") == ""
        assert sanitize_streaming_text(".GetType") == ""

    def test_removes_special_tokens(self):
        """Should remove LLM special tokens."""
        assert sanitize_streaming_text("<|endoftext|>") == ""
        assert sanitize_streaming_text("<|im_end|>") == ""
        assert sanitize_streaming_text("<|im_start|>") == ""

    def test_preserves_normal_text(self):
        """Should pass through normal medical text unchanged."""
        text = "Testosterone therapy shows efficacy in treating HSDD."
        assert sanitize_streaming_text(text) == text

    def test_preserves_text_with_periods(self):
        """Should not remove periods in normal sentences."""
        text = "Dr. Smith conducted the study. Results were positive."
        assert sanitize_streaming_text(text) == text

    def test_preserves_abbreviations(self):
        """Should preserve medical abbreviations."""
        text = "The FDA approved the drug. HSDD affects many patients."
        assert sanitize_streaming_text(text) == text

    def test_preserves_markdown_headers(self):
        """Should preserve markdown headers with content."""
        text = "## Executive Summary"
        assert sanitize_streaming_text(text) == text

    def test_removes_empty_markdown_headers(self):
        """Should remove empty markdown headers (formatting glitch)."""
        assert sanitize_streaming_text("###") == ""
        assert sanitize_streaming_text("## ") == ""

    def test_handles_empty_string(self):
        """Should handle empty input gracefully."""
        assert sanitize_streaming_text("") == ""

    def test_handles_whitespace_only(self):
        """Should handle whitespace input."""
        assert sanitize_streaming_text("   ") == "   "

    def test_removes_inline_garbage(self):
        """Should remove garbage tokens appearing mid-text."""
        text = "Normal text .ToDecimal more text"
        result = sanitize_streaming_text(text)
        assert ".ToDecimal" not in result
        assert "Normal text" in result

    def test_fast_path_no_suspicious_chars(self):
        """Should use fast path when no suspicious patterns possible."""
        # Text without '.' or '<|' should return immediately
        text = "Simple text without suspicious characters"
        assert sanitize_streaming_text(text) == text


class TestSanitizeCompleteOutput:
    """Tests for complete multi-line output sanitization."""

    def test_removes_garbage_lines(self):
        """Should remove entire lines that are garbage."""
        text = "Line one.\n.ToDecimal\nLine three."
        result = sanitize_complete_output(text)
        assert ".ToDecimal" not in result
        assert "Line one." in result
        assert "Line three." in result

    def test_preserves_structure(self):
        """Should preserve document structure."""
        text = """## Summary
This is the summary.

## Methods
These are the methods."""
        result = sanitize_complete_output(text)
        assert "## Summary" in result
        assert "## Methods" in result

    def test_handles_multiple_garbage_tokens(self):
        """Should remove multiple different garbage tokens."""
        text = "Good text.\n.ToDecimal\n<|endoftext|>\nMore good text."
        result = sanitize_complete_output(text)
        assert ".ToDecimal" not in result
        assert "<|endoftext|>" not in result
        assert "Good text." in result
        assert "More good text." in result

    def test_handles_empty_input(self):
        """Should handle empty input."""
        assert sanitize_complete_output("") == ""

    def test_cleans_inline_garbage_in_lines(self):
        """Should clean inline garbage while preserving surrounding text."""
        text = "Start .ToString end"
        result = sanitize_complete_output(text)
        assert ".ToString" not in result
        assert "Start" in result
        assert "end" in result


class TestIsGarbageToken:
    """Tests for garbage detection helper."""

    def test_detects_csharp_methods(self):
        """Should detect C# method-like tokens."""
        assert is_garbage_token(".ToDecimal") is True
        assert is_garbage_token(".ToString") is True
        assert is_garbage_token("  .Parse  ") is True

    def test_detects_special_tokens(self):
        """Should detect LLM special tokens."""
        assert is_garbage_token("<|endoftext|>") is True
        assert is_garbage_token("<|im_end|>") is True

    def test_rejects_normal_text(self):
        """Should not flag normal text as garbage."""
        assert is_garbage_token("Normal text") is False
        assert is_garbage_token("Dr. Smith") is False
        assert is_garbage_token("## Header") is False

    def test_handles_empty(self):
        """Should handle empty input."""
        assert is_garbage_token("") is False
        assert is_garbage_token(None) is False  # type: ignore[arg-type]


class TestIntegrationWithOrchestrator:
    """Tests verifying integration with orchestrator flow."""

    def test_streaming_filter_scenario(self):
        """Simulate the actual bug scenario from production."""
        # This simulates what was observed:
        # LLM outputs ".ToDecimal" between normal text chunks
        chunks = [
            "Research sexual health",
            " and wellness interventions",
            ".ToDecimal",
            " for testosterone therapy.",
        ]

        accumulated = ""
        for chunk in chunks:
            clean = sanitize_streaming_text(chunk)
            if clean:
                accumulated += clean

        assert ".ToDecimal" not in accumulated
        assert "Research sexual health" in accumulated
        assert "wellness interventions" in accumulated
        assert "testosterone therapy" in accumulated

    def test_preserves_medical_terminology(self):
        """Should not corrupt medical terms with periods."""
        medical_terms = [
            "P.O. administration",
            "q.d. dosing",
            "i.v. injection",
            "E. coli infection",
            "S. aureus colonization",
        ]
        for term in medical_terms:
            assert sanitize_streaming_text(term) == term

    def test_preserves_citations(self):
        """Should not corrupt citation formats."""
        citations = [
            "(Smith et al., 2024)",
            "[1] PubMed: 12345678",
            "DOI: 10.1234/example.2024",
        ]
        for citation in citations:
            assert sanitize_streaming_text(citation) == citation
