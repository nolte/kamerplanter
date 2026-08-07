"""Fail-closed tenant isolation for ``TaskService`` (GHSA-h5wp-r68x-97g8).

The advisory's durable fix removes the ``tenant_key: str = ""`` default on
``TaskService.get_task`` so a forgotten argument fails **closed** rather than
open. These tests pin both directions, driving real ``Task`` domain objects
through an in-memory repository (a mock that never becomes a model would prove
nothing, cf. #996):

* an omitted / empty ``tenant_key`` is refused before any read or mutation,
* a foreign tenant is refused with ``NotFoundError`` (HTTP 404 — not 403 — so
  the endpoints do not become a cross-tenant existence oracle),
* the owning tenant can still read and mutate its own task.
"""

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.task import Task
from app.domain.services.task_service import TaskService


class _InMemoryTaskRepo:
    """Minimal repository holding one real ``Task`` owned by ``tenant-B``."""

    def __init__(self, task: Task) -> None:
        self._task = task

    def get_task_or_raise(self, key: str) -> Task:
        if key != self._task.key:
            raise NotFoundError("Task", key)
        return self._task

    def update_task(self, key: str, task: Task) -> Task:
        self._task = task
        return task

    def delete_task(self, key: str) -> bool:
        return True


@pytest.fixture
def owner_key() -> str:
    return "tenant-B"


@pytest.fixture
def foreign_key() -> str:
    return "tenant-A"


@pytest.fixture
def task_b(owner_key: str) -> Task:
    return Task(key="900001", tenant_key=owner_key, name="B's private task", status="pending")


@pytest.fixture
def service(task_b: Task) -> TaskService:
    from unittest.mock import MagicMock

    return TaskService(_InMemoryTaskRepo(task_b), MagicMock(), MagicMock())


# ── Negative direction: the gap must fail closed ──


def test_get_task_without_tenant_key_is_a_call_error(service: TaskService) -> None:
    """Omitting ``tenant_key`` cannot even be called — the parameter is required."""
    with pytest.raises(TypeError):
        service.get_task("900001")  # type: ignore[call-arg]


def test_get_task_with_empty_tenant_key_is_rejected(service: TaskService) -> None:
    """The empty sentinel that used to skip the check now raises (fail-closed)."""
    with pytest.raises(ValueError, match="tenant-scoped"):
        service.get_task("900001", tenant_key="")


@pytest.mark.parametrize(
    "call",
    [
        lambda s: s.start_task("900001"),
        lambda s: s.skip_task("900001"),
        lambda s: s.complete_task("900001"),
        lambda s: s.delete_task("900001"),
        lambda s: s.reopen_task("900001"),
        lambda s: s.clone_task("900001"),
        lambda s: s.add_photo_ref("900001", "http://example.test/p.jpg"),
        lambda s: s.create_comment("900001", "text", "user"),
        lambda s: s.get_task_history("900001"),
    ],
)
def test_mutating_and_reading_methods_require_tenant_key(service: TaskService, call) -> None:
    """None of the task-scoped methods can be invoked without ``tenant_key``."""
    with pytest.raises(TypeError):
        call(service)


def test_get_task_for_foreign_tenant_raises_not_found(service: TaskService, foreign_key: str) -> None:
    """A foreign tenant is refused with NotFoundError (-> 404), not a 403 oracle."""
    with pytest.raises(NotFoundError):
        service.get_task("900001", tenant_key=foreign_key)


def test_mutation_by_foreign_tenant_is_refused_before_write(service: TaskService, foreign_key: str) -> None:
    """A foreign tenant cannot mutate; the task stays pending (no write happened)."""
    with pytest.raises(NotFoundError):
        service.start_task("900001", tenant_key=foreign_key)
    # The task was never mutated by the refused call.
    assert service.get_task("900001", tenant_key="tenant-B").status == "pending"


# ── Positive direction: the owner still works (catches an over-broad refusal) ──


def test_owner_can_read_own_task(service: TaskService, owner_key: str) -> None:
    task = service.get_task("900001", tenant_key=owner_key)
    assert task.key == "900001"
    assert task.tenant_key == owner_key


def test_owner_can_mutate_own_task(service: TaskService, owner_key: str) -> None:
    started = service.start_task("900001", tenant_key=owner_key)
    assert started.status == "in_progress"
