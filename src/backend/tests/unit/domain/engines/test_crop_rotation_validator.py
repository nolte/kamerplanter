from unittest.mock import MagicMock

import pytest

from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.models.species import Species


def _make_species(key: str, family_key: str) -> Species:
    return Species(scientific_name=f"Test {key}", genus="Test", family_key=family_key, _key=key)


def _make_plant(species_key: str):
    plant = MagicMock()
    plant.species_key = species_key
    return plant


class TestCropRotationValidator:
    def setup_method(self):
        self.plant_repo = MagicMock()
        self.species_repo = MagicMock()
        self.graph_repo = MagicMock()
        self.validator = CropRotationValidator(self.plant_repo, self.species_repo, self.graph_repo)

    def test_critical_same_family(self):
        """Same family in history should return CRITICAL."""
        planned = _make_species("sp1", "fam_a")
        past = _make_species("sp2", "fam_a")

        self.species_repo.get_by_key = lambda k: {"sp1": planned, "sp2": past}.get(k)
        self.plant_repo.get_history_by_slot.return_value = [_make_plant("sp2")]
        self.graph_repo.get_pest_risks.return_value = []
        self.graph_repo.get_rotation_successors.return_value = []

        results = self.validator.validate_planting("slot1", "sp1")
        assert any(r.severity == "CRITICAL" for r in results)
        assert "Same family" in results[0].message

    def test_warning_shared_pest_risk_high(self):
        """High pest risk between families should return WARNING."""
        planned = _make_species("sp1", "fam_a")
        past = _make_species("sp2", "fam_b")

        self.species_repo.get_by_key = lambda k: {"sp1": planned, "sp2": past}.get(k)
        self.plant_repo.get_history_by_slot.return_value = [_make_plant("sp2")]
        self.graph_repo.get_pest_risks.return_value = [
            {"family": {"_key": "fam_b"}, "shared_pests": ["aphids"], "shared_diseases": [], "risk_level": "high"},
        ]
        self.graph_repo.get_rotation_successors.return_value = []

        results = self.validator.validate_planting("slot1", "sp1")
        assert any(r.severity == "WARNING" for r in results)

    def test_ok_good_rotation(self):
        """Recommended successor should return OK with benefit info."""
        planned = _make_species("sp1", "fam_a")
        past = _make_species("sp2", "fam_b")

        self.species_repo.get_by_key = lambda k: {"sp1": planned, "sp2": past}.get(k)
        self.plant_repo.get_history_by_slot.return_value = [_make_plant("sp2")]
        self.graph_repo.get_pest_risks.return_value = []
        self.graph_repo.get_rotation_successors.return_value = [
            {"family": {"_key": "fam_a"}, "benefit_score": 0.9, "benefit_reason": "nitrogen_fixation"},
        ]

        results = self.validator.validate_planting("slot1", "sp1")
        assert any(r.severity == "OK" for r in results)
        ok_result = next(r for r in results if r.severity == "OK")
        assert ok_result.rotation_benefit is not None
        assert ok_result.rotation_benefit["benefit_score"] == 0.9

    def test_info_no_specific_relationship(self):
        """No history matches should return INFO."""
        planned = _make_species("sp1", "fam_a")

        self.species_repo.get_by_key = lambda k: planned if k == "sp1" else None
        self.plant_repo.get_history_by_slot.return_value = []

        results = self.validator.validate_planting("slot1", "sp1")
        assert len(results) == 1
        assert results[0].severity == "INFO"

    def test_validate_or_raise_critical(self):
        """validate_or_raise should raise on CRITICAL."""
        planned = _make_species("sp1", "fam_a")
        past = _make_species("sp2", "fam_a")

        self.species_repo.get_by_key = lambda k: {"sp1": planned, "sp2": past}.get(k)
        self.plant_repo.get_history_by_slot.return_value = [_make_plant("sp2")]
        self.graph_repo.get_pest_risks.return_value = []
        self.graph_repo.get_rotation_successors.return_value = []

        from app.common.exceptions import RotationViolationError

        with pytest.raises(RotationViolationError):
            self.validator.validate_or_raise("slot1", "sp1")

    def test_validate_or_raise_ok(self):
        """validate_or_raise should not raise when OK."""
        planned = _make_species("sp1", "fam_a")
        past = _make_species("sp2", "fam_b")

        self.species_repo.get_by_key = lambda k: {"sp1": planned, "sp2": past}.get(k)
        self.plant_repo.get_history_by_slot.return_value = [_make_plant("sp2")]
        self.graph_repo.get_pest_risks.return_value = []
        self.graph_repo.get_rotation_successors.return_value = [
            {"family": {"_key": "fam_a"}, "benefit_score": 0.9, "benefit_reason": "nitrogen_fixation"},
        ]

        # Should not raise
        self.validator.validate_or_raise("slot1", "sp1")

    def test_species_not_found(self):
        """Missing species should return CRITICAL."""
        self.species_repo.get_by_key.return_value = None

        results = self.validator.validate_planting("slot1", "sp_missing")
        assert results[0].severity == "CRITICAL"
        assert "not found" in results[0].message

    def test_no_graph_repo(self):
        """Validator without graph_repo should still work (no pest/rotation checks)."""
        validator = CropRotationValidator(self.plant_repo, self.species_repo, None)
        planned = _make_species("sp1", "fam_a")
        past = _make_species("sp2", "fam_b")

        self.species_repo.get_by_key = lambda k: {"sp1": planned, "sp2": past}.get(k)
        self.plant_repo.get_history_by_slot.return_value = [_make_plant("sp2")]

        results = validator.validate_planting("slot1", "sp1")
        assert results[0].severity == "INFO"
