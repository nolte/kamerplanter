"""#2727 — an occupation write sets ``currently_occupied`` alone; it never writes back a slot it read.

The planting-run and plant-instance services used to read the whole slot, flip ``currently_occupied`` on the
model and hand it to ``update_slot`` (an object merge of every column). A ``PATCH /slots`` that changed the role,
geometry or capacity between that read and that write was reverted, and an old point geometry was merged into a
new polygon. The flag now has its own single-field write, ``ISiteRepository.set_slot_occupied``.

**The class, enumerated over the source** rather than over the callers known on the day of the fix:

* every call of a whole-slot write under ``app/`` is listed in :data:`_WHOLE_SLOT_WRITERS` with its reason — a
  new caller fails until it is either moved to ``set_slot_occupied`` or justified here. The write methods are
  derived from ``ISiteRepository`` (every method taking a ``Slot``, the insert excepted), plus the private slot
  view's ``update_leaving`` and any reach into ``._slots`` — so a ``replace_slot(key, slot)`` added later is
  covered without editing this file;
* every way of setting the flag on a model under ``app/`` is listed in :data:`_FLAG_ASSIGNMENTS`:
  ``x.currently_occupied = …``, ``setattr(x, "currently_occupied", …)`` and ``x.model_copy(update={…
  "currently_occupied": …})``. The occupation writers left none behind, and a reintroduced "flip then write the
  slot" is caught at the flip, whatever write follows it.

The runtime half lives in the service doubles (``tests/support/planting_reservation_fakes.py``,
``test_planting_run_location_ownership.py``, ``test_run_and_tank_writes_check_the_tenant.py``,
``test_plant_instance_reference_resolution.py``): their ``update_slot`` raises, so an occupation path that wrote
the whole slot again fails the behaviour tests, not only this scan. The interleaving itself is measured against
ArangoDB in ``tests/integration/test_garden_resource_repository.py::TestOccupationWritesOnlyTheFlag``.
"""

from __future__ import annotations

import ast
import inspect
from functools import cache
from pathlib import Path

from app.domain.interfaces.site_repository import ISiteRepository
from app.domain.models.site import Slot
from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"

#: Site-repository methods that take a ``Slot`` but insert a new row: nothing stored to revert.
_INSERTS = frozenset({"create_slot"})
#: Whole-slot writes not on the interface: the private slot view of ``ArangoSiteRepository``.
_PRIVATE_WRITES = frozenset({"update_leaving"})


@cache
def _whole_slot_write_methods() -> frozenset[str]:
    """Every ``ISiteRepository`` method with a ``Slot`` parameter except the inserts, plus the private ones."""
    names = {
        name
        for name, fn in inspect.getmembers(ISiteRepository, inspect.isfunction)
        if any(p.annotation in (Slot, "Slot") for p in inspect.signature(fn).parameters.values())
    }
    assert "update_slot" in names, "the derivation lost the write it exists for"
    return frozenset(names - _INSERTS) | _PRIVATE_WRITES


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
    writes = _whole_slot_write_methods()
    for node in ast.walk(tree):
        where = f"{module}::{owner.get(id(node), '<module>')}"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in writes:
            callers.add(where)
        if isinstance(node, ast.Attribute) and node.attr == "_slots" and not _is_self(node.value):
            callers.add(where)  # a reach into another object's private slot view, whatever it calls there
        if _sets_the_flag(node):
            assigners.add(where)
    return callers, assigners


def _is_self(node: ast.expr) -> bool:
    """``self._slots`` is an object's own attribute (a memo dict in ``phase_transitions``), not a reach-in."""
    return isinstance(node, ast.Name) and node.id == "self"


def _is_flag(node: ast.expr | None) -> bool:
    return isinstance(node, ast.Constant) and node.value == "currently_occupied"


def _sets_the_flag(node: ast.AST) -> bool:
    """``x.currently_occupied = …`` (plain, augmented, annotated), ``setattr(x, "currently_occupied", …)`` or
    ``x.model_copy(update={… "currently_occupied": …})``."""
    if isinstance(node, ast.Assign | ast.AugAssign | ast.AnnAssign):
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        return any(isinstance(t, ast.Attribute) and t.attr == "currently_occupied" for t in targets)
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name) and node.func.id == "setattr":
        return len(node.args) >= 2 and _is_flag(node.args[1])
    if isinstance(node.func, ast.Attribute) and node.func.attr == "model_copy":
        updates = [kw.value for kw in node.keywords if kw.arg == "update"] + list(node.args)
        return any(isinstance(u, ast.Dict) and any(_is_flag(k) for k in u.keys) for u in updates)
    return False


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


_CONTROL_MODULE = "app/domain/services/x.py"
_CONTROL_WHERE = f"{_CONTROL_MODULE}::PlantingRunService.occupy"


def _control(body: str) -> tuple[set[str], set[str]]:
    """``body`` as the method ``PlantingRunService.occupy``, through the same :func:`_scan`."""
    lines = "".join(f"        {line}\n" for line in body.strip().splitlines())
    return _scan(_CONTROL_MODULE, f"class PlantingRunService:\n    def occupy(self, slot_key, slot):\n{lines}")


def test_the_scan_sees_the_spelling_it_forbids() -> None:
    """Positive control: the old occupation write, through the same scan, is found at both of its halves."""
    found = _control("slot.currently_occupied = True\nself._site_repo.update_slot(slot_key, slot)")

    assert found == ({_CONTROL_WHERE}, {_CONTROL_WHERE})


def test_the_scan_sees_every_way_of_setting_the_flag() -> None:
    for body in (
        "slot.currently_occupied |= True",
        "slot.currently_occupied: bool = True",
        'setattr(slot, "currently_occupied", True)',
        'slot = slot.model_copy(update={"slot_id": "A", "currently_occupied": True})',
        'slot = slot.model_copy(deep=True, update={"currently_occupied": True})',
    ):
        assert _control(body) == (set(), {_CONTROL_WHERE}), body
    # Negative controls: another column, another attribute, a read of the flag.
    for body in (
        'slot = slot.model_copy(update={"slot_id": "A"})',
        'setattr(slot, "slot_id", "A")',
        "busy = slot.currently_occupied",
    ):
        assert _control(body) == (set(), set()), body


def test_the_scan_sees_every_whole_slot_write() -> None:
    for body in (
        "self._site_repo.update_slot(slot_key, slot)",
        "self._site_repo._slots.update_leaving(slot_key, slot, untouched=())",
        "self._site_repo._slots.update(slot_key, slot)",
    ):
        assert _control(body)[0] == {_CONTROL_WHERE}, body
    assert _control("self._site_repo.set_slot_occupied(slot_key, True)") == (set(), set())
    assert _control("self._site_repo.create_slot(slot)") == (set(), set())  # an insert, nothing to revert
    assert _control("self._slots = {}\nreturn self._slots.get(slot_key)") == (set(), set())  # own attribute


def test_a_new_slot_taking_write_on_the_interface_is_covered() -> None:
    """The write set is derived: today ``update_slot``; an added ``replace_slot(key, slot: Slot)`` joins it."""
    assert _whole_slot_write_methods() == {"update_slot", "update_leaving"}


def test_the_listed_reasons_name_live_sites() -> None:
    """A stale entry fails too: the lists may only describe what the source holds."""
    callers, assigners = _sites()
    assert set(_WHOLE_SLOT_WRITERS) <= callers | {"app/api/v1/slots/tenant_router.py::update_slot"}
    assert set(_FLAG_ASSIGNMENTS) <= assigners
