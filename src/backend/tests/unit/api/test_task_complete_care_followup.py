"""#761 — completing a watering task in the queue schedules the next occurrence.

``POST /t/{tenant}/tasks/{key}/complete`` is the task-queue half of the care
bridge: it closes the care-reminder task, records the confirmation and asks
:meth:`CareReminderService.ensure_next_watering_task` for the follow-up. Because
the task is already ``COMPLETED`` at that point, the #509 recency rule ("a task
completed today satisfies the reminder") vetoed the follow-up — the same defect
E2E TC-004-092 exposed on the watering-log path.

The router function is exercised directly with a stub ``TaskService`` and a real
``CareReminderService`` over the faithful care-task repository model, so the
assertion is behavioural (one pending follow-up) rather than a call-shape mock.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from starlette.requests import Request

from app.api.v1.tasks.schemas import TaskCompleteRequest
from app.api.v1.tasks.tenant_router import complete_task
from app.common.enums import ReminderType, TaskCategory, TaskStatus, TenantRole
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.task import Task
from app.domain.models.task_completion import TaskCompletionOutcome
from app.domain.models.tenant_context import TenantContext
from app.domain.services.care_reminder_service import CareReminderService
from tests.unit.domain.services.care_task_fakes import FakeTaskRepo

PLANT_KEY = "plant-1"
TENANT = "tenant-A"
TASK_KEY = "task-due"


def _ctx() -> TenantContext:
    return TenantContext(tenant_key=TENANT, tenant_slug="personal", user_key="user-a", role=TenantRole.LEAD)


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


def _request() -> Request:
    """The limiter wraps the handler and wants a real request; a bare scope is enough to be counted."""
    return Request({"type": "http", "method": "POST", "path": "/", "headers": [], "query_string": b""})


class _TaskServiceStub:
    def __init__(self, completed: Task) -> None:
        self._completed = completed

    def get_task(self, key: str, tenant_key: str = "") -> Task:
        return self._completed

    def complete_task(self, key: str, *args, **kwargs) -> Task:
        return self._completed

    def complete_task_once(self, key: str, *args, **kwargs) -> TaskCompletionOutcome:
        # The route's entry point since REQ-053 WP 9.3; without a client id it is ``complete_task``.
        return TaskCompletionOutcome(self.complete_task(key, *args, **kwargs))


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


def test_completing_a_watering_task_schedules_the_next_occurrence(monkeypatch, care_stack) -> None:
    care_service, task_store = care_stack
    monkeypatch.setattr("app.common.dependencies.get_care_reminder_service", lambda: care_service)
    completed = task_store.store[0]

    response = complete_task(
        _request(),
        TASK_KEY,
        TaskCompleteRequest(),
        ctx=_ctx(),
        service=_TaskServiceStub(completed),  # type: ignore[arg-type]
    )

    assert response.status == TaskStatus.COMPLETED
    pending = task_store.open_care_tasks(ReminderType.WATERING)
    assert len(pending) == 1
    assert pending[0].key != TASK_KEY
    assert pending[0].tenant_key == TENANT
    # The follow-up lookup was the narrowed one — the request closed the task itself.
    assert task_store.lookups[-1]["include_completed_today"] is False


class _ReplayingStub(_TaskServiceStub):
    """The first call commits (not a replay), every later one is a replay of it (REQ-053 WP 9.3)."""

    def __init__(self, completed: Task) -> None:
        super().__init__(completed)
        self.calls = 0

    def complete_task_once(self, key: str, *args, **kwargs) -> TaskCompletionOutcome:
        self.calls += 1
        return TaskCompletionOutcome(self._completed, replayed=self.calls > 1, client_event_id="ce-1")


def test_a_replay_records_the_confirmation_a_crashed_first_attempt_lost_and_only_once(monkeypatch, care_stack):
    # REQ-053 WP 9.3: the first attempt committed and died before its follow-up; the replay must record the
    # confirmation, and a further replay must not record it twice.
    care_service, task_store = care_stack
    repo = care_service._repo  # noqa: SLF001 - the MagicMock the fixture built
    confirmations: list[CareConfirmation] = []
    repo.find_confirmation_by_completion.side_effect = lambda plant_key, client_id: next(
        (c for c in confirmations if c.completion_client_event_id == client_id), None
    )
    repo.create_confirmation_logged.side_effect = lambda confirmation, **_: confirmations.append(confirmation)
    completed = task_store.store[0].model_copy(update={"completion_client_event_id": "ce-1"})
    task_store.store[0] = completed
    stub = _ReplayingStub(completed)

    def crashed() -> CareReminderService:
        raise RuntimeError("the process died between the commit and the follow-up")

    monkeypatch.setattr("app.common.dependencies.get_care_reminder_service", crashed)
    with pytest.raises(RuntimeError):
        complete_task(_request(), TASK_KEY, TaskCompleteRequest(), ctx=_ctx(), service=stub)  # type: ignore[arg-type]
    assert confirmations == []

    monkeypatch.setattr("app.common.dependencies.get_care_reminder_service", lambda: care_service)
    for _ in range(2):
        complete_task(_request(), TASK_KEY, TaskCompleteRequest(), ctx=_ctx(), service=stub)  # type: ignore[arg-type]

    assert [c.completion_client_event_id for c in confirmations] == ["ce-1"]
    assert len(task_store.open_care_tasks(ReminderType.WATERING)) == 1  # the next occurrence once, too


def test_a_replay_of_a_reopened_task_runs_no_follow_up(monkeypatch, care_stack):
    care_service, task_store = care_stack
    repo = care_service._repo  # noqa: SLF001
    repo.find_confirmation_by_completion.return_value = None
    reopened = task_store.store[0].model_copy(update={"status": TaskStatus.PENDING, "completion_client_event_id": "c"})
    stub = _ReplayingStub(reopened)
    stub.calls = 1  # every call is a replay
    monkeypatch.setattr("app.common.dependencies.get_care_reminder_service", lambda: care_service)

    complete_task(_request(), TASK_KEY, TaskCompleteRequest(), ctx=_ctx(), service=stub)  # type: ignore[arg-type]

    repo.create_confirmation_logged.assert_not_called()


class _ScriptedStub(_TaskServiceStub):
    """Answers the outcomes it is given, in order: what the route sees of A, a reopen, B and a late replay."""

    def __init__(self, completed: Task, outcomes: list[tuple[bool, str | None]]) -> None:
        super().__init__(completed)
        self._outcomes = list(outcomes)

    def complete_task_once(self, key: str, *args, **kwargs) -> TaskCompletionOutcome:
        replayed, client_id = self._outcomes.pop(0)
        return TaskCompletionOutcome(self._completed, replayed=replayed, client_event_id=client_id)


def test_a_completion_without_an_id_after_a_reopen_confirms_again_and_a_late_replay_does_not(monkeypatch, care_stack):
    # Verifying review of #2787 (F1): A completed with id X, the task was reopened, B completed it WITHOUT an id -
    # the task still carries X. B's confirmation must not be deduped against A's, and a late replay of X confirms
    # nothing more: exactly two confirmations and two watering logs.
    care_service, task_store = care_stack
    repo = care_service._repo  # noqa: SLF001
    confirmations: list[CareConfirmation] = []
    repo.find_confirmation_by_completion.side_effect = lambda plant_key, client_id: next(
        (c for c in confirmations if c.completion_client_event_id == client_id), None
    )
    repo.create_confirmation_logged.side_effect = lambda confirmation, **_: confirmations.append(confirmation)
    stale = task_store.store[0].model_copy(update={"completion_client_event_id": "X"})  # A's id stays on the task
    stub = _ScriptedStub(stale, [(False, "X"), (False, None), (True, "X")])
    monkeypatch.setattr("app.common.dependencies.get_care_reminder_service", lambda: care_service)

    for _ in range(3):  # A, then B (no id), then the late replay of A
        complete_task(_request(), TASK_KEY, TaskCompleteRequest(), ctx=_ctx(), service=stub)  # type: ignore[arg-type]

    assert [c.completion_client_event_id for c in confirmations] == ["X", None]
    assert care_service._watering_log_repo.create.call_count == 2  # noqa: SLF001
