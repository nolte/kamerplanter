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

from app.api.v1.tasks.schemas import TaskCompleteRequest
from app.api.v1.tasks.tenant_router import complete_task
from app.common.enums import ReminderType, TaskCategory, TaskStatus, TenantRole
from app.domain.engines.care_reminder_engine import CareReminderEngine
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.task import Task
from app.domain.models.tenant_context import TenantContext
from app.domain.services.care_reminder_service import CareReminderService
from tests.unit.domain.services.care_task_fakes import FakeTaskRepo

PLANT_KEY = "plant-1"
TENANT = "tenant-A"
TASK_KEY = "task-due"


def _ctx() -> TenantContext:
    return TenantContext(tenant_key=TENANT, tenant_slug="personal", user_key="user-a", role=TenantRole.ADMIN)


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


class _TaskServiceStub:
    def __init__(self, completed: Task) -> None:
        self._completed = completed

    def get_task(self, key: str, tenant_key: str = "") -> Task:
        return self._completed

    def complete_task(self, key: str, *args, **kwargs) -> Task:
        return self._completed


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
