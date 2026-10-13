"""MT-035 (#2131) — nobody pays for a ``total`` and throws it away.

The defect class: a call site that unpacks ``rows, _ = service.list_x(...)``.
The method answers ``(rows, total)`` and ``total`` costs a second scan of every
row the filter matches — on every page, for a number the caller never reads (the
list routes answer a bare JSON array, no envelope). The window is bounded; the
count is not, it grows with the collection.

Two predicates, both on the AST:

**Routes** — in every module under ``app/api``, every function decorated with
``<router>.get/post/put/patch/delete(...)`` that contains an assignment
``<name>, <_name> = <call>(...)``: a two-element tuple target whose second name
starts with ``_`` and whose value is a call. No route may contain one: the 28
hits measured when this guard was written were all converted (#2242: 13, the
fourth slice: 15). The fix is the count-free ``*_window`` sibling
(``BaseArangoRepository.list_window`` / ``get_page_window`` or a repository
method of the same shape).

**Everywhere else** — the same spelling anywhere in ``app``, narrowed to calls of a
*counted method*: a method whose return annotation is ``tuple[list[...], int]``,
derived from the source tree (:func:`_counted_method_names`), not listed by hand.
Every hit must be classified in :data:`_DISCARDING` with the reason the count is
tolerable there or who owns the conversion.

**What it cannot see**: a total discarded under another spelling (``rows =
service.list_x(...)[0]``, ``result[0]``, an unused named ``total``) — the
spellings in ``app/api`` were measured when this guard was written and are
asserted absent by :func:`test_no_route_discards_the_total_by_indexing`; a
counted method whose return is not annotated ``tuple[list[...], int]``; a call
whose name collides with a counted method of another class (the guard errs to a
false hit, which classification resolves); and a count paid inside a service
method that never surfaces it.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path

_APP = Path(__file__).resolve().parents[3] / "app"
_API = _APP / "api"
_ROUTE_DECORATORS = frozenset({"get", "post", "put", "patch", "delete"})

#: ``(module relative to app, enclosing function)`` → reason. Outside the routes only.
_DISCARDING: dict[tuple[str, str], str] = {
    ("domain/services/task_service.py", "get_task_queue"): (
        "the tenant-wide queue read is capped at QUEUE_LIMIT and de-duplicated in Python; the queue's "
        "window and its index belong to #1534"
    ),
}

#: Pinned: a conversion lowers it; a new discarding call site cannot join silently.
_DISCARDING_COUNT = 1


def _is_route(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in _ROUTE_DECORATORS
        for d in fn.decorator_list
    )


def _route_handlers(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_route(n)]


def _discards_a_total(node: ast.AST) -> bool:
    if not (isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple)):
        return False
    elts = node.targets[0].elts
    return (
        len(elts) == 2
        and isinstance(elts[1], ast.Name)
        and elts[1].id.startswith("_")
        and isinstance(node.value, ast.Call)
    )


def _indexes_a_list_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr.startswith(("list_", "get_all", "get_page"))
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == 0
    )


def _hits(source: str, predicate: Callable[[ast.AST], bool]) -> set[str]:
    tree = ast.parse(source)
    return {fn.name for fn in _route_handlers(tree) for node in ast.walk(fn) if predicate(node)}


def _scan(predicate: Callable[[ast.AST], bool]) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for path in sorted(_API.rglob("*.py")):
        rel = path.relative_to(_API).as_posix()
        found |= {(rel, name) for name in _hits(path.read_text(encoding="utf-8"), predicate)}
    return found


def _route_count() -> int:
    return sum(len(_route_handlers(ast.parse(p.read_text(encoding="utf-8")))) for p in _API.rglob("*.py"))


def _returns_a_counted_page(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    returns = fn.returns
    return (
        isinstance(returns, ast.Subscript)
        and isinstance(returns.value, ast.Name)
        and returns.value.id == "tuple"
        and isinstance(returns.slice, ast.Tuple)
        and len(returns.slice.elts) == 2
        and isinstance(returns.slice.elts[0], ast.Subscript)
        and isinstance(returns.slice.elts[0].value, ast.Name)
        and returns.slice.elts[0].value.id == "list"
        and isinstance(returns.slice.elts[1], ast.Name)
        and returns.slice.elts[1].id == "int"
    )


def _counted_names_in(source: str) -> set[str]:
    return {
        n.name
        for n in ast.walk(ast.parse(source))
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and _returns_a_counted_page(n)
    }


def _counted_method_names() -> frozenset[str]:
    names: set[str] = set()
    for path in _APP.rglob("*.py"):
        names |= _counted_names_in(path.read_text(encoding="utf-8"))
    return frozenset(names)


def _callee(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    if isinstance(call.func, ast.Name):
        return call.func.id
    return None


def _discarding_calls_in(source: str, counted: frozenset[str]) -> set[str]:
    """Enclosing functions of ``rows, _ = <counted>(...)`` in ``source``."""
    found: set[str] = set()
    for fn in ast.walk(ast.parse(source)):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(fn):
            if (
                _discards_a_total(node)
                and isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Call)
                and _callee(node.value) in counted
            ):
                found.add(fn.name)
    return found


def _scan_app(counted: frozenset[str]) -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for path in sorted(_APP.rglob("*.py")):
        rel = path.relative_to(_APP).as_posix()
        found |= {(rel, name) for name in _discarding_calls_in(path.read_text(encoding="utf-8"), counted)}
    return found


# ── the guard on the source tree ────────────────────────────────────────────


def test_no_route_discards_a_total() -> None:
    # Non-vacuity: the scan reaches the routers (the predicate itself is pinned by
    # the self-test on synthetic source below).
    assert _route_count() >= 300
    found = sorted(_scan(_discards_a_total))
    assert found == [], (
        "list route unpacks (rows, _total) and pays a count query for nothing: call the count-free "
        f"*_window sibling (MT-035, #2131): {found}"
    )


def test_the_counted_methods_are_derived_from_the_tree() -> None:
    counted = _counted_method_names()
    # Non-vacuity: the derivation finds the counted repository and service methods.
    assert len(counted) >= 40, sorted(counted)
    assert {"get_all", "get_page", "list_plants", "get_inspections_for_plant", "get_pending_tasks"} <= counted


def test_every_call_site_that_discards_a_counted_total_is_classified() -> None:
    found = _scan_app(_counted_method_names())
    unclassified = sorted(found - set(_DISCARDING))
    assert unclassified == [], (
        "call site unpacks (rows, _total) from a counted method and pays a count query for nothing: "
        f"call the count-free *_window sibling, or classify it in _DISCARDING (MT-035, #2131): {unclassified}"
    )


def test_every_classification_still_names_a_discarding_call_site() -> None:
    stale = sorted(set(_DISCARDING) - _scan_app(_counted_method_names()))
    assert stale == [], f"classified call site no longer discards a total — drop the entry: {stale}"


def test_the_discarding_call_sites_are_pinned_and_explained() -> None:
    assert len(_DISCARDING) == _DISCARDING_COUNT
    assert all(len(reason) >= 15 for reason in _DISCARDING.values())


def test_no_route_discards_the_total_by_indexing() -> None:
    assert _scan(_indexes_a_list_call) == set()


# ── the predicate on synthetic source (self-test) ───────────────────────────

_PROBE = """
@router.get("/a")
def discards(service):
    rows, _ = service.list_rows(0, 50)
    return rows

@router.get("/b")
def discards_named(service):
    rows, _total = service.list_rows(0, 50)
    return rows

@router.get("/c")
def windowed(service):
    return service.list_rows_window(0, 50)

@router.get("/d")
def uses_total(service):
    rows, total = service.list_rows(0, 50)
    return {"rows": rows, "total": total}

@router.get("/e")
def indexes(service):
    return service.list_rows(0, 50)[0]

def helper(service):
    rows, _ = service.list_rows(0, 50)
    return rows
"""


def test_the_predicate_flags_both_spellings_of_a_discarded_total() -> None:
    assert _hits(_PROBE, _discards_a_total) == {"discards", "discards_named"}


def test_the_indexing_predicate_flags_only_the_indexed_call() -> None:
    assert _hits(_PROBE, _indexes_a_list_call) == {"indexes"}


_COUNTED_PROBE = """
class Repo:
    def list_rows(self, offset: int, limit: int) -> tuple[list[Row], int]:
        ...

    def list_rows_window(self, offset: int, limit: int) -> list[Row]:
        ...

    def pair(self) -> tuple[str, int]:
        ...


def service_discards(repo):
    rows, _ = repo.list_rows(0, 50)
    return rows


def service_windowed(repo):
    return repo.list_rows_window(0, 50)


def service_uses_total(repo):
    rows, total = repo.list_rows(0, 50)
    return rows, total


def not_a_page(repo):
    name, _ = repo.pair()
    return name
"""


def test_the_counted_method_derivation_reads_the_return_annotation() -> None:
    assert _counted_names_in(_COUNTED_PROBE) == {"list_rows"}


def test_the_app_predicate_flags_only_a_discarded_counted_total() -> None:
    counted = frozenset(_counted_names_in(_COUNTED_PROBE))
    assert _discarding_calls_in(_COUNTED_PROBE, counted) == {"service_discards"}
