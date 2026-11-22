"""GP-ACC-038 (REQ-053 M5, #2325): a task with a cron ``recurrence_rule`` is refused at the service with 422.

The create and the update path both run ``RecurrenceEngine.require_rrule`` before any
write, so the repository never sees a non-RRULE rule; the error carries the code
``recurrence.rrule_required`` the frontend can explain.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import RecurrenceRuleRequiredError
from app.domain.models.task import Task
from app.domain.services.task_service import TaskService


class _Repo:
    def __init__(self) -> None:
        self.created: list[Task] = []
        self.updated: list[tuple[str, Task]] = []

    def create_task(self, task: Task) -> Task:
        self.created.append(task)
        return task.model_copy(update={"key": "t1"})

    def update_task(self, key: str, task: Task) -> Task:
        self.updated.append((key, task))
        return task.model_copy(update={"key": key})


@pytest.fixture
def repo() -> _Repo:
    return _Repo()


@pytest.fixture
def service(repo: _Repo) -> TaskService:
    return TaskService(repo, MagicMock(), MagicMock())  # type: ignore[arg-type]


@pytest.mark.parametrize("rule", ["0 8 * * 1", "*/15 * * * *", "every monday"])
def test_create_refuses_a_non_rrule_before_writing(service: TaskService, repo: _Repo, rule: str) -> None:
    with pytest.raises(RecurrenceRuleRequiredError) as excinfo:
        service.create_task(Task(name="Mulchen", recurrence_rule=rule))

    assert excinfo.value.status_code == 422
    assert excinfo.value.error_code == "recurrence.rrule_required"
    assert repo.created == []


def test_update_refuses_a_non_rrule_before_writing(service: TaskService, repo: _Repo) -> None:
    with pytest.raises(RecurrenceRuleRequiredError):
        service.update_task("t1", Task(name="Mulchen", recurrence_rule="0 8 * * 1"))

    assert repo.updated == []


@pytest.mark.parametrize("rule", [None, "", "FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0"])
def test_an_rrule_or_no_rule_is_written(service: TaskService, repo: _Repo, rule: str | None) -> None:
    created = service.create_task(Task(name="Mulchen", recurrence_rule=rule))

    assert created.recurrence_rule == rule
    assert len(repo.created) == 1
