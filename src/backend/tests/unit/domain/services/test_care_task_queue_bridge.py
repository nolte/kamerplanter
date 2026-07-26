"""Task-queue completion bridge → care state (REQ-022, #768).

Completing a ``care_reminder`` task from the task queue must move the plant's
care state exactly like the dashboard-confirmation and the Gießprotokoll paths:
write the ``CareConfirmation`` (+ edges), materialise the watering log, and — for
watering — schedule the next occurrence.

That composition used to live inline in
``api/v1/tasks/tenant_router.py::complete_task`` (a 5-layer violation, NFR-001),
which is why it had **zero** test coverage and broke 100 % of the time:
``TaskService.complete_task`` always stamps ``completed_at=now`` first, so the
follow-up lookup returned the very task that had just been completed and the
plant's reminder chain ended until the next nightly run. These tests cover the
extracted :meth:`CareReminderService.record_care_task_completion` against a
**stateful** repository fake, so that regression can never come back unseen.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from app.common.enums import ConfirmAction, ReminderType, TaskCategory, TaskStatus
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.task import Task
from app.domain.services.care_reminder_service import CareReminderService
from tests.unit.domain.services.care_task_fakes import FakeTaskRepo

PLANT_KEY = "plant-1"
TENANT = "tenant-A"
INTERVAL_DAYS = 7


def _today() -> datetime:
    now = datetime.now(UTC)
    return datetime(now.year, now.month, now.day, tzinfo=UTC)


def _profile(auto_create: bool = True) -> CareProfile:
    return CareProfile(
        key="cp-1",
        plant_key=PLANT_KEY,
        watering_interval_days=INTERVAL_DAYS,
        fertilizing_interval_days=14,
        auto_create_watering_task=auto_create,
        adaptive_learning_enabled=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _queue_completed_task(
    reminder_type: ReminderType = ReminderType.WATERING,
    *,
    category: TaskCategory = TaskCategory.CARE_REMINDER,
    entity_type: str = "plant_instance",
) -> Task:
    """A care task as ``TaskService.complete_task`` leaves it: completed *today*."""
    return Task(
        key="task-open",
        name=f"Strawberry — {reminder_type.value}",
        instruction=f"Water Strawberry (every {INTERVAL_DAYS} days).",
        category=category,
        entity_key=PLANT_KEY,
        entity_type=entity_type,
        tenant_key=TENANT,
        status=TaskStatus.COMPLETED,
        due_date=_today(),
        completed_at=datetime.now(UTC),
        completion_notes="watered by hand",
    )


def _build(
    *,
    task_repo: FakeTaskRepo,
    profile: CareProfile | None,
    plant_tenant: str = TENANT,
) -> tuple[CareReminderService, MagicMock, MagicMock]:
    care_repo = MagicMock()
    care_repo.get_profile_by_plant_key.return_value = profile

    # Stateful confirmation history: the bridge writes the confirmation *before*
    # scheduling, so the follow-up must anchor on it (not on the profile bootstrap).
    history: list[CareConfirmation] = []

    def _create_confirmation(confirmation: CareConfirmation) -> CareConfirmation:
        saved = CareConfirmation(**{**confirmation.model_dump(), "_key": f"conf-{len(history) + 1}"})
        history.append(saved)
        return saved

    def _last_confirmation(plant_key: str, reminder_type: ReminderType) -> CareConfirmation | None:
        matches = [c for c in history if c.plant_key == plant_key and c.reminder_type == reminder_type]
        return matches[-1] if matches else None

    care_repo.create_confirmation.side_effect = _create_confirmation
    care_repo.get_last_confirmation.side_effect = _last_confirmation

    plant = MagicMock()
    plant.key = PLANT_KEY
    plant.plant_name = "Strawberry"
    plant.instance_id = "FRAGA-1"
    plant.tenant_key = plant_tenant
    plant.current_phase_key = None
    plant.slot_key = None
    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = plant

    log_repo = MagicMock()

    service = CareReminderService(
        care_repo,
        CareReminderEngine(),
        task_repo,
        watering_log_repo=log_repo,
        plant_repo=plant_repo,
    )
    return service, care_repo, log_repo


def test_queue_completion_schedules_exactly_one_follow_up() -> None:
    """Completing a watering task in the queue yields one new pending follow-up.

    The completed task is already in the repository with ``completed_at`` set to
    *today* — exactly the state the router sees. Without suppressing the
    completed-today dedup branch the follow-up would never be created (#768).
    """
    completed = _queue_completed_task()
    task_repo = FakeTaskRepo([completed])
    service, care_repo, log_repo = _build(task_repo=task_repo, profile=_profile())

    result = service.record_care_task_completion(completed, tenant_key=TENANT)

    assert result is not None
    pending = task_repo.open_care_tasks(ReminderType.WATERING)
    assert len(pending) == 1
    assert pending[0].key != "task-open"
    assert pending[0].tenant_key == TENANT
    assert pending[0].entity_key == PLANT_KEY
    assert pending[0].due_date == _today() + timedelta(days=INTERVAL_DAYS)
    # The already-completed task is untouched (never re-completed / reopened).
    assert [task.key for task in task_repo.completed_care_tasks(ReminderType.WATERING)] == ["task-open"]
    assert task_repo.updated == []

    # The care state mirrors the dashboard path: confirmation + edges + log.
    confirmation = care_repo.create_confirmation.call_args[0][0]
    assert confirmation.reminder_type == ReminderType.WATERING
    assert confirmation.action == ConfirmAction.CONFIRMED
    assert confirmation.task_key == "task-open"
    assert confirmation.notes == "watered by hand"
    assert confirmation.interval_at_time == INTERVAL_DAYS
    assert confirmation.care_profile_key == "cp-1"
    care_repo.create_confirmation_edges.assert_called_once_with("conf-1", "cp-1", PLANT_KEY)
    log_repo.create.assert_called_once()
    assert log_repo.create.call_args[0][0].tenant_key == TENANT


def test_queue_completion_is_idempotent_on_a_second_call() -> None:
    """Replaying the bridge for the same task does not mint a second follow-up."""
    completed = _queue_completed_task()
    task_repo = FakeTaskRepo([completed])
    service, _, _ = _build(task_repo=task_repo, profile=_profile())

    service.record_care_task_completion(completed, tenant_key=TENANT)
    second = service.record_care_task_completion(completed, tenant_key=TENANT)

    assert second is None, "the pending follow-up already satisfies the reminder"
    assert len(task_repo.open_care_tasks(ReminderType.WATERING)) == 1


def test_queue_completion_without_opt_in_creates_no_follow_up() -> None:
    """``auto_create_watering_task=False`` still records the confirmation only."""
    completed = _queue_completed_task()
    task_repo = FakeTaskRepo([completed])
    service, care_repo, log_repo = _build(task_repo=task_repo, profile=_profile(auto_create=False))

    result = service.record_care_task_completion(completed, tenant_key=TENANT)

    assert result is None
    assert task_repo.created == []
    care_repo.create_confirmation.assert_called_once()
    log_repo.create.assert_called_once()


def test_queue_completion_of_non_watering_task_creates_no_watering_task() -> None:
    """A fertilizing completion writes its confirmation but schedules no watering."""
    completed = _queue_completed_task(ReminderType.FERTILIZING)
    task_repo = FakeTaskRepo([completed])
    service, care_repo, log_repo = _build(task_repo=task_repo, profile=_profile())

    result = service.record_care_task_completion(completed, tenant_key=TENANT)

    assert result is None
    assert task_repo.created == []
    assert care_repo.create_confirmation.call_args[0][0].reminder_type == ReminderType.FERTILIZING
    log_repo.create.assert_called_once()


def test_bridge_ignores_non_care_and_non_plant_tasks() -> None:
    """A plain task (or a care task on another entity type) is a no-op."""
    task_repo = FakeTaskRepo()
    service, care_repo, log_repo = _build(task_repo=task_repo, profile=_profile())

    assert service.record_care_task_completion(_queue_completed_task(category=TaskCategory.MAINTENANCE)) is None
    assert service.record_care_task_completion(_queue_completed_task(entity_type="location")) is None

    care_repo.get_profile_by_plant_key.assert_not_called()
    care_repo.create_confirmation.assert_not_called()
    log_repo.create.assert_not_called()
    assert task_repo.created == []


def test_bridge_without_care_profile_writes_nothing() -> None:
    """A plant without a care profile writes no confirmation and no task."""
    completed = _queue_completed_task()
    task_repo = FakeTaskRepo([completed])
    service, care_repo, log_repo = _build(task_repo=task_repo, profile=None)

    assert service.record_care_task_completion(completed, tenant_key=TENANT) is None

    care_repo.create_confirmation.assert_not_called()
    log_repo.create.assert_not_called()
    assert task_repo.created == []


def test_completion_refuses_a_task_pointing_at_a_foreign_tenants_plant() -> None:
    """SEC-001 — the bridge must not write into another tenant's care state.

    ``TaskCreate.entity_key`` is caller-supplied and is not validated against the
    creating tenant, so a task legitimately owned by tenant A can name a plant of
    tenant B. Completing it used to write a ``CareConfirmation`` plus graph edges
    on the victim's plant, a watering log carrying the *attacker's* tenant but the
    victim's ``plant_keys``, and a follow-up care task in the *victim's* tenant
    (``ensure_next_watering_task`` resolves the tenant from the plant). Nothing at
    all may be written.
    """
    completed = _queue_completed_task()
    task_repo = FakeTaskRepo([completed])
    service, care_repo, log_repo = _build(
        task_repo=task_repo,
        profile=_profile(),
        plant_tenant="tenant-VICTIM",
    )

    assert service.record_care_task_completion(completed, tenant_key=TENANT) is None

    care_repo.create_confirmation.assert_not_called()
    care_repo.create_confirmation_edges.assert_not_called()
    log_repo.create.assert_not_called()
    assert task_repo.created == []
    assert task_repo.updated == []


def test_completion_refuses_a_task_of_another_tenant() -> None:
    """Defence in depth — the service verifies the task's own tenant too.

    The router already 404s a foreign task before calling in, but the service must
    not depend on a caller-side check for its isolation guarantee.
    """
    completed = _queue_completed_task()
    completed.tenant_key = "tenant-OTHER"
    task_repo = FakeTaskRepo([completed])
    service, care_repo, log_repo = _build(task_repo=task_repo, profile=_profile())

    assert service.record_care_task_completion(completed, tenant_key=TENANT) is None

    care_repo.create_confirmation.assert_not_called()
    log_repo.create.assert_not_called()
    assert task_repo.created == []


def test_skip_records_a_skipped_confirmation() -> None:
    """The skip bridge writes the SKIPPED confirmation and its edges — nothing else.

    A skip is not a care event: no watering log is materialised and no follow-up
    task is scheduled.
    """
    skipped = _queue_completed_task()
    skipped.status = TaskStatus.SKIPPED
    task_repo = FakeTaskRepo([skipped])
    service, care_repo, log_repo = _build(task_repo=task_repo, profile=_profile())

    created = service.record_care_task_skip(skipped, tenant_key=TENANT)

    assert created is not None
    confirmation = care_repo.create_confirmation.call_args[0][0]
    assert confirmation.action == ConfirmAction.SKIPPED
    assert confirmation.reminder_type == ReminderType.WATERING
    assert confirmation.plant_key == PLANT_KEY
    assert confirmation.care_profile_key == "cp-1"
    assert confirmation.task_key == "task-open"
    assert confirmation.interval_at_time == INTERVAL_DAYS
    care_repo.create_confirmation_edges.assert_called_once_with("conf-1", "cp-1", PLANT_KEY)
    log_repo.create.assert_not_called()
    assert task_repo.created == []


def test_skip_refuses_a_task_pointing_at_a_foreign_tenants_plant() -> None:
    """SEC-001 — the skip bridge shares the completion bridge's tenant guard.

    The skip composition used to live in the API layer, reaching around the
    service into its repository/engine; a guard inside the service would have been
    bypassed there. Driven through the service it is refused like a completion.
    """
    skipped = _queue_completed_task()
    skipped.status = TaskStatus.SKIPPED
    task_repo = FakeTaskRepo([skipped])
    service, care_repo, log_repo = _build(
        task_repo=task_repo,
        profile=_profile(),
        plant_tenant="tenant-VICTIM",
    )

    assert service.record_care_task_skip(skipped, tenant_key=TENANT) is None

    care_repo.create_confirmation.assert_not_called()
    care_repo.create_confirmation_edges.assert_not_called()
    log_repo.create.assert_not_called()


def test_bridge_ignores_a_care_task_without_a_reminder_type_suffix() -> None:
    """A care task whose name carries no known reminder type is left alone."""
    completed = _queue_completed_task()
    completed.name = "Strawberry — spring cleanup"
    task_repo = FakeTaskRepo([completed])
    service, care_repo, log_repo = _build(task_repo=task_repo, profile=_profile())

    assert service.record_care_task_completion(completed, tenant_key=TENANT) is None

    care_repo.create_confirmation.assert_not_called()
    log_repo.create.assert_not_called()
    assert task_repo.created == []
