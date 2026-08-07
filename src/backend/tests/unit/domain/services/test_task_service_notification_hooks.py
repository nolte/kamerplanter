"""Wiring tests: TaskService mutations fan out to notification propagation (#742).

These verify the *coupling* — that create/update/complete/delete/batch_assign each
invoke the right :class:`NotificationPropagationService` hook — while the
propagation *behaviour* is covered by test_notification_propagation_service.py.
The propagation collaborator is a ``MagicMock`` so a hook is asserted on its call.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ValidationError
from app.domain.models.task import Task
from app.domain.services.task_service import TaskService


@pytest.fixture
def repo() -> MagicMock:
    repo = MagicMock()
    repo.create_task.side_effect = lambda task: task
    repo.update_task.side_effect = lambda key, task: task
    repo.delete_task.return_value = True
    return repo


@pytest.fixture
def propagation() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(repo, propagation) -> TaskService:
    return TaskService(repo, MagicMock(), MagicMock(), notification_propagation=propagation)


def _task(**kwargs) -> Task:
    defaults = {
        "_key": "task1",
        "tenant_key": "t1",
        "name": "Prune apple tree",
        "status": "pending",
        "due_date": datetime(2026, 7, 24, tzinfo=UTC),
        "assigned_to_user_key": "user-a",
    }
    defaults.update(kwargs)
    return Task(**defaults)


def test_create_task_syncs_due_notification(service, propagation):
    service.create_task(_task(assigned_to_user_key=None))
    propagation.sync_task_due_notification.assert_called_once()


def test_create_assigned_task_also_reassigns(service, propagation):
    service.create_task(_task(assigned_to_user_key="user-a"))
    propagation.on_task_reassigned.assert_called_once()


def test_update_task_due_change_syncs(service, propagation, repo):
    previous = _task()
    moved = _task(due_date=datetime(2026, 7, 28, tzinfo=UTC))
    service.update_task("task1", moved, previous=previous)
    propagation.sync_task_due_notification.assert_called_once()
    propagation.on_task_reassigned.assert_not_called()


def test_update_task_reassignment_moves_notifications(service, propagation):
    previous = _task(assigned_to_user_key="user-a")
    reassigned = _task(assigned_to_user_key="user-b")
    service.update_task("task1", reassigned, previous=previous)
    propagation.on_task_reassigned.assert_called_once()
    _, kwargs = propagation.on_task_reassigned.call_args
    assert kwargs["previous_user_key"] == "user-a"


def test_complete_task_marks_notification_done(service, propagation, repo):
    repo.get_task_or_raise.return_value = _task(status="pending", requires_photo=False)
    service.complete_task("task1", tenant_key="t1")
    propagation.on_task_completed.assert_called_once()


def test_delete_task_removes_notification(service, propagation, repo):
    repo.get_task_or_raise.return_value = _task(status="pending")
    service.delete_task("task1", tenant_key="t1")
    propagation.on_task_deleted.assert_called_once()


def test_delete_disallowed_status_does_not_propagate(service, propagation, repo):
    repo.get_task_or_raise.return_value = _task(status="completed")
    with pytest.raises(ValidationError):
        service.delete_task("task1", tenant_key="t1")
    propagation.on_task_deleted.assert_not_called()


def test_batch_assign_propagates_reassignment(service, propagation, repo):
    repo.get_task_or_raise.return_value = _task(assigned_to_user_key="user-a")
    # ``tenant_key`` is required and keyword-only since #948 — the batch routes
    # were the ones that forgot the guard every single-task route applies.
    service.batch_assign(["task1"], "user-b", tenant_key="t1")
    propagation.on_task_reassigned.assert_called_once()


def test_batch_assign_noop_when_same_assignee(service, propagation, repo):
    repo.get_task_or_raise.return_value = _task(assigned_to_user_key="user-a")
    service.batch_assign(["task1"], "user-a", tenant_key="t1")
    propagation.on_task_reassigned.assert_not_called()


def test_no_propagation_service_is_safe(repo):
    """A TaskService without the coupling wired must not crash on mutations."""
    service = TaskService(repo, MagicMock(), MagicMock())
    repo.get_task_or_raise.return_value = _task(status="pending")
    # Should complete without raising even though no propagation is wired.
    service.create_task(_task())
    service.delete_task("task1", tenant_key="t1")
