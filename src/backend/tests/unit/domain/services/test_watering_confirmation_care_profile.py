"""confirm_watering writes a valid CareConfirmation per plant when a care repo is wired — #1898.

Both ``WateringService.confirm_watering`` and ``WateringLogService.confirm_watering``
built ``CareConfirmation`` without the required ``care_profile_key``, so the
construction raised ``ValidationError`` whenever the run had a plant and
``care_repo`` was wired (production always wires it). The existing scope tests
build the services without a care repo and never reached the loop.

The services are the real ones, wired with a care repository double the way
``get_watering_service`` / ``get_watering_log_service`` wire one. The double
records only what the real repository receives: a ``CareConfirmation`` model —
so a confirmation that the model refuses never reaches it, exactly as in
production.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import PlantingRunType
from app.domain.engines.watering_engine import WateringEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.planting_run import PlantingRun
from app.domain.models.task import Task
from app.domain.services.watering_log_service import WateringLogService
from app.domain.services.watering_service import WateringService

TENANT = "t_a"


class _Runs:
    def __init__(self) -> None:
        self.run = PlantingRun(_key="run_a", tenant_key=TENANT, name="A", run_type=PlantingRunType.MONOCULTURE)

    def get_by_key(self, key: str):
        return self.run if key == "run_a" else None

    def get_run_nutrient_plan_key(self, run_key: str):
        return None

    def get_run_plants(self, run_key: str, include_detached: bool = False):
        return [
            {"_key": "plant_with_profile", "slot_key": "s1"},
            {"_key": "plant_without_profile", "slot_key": "s2"},
        ]


class _Tasks:
    def __init__(self) -> None:
        self.task = Task(_key="task_a", tenant_key=TENANT, name="Gießen A")
        self.updated: list[str] = []

    def get_by_key(self, key: str):
        return self.task if key == "task_a" else None

    def update_fields(self, key: str, fields: dict) -> None:
        self.updated.append(key)


class _Store:
    def create(self, item):
        return item


class _CareRepo:
    """Care repository double: only ``plant_with_profile`` owns a care profile."""

    def __init__(self) -> None:
        self.confirmations: list[CareConfirmation] = []

    def get_profile_by_plant_key(self, plant_key: str) -> CareProfile | None:
        if plant_key == "plant_with_profile":
            return CareProfile(_key="profile_1", plant_key=plant_key, tenant_key=TENANT)
        return None

    def create_confirmation(self, confirmation: CareConfirmation) -> CareConfirmation:
        assert isinstance(confirmation, CareConfirmation)
        self.confirmations.append(confirmation)
        return confirmation


def _event_service(tasks: _Tasks, care: _CareRepo) -> WateringService:
    return WateringService(
        repo=_Store(),
        engine=MagicMock(),
        site_repo=MagicMock(),
        run_repo=_Runs(),
        task_repo=tasks,
        feeding_repo=_Store(),
        care_repo=care,
    )  # type: ignore[arg-type]


def _log_service(tasks: _Tasks, care: _CareRepo) -> WateringLogService:
    return WateringLogService(
        _Store(), WateringEngine(), site_repo=MagicMock(), run_repo=_Runs(), task_repo=tasks, care_repo=care
    )  # type: ignore[arg-type]


_FACTORIES = {"events": _event_service, "logs": _log_service}


@pytest.mark.parametrize("path", sorted(_FACTORIES))
def test_confirm_writes_a_valid_confirmation_for_a_plant_with_a_profile(path: str) -> None:
    tasks, care = _Tasks(), _CareRepo()

    result = _FACTORIES[path](tasks, care).confirm_watering("run_a", "task_a", tenant_key=TENANT)

    assert result["task_completed"] is True
    assert tasks.updated == ["task_a"]
    assert [c.plant_key for c in care.confirmations] == ["plant_with_profile"]
    assert care.confirmations[0].care_profile_key == "profile_1"
    assert care.confirmations[0].task_key == "task_a"


@pytest.mark.parametrize("path", sorted(_FACTORIES))
def test_a_plant_without_a_care_profile_is_skipped_not_fatal(path: str) -> None:
    tasks, care = _Tasks(), _CareRepo()

    _FACTORIES[path](tasks, care).confirm_watering("run_a", "task_a", tenant_key=TENANT)

    assert "plant_without_profile" not in [c.plant_key for c in care.confirmations]
