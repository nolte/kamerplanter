"""#1393 — "was this task ever completed" must survive a second reopen.

``delete_task`` refuses a task that was completed and reopened, because it still
carries the ``photo_refs`` that completion wrote and deleting it would destroy that
record irreversibly. The refusal reads ``task.reopened_from_status == "completed"``.

``reopen_task`` assigned ``task.reopened_from_status = task.status`` unconditionally,
and ``skip_task`` accepts a ``pending`` task while ``reopen_task`` accepts a
``skipped`` one. So:

    complete  → status=completed, photo_refs written
    reopen    → reopened_from_status="completed", status=pending
    skip      → status=skipped                      (photo_refs untouched)
    reopen    → reopened_from_status="skipped"      ← the marker is overwritten
    delete    → both gates pass, photos destroyed

Four ordinary operations, every one of them offered by the UI, and the gate that the
whole "delete photos with the task" decision rests on is gone. Nothing about the
sequence is exotic: reopening a task, deciding not to do it after all, then changing
your mind again is a Tuesday.

**A comment in ``delete_task`` asserted the opposite** — that the marker "is never
cleared — not by completing again, not by skipping — so this is permanent". Both
halves of that are true and the conclusion is false: skipping does not clear it, the
*reopen after* the skip overwrites it. The claim was written from reading
``skip_task``, never from running the sequence, and it is precisely the kind of
confident note that stops the next reader from checking.

The marker is therefore no longer downgraded once it says ``"completed"``. The
alternative anchors were measured and rejected: ``completed_at`` is set to ``None``
by ``reopen_task`` (``task_service.py``), and gating on non-empty ``photo_refs``
would narrow the rule to "carries photos" when the decision taken was "was ever
completed".
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ValidationError
from app.domain.models.task import Task
from app.domain.services.task_service import TaskService

TENANT = "tenant-a"
KEY = "task-1"


def _service(task: Task) -> TaskService:
    service = TaskService.__new__(TaskService)
    repo = MagicMock()
    repo.get_task.return_value = task
    repo.update_task.side_effect = lambda key, updated: updated
    repo.delete_task.return_value = True
    service._repo = repo
    service._propagate = lambda fn: None
    service._attachment_repo = None
    return service


def _completed_task_with_a_photo() -> Task:
    return Task(
        key=KEY,
        tenant_key=TENANT,
        name="Water the tomatoes",
        status="completed",
        photo_refs=["att-1"],
    )


def test_the_second_reopen_does_not_erase_the_completion(monkeypatch):
    """The finding, driven through the real service methods.

    Asserted on the *marker*, not only on the eventual refusal, so the test says
    which fact went missing rather than only that something downstream changed.
    """
    task = _completed_task_with_a_photo()
    service = _service(task)
    monkeypatch.setattr(service, "get_task", lambda key, *, tenant_key: task)

    service.reopen_task(KEY, tenant_key=TENANT)
    assert task.reopened_from_status == "completed"

    service.skip_task(KEY, tenant_key=TENANT)
    service.reopen_task(KEY, tenant_key=TENANT)

    assert task.reopened_from_status == "completed", (
        "The second reopen overwrote the completion marker with 'skipped', which is "
        "the only thing standing between `delete_task` and the irreversible deletion "
        "of this task's completion photos (#1393)."
    )


def test_the_delete_gate_still_refuses_after_the_detour(monkeypatch):
    """The consequence, asserted end-to-end.

    The marker assertion above could be satisfied by a change that fixes the field
    and leaves the gate reading something else; this pins the behaviour the field
    exists for.
    """
    task = _completed_task_with_a_photo()
    service = _service(task)
    monkeypatch.setattr(service, "get_task", lambda key, *, tenant_key: task)

    service.reopen_task(KEY, tenant_key=TENANT)
    service.skip_task(KEY, tenant_key=TENANT)
    service.reopen_task(KEY, tenant_key=TENANT)

    with pytest.raises(ValidationError, match="completed and reopened"):
        service.delete_task(KEY, tenant_key=TENANT)


def test_a_task_that_was_never_completed_still_reports_its_real_origin(monkeypatch):
    """The control: the marker must not become a constant.

    "Never downgrade" is one character away from "never write", and a marker frozen
    at its first value would make every reopened task look completed — refusing the
    deletion of tasks that carry no record at all, silently and for ever.
    """
    task = Task(key=KEY, tenant_key=TENANT, name="Prune", status="pending")
    service = _service(task)
    monkeypatch.setattr(service, "get_task", lambda key, *, tenant_key: task)

    service.skip_task(KEY, tenant_key=TENANT)
    service.reopen_task(KEY, tenant_key=TENANT)

    assert task.reopened_from_status == "skipped"
    assert service.delete_task(KEY, tenant_key=TENANT) is True
