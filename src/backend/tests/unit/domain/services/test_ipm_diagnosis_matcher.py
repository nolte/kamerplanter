"""REQ-038 — IpmDiagnosisMatcher against a fake IIpmRepository."""

from app.domain.models.ipm import Disease, Pest
from app.domain.services.ipm_diagnosis_matcher import IpmDiagnosisMatcher


class _FakeIpmRepo:
    def get_disease_by_scientific_name(self, scientific_name: str):
        if scientific_name == "Alternaria solani":
            return Disease(
                _key="disease_early_blight",
                scientific_name=scientific_name,
                common_name="Early blight",
                pathogen_type="fungal",
            )
        return None

    def get_pest_by_scientific_name(self, scientific_name: str):
        if scientific_name == "Tetranychus urticae":
            return Pest(_key="pest_spider_mite", scientific_name=scientific_name, common_name="Spider mite")
        return None


def _matcher() -> IpmDiagnosisMatcher:
    return IpmDiagnosisMatcher(_FakeIpmRepo())


class TestDiseaseMatching:
    def test_known_disease_resolves_key(self):
        assert _matcher().match_disease_key("Alternaria solani") == "disease_early_blight"

    def test_unknown_disease_is_none(self):
        assert _matcher().match_disease_key("Unknownus fictus") is None

    def test_none_scientific_name_is_none(self):
        assert _matcher().match_disease_key(None) is None


class TestPestMatching:
    def test_known_pest_resolves_key(self):
        assert _matcher().match_pest_key("Tetranychus urticae") == "pest_spider_mite"

    def test_unknown_pest_is_none(self):
        assert _matcher().match_pest_key("Nonexistent") is None


class TestSymptomSlug:
    def test_deficiency_label_bridges_to_symptom_slug(self):
        assert _matcher().match_symptom_slug("nitrogen_deficiency") == "nitrogen_deficiency"

    def test_empty_label_is_none(self):
        assert _matcher().match_symptom_slug("") is None
