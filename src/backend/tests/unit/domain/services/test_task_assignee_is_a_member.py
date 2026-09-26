"""A task can only be assigned to an active member of its tenant — #1871 B9.

``assigned_to_user_key`` came from the create body, the update body and the
batch-assign body and was stored as given; the assignment then produced a
``task.assigned`` notification for that user (``notification_propagation_service``).
A member of tenant A could assign A's tasks — and send notifications naming
them — to any user of the installation. The service now resolves the assignee
against the task's tenant on every path that sets or changes it; an assignee
that is not an active member is refused like an unknown one (404, no oracle
about which user keys exist).
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.task import Task
from app.domain.services.task_service import TaskService

_MEMBERS = {("t1", "member"), ("t1", "left")}
_INACTIVE = {("t1", "left")}


def _membership(user_key: str, tenant_key: str):
    if (tenant_key, user_key) not in _MEMBERS:
        return None
    return SimpleNamespace(is_active=(tenant_key, user_key) not in _INACTIVE)


def _service() -> tuple[TaskService, MagicMock, MagicMock]:
    repo = MagicMock()
    repo.create_task.side_effect = lambda task: task
    repo.update_task.side_effect = lambda key, task: task
    repo.get_task_or_raise.side_effect = lambda key: _task(assigned_to_user_key=None).model_copy(update={"key": key})
    propagation = MagicMock()
    service = TaskService(
        repo, MagicMock(), MagicMock(), notification_propagation=propagation, membership_lookup=_membership
    )
    return service, repo, propagation


def _task(**kwargs) -> Task:
    defaults = {"_key": "task1", "tenant_key": "t1", "name": "Gießen", "due_date": datetime(2026, 9, 1, tzinfo=UTC)}
    defaults.update(kwargs)
    return Task(**defaults)


@pytest.mark.parametrize("assignee", ["stranger", "left", "member-of-another-tenant"])
def test_a_task_is_not_assigned_to_someone_who_is_not_an_active_member(assignee: str) -> None:
    service, repo, propagation = _service()

    with pytest.raises(NotFoundError):
        service.create_task(_task(assigned_to_user_key=assignee))
    with pytest.raises(NotFoundError):
        service.update_task("task1", _task(assigned_to_user_key=assignee), previous=_task())
    succeeded, failed = service.batch_assign(["task1"], assignee, tenant_key="t1")

    assert succeeded == [] and len(failed) == 1
    repo.create_task.assert_not_called()
    repo.update_task.assert_not_called()
    propagation.on_task_reassigned.assert_not_called()


def test_an_active_member_is_assigned_on_every_path() -> None:
    service, repo, propagation = _service()

    service.create_task(_task(assigned_to_user_key="member"))
    service.update_task("task1", _task(assigned_to_user_key="member"), previous=_task())
    succeeded, _failed = service.batch_assign(["task1"], "member", tenant_key="t1")

    assert succeeded == ["task1"]
    assert propagation.on_task_reassigned.call_count == 3


def test_an_unassigned_task_needs_no_lookup_and_clearing_an_assignee_is_allowed() -> None:
    repo = MagicMock()
    repo.create_task.side_effect = lambda task: task
    repo.update_task.side_effect = lambda key, task: task
    service = TaskService(repo, MagicMock(), MagicMock())

    service.create_task(_task(assigned_to_user_key=None))
    service.update_task("task1", _task(assigned_to_user_key=None), previous=_task(assigned_to_user_key="member"))


def test_without_a_membership_lookup_an_assignment_is_refused() -> None:
    repo = MagicMock()
    service = TaskService(repo, MagicMock(), MagicMock())

    with pytest.raises(NotFoundError):
        service.create_task(_task(assigned_to_user_key="member"))
