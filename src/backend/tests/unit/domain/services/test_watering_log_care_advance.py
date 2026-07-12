"""#548 — logging watering via the Gießprotokoll path advances the watering task.

``WateringLogService.create_log`` must have the *same* effect on the care state as
completing the watering task in the task queue: complete the plant's open watering
``care_reminder`` task and schedule the next occurrence, through the shared
tenant-aware CARE helpers. These tests wire a real ``CareReminderService`` (so the
shared ``_complete_pending_care_task`` / ``ensure_next_watering_task`` path is
exercised for real) with capturing mock repositories.
"""

from datetime import UTC, date, datetime, time
from unittest.mock import MagicMock

import pytest

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.engines.watering_engine import WateringEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.task import Task
from app.domain.models.watering_log import WateringLog
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.watering_log_service import WateringLogService

PLANT_KEY = "plant-1"
TENANT = "tenant-A"


def _profile(auto_create: bool = True) -> CareProfile:
    return CareProfile(
        plant_key=PLANT_KEY,
        watering_interval_days=7,
        auto_create_watering_task=auto_create,
        adaptive_learning_enabled=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _open_watering_task() -> Task:
    return Task(
        key="task-open",
        name=f"Strawberry — {ReminderType.WATERING.value}",
        instruction="Water Strawberry (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key=PLANT_KEY,
        entity_type="plant_instance",
        tenant_key=TENANT,
        status=TaskStatus.PENDING,
        due_date=datetime(2026, 7, 14, tzinfo=UTC),
    )


def _plant(tenant_key: str = TENANT) -> MagicMock:
    plant = MagicMock()
    plant.key = PLANT_KEY
    plant.plant_name = "Strawberry"
    plant.instance_id = "FRAGA-0712-TCJ"
    plant.tenant_key = tenant_key
    plant.current_phase_key = None
    plant.slot_key = None
    return plant


def _build(
    *,
    find_open_side_effect,
    plant_tenant: str = TENANT,
    auto_create: bool = True,
) -> tuple[WateringLogService, MagicMock, MagicMock]:
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = _profile(auto_create)
    care_repo.create_confirmation.side_effect = lambda c: CareConfirmation(**{**c.model_dump(), "_key": "conf-1"})
    care_repo.get_last_confirmation.return_value = None

    task_repo = MagicMock()
    task_repo.find_open_care_task.side_effect = find_open_side_effect
    task_repo.create_task.side_effect = lambda t: t

    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = _plant(plant_tenant)

    care_service = CareReminderService(
        care_repo,
        CareReminderEngine(),
        task_repo,
        plant_repo=plant_repo,
    )

    log_repo = MagicMock()
    log_repo.create.side_effect = lambda log: WateringLog(**{**log.model_dump(), "_key": "log-1"})
    site_repo = MagicMock()
    site_repo.get_slot_by_key.return_value = None

    service = WateringLogService(
        log_repo,
        WateringEngine(),
        site_repo,
        care_repo=care_repo,
        care_service=care_service,
        plant_repo=plant_repo,
    )
    return service, task_repo, care_repo


def _log() -> WateringLog:
    return WateringLog(
        tenant_key=TENANT,
        logged_at=datetime(2026, 7, 12, 10, 0, tzinfo=UTC),
        volume_liters=1.5,
        plant_keys=[PLANT_KEY],
        slot_keys=[],
    )


def test_create_log_completes_open_task_and_schedules_next() -> None:
    """Logging watering completes the open watering task and creates the next one.

    ``find_open_care_task`` is answered per the two shared calls: the completion
    lookup (``include_completed_today=False``) reports the open task, while the
    next-occurrence lookup (``include_completed_today=True``) reports nothing, so
    the service both closes the open task and schedules the following cycle.
    """

    def find_open(entity_key, reminder_type, tenant_key, *, include_completed_today=True):
        return None if include_completed_today else _open_watering_task()

    service, task_repo, care_repo = _build(find_open_side_effect=find_open)

    result = service.create_log(_log())

    assert result["log"].key == "log-1"
    care_repo.create_confirmation.assert_called_once()

    # The open watering task was completed (not left pending).
    task_repo.update_task.assert_called_once()
    completed = task_repo.update_task.call_args[0][1]
    assert completed.status == TaskStatus.COMPLETED.value
    assert completed.completed_at is not None

    # The next watering occurrence was scheduled.
    task_repo.create_task.assert_called_once()
    scheduled = task_repo.create_task.call_args[0][0]
    assert scheduled.category == TaskCategory.CARE_REMINDER
    assert scheduled.entity_key == PLANT_KEY
    assert scheduled.tenant_key == TENANT

    # Every dedup lookup was scoped to the plant's own tenant (#509 guard).
    for call in task_repo.find_open_care_task.call_args_list:
        assert call.args[2] == TENANT


def test_create_log_is_idempotent_when_already_watered_today() -> None:
    """Logging watering again the same day neither re-completes nor re-schedules.

    Nothing is open (the completion lookup returns ``None``) and a task completed
    today satisfies the reminder (the next-occurrence lookup reports it), so the
    second log is a no-op on the task state.
    """
    completed_today = _open_watering_task()
    completed_today.status = TaskStatus.COMPLETED
    completed_today.completed_at = datetime.combine(date.today(), time(9, 0), tzinfo=UTC)

    def find_open(entity_key, reminder_type, tenant_key, *, include_completed_today=True):
        return completed_today if include_completed_today else None

    service, task_repo, _ = _build(find_open_side_effect=find_open)

    service.create_log(_log())

    task_repo.update_task.assert_not_called()  # nothing open to complete
    task_repo.create_task.assert_not_called()  # completed-today blocks re-scheduling


def test_create_log_does_not_touch_foreign_tenant_plant() -> None:
    """SEC-001: a tenant-A log with a tenant-B plant_key writes no care state.

    The log carries ``tenant_key=tenant-A`` but the plant resolves to ``tenant-B``.
    The fail-closed tenant guard at the *top* of the per-plant block bails out
    before ANY care-state write: no ``CareConfirmation`` (or its edges) is written
    into tenant B's care graph, and no watering task is advanced. Tenant isolation
    must not rely on plant_key-unguessability.
    """

    def find_open(*_args, **_kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("find_open_care_task must not run for a foreign-tenant plant")

    service, task_repo, care_repo = _build(find_open_side_effect=find_open, plant_tenant="tenant-B")

    service.create_log(_log())

    # No cross-tenant care-state write at all (SEC-001 closed).
    care_repo.get_profile_by_plant_key.assert_not_called()
    care_repo.create_confirmation.assert_not_called()
    care_repo.create_confirmation_edges.assert_not_called()
    # And no task advancement either.
    task_repo.find_open_care_task.assert_not_called()
    task_repo.update_task.assert_not_called()
    task_repo.create_task.assert_not_called()


def test_create_log_missing_plant_writes_no_confirmation() -> None:
    """A plant_key that resolves to no plant (deleted/unknown) writes no care state.

    Fail-closed: an unresolvable plant_key is skipped just like a foreign one, so a
    dangling key can never create an orphan ``CareConfirmation``.
    """

    def find_open(*_args, **_kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("find_open_care_task must not run for a missing plant")

    service, task_repo, care_repo = _build(find_open_side_effect=find_open)
    service._plant_repo.get_by_key.return_value = None  # type: ignore[union-attr]

    result = service.create_log(_log())

    assert result["log"].key == "log-1"  # the log itself is still recorded
    care_repo.create_confirmation.assert_not_called()
    task_repo.update_task.assert_not_called()
    task_repo.create_task.assert_not_called()


def test_create_log_without_auto_create_still_closes_open_task() -> None:
    """With auto-scheduling disabled the open task is closed but no next one is made."""

    def find_open(entity_key, reminder_type, tenant_key, *, include_completed_today=True):
        return None if include_completed_today else _open_watering_task()

    service, task_repo, _ = _build(find_open_side_effect=find_open, auto_create=False)

    service.create_log(_log())

    task_repo.update_task.assert_called_once()
    task_repo.create_task.assert_not_called()


@pytest.mark.parametrize("plant_keys", [[], ["_compat"]])
def test_create_log_without_real_plants_skips_advancement(plant_keys) -> None:
    """A compat/empty log (no real plant) creates the log but advances no task."""

    def find_open(*_args, **_kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("no plant → no care advancement")

    service, task_repo, care_repo = _build(find_open_side_effect=find_open)
    log = WateringLog(
        tenant_key=TENANT,
        logged_at=datetime(2026, 7, 12, tzinfo=UTC),
        volume_liters=1.0,
        plant_keys=plant_keys,
        slot_keys=["slot-x"],
    )

    result = service.create_log(log)

    assert result["log"].key == "log-1"
    care_repo.create_confirmation.assert_not_called()
    task_repo.update_task.assert_not_called()
    task_repo.create_task.assert_not_called()
