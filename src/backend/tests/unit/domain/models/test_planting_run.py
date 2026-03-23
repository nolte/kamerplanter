import pytest
from pydantic import ValidationError

from app.common.enums import PlantingRunStatus, PlantingRunType
from app.domain.models.planting_run import ALLOWED_STATUS_TRANSITIONS, PlantingRun, PlantingRunEntry


class TestPlantingRun:
    def test_valid_monoculture(self):
        run = PlantingRun(name="Tomatoes 2026", run_type=PlantingRunType.MONOCULTURE)
        assert run.status == PlantingRunStatus.PLANNED
        assert run.run_type == PlantingRunType.MONOCULTURE

    def test_clone_without_source_raises(self):
        with pytest.raises(ValidationError, match="source_plant_key"):
            PlantingRun(name="Clones", run_type=PlantingRunType.CLONE)

    def test_clone_with_source(self):
        run = PlantingRun(
            name="Clones",
            run_type=PlantingRunType.CLONE,
            source_plant_key="plant_123",
        )
        assert run.source_plant_key == "plant_123"

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            PlantingRun(name="Test", run_type=PlantingRunType.MONOCULTURE, status="invalid")

    def test_name_too_short(self):
        with pytest.raises(ValidationError):
            PlantingRun(name="", run_type=PlantingRunType.MONOCULTURE)

    def test_key_alias(self):
        run = PlantingRun(name="Test", run_type=PlantingRunType.MONOCULTURE, **{"_key": "abc123"})
        assert run.key == "abc123"


class TestPlantingRunEntry:
    def test_valid_entry(self):
        entry = PlantingRunEntry(species_key="sp1", quantity=10, id_prefix="TOM")
        assert entry.quantity == 10

    def test_invalid_prefix_lowercase(self):
        with pytest.raises(ValidationError, match="id_prefix"):
            PlantingRunEntry(species_key="sp1", quantity=5, id_prefix="tom")

    def test_invalid_prefix_too_short(self):
        with pytest.raises(ValidationError, match="id_prefix"):
            PlantingRunEntry(species_key="sp1", quantity=5, id_prefix="T")

    def test_invalid_prefix_too_long(self):
        with pytest.raises(ValidationError, match="id_prefix"):
            PlantingRunEntry(species_key="sp1", quantity=5, id_prefix="TOMATO")

    def test_invalid_prefix_digits(self):
        with pytest.raises(ValidationError, match="id_prefix"):
            PlantingRunEntry(species_key="sp1", quantity=5, id_prefix="TO1")

    def test_quantity_zero(self):
        with pytest.raises(ValidationError):
            PlantingRunEntry(species_key="sp1", quantity=0, id_prefix="TOM")

    def test_spacing(self):
        entry = PlantingRunEntry(species_key="sp1", quantity=5, id_prefix="TOM", spacing_cm=30.0)
        assert entry.spacing_cm == 30.0


class TestAllowedStatusTransitions:
    def test_planned_can_go_active(self):
        assert PlantingRunStatus.ACTIVE in ALLOWED_STATUS_TRANSITIONS[PlantingRunStatus.PLANNED]

    def test_planned_can_go_cancelled(self):
        assert PlantingRunStatus.CANCELLED in ALLOWED_STATUS_TRANSITIONS[PlantingRunStatus.PLANNED]

    def test_planned_cannot_go_completed(self):
        assert PlantingRunStatus.COMPLETED not in ALLOWED_STATUS_TRANSITIONS[PlantingRunStatus.PLANNED]

    def test_active_can_go_harvesting(self):
        assert PlantingRunStatus.HARVESTING in ALLOWED_STATUS_TRANSITIONS[PlantingRunStatus.ACTIVE]

    def test_active_can_go_completed(self):
        assert PlantingRunStatus.COMPLETED in ALLOWED_STATUS_TRANSITIONS[PlantingRunStatus.ACTIVE]

    def test_completed_is_terminal(self):
        assert ALLOWED_STATUS_TRANSITIONS[PlantingRunStatus.COMPLETED] == []

    def test_cancelled_is_terminal(self):
        assert ALLOWED_STATUS_TRANSITIONS[PlantingRunStatus.CANCELLED] == []
