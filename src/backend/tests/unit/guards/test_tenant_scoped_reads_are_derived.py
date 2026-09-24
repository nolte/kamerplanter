"""#1708 — which repository reads must be tenant-scoped is derived, not remembered.

#1704 found the aggregated calendar reading three sources of **every** tenant.
No guard saw it: ``test_catalogue_reads_carry_a_tenant_predicate.py`` covers only
the hybrid catalogues, and ``TestTheSurfacesStayStrict`` in
``test_arango_call_surface_scoping.py`` was a hand list of methods — a new read
that takes no tenant is simply not on it. That is the "guard opt-in at the call
site" shape again: a guard that holds only for the sites someone enrolled.

**The rule, stated as a derivation.** Every public *read* method on a class under
``app/data_access`` is inventoried from the AST. Its collections are the ones its
body names (``col.X``, a bound sub-repository ``self._x``, the class's own
collection through the base primitives, a literal ``FOR v IN <name>``), followed
through same-class ``self.<method>()`` calls. A read is **subject** when one of
those collections carries a tenant:

* its model declares ``tenant_key`` (the models are the anchor — read through
  ``BaseArangoRepository[M]`` via ``scripts/arango_repository_bindings.py``, the
  module the privacy inventory shares), or
* its tenant is reachable through a parent declared once in
  :data:`PARENT_CHAINS` (``maintenance_logs → tanks``, ``slots → locations →
  sites`` …).

A subject read passes when it is, in this order:

``strict``            ``tenant_key`` keyword-only without a default. The target shape.
``positional``        ``tenant_key`` required but positional. It cannot be omitted,
                      which is the #1533 failure; it can be transposed with a
                      neighbouring ``str``. Not converted here — the count is pinned
                      exactly (:data:`POSITIONAL_TENANT_COUNT`) so a *new* method must
                      be ``strict`` and each conversion lowers the number.
``runtime-enforced``  ``tenant_key`` optional, paired with a keyword-only
                      ``all_tenants`` flag, and the body reaches
                      ``BaseArangoRepository._enforce_tenant_scope`` — omission raises
                      at run time unless the caller *says* "system context".
``catalogue-union``   reads only hybrid catalogues, takes ``tenant_key`` and builds the
                      ``tenant_scope`` union predicate; ``None`` is the documented
                      system-context whole-catalogue read (``SpeciesRepository.get_all``).
``anchored``          no tenant, but a parameter names a document of a **tenant-owned**
                      collection: ``key`` (the one document itself — its ``tenant_key``
                      comes back for the caller to verify), ``keys`` on a strictly owned
                      collection, the declared parent key of a collection it reads
                      (:data:`PARENT_CHAINS`), or a name/annotation in
                      :data:`ANCHOR_TARGETS` that lands on a strictly owned or
                      parent-scoped collection. A hybrid-catalogue anchor
                      (``species_key``) is **not** one: every tenant's rows hang off a
                      global species. Nor is ``keys`` over a catalogue — a batch
                      dereference is the #952 name-disclosure shape.

Anything else is a **finding**, unless it is on :data:`EXCLUSIONS` with a kind and
a reason. An exclusion that no longer matches a finding fails, so the list cannot
outlive what it excused; a ``system`` exclusion is additionally checked against
the typed call graph (no HTTP or MCP handler may reach it).

**What ``anchored`` does not prove — measured, not assumed.** The issue asked
whether a by-key read followed by an ownership check at the caller is a
legitimate category, *with evidence the check exists*. That evidence was measured
over the typed call graph of ``tests/unit/api/_write_call_graph.py``: of the 111
tenant-less subject reads of a first inventory on 2026-09-24, **73** had at least one resolved caller
without an ownership primitive (``verify_tenant_ownership``, ``require_owned_*``,
``resolve_owned_*``, a ``.tenant_key`` comparison) in the caller or a same-class
helper. The misses are dominated by shapes where the check is real but elsewhere:
a router-level ``Depends(require_owned_plant)`` (no call edge), a parent resolved
by one helper and the child read in the next, a Celery task that iterates one
tenant at a time. A rule that red on 73 mostly-correct sites would be lifted blind
the third time, so ``anchored`` is decided on the signature alone. Its residual is
the #927 shape — a route that hands an *unresolved* URL key to an anchored read —
and that is what the per-route two-tenant tests and the ``require_owned_*``
dependencies cover, not this file. Where an exclusion *can* name the check, it
does: a ``verified`` exclusion carries a witness function that is proven to call
both the read and the authorisation (:class:`TestTheExclusionsHoldTheirEvidence`).

**What the first run found.** On ``origin/develop`` at 18329ac36 the derivation
named 50 unscoped or optionally scoped reads out of 324 subject reads. Seven were
fixed as cross-tenant leaks reachable from a tenant route, each with a two-tenant
test (``tests/integration/test_derived_read_scope_tenant_isolation.py``); five took
an optional ``tenant_key`` and now take it without a default; one was dead code and
was removed. The remaining 37 are :data:`EXCLUSIONS`, each with a kind that says
what was checked. The interface half found ``IFertilizerRepository.get_stocks``
lagging its strict implementation.

**Spellings this does not match**, named rather than discovered later:

* a collection reached only through a **graph traversal over an edge** whose
  ``_to`` lands in it, with no ``col.X`` of that collection in the body — the edge
  collection is seen, the vertex collection is not;
* a collection reached by calling **another repository's** method from inside a
  repository (a hop across classes is not followed). A call to a module-level
  helper under ``app/data_access`` *is* followed one level, and those helpers are
  not inventoried as reads themselves — ``visible_fertilizer_labels`` takes its
  tenant keyword-only on its own account;
* a method that both reads and writes (``get_or_create``) is a *writer* here and
  is not inspected;
* a read on a class that is not under ``app/data_access`` (a service that holds a
  ``StandardDatabase`` is refused outright by ``check_layer_imports.py``).
"""

from __future__ import annotations

import ast
import inspect
import re
import shutil
from collections import defaultdict, deque
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import pytest

from app.data_access.arango import collections as col
from app.domain.services.favorites_service import _TENANT_OWNED_CATALOG_COLLECTIONS
from tests.support.execution_guards import find_project_root
from tests.support.repo_scripts import load_repo_script
from tests.unit.api._write_call_graph import _COLLECTION_MUTATORS, _QUERY_WRITE, call_graph

bindings = load_repo_script("arango_repository_bindings")

_APP = find_project_root(Path(__file__)) / "app"

# ── The declarations: collection-level, once ─────────────────────────────────

#: Hybrid catalogues: global seeds (``tenant_key == ""``) plus tenant rows, read
#: through the ``tenant_scope`` union. The favouritable set is held equal to the
#: models by ``test_favoritable_collections_declare_ownership.py``; cultivars are
#: added because #1090 made them tenant-ownable while ``v0038`` left the whole
#: legacy population global — the same shape, not favouritable.
#: Workflow and task templates follow the same convention (``TaskTemplate``'s
#: own comment: ``""`` is the hybrid-catalogue marker), and their reads go
#: through ``verify_tenant_read_access``, the hybrid read check.
HYBRID_CATALOGUES: frozenset[str] = frozenset(_TENANT_OWNED_CATALOG_COLLECTIONS) | {
    col.CULTIVARS,
    col.WORKFLOW_TEMPLATES,
    col.TASK_TEMPLATES,
}

#: Collections whose tenant is reachable only through a parent document, as
#: ``collection -> ((foreign-key field, parent collection), ...)``. More than one
#: pair means "exactly one of these parents" (``Sensor`` validates at most one).
#: ``locations`` and ``slots`` *have* a ``tenant_key`` field, but no write path
#: fills it (#1397) — the site is the only document in the chain that carries it,
#: which is why they are declared here and not left to the model.
#:
#: Checked both ways by :class:`TestTheParentChainsAreDeclaredOnceAndComplete`:
#: every field named here exists on the model and every parent carries a tenant,
#: and every non-tenant model with a foreign key onto a tenant-bearing collection
#: is declared here — so a new child collection cannot be forgotten.
PARENT_CHAINS: dict[str, tuple[tuple[str, str], ...]] = {
    col.MAINTENANCE_LOGS: (("tank_key", col.TANKS),),
    col.MAINTENANCE_SCHEDULES: (("tank_key", col.TANKS),),
    col.TANK_STATES: (("tank_key", col.TANKS),),
    col.TANK_FILL_EVENTS: (("tank_key", col.TANKS),),
    col.CARE_PROFILES: (("plant_key", col.PLANT_INSTANCES),),
    col.CARE_CONFIRMATIONS: (("plant_key", col.PLANT_INSTANCES),),
    col.HARVEST_OBSERVATIONS: (("plant_key", col.PLANT_INSTANCES),),
    col.PHASE_HISTORIES: (("plant_instance_key", col.PLANT_INSTANCES),),
    col.QUALITY_ASSESSMENTS: (("batch_key", col.HARVEST_BATCHES),),
    col.YIELD_METRICS: (("batch_key", col.HARVEST_BATCHES),),
    col.DRYING_PROGRESS: (("batch_key", col.POST_HARVEST_BATCHES),),
    col.STORAGE_OBSERVATIONS: (("batch_key", col.POST_HARVEST_BATCHES),),
    col.MOLD_ALERTS: (("batch_key", col.POST_HARVEST_BATCHES),),
    col.BURPING_EVENTS: (("batch_key", col.POST_HARVEST_BATCHES),),
    col.NUTRIENT_PLAN_PHASE_ENTRIES: (("plan_key", col.NUTRIENT_PLANS),),
    col.SENSORS: (("tank_key", col.TANKS), ("site_key", col.SITES), ("location_key", col.LOCATIONS)),
    col.LOCATIONS: (("site_key", col.SITES),),
    col.SLOTS: (("location_key", col.LOCATIONS),),
    col.TASK_COMMENTS: (("task_key", col.TASKS),),
    col.TASK_AUDIT_ENTRIES: (("task_key", col.TASKS),),
    # ``entity_key`` is polymorphic over ``entity_type`` — every target owns it.
    col.WORKFLOW_EXECUTIONS: (
        ("entity_key", col.PLANT_INSTANCES),
        ("entity_key", col.LOCATIONS),
        ("entity_key", col.TANKS),
        ("entity_key", col.PLANTING_RUNS),
    ),
}

#: Non-tenant collections owned by an **account**, not a tenant: a reference from
#: one of them onto a tenant-bearing collection is a pointer the account wrote,
#: not the row's owner. Exempt from the parent-chain completeness check, with the
#: reason.
ACCOUNT_SCOPED_COLLECTIONS: dict[str, str] = {
    col.ONBOARDING_STATES: "the wizard state of one account (REQ-020); selected_site_key is its own choice",
}

#: Foreign-key field / parameter name -> the collection it names. ``None`` marks
#: a reference that is not a tenant anchor at all (an account, an external id, a
#: global catalogue row). Used twice: to decide whether a read's parameter
#: *anchors* it, and to prove :data:`PARENT_CHAINS` complete. A name that is not
#: here is not guessed at — an unknown ``*_key`` field on a non-tenant model is
#: reported, and an unknown parameter does not anchor.
#:
#: ``batch_key`` and ``plan_key`` are deliberately absent: each names a different
#: collection in different models, so only :data:`PARENT_CHAINS` may resolve them.
ANCHOR_TARGETS: dict[str, str | None] = {
    "tank_key": col.TANKS,
    "source_tank_key": col.TANKS,
    "plant_key": col.PLANT_INSTANCES,
    "plant_instance_key": col.PLANT_INSTANCES,
    "mother_key": col.PLANT_INSTANCES,
    "site_key": col.SITES,
    "location_key": col.LOCATIONS,
    "slot_key": col.SLOTS,
    "run_key": col.PLANTING_RUNS,
    "planting_run_key": col.PLANTING_RUNS,
    "run_keys": col.PLANTING_RUNS,
    "actuator_key": col.ACTUATORS,
    "system_key": col.AQUAPONIC_SYSTEMS,
    "membership_key": col.MEMBERSHIPS,
    "harvest_batch_key": col.HARVEST_BATCHES,
    "task_key": col.TASKS,
    "task_keys": col.TASKS,
    "watering_log_key": col.WATERING_LOGS,
    "care_profile_key": col.CARE_PROFILES,
    "substrate_key": col.SUBSTRATES,
    "nutrient_plan_key": col.NUTRIENT_PLANS,
    "species_key": col.SPECIES,
    "cultivar_key": col.CULTIVARS,
    # Not tenant anchors.
    "user_key": None,  # an account; spans every tenant it is a member of
    "owner_user_key": None,
    "default_tenant_key": None,  # a tenant id, not a document of one
    "gbif_taxon_key": None,  # external taxonomy id
    "internal_key": None,  # ExternalMapping -> species / cultivar, both catalogue
    "source_key": None,  # external source registry
    "lifecycle_key": None,  # species lifecycle catalogue
    "phase_sequence_key": None,
    "phase_key": None,  # growth phase catalogue
    "from_phase_key": None,
    "to_phase_key": None,
    "indicator_key": None,  # harvest indicator catalogue
    "mixing_result_key": None,  # a computed mixing result, stored on the event itself
    "family_key": None,  # botanical families are global
    "pest_key": None,  # pests are global
    "workflow_template_key": col.WORKFLOW_TEMPLATES,
    "source_template_key": col.TASK_TEMPLATES,
    "activity_key": col.ACTIVITIES,
    "workflow_phase_key": None,  # a phase of a (hybrid) workflow template
    "phase_definition_key": None,  # phase definition catalogue
    # Catalogue references held by a starter kit or an onboarding state.
    "species_keys": col.SPECIES,
    "cultivar_keys": col.CULTIVARS,
    "nutrient_plan_keys": col.NUTRIENT_PLANS,
    "workflow_template_keys": col.WORKFLOW_TEMPLATES,
    "favorite_species_keys": col.SPECIES,
    "favorite_nutrient_plan_keys": col.NUTRIENT_PLANS,
    "selected_site_key": col.SITES,
    # Parameter *annotations* (``app/common/types.py`` aliases) name the same
    # thing where the parameter name does not: ``entry_key: PlantingRunEntryKey``.
    "PlantInstanceKey": col.PLANT_INSTANCES,
    "SiteKey": col.SITES,
    "LocationKey": col.LOCATIONS,
    "SlotKey": col.SLOTS,
    "PlantingRunKey": col.PLANTING_RUNS,
    "PlantingRunEntryKey": col.PLANTING_RUN_ENTRIES,
    "TankKey": col.TANKS,
    "TankStateKey": col.TANK_STATES,
    "MaintenanceLogKey": col.MAINTENANCE_LOGS,
    "MaintenanceScheduleKey": col.MAINTENANCE_SCHEDULES,
    "HarvestBatchKey": col.HARVEST_BATCHES,
    "HarvestObservationKey": col.HARVEST_OBSERVATIONS,
    "TaskKey": col.TASKS,
    "CareProfileKey": col.CARE_PROFILES,
    "SuccessionPlanKey": col.SUCCESSION_PLANS,
    "SpeciesKey": col.SPECIES,
    "CultivarKey": col.CULTIVARS,
    "FamilyKey": None,
    "PestKey": None,
    "UserKey": None,
}

#: The ``tenant_scope`` predicate builders a catalogue read must call. Read off
#: the module so a new builder is recognised without editing this file.
from app.data_access.arango import tenant_scope as _tenant_scope  # noqa: E402

PREDICATE_BUILDERS: frozenset[str] = frozenset(
    name for name in dir(_tenant_scope) if not name.startswith("_") and callable(getattr(_tenant_scope, name))
)

#: Methods of ``BaseArangoRepository`` that read the class's OWN collection. A
#: call ``self.<name>(...)`` in a repository body means "this reads my
#: collection". Attribute reads (``self.collection``, ``self._collection_name``)
#: count the same way.
_OWN_COLLECTION_ACCESS = frozenset(
    {
        "collection",
        "_collection_name",
        "_list_docs",
        "_find_docs",
        "_get_doc",
        "get_by_key",
        "get_or_raise",
        "get_all",
        "get_page",
        "find_by_field",
        "find_one_by_field",
        "get_edges",
    }
)

#: A literal loop over a collection inside a query string: ``FOR t IN tasks``.
#: Read from AST string constants, never from file text (#1456).
_LITERAL_LOOP = re.compile(r"\bIN\s+([a-z_][a-z_0-9]*)\b")

#: Measured on 2026-09-24. Pinned exactly: raising it means a new method took the
#: tenant positionally instead of keyword-only; lowering it is the conversion
#: this number exists to record.
POSITIONAL_TENANT_COUNT = 102

#: Anti-vacuity floors, a margin below the measured 2026-09-24 inventory (see
#: :class:`TestTheInventoryIsNotVacuous` for the printed counts).
MIN_READ_METHODS = 380
MIN_SUBJECT_READS = 220
MIN_REPOSITORY_CLASSES = 70


# ── The inventory ────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ReadMethod:
    """One public read method on a data-access class."""

    path: str
    owner: str
    name: str
    lineno: int
    collections: frozenset[str]
    positional: tuple[str, ...]
    #: The annotation name of each positional parameter (``None`` when absent).
    annotations: tuple[str | None, ...]
    keyword_only: tuple[str, ...]
    #: The annotation name of each keyword-only parameter.
    keyword_annotations: tuple[str | None, ...]
    tenant_shape: str
    all_tenants_flag: bool
    enforces_tenant_scope: bool
    builds_union_predicate: bool

    @property
    def qualname(self) -> str:
        return f"{self.owner}.{self.name}"


@dataclass
class Inventory:
    app_root: Path
    reads: list[ReadMethod] = field(default_factory=list)
    classes_seen: int = 0
    tenant_models: set[tuple[str, str]] = field(default_factory=set)
    #: collection -> ("own" | "hybrid" | "parent")
    tenant_collections: dict[str, str] = field(default_factory=dict)
    #: collection -> model identities bound to it
    collection_models: dict[str, set[tuple[str, str]]] = field(default_factory=lambda: defaultdict(set))
    fields_by_model: dict[tuple[str, str], set[str]] = field(default_factory=dict)
    duplicate_class_names: list[str] = field(default_factory=list)
    unplaceable_by_hand: list[str] = field(default_factory=list)


def _tenant_shape(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = fn.args
    positional = [*args.posonlyargs, *args.args]
    defaults = dict(
        zip([a.arg for a in positional][len(positional) - len(args.defaults) :], args.defaults, strict=True)
    )
    keyword_only = {a.arg: d for a, d in zip(args.kwonlyargs, args.kw_defaults, strict=True)}
    if "tenant_key" in keyword_only:
        return "strict" if keyword_only["tenant_key"] is None else "optional"
    if any(a.arg == "tenant_key" for a in positional):
        return "optional" if "tenant_key" in defaults else "positional"
    return "absent"


def _calls(fn: ast.AST) -> list[ast.Call]:
    return [node for node in ast.walk(fn) if isinstance(node, ast.Call)]


def _callee_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _is_self(node: ast.expr) -> bool:
    return isinstance(node, ast.Name) and node.id == "self"


def _is_super(node: ast.expr) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "super"


@cache
def _base_repository_writers(app_root: Path) -> frozenset[str]:
    """``BaseArangoRepository`` methods that write, derived from its own body.

    A method writes when it calls a python-arango mutator on a collection
    receiver, holds an AQL write statement, or calls another base method that
    writes. Derived so a new base writer joins by existing.
    """
    path = app_root / "data_access" / "arango" / "base_repository.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    base = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == bindings.BASE_REPOSITORY)
    methods = {n.name: n for n in base.body if isinstance(n, ast.FunctionDef)}
    direct = {name for name, fn in methods.items() if _writes_directly(fn, frozenset())}
    writers = set(direct)
    changed = True
    while changed:
        changed = False
        for name, fn in methods.items():
            if name in writers:
                continue
            if any(
                _callee_name(c) in writers and (_is_self(c.func.value) if isinstance(c.func, ast.Attribute) else False)
                for c in _calls(fn)
            ):
                writers.add(name)
                changed = True
    return frozenset(writers)


def _writes_directly(fn: ast.AST, repository_writers: frozenset[str]) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr, receiver = node.func.attr, node.func.value
            if attr in _COLLECTION_MUTATORS and re.search(r"\bcollection\b|\bcol\b|coll\b", ast.unparse(receiver)):
                return True
            if attr in repository_writers and (
                _is_self(receiver)
                or _is_super(receiver)
                or (isinstance(receiver, ast.Attribute) and _is_self(receiver.value))
            ):
                return True
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and _QUERY_WRITE.search(node.value):
            return True
        elif isinstance(node, ast.JoinedStr):
            literal = "FMT".join(
                part.value for part in node.values if isinstance(part, ast.Constant) and isinstance(part.value, str)
            )
            if _QUERY_WRITE.search(literal):
                return True
    return False


def _annotation_name(node: ast.expr | None) -> str | None:
    """``PlantingRunEntryKey`` / ``types.PlantingRunEntryKey`` -> the name; anything else -> ``None``."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _uses_arango(repo: object) -> bool:
    imports = repo.imports  # type: ignore[attr-defined]
    return any(module == "arango" or module.startswith("arango.") for module in imports.values())


def build_inventory(app_root: Path) -> Inventory:
    """Derive every public read method under ``app_root/data_access`` and its collections."""
    inventory = Inventory(app_root=app_root)
    constants = bindings.collection_constants(app_root)
    names = set(constants.values())
    classes = bindings.repository_classes(app_root, constants, include_plain=True)
    repositories = bindings.repository_classes(app_root, constants)
    fields = bindings.model_fields(app_root)
    inventory.fields_by_model = fields

    # Duplicate class names would make the name-keyed maps above lie.
    seen_names: dict[str, int] = defaultdict(int)
    for path in sorted((app_root / bindings.DATA_ACCESS_REL).rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ClassDef):
                seen_names[node.name] += 1
    inventoried = {n for n, r in classes.items() if n in repositories or _uses_arango(r)}
    inventory.duplicate_class_names = sorted(n for n, count in seen_names.items() if count > 1 and n in inventoried)

    # Model identity per binding, resolved through the repository's own imports.
    for repo in classes.values():
        pairs = []
        if repo.model and repo.collection:
            pairs.append((repo.model, repo.collection))
        for attribute, model in repo.attribute_models.items():
            pairs.append((model, repo.attributes[attribute]))
        for model, collection in pairs:
            module = repo.imports.get(model)
            if module is not None and (module, model) in fields:
                inventory.collection_models[collection].add((module, model))

    # Models the repositories write without a ``BaseArangoRepository[M]`` binding,
    # placed by the same declaration the privacy inventory reads (#1700).
    for model, collection in bindings.MODEL_COLLECTIONS_BY_HAND.items():
        defined = [ident for ident in fields if ident[1] == model]
        if len(defined) == 1:
            inventory.collection_models[collection].add(defined[0])
        else:
            inventory.unplaceable_by_hand.append(f"{model}: {len(defined)} definitions")

    for collection, models in inventory.collection_models.items():
        if any("tenant_key" in fields[m] for m in models):
            inventory.tenant_models |= {m for m in models if "tenant_key" in fields[m]}
            inventory.tenant_collections[collection] = "hybrid" if collection in HYBRID_CATALOGUES else "own"
    for collection in HYBRID_CATALOGUES:
        inventory.tenant_collections[collection] = "hybrid"
    for collection in PARENT_CHAINS:
        inventory.tenant_collections[collection] = "parent"

    repository_writers = _base_repository_writers(app_root)

    # Module-level helpers under ``data_access`` that a method may call by bare
    # name (``visible_fertilizer_labels(self._db, ...)``, the care repository's
    # AQL builders): their collections count for the caller. ``collections.py``
    # is the schema bootstrap, not a read path.
    helper_collections: dict[str, set[str]] = defaultdict(set)
    for path in sorted((app_root / bindings.DATA_ACCESS_REL).rglob("*.py")):
        if path.name == "collections.py":
            continue
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for inner in ast.walk(node):
                if isinstance(inner, ast.Attribute) and isinstance(inner.value, ast.Name):
                    if inner.value.id == "col" and inner.attr in constants:
                        helper_collections[node.name].add(constants[inner.attr])
                elif isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                    helper_collections[node.name].update(m for m in _LITERAL_LOOP.findall(inner.value) if m in names)

    for repo in sorted(classes.values(), key=lambda r: r.name):
        if repo.name not in repositories and not _uses_arango(repo):
            continue
        inventory.classes_seen += 1
        methods = {n.name: n for n in repo.node.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}

        def direct(fn: ast.AST, repo=repo, methods=methods) -> tuple[set[str], bool, set[str], set[str]]:
            collections: set[str] = set()
            self_calls: set[str] = set()
            callee_names: set[str] = set()
            for node in ast.walk(fn):
                if isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name) and node.value.id == "col" and node.attr in constants:
                        collections.add(constants[node.attr])
                    elif _is_self(node.value):
                        if node.attr in repo.attributes:
                            collections.add(repo.attributes[node.attr])
                        if node.attr in _OWN_COLLECTION_ACCESS and repo.collection:
                            collections.add(repo.collection)
                        if node.attr in methods:
                            self_calls.add(node.attr)
                    elif _is_super(node.value) and repo.collection:
                        collections.add(repo.collection)
                elif isinstance(node, ast.Name) and node.id in constants and node.id.isupper():
                    collections.add(constants[node.id])
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    collections.update(m for m in _LITERAL_LOOP.findall(node.value) if m in names)
                elif isinstance(node, ast.Call) and (name := _callee_name(node)) is not None:
                    callee_names.add(name)
                    if isinstance(node.func, ast.Name):
                        collections |= helper_collections.get(name, set())
            return collections, _writes_directly(fn, repository_writers), self_calls, callee_names

        facts = {name: direct(fn) for name, fn in methods.items()}

        def closure(name: str, seen: frozenset[str], facts=facts) -> tuple[set[str], bool, set[str]]:
            collections, writes, self_calls, callees = facts[name]
            collections, callees = set(collections), set(callees)
            for other in self_calls - seen:
                c2, w2, n2 = closure(other, seen | {other})
                collections |= c2
                writes = writes or w2
                callees |= n2
            return collections, writes, callees

        for name, fn in methods.items():
            if name.startswith("_"):
                continue
            collections, writes, callees = closure(name, frozenset({name}))
            if writes:
                continue
            args = fn.args
            inventory.reads.append(
                ReadMethod(
                    path=str(repo.path.relative_to(app_root)),
                    owner=repo.name,
                    name=name,
                    lineno=fn.lineno,
                    collections=frozenset(collections),
                    positional=tuple(a.arg for a in [*args.posonlyargs, *args.args][1:]),
                    annotations=tuple(_annotation_name(a.annotation) for a in [*args.posonlyargs, *args.args][1:]),
                    keyword_only=tuple(a.arg for a in args.kwonlyargs),
                    keyword_annotations=tuple(_annotation_name(a.annotation) for a in args.kwonlyargs),
                    tenant_shape=_tenant_shape(fn),
                    all_tenants_flag="all_tenants" in {a.arg for a in args.kwonlyargs},
                    enforces_tenant_scope=bool(callees & {"_enforce_tenant_scope", "_list_docs"})
                    or ("get_all" in callees and "all_tenants" in {a.arg for a in args.kwonlyargs}),
                    builds_union_predicate=bool(callees & PREDICATE_BUILDERS),
                )
            )
    return inventory


# ── The verdict ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Verdict:
    method: ReadMethod
    passed: bool
    category: str
    detail: str = ""

    def __str__(self) -> str:
        return f"{self.method.path}:{self.method.lineno} {self.method.qualname} [{self.category}] {self.detail}"


def _anchor(method: ReadMethod, inventory: Inventory) -> str | None:
    """The parameter that anchors *method* on a tenant-owned document, if any.

    Three ways, in order: ``key``/``keys`` is the document itself; a parameter
    that is the declared parent foreign key of a collection the method reads is
    the parent (reading a tank's logs by ``tank_key`` *is* reading the tank);
    otherwise the parameter's name or annotation must land, via
    :data:`ANCHOR_TARGETS`, on a strictly owned or parent-scoped collection.
    """
    strict_owned = {c for c, kind in inventory.tenant_collections.items() if kind in ("own", "parent")}
    declared_parents = {fk: parent for c in method.collections & set(PARENT_CHAINS) for fk, parent in PARENT_CHAINS[c]}
    touched = method.collections & set(inventory.tenant_collections)
    parameters = [
        *zip(method.positional, method.annotations, strict=True),
        *zip(method.keyword_only, method.keyword_annotations, strict=True),
    ]
    for parameter, annotation in parameters:
        if parameter == "key":
            return "key (the document itself)"
        if parameter == "keys" and touched <= strict_owned:
            # A batch dereference of catalogue rows is the #952 disclosure shape:
            # nobody verifies each of N documents after the fact, so on a hybrid
            # catalogue ``keys`` is not an anchor.
            return "keys (the documents themselves)"
        if parameter in declared_parents:
            return f"{parameter} -> {declared_parents[parameter]} (declared parent)"
        for name in (parameter, annotation):
            target = ANCHOR_TARGETS.get(name) if name is not None else None
            if target is not None and target in strict_owned:
                return f"{parameter}: {name} -> {target}"
    return None


def classify(method: ReadMethod, inventory: Inventory) -> Verdict | None:
    """``None`` for a read that touches no tenant-bearing collection."""
    touched = method.collections & set(inventory.tenant_collections)
    if not touched:
        return None
    reads = f"reads {sorted(touched)}"
    if method.tenant_shape == "strict":
        return Verdict(method, True, "strict")
    if method.tenant_shape == "positional":
        return Verdict(method, True, "positional", reads)
    if method.tenant_shape == "optional":
        if method.all_tenants_flag and method.enforces_tenant_scope:
            return Verdict(method, True, "runtime-enforced")
        only_catalogue = all(inventory.tenant_collections[c] == "hybrid" for c in touched)
        if only_catalogue and method.builds_union_predicate:
            return Verdict(method, True, "catalogue-union")
        return Verdict(method, False, "optional-tenant", f"{reads}; tenant_key has a default and nothing enforces it")
    anchor = _anchor(method, inventory)
    if anchor is not None:
        return Verdict(method, True, "anchored", anchor)
    return Verdict(method, False, "unscoped", f"{reads}; no tenant_key and no tenant-owned anchor")


@dataclass(frozen=True)
class Exclusion:
    """A finding this file accepts, with the decision and — where it can — the proof.

    ``kind`` decides what is checked, not only what is written:

    ``system``     a cross-tenant sweep (Celery task, migration, operator report).
                   **Checked:** no HTTP route and no MCP tool reaches it through the
                   typed call graph (:class:`TestTheExclusionsHoldTheirEvidence`).
    ``platform``   a platform-admin surface. **Checked:** at least one route reaches
                   it, every route that does is gated by ``require_platform_admin``
                   (decorator, parameter or router dependency), and no MCP tool does.
    ``verified``   a read whose result the caller authorises before using it.
                   **Checked:** ``witness`` (``module::qualname``) calls both
                   ``via`` (the read, or the service method that performs it) and
                   ``check`` (the authorisation). That proves the check exists on
                   the path named; it does not prove every path has one.
    ``catalogue``  global reference data written only by platform admins or seeds;
                   the reason names the write gate. Reason only.
    ``credential`` a lookup by a secret (a token or its hash); the secret is the
                   anchor. Reason only.
    ``account``    scoped by the calling account's ``user_key`` — every row belongs
                   to that account, across the tenants it is a member of. Reason only.
    ``probe``      a boolean existence check whose answer never leaves the service.
                   Reason only.
    """

    kind: str
    reason: str
    witness: str | None = None
    via: str | None = None
    check: str | None = None


_CATALOGUE_WRITTEN_BY_ADMINS = (
    "every write path is platform-admin only (require_platform_admin on the write routes) or a seed, "
    "and none stamps a tenant — every stored row is global catalogue data"
)

#: ``(class, method) -> Exclusion``. Each entry was measured on 2026-09-24; an
#: entry that no longer matches a finding fails (:class:`TestTheExclusionsAreLive`).
EXCLUSIONS: dict[tuple[str, str], Exclusion] = {
    # ── catalogue ──────────────────────────────────────────────────────────
    ("ArangoActivityRepository", "get_all"): Exclusion("catalogue", f"activities: {_CATALOGUE_WRITTEN_BY_ADMINS}"),
    ("ArangoActivityRepository", "get_by_name"): Exclusion("catalogue", f"activities: {_CATALOGUE_WRITTEN_BY_ADMINS}"),
    ("ArangoActivityRepository", "get_system_activities"): Exclusion(
        "catalogue", f"activities: {_CATALOGUE_WRITTEN_BY_ADMINS}"
    ),
    ("ArangoActivityRepository", "get_by_category"): Exclusion(
        "catalogue", f"activities: {_CATALOGUE_WRITTEN_BY_ADMINS}"
    ),
    ("ArangoGraphRepository", "get_compatible_species"): Exclusion(
        "catalogue",
        "companion edges are written only by platform admins (PUT /companion-planting/...), and the "
        "routes resolve the anchor species tenant-aware first (SEC-005, #808)",
    ),
    ("ArangoGraphRepository", "get_incompatible_species"): Exclusion(
        "catalogue",
        "companion edges are written only by platform admins (PUT /companion-planting/...), and the "
        "routes resolve the anchor species tenant-aware first (SEC-005, #808)",
    ),
    ("ArangoLifecycleRepository", "get_lifecycle_by_species"): Exclusion(
        "catalogue", f"lifecycle configs: {_CATALOGUE_WRITTEN_BY_ADMINS}; the species key only selects one"
    ),
    ("ArangoPhaseSequenceRepository", "get_sequence_by_species"): Exclusion(
        "catalogue",
        "phase sequences are written only by platform admins (require_platform_admin_for_global_catalogue, "
        "#1501) or seeds; the species key only selects one",
    ),
    ("ArangoPestImageRepository", "list_promoted_for_pest"): Exclusion(
        "catalogue",
        "a PROMOTED contribution is one a platform admin moved into the shared reference set; "
        "PestImageService.list_for_pest unions it with the caller's own and marks foreign ones",
    ),
    # ── credential ─────────────────────────────────────────────────────────
    ("ArangoCalendarFeedRepository", "get_by_token"): Exclusion(
        "credential", "the iCal feed token is the credential of the unauthenticated feed URL (REQ-015)"
    ),
    ("ArangoInvitationRepository", "get_by_token_hash"): Exclusion(
        "credential", "the hashed invitation token is what the invitee presents; it names one invitation"
    ),
    # ── account ────────────────────────────────────────────────────────────
    ("ArangoMembershipRepository", "list_by_user"): Exclusion(
        "account", "a user's memberships span their tenants by definition; the key is the caller's own"
    ),
    ("ArangoMembershipRepository", "list_by_user_with_tenant"): Exclusion(
        "account", "a user's memberships span their tenants by definition; the key is the caller's own"
    ),
    ("ArangoNotificationRepository", "list_for_user"): Exclusion(
        "account",
        "filters on the recipient's user_key; tenant_key only narrows within that account's own "
        "notifications, so an omitted tenant widens nothing beyond the caller's rows",
    ),
    ("ArangoNotificationRepository", "count_unread"): Exclusion(
        "account", "same shape as list_for_user: recipient user_key first, tenant narrows within it"
    ),
    ("ArangoNotificationRepository", "list_for_user_since"): Exclusion(
        "account", "the e-mail digest of one recipient, across the tenants that recipient belongs to"
    ),
    ("ArangoPestImageRepository", "list_for_user"): Exclusion(
        "account", "the contributions one account made — read for its own DSGVO export and erasure"
    ),
    ("ArangoMcpAuditRepository", "list_for_service_account"): Exclusion(
        "account", "the MCP audit trail of one service account, read by that account (REQ-033 §4.6)"
    ),
    ("ArangoMcpAuditRepository", "list_for_user_accounts"): Exclusion(
        "account", "the MCP audit trail across the service accounts one user owns (REQ-033 §4.6)"
    ),
    # ── probe ──────────────────────────────────────────────────────────────
    ("ArangoHarvestRepository", "batch_id_exists"): Exclusion(
        "probe",
        "the batch_id unique index is global, so the id generator must ask globally; the boolean "
        "only steers HarvestService._generate_batch_id and is never returned",
    ),
    # ── verified ───────────────────────────────────────────────────────────
    ("ArangoSpeciesRepository", "list_grants"): Exclusion(
        "verified",
        "owner-only: the grant list is read after the species write authorisation (#1092)",
        witness="app.domain.services.species_service::SpeciesService.list_species_grants",
        via="list_grants",
        check="_authorize_species_write",
    ),
    ("ArangoSpeciesRepository", "list_cultivar_grants"): Exclusion(
        "verified",
        "owner-only: the grant list is read after the cultivar write authorisation (#1092)",
        witness="app.domain.services.species_service::SpeciesService.list_cultivar_grants",
        via="list_cultivar_grants",
        check="_authorize_cultivar_write",
    ),
    ("ArangoSpeciesRepository", "get_by_scientific_name"): Exclusion(
        "verified",
        "the CSV import's update strategy authorises every matched row before writing it (#1110); "
        "the other callers are seeders",
        witness="app.domain.services.import_service::ImportService._get_update_fn.<locals>.update_species",
        via="get_by_scientific_name",
        check="_authorize_tenant_owned_write",
    ),
    ("ArangoTaskRepository", "get_task_templates_for_workflow"): Exclusion(
        "verified",
        "task templates are read by their workflow template, whose hybrid read access the route "
        "checks first; the service-internal callers act on a template they already resolved",
        witness="app.api.v1.tasks.tenant_router::list_task_templates",
        via="get_task_templates",
        check="get_workflow_template",
    ),
    # ── system ─────────────────────────────────────────────────────────────
    ("ArangoAttachmentRepository", "find_orphaned_task_photos"): Exclusion(
        "system", "the orphaned task-photo sweep of the storage Celery task (#1393)"
    ),
    ("ArangoCareReminderRepository", "get_all_profiles"): Exclusion(
        "system", "the care-reminder Celery task walks every profile to generate due tasks"
    ),
    ("ArangoNotificationRepository", "find_overdue_watering"): Exclusion(
        "system", "the escalation Celery task re-notifies every overdue watering reminder"
    ),
    ("ArangoPlantingRunRepository", "get_active_runs_with_schedule"): Exclusion(
        "system", "the watering-task generator iterates every run with an active schedule"
    ),
    ("ArangoPlantingRunRepository", "get_plant_keys_with_active_schedule"): Exclusion(
        "system", "the watering-task generator skips plants already covered by a run schedule"
    ),
    ("ArangoSiteRepository", "find_site_docs_by_types"): Exclusion(
        "system", "the daily season and irrigation tasks evaluate every outdoor site (REQ-047 AC-18)"
    ),
    ("ArangoSiteRepository", "find_site_keys_with_frost_exposed_location"): Exclusion(
        "system", "the daily season task adds sites with a frost-exposed location to its batch"
    ),
    ("ArangoSpeciesRepository", "get_by_normalized_scientific_name"): Exclusion(
        "system", "the unscoped dedup lookup kept for migrations and reports (#1162); no route calls it"
    ),
    ("ArangoSpeciesRepository", "list_all_species"): Exclusion(
        "system", "backs the operator shadow-pair report (#975), a cross-comparison of every record"
    ),
    ("ArangoTankRepository", "get_active_auto_create_schedules"): Exclusion(
        "system", "the maintenance Celery task creates tasks from every auto-create schedule"
    ),
    # ── platform ───────────────────────────────────────────────────────────
    ("ArangoPestImageRepository", "list_all_for_pest"): Exclusion(
        "platform", "platform-admin moderation of every tenant's contributions (REQ-044)"
    ),
    ("ArangoMembershipRepository", "count"): Exclusion(
        "platform", "installation-wide membership count for the platform statistics"
    ),
    ("ArangoExternalMappingRepository", "find_unmapped_species"): Exclusion(
        "platform",
        "REQ-011 enrichment sweep, run by the Celery schedule or a platform admin's sync trigger; its "
        "result becomes mappings, never a response",
    ),
}

_EXCLUSION_KINDS = frozenset({"system", "platform", "verified", "catalogue", "credential", "account", "probe"})


@cache
def _real_inventory() -> Inventory:
    return build_inventory(_APP)


def _verdicts(inventory: Inventory) -> list[Verdict]:
    return [v for m in inventory.reads if (v := classify(m, inventory)) is not None]


def findings(inventory: Inventory, exclusions: dict[tuple[str, str], Exclusion]) -> list[Verdict]:
    return [v for v in _verdicts(inventory) if not v.passed and (v.method.owner, v.method.name) not in exclusions]


# ── Tests ────────────────────────────────────────────────────────────────────


class TestTheInventoryIsNotVacuous:
    """A derivation over an empty or collapsed tree is green and proves nothing."""

    def test_the_counts_clear_their_floors(self, capsys: pytest.CaptureFixture[str]) -> None:
        inventory = _real_inventory()
        verdicts = _verdicts(inventory)
        by_category: dict[str, int] = defaultdict(int)
        for verdict in verdicts:
            by_category[verdict.category] += 1
        with capsys.disabled():
            print(
                f"\n[#1708] classes={inventory.classes_seen} reads={len(inventory.reads)} "
                f"subject={len(verdicts)} " + " ".join(f"{k}={v}" for k, v in sorted(by_category.items()))
            )
        assert inventory.classes_seen >= MIN_REPOSITORY_CLASSES
        assert len(inventory.reads) >= MIN_READ_METHODS
        assert len(verdicts) >= MIN_SUBJECT_READS

    def test_no_class_name_is_ambiguous(self) -> None:
        """The binding maps are keyed by class name; a duplicate would merge two classes."""
        assert _real_inventory().duplicate_class_names == []


class TestTheReaderAgreesWithTheRuntime:
    """The AST reader decides; the imported models are the independent check on it."""

    def test_tenant_models_match_model_fields(self) -> None:
        import importlib

        inventory = _real_inventory()
        disagreements = []
        for models in inventory.collection_models.values():
            for module, name in models:
                runtime = importlib.import_module(module).__dict__[name]
                derived = "tenant_key" in inventory.fields_by_model[(module, name)]
                if derived != ("tenant_key" in runtime.model_fields):
                    disagreements.append(f"{module}.{name}: AST says {derived}")
        assert disagreements == []

    def test_the_reader_sees_the_spellings_it_was_extended_for(self) -> None:
        """Two binding spellings the first version of the shared reader missed (#1708).

        ``PropagationRepository`` binds its sibling collections with an
        unsubscripted ``BaseArangoRepository(db, col.X, Model)`` — the model is only
        the third argument — and ``ArangoPhaseSequenceRepository`` calls
        ``BaseArangoRepository.__init__(self, db, col.X)`` instead of ``super()``.
        """
        inventory = _real_inventory()
        assert {col.PROPAGATION_BATCHES, col.PHENOTYPE_NOTES, col.ROOTING_PROTOCOLS} <= set(inventory.collection_models)
        constants = bindings.collection_constants(_APP)
        classes = bindings.repository_classes(_APP, constants)
        assert classes["ArangoPhaseSequenceRepository"].collection == col.PHASE_DEFINITIONS

    def test_every_hand_placed_model_names_a_declared_collection(self) -> None:
        constants = bindings.collection_constants(_APP)
        unknown = {m: c for m, c in bindings.MODEL_COLLECTIONS_BY_HAND.items() if c not in constants.values()}
        assert unknown == {}
        assert _real_inventory().unplaceable_by_hand == []

    def test_every_bound_collection_is_placed(self) -> None:
        """A repository binding whose model the reader cannot find is a silent hole."""
        inventory = _real_inventory()
        constants = bindings.collection_constants(_APP)
        placed = set(inventory.collection_models)
        bound = set().union(*bindings.repository_bindings(_APP, constants).values())
        assert bound - placed == set()


class TestTheParentChainsAreDeclaredOnceAndComplete:
    def test_every_declared_chain_names_a_real_field_and_a_tenant_parent(self) -> None:
        inventory = _real_inventory()
        problems = []
        for collection, chains in PARENT_CHAINS.items():
            models = inventory.collection_models.get(collection, set())
            if not models:
                problems.append(f"{collection}: no repository binds a model to it")
            for fk, parent in chains:
                for model in models:
                    if fk not in inventory.fields_by_model[model]:
                        problems.append(f"{collection}: {model[1]} has no field {fk!r}")
                if parent not in inventory.tenant_collections:
                    problems.append(f"{collection}: parent {parent} carries no tenant")
        assert problems == []

    def test_every_child_of_a_tenant_collection_is_declared(self) -> None:
        """The completeness half: derived from the models, not from this file."""
        inventory = _real_inventory()
        strict_owned = {c for c, kind in inventory.tenant_collections.items() if kind in ("own", "parent")}
        problems = []
        for collection, models in sorted(inventory.collection_models.items()):
            if collection in PARENT_CHAINS or collection in ACCOUNT_SCOPED_COLLECTIONS:
                continue
            for model in sorted(models):
                fields = inventory.fields_by_model[model]
                if "tenant_key" in fields:
                    continue
                for name in sorted(f for f in fields if f.endswith(("_key", "_keys")) and f != "tenant_key"):
                    if name not in ANCHOR_TARGETS:
                        problems.append(f"{collection}: {model[1]}.{name} names no known target")
                    elif ANCHOR_TARGETS[name] in strict_owned:
                        problems.append(
                            f"{collection}: {model[1]}.{name} -> {ANCHOR_TARGETS[name]} carries a tenant; "
                            "declare the chain in PARENT_CHAINS"
                        )
        assert problems == [], (
            "A non-tenant model references a tenant-bearing collection without a declared parent "
            "chain (or names a key this file cannot resolve):\n  " + "\n  ".join(problems)
        )


class TestTheRuleFires:
    """Red first, on a copy of the real tree with one tenant-less read planted."""

    #: The shape #1704 shipped: a date-window read with no tenant at all.
    _PLANTED = (
        "\n    def list_between(self, start: str, end: str) -> list[WateringLog]:\n"
        '        query = f"FOR w IN {col.WATERING_LOGS} FILTER w.logged_at >= @start RETURN w"\n'
        "        cursor = self._db.aql.execute(query, bind_vars={'start': start})\n"
        "        return [WateringLog(**self._from_doc(d)) for d in cursor]\n"
    )

    def _copy(self, tmp_path: Path) -> Path:
        root = tmp_path / "app"
        shutil.copytree(_APP, root, ignore=shutil.ignore_patterns("__pycache__"))
        return root

    def test_a_tenant_less_watering_log_read_is_a_finding(self, tmp_path: Path) -> None:
        root = self._copy(tmp_path)
        baseline = {str(v) for v in findings(build_inventory(root), EXCLUSIONS)}
        target = root / "data_access" / "arango" / "watering_log_repository.py"
        target.write_text(target.read_text(encoding="utf-8") + self._PLANTED, encoding="utf-8")
        after = findings(build_inventory(root), EXCLUSIONS)
        new = [v for v in after if str(v) not in baseline]
        assert [v.method.qualname for v in new] == ["ArangoWateringLogRepository.list_between"]
        assert new[0].category == "unscoped"

    def test_a_calendar_read_that_drops_its_tenant_is_a_finding(self, tmp_path: Path) -> None:
        """#1704's five methods are caught by derivation, not by enrolment."""
        root = self._copy(tmp_path)
        target = root / "data_access" / "arango" / "calendar_source_repository.py"
        source = target.read_text(encoding="utf-8")
        planted = source.replace(
            "def list_watering_logs(self, start: str, end: str, *, tenant_key: str)",
            "def list_watering_logs(self, start: str, end: str, tenant_key: str | None = None)",
        )
        assert planted != source, "the #1704 signature moved; re-aim this falsification"
        target.write_text(planted, encoding="utf-8")
        hits = [v for v in findings(build_inventory(root), EXCLUSIONS) if v.method.name == "list_watering_logs"]
        assert [v.category for v in hits] == ["optional-tenant"]

    def test_a_parent_scoped_read_is_subject_through_its_parent(self, tmp_path: Path) -> None:
        """``maintenance_logs`` has no tenant field; its tank does."""
        root = self._copy(tmp_path)
        target = root / "data_access" / "arango" / "tank_repository.py"
        target.write_text(
            target.read_text(encoding="utf-8")
            + "\n    def all_logs(self) -> list[MaintenanceLog]:\n"
            + "        return self._logs.find_by_field('kind', 'x')\n",
            encoding="utf-8",
        )
        hits = [v for v in findings(build_inventory(root), EXCLUSIONS) if v.method.name == "all_logs"]
        assert [(v.category, v.method.collections) for v in hits] == [("unscoped", frozenset({col.MAINTENANCE_LOGS}))]

    def test_a_hybrid_catalogue_key_does_not_anchor(self) -> None:
        inventory = _real_inventory()
        method = ReadMethod(
            path="x.py",
            owner="X",
            name="by_species",
            lineno=1,
            collections=frozenset({col.PLANT_INSTANCES}),
            positional=("species_key",),
            annotations=("SpeciesKey",),
            keyword_only=(),
            keyword_annotations=(),
            tenant_shape="absent",
            all_tenants_flag=False,
            enforces_tenant_scope=False,
            builds_union_predicate=False,
        )
        verdict = classify(method, inventory)
        assert verdict is not None and verdict.category == "unscoped"


class TestTheApplicationIsClean:
    def test_every_tenant_bearing_read_is_scoped_anchored_or_excluded(self) -> None:
        offenders = findings(_real_inventory(), EXCLUSIONS)
        assert offenders == [], (
            "Repository reads over a tenant-bearing collection that take no enforceable tenant "
            "(#1704/#1708). Take tenant_key keyword-only without a default, anchor the read on a "
            "tenant-owned document key, or add it to EXCLUSIONS with a kind and a reason:\n  "
            + "\n  ".join(str(v) for v in offenders)
        )

    def test_the_positional_count_does_not_grow(self) -> None:
        positional = [v for v in _verdicts(_real_inventory()) if v.category == "positional"]
        assert len(positional) == POSITIONAL_TENANT_COUNT, (
            "The number of reads taking tenant_key positionally changed. A new read must take it "
            "keyword-only; a conversion lowers POSITIONAL_TENANT_COUNT in the same change.\n  "
            + "\n  ".join(str(v) for v in positional)
        )


class TestTheExclusionsAreLive:
    def test_every_exclusion_names_a_current_finding(self) -> None:
        inventory = _real_inventory()
        failing = {(v.method.owner, v.method.name) for v in _verdicts(inventory) if not v.passed}
        stale = sorted(set(EXCLUSIONS) - failing)
        assert stale == [], f"exclusions that no longer excuse anything: {stale}"

    def test_every_exclusion_has_a_known_kind_and_a_reason(self) -> None:
        bad = [k for k, e in EXCLUSIONS.items() if e.kind not in _EXCLUSION_KINDS or len(e.reason) < 40]
        assert bad == []

    def test_only_verified_exclusions_carry_a_witness(self) -> None:
        shapes = {
            k: (e.kind == "verified", all((e.witness, e.via, e.check)), any((e.witness, e.via, e.check)))
            for k, e in EXCLUSIONS.items()
        }
        wrong = [
            k for k, (verified, complete, partial) in shapes.items() if verified != complete or complete != partial
        ]
        assert wrong == []


def _callers(graph) -> dict[str, list[str]]:
    callers: dict[str, list[str]] = defaultdict(list)
    for fn in graph.functions:
        for callee in fn.callees:
            if (fn.id, callee.id) not in graph.fallback_edges:
                callers[callee.id].append(fn.id)
    return callers


def _reachers(owner: str, method: str) -> tuple[set[str], set[str]]:
    """``(every function reaching owner.method, the roots among them)`` over the typed call graph.

    A root has no caller in the graph: a route handler, a Celery task, a
    migration step. Name-fallback edges are left out — they are guesses.
    """
    graph = call_graph()
    callers = _callers(graph)
    start = [fn.id for fn in graph.functions if fn.owner == owner and fn.name == method]
    assert start, f"{owner}.{method} is not in the call graph — the evidence check would pass on nothing"
    seen, queue = set(start), deque(start)
    while queue:
        current = queue.popleft()
        for caller in callers.get(current, ()):
            if caller not in seen:
                seen.add(caller)
                queue.append(caller)
    roots = {fn for fn in seen if not callers.get(fn)}
    return seen, roots


_REQUEST_MODULES = ("app.api.", "app.mcp_server.")


def _request_entry_points(owner: str, method: str) -> set[str]:
    """Every function under ``app.api`` / ``app.mcp_server`` that reaches ``owner.method``."""
    reaching, _roots = _reachers(owner, method)
    return {fn for fn in reaching if fn.startswith(_REQUEST_MODULES)}


def _names(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)
    }


def _is_platform_admin_route(function_id: str) -> bool:
    """Whether a route handler is gated by ``require_platform_admin`` — read off the AST.

    Three places a FastAPI gate can sit: the route decorator's
    ``dependencies=[...]``, a parameter's ``Depends(...)``, or the module
    router's ``APIRouter(dependencies=[...])``. Nothing else counts, and a
    comment naming the gate cannot create any of these nodes (#1456).
    """
    module, qualname = function_id.split("::", 1)
    path = _APP.parent / (module.replace(".", "/") + ".py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    function = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef) and n.name == qualname), None
    )
    if function is None:
        return False
    gate = "require_platform_admin"
    if any(gate in _names(decorator) for decorator in function.decorator_list):
        return True
    if any(gate in _names(default) for default in [*function.args.defaults, *function.args.kw_defaults] if default):
        return True
    return any(
        isinstance(stmt, ast.Assign)
        and isinstance(stmt.value, ast.Call)
        and _callee_name(stmt.value) == "APIRouter"
        and gate in _names(stmt.value)
        for stmt in tree.body
    )


class TestTheExclusionsHoldTheirEvidence:
    """The kinds that can be checked are checked; the rest carry a reason only."""

    @pytest.mark.parametrize(
        "owner,method", sorted(k for k, e in EXCLUSIONS.items() if e.kind == "system"), ids=lambda v: str(v)
    )
    def test_a_system_read_is_not_reachable_from_a_request(self, owner: str, method: str) -> None:
        assert _request_entry_points(owner, method) == set()

    @pytest.mark.parametrize(
        "owner,method", sorted(k for k, e in EXCLUSIONS.items() if e.kind == "platform"), ids=lambda v: str(v)
    )
    def test_a_platform_read_is_reached_from_admin_routes_only(self, owner: str, method: str) -> None:
        _reaching, roots = _reachers(owner, method)
        request_roots = {r for r in roots if r.startswith(_REQUEST_MODULES)}
        ungated = {r for r in request_roots if r.startswith("app.mcp_server.") or not _is_platform_admin_route(r)}
        assert request_roots, f"{owner}.{method}: no route reaches it — it is a system read, not a platform one"
        assert ungated == set(), f"reached from a route without require_platform_admin: {sorted(ungated)}"

    @pytest.mark.parametrize(
        "owner,method", sorted(k for k, e in EXCLUSIONS.items() if e.kind == "verified"), ids=lambda v: str(v)
    )
    def test_a_verified_read_has_a_witness_that_checks_before_it_reads(self, owner: str, method: str) -> None:
        exclusion = EXCLUSIONS[(owner, method)]
        witness = call_graph().by_id.get(exclusion.witness or "")
        assert witness is not None, f"witness {exclusion.witness} does not exist"
        called = {_callee_name(call) for call in witness._call_nodes}
        assert exclusion.via in called, f"{exclusion.witness} no longer calls {exclusion.via}"
        assert exclusion.check in called, f"{exclusion.witness} no longer calls {exclusion.check}"

    def test_the_reachability_check_can_see_a_route(self) -> None:
        """Falsification: a read a tenant route certainly reaches is reported as reachable."""
        entries = _request_entry_points("ArangoWateringLogRepository", "get_by_slot")
        assert any(e.startswith("app.api.v1.watering_logs.") for e in entries), entries

    def test_the_gate_check_tells_a_gated_route_from_an_open_one(self) -> None:
        """Falsification of the platform check, on both sides of the line."""
        assert _is_platform_admin_route("app.api.v1.enrichment.router::trigger_sync")
        assert _is_platform_admin_route("app.api.v1.admin.pests.router::list_pest_contributions")
        assert not _is_platform_admin_route("app.api.v1.watering_logs.tenant_router::get_slot_logs")


class TestInterfacesStayAsStrictAsTheirImplementations:
    """Replaces the hand list in ``TestTheSurfacesStayStrict`` (#1533, #1704).

    A service typed against ``ITaskRepository`` reads the interface signature. If
    the interface regains a default, a call that omits the tenant type-checks — so
    every interface method an implementation overrides strictly must be strict too.
    """

    def test_interface_signatures_match_strict_implementations(self) -> None:
        import importlib

        inventory = _real_inventory()
        drifted = []
        checked = 0
        for verdict in _verdicts(inventory):
            if verdict.category != "strict":
                continue
            method = verdict.method
            module = "app." + method.path.removesuffix(".py").replace("/", ".")
            owner = importlib.import_module(module).__dict__[method.owner]
            for base in owner.__mro__[1:]:
                if not base.__module__.startswith("app.domain.interfaces") or method.name not in base.__dict__:
                    continue
                checked += 1
                parameter = inspect.signature(base.__dict__[method.name]).parameters.get("tenant_key")
                if (
                    parameter is None
                    or parameter.kind is not inspect.Parameter.KEYWORD_ONLY
                    or parameter.default is not inspect.Parameter.empty
                ):
                    drifted.append(f"{base.__name__}.{method.name}")
        assert drifted == []
        assert checked >= 10, f"only {checked} interface methods compared — the walk lost its subjects"
