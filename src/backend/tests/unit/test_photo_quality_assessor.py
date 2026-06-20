"""REQ-034 §4a.2 — unit tests for :class:`PhotoQualityAssessor`.

Pure rating logic against constructed ``IdentificationResult``s — no I/O.
"""

from __future__ import annotations

from app.domain.engines.photo_quality_assessor import (
    GOOD_CONFIDENCE_THRESHOLD,
    POOR_CONFIDENCE_THRESHOLD,
    STORED_SUGGESTIONS,
    PhotoQualityAssessor,
)
from app.domain.interfaces.plant_identification_adapter import (
    IdentificationResult,
    IdentificationSuggestion,
)

ASSESSOR = PhotoQualityAssessor()
EXPECTED = "Ocimum basilicum"


def _result(pairs, *, is_plant=True):
    return IdentificationResult(
        suggestions=[
            IdentificationSuggestion(rank=i + 1, scientific_name=n, confidence=c, external_id=f"x:{i}")
            for i, (n, c) in enumerate(pairs)
        ],
        is_plant=is_plant,
    )


def _assess(result, expected=EXPECTED):
    return ASSESSOR.assess(result, adapter_key="plantnet", expected_scientific_name=expected)


class TestWithExpectedSpecies:
    def test_good_top1_high_confidence(self):
        a = _assess(_result([(EXPECTED, GOOD_CONFIDENCE_THRESHOLD), ("Mentha spicata", 0.1)]))
        assert a.rating == "good"
        assert a.expected_species_matched is True

    def test_fair_expected_not_top1(self):
        a = _assess(_result([("Mentha spicata", 0.6), (EXPECTED, 0.3)]))
        assert a.rating == "fair"
        assert a.expected_species_matched is True

    def test_fair_top1_match_but_low_confidence(self):
        # Expected is top-1 but below the GOOD threshold → fair, not good.
        a = _assess(_result([(EXPECTED, GOOD_CONFIDENCE_THRESHOLD - 0.05)]))
        assert a.rating == "fair"

    def test_poor_expected_missing_low_confidence(self):
        a = _assess(_result([("Mentha spicata", 0.3), ("Rosa canina", 0.1)]))
        assert a.rating == "poor"
        assert a.expected_species_matched is False

    def test_fair_expected_missing_but_confident_other(self):
        # A confident-but-different top-1 → usable (fair), not poor.
        a = _assess(_result([("Mentha spicata", GOOD_CONFIDENCE_THRESHOLD + 0.1)]))
        assert a.rating == "fair"
        assert a.expected_species_matched is False

    def test_poor_not_a_plant(self):
        a = _assess(_result([], is_plant=False))
        assert a.rating == "poor"
        assert a.is_plant is False

    def test_name_match_is_case_and_space_insensitive(self):
        a = _assess(_result([("  ocimum   BASILICUM ", 0.9)]))
        assert a.rating == "good"
        assert a.expected_species_matched is True

    def test_only_top_k_counts_for_match(self):
        # Expected sits at rank 6 (beyond TOP_K=5) → treated as missing.
        pairs = [("A sp", 0.3), ("B sp", 0.25), ("C sp", 0.2), ("D sp", 0.15), ("E sp", 0.12), (EXPECTED, 0.1)]
        a = _assess(_result(pairs))
        assert a.expected_species_matched is False
        assert a.rating == "poor"


class TestWithoutExpectedSpecies:
    def test_good_high_confidence(self):
        a = _assess(_result([("Anything sp", GOOD_CONFIDENCE_THRESHOLD)]), expected=None)
        assert a.rating == "good"
        assert a.expected_species_matched is None

    def test_fair_mid_confidence(self):
        mid = (GOOD_CONFIDENCE_THRESHOLD + POOR_CONFIDENCE_THRESHOLD) / 2
        a = _assess(_result([("Anything sp", mid)]), expected=None)
        assert a.rating == "fair"

    def test_poor_low_confidence(self):
        a = _assess(_result([("Anything sp", POOR_CONFIDENCE_THRESHOLD - 0.05)]), expected=None)
        assert a.rating == "poor"

    def test_poor_not_a_plant(self):
        a = _assess(_result([], is_plant=False), expected=None)
        assert a.rating == "poor"


class TestStoredSuggestions:
    def test_only_top_n_suggestions_stored(self):
        pairs = [(f"Sp {i}", 0.5) for i in range(6)]
        a = _assess(_result(pairs))
        assert len(a.suggestions) == STORED_SUGGESTIONS
        assert a.suggestions[0].scientific_name == "Sp 0"

    def test_adapter_key_recorded(self):
        a = ASSESSOR.assess(
            _result([(EXPECTED, 0.9)]),
            adapter_key="local_embedding",
            expected_scientific_name=EXPECTED,
        )
        assert a.adapter == "local_embedding"
        assert a.assessed_at is not None
