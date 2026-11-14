"""#2773 — every check of the bed-level slot rules V-04/V-06 is fenced against a concurrent slot or frame write.

V-04 (inside the bed) and V-06 (zones do not overlap) are checked against the bed's frame and its other slots, read
before the write's transaction opens. Two ``PATCH /slots`` redrawing two zones into one area both passed that way:
each saw the other's old polygon. The fix is a counter on the bed, ``slot_rules_revision``, read in one snapshot
with the frame and the slots (``IGardenPlanRepository.load_slot_rule_basis``) and compared and raised by the write's
transaction (``slot_rules_fence.take_slot_rules``); the loser answers 409.

**The class, enumerated over the source** rather than over the five check sites known on the day of the fix:

* every service method that reaches a V-04/V-06 predicate (``slots_outside_bed``, ``overlapping_zones``) - directly
  or through a method of its own class - and reads stored slots does so through ``load_slot_rule_basis``, never
  ``load_active_slots`` (which carries no fence). A new check site that reads its siblings unfenced fails here;
* every production construction of a write that carries slots into a bed (``SlotBatchWrite``, ``RunSlotsWrite``,
  ``MixedRunsWrite``, ``QuickPlantWrite``; ``PlanBatchWrite`` with ``slot_inserts``) hands the fence over by keyword;
* every public repository method that takes one of those writes, and ``update_slot_fields``, calls
  ``take_slot_rules`` - so a fence handed over is never dropped on the floor.

The interleavings themselves are forced against ArangoDB in
``tests/integration/test_garden_resource_repository.py::TestBedLevelSlotRulesHoldUnderConcurrentWrites`` and
``tests/integration/test_planting_reservation_flow.py::test_a_run_layout_loses_to_a_zone_drawn_after_its_check_2773``.
"""

from __future__ import annotations

import ast
from functools import cache
from pathlib import Path

from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"
_SERVICES = _APP / "domain" / "services"
_DATA_ACCESS = _APP / "data_access"

#: The two rule predicates of ``garden_plan_engine``.
_PREDICATES = frozenset({"slots_outside_bed", "overlapping_zones"})
#: The write types that carry slots into a bed → the keyword that hands their fence over.
_FENCED_WRITES: dict[str, str] = {
    "SlotBatchWrite": "slot_rules_revision",
    "RunSlotsWrite": "slot_rules_revision",
    "MixedRunsWrite": "slot_rules_revision",
    "QuickPlantWrite": "slot_rules_revision",
}
#: ``PlanBatchWrite`` carries slots only with ``slot_inserts``; the import inserts them into beds it creates itself.
_PLAN_BATCH_SLOT_INSERTS_EXEMPT: dict[str, str] = {
    "app/domain/services/garden_plan_import_service.py": (
        "the import inserts slots only into the beds it inserts in the same transaction - no sibling to race"
    ),
}


def _relative(path: Path) -> str:
    return path.relative_to(_APP.parent).as_posix()


@cache
def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _called_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute):
                names.add(func.attr)
            elif isinstance(func, ast.Name):
                names.add(func.id)
    return names


def _methods(cls: ast.ClassDef) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {node.name: node for node in cls.body if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)}


def _check_sites() -> dict[str, set[str]]:
    """``path::Class.method`` → the names it calls, for every method that reaches a V-04/V-06 predicate."""
    sites: dict[str, set[str]] = {}
    for path in sorted(_SERVICES.rglob("*.py")):
        for cls in (node for node in ast.walk(_tree(path)) if isinstance(node, ast.ClassDef)):
            methods = _methods(cls)
            calls = {name: _called_names(fn) for name, fn in methods.items()}
            for name in methods:
                if _reaches(calls, name, frozenset()):
                    sites[f"{_relative(path)}::{cls.name}.{name}"] = calls[name]
    return sites


def _reaches(calls: dict[str, set[str]], name: str, seen: frozenset[str]) -> bool:
    """Whether ``name`` calls a predicate itself or through a method of its own class."""
    if name in seen or name not in calls:
        return False
    own = calls[name]
    return bool(own & _PREDICATES) or any(_reaches(calls, other, seen | {name}) for other in own if other in calls)


def test_the_derivation_finds_the_check_sites_it_exists_for() -> None:
    """Positive control: the scan sees the five sites the fix fenced (it would pass vacuously if it saw none)."""
    readers = {site for site, calls in _check_sites().items() if "load_slot_rule_basis" in calls}
    assert readers >= {
        "app/domain/services/garden_resource_service.py::GardenResourceService._checked_bed_rules",
        "app/domain/services/garden_resource_service.py::GardenResourceService.replace_slots",
        "app/domain/services/planting_reservation_service.py::PlantingReservationService.prepare_layout",
        "app/domain/services/garden_plan_service.py::GardenPlanService._check_slots_of_reshaped_beds",
        "app/domain/services/garden_plan_season_service.py::GardenPlanSeasonService._plan_the_beds",
    }


def test_no_slot_rule_check_reads_its_siblings_without_the_fence() -> None:
    unfenced = sorted(site for site, calls in _check_sites().items() if "load_active_slots" in calls)
    assert unfenced == [], (
        "These methods check V-04/V-06 against slots read through load_active_slots, which carries no fence; a slot "
        "or frame write landing after that read is never noticed (#2773). Read through load_slot_rule_basis and hand "
        f"its revision to the write: {unfenced}"
    )


def _keywords(call: ast.Call) -> set[str]:
    return {keyword.arg for keyword in call.keywords if keyword.arg is not None}


def test_every_write_that_carries_slots_hands_the_fence_over() -> None:
    missing: list[str] = []
    seen: set[str] = set()
    for path in sorted(_APP.rglob("*.py")):
        if _DATA_ACCESS in path.parents:
            continue
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            name, where = node.func.id, f"{_relative(path)}:{node.lineno}"
            if name in _FENCED_WRITES:
                seen.add(name)
                if _FENCED_WRITES[name] not in _keywords(node):
                    missing.append(f"{where} {name} without {_FENCED_WRITES[name]}=")
            elif name == "PlanBatchWrite" and "slot_inserts" in _keywords(node):
                seen.add(name)
                if "slot_rules_revisions" not in _keywords(node) and _relative(path) not in (
                    _PLAN_BATCH_SLOT_INSERTS_EXEMPT
                ):
                    missing.append(f"{where} PlanBatchWrite(slot_inserts=...) without slot_rules_revisions=")
    assert seen == {*_FENCED_WRITES, "PlanBatchWrite"}, f"the scan lost a write it exists for: {sorted(seen)}"
    assert missing == [], f"A write carries slots into a bed without the fence its check read (#2773): {missing}"


def test_every_repository_write_of_slots_takes_the_fence() -> None:
    write_types = {*_FENCED_WRITES, "PlanBatchWrite"}
    takers: dict[str, bool] = {}
    for path in sorted(_DATA_ACCESS.rglob("*.py")):
        for cls in (node for node in ast.walk(_tree(path)) if isinstance(node, ast.ClassDef)):
            for name, fn in _methods(cls).items():
                annotations = {
                    ast.unparse(arg.annotation) for arg in fn.args.args + fn.args.kwonlyargs if arg.annotation
                }
                carries = bool(annotations & write_types) and not name.startswith("_")
                if carries or name == "update_slot_fields":
                    takers[f"{_relative(path)}::{cls.name}.{name}"] = "take_slot_rules" in _called_names(fn)
    assert {
        "app/data_access/arango/garden_plan_repository.py::ArangoGardenPlanRepository.update_slot_fields",
        "app/data_access/arango/garden_plan_repository.py::ArangoGardenPlanRepository.replace_slots",
        "app/data_access/arango/garden_plan_repository.py::ArangoGardenPlanRepository.apply_plan_batch",
        "app/data_access/arango/planting_reservation_repository.py::ArangoPlantingReservationRepository.place_run_layout",
        "app/data_access/arango/planting_reservation_repository.py::ArangoPlantingReservationRepository.create_mixed_runs",
        "app/data_access/arango/planting_reservation_repository.py::ArangoPlantingReservationRepository.quick_plant",
    } <= set(takers), f"the scan lost a writer it exists for: {sorted(takers)}"
    dropped = sorted(site for site, takes in takers.items() if not takes)
    assert dropped == [], f"These repository writes take a fence but never compare it (take_slot_rules): {dropped}"
