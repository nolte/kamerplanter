"""Issue #367 Fix #9 — PlantingRunService.create_plants runs the same rotation +
companion checks as the single-plant path (PlantInstanceService.create_plant),
so neighbour/rotation validation is not bypassed for batch creation (R9).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import PlantingRunStatus, PlantingRunType
from app.common.exceptions import CompanionConflictError, RotationViolationError
from app.domain.models.planting_run import PlantingRun, PlantingRunEntry
from app.domain.services.planting_run_service import PlantingRunService
from tests.conftest import wire_get_or_raise

RUN_KEY = "run_1"
LOCATION_KEY = "loc_beet_a"
SPECIES_KEY = "sp_tomato"


def _fake_slot(slot_id: str, key: str):
    return SimpleNamespace(slot_id=slot_id, key=key, currently_occupied=False)


def _planned_run() -> PlantingRun:
    return PlantingRun(
        _key=RUN_KEY,
        name="Tomaten 2026",
        run_type=PlantingRunType.MONOCULTURE,
        status=PlantingRunStatus.PLANNED,
        location_key=LOCATION_KEY,
    )


def _entries() -> list[PlantingRunEntry]:
    return [
        PlantingRunEntry(_key="e1", run_key=RUN_KEY, species_key=SPECIES_KEY, quantity=2, id_prefix="TOM"),
    ]


def _build_service(*, slots: list, plant_specs: list[dict]):
    run_repo = MagicMock()
    run_repo.get_by_key.return_value = _planned_run()
    wire_get_or_raise(run_repo, "PlantingRun")
    run_repo.get_entries.return_value = _entries()
    run_repo.get_existing_ids_at_location.return_value = set()

    plant_repo = MagicMock()
    plant_repo.create.side_effect = lambda plant: plant.model_copy(update={"key": plant.instance_id})

    site_repo = MagicMock()
    site_repo.get_slots_by_location.return_value = slots

    engine = MagicMock()
    engine.validate_run_type_constraints.return_value = None
    engine.generate_plant_ids.return_value = plant_specs

    rotation = MagicMock()
    companion = MagicMock()

    service = PlantingRunService(
        run_repo=run_repo,
        plant_repo=plant_repo,
        engine=engine,
        site_repo=site_repo,
        rotation_validator=rotation,
        companion_engine=companion,
    )
    return service, plant_repo, rotation, companion


def _specs(count: int) -> list[dict]:
    return [{"instance_id": f"TOM-{i}", "species_key": SPECIES_KEY, "cultivar_key": None} for i in range(1, count + 1)]


class TestCreatePlantsChecks:
    def test_incompatible_companion_raises_and_creates_nothing(self):
        service, plant_repo, _rotation, companion = _build_service(
            slots=[_fake_slot("A1", "slot_a1"), _fake_slot("A2", "slot_a2")],
            plant_specs=_specs(2),
        )
        companion.check_or_raise.side_effect = CompanionConflictError(SPECIES_KEY, "neighbors")

        with pytest.raises(CompanionConflictError):
            service.create_plants(RUN_KEY)

        # Validated up-front — no partial batch is written on a conflict.
        plant_repo.create.assert_not_called()

    def test_rotation_violation_raises_and_creates_nothing(self):
        service, plant_repo, rotation, _companion = _build_service(
            slots=[_fake_slot("A1", "slot_a1"), _fake_slot("A2", "slot_a2")],
            plant_specs=_specs(2),
        )
        rotation.validate_or_raise.side_effect = RotationViolationError("Solanaceae", "slot_a1", 3)

        with pytest.raises(RotationViolationError):
            service.create_plants(RUN_KEY)

        plant_repo.create.assert_not_called()

    def test_compatible_batch_creates_plants_and_runs_checks_per_slot(self):
        service, plant_repo, rotation, companion = _build_service(
            slots=[_fake_slot("A1", "slot_a1"), _fake_slot("A2", "slot_a2")],
            plant_specs=_specs(2),
        )

        result = service.create_plants(RUN_KEY)

        assert result["created_count"] == 2
        assert plant_repo.create.call_count == 2
        # Same argument order as the single-plant path.
        rotation.validate_or_raise.assert_any_call("slot_a1", SPECIES_KEY)
        rotation.validate_or_raise.assert_any_call("slot_a2", SPECIES_KEY)
        companion.check_or_raise.assert_any_call(SPECIES_KEY, "slot_a1")
        companion.check_or_raise.assert_any_call(SPECIES_KEY, "slot_a2")

    def test_instance_without_slot_skips_checks_without_crashing(self):
        # Two plants, but only one available slot -> the second instance has no
        # slot_key and must skip the checks (mirror the ``if plant.slot_key`` guard).
        service, plant_repo, rotation, companion = _build_service(
            slots=[_fake_slot("A1", "slot_a1")],
            plant_specs=_specs(2),
        )

        result = service.create_plants(RUN_KEY)

        assert result["created_count"] == 2
        assert plant_repo.create.call_count == 2
        # Checks ran only for the single slot-assigned instance.
        rotation.validate_or_raise.assert_called_once_with("slot_a1", SPECIES_KEY)
        companion.check_or_raise.assert_called_once_with(SPECIES_KEY, "slot_a1")

    def test_checks_skipped_when_engines_unwired(self):
        # Backward-compat: a service built without the engines still creates plants.
        run_repo = MagicMock()
        run_repo.get_by_key.return_value = _planned_run()
        wire_get_or_raise(run_repo, "PlantingRun")
        run_repo.get_entries.return_value = _entries()
        run_repo.get_existing_ids_at_location.return_value = set()

        plant_repo = MagicMock()
        plant_repo.create.side_effect = lambda plant: plant.model_copy(update={"key": plant.instance_id})

        site_repo = MagicMock()
        site_repo.get_slots_by_location.return_value = [_fake_slot("A1", "slot_a1")]

        engine = MagicMock()
        engine.validate_run_type_constraints.return_value = None
        engine.generate_plant_ids.return_value = _specs(1)

        service = PlantingRunService(
            run_repo=run_repo,
            plant_repo=plant_repo,
            engine=engine,
            site_repo=site_repo,
        )

        result = service.create_plants(RUN_KEY)
        assert result["created_count"] == 1
