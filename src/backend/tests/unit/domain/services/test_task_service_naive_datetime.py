"""Regression tests: TaskService tolerates naive/aware datetime mixes.

A date-only ``due_date`` is persisted timezone-naive, while ``completed_at`` and
freshly parsed timestamps are timezone-aware. Comparing the two raised
``TypeError`` and (a) crashed the task queue through
``_deduplicate_care_tasks`` and (b) aborted the recurrence follow-up in
``complete_task`` (via ``_reschedule_dependents``) before the next instance
could be created. These tests pin both paths against the real domain engines so
the coercion cannot silently regress.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.domain.engines.dependency_resolver import DependencyResolver
from app.domain.models.task import Task
from app.domain.services.task_service import TaskService


@pytest.fixture
def service_with_real_deps() -> tuple[TaskService, MagicMock]:
    """A TaskService wired with a real DependencyResolver + RecurrenceEngine.

    Only the repository is mocked; the resolver runs for real so the
    naive/aware comparison that used to crash is actually exercised.
    """
    repo = MagicMock()
    service = TaskService(repo, MagicMock(), DependencyResolver())
    return service, repo


def test_complete_recurring_task_with_naive_due_date_spawns_followup(
    service_with_real_deps: tuple[TaskService, MagicMock],
) -> None:
    """Completing a recurring task with a naive due_date must not crash and must spawn."""
    service, repo = service_with_real_deps
    task = Task(
        key="t1",
        tenant_key="tenant1",
        name="Water plant",
        category="care_reminder",
        status="pending",
        due_date=datetime(2026, 7, 23),  # naive, date-only (the crashing shape)
        recurrence_rule="FREQ=WEEKLY",
    )
    repo.get_task_or_raise.return_value = task
    repo.update_task.side_effect = lambda key, updated: updated
    repo.get_blocking_tasks.return_value = []

    created: dict[str, Task] = {}

    def _create(new_task: Task) -> Task:
        created["task"] = new_task
        return new_task

    repo.create_task.side_effect = _create

    result = service.complete_task("t1")

    assert result.status == "completed"
    repo.create_task.assert_called_once()

    follow_up = created["task"]
    assert follow_up.status == "pending"
    assert follow_up.recurrence_rule == "FREQ=WEEKLY"
    assert follow_up.parent_recurring_task_key == "t1"
    assert follow_up.due_date is not None
    assert follow_up.due_date > datetime.now(UTC)


def test_deduplicate_care_tasks_tolerates_mixed_timezone(
    service_with_real_deps: tuple[TaskService, MagicMock],
) -> None:
    """Grouping care tasks with mixed tz-awareness must collapse without a TypeError."""
    service, _repo = service_with_real_deps
    aware = Task(
        key="a",
        tenant_key="t",
        name="Water",
        category="care_reminder",
        due_date=datetime(2026, 7, 30, tzinfo=UTC),
    )
    naive = Task(
        key="b",
        tenant_key="t",
        name="Water",
        category="care_reminder",
        due_date=datetime(2026, 7, 23),  # naive
    )

    result = service._deduplicate_care_tasks([aware, naive])

    # Same tenant + name -> one survivor, and no comparison crash.
    assert len(result) == 1
    assert result[0].key in {"a", "b"}
