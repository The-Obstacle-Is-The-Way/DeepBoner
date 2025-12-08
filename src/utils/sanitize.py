"""LLM output sanitization utilities.

This module provides defense-in-depth filtering for LLM outputs.
Even premium models (GPT-4, Claude) can emit garbage tokens from training data.

Principle: Never trust external systems. An LLM is an external system.

References:
- P2 Bug: docs/bugs/p2-llm-output-contamination.md
- Observed artifacts: .ToDecimal (C# method), <|endoftext|> (training tokens)
"""

import re
from typing import Final

# Known garbage patterns from LLM training data contamination
# Each pattern matches a COMPLETE line that should be removed
_GARBAGE_LINE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    # C#/Java method-like tokens: .ToDecimal, .ToString, .Parse, .GetType
    re.compile(r"^\s*\.[A-Z][a-zA-Z]+\s*$"),
    # Special tokens from various model architectures
    re.compile(r"^\s*<\|[a-z_]+\|>\s*$"),  # <|endoftext|>, <|im_end|>
    re.compile(r"^\s*<\|.*?\|>\s*$"),  # Broader special token catch
    # Empty markdown headers (common formatting glitch)
    re.compile(r"^\s*#{1,6}\s*$"),
    # Isolated punctuation lines
    re.compile(r"^\s*[.]{3,}\s*$"),  # Just ellipsis
    re.compile(r"^\s*[-]{3,}\s*$"),  # Just dashes (but keep --- as separator)
)

# Inline patterns to remove (within a line, not the whole line)
_GARBAGE_INLINE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    # C# method calls appearing mid-text
    re.compile(r"\s*\.[A-Z][a-zA-Z]+(?:\(\))?(?=\s|$)"),
    # Stray special tokens inline
    re.compile(r"<\|[a-z_]+\|>"),
)


def sanitize_streaming_text(text: str) -> str:
    """Sanitize a single streaming chunk from LLM output.

    This is called on each streaming token/chunk before yielding to UI.
    Designed for low overhead on hot path.

    Args:
        text: Raw text chunk from LLM

    Returns:
        Sanitized text with garbage tokens removed

    Example:
        >>> sanitize_streaming_text(".ToDecimal")
        ''
        >>> sanitize_streaming_text("Normal medical text")
        'Normal medical text'
    """
    if not text:
        return text

    # Fast path: most text is clean
    # Check if any suspicious patterns might be present
    # Note: '#' alone could be empty markdown header glitch
    empty_headers = {"#", "##", "###", "####", "#####", "######"}
    if "." not in text and "<|" not in text and text.strip() not in empty_headers:
        return text

    # Check full-line patterns (for single-line chunks)
    stripped = text.strip()
    for pattern in _GARBAGE_LINE_PATTERNS:
        if pattern.match(stripped):
            return ""

    # Check inline patterns
    result = text
    for pattern in _GARBAGE_INLINE_PATTERNS:
        result = pattern.sub("", result)

    return result


def sanitize_complete_output(text: str) -> str:
    """Sanitize complete LLM output (multi-line).

    Used for final output cleanup before displaying complete responses.

    Args:
        text: Complete multi-line text from LLM

    Returns:
        Sanitized text with garbage lines and tokens removed
    """
    if not text:
        return text

    lines = text.split("\n")
    cleaned_lines: list[str] = []

    for line in lines:
        # Check if entire line is garbage
        stripped = line.strip()
        is_garbage_line = any(p.match(stripped) for p in _GARBAGE_LINE_PATTERNS)

        if is_garbage_line:
            continue  # Skip this line entirely

        # Clean inline garbage from the line
        cleaned = line
        for pattern in _GARBAGE_INLINE_PATTERNS:
            cleaned = pattern.sub("", cleaned)

        cleaned_lines.append(cleaned)

    return "\n".join(cleaned_lines)


def is_garbage_token(text: str) -> bool:
    """Check if text is purely a garbage token.

    Useful for pre-filtering before accumulation.

    Args:
        text: Text to check

    Returns:
        True if text matches known garbage patterns
    """
    if not text:
        return False

    stripped = text.strip()
    return any(p.match(stripped) for p in _GARBAGE_LINE_PATTERNS)
