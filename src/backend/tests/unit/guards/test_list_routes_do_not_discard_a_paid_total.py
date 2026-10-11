"""MT-035 (#2131) — a list route does not pay for a ``total`` it throws away.

The defect class: a route handler that unpacks ``rows, _ = service.list_x(...)``.
The service answers ``(rows, total)`` and ``total`` costs a second scan of every
row the filter matches — on every page, for a number the route never sends (the
list routes answer a bare JSON array, no envelope). The window is bounded; the
count is not, it grows with the collection.

**Predicate** — in every module under ``app/api``, every function decorated with
``<router>.get/post/put/patch/delete(...)`` that contains an assignment
``<name>, <_name> = <call>(...)``: a two-element tuple target whose second name
starts with ``_`` and whose value is a call. Every hit must be listed in
:data:`_DISCARDING` with the reason the count is tolerable there. The fix for a
hit is the count-free ``*_window`` sibling (``BaseArangoRepository.list_window`` /
``get_page_window`` or a repository method of the same shape).

**Kinds**: ``catalogue`` (seeded/curated reference data, grows with the seed,
not with a tenant's activity) and ``tenant-config`` (rows a person creates one
by one). A tenant-growing collection is not a kind — convert it.

**What it cannot see**: a total discarded under another spelling (``rows =
service.list_x(...)[0]``, ``result[0]``, an unused named ``total``) — the
spellings in ``app/api`` were measured when this guard was written and are
asserted absent by :func:`test_no_route_discards_the_total_by_indexing`; and a
count paid inside a service method that never surfaces it.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path

_API = Path(__file__).resolve().parents[3] / "app" / "api"
_ROUTE_DECORATORS = frozenset({"get", "post", "put", "patch", "delete"})

#: ``(module relative to app/api, handler)`` → ``(kind, reason)``.
_DISCARDING: dict[tuple[str, str], tuple[str, str]] = {
    ("v1/activities/router.py", "list_activities"): (
        "catalogue",
        "the activity catalogue: global seed rows plus the tenant's own (#2119)",
    ),
    ("v1/fertilizers/tenant_router.py", "list_fertilizers"): (
        "tenant-config",
        "the tenant's fertilizer products, created one by one",
    ),
    ("v1/harvest/tenant_router.py", "list_indicators"): ("catalogue", "the seeded harvest-indicator catalogue"),
    ("v1/ipm/router.py", "list_pests"): ("catalogue", "the seeded pest catalogue"),
    ("v1/ipm/router.py", "list_diseases"): ("catalogue", "the seeded disease catalogue"),
    ("v1/ipm/router.py", "list_treatments"): ("catalogue", "the seeded treatment catalogue"),
    ("v1/nutrient_plans/tenant_router.py", "list_plans"): (
        "tenant-config",
        "the tenant's nutrient plans plus shared templates, authored one by one",
    ),
    ("v1/overwintering_profiles/tenant_router.py", "list_overwintering_profiles"): (
        "tenant-config",
        "the tenant's overwintering profiles, one per plant group",
    ),
    ("v1/phase_sequences/router.py", "list_phase_definitions"): (
        "catalogue",
        "the phase-definition catalogue",
    ),
    ("v1/phase_sequences/router.py", "list_phase_sequences"): ("catalogue", "the phase-sequence catalogue"),
    ("v1/propagation/tenant_router.py", "list_protocols"): (
        "tenant-config",
        "rooting protocols: global templates plus the tenant's own",
    ),
    ("v1/sites/tenant_router.py", "list_sites"): ("tenant-config", "the tenant's sites, registered one by one"),
    ("v1/succession_plans/tenant_router.py", "list_succession_plans"): (
        "tenant-config",
        "the tenant's succession plans, authored one by one",
    ),
    ("v1/tanks/tenant_router.py", "list_tanks"): ("tenant-config", "the tenant's tanks, registered one by one"),
    ("v1/tasks/tenant_router.py", "list_workflows"): (
        "tenant-config",
        "workflow templates: system templates plus the tenant's own",
    ),
}

#: Pinned: a conversion lowers it; a new discarding route cannot join silently.
_DISCARDING_COUNT = 15
_KINDS = frozenset({"catalogue", "tenant-config"})


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


# ── the guard on the source tree ────────────────────────────────────────────


def test_every_route_that_discards_a_total_is_classified() -> None:
    found = _scan(_discards_a_total)
    # Non-vacuity: the scan reaches the routers and recognises the spelling.
    assert len(found) >= 10, found
    unclassified = sorted(found - set(_DISCARDING))
    assert unclassified == [], (
        "list route unpacks (rows, _total) and pays a count query for nothing: call the count-free "
        f"*_window sibling, or classify it in _DISCARDING (MT-035, #2131): {unclassified}"
    )


def test_every_classification_still_names_a_discarding_route() -> None:
    stale = sorted(set(_DISCARDING) - _scan(_discards_a_total))
    assert stale == [], f"classified route no longer discards a total — drop the entry: {stale}"


def test_the_discarding_routes_are_pinned_and_explained() -> None:
    assert len(_DISCARDING) == _DISCARDING_COUNT
    assert {kind for kind, _ in _DISCARDING.values()} <= _KINDS
    assert all(len(reason) >= 15 for _, reason in _DISCARDING.values())


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
