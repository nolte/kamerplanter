"""#1393 — a task that may be deleted never carries ``photo_refs``.

This is the invariant the eager photo deletion was built for and the reason it was
removed. Both halves matter, so both are asserted here rather than argued in a
commit message nobody re-reads.

The reachability argument, measured against the service rather than reasoned about:

* ``task.photo_refs`` is written in exactly one place — ``complete_task`` — which
  sets ``status = "completed"`` in the same call. Nothing anywhere removes an entry.
* ``delete_task`` admits ``pending``, ``skipped`` and ``dormant``.
* ``dormant`` is only ever an *initial* status (``activity_plan_service``,
  ``_materialise``); no transition leads into it.
* The only way out of ``completed`` is ``reopen_task``, which stamps
  ``reopened_from_status = "completed"`` and — since #1393 round 6 — never downgrades
  it. ``delete_task`` refuses on that marker.
* ``batch_status_change`` and ``batch_delete`` delegate to these same methods, so
  they add no path.

Therefore ``_dispatch_photo_deletion`` could never have had photos to delete, and
"deleting a task also deletes its photos" was a decision taken on a premise that does
not hold. Shipping it would have meant carrying a background call that destroys
attachments on a path that cannot execute — and it nearly did execute, through the
reopen hole that round 6 found.

What this file protects is the invariant, not the deleted code. If someone later
relaxes ``delete_task``'s gate, these tests fail and say what the relaxation costs:
deleting the task now strands its completion photos, and the orphan sweep that would
collect them ships disabled.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ValidationError
from app.domain.models.task import Task
from app.domain.services import task_service as task_service_module
from app.domain.services.task_service import TaskService

TENANT = "tenant-a"
KEY = "task-1"

#: Statuses ``delete_task`` admits, read off the service so the two cannot drift.
_DELETABLE = {"pending", "skipped", "dormant"}


def _service(task: Task) -> TaskService:
    service = TaskService.__new__(TaskService)
    repo = MagicMock()
    repo.update_task.side_effect = lambda key, updated: updated
    repo.delete_task.return_value = True
    service._repo = repo
    service._propagate = lambda fn: None
    service._attachment_repo = None
    return service


def _with(task: Task) -> TaskService:
    service = _service(task)
    service.get_task = lambda key, *, tenant_key: task  # type: ignore[method-assign]
    return service


def _completed_with_photo() -> Task:
    return Task(key=KEY, tenant_key=TENANT, name="Water", status="completed", photo_refs=["att-1"])


def test_the_deletable_statuses_are_what_this_file_assumes():
    """The control. If ``delete_task`` gains a status, the reasoning above is stale.

    Read out of the source rather than duplicated as a literal, so widening the gate
    fails here instead of leaving the rest of the file quietly checking the wrong set.
    """
    source = Path(task_service_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    found: set[str] | None = None
    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef) and node.name == "delete_task"):
            continue
        for statement in ast.walk(node):
            if (
                isinstance(statement, ast.Assign)
                and any(getattr(t, "id", None) == "allowed" for t in statement.targets)
                and isinstance(statement.value, ast.Set)
            ):
                found = {element.value for element in statement.value.elts if isinstance(element, ast.Constant)}
    assert found == _DELETABLE, (
        f"delete_task now admits {found}, not {_DELETABLE}. Re-derive whether a task in "
        f"the new status can carry photo_refs before changing this constant (#1393)."
    )


@pytest.mark.parametrize(
    "detour",
    [
        pytest.param(["reopen"], id="completed-then-reopened"),
        pytest.param(["reopen", "skip"], id="completed-reopened-skipped"),
        pytest.param(["reopen", "skip", "reopen"], id="completed-reopened-skipped-reopened"),
        pytest.param(["reopen", "skip", "reopen", "skip", "reopen"], id="and-round-again"),
    ],
)
def test_no_route_out_of_completed_makes_the_photos_deletable(detour: list[str]):
    """Every way back into a deletable status still refuses the deletion.

    Parametrised over the sequence length because the hole round 6 found needed
    *four* steps: the three-step version was refused and the four-step version was
    not, so a single-detour test would have reported the gate healthy.
    """
    task = _completed_with_photo()
    service = _with(task)
    for step in detour:
        {"reopen": service.reopen_task, "skip": service.skip_task}[step](KEY, tenant_key=TENANT)

    assert task.photo_refs == ["att-1"], "the detour must not be what removes the photos"
    # Not guarded by ``if task.status in _DELETABLE``. Every detour here ends on
    # ``reopen`` or ``skip``, both of which land in a deletable status — so the guard
    # asserted nothing it did not already know, and would have turned this whole
    # parametrisation vacuous the moment a detour stopped reaching one.
    assert task.status in _DELETABLE, (
        f"detour ended in {task.status!r}, which delete_task would refuse for an "
        f"unrelated reason — this case then proves nothing about the photo gate"
    )
    with pytest.raises(ValidationError, match="completed and reopened"):
        service.delete_task(KEY, tenant_key=TENANT)


def test_a_task_with_no_completion_is_deletable_and_has_nothing_to_clean_up():
    """The other half: deletion still works, and finds no photos to destroy.

    Without this the invariant could be satisfied by refusing every deletion, which
    would be a different bug wearing the same green.
    """
    task = Task(key=KEY, tenant_key=TENANT, name="Prune", status="pending")
    service = _with(task)

    assert task.photo_refs == []
    assert service.delete_task(KEY, tenant_key=TENANT) is True


def test_completion_is_the_only_writer_of_photo_refs():
    """The premise the whole argument rests on, checked against the source.

    Asserted structurally because it is the fact most likely to change without anyone
    connecting it to task deletion: a new endpoint that attaches a photo to a
    *pending* task would make deletable tasks carry photos again, and the eager
    cleanup this file documents as unnecessary would become necessary once more.
    """
    source = Path(task_service_module.__file__).read_text(encoding="utf-8")
    writers = {
        node.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.FunctionDef)
        for inner in ast.walk(node)
        if isinstance(inner, ast.Attribute)
        and inner.attr == "photo_refs"
        and isinstance(inner.ctx, ast.Load)
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr in {"append", "extend"}
            and getattr(call.func.value, "attr", None) == "photo_refs"
            for call in ast.walk(node)
        )
    }
    assert writers == {"complete_task"}, (
        f"task.photo_refs is now mutated by {sorted(writers)}, not only complete_task. "
        f"A task can carry photos without having been completed, so re-derive whether "
        f"delete_task needs to clean them up (#1393)."
    )
