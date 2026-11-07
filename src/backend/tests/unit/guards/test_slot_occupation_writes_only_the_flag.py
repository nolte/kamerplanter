"""#2727 — an occupation write sets ``currently_occupied`` alone; it never writes back a slot it read.

The planting-run and plant-instance services used to read the whole slot, flip ``currently_occupied`` on the
model and hand it to ``update_slot`` (an object merge of every column). A ``PATCH /slots`` that changed the role,
geometry or capacity between that read and that write was reverted, and an old point geometry was merged into a
new polygon. The flag now has its own single-field write, ``ISiteRepository.set_slot_occupied``.

**The class, enumerated over the source** rather than over the callers known on the day of the fix:

* every ``.update_slot(`` call under ``app/`` is listed in :data:`_WHOLE_SLOT_WRITERS` with its reason — a new
  caller fails until it is either moved to ``set_slot_occupied`` or justified here;
* every assignment to ``<x>.currently_occupied`` under ``app/`` is listed in :data:`_FLAG_ASSIGNMENTS` — the
  occupation writers left none behind, and a reintroduced "flip then write the slot" is caught at the flip,
  whatever write follows it.

The runtime half lives in the service doubles (``tests/support/planting_reservation_fakes.py``,
``test_planting_run_location_ownership.py``, ``test_run_and_tank_writes_check_the_tenant.py``,
``test_plant_instance_reference_resolution.py``): their ``update_slot`` raises, so an occupation path that wrote
the whole slot again fails the behaviour tests, not only this scan. The interleaving itself is measured against
ArangoDB in ``tests/integration/test_garden_resource_repository.py::TestOccupationWritesOnlyTheFlag``.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"

#: ``module::Class.method`` → why it may rewrite the whole slot.
_WHOLE_SLOT_WRITERS: dict[str, str] = {
    "app/domain/services/site_service.py::SiteService.update_slot": (
        "PUT /slots: writes the body's columns only, the rest (the flag included) untouched (#2639)"
    ),
}

#: ``module::Class.method`` → why it sets the flag on a model.
_FLAG_ASSIGNMENTS: dict[str, str] = {
    "app/domain/services/site_service.py::SiteService.update_slot": (
        "copies the stored flag onto the rebuilt model so it validates as stored; the column is untouched"
    ),
    "app/domain/services/planting_run_service.py::PlantingRunService._quick_layout": (
        "new slots, inserted occupied by the quick-plant transaction; no stored row to revert"
    ),
}


def _qualified_functions(tree: ast.Module) -> list[tuple[str, ast.AST]]:
    found: list[tuple[str, ast.AST]] = []

    def visit(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, f"{prefix}{child.name}.")
            elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                found.append((f"{prefix}{child.name}", child))
                visit(child, f"{prefix}{child.name}.")

    visit(tree, "")
    return found


def _scan(module: str, source: str) -> tuple[set[str], set[str]]:
    """``(update_slot callers, currently_occupied assigners)`` of one module, as ``module::qualname``."""
    callers: set[str] = set()
    assigners: set[str] = set()
    tree = ast.parse(source)
    owner: dict[int, str] = {}
    for name, fn in _qualified_functions(tree):
        for node in ast.walk(fn):
            owner[id(node)] = name  # inner functions are visited later and overwrite: innermost wins
    for node in ast.walk(tree):
        where = f"{module}::{owner.get(id(node), '<module>')}"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "update_slot":
            callers.add(where)
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AugAssign | ast.AnnAssign):
            targets = [node.target]
        if any(isinstance(t, ast.Attribute) and t.attr == "currently_occupied" for t in targets):
            assigners.add(where)
    return callers, assigners


def _sites() -> tuple[set[str], set[str]]:
    """:func:`_scan` over ``app/`` — the repository implementations and interfaces are not callers."""
    callers: set[str] = set()
    assigners: set[str] = set()
    for path in sorted(_APP.rglob("*.py")):
        module = path.relative_to(_APP.parent).as_posix()
        if module.startswith(("app/data_access/", "app/domain/interfaces/")):
            continue
        found_calls, found_flips = _scan(module, path.read_text(encoding="utf-8"))
        callers |= found_calls
        assigners |= found_flips
    return callers, assigners


def test_every_whole_slot_write_is_justified() -> None:
    callers, _ = _sites()
    # The router calls the service's update_slot (not a repository write); it is the API surface of PUT itself.
    callers.discard("app/api/v1/slots/tenant_router.py::update_slot")
    assert callers == set(_WHOLE_SLOT_WRITERS), (
        "a new update_slot caller writes the whole slot back; an occupation write uses set_slot_occupied (#2727)"
    )


def test_no_occupation_writer_flips_the_flag_on_a_slot_it_read() -> None:
    _, assigners = _sites()
    assert assigners == set(_FLAG_ASSIGNMENTS), (
        "currently_occupied is set on a model again; write it through ISiteRepository.set_slot_occupied (#2727)"
    )


def test_the_scan_sees_the_spelling_it_forbids() -> None:
    """Positive control: the old occupation write, through the same scan, is found at both of its halves."""
    source = (
        "class PlantingRunService:\n"
        "    def create_plants(self, slot_key):\n"
        "        slot = self._site_repo.get_slot_by_key(slot_key)\n"
        "        slot.currently_occupied = True\n"
        "        self._site_repo.update_slot(slot_key, slot)\n"
    )
    where = "app/domain/services/x.py::PlantingRunService.create_plants"

    assert _scan("app/domain/services/x.py", source) == ({where}, {where})


def test_the_listed_reasons_name_live_sites() -> None:
    """A stale entry fails too: the lists may only describe what the source holds."""
    callers, assigners = _sites()
    assert set(_WHOLE_SLOT_WRITERS) <= callers | {"app/api/v1/slots/tenant_router.py::update_slot"}
    assert set(_FLAG_ASSIGNMENTS) <= assigners
