from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.domain.engines.crop_rotation_validator import CropRotationValidator
from app.domain.models.species import Species

#: Every slot read behind the validator is tenant-scoped (#927), so the tests
#: name a tenant. The assertions below then also pin that the tenant reaches
#: the repository rather than being dropped on the way.
TENANT_KEY = "tenant-a"


def _make_species(key: str, family_key: str) -> Species:
    return Species(scientific_name=f"Test {key}", genus="Test", family_key=family_key, _key=key)


def _make_plant(species_key: str):
    plant = MagicMock()
    plant.species_key = species_key
    return plant


@pytest.fixture(autouse=True)
def family_repo(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Serve the engine's family lookup from a fake instead of the real database.

    ``validate_planting`` reaches into the DI container for the botanical-family
    repository (``get_family_repo()``) and wraps the call in ``except Exception:
    pass``. Until #978 that meant every test here opened a real ArangoDB
    connection: green on a machine with the dev stack up — reading the dev
    database — and ~18 s of connection retries per test everywhere else, with the
    swallowed failure leaving ``planned_family`` at ``None`` either way.

    The fake reproduces that ``None`` by default, so the existing expectations
    still describe what the engine does, and lets a test opt into a real family.
    """
    repo = MagicMock()
    repo.get_by_key.return_value = None
    monkeypatch.setattr("app.common.dependencies.get_family_repo", lambda: repo)
    return repo


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

        results = self.validator.validate_planting("slot1", "sp1", tenant_key=TENANT_KEY)
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

        results = self.validator.validate_planting("slot1", "sp1", tenant_key=TENANT_KEY)
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

        results = self.validator.validate_planting("slot1", "sp1", tenant_key=TENANT_KEY)
        assert any(r.severity == "OK" for r in results)
        ok_result = next(r for r in results if r.severity == "OK")
        assert ok_result.rotation_benefit is not None
        assert ok_result.rotation_benefit["benefit_score"] == 0.9

    def test_info_no_specific_relationship(self):
        """No history matches should return INFO."""
        planned = _make_species("sp1", "fam_a")

        self.species_repo.get_by_key = lambda k: planned if k == "sp1" else None
        self.plant_repo.get_history_by_slot.return_value = []

        results = self.validator.validate_planting("slot1", "sp1", tenant_key=TENANT_KEY)
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
            self.validator.validate_or_raise("slot1", "sp1", tenant_key=TENANT_KEY)

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
        self.validator.validate_or_raise("slot1", "sp1", tenant_key=TENANT_KEY)

    def test_species_not_found(self):
        """Missing species should return CRITICAL."""
        self.species_repo.get_by_key.return_value = None

        results = self.validator.validate_planting("slot1", "sp_missing", tenant_key=TENANT_KEY)
        assert results[0].severity == "CRITICAL"
        assert "not found" in results[0].message

    def test_slot_history_is_read_within_the_callers_tenant(self):
        """The tenant reaches the repository, it is not dropped in the engine (#927).

        The rotation verdict names the botanical families previously grown in the
        bed. Reading that history unscoped would describe another tenant's slot,
        so the engine must forward the tenant it was given.
        """
        planned = _make_species("sp1", "fam_a")
        self.species_repo.get_by_key = lambda k: {"sp1": planned}.get(k)
        self.plant_repo.get_history_by_slot.return_value = []
        self.graph_repo.get_pest_risks.return_value = []
        self.graph_repo.get_rotation_successors.return_value = []

        self.validator.validate_planting("slot1", "sp1", tenant_key=TENANT_KEY)

        assert self.plant_repo.get_history_by_slot.call_args.kwargs["tenant_key"] == TENANT_KEY

    def test_nitrogen_fixing_family_annotates_every_result(self, family_repo):
        """A nitrogen-fixing planned family adds the soil-benefit note to each result.

        Never covered before #978: the family lookup died in a swallowed
        connection error, so ``planned_family`` was always ``None`` here and this
        branch never executed in a test run.
        """
        planned = _make_species("sp1", "fam_a")
        past = _make_species("sp2", "fam_a")

        family_repo.get_by_key.return_value = SimpleNamespace(nitrogen_fixing=True)
        self.species_repo.get_by_key = lambda k: {"sp1": planned, "sp2": past}.get(k)
        self.plant_repo.get_history_by_slot.return_value = [_make_plant("sp2")]
        self.graph_repo.get_pest_risks.return_value = []
        self.graph_repo.get_rotation_successors.return_value = []

        results = self.validator.validate_planting("slot1", "sp1", tenant_key=TENANT_KEY)

        assert family_repo.get_by_key.call_args.args == ("fam_a",)
        assert results
        assert all(r.nitrogen_benefit == "Nitrogen-fixing species improves soil for subsequent crops" for r in results)

    def test_no_graph_repo(self):
        """Validator without graph_repo should still work (no pest/rotation checks)."""
        validator = CropRotationValidator(self.plant_repo, self.species_repo, None)
        planned = _make_species("sp1", "fam_a")
        past = _make_species("sp2", "fam_b")

        self.species_repo.get_by_key = lambda k: {"sp1": planned, "sp2": past}.get(k)
        self.plant_repo.get_history_by_slot.return_value = [_make_plant("sp2")]

        results = validator.validate_planting("slot1", "sp1", tenant_key=TENANT_KEY)
        assert results[0].severity == "INFO"
