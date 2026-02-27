from unittest.mock import MagicMock

from app.domain.engines.companion_planting_engine import CompanionPlantingEngine
from app.domain.models.species import Species


def _make_species(key: str, family_key: str = "") -> Species:
    return Species(scientific_name=f"Test {key}", genus="Test", family_key=family_key, _key=key)


class TestCompanionPlantingRecommendations:
    def setup_method(self):
        self.graph_repo = MagicMock()
        self.plant_repo = MagicMock()
        self.species_repo = MagicMock()
        self.engine = CompanionPlantingEngine(self.graph_repo, self.plant_repo, self.species_repo)

    def test_species_level_match(self):
        """Species-level matches should return match_level='species' with original score."""
        self.graph_repo.get_compatible_species.return_value = [
            {"species": {"_key": "sp2", "scientific_name": "Basil"}, "score": 0.9},
        ]

        result = self.engine.get_companion_recommendations("sp1")

        assert result["match_level"] == "species"
        assert len(result["matches"]) == 1
        assert result["matches"][0]["score"] == 0.9
        assert result["matches"][0]["match_level"] == "species"

    def test_family_fallback(self):
        """No species matches should trigger family-level fallback with score * 0.8."""
        self.graph_repo.get_compatible_species.return_value = []
        self.species_repo.get_by_key.return_value = _make_species("sp1", "fam_a")
        self.graph_repo.get_family_compatible.return_value = [
            {"family": {"_key": "fam_b"}, "compatibility_score": 0.85,
             "benefit_type": "nitrogen_fixation", "notes": ""},
        ]
        self.graph_repo.get_species_by_family.return_value = [
            {"_key": "sp3", "scientific_name": "Bean"},
        ]

        result = self.engine.get_companion_recommendations("sp1")

        assert result["match_level"] == "family"
        assert len(result["matches"]) == 1
        assert result["matches"][0]["score"] == round(0.85 * 0.8, 2)
        assert result["matches"][0]["match_level"] == "family"
        assert result["matches"][0]["benefit_type"] == "nitrogen_fixation"

    def test_no_match_at_all(self):
        """No species or family matches should return empty list."""
        self.graph_repo.get_compatible_species.return_value = []
        self.species_repo.get_by_key.return_value = _make_species("sp1", "fam_a")
        self.graph_repo.get_family_compatible.return_value = []

        result = self.engine.get_companion_recommendations("sp1")

        assert result["matches"] == []
        assert result["match_level"] == "species"

    def test_family_fallback_excludes_self(self):
        """Family fallback should not include the queried species itself."""
        self.graph_repo.get_compatible_species.return_value = []
        self.species_repo.get_by_key.return_value = _make_species("sp1", "fam_a")
        self.graph_repo.get_family_compatible.return_value = [
            {"family": {"_key": "fam_a"}, "compatibility_score": 0.7, "benefit_type": "pest_deterrent", "notes": ""},
        ]
        self.graph_repo.get_species_by_family.return_value = [
            {"_key": "sp1", "scientific_name": "Self"},
            {"_key": "sp2", "scientific_name": "Other"},
        ]

        result = self.engine.get_companion_recommendations("sp1")

        assert len(result["matches"]) == 1
        assert result["matches"][0]["species_key"] == "sp2"

    def test_no_family_assigned(self):
        """Species without family should return empty matches."""
        self.graph_repo.get_compatible_species.return_value = []
        self.species_repo.get_by_key.return_value = _make_species("sp1", "")

        result = self.engine.get_companion_recommendations("sp1")

        assert result["matches"] == []
