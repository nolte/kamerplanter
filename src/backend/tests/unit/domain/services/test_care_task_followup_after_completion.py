"""#761 — closing a watering task must not veto its own follow-up occurrence.

E2E TC-004-092 asserts that logging a watering both completes the plant's due
``— watering`` care task **and** schedules exactly one follow-up. It never did:
every path that closes the satisfying task and then asks
:meth:`CareReminderService.ensure_next_watering_task` for the next occurrence ran
into the #509 recency rule ("a task completed today satisfies the reminder") —
and the task completed today was the one the same call chain had just closed, so
the guard vetoed the follow-up and the plant was left with no pending watering
task at all.

These tests exercise the service against
:class:`~tests.unit.domain.services.care_task_fakes.FakeTaskRepo`, which
models the real AQL predicate, so they fail against the pre-fix behaviour. The
counterpart tests below pin that the recency rule is *unchanged* for every caller
that did not itself close a task (the daily Celery producer, the interval
reschedule) — they fail if anyone ever flips the flag globally.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import ConfirmAction, ReminderType, TaskCategory, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService
from tests.unit.domain.services.care_task_fakes import FakeTaskRepo

PLANT_KEY = "plant-1"
TENANT = "tenant-A"
INTERVAL_DAYS = 7


def _profile(auto_create: bool = True) -> CareProfile:
    return CareProfile(
        key="cp-1",
        plant_key=PLANT_KEY,
        watering_interval_days=INTERVAL_DAYS,
        auto_create_watering_task=auto_create,
        adaptive_learning_enabled=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _due_watering_task(key: str = "task-due") -> Task:
    """The plant's open watering care task, due today (as the E2E sees it)."""
    return Task(
        key=key,
        name=f"Strawberry — {ReminderType.WATERING.value}",
        instruction=f"Water Strawberry (every {INTERVAL_DAYS} days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key=PLANT_KEY,
        entity_type="plant_instance",
        tenant_key=TENANT,
        status=TaskStatus.PENDING,
        due_date=datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0),
    )


def _completed_today_task(key: str = "task-earlier") -> Task:
    task = _due_watering_task(key)
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(UTC) - timedelta(hours=2)
    return task


def _service(repo: FakeTaskRepo, *, auto_create: bool = True) -> CareReminderService:
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = _profile(auto_create)
    care_repo.get_last_confirmation.return_value = None
    care_repo.create_confirmation.side_effect = lambda c: CareConfirmation(**{**c.model_dump(), "_key": "conf-1"})

    plant = SimpleNamespace(
        key=PLANT_KEY,
        plant_name="Strawberry",
        instance_id="FRAGA-0712-TCJ",
        tenant_key=TENANT,
        current_phase_key=None,
        slot_key=None,
    )
    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = plant
    plant_repo.get_or_raise.return_value = plant
    return CareReminderService(care_repo, CareReminderEngine(), repo, plant_repo=plant_repo)


def _confirmation(when: datetime | None = None) -> CareConfirmation:
    return CareConfirmation(
        plant_key=PLANT_KEY,
        care_profile_key="cp-1",
        reminder_type=ReminderType.WATERING,
        action=ConfirmAction.CONFIRMED,
        confirmed_at=when or datetime.now(UTC),
    )


# ── the defect: the follow-up occurrence ──


def test_watering_log_advance_schedules_exactly_one_follow_up() -> None:
    """TC-004-092 at unit level: the due task closes and one follow-up appears."""
    repo = FakeTaskRepo([_due_watering_task()])
    service = _service(repo)
    confirmed_at = datetime.now(UTC)

    created = service.advance_watering_task_after_log(PLANT_KEY, _confirmation(confirmed_at), tenant_key=TENANT)

    assert created is not None
    # The due task was closed …
    closed = next(task for task in repo.store if task.key == "task-due")
    assert closed.status == TaskStatus.COMPLETED
    assert closed.completed_at is not None
    # … and exactly one pending follow-up exists, due one interval later.
    pending = repo.open_care_tasks(ReminderType.WATERING)
    assert len(pending) == 1
    assert pending[0].key == created.key
    assert created.due_date is not None
    assert created.due_date.date() == (confirmed_at + timedelta(days=INTERVAL_DAYS)).date()
    assert created.tenant_key == TENANT


def test_dashboard_confirmation_schedules_the_follow_up() -> None:
    """The dashboard confirm path had the same shape and is fixed with it."""
    repo = FakeTaskRepo([_due_watering_task()])
    service = _service(repo)

    service.confirm_reminder(PLANT_KEY, ReminderType.WATERING, tenant_key=TENANT)

    assert len(repo.open_care_tasks(ReminderType.WATERING)) == 1
    assert next(task for task in repo.store if task.key == "task-due").status == TaskStatus.COMPLETED


def test_task_queue_completion_bridge_schedules_the_follow_up() -> None:
    """The task-queue bridge closes the task itself and passes it in (#761).

    Mirrors ``POST /tasks/{key}/complete``: the task is already ``COMPLETED``
    when the follow-up is requested, so only ``just_completed_task`` keeps the
    recency rule from vetoing it.
    """
    completed = _completed_today_task("task-queue")
    repo = FakeTaskRepo([completed])
    service = _service(repo)

    created = service.ensure_next_watering_task(_profile(), just_completed_task=completed)

    assert created is not None
    assert len(repo.open_care_tasks(ReminderType.WATERING)) == 1


def test_second_log_the_same_day_keeps_exactly_one_pending_task() -> None:
    """Logging watering twice a day never accumulates pending watering tasks."""
    repo = FakeTaskRepo([_due_watering_task()])
    service = _service(repo)

    service.advance_watering_task_after_log(PLANT_KEY, _confirmation(), tenant_key=TENANT)
    service.advance_watering_task_after_log(PLANT_KEY, _confirmation(), tenant_key=TENANT)

    assert len(repo.open_care_tasks(ReminderType.WATERING)) == 1


def test_advance_without_auto_create_closes_but_schedules_nothing() -> None:
    """Opting out of auto-scheduling still closes the task and creates none."""
    repo = FakeTaskRepo([_due_watering_task()])
    service = _service(repo, auto_create=False)

    assert service.advance_watering_task_after_log(PLANT_KEY, _confirmation(), tenant_key=TENANT) is None
    assert repo.open_care_tasks(ReminderType.WATERING) == []
    assert next(task for task in repo.store if task.key == "task-due").status == TaskStatus.COMPLETED


# ── the #509 recency rule for every other caller ──


def test_recency_rule_still_blocks_callers_that_closed_nothing() -> None:
    """#509 unchanged: the daily producer must not re-materialize today's reminder.

    ``ensure_next_watering_task`` without ``just_completed_task`` (the daily
    Celery producer and the interval-reschedule path) still treats a task
    completed today as satisfying the reminder — this test fails if the
    ``include_completed_today`` flag is ever flipped globally to "fix" #761.
    """
    repo = FakeTaskRepo([_completed_today_task()])
    service = _service(repo)

    created = service.ensure_next_watering_task(_profile())

    assert created is None
    assert repo.open_care_tasks(ReminderType.WATERING) == []
    assert [lookup["include_completed_today"] for lookup in repo.lookups] == [True]


def test_advance_is_a_no_op_when_a_foreign_path_closed_the_task_today() -> None:
    """Nothing open to close → no ``just_completed_task`` → the recency rule holds.

    A watering log added after the task was already completed elsewhere today
    neither reopens nor duplicates anything: the advance path opts into the
    narrowed lookup only when it actually closed a task itself.
    """
    repo = FakeTaskRepo([_completed_today_task()])
    service = _service(repo)

    created = service.advance_watering_task_after_log(PLANT_KEY, _confirmation(), tenant_key=TENANT)

    assert created is None
    assert repo.open_care_tasks(ReminderType.WATERING) == []
    assert repo.lookups[-1]["include_completed_today"] is True


def test_follow_up_defers_to_another_still_open_task() -> None:
    """Even after closing one task, a still-open one blocks a second follow-up."""
    still_open = _due_watering_task("task-other")
    still_open.due_date = datetime.now(UTC) + timedelta(days=3)
    repo = FakeTaskRepo([still_open])
    service = _service(repo)

    created = service.ensure_next_watering_task(_profile(), just_completed_task=_completed_today_task())

    assert created is None
    assert [task.key for task in repo.open_care_tasks(ReminderType.WATERING)] == ["task-other"]


@pytest.mark.parametrize(
    ("just_completed", "expected_flag"),
    [(None, True), (_completed_today_task(), False)],
)
def test_lookup_flag_is_chosen_per_caller(just_completed: Task | None, expected_flag: bool) -> None:
    """The narrowed lookup is opt-in and never leaks into the default path."""
    repo = FakeTaskRepo()
    service = _service(repo)

    service.ensure_next_watering_task(_profile(), just_completed_task=just_completed)

    assert repo.lookups[0]["include_completed_today"] is expected_flag
    assert repo.lookups[0]["tenant_key"] == TENANT
