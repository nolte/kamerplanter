"""REQ-038 §4 — CV disease-diagnosis result processing.

Pure logic: applies the confidence gates (``CONFIDENCE_SHOW`` drop floor,
``CONFIDENCE_HIGHLIGHT`` emphasis bar), maps each class against REQ-010
``diseases``/``pests`` stammdaten (deficiencies stay null and map via REQ-036
symptom slugs), and derives whether the result is confident. It NEVER triggers a
treatment (§0): the strongest outcome is an IPM inspection/treatment *suggestion*
the grower confirms manually. The disclaimer is guaranteed non-empty (§4.4).
"""

from typing import Protocol

from app.common.enums import DiagnosisCategory
from app.domain.interfaces.cv_diagnosis_adapter import (
    DEFAULT_DISEASE_DISCLAIMER,
    CvDiagnosisResult,
    DiseaseClassification,
)

# Categories that can warrant an IPM inspection. ``healthy`` never does.
_ACTIONABLE = {DiagnosisCategory.DISEASE, DiagnosisCategory.DEFICIENCY, DiagnosisCategory.PEST}


class DiagnosisMatcher(Protocol):
    """Resolves a CV class against REQ-010 stammdaten / REQ-036 symptom slugs.

    Implementations wrap the IPM repository; each method returns the matched key
    or ``None`` when nothing is found (open-set: an unmapped hit is still shown).
    """

    def match_disease_key(self, scientific_name: str | None) -> str | None: ...

    def match_pest_key(self, scientific_name: str | None) -> str | None: ...

    def match_symptom_slug(self, label: str) -> str | None: ...


class CvDiagnosisEngine:
    """Applies confidence gates and IPM mapping to a raw diagnosis result."""

    def __init__(
        self,
        matcher: DiagnosisMatcher,
        *,
        confidence_show: float,
        confidence_highlight: float,
    ) -> None:
        self._matcher = matcher
        self._confidence_show = confidence_show
        self._confidence_highlight = confidence_highlight

    def process(self, result: CvDiagnosisResult) -> CvDiagnosisResult:
        """Filter, gate, map and finalise a raw diagnosis result (returns a copy)."""
        kept = [c for c in result.classifications if c.probability >= self._confidence_show]
        for classification in kept:
            classification.highlight = classification.probability >= self._confidence_highlight
            self._map_classification(classification)

        is_confident = any(c.category in _ACTIONABLE and c.highlight for c in kept)
        disclaimer = result.disclaimer or DEFAULT_DISEASE_DISCLAIMER

        return result.model_copy(
            update={
                "classifications": kept,
                "is_confident": is_confident,
                "disclaimer": disclaimer,
            }
        )

    def _map_classification(self, classification: DiseaseClassification) -> None:
        """Resolve one class against stammdaten; deficiencies use symptom slugs."""
        # Reset so a reprocessed result never carries stale keys.
        classification.matched_disease_key = None
        classification.matched_pest_key = None
        classification.matched_symptom_slug = None

        if classification.category == DiagnosisCategory.DISEASE:
            classification.matched_disease_key = self._matcher.match_disease_key(classification.scientific_name)
        elif classification.category == DiagnosisCategory.PEST:
            classification.matched_pest_key = self._matcher.match_pest_key(classification.scientific_name)
        elif classification.category == DiagnosisCategory.DEFICIENCY:
            # No REQ-010 deficiency collection yet — bridge via REQ-036 symptom slug.
            classification.matched_symptom_slug = self._matcher.match_symptom_slug(classification.label)
        # HEALTHY: intentionally no mapping.
