"""#2108 — every dispatch of the thumbnail task goes through the per-window claim.

The defect class: a code path that finds a rendition missing and queues
``generate_thumbnails`` straight away. #2108 measured it on
``GET /attachments/{id}/thumbnails/{size}`` — five GETs, five queued decodes —
and the same spelling sat in two siblings nobody had named: the promoted
pest-image thumbnail route and the MCP diary photo tool.

The class is **every reference to a dispatch method of the task** —
``generate_thumbnails.delay``, ``.apply_async``, ``.s``, ``.si``,
``.signature`` — and every ``send_task`` naming it, in every module under
``app/``. They must sit inside
:func:`app.tasks.storage_tasks.request_thumbnails`, which claims the window
(``IRenditionDispatchClaims``) and refuses renditions that failed for good.

**What this predicate cannot see**: the task object reached under another name
(``task = generate_thumbnails; task.delay(...)``) or through ``getattr``, and a
dispatch from outside ``app/``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[3] / "app"
_GATE_MODULE = APP / "tasks" / "storage_tasks.py"
_GATE_FUNCTION = "request_thumbnails"
_TASK = "generate_thumbnails"
_DISPATCH_METHODS = frozenset({"delay", "apply_async", "s", "si", "signature"})

#: Pinned so a predicate that silently stops reaching the dispatch fails: the
#: modules that request renditions through the gate.
_EXPECTED_GATE_USERS = frozenset(
    {
        "app/domain/services/attachment_service.py",
        "app/api/v1/ipm/pest_images_router.py",
        "app/mcp_server/tools/diary.py",
    }
)


def _dispatches_in_source(source: str) -> list[tuple[int, str | None]]:
    """``(line, enclosing function)`` of every dispatch of the thumbnail task in *source*."""
    tree = ast.parse(source)
    found: list[tuple[int, str | None]] = []

    def visit(node: ast.AST, function: str | None) -> None:
        for child in ast.iter_child_nodes(node):
            enclosing = child.name if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) else function
            if (
                isinstance(child, ast.Attribute)
                and child.attr in _DISPATCH_METHODS
                and (
                    (isinstance(child.value, ast.Name) and child.value.id == _TASK)
                    or (isinstance(child.value, ast.Attribute) and child.value.attr == _TASK)
                )
            ) or (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "send_task"
                and any(
                    isinstance(arg, ast.Constant) and isinstance(arg.value, str) and _TASK in arg.value
                    for arg in child.args
                )
            ):
                found.append((child.lineno, function))
            visit(child, enclosing)

    visit(tree, None)
    return found


def _app_modules() -> list[Path]:
    return sorted(path for path in APP.rglob("*.py") if "__pycache__" not in path.parts)


def test_every_thumbnail_dispatch_is_inside_the_claiming_gate() -> None:
    offenders: list[str] = []
    gate_dispatches = 0
    for path in _app_modules():
        for line, function in _dispatches_in_source(path.read_text(encoding="utf-8")):
            if path == _GATE_MODULE and function == _GATE_FUNCTION:
                gate_dispatches += 1
                continue
            offenders.append(f"{path.relative_to(APP.parent).as_posix()}:{line} (in {function})")
    assert not offenders, (
        "dispatch generate_thumbnails through app.tasks.storage_tasks.request_thumbnails (#2108):\n"
        + "\n".join(offenders)
    )
    assert gate_dispatches == 1, "the gate itself must be where the task is queued"


def _calls_the_gate(source: str) -> bool:
    """Whether *source* calls ``request_thumbnails`` — by name or as a method (parsed, not text-matched)."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name == _GATE_FUNCTION:
                return True
    return False


def test_the_requesting_modules_go_through_the_gate() -> None:
    users = {
        path.relative_to(APP.parent).as_posix()
        for path in _app_modules()
        if path != _GATE_MODULE and _calls_the_gate(path.read_text(encoding="utf-8"))
    }
    assert users >= _EXPECTED_GATE_USERS, sorted(_EXPECTED_GATE_USERS - users)


@pytest.mark.parametrize(
    "source",
    [
        "def f():\n    generate_thumbnails.delay(a, t)\n",
        "def f():\n    storage_tasks.generate_thumbnails.apply_async((a, t))\n",
        "sig = generate_thumbnails.s(a, t)\n",
        "def f():\n    celery_app.send_task('app.tasks.storage_tasks.generate_thumbnails', args=[a])\n",
        "async def f():\n    d = generate_thumbnails.delay\n    d(a, t)\n",
    ],
)
def test_the_scan_flags_every_dispatch_spelling(source: str) -> None:
    """Self-test through the same detector the tree scan uses."""
    assert _dispatches_in_source(source), source


def test_the_scan_names_the_enclosing_function() -> None:
    source = "def request_thumbnails(a):\n    generate_thumbnails.delay(a)\n"
    assert _dispatches_in_source(source) == [(2, "request_thumbnails")]


def test_the_scan_leaves_other_tasks_alone() -> None:
    assert not _dispatches_in_source("def f():\n    migrate_storage.delay(a)\n    send_task('other')\n")
