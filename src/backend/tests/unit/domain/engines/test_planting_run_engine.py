import pytest

from app.common.enums import EntryRole, PlantingRunStatus, PlantingRunType
from app.common.exceptions import InvalidStatusTransitionError
from app.domain.engines.planting_run_engine import PlantingRunEngine
from app.domain.models.planting_run import PlantingRunEntry


@pytest.fixture
def engine():
    return PlantingRunEngine()


class TestValidateStatusTransition:
    def test_planned_to_active(self, engine):
        engine.validate_status_transition(PlantingRunStatus.PLANNED, PlantingRunStatus.ACTIVE)

    def test_planned_to_cancelled(self, engine):
        engine.validate_status_transition(PlantingRunStatus.PLANNED, PlantingRunStatus.CANCELLED)

    def test_active_to_harvesting(self, engine):
        engine.validate_status_transition(PlantingRunStatus.ACTIVE, PlantingRunStatus.HARVESTING)

    def test_active_to_completed(self, engine):
        engine.validate_status_transition(PlantingRunStatus.ACTIVE, PlantingRunStatus.COMPLETED)

    def test_active_to_cancelled(self, engine):
        engine.validate_status_transition(PlantingRunStatus.ACTIVE, PlantingRunStatus.CANCELLED)

    def test_harvesting_to_completed(self, engine):
        engine.validate_status_transition(PlantingRunStatus.HARVESTING, PlantingRunStatus.COMPLETED)

    def test_planned_to_completed_raises(self, engine):
        with pytest.raises(InvalidStatusTransitionError):
            engine.validate_status_transition(PlantingRunStatus.PLANNED, PlantingRunStatus.COMPLETED)

    def test_completed_to_active_raises(self, engine):
        with pytest.raises(InvalidStatusTransitionError):
            engine.validate_status_transition(PlantingRunStatus.COMPLETED, PlantingRunStatus.ACTIVE)

    def test_cancelled_to_active_raises(self, engine):
        with pytest.raises(InvalidStatusTransitionError):
            engine.validate_status_transition(PlantingRunStatus.CANCELLED, PlantingRunStatus.ACTIVE)

    def test_active_to_planned_raises(self, engine):
        with pytest.raises(InvalidStatusTransitionError):
            engine.validate_status_transition(PlantingRunStatus.ACTIVE, PlantingRunStatus.PLANNED)


class TestGeneratePlantIds:
    def test_monoculture_20_ids(self, engine):
        entries = [
            PlantingRunEntry(species_key="sp1", quantity=20, id_prefix="TOM"),
        ]
        result = engine.generate_plant_ids("TENT01", entries, set())
        assert len(result) == 20
        ids = [r["instance_id"] for r in result]
        assert ids[0] == "TENT01_TOM_01"
        assert ids[19] == "TENT01_TOM_20"
        assert len(set(ids)) == 20  # all unique

    def test_mixed_culture_different_prefixes(self, engine):
        entries = [
            PlantingRunEntry(species_key="sp1", quantity=3, id_prefix="TOM"),
            PlantingRunEntry(species_key="sp2", quantity=2, id_prefix="BAS", role=EntryRole.COMPANION),
        ]
        result = engine.generate_plant_ids("BED01", entries, set())
        assert len(result) == 5
        tom_ids = [r for r in result if r["species_key"] == "sp1"]
        bas_ids = [r for r in result if r["species_key"] == "sp2"]
        assert len(tom_ids) == 3
        assert len(bas_ids) == 2
        assert tom_ids[0]["instance_id"] == "BED01_TOM_01"
        assert bas_ids[0]["instance_id"] == "BED01_BAS_01"

    def test_collision_avoidance(self, engine):
        entries = [
            PlantingRunEntry(species_key="sp1", quantity=3, id_prefix="TOM"),
        ]
        existing = {"TENT01_TOM_01", "TENT01_TOM_02"}
        result = engine.generate_plant_ids("TENT01", entries, existing)
        assert len(result) == 3
        ids = [r["instance_id"] for r in result]
        assert "TENT01_TOM_01" not in ids
        assert "TENT01_TOM_02" not in ids
        assert ids[0] == "TENT01_TOM_03"
        assert ids[1] == "TENT01_TOM_04"
        assert ids[2] == "TENT01_TOM_05"

    def test_preserves_species_and_cultivar(self, engine):
        entries = [
            PlantingRunEntry(species_key="sp1", cultivar_key="cv1", quantity=1, id_prefix="TOM"),
        ]
        result = engine.generate_plant_ids("LOC", entries, set())
        assert result[0]["species_key"] == "sp1"
        assert result[0]["cultivar_key"] == "cv1"


class TestFilterTransitionEligible:
    def test_basic_split(self, engine):
        plants = [
            {"_key": "p1", "current_phase": "seedling", "removed_on": None},
            {"_key": "p2", "current_phase": "vegetative", "removed_on": None},
            {"_key": "p3", "current_phase": "vegetative", "removed_on": None},
        ]
        eligible, skipped = engine.filter_transition_eligible(plants, "vegetative")
        assert len(eligible) == 1
        assert eligible[0]["_key"] == "p1"
        assert len(skipped) == 2

    def test_exclude_keys(self, engine):
        plants = [
            {"_key": "p1", "current_phase": "seedling", "removed_on": None},
            {"_key": "p2", "current_phase": "seedling", "removed_on": None},
        ]
        eligible, skipped = engine.filter_transition_eligible(plants, "vegetative", exclude_keys={"p1"})
        assert len(eligible) == 1
        assert eligible[0]["_key"] == "p2"
        assert len(skipped) == 1

    def test_removed_plants_skipped(self, engine):
        plants = [
            {"_key": "p1", "current_phase": "seedling", "removed_on": "2026-01-01"},
        ]
        eligible, skipped = engine.filter_transition_eligible(plants, "vegetative")
        assert len(eligible) == 0
        assert len(skipped) == 1

    def test_empty_list(self, engine):
        eligible, skipped = engine.filter_transition_eligible([], "vegetative")
        assert eligible == []
        assert skipped == []


class TestValidateRunTypeConstraints:
    def test_clone_without_source_raises(self, engine):
        entries = [PlantingRunEntry(species_key="sp1", quantity=5, id_prefix="CL")]
        with pytest.raises(ValueError, match="source_plant_key"):
            engine.validate_run_type_constraints(PlantingRunType.CLONE, entries, None)

    def test_clone_multiple_entries_raises(self, engine):
        entries = [
            PlantingRunEntry(species_key="sp1", quantity=5, id_prefix="CL"),
            PlantingRunEntry(species_key="sp2", quantity=3, id_prefix="XX"),
        ]
        with pytest.raises(ValueError, match="exactly one"):
            engine.validate_run_type_constraints(PlantingRunType.CLONE, entries, "plant_123")

    def test_monoculture_multiple_entries_raises(self, engine):
        entries = [
            PlantingRunEntry(species_key="sp1", quantity=5, id_prefix="TOM"),
            PlantingRunEntry(species_key="sp2", quantity=3, id_prefix="BAS"),
        ]
        with pytest.raises(ValueError, match="exactly one"):
            engine.validate_run_type_constraints(PlantingRunType.MONOCULTURE, entries)

    def test_mixed_single_entry_raises(self, engine):
        entries = [PlantingRunEntry(species_key="sp1", quantity=5, id_prefix="TOM")]
        with pytest.raises(ValueError, match="at least two"):
            engine.validate_run_type_constraints(PlantingRunType.MIXED_CULTURE, entries)

    def test_valid_monoculture(self, engine):
        entries = [PlantingRunEntry(species_key="sp1", quantity=20, id_prefix="TOM")]
        engine.validate_run_type_constraints(PlantingRunType.MONOCULTURE, entries)

    def test_valid_mixed(self, engine):
        entries = [
            PlantingRunEntry(species_key="sp1", quantity=10, id_prefix="TOM"),
            PlantingRunEntry(species_key="sp2", quantity=5, id_prefix="BAS", role=EntryRole.COMPANION),
        ]
        engine.validate_run_type_constraints(PlantingRunType.MIXED_CULTURE, entries)

    def test_valid_clone(self, engine):
        entries = [PlantingRunEntry(species_key="sp1", quantity=10, id_prefix="CL")]
        engine.validate_run_type_constraints(PlantingRunType.CLONE, entries, "plant_123")
