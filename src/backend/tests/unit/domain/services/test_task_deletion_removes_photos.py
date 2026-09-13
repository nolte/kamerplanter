"""#1393 decision 2 — deleting a task takes its photos with it.

Before this, `TaskService.delete_task` deleted the document and propagated a
notification, and never touched the attachments it referenced. Every photo the task
carried outlived it, counting against ``STORAGE_TENANT_QUOTA_MB`` with no surface
in the product that reached it for the ``task`` category.

**Why deleting them is safe, and why that argument belongs in a test rather than a
comment.** A task is deletable only in ``pending``/``skipped``/``dormant`` — a
completed task's documentation can never be lost this way. That
status gate is the whole justification, so it is asserted here: if the gate ever
widens to admit ``completed``, this file goes red and whoever widened it has to
decide about the photos again, rather than discovering the loss afterwards.

Asserted on the dispatch, not on the storage backend: the deletion itself is
`AttachmentService.delete`, which has its own tests. What is new here is that
something asks for it, with the right ids and the right tenant.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.common.exceptions import ValidationError
from app.domain.models.task import Task
from app.domain.services.task_service import TaskService

TENANT = "tenant-B"


class _InMemoryTaskRepo:
    def __init__(self, task: Task) -> None:
        self._task = task
        self.deleted: list[str] = []

    def get_task_or_raise(self, key: str) -> Task:
        return self._task

    def delete_task(self, key: str) -> bool:
        self.deleted.append(key)
        return True


def _service(task: Task) -> tuple[TaskService, _InMemoryTaskRepo]:
    repo = _InMemoryTaskRepo(task)
    return TaskService(repo, MagicMock(), MagicMock()), repo


def _task(**overrides) -> Task:
    fields = {
        "key": "900001",
        "tenant_key": TENANT,
        "name": "Giessen",
        "status": "pending",
        "photo_refs": ["att-1", "att-2"],
    }
    fields.update(overrides)
    return Task(**fields)


class TestDeletingATaskDeletesItsPhotos:
    def test_the_deletion_is_dispatched_with_the_ids_and_the_tenant(self):
        service, _repo = _service(_task())

        with patch("app.tasks.storage_tasks.delete_attachments") as dispatch:
            service.delete_task("900001", tenant_key=TENANT)

        dispatch.delay.assert_called_once_with(["att-1", "att-2"], TENANT)

    def test_a_task_without_photos_dispatches_nothing(self):
        """No empty job, and no Celery import on the common path."""
        service, _repo = _service(_task(photo_refs=[]))

        with patch("app.tasks.storage_tasks.delete_attachments") as dispatch:
            service.delete_task("900001", tenant_key=TENANT)

        dispatch.delay.assert_not_called()

    def test_nothing_is_dispatched_when_the_document_was_not_deleted(self):
        """The photos follow the document. If it survived, so do they."""
        service, repo = _service(_task())
        repo.delete_task = lambda key: False  # type: ignore[method-assign]

        with patch("app.tasks.storage_tasks.delete_attachments") as dispatch:
            service.delete_task("900001", tenant_key=TENANT)

        dispatch.delay.assert_not_called()


class TestTheDispatchCannotBreakTheDeletion:
    def test_a_failing_dispatch_does_not_fail_the_request(self):
        """The document is already gone by then.

        Raising here would answer 500 for an operation that succeeded, and would
        leave the caller believing the task is still there. The orphan sweep is the
        backstop: deleting the document is precisely what makes those photos
        unreferenced, so the next run collects them.
        """
        service, _repo = _service(_task())

        with patch("app.tasks.storage_tasks.delete_attachments") as dispatch:
            dispatch.delay.side_effect = RuntimeError("broker unreachable")

            assert service.delete_task("900001", tenant_key=TENANT) is True


class TestTheStatusGateIsTheSafetyArgument:
    # `cancelled` is deliberately absent: `TaskStatus` has no such member, so the
    # entry the service's allowlist carried for it could never match. See the
    # dead-entry test below.
    @pytest.mark.parametrize("status", ["pending", "skipped", "dormant"])
    def test_a_deletable_status_is_still_deletable(self, status: str):
        service, _repo = _service(_task(status=status))

        with patch("app.tasks.storage_tasks.delete_attachments"):
            assert service.delete_task("900001", tenant_key=TENANT) is True

    @pytest.mark.parametrize("status", ["completed", "in_progress"])
    def test_a_completed_task_cannot_be_deleted_so_its_photos_are_never_lost(self, status: str):
        """The premise of decision 2, pinned.

        Widening the gate to admit a status whose photos are documentation rather
        than staging turns this red, which is the moment to decide about the photos
        again — not after a user has lost some.
        """
        service, _repo = _service(_task(status=status))

        with patch("app.tasks.storage_tasks.delete_attachments") as dispatch, pytest.raises(ValidationError):
            service.delete_task("900001", tenant_key=TENANT)

        dispatch.delay.assert_not_called()


class TestTheAllowlistNamesOnlyRealStatuses:
    """The gate used to allow ``cancelled``, which `TaskStatus` does not have.

    Pydantic rejects the value on the model, so that row could never match anything
    — an allowlist entry that cannot fire, describing a state machine this codebase
    does not have. It was removed; this keeps a replacement from being typed in.

    Read off the service rather than restated, so the two cannot drift: a set
    transcribed here would keep passing while the real one grew a ghost.
    """

    def test_every_deletable_status_exists_on_the_enum(self):
        import inspect

        from app.common.enums import TaskStatus

        source = inspect.getsource(TaskService.delete_task)
        line = next(line for line in source.splitlines() if line.strip().startswith("allowed = {"))
        named = {part.strip().strip('"') for part in line.split("{", 1)[1].rstrip("}").split(",") if part.strip()}

        real = {status.value for status in TaskStatus}
        ghosts = sorted(named - real)

        assert not ghosts, (
            f"delete_task allows {ghosts}, which TaskStatus does not have — the row can never "
            f"match. Valid values: {sorted(real)}"
        )

    def test_the_allowlist_was_actually_found(self):
        """The control: a parser that found nothing would pass the test above silently."""
        import inspect

        source = inspect.getsource(TaskService.delete_task)
        line = next(line for line in source.splitlines() if line.strip().startswith("allowed = {"))
        named = {part.strip().strip('"') for part in line.split("{", 1)[1].rstrip("}").split(",") if part.strip()}

        assert "pending" in named and len(named) >= 3
