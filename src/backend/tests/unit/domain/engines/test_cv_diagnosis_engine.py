"""REQ-038 §4 — CvDiagnosisEngine: gates, IPM mapping, disclaimer invariant."""

from app.common.enums import DiagnosisCategory
from app.domain.engines.cv_diagnosis_engine import CvDiagnosisEngine
from app.domain.interfaces.cv_diagnosis_adapter import (
    DEFAULT_DISEASE_DISCLAIMER,
    CvDiagnosisResult,
    DiseaseClassification,
)


class _FakeMatcher:
    """Resolves a fixed set of classes against pretend stammdaten."""

    def match_disease_key(self, scientific_name: str | None) -> str | None:
        return "disease_early_blight" if scientific_name == "Alternaria solani" else None

    def match_pest_key(self, scientific_name: str | None) -> str | None:
        return "pest_spider_mite" if scientific_name == "Tetranychus urticae" else None

    def match_symptom_slug(self, label: str) -> str | None:
        return "chlorosis" if label == "nitrogen_deficiency" else None


def _engine(show: float = 0.10, highlight: float = 0.75) -> CvDiagnosisEngine:
    return CvDiagnosisEngine(_FakeMatcher(), confidence_show=show, confidence_highlight=highlight)


def _result(classifications: list[DiseaseClassification]) -> CvDiagnosisResult:
    return CvDiagnosisResult(classifications=classifications, adapter_key="local_cv_diagnosis")


class TestConfidenceGates:
    def test_drops_classes_below_show_floor(self):
        result = _result(
            [
                DiseaseClassification(label="a", category=DiagnosisCategory.DISEASE, probability=0.80),
                DiseaseClassification(label="b", category=DiagnosisCategory.DISEASE, probability=0.05),
            ]
        )
        processed = _engine().process(result)
        assert [c.label for c in processed.classifications] == ["a"]

    def test_highlight_flag_above_highlight_bar(self):
        result = _result(
            [
                DiseaseClassification(label="hi", category=DiagnosisCategory.DISEASE, probability=0.90),
                DiseaseClassification(label="lo", category=DiagnosisCategory.DISEASE, probability=0.40),
            ]
        )
        processed = _engine().process(result)
        by_label = {c.label: c for c in processed.classifications}
        assert by_label["hi"].highlight is True
        assert by_label["lo"].highlight is False

    def test_is_confident_only_when_actionable_class_highlighted(self):
        confident = _engine().process(
            _result([DiseaseClassification(label="x", category=DiagnosisCategory.DISEASE, probability=0.9)])
        )
        assert confident.is_confident is True
        # Healthy is never actionable, even at high probability.
        healthy = _engine().process(
            _result([DiseaseClassification(label="ok", category=DiagnosisCategory.HEALTHY, probability=0.99)])
        )
        assert healthy.is_confident is False


class TestIpmMapping:
    def test_disease_maps_to_disease_key(self):
        result = _result(
            [
                DiseaseClassification(
                    label="tomato_early_blight",
                    category=DiagnosisCategory.DISEASE,
                    scientific_name="Alternaria solani",
                    probability=0.9,
                )
            ]
        )
        c = _engine().process(result).classifications[0]
        assert c.matched_disease_key == "disease_early_blight"
        assert c.matched_pest_key is None
        assert c.matched_symptom_slug is None

    def test_pest_maps_to_pest_key(self):
        result = _result(
            [
                DiseaseClassification(
                    label="spider_mite_damage",
                    category=DiagnosisCategory.PEST,
                    scientific_name="Tetranychus urticae",
                    probability=0.9,
                )
            ]
        )
        c = _engine().process(result).classifications[0]
        assert c.matched_pest_key == "pest_spider_mite"
        assert c.matched_disease_key is None

    def test_deficiency_stays_null_and_bridges_via_symptom_slug(self):
        result = _result(
            [
                DiseaseClassification(
                    label="nitrogen_deficiency",
                    category=DiagnosisCategory.DEFICIENCY,
                    probability=0.9,
                )
            ]
        )
        c = _engine().process(result).classifications[0]
        assert c.matched_disease_key is None
        assert c.matched_pest_key is None
        assert c.matched_symptom_slug == "chlorosis"

    def test_unmatched_disease_stays_open_set_null(self):
        result = _result(
            [
                DiseaseClassification(
                    label="unknown_spot",
                    category=DiagnosisCategory.DISEASE,
                    scientific_name="Unknownus fictus",
                    probability=0.9,
                )
            ]
        )
        c = _engine().process(result).classifications[0]
        assert c.matched_disease_key is None


class TestDisclaimerInvariant:
    def test_disclaimer_never_empty_even_when_missing(self):
        result = _result([DiseaseClassification(label="x", category=DiagnosisCategory.DISEASE, probability=0.9)])
        result.disclaimer = ""  # simulate a malformed upstream payload
        processed = _engine().process(result)
        assert processed.disclaimer == DEFAULT_DISEASE_DISCLAIMER
        assert processed.disclaimer.strip() != ""

    def test_disclaimer_preserved_when_present(self):
        result = _result([])
        result.disclaimer = "custom hint"
        assert _engine().process(result).disclaimer == "custom hint"
