"""#580 (bug/security) — every care/task watering log carries its tenant_key.

Root cause: watering logs built in the care-reminder and task-completion paths were
constructed WITHOUT a ``tenant_key`` and persisted with the model default ``""``.
The global ``GET /watering-logs`` view filters strictly on ``tenant_key`` and
dropped these empty-tenant orphans, so a watering logged via a Pflege-/Task-flow
never showed up in the tenant's global Gießprotokoll — while the per-plant view
(which did not filter at all) still listed them.

These tests pin the fix on both sides:

* the three construction sites (``confirm_reminder``, ``complete_care_task_with_log``,
  ``WateringLogService.confirm_watering``) stamp a real ``tenant_key`` — from the
  caller when supplied, otherwise resolved from the plant;
* a stamped log is then visible in BOTH the global tenant-scoped list AND the
  tenant-scoped per-plant view (the divergence the bug created is closed);
* the per-plant repository query is fail-closed (SEC-B4): an unscoped read raises
  and never leaks cross-tenant logs.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import ReminderType
from app.data_access.arango.watering_log_repository import ArangoWateringLogRepository
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.engines.watering_engine import WateringEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.watering_log import WateringLog
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.watering_log_service import WateringLogService

PLANT_KEY = "plant-1"
TENANT = "tenant-A"


class FakeWateringLogRepo:
    """In-memory watering-log repo that mirrors the tenant-scoping contract.

    ``get_all`` and ``get_by_plant`` filter on ``tenant_key`` exactly like the real
    Arango repository (SEC-B4), so a test can prove a stamped log surfaces in both
    scoped views — and an empty-tenant log would surface in neither.
    """

    def __init__(self) -> None:
        self._logs: list[WateringLog] = []
        self._seq = 0

    def create(self, log: WateringLog) -> WateringLog:
        self._seq += 1
        stored = WateringLog(**{**log.model_dump(), "_key": f"log-{self._seq}"})
        self._logs.append(stored)
        return stored

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str = "",
        *,
        all_tenants: bool = False,
    ) -> tuple[list[WateringLog], int]:
        items = [log for log in self._logs if all_tenants or (tenant_key and log.tenant_key == tenant_key)]
        return items[offset : offset + limit], len(items)

    def get_by_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str = "",
        *,
        all_tenants: bool = False,
    ) -> list[WateringLog]:
        if not tenant_key and not all_tenants:
            raise ValueError("watering_logs is tenant-scoped: pass a tenant_key")
        items = [
            log for log in self._logs if plant_key in log.plant_keys and (all_tenants or log.tenant_key == tenant_key)
        ]
        return items[offset : offset + limit]


def _plant(tenant_key: str = TENANT) -> SimpleNamespace:
    return SimpleNamespace(
        key=PLANT_KEY,
        plant_name="Strawberry",
        instance_id="FRAGA-0712-TCJ",
        tenant_key=tenant_key,
        current_phase_key=None,
        slot_key="slot-1",
        removed_on=None,
    )


def _profile() -> CareProfile:
    return CareProfile(
        plant_key=PLANT_KEY,
        watering_interval_days=7,
        auto_create_watering_task=False,
        adaptive_learning_enabled=False,
    )


def _care_service(log_repo: FakeWateringLogRepo, plant_tenant: str = TENANT) -> tuple[CareReminderService, MagicMock]:
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = _profile()
    care_repo.create_confirmation.side_effect = lambda c: CareConfirmation(**{**c.model_dump(), "_key": "conf-1"})

    plant_repo = MagicMock()
    plant = _plant(plant_tenant)
    plant_repo.get_by_key.return_value = plant
    plant_repo.get_or_raise.return_value = plant

    service = CareReminderService(
        care_repo,
        CareReminderEngine(),
        task_repo=None,
        watering_log_repo=log_repo,
        plant_repo=plant_repo,
    )
    return service, care_repo


def _log_service(log_repo: FakeWateringLogRepo) -> WateringLogService:
    return WateringLogService(log_repo, WateringEngine(), site_repo=MagicMock())


# ── confirm_reminder ──────────────────────────────────────────────────────────


def test_confirm_reminder_stamps_caller_tenant_key() -> None:
    log_repo = FakeWateringLogRepo()
    care_service, _ = _care_service(log_repo)

    care_service.confirm_reminder(PLANT_KEY, ReminderType.WATERING, tenant_key=TENANT)

    assert len(log_repo._logs) == 1
    assert log_repo._logs[0].tenant_key == TENANT


def test_confirm_reminder_resolves_tenant_from_plant_when_caller_omits_it() -> None:
    # The REST care path (care_reminders/router) passes no tenant_key; the tenant
    # is resolved from the plant so the log is never left unbound.
    log_repo = FakeWateringLogRepo()
    care_service, _ = _care_service(log_repo)

    care_service.confirm_reminder(PLANT_KEY, ReminderType.WATERING)

    assert log_repo._logs[0].tenant_key == TENANT


def test_confirm_reminder_log_visible_in_both_global_and_per_plant_views() -> None:
    # The bug: care-path logs appeared only in the (unfiltered) per-plant view.
    # After the fix the stamped log is in BOTH tenant-scoped views.
    log_repo = FakeWateringLogRepo()
    care_service, _ = _care_service(log_repo)
    log_service = _log_service(log_repo)

    care_service.confirm_reminder(PLANT_KEY, ReminderType.WATERING, tenant_key=TENANT)

    global_logs, total = log_service.list_logs(tenant_key=TENANT)
    per_plant_logs = log_service.get_by_plant(PLANT_KEY, tenant_key=TENANT)

    assert total == 1
    assert [log.key for log in global_logs] == [log_repo._logs[0].key]
    assert [log.key for log in per_plant_logs] == [log_repo._logs[0].key]


# ── complete_care_task_with_log ───────────────────────────────────────────────


def test_complete_care_task_with_log_stamps_caller_tenant_key() -> None:
    log_repo = FakeWateringLogRepo()
    care_service, _ = _care_service(log_repo)

    care_service.complete_care_task_with_log("task-1", PLANT_KEY, ReminderType.WATERING, tenant_key=TENANT)

    assert log_repo._logs[0].tenant_key == TENANT


def test_complete_care_task_with_log_resolves_tenant_from_plant() -> None:
    log_repo = FakeWateringLogRepo()
    care_service, _ = _care_service(log_repo)

    care_service.complete_care_task_with_log("task-1", PLANT_KEY, ReminderType.FERTILIZING)

    assert log_repo._logs[0].tenant_key == TENANT


def test_complete_care_task_with_log_visible_in_both_views() -> None:
    log_repo = FakeWateringLogRepo()
    care_service, _ = _care_service(log_repo)
    log_service = _log_service(log_repo)

    care_service.complete_care_task_with_log("task-1", PLANT_KEY, ReminderType.WATERING, tenant_key=TENANT)

    global_logs, total = log_service.list_logs(tenant_key=TENANT)
    per_plant_logs = log_service.get_by_plant(PLANT_KEY, tenant_key=TENANT)

    assert total == 1
    assert global_logs and per_plant_logs
    assert global_logs[0].key == per_plant_logs[0].key


# ── WateringLogService.confirm_watering ───────────────────────────────────────


def test_confirm_watering_stamps_tenant_key_and_is_visible_in_both_views() -> None:
    log_repo = FakeWateringLogRepo()
    run_repo = MagicMock()
    run_repo.get_run_nutrient_plan_key.return_value = None
    run_repo.get_run_plants.return_value = [{"_key": PLANT_KEY, "slot_key": "slot-1"}]
    task_repo = MagicMock()
    task_repo.get_by_key.return_value = None

    service = WateringLogService(
        log_repo,
        WateringEngine(),
        site_repo=MagicMock(),
        run_repo=run_repo,
        task_repo=task_repo,
    )

    service.confirm_watering(run_key="run-1", task_key="task-1", tenant_key=TENANT)

    assert log_repo._logs[0].tenant_key == TENANT
    global_logs, total = service.list_logs(tenant_key=TENANT)
    per_plant_logs = service.get_by_plant(PLANT_KEY, tenant_key=TENANT)
    assert total == 1
    assert global_logs[0].key == per_plant_logs[0].key


# ── SEC-B4: repository fail-closed per-plant scoping ──────────────────────────


def test_repository_get_by_plant_is_fail_closed_without_tenant() -> None:
    repo = ArangoWateringLogRepository(MagicMock())
    with pytest.raises(ValueError, match="tenant-scoped"):
        repo.get_by_plant(PLANT_KEY)


def test_repository_get_by_plant_applies_tenant_filter() -> None:
    db = MagicMock()
    db.aql.execute.return_value = []
    repo = ArangoWateringLogRepository(db)

    repo.get_by_plant(PLANT_KEY, tenant_key=TENANT)

    _args, kwargs = db.aql.execute.call_args
    query = _args[0] if _args else kwargs["query"]
    assert "doc.tenant_key == @tenant_key" in query
    assert kwargs["bind_vars"]["tenant_key"] == TENANT


def test_repository_get_by_plant_all_tenants_skips_filter() -> None:
    db = MagicMock()
    db.aql.execute.return_value = []
    repo = ArangoWateringLogRepository(db)

    repo.get_by_plant(PLANT_KEY, all_tenants=True)

    _args, kwargs = db.aql.execute.call_args
    query = _args[0] if _args else kwargs["query"]
    assert "doc.tenant_key" not in query
    assert "tenant_key" not in kwargs["bind_vars"]
