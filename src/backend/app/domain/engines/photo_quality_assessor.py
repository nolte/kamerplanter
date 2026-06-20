"""REQ-034 §4a.2 — derive a photo-quality traffic light from a recognition result.

Given an ``IdentificationResult`` (suggestions with ``scientific_name`` +
``confidence`` and the ``is_plant`` flag) and — optionally — the plant's known
species, this engine derives a ``good`` / ``fair`` / ``poor`` rating that tells
a non-expert user whether a gallery photo is sharp and typical enough for the
recognition to reliably find their plant again.

This is a pure, side-effect-free domain rule (no I/O, no persistence). The
caller (``PlantPhotoService``) persists the resulting :class:`QualityAssessment`
on the attachment.

Rating rules (§4a.2):

* **poor** — ``is_plant == False`` OR the expected species is not among the
  top-k *and* the top-1 confidence is low (probably blurry, wrong crop, or
  atypical).
* **good** — the expected species is the top-1 suggestion *and* its confidence
  is high (representative photo).
* **fair** — anything in between (expected species present but not top-1, or a
  middling top-1 confidence).

Without an expected species (``species_key`` unset) the soll/ist comparison is
skipped and the rating rests on ``is_plant`` + top-1 confidence only.

The thresholds are named module constants so the policy is documented in one
place. They sit between the recognition feature's own
``identification_confidence_min_show`` (0.10) and ``..._auto_accept`` (0.85)
defaults and are intentionally a quality (not an identification) judgement.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.domain.interfaces.plant_identification_adapter import IdentificationResult
from app.domain.models.attachment import QualityAssessment, QualityRating, QualitySuggestion

#: Top-1 confidence at/above which a *matching* top-1 species counts as ``good``.
GOOD_CONFIDENCE_THRESHOLD = 0.70
#: Top-1 confidence below which — with no species match — the photo is ``poor``.
POOR_CONFIDENCE_THRESHOLD = 0.40
#: How many leading suggestions count as the "top-k" the expected species may
#: appear in (matches the recognition default of five candidates).
TOP_K = 5
#: How many suggestions are stored on the assessment for later display (§4a.2).
STORED_SUGGESTIONS = 3


class PhotoQualityAssessor:
    """Derive a :class:`QualityAssessment` from a recognition result (REQ-034 §4a.2)."""

    @staticmethod
    def _normalize(name: str) -> str:
        """Case/space-insensitive scientific-name key for comparison."""
        return " ".join(name.lower().split())

    def assess(
        self,
        result: IdentificationResult,
        *,
        adapter_key: str,
        expected_scientific_name: str | None,
    ) -> QualityAssessment:
        """Return the Ampel verdict for one photo.

        Args:
            result: The raw recognition result for the photo.
            adapter_key: The adapter that produced ``result`` (stored for display).
            expected_scientific_name: The plant's known species name, or ``None``
                when the plant has no ``species_key`` (no soll/ist comparison).
        """
        suggestions = sorted(result.suggestions, key=lambda s: s.rank)
        top1 = suggestions[0] if suggestions else None
        top1_confidence = top1.confidence if top1 else 0.0

        expected_matched: bool | None = None
        if expected_scientific_name:
            expected_norm = self._normalize(expected_scientific_name)
            top_k = suggestions[:TOP_K]
            expected_matched = any(self._normalize(s.scientific_name) == expected_norm for s in top_k)
            is_top1_match = top1 is not None and self._normalize(top1.scientific_name) == expected_norm
        else:
            is_top1_match = False

        rating = self._derive_rating(
            is_plant=result.is_plant,
            expected_scientific_name=expected_scientific_name,
            expected_matched=expected_matched,
            is_top1_match=is_top1_match,
            top1_confidence=top1_confidence,
        )

        stored = [
            QualitySuggestion(
                scientific_name=s.scientific_name,
                confidence=s.confidence,
                external_id=s.external_id,
            )
            for s in suggestions[:STORED_SUGGESTIONS]
        ]

        return QualityAssessment(
            adapter=adapter_key,
            assessed_at=datetime.now(UTC),
            is_plant=result.is_plant,
            rating=rating,
            expected_species_matched=expected_matched,
            suggestions=stored,
        )

    def _derive_rating(
        self,
        *,
        is_plant: bool,
        expected_scientific_name: str | None,
        expected_matched: bool | None,
        is_top1_match: bool,
        top1_confidence: float,
    ) -> QualityRating:
        # No plant material at all → always the worst rating (§4a.2).
        if not is_plant:
            return "poor"

        if expected_scientific_name:
            # With a known species we judge against the soll/ist comparison.
            if is_top1_match and top1_confidence >= GOOD_CONFIDENCE_THRESHOLD:
                return "good"
            if not expected_matched and top1_confidence < GOOD_CONFIDENCE_THRESHOLD:
                # Expected species missing from the top-k and nothing confident
                # took its place → likely unusable for re-recognition.
                return "poor"
            # Expected species present (but not a confident top-1), or a
            # confident-but-different top-1 → usable, not ideal.
            return "fair"

        # No known species: rate purely on plant-ness + top-1 confidence.
        if top1_confidence >= GOOD_CONFIDENCE_THRESHOLD:
            return "good"
        if top1_confidence < POOR_CONFIDENCE_THRESHOLD:
            return "poor"
        return "fair"


__all__ = [
    "GOOD_CONFIDENCE_THRESHOLD",
    "POOR_CONFIDENCE_THRESHOLD",
    "STORED_SUGGESTIONS",
    "TOP_K",
    "PhotoQualityAssessor",
]
