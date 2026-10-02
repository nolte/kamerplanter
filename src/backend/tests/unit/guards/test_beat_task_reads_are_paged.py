"""#2012 class guard: a beat task must not treat one ``get_all`` page as the whole collection.

``repo.get_all(offset=0, limit=1000, all_tenants=True)`` returns *at most* 1000 rows
plus a ``total``. Nine reads in ``app/tasks`` called it once, iterated the rows and
dropped the ``total``: past the page every row (a plant's dormancy check, a tank's
alert, a care task's reminder) was silently never visited.

**The rule.** In ``app/tasks/``, a ``<anything>.get_all(...)`` call whose ``limit`` is
an integer literal and whose ``offset`` is absent or an integer literal is a single
fixed window, i.e. one page. Such a call is a violation. The sanctioned spelling is
``get_all_pages(repo, ...)`` from ``app.data_access.arango.base_repository`` (it pages
until the offset reaches ``total``); a hand-written paging loop passes because its
``offset`` is a variable. This is a superset of the issue's predicate (it also covers
reads without ``all_tenants=True``, and the positional spelling ``get_all(0, 1000)``).

Spellings this does NOT see
---------------------------

* a limit held in a variable or constant (``limit=PAGE``, ``limit=settings.x``)
  together with a fixed offset: the call is not recognised as a fixed window;
* a ``get_all`` reached through an alias (``fetch = repo.get_all; fetch(...)``) or
  through ``getattr(repo, "get_all")``;
* other list methods with the same defect (``list_by_*``, ``find_*`` with a limit);
* paging code outside ``app/tasks/`` (services called from a beat task; swept once
  by hand in #2012, not guarded).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

TASKS = Path(__file__).resolve().parents[3] / "app" / "tasks"

#: ``(file name, enclosing function)`` -> reason this single-window read is correct.
#: An entry needs a reason that says why the collection cannot outgrow the window.
ALLOWED: dict[tuple[str, str], str] = {}


def _int_literal(node: ast.expr | None) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool)


def fixed_window_reads(source: str) -> list[tuple[str, int]]:
    """``(enclosing function, line)`` of every ``get_all`` call that asks for one fixed window."""
    tree = ast.parse(source)
    found: list[tuple[str, int]] = []

    def visit(node: ast.AST, function: str) -> None:
        for child in ast.iter_child_nodes(node):
            name = child.name if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef) else function
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "get_all"
                and _is_fixed_window(child)
            ):
                found.append((function, child.lineno))
            visit(child, name)

    visit(tree, "<module>")
    return found


def _is_fixed_window(call: ast.Call) -> bool:
    keywords = {kw.arg: kw.value for kw in call.keywords if kw.arg}
    offset = keywords.get("offset", call.args[0] if call.args else None)
    limit = keywords.get("limit", call.args[1] if len(call.args) > 1 else None)
    return _int_literal(limit) and (offset is None or _int_literal(offset))


def violations(directory: Path) -> list[tuple[str, str, int]]:
    out: list[tuple[str, str, int]] = []
    for path in sorted(directory.glob("*.py")):
        for function, line in fixed_window_reads(path.read_text(encoding="utf-8")):
            if (path.name, function) not in ALLOWED:
                out.append((path.name, function, line))
    return out


def test_no_beat_task_reads_a_single_fixed_page() -> None:
    assert violations(TASKS) == [], (
        "a fixed get_all window reads one page and ignores the rest (#2012); use "
        "app.data_access.arango.base_repository.get_all_pages(repo, ...)"
    )


def test_every_allow_list_entry_is_still_a_real_fixed_window_read() -> None:
    live = {
        (path.name, function)
        for path in TASKS.glob("*.py")
        for function, _line in fixed_window_reads(path.read_text(encoding="utf-8"))
    }
    stale = sorted(set(ALLOWED) - live)
    assert stale == [], f"stale allow-list entries (the read was fixed or removed): {stale}"
    assert all(len(reason) > 20 for reason in ALLOWED.values()), "an allow-list entry needs a real reason"


class TestDetector:
    """Each spelling the old tasks used is caught; a paged or helper-routed read is not."""

    @pytest.mark.parametrize(
        "call",
        [
            "repo.get_all(offset=0, limit=1000, all_tenants=True)",
            "repo.get_all(offset=0, limit=500, all_tenants=True)",
            "repo.get_all(0, 1000, all_tenants=True)",
            "repo.get_all(limit=5000, all_tenants=True)",
            "repo.get_all(offset=0, limit=1000)",
            "self.repo.get_all(offset=0, limit=50, tenant_key=tk)",
        ],
    )
    def test_fixed_window_is_flagged(self, call: str) -> None:
        assert fixed_window_reads(f"def task():\n    rows, _ = {call}\n") == [("task", 2)]

    @pytest.mark.parametrize(
        "call",
        [
            "get_all_pages(repo, all_tenants=True)",
            "repo.get_all(offset=offset, limit=100)",
            "repo.get_all(offset=offset, limit=batch_size)",
            "repo.get_all(offset=0, limit=PAGE, all_tenants=True)",  # the documented blind spot
            "repo.get_all_tasks(0, 200, {})",
        ],
    )
    def test_paged_or_unrecognised_read_is_not_flagged(self, call: str) -> None:
        assert fixed_window_reads(f"def task():\n    rows = {call}\n") == []

    def test_allow_list_suppresses_only_its_own_function(self, monkeypatch, tmp_path: Path) -> None:
        (tmp_path / "t.py").write_text(
            "def a():\n    repo.get_all(offset=0, limit=10)\ndef b():\n    repo.get_all(offset=0, limit=10)\n"
        )
        monkeypatch.setitem(ALLOWED, ("t.py", "a"), "a bounded lookup table that cannot exceed ten rows")
        assert violations(tmp_path) == [("t.py", "b", 4)]
