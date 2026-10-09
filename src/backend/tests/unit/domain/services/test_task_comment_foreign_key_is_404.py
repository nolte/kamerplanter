"""A comment key that is not the addressed task's answers 404, not 422 — MT-045.7 (#2144).

``PUT``/``DELETE /t/{slug}/tasks/{task_key}/comments/{comment_key}`` scoped the
*task* to the caller's tenant, then loaded the comment by key alone and answered
``422 "Comment does not belong to this task."`` when it was another task's. The
caller's own task plus any comment key thus told "this key exists somewhere"
(422) from "no such key" (404) — an existence oracle over every tenant's
comments. A comment of another task now answers exactly like a missing one.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import NotFoundError
from app.domain.models.task import Task, TaskComment
from app.domain.services.task_service import TaskService


class _Repo:
    def __init__(self) -> None:
        self.tasks = {
            "own": Task(_key="own", tenant_key="t-a", name="mine", status="pending"),
            "foreign": Task(_key="foreign", tenant_key="t-b", name="theirs", status="pending"),
        }
        self.comments = {
            "c-own": TaskComment(_key="c-own", task_key="own", comment_text="hi", created_by="u"),
            "c-foreign": TaskComment(_key="c-foreign", task_key="foreign", comment_text="secret", created_by="v"),
        }
        self.updated: list[str] = []
        self.deleted: list[str] = []

    def get_task_or_raise(self, key: str) -> Task:
        if key not in self.tasks:
            raise NotFoundError("Task", key)
        return self.tasks[key]

    def get_comment_or_raise(self, key: str) -> TaskComment:
        if key not in self.comments:
            raise NotFoundError("TaskComment", key)
        return self.comments[key]

    def update_comment(self, key: str, comment: TaskComment) -> TaskComment:
        self.updated.append(key)
        return comment

    def delete_comment(self, key: str) -> bool:
        self.deleted.append(key)
        return True


@pytest.fixture
def repo() -> _Repo:
    return _Repo()


@pytest.fixture
def service(repo: _Repo) -> TaskService:
    return TaskService(repo, MagicMock(), MagicMock())  # type: ignore[arg-type]


@pytest.mark.parametrize("comment_key", ["c-foreign", "no-such-comment"], ids=["another-tasks", "absent"])
def test_updating_a_comment_that_is_not_the_tasks_is_404(service: TaskService, repo: _Repo, comment_key: str) -> None:
    with pytest.raises(NotFoundError):
        service.update_comment("own", comment_key, "overwritten", tenant_key="t-a")
    assert repo.updated == []


@pytest.mark.parametrize("comment_key", ["c-foreign", "no-such-comment"], ids=["another-tasks", "absent"])
def test_deleting_a_comment_that_is_not_the_tasks_is_404(service: TaskService, repo: _Repo, comment_key: str) -> None:
    with pytest.raises(NotFoundError):
        service.delete_comment("own", comment_key, tenant_key="t-a")
    assert repo.deleted == []


def test_the_tasks_own_comment_is_still_editable(service: TaskService, repo: _Repo) -> None:
    service.update_comment("own", "c-own", "edited", tenant_key="t-a")
    service.delete_comment("own", "c-own", tenant_key="t-a")
    assert repo.updated == ["c-own"]
    assert repo.deleted == ["c-own"]
