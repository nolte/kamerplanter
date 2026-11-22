"""#2556 — every repository delete cuts the edges derived for what it removes, and every declared reference is settled.

Process finding of group ``2026-10-29-delete-cascades`` (and again ``2026-11-16-delete-cascades``): ``delete_site``,
``delete_location``, ``delete_template``, ``delete_slot`` and ``delete_substrate`` each **hand-listed** what they
removed, and each missed something registered later — ``care_event_at`` on a location, ``placed_in`` on a slot,
``uses_type`` on a substrate — which then dangled on a document that was gone. The repository already has the two
machine-readable populations a delete has to reach:

1. **Edges.** ``graph_edges.edges_touching(V)``, derived from ``GRAPH_EDGE_DEFINITIONS``: every edge collection that
   can end at a vertex of ``V``. A delete method that removes rows of ``V`` must reference that derivation — a
   module constant bound to ``edges_touching(col.V)`` (``_SLOT_EDGES``, ``ZONE_EDGES`` …) or the call itself —
   anywhere in what it calls on its own class. Naming the edge collections one by one does not count: that is the
   hand list this guard exists to retire.
2. **References.** ``TenantExportEngine.FIELD_REFERENCES`` / ``COLLECTION_REFERENCES`` declare every ``*_key`` field
   that points at a tenant row. For each internal ``(field → target)`` pair, one decision is pinned: the import
   heals it (``provenance`` — cleared and counted on re-import), nothing in the data-access layer deletes the
   target, the target's delete names the field (it nulls or refuses on it), or :data:`REFERENCE_DECISIONS` says why
   the key may outlive its row.

Both populations are enumerated from code; :data:`EDGE_ALLOWLIST` and :data:`REFERENCE_DECISIONS` are the only
hand-written parts, every entry carries its reason, and an entry that no longer matches a gap fails the guard.

**Why the erasure guards do not cover this.** ``test_tenant_erasure_inventory_is_complete`` and
``test_garden_plan_collections_are_in_the_erasure_cascade`` pin that every collection and account field is *in the
erasure rules* — a statement about what the tenant/account cascade removes as a whole. Neither asks whether one
parent's delete reaches its children inside a living tenant; both stayed green while the five deletes above left
edges and keys behind.

What the scan reads (AST, ``app/data_access/arango/*.py``): a method named ``delete`` or ``delete_*`` on a class
removes rows of ``V`` when it, or a method of its own class it calls, calls ``super().delete``/``self.delete`` (the
class's collection, from ``super().__init__(db, col.V)``), ``self.<view>.delete`` (the view's collection, from
``self.<view> = …(db, col.V …)``), ``txn.collection(col.V).delete`` or ``self._remove_rows(txn, col.V, …)``.
Spelling it does not see: a removal through a variable collection name (``delete_site``'s dependents loop) or an
AQL ``REMOVE`` over a bound ``@@col`` it cannot resolve — those are covered by the integration tests of the
respective delete, not here.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from app.data_access.arango import collections as col
from app.data_access.arango.graph_edges import edges_touching
from app.domain.engines.tenant_export_engine import TenantExportEngine

ARANGO = Path(__file__).resolve().parents[3] / "app" / "data_access" / "arango"

_RESIDUAL = (
    "pre-existing hand-listed delete, measured by this guard on 2026-11-16 and outside the #2560 class sweep (which "
    "named slots, substrates and plant_instances); migrate it to the derived set when the delete is next touched"
)
_CATALOGUE_RESIDUAL = "global catalogue row, deleted by a platform admin only; " + _RESIDUAL.removeprefix(
    "pre-existing "
)

#: ``"<module stem>:<Class>.<method>"`` → why the delete may leave edges of what it removes. Only gaps belong here.
EDGE_ALLOWLIST: dict[str, str] = {
    "api_key_repository:ArangoApiKeyRepository.delete": _RESIDUAL,
    "botanical_family_repository:ArangoBotanicalFamilyRepository.delete_family": _CATALOGUE_RESIDUAL,
    "fertilizer_repository:ArangoFertilizerRepository.delete": _RESIDUAL,
    "inventree_repository:ArangoInvenTreeRepository.delete_equipment": _RESIDUAL,
    "ipm_repository:ArangoIpmRepository.delete_pest": _CATALOGUE_RESIDUAL,
    "ipm_repository:ArangoIpmRepository.delete_disease": _CATALOGUE_RESIDUAL,
    "lifecycle_repository:ArangoLifecycleRepository.delete_phase": _CATALOGUE_RESIDUAL,
    "membership_repository:ArangoMembershipRepository.delete": _RESIDUAL,
    "membership_repository:ArangoMembershipRepository.delete_while_tenant_frozen": _RESIDUAL,
    "nutrient_plan_repository:ArangoNutrientPlanRepository.delete": _RESIDUAL,
    "overwintering_profile_repository:ArangoOverwinteringProfileRepository.delete_profile": _RESIDUAL,
    "phase_sequence_repository:ArangoPhaseSequenceRepository.delete_definition": _CATALOGUE_RESIDUAL,
    "phase_sequence_repository:ArangoPhaseSequenceRepository.delete_sequence": _CATALOGUE_RESIDUAL,
    "planting_run_repository:ArangoPlantingRunRepository.delete": (
        "only a planned run is deleted (PlantingRunService.delete_run refuses any other status, and drops its "
        "reservations first) or the run a failed create just wrote — the relations a run collects while it grows "
        "(phases, feedings, care, diagnoses, tasks) cannot exist yet; " + _RESIDUAL.removeprefix("pre-existing ")
    ),
    "post_harvest_repository:ArangoPostHarvestRepository.delete_batch": _RESIDUAL,
    "sensor_repository:ArangoSensorRepository.delete": _RESIDUAL,
    "species_repository:ArangoSpeciesRepository.delete_cultivar": _CATALOGUE_RESIDUAL,
    "substrate_repository:ArangoSubstrateRepository.delete_batch": _RESIDUAL,
    "tank_repository:ArangoTankRepository.delete": _RESIDUAL,
    "tank_repository:ArangoTankRepository.delete_schedule": _RESIDUAL,
    "task_repository:ArangoTaskRepository.delete_workflow_template": _RESIDUAL,
    "task_repository:ArangoTaskRepository.delete_task_template": _RESIDUAL,
    "task_repository:ArangoTaskRepository.delete_task": _RESIDUAL,
}

_REIMPORT_REFUSED = (
    "open (#2560 predicate 2): the delete leaves the key on its referrers, and a tenant archive holding one is "
    "refused on re-import (IMPORT_MISSING_CATALOG_ENTRIES) — null, refuse or declare it provenance, per pair"
)

#: ``(field path, target collection)`` → why the key may outlive the row it names. Only open pairs belong here.
REFERENCE_DECISIONS: dict[tuple[str, str], str] = {
    ("activity_key", "activities"): _REIMPORT_REFUSED,
    ("cloned_from_key", "nutrient_plans"): (
        "lineage of a cloned plan; " + _REIMPORT_REFUSED.removeprefix("open (#2560 predicate 2): ")
    ),
    ("cultivar_key", "cultivars"): _REIMPORT_REFUSED,
    ("default_nutrient_plan_key", "nutrient_plans"): _REIMPORT_REFUSED,
    ("delivery_channels.fertilizer_dosages.fertilizer_key", "fertilizers"): _REIMPORT_REFUSED,
    ("fertilizers_used.fertilizer_key", "fertilizers"): _REIMPORT_REFUSED,
    ("fertilizers_used.product_key", "fertilizers"): _REIMPORT_REFUSED,
    ("nutrient_plan_key", "nutrient_plans"): _REIMPORT_REFUSED,
    ("product_key", "fertilizers"): _REIMPORT_REFUSED,
    ("mix_components.substrate_key", "substrates"): (
        "a mix keeps the components it was mixed from; delete_substrate refuses only while a plant or a run uses "
        "the substrate (operator decision D2, #2560) — " + _REIMPORT_REFUSED.removeprefix("open (#2560 predicate 2): ")
    ),
    ("recurring_task_templates", "task_templates"): _REIMPORT_REFUSED,
    ("source_template_key", "task_templates"): _REIMPORT_REFUSED,
    ("source_workflow_key", "workflow_templates"): _REIMPORT_REFUSED,
    ("template_key", "task_templates"): _REIMPORT_REFUSED,
}


# ── the scan ─────────────────────────────────────────────────────────────────────────────────────────────────────────


def _col_name(node: ast.AST | None) -> str | None:
    """``col.SLOTS`` → ``"slots"`` (the value of the constant), else ``None``."""
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "col":
        value = getattr(col, node.attr, None)
        return value if isinstance(value, str) else None
    return None


@dataclass
class _Class:
    module: str
    name: str
    collection: str | None = None
    views: dict[str, str] = field(default_factory=dict)
    methods: dict[str, ast.FunctionDef] = field(default_factory=dict)


@dataclass
class _Module:
    stem: str
    tree: ast.Module
    #: module-level name → the vertex collection whose ``edges_touching`` it holds
    edge_sets: dict[str, str] = field(default_factory=dict)
    classes: list[_Class] = field(default_factory=list)


def _edges_touching_arg(node: ast.AST | None) -> str | None:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "edges_touching"
        and node.args
    ):
        return _col_name(node.args[0])
    return None


@cache
def _parse() -> dict[str, _Module]:
    modules: dict[str, _Module] = {}
    for path in sorted(ARANGO.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module = _Module(path.stem, tree)
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                vertex = _edges_touching_arg(node.value)
                for target in targets:
                    if vertex and isinstance(target, ast.Name):
                        module.edge_sets[target.id] = vertex
            if isinstance(node, ast.ClassDef):
                module.classes.append(_class_of(path.stem, node))
        modules[path.stem] = module
    # Imported edge sets (``from …irrigation_zone_repository import ZONE_EDGES``) resolve to their defining module.
    for module in modules.values():
        for node in module.tree.body:
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app.data_access.arango."):
                source = modules.get(node.module.rsplit(".", 1)[-1])
                for alias in node.names:
                    if source and alias.name in source.edge_sets:
                        module.edge_sets[alias.asname or alias.name] = source.edge_sets[alias.name]
    return modules


def _class_of(stem: str, node: ast.ClassDef) -> _Class:
    found = _Class(stem, node.name)
    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            found.methods[item.name] = item
    init = found.methods.get("__init__")
    for sub in ast.walk(init) if init else ():
        is_init = isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "__init__"
        if is_init and len(sub.args) >= 2 and (name := _col_name(sub.args[1])):
            found.collection = name
        if isinstance(sub, ast.Assign) and isinstance(sub.value, ast.Call):
            target = sub.targets[0]
            args = sub.value.args
            if isinstance(target, ast.Attribute) and len(args) >= 2 and (name := _col_name(args[1])):
                found.views[target.attr] = name
    return found


def _reachable(cls: _Class, method: str) -> Iterator[ast.FunctionDef]:
    """*method* and every method of its own class it calls (``self.x(``, ``Cls.x(``), transitively."""
    seen: set[str] = set()
    stack = [method]
    while stack:
        name = stack.pop()
        if name in seen or name not in cls.methods:
            continue
        seen.add(name)
        fn = cls.methods[name]
        yield fn
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                owner = sub.func.value
                if isinstance(owner, ast.Name) and owner.id in ("self", cls.name):
                    stack.append(sub.func.attr)


def _removed(cls: _Class, method: str) -> set[str]:
    removed: set[str] = set()
    for fn in _reachable(cls, method):
        for sub in ast.walk(fn):
            if not (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)):
                continue
            owner, attr = sub.func.value, sub.func.attr
            if attr == "delete":
                via_super = (
                    isinstance(owner, ast.Call) and isinstance(owner.func, ast.Name) and owner.func.id == "super"
                )
                via_self = isinstance(owner, ast.Name) and owner.id == "self" and method != "delete"
                if via_super or via_self:
                    removed.add(cls.collection or "")
                elif (
                    isinstance(owner, ast.Attribute) and isinstance(owner.value, ast.Name) and owner.value.id == "self"
                ):
                    if owner.attr in cls.views:
                        removed.add(cls.views[owner.attr])
                elif (
                    isinstance(owner, ast.Call)
                    and isinstance(owner.func, ast.Attribute)
                    and owner.func.attr == "collection"
                    and owner.args
                    and (name := _col_name(owner.args[0]))
                ):
                    removed.add(name)
            elif attr == "_remove_rows" and len(sub.args) >= 2 and (name := _col_name(sub.args[1])):
                removed.add(name)
    removed.discard("")
    return removed


def _derived_for(module: _Module, cls: _Class, method: str) -> tuple[set[str], set[str]]:
    """The vertex collections whose ``edges_touching`` set the method reaches, and the collections it names."""
    derived: set[str] = set()
    named: set[str] = set()
    for fn in _reachable(cls, method):
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Name) and sub.id in module.edge_sets:
                derived.add(module.edge_sets[sub.id])
            if vertex := _edges_touching_arg(sub):
                derived.add(vertex)
            if name := _col_name(sub):
                named.add(name)
    return derived, named


@dataclass(frozen=True)
class DeletePath:
    ident: str
    removes: frozenset[str]
    derived: frozenset[str]
    named: frozenset[str]

    def missing(self) -> dict[str, list[str]]:
        """Per removed vertex collection, the edge collections of its derived set the delete does not reach.

        Reached means: the delete references the derivation for that collection, or names every edge collection
        of it. A hand list that is complete today passes — the guard re-derives the set on every run, so the next
        relation registered for the collection fails it here instead of dangling in production. The endpoint
        (``_from``/``_to``) a hand-listed cut uses is not checked; the integration tests of each delete are.
        """
        gaps: dict[str, list[str]] = {}
        for vertex in sorted(self.removes):
            if vertex in self.derived:
                continue
            absent = sorted({edge for edge, _ in edges_touching(vertex)} - self.named)
            if absent:
                gaps[vertex] = absent
        return gaps


@cache
def delete_paths() -> tuple[DeletePath, ...]:
    paths: list[DeletePath] = []
    for module in _parse().values():
        for cls in module.classes:
            for name in cls.methods:
                if name != "delete" and not name.startswith("delete_"):
                    continue
                removes = _removed(cls, name)
                if not removes:
                    continue
                derived, named = _derived_for(module, cls, name)
                paths.append(
                    DeletePath(
                        f"{module.stem}:{cls.name}.{name}", frozenset(removes), frozenset(derived), frozenset(named)
                    )
                )
    return tuple(paths)


def _strings_of(path: DeletePath) -> set[str]:
    module = _parse()[path.ident.split(":", 1)[0]]
    cls_name, method = path.ident.split(":", 1)[1].split(".", 1)
    cls = next(c for c in module.classes if c.name == cls_name)
    return {
        sub.value
        for fn in _reachable(cls, method)
        for sub in ast.walk(fn)
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str)
    }


def internal_reference_pairs() -> set[tuple[str, str, bool]]:
    """``(field path, target, provenance)`` of every internal reference the export engine declares."""
    pairs: set[tuple[str, str, bool]] = set()
    declared = [
        *TenantExportEngine.FIELD_REFERENCES.items(),
        *(item for refs in TenantExportEngine.COLLECTION_REFERENCES.values() for item in refs.items()),
    ]
    for path, ref in declared:
        if ref.kind != "internal":
            continue
        for target in ref.targets:
            pairs.add((path, target, bool(getattr(ref, "provenance", False))))
    return pairs


def reference_pairs_needing_a_decision() -> dict[tuple[str, str], list[str]]:
    """Internal pairs a delete can leave dangling **and** the import cannot clear: ``(field, target)`` → its deletes.

    The import clears an internal key the archive does not hold — unless the target is a (hybrid) catalogue: then
    the key may name a row of the target installation, and a missing one refuses the archive. A ``provenance``
    reference is cleared and counted even there (#2528). So only a non-provenance pair whose target is a catalogue
    and has a delete path needs a pinned decision.
    """
    catalogues = set(TenantExportEngine.HYBRID_CATALOGUES) | set(TenantExportEngine.global_catalogues())
    deletes: dict[str, list[DeletePath]] = {}
    for path in delete_paths():
        for vertex in path.removes:
            deletes.setdefault(vertex, []).append(path)
    needing: dict[tuple[str, str], list[str]] = {}
    for field_path, target, provenance in sorted(internal_reference_pairs()):
        if provenance or target not in catalogues or target not in deletes:
            continue
        # Settled in code: a delete of the target names the field — it nulls, removes or refuses on it. A nested path
        # (``mix_components.substrate_key``) must be named whole: naming its leaf is a position on another field.
        if any(any(field_path in text for text in _strings_of(path)) for path in deletes[target]):
            continue
        needing[(field_path, target)] = [path.ident for path in deletes[target]]
    return needing


# ── the checks ───────────────────────────────────────────────────────────────────────────────────────────────────────


def test_the_scan_sees_the_deletes_it_is_about() -> None:
    """Positive control: the scan finds the deletes this guard was written for, and each reaches its derived set."""
    by_ident = {path.ident: path for path in delete_paths()}
    expected = {
        "site_repository:ArangoSiteRepository.delete_site": {col.SITES, col.LOCATIONS, col.SLOTS},
        "site_repository:ArangoSiteRepository.delete_location": {col.LOCATIONS, col.SLOTS},
        "site_repository:ArangoSiteRepository.delete_slot": {col.SLOTS},
        "substrate_repository:ArangoSubstrateRepository.delete_substrate": {col.SUBSTRATES},
        "plant_instance_repository:ArangoPlantInstanceRepository.delete": {col.PLANT_INSTANCES},
        "irrigation_zone_repository:ArangoIrrigationZoneRepository.delete_zone": {col.IRRIGATION_ZONES},
    }
    for ident, removes in expected.items():
        assert ident in by_ident, f"the scan no longer sees {ident}"
        assert removes <= by_ident[ident].removes, ident
        assert by_ident[ident].missing() == {}, ident
    assert len(by_ident) > 40, "the scan sees far fewer deletes than the repository has — the AST walk broke"


def test_every_delete_reaches_the_edges_derived_for_what_it_removes() -> None:
    gaps = {path.ident: path.missing() for path in delete_paths() if path.missing()}
    unexplained = {ident: missing for ident, missing in gaps.items() if ident not in EDGE_ALLOWLIST}
    assert not unexplained, (
        "These deletes leave edges of what they remove behind — cut ``edges_touching(V)`` for each removed "
        "collection (graph_edges.remove_edges) or, only for a deliberate exception, add an EDGE_ALLOWLIST entry "
        "with the reason:\n" + "\n".join(f"  {ident}: {missing}" for ident, missing in sorted(unexplained.items()))
    )


def test_no_edge_allowlist_entry_is_stale() -> None:
    gaps = {path.ident for path in delete_paths() if path.missing()}
    stale = sorted(set(EDGE_ALLOWLIST) - gaps)
    assert not stale, f"These EDGE_ALLOWLIST entries no longer name a gap (remove them): {stale}"


def test_every_reference_a_delete_can_strand_has_a_pinned_decision() -> None:
    needing = reference_pairs_needing_a_decision()
    undecided = {pair: deletes for pair, deletes in needing.items() if pair not in REFERENCE_DECISIONS}
    assert not undecided, (
        "A delete of these catalogue targets leaves the key on its referrers, and the tenant import refuses an "
        "archive holding it. Null the field or refuse in the delete (naming the field there settles the pair), "
        "declare the reference provenance in TenantExportEngine, or pin a REFERENCE_DECISIONS entry:\n"
        + "\n".join(f"  {pair}: {deletes}" for pair, deletes in sorted(undecided.items()))
    )


def test_no_reference_decision_is_stale() -> None:
    stale = sorted(set(REFERENCE_DECISIONS) - set(reference_pairs_needing_a_decision()))
    assert not stale, f"These REFERENCE_DECISIONS entries are settled in code or gone (remove them): {stale}"


def test_every_entry_says_why() -> None:
    for ident, reason in [*EDGE_ALLOWLIST.items(), *((str(pair), why) for pair, why in REFERENCE_DECISIONS.items())]:
        assert len(reason.strip()) >= 40, f"{ident}: a reason, not a label"
