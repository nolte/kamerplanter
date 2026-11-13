"""#2715 item 5 — the photos a committed bed delete lets go of are released, by construction, not by memory.

A bed delete reads the photo ids its deleted beds held inside the transaction and hands them back on a carrier
(``PlanBatchOutcome.released_photo_refs``, ``PlanBatchResult.released_photo_refs``,
``PlanImportReport.released_photo_refs``, ``SiteDeletion.location_photo_refs``). The photos go only when somebody
passes those ids to :func:`~app.domain.services.location_photo_service.release_location_photos` after the commit.
Before #2715 five callers did and two public ones did not (the synchronous ``GardenPlanService.apply_batch`` and
``GardenResourceService.delete_location``, which handed the ids to *its* caller): the nightly bed-photo sweep was the
only thing that caught a forgotten release.

**The class, enumerated from the data, not from the sites.** A *carrier* is any class under ``app/`` that declares
one of :data:`_CARRIER_FIELDS` (or inherits from one that does). A *producer* is any function under ``app/`` whose
return annotation names a carrier. A producer *releases* when its own body calls one of :data:`_RELEASERS`. Every
function that refers to a producer (calls it, or hands it to ``run_in_threadpool``) must:

* refer only to producers that release (``apply_batch_async`` discards what it committed), or
* release itself (a router that calls ``service.release_photos(report, …)``), or
* be a producer itself (it hands the carrier on, so *its* callers are held to this rule), or
* be decided in :data:`_NO_BED_DELETE` — a caller whose operations cannot delete a bed, with the reason.

A new caller of a non-releasing producer therefore fails here until it releases or is decided: the opt-in at the
call site that drifted between siblings (#948) becomes a listed decision. A stale entry fails too.

**What the selector does not see**, named rather than discovered later: a producer reached through a variable
(``fn = service.apply_batch; fn(...)``), dynamic dispatch, and a carrier built from a ``dict``. Names are matched
by attribute name, so two functions of one name are judged together (the stricter one wins).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"

#: The fields a committed bed delete fills with the photo ids it let go of.
_CARRIER_FIELDS = frozenset({"released_photo_refs", "location_photo_refs"})

#: The calls that discard released photos after a commit.
_RELEASERS = frozenset({"release_location_photos", "release_photos"})

#: Callers of a non-releasing producer whose operations cannot delete a bed - qualified name: reason.
_RESOURCES = "app.domain.services.garden_resource_service.GardenResourceService"
_OBJECT_OPS = (
    "garden-object operations only (create / update_fields / update_geometry / set_z_order / delete of an object)"
)
_NO_BED_DELETE: dict[str, str] = {
    "app.api.v1.garden_plan.tenant_router.put_boundary": "set_boundary sends one SetBoundaryOp",
    "app.domain.services.bed_csv_import_service.BedCsvImportService.import_beds": (
        "create_beds sends create_location operations only"
    ),
    "app.domain.services.garden_plan_season_service.GardenPlanSeasonService.new_season": (
        "the season write archives slots and moves plants; its PlanBatchWrite sets no location_deletes"
    ),
    f"{_RESOURCES}.patch_location": "field, geometry and status operations of the one bed it patches",
    f"{_RESOURCES}._write_status": "a status change: location_updates and a care event, no location_deletes",
    f"{_RESOURCES}.create_garden_object": _OBJECT_OPS,
    f"{_RESOURCES}.patch_garden_object": _OBJECT_OPS,
    f"{_RESOURCES}.delete_garden_object": _OBJECT_OPS,
}


@dataclass(frozen=True)
class _Function:
    module: str
    qualname: str
    node: ast.FunctionDef | ast.AsyncFunctionDef

    def names(self) -> set[str]:
        """Every attribute and bare name this function refers to (calls and references alike)."""
        found: set[str] = set()
        for node in ast.walk(self.node):
            if isinstance(node, ast.Attribute):
                found.add(node.attr)
            elif isinstance(node, ast.Name):
                found.add(node.id)
        return found

    def returns(self) -> set[str]:
        if self.node.returns is None:
            return set()
        return {
            node.id if isinstance(node, ast.Name) else node.attr
            for node in ast.walk(self.node.returns)
            if isinstance(node, ast.Name | ast.Attribute)
        } | _string_annotation_names(self.node.returns)

    def calls(self) -> set[str]:
        found: set[str] = set()
        for node in ast.walk(self.node):
            if isinstance(node, ast.Call):
                func = node.func
                found.add(func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", ""))
        return found


def _string_annotation_names(annotation: ast.expr) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(annotation):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            try:
                parsed = ast.parse(node.value, mode="eval")
            except SyntaxError:
                continue
            names |= {n.id for n in ast.walk(parsed) if isinstance(n, ast.Name)}
    return names


@cache
def _modules() -> tuple[tuple[str, ast.Module], ...]:
    return tuple(
        (str(path.relative_to(_APP.parent)), ast.parse(path.read_text(encoding="utf-8")))
        for path in sorted(_APP.rglob("*.py"))
    )


@cache
def _carriers() -> frozenset[str]:
    classes: dict[str, ast.ClassDef] = {}
    for _name, module in _modules():
        for node in ast.walk(module):
            if isinstance(node, ast.ClassDef):
                classes[node.name] = node
    carriers = {
        name
        for name, node in classes.items()
        if any(
            isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name) and item.target.id in _CARRIER_FIELDS
            for item in node.body
        )
    }
    grew = True
    while grew:  # a subclass of a carrier carries the field too (``PlanImportResponse(PlanImportReport)``)
        grew = False
        for name, node in classes.items():
            bases = {base.id if isinstance(base, ast.Name) else getattr(base, "attr", "") for base in node.bases}
            if name not in carriers and bases & carriers:
                carriers.add(name)
                grew = True
    return frozenset(carriers)


@cache
def _functions() -> tuple[_Function, ...]:
    found: list[_Function] = []
    for module_name, module in _modules():
        prefix = module_name.removesuffix(".py").replace("/", ".")

        _visit(module, prefix, prefix, found)
    return tuple(found)


def _visit(node: ast.AST, module: str, scope: str, found: list[_Function]) -> None:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.ClassDef):
            _visit(child, module, f"{scope}.{child.name}", found)
        elif isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            found.append(_Function(module, f"{scope}.{child.name}", child))
            _visit(child, module, f"{scope}.{child.name}", found)


def _producers() -> dict[str, list[_Function]]:
    carriers = _carriers()
    producers: dict[str, list[_Function]] = {}
    for function in _functions():
        if function.returns() & carriers:
            producers.setdefault(function.node.name, []).append(function)
    return producers


def _releases(function: _Function) -> bool:
    return bool(function.calls() & _RELEASERS)


def _unreleased_callers() -> dict[str, list[str]]:
    producers = _producers()
    offenders: dict[str, list[str]] = {}
    for function in _functions():
        referred: set[str] = set()
        for name in function.names() - {function.node.name}:
            # A private name is the module's own (``_apply``, ``_report`` mean something else in every module); a
            # public one is matched across modules. Either way a name is safe only when every function of that
            # name in reach releases what it committed.
            reachable = [d for d in producers.get(name, []) if not name.startswith("_") or d.module == function.module]
            if reachable and not all(_releases(d) for d in reachable):
                referred.add(name)
        if not referred or _releases(function) or function.node.name in producers:
            continue
        offenders[function.qualname] = sorted(referred)
    return offenders


def test_the_detector_finds_the_carriers_and_producers_it_was_built_around() -> None:
    """The measuring tool first: a renamed field or a moved class must fail here, not empty the selection."""
    assert {"PlanBatchOutcome", "PlanBatchResult", "PlanImportReport", "PlanImportResponse", "SiteDeletion"} <= (
        _carriers()
    )
    assert {
        "apply_plan_batch",
        "apply_batch",
        "apply_batch_async",
        "import_plan",
        "restore_snapshot",
        "delete_site",
    } <= (set(_producers()))


def test_every_caller_of_an_unreleasing_bed_delete_releases_or_is_decided() -> None:
    offenders = {name: refs for name, refs in _unreleased_callers().items() if name not in _NO_BED_DELETE}

    assert offenders == {}, (
        "These functions refer to a bed-deleting call that hands the released photo ids back, and neither release "
        "them (release_location_photos / release_photos), nor hand the carrier on, nor are decided in "
        f"_NO_BED_DELETE: {offenders}"
    )


def test_no_decision_is_stale() -> None:
    assert sorted(set(_NO_BED_DELETE) - set(_unreleased_callers())) == []
    assert all(reason.strip() for reason in _NO_BED_DELETE.values())
