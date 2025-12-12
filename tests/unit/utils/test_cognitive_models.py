"""Unit tests for cognitive state models (Hypothesis, Conflict).

These models support research memory and hypothesis tracking.
"""

from src.utils.models import Conflict, Hypothesis


def test_hypothesis_pydantic_model():
    """Verify Hypothesis Pydantic model validation."""
    hypo = Hypothesis(id="h1", statement="Test hypothesis", status="proposed", confidence=0.5)
    assert hypo.id == "h1"
    assert hypo.status == "proposed"
    assert hypo.confidence == 0.5
    # Test default lists
    assert hypo.supporting_evidence_ids == []
    assert hypo.contradicting_evidence_ids == []


def test_hypothesis_status_transitions():
    """Verify hypothesis status can be set to all valid values."""
    for status in ["proposed", "validating", "confirmed", "refuted"]:
        hypo = Hypothesis(id="h1", statement="Test", status=status)  # type: ignore[arg-type]
        assert hypo.status == status


def test_hypothesis_confidence_bounds():
    """Verify confidence is bounded between 0 and 1."""
    hypo = Hypothesis(id="h1", statement="Test", confidence=0.0)
    assert hypo.confidence == 0.0

    hypo = Hypothesis(id="h1", statement="Test", confidence=1.0)
    assert hypo.confidence == 1.0


def test_conflict_model():
    """Verify Conflict model."""
    conflict = Conflict(
        id="c1",
        description="Conflict A vs B",
        source_a_id="doc1",
        source_b_id="doc2",
        status="open",
    )
    assert conflict.status == "open"
    assert conflict.resolution is None


def test_conflict_resolution():
    """Verify Conflict can be resolved."""
    conflict = Conflict(
        id="c1",
        description="Conflict",
        source_a_id="a",
        source_b_id="b",
        status="resolved",
        resolution="Source A was more recent",
    )
    assert conflict.status == "resolved"
    assert conflict.resolution == "Source A was more recent"
