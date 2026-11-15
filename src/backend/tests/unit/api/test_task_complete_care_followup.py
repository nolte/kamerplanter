"""#761 / #2960 - completing a care-reminder task records the confirmation and schedules the next occurrence.

Completing a care-reminder task closes it, records the confirmation and asks
:meth:`CareReminderService.ensure_next_watering_task` for the follow-up. Because
the task is already ``COMPLETED`` at that point, the #509 recency rule ("a task
completed today satisfies the reminder") vetoed the follow-up - the same defect
E2E TC-004-092 exposed on the watering-log path.

Since #2960 the mirror runs inside :class:`TaskService` (single route, batch, replay alike), so these tests drive
the real service with a real ``CareReminderService`` over the faithful care-task repository model: the assertion is
behavioural (one confirmation, one pending follow-up) rather than a call-shape mock.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.common.enums import ReminderType, TaskCategory, TaskStatus, TenantRole
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.engines.hst_validator import HSTValidator
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.task import Task
from app.domain.models.task_completion import CompletionActor
from app.domain.services.care_reminder_service import CareReminderService
from app.domain.services.task_service import TaskService
from tests.support import task_completion_fakes
from tests.unit.domain.services.care_task_fakes import FakeTaskRepo

PLANT_KEY = "plant-1"
TENANT = "tenant-A"
TASK_KEY = "task-due"


ACTOR = CompletionActor(user_key="user-a", role=TenantRole.LEAD)


def _completed_watering_task() -> Task:
    """The care task as ``TaskService.complete_task`` leaves it: closed just now."""
    return Task(
        key=TASK_KEY,
        name=f"Strawberry — {ReminderType.WATERING.value}",
        instruction="Water Strawberry (every 7 days).",
        category=TaskCategory.CARE_REMINDER,
        entity_key=PLANT_KEY,
        entity_type="plant_instance",
        tenant_key=TENANT,
        status=TaskStatus.COMPLETED,
        due_date=datetime.now(UTC) - timedelta(days=1),
        completed_at=datetime.now(UTC),
    )


def _task_service(care_service: CareReminderService | None, *, crash_first: bool = False) -> tuple[TaskService, dict]:
    """The real task service over the completion doubles; its care mirror is ``care_service``."""
    pending = _completed_watering_task().model_copy(update={"status": TaskStatus.PENDING, "completed_at": None})
    tasks = task_completion_fakes.FakeTaskRepo(pending)
    crashes = {"left": 1 if crash_first else 0}

    def mirror() -> CareReminderService:
        if crashes["left"]:
            crashes["left"] -= 1
            raise RuntimeError("the process died between the commit and the follow-up")
        assert care_service is not None
        return care_service

    service = TaskService(
        tasks,
        HSTValidator(),
        DependencyResolver(),
        completion=task_completion_fakes.FakeCompletionRepo(tasks, {}),
        care_mirror=mirror,
    )
    return service, tasks.store


def _complete(service: TaskService, client_event_id=None):
    return service.complete_task_once(TASK_KEY, tenant_key=TENANT, client_event_id=client_event_id, actor=ACTOR)


@pytest.fixture
def care_stack() -> tuple[CareReminderService, FakeTaskRepo]:
    care_repo = MagicMock()
    profile = CareProfile(
        key="cp-1",
        plant_key=PLANT_KEY,
        watering_interval_days=7,
        auto_create_watering_task=True,
        adaptive_learning_enabled=False,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    care_repo.get_profile_by_plant_key.return_value = profile
    care_repo.get_last_confirmation.return_value = None
    care_repo.create_confirmation.side_effect = lambda c: CareConfirmation(**{**c.model_dump(), "_key": "conf-1"})

    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = SimpleNamespace(
        key=PLANT_KEY,
        plant_name="Strawberry",
        instance_id="FRAGA-0712-TCJ",
        tenant_key=TENANT,
        current_phase_key=None,
        slot_key=None,
    )

    task_store = FakeTaskRepo([_completed_watering_task()])
    service = CareReminderService(
        care_repo,
        CareReminderEngine(),
        task_store,
        watering_log_repo=MagicMock(),
        plant_repo=plant_repo,
    )
    return service, task_store


def test_completing_a_watering_task_schedules_the_next_occurrence(care_stack) -> None:
    care_service, task_store = care_stack
    service, _store = _task_service(care_service)

    outcome = _complete(service)

    assert outcome.task.status == TaskStatus.COMPLETED
    pending = task_store.open_care_tasks(ReminderType.WATERING)
    assert len(pending) == 1
    assert pending[0].key != TASK_KEY
    assert pending[0].tenant_key == TENANT
    # The follow-up lookup was the narrowed one - the request closed the task itself.
    assert task_store.lookups[-1]["include_completed_today"] is False


def test_a_batch_completion_records_the_confirmation_and_the_next_occurrence(care_stack) -> None:
    """#2960: ``POST /tasks/batch/status`` closes a care reminder like the single route does."""
    care_service, task_store = care_stack
    repo = care_service._repo  # noqa: SLF001 - the MagicMock the fixture built
    confirmations: list[CareConfirmation] = []
    repo.find_confirmation_by_completion.return_value = None
    repo.create_confirmation_logged.side_effect = lambda confirmation, **_: confirmations.append(confirmation)
    service, _store = _task_service(care_service)

    succeeded, failed = service.batch_status_change([TASK_KEY], "complete", tenant_key=TENANT, actor=ACTOR)

    assert (succeeded, failed) == ([TASK_KEY], [])
    assert len(confirmations) == 1
    assert len(task_store.open_care_tasks(ReminderType.WATERING)) == 1


def _recording(care_service: CareReminderService) -> list[CareConfirmation]:
    repo = care_service._repo  # noqa: SLF001 - the MagicMock the fixture built
    confirmations: list[CareConfirmation] = []
    repo.find_confirmation_by_completion.side_effect = lambda plant_key, client_id: next(
        (c for c in confirmations if c.completion_client_event_id == client_id), None
    )
    repo.create_confirmation_logged.side_effect = lambda confirmation, **_: confirmations.append(confirmation)
    return confirmations


def test_a_replay_records_the_confirmation_a_crashed_first_attempt_lost_and_only_once(care_stack):
    # REQ-053 WP 9.3: the first attempt committed and died before its follow-up; the replay must record the
    # confirmation, and a further replay must not record it twice.
    care_service, task_store = care_stack
    confirmations = _recording(care_service)
    service, _store = _task_service(care_service, crash_first=True)
    client_id = uuid4()

    with pytest.raises(RuntimeError):
        _complete(service, client_id)
    assert confirmations == []

    for _ in range(2):
        assert _complete(service, client_id).replayed

    assert [c.completion_client_event_id for c in confirmations] == [str(client_id)]
    assert len(task_store.open_care_tasks(ReminderType.WATERING)) == 1  # the next occurrence once, too


def test_a_replay_of_a_reopened_task_runs_no_follow_up(care_stack):
    care_service, _task_store = care_stack
    repo = care_service._repo  # noqa: SLF001
    repo.find_confirmation_by_completion.return_value = None
    service, store = _task_service(care_service, crash_first=True)
    client_id = uuid4()
    with pytest.raises(RuntimeError):
        _complete(service, client_id)
    store[TASK_KEY] = store[TASK_KEY].model_copy(update={"status": TaskStatus.PENDING})

    assert _complete(service, client_id).replayed

    repo.create_confirmation_logged.assert_not_called()


def test_a_completion_without_an_id_after_a_reopen_confirms_again_and_a_late_replay_does_not(care_stack):
    # Verifying review of #2787 (F1): A completed with id X, the task was reopened, B completed it WITHOUT an id -
    # the task still carries X. B's confirmation must not be deduped against A's, and a late replay of X confirms
    # nothing more: exactly two confirmations and two watering logs.
    care_service, _task_store = care_stack
    confirmations = _recording(care_service)
    service, store = _task_service(care_service)
    x = uuid4()

    _complete(service, x)  # A
    store[TASK_KEY] = store[TASK_KEY].model_copy(update={"status": TaskStatus.PENDING, "completed_at": None})
    _complete(service)  # B, no id - the task keeps A's id
    assert store[TASK_KEY].completion_client_event_id == str(x)
    assert _complete(service, x).replayed  # the late replay of A

    assert [c.completion_client_event_id for c in confirmations] == [str(x), None]
    assert care_service._watering_log_repo.create.call_count == 2  # noqa: SLF001
