"""A watering confirmation cannot complete, or cite, another tenant's task or run — #1864 sweep (L8).

``confirm`` / ``quick-confirm`` on watering events and watering logs took
``run_key`` and ``task_key`` from the body. The task was loaded unscoped and
marked ``COMPLETED`` — any tenant's — and on the log path any ``run_key``
worked (an empty plant list still produced a log). The run is now resolved
under the tenant first (404); the task stays optional — the run's watering
schedule confirms by *date* and sends the date as ``task_key`` — but only the
tenant's own task is completed, and a foreign task is treated exactly like a
missing one.
The services are the real ones; the repositories are doubles that keep the
task and run documents the stores hold.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import PlantingRunType
from app.common.exceptions import NotFoundError
from app.domain.engines.watering_engine import WateringEngine
from app.domain.models.planting_run import PlantingRun
from app.domain.models.task import Task
from app.domain.services.watering_log_service import WateringLogService
from app.domain.services.watering_service import WateringService

TENANT = "t_a"


class _Runs:
    def __init__(self) -> None:
        self.runs = {
            "run_a": PlantingRun(_key="run_a", tenant_key="t_a", name="A", run_type=PlantingRunType.MONOCULTURE),
            "run_b": PlantingRun(_key="run_b", tenant_key="t_b", name="B", run_type=PlantingRunType.MONOCULTURE),
        }

    def get_by_key(self, key: str):
        return self.runs.get(key)

    def get_run_nutrient_plan_key(self, run_key: str):
        return None

    def get_run_plants(self, run_key: str, include_detached: bool = False):
        return [{"_key": f"plant_{run_key}", "slot_key": f"slot_{run_key}"}]


class _Tasks:
    def __init__(self) -> None:
        self.tasks = {
            "task_a": Task(_key="task_a", tenant_key="t_a", name="Gießen A"),
            "task_b": Task(_key="task_b", tenant_key="t_b", name="Gießen B"),
        }
        self.updated: list[str] = []

    def get_by_key(self, key: str):
        return self.tasks.get(key)

    def update_fields(self, key: str, fields: dict) -> None:
        self.updated.append(key)


class _Store:
    def __init__(self) -> None:
        self.created: list = []

    def create(self, item):
        self.created.append(item)
        return item


def _event_service(tasks: _Tasks, store: _Store) -> WateringService:
    return WateringService(
        repo=store, engine=MagicMock(), site_repo=MagicMock(), run_repo=_Runs(), task_repo=tasks, feeding_repo=_Store()
    )  # type: ignore[arg-type]


def _log_service(tasks: _Tasks, store: _Store) -> WateringLogService:
    return WateringLogService(store, WateringEngine(), site_repo=MagicMock(), run_repo=_Runs(), task_repo=tasks)  # type: ignore[arg-type]


_FACTORIES = {"events": _event_service, "logs": _log_service}


@pytest.mark.parametrize("path", sorted(_FACTORIES))
@pytest.mark.parametrize("run", ["run_b", "no-such-run"], ids=["foreign-run", "unknown-run"])
def test_a_foreign_or_unknown_run_is_refused_before_anything_is_written(path: str, run: str) -> None:
    tasks, store = _Tasks(), _Store()
    service = _FACTORIES[path](tasks, store)

    with pytest.raises(NotFoundError):
        service.confirm_watering(run, "task_a", tenant_key=TENANT)
    with pytest.raises(NotFoundError):
        service.quick_confirm_watering(run, "task_a", tenant_key=TENANT)

    assert tasks.updated == []
    assert store.created == []


@pytest.mark.parametrize("path", sorted(_FACTORIES))
@pytest.mark.parametrize(
    "task", ["task_b", "2026-09-26", "no-such-task"], ids=["foreign-task", "schedule-date", "unknown"]
)
def test_a_task_that_is_not_the_tenants_is_never_completed_and_looks_like_a_missing_one(path: str, task: str) -> None:
    tasks, store = _Tasks(), _Store()

    result = _FACTORIES[path](tasks, store).confirm_watering("run_a", task, tenant_key=TENANT)

    assert tasks.updated == []
    assert result["task_completed"] is False
    assert len(store.created) == 1  # the confirmation of the own run still happens


@pytest.mark.parametrize("path", sorted(_FACTORIES))
def test_the_tenants_own_task_is_completed(path: str) -> None:
    tasks, store = _Tasks(), _Store()

    result = _FACTORIES[path](tasks, store).confirm_watering("run_a", "task_a", tenant_key=TENANT)

    assert tasks.updated == ["task_a"]
    assert result["task_completed"] is True
