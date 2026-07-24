"""#548 — logging watering via the Gießprotokoll path advances the watering task.

``WateringLogService.create_log`` must have the *same* effect on the care state as
completing the watering task in the task queue: complete the plant's open watering
``care_reminder`` task and schedule the next occurrence, through the shared
tenant-aware CARE helpers. These tests wire a real ``CareReminderService`` (so the
shared ``_complete_pending_care_task`` / ``ensure_next_watering_task`` path is
exercised for real) with capturing mock repositories.

The task-state assertions run against the **stateful** :class:`FakeTaskRepo`
(#768): the previous stateless stub answered the follow-up lookup with ``None``
even though the completion had just marked a task completed *today*, which is
precisely the repository behaviour the real AQL does have — so the missing
follow-up task (E2E TC-004-092) was invisible at unit level.
"""

from datetime import UTC, datetime, timedelta
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
from tests.unit.domain.services.care_task_fakes import FakeTaskRepo

PLANT_KEY = "plant-1"
TENANT = "tenant-A"
INTERVAL_DAYS = 7


def _today() -> datetime:
    now = datetime.now(UTC)
    return datetime(now.year, now.month, now.day, tzinfo=UTC)


def _profile(auto_create: bool = True) -> CareProfile:
    return CareProfile(
        plant_key=PLANT_KEY,
        watering_interval_days=INTERVAL_DAYS,
        auto_create_watering_task=auto_create,
        adaptive_learning_enabled=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _open_watering_task(due_offset_days: int = 0) -> Task:
    """A persisted, still-open watering care task due *due_offset_days* from today."""
    return Task(
        key="task-open",
        name=f"Strawberry — {ReminderType.WATERING.value}",
        instruction=f"Water Strawberry (every {INTERVAL_DAYS} days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key=PLANT_KEY,
        entity_type="plant_instance",
        tenant_key=TENANT,
        status=TaskStatus.PENDING,
        due_date=_today() + timedelta(days=due_offset_days),
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
    task_repo,
    plant_tenant: str = TENANT,
    auto_create: bool = True,
) -> tuple[WateringLogService, MagicMock]:
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = _profile(auto_create)
    care_repo.create_confirmation.side_effect = lambda c: CareConfirmation(**{**c.model_dump(), "_key": "conf-1"})
    care_repo.get_last_confirmation.return_value = None

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
    return service, care_repo


def _build_with_mock_repo(
    *,
    find_open_side_effect,
    plant_tenant: str = TENANT,
) -> tuple[WateringLogService, MagicMock, MagicMock]:
    """Variant with a mock task repo, for the paths that must never touch it."""
    task_repo = MagicMock()
    task_repo.find_open_care_task.side_effect = find_open_side_effect
    task_repo.create_task.side_effect = lambda t: t
    service, care_repo = _build(task_repo=task_repo, plant_tenant=plant_tenant)
    return service, task_repo, care_repo


def _log() -> WateringLog:
    return WateringLog(
        tenant_key=TENANT,
        logged_at=datetime.now(UTC),
        volume_liters=1.5,
        plant_keys=[PLANT_KEY],
        slot_keys=[],
    )


def test_create_log_completes_open_task_and_schedules_next() -> None:
    """Logging watering completes the open watering task and creates the next one.

    Regression for #768: the follow-up lookup runs against a repository that has
    *already seen* the completion, so it must be told to ignore the
    completed-today branch — otherwise it returns the task this very call closed
    and no follow-up is ever scheduled (E2E TC-004-092).
    """
    task_repo = FakeTaskRepo([_open_watering_task()])
    service, care_repo = _build(task_repo=task_repo)

    result = service.create_log(_log())

    assert result["log"].key == "log-1"
    care_repo.create_confirmation.assert_called_once()

    # The open watering task was completed (not left pending).
    completed = task_repo.completed_care_tasks(ReminderType.WATERING)
    assert [task.key for task in completed] == ["task-open"]
    assert completed[0].completed_at is not None

    # The next watering occurrence was scheduled — exactly one, correctly terminated.
    scheduled = task_repo.open_care_tasks(ReminderType.WATERING)
    assert len(scheduled) == 1
    assert scheduled[0].key != "task-open"
    assert scheduled[0].category == TaskCategory.CARE_REMINDER
    assert scheduled[0].entity_key == PLANT_KEY
    assert scheduled[0].tenant_key == TENANT
    assert scheduled[0].due_date == _today() + timedelta(days=INTERVAL_DAYS)

    # Every dedup lookup was scoped to the plant's own tenant (#509 guard).
    assert {lookup["tenant_key"] for lookup in task_repo.lookups} == {TENANT}


def test_create_log_is_idempotent_when_already_watered_today() -> None:
    """A second watering the same day neither re-completes nor double-schedules.

    Run against real repository state: the first log closes the open task and
    schedules the follow-up; the second finds only that follow-up, which is not
    yet due — so it is left untouched and no third task appears (#768).
    """
    task_repo = FakeTaskRepo([_open_watering_task()])
    service, _ = _build(task_repo=task_repo)

    service.create_log(_log())
    service.create_log(_log())

    pending = task_repo.open_care_tasks(ReminderType.WATERING)
    completed = task_repo.completed_care_tasks(ReminderType.WATERING)
    assert len(pending) == 1, "the follow-up must stay a single pending task"
    assert len(completed) == 1, "only the originally due task may be completed"
    assert pending[0].due_date == _today() + timedelta(days=INTERVAL_DAYS)
    assert len(task_repo.store) == 2


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

    service, task_repo, care_repo = _build_with_mock_repo(
        find_open_side_effect=find_open,
        plant_tenant="tenant-B",
    )

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

    service, task_repo, care_repo = _build_with_mock_repo(find_open_side_effect=find_open)
    service._plant_repo.get_by_key.return_value = None  # type: ignore[union-attr]

    result = service.create_log(_log())

    assert result["log"].key == "log-1"  # the log itself is still recorded
    care_repo.create_confirmation.assert_not_called()
    task_repo.update_task.assert_not_called()
    task_repo.create_task.assert_not_called()


def test_create_log_without_auto_create_still_closes_open_task() -> None:
    """With auto-scheduling disabled the open task is closed but no next one is made."""
    task_repo = FakeTaskRepo([_open_watering_task()])
    service, _ = _build(task_repo=task_repo, auto_create=False)

    service.create_log(_log())

    assert [task.key for task in task_repo.completed_care_tasks(ReminderType.WATERING)] == ["task-open"]
    assert task_repo.open_care_tasks(ReminderType.WATERING) == []
    assert task_repo.created == []


def test_create_log_does_not_close_a_task_due_later() -> None:
    """A not-yet-due watering task is never closed by an ad-hoc watering (#768).

    Only a *due* task represents the reminder the log satisfies; closing a future
    occurrence would collapse the whole cycle into a single day.
    """
    task_repo = FakeTaskRepo([_open_watering_task(due_offset_days=3)])
    service, _ = _build(task_repo=task_repo)

    service.create_log(_log())

    assert task_repo.completed_care_tasks(ReminderType.WATERING) == []
    assert [task.key for task in task_repo.open_care_tasks(ReminderType.WATERING)] == ["task-open"]
    assert task_repo.created == []


@pytest.mark.parametrize("plant_keys", [[], ["_compat"]])
def test_create_log_without_real_plants_skips_advancement(plant_keys) -> None:
    """A compat/empty log (no real plant) creates the log but advances no task."""

    def find_open(*_args, **_kwargs):  # pragma: no cover - must not be reached
        raise AssertionError("no plant → no care advancement")

    service, task_repo, care_repo = _build_with_mock_repo(find_open_side_effect=find_open)
    log = WateringLog(
        tenant_key=TENANT,
        logged_at=datetime.now(UTC),
        volume_liters=1.0,
        plant_keys=plant_keys,
        slot_keys=["slot-x"],
    )

    result = service.create_log(log)

    assert result["log"].key == "log-1"
    care_repo.create_confirmation.assert_not_called()
    task_repo.update_task.assert_not_called()
    task_repo.create_task.assert_not_called()
