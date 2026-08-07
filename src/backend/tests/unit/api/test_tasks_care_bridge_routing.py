"""The task-queue care bridges are routed through the service, not around it.

Both ``POST /tasks/{key}/complete`` and ``POST /tasks/{key}/skip`` mirror a care
task into the plant's care state. The skip endpoint used to do that *inline*,
reaching around the care service into its repository and engine — a 5-layer
violation (NFR-001) that also bypassed the service-side tenant guard on the
plant the task points at (SEC-001): a guard added to the service alone would
simply not have been reached.

These tests pin the routing itself: the router delegates to the service with the
request's ``tenant_key`` and touches no private service internals. The care-state
behaviour behind those calls is covered in
``tests/unit/domain/services/test_care_task_queue_bridge.py``.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.api.v1.tasks.schemas import TaskCompleteRequest
from app.api.v1.tasks.tenant_router import complete_task, skip_task
from app.common.enums import TaskCategory, TaskStatus, TenantRole
from app.domain.models.task import Task
from app.domain.models.tenant_context import TenantContext

TENANT = "tenant-A"
PLANT_KEY = "plant-1"


def _ctx() -> TenantContext:
    return TenantContext(
        tenant_key=TENANT,
        tenant_slug="personal",
        user_key="user-a",
        role=TenantRole.LEAD,
    )


def _care_task(status: TaskStatus) -> Task:
    return Task(
        _key="task-1",
        name="Strawberry — watering",
        category=TaskCategory.CARE_REMINDER,
        entity_key=PLANT_KEY,
        entity_type="plant_instance",
        tenant_key=TENANT,
        status=status,
        due_date=datetime.now(UTC),
    )


class _TaskServiceStub:
    """Minimal ``TaskService`` slice: returns the task the endpoints operate on."""

    def __init__(self, task: Task) -> None:
        self._task = task
        self.get_task_calls: list[tuple[str, str]] = []
        self.skip_calls: list[tuple[str, str]] = []
        self.complete_calls: list[tuple[str, str]] = []

    def get_task(self, key: str, *, tenant_key: str) -> Task:
        self.get_task_calls.append((key, tenant_key))
        return self._task

    def complete_task(self, key, *args, tenant_key: str, **kwargs) -> Task:  # noqa: ANN002, ANN003 — router passes positionals
        self.complete_calls.append((key, tenant_key))
        return self._task

    def skip_task(self, key: str, *, tenant_key: str) -> Task:
        self.skip_calls.append((key, tenant_key))
        return self._task


class _CareServiceStub:
    """Care service that records bridge calls and forbids private access.

    ``_repo``/``_engine`` raise on attribute access, so the previous
    reach-around implementation would fail this test instead of silently
    re-appearing.
    """

    def __init__(self) -> None:
        self.completions: list[tuple[Task, str]] = []
        self.skips: list[tuple[Task, str]] = []

    def __getattr__(self, name: str):  # noqa: ANN204 — test guard
        raise AssertionError(f"the router must not touch the care service's private {name!r}")

    def record_care_task_completion(self, task: Task, *, tenant_key: str = "") -> None:
        self.completions.append((task, tenant_key))
        return None

    def record_care_task_skip(self, task: Task, *, tenant_key: str = "") -> None:
        self.skips.append((task, tenant_key))
        return None


@pytest.fixture
def care_stub(monkeypatch: pytest.MonkeyPatch) -> _CareServiceStub:
    """Install the care-service stub behind the router's lazy DI lookup."""
    import app.common.dependencies as dependencies

    stub = _CareServiceStub()
    monkeypatch.setattr(dependencies, "get_care_reminder_service", lambda: stub)
    return stub


def test_skip_delegates_to_the_service_with_the_request_tenant(care_stub: _CareServiceStub) -> None:
    task = _care_task(TaskStatus.SKIPPED)
    service = _TaskServiceStub(task)

    skip_task("task-1", ctx=_ctx(), service=service)  # type: ignore[arg-type]

    assert [(t.key, tenant) for t, tenant in care_stub.skips] == [("task-1", TENANT)]
    # The request tenant is threaded into the mutating service call itself, which
    # now owns the ownership check (GHSA-h5wp-r68x-97g8) instead of a separate
    # router pre-check.
    assert service.skip_calls == [("task-1", TENANT)]


def test_complete_delegates_to_the_service_with_the_request_tenant(care_stub: _CareServiceStub) -> None:
    task = _care_task(TaskStatus.COMPLETED)
    service = _TaskServiceStub(task)

    complete_task("task-1", TaskCompleteRequest(), ctx=_ctx(), service=service)  # type: ignore[arg-type]

    assert [(t.key, tenant) for t, tenant in care_stub.completions] == [("task-1", TENANT)]


def test_plain_task_never_builds_a_care_service(care_stub: _CareServiceStub) -> None:
    """A non-care task short-circuits in the presentation layer (no care service)."""
    task = _care_task(TaskStatus.SKIPPED)
    task.category = TaskCategory.MAINTENANCE
    service = _TaskServiceStub(task)

    skip_task("task-1", ctx=_ctx(), service=service)  # type: ignore[arg-type]
    complete_task("task-1", TaskCompleteRequest(), ctx=_ctx(), service=service)  # type: ignore[arg-type]

    assert care_stub.skips == []
    assert care_stub.completions == []
