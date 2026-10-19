"""#2107 (MT-010) — a service method that loads by key and writes takes the tenant itself.

The audit's OWN-04: the ownership check of a write lived in the **router**.
``service.get_X(key, tenant_key=ctx.tenant_key)`` came first, then an unscoped
``service.update_X(key, …)`` that reloaded the row without a tenant. Correct as
long as every handler and every MCP tool remembered the first call — the #948 /
#1402 sibling-drift class, where two of four routes of one form were repaired and
the other two stayed open for months. ``tenant_key: str = ""`` made it worse: an
empty tenant switched every ``if tenant_key:`` check off.

**The rule.** Every public method of a class under ``app/domain/services`` that

* reaches a persistence write (the typed call graph of
  ``tests/unit/api/_write_call_graph.py``), and
* loads a document by key — a call to ``get_or_raise`` / ``get_by_key`` /
  ``get_<x>_by_key`` / ``get_<x>_or_raise`` on a repository, in the method or in a
  same-class helper it calls —

takes its tenant so that it cannot be omitted: ``tenant_key`` keyword-only
**without** a default, or a required ``TenantContext`` parameter (the verified
request context, as ``AiAssistantService`` takes it). A positional ``tenant_key``
counts as not converted: it cannot be omitted, but it can be transposed with the
neighbouring ``str`` key.

**Not every keyed write is tenant data.** :data:`_NOT_TENANT_DATA` names the
service classes whose keys address something else, each with the reason.

**Converted per slice, the rest pinned.** #2107 is converted service by service
(site → plan → …). :data:`_REMAINING` is the measured list of methods not yet
converted; it may only shrink. A new method must be strict, a converted one must
leave the list (a stale entry fails), so a finished slice cannot regress.

**What the selector does not see**, named rather than discovered later: a write
reached only through dynamic dispatch or a Celery task (the call graph's own
blind spots), a load through a repository method not named ``get…by_key`` /
``get…or_raise`` (``find_…``, an AQL read), and module-level functions.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from tests.support.execution_guards import find_project_root
from tests.unit.api._write_call_graph import call_graph

_APP = find_project_root(Path(__file__)) / "app"
_SERVICES = _APP / "domain" / "services"

#: ``get_or_raise``, ``get_by_key``, ``get_site_by_key``, ``get_workflow_template_or_raise`` …
_KEYED_LOAD = re.compile(r"get(?:_\w+)?_(?:by_key|or_raise)|get_or_raise|get_by_key")

_ACCOUNT = "keys address the caller's own account rows (sessions, keys, consents, providers); ownership is the user key"
_NOT_TENANT_DATA: dict[str, str] = {
    "AuthService": _ACCOUNT,
    "UserService": _ACCOUNT,
    "PrivacyService": _ACCOUNT + "; DSGVO self-service (REQ-025)",
    "OidcProviderAdminService": "platform OIDC provider configuration, require_platform_admin on every route",
    "TenantService": (
        "keys address tenants, memberships and invitations themselves; authorised by membership role, "
        "step-up and the platform-admin gate (REQ-024/REQ-049), not by a tenant predicate"
    ),
    "ModeSwitchService": (
        "keys address the light-mode system account and the installation's system_meta bookkeeping (REQ-027 §7a, "
        "#1855); the start runs without a request, the take-over is authorised as platform admin or first account"
    ),
    "ActivityService": "global activity catalogue, written only behind require_platform_admin (#2119 owns tenant rows)",
    "LocationTypeService": "global location-type catalogue, written only behind require_platform_admin",
    "TenantExportService": (
        "keys address tenants and their export/import requests; authorised from the stored membership "
        "(lead + management) or the platform-admin membership plus the requester's step-up (REQ-056 §8.2, #2138), "
        "and every export row is read through the tenant-erasure predicate of that tenant"
    ),
    "CompanionEdgeService": (
        "global companion edges (REQ-028), written only behind require_platform_admin and only between global "
        "species (MT-054, #2144) — the keyed load is the global-species check itself"
    ),
    "PhaseSequenceService": (
        "global-only catalogue: PhaseDefinition, PhaseSequence and PhaseSequenceEntry carry no tenant_key "
        "(app/domain/models/phase_sequence.py); every write takes is_platform_admin keyword-only without a "
        "default and refuses a non-admin in the service (#1501)"
    ),
}

#: Single methods of an otherwise tenant-bearing class whose keys address global data — the
#: method-level twin of :data:`_NOT_TENANT_DATA`, for a class that mixes both. Each entry names
#: why no tenant can own the row it writes; a stale entry (no longer a keyed write) fails.
_GLOBAL_LIFECYCLE = (
    "LifecycleConfig and GrowthPhase carry no tenant_key (app/domain/models/lifecycle.py); the routes are "
    "mounted behind require_platform_admin (lifecycle_configs/router.py, growth_phases/router.py, "
    "profiles/router.py)"
)
_GLOBAL_METHODS: dict[str, str] = {
    "PhaseService.update_lifecycle": _GLOBAL_LIFECYCLE,
    "PhaseService.update_phase": _GLOBAL_LIFECYCLE,
    "PhaseService.delete_phase": _GLOBAL_LIFECYCLE,
    "PhaseService.generate_default_profiles": _GLOBAL_LIFECYCLE + "; the profiles hang off a global GrowthPhase",
    "PhaseService.assign_phase_sequence": (
        _GLOBAL_LIFECYCLE + "; the MCP tool admits only a global species and the dispatcher refuses a global "
        "write to anyone but a platform admin (mcp_server/dispatcher.py, #2103)"
    ),
}


@dataclass(frozen=True)
class KeyedWrite:
    owner: str
    name: str
    shape: str
    #: ``is_platform_admin`` keyword-only without a default — the decision a global-catalogue write takes instead.
    admin_gated: bool = False

    @property
    def qualname(self) -> str:
        return f"{self.owner}.{self.name}"


def _shape(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """``strict`` when the tenant cannot be omitted nor transposed, else the shape it has."""
    args = fn.args
    keyword_defaults = dict(zip((a.arg for a in args.kwonlyargs), args.kw_defaults, strict=True))
    if "tenant_key" in keyword_defaults:
        return "strict" if keyword_defaults["tenant_key"] is None else "keyword-with-default"
    positional = [*args.posonlyargs, *args.args]
    for index, arg in enumerate(positional):
        annotation = ast.unparse(arg.annotation) if arg.annotation is not None else ""
        has_default = index >= len(positional) - len(args.defaults)
        if annotation.endswith("TenantContext") and not has_default:
            return "strict"
        if arg.arg == "tenant_key":
            return "positional-with-default" if has_default else "positional"
    for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        if ast.unparse(arg.annotation or ast.Constant(None)).endswith("TenantContext") and default is None:
            return "strict"
    return "none"


def _takes_platform_admin_strictly(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """``is_platform_admin`` keyword-only without a default, and not also positional."""
    args = fn.args
    if "is_platform_admin" in {a.arg for a in [*args.posonlyargs, *args.args]}:
        return False
    return any(
        arg.arg == "is_platform_admin" and default is None
        for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True)
    )


def _loads_by_key(fn: ast.AST, methods: dict[str, ast.AST], seen: frozenset[str]) -> bool:
    for node in ast.walk(fn):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        receiver = node.func.value
        is_self = isinstance(receiver, ast.Name) and receiver.id == "self"
        if not is_self and _KEYED_LOAD.fullmatch(node.func.attr):
            return True
        helper = node.func.attr
        if (
            is_self
            and helper in methods
            and helper not in seen
            and _loads_by_key(methods[helper], methods, seen | {helper})
        ):
            return True
    return False


def keyed_writes(root: Path, writers: set[str]) -> list[KeyedWrite]:
    """Every public service method that loads by key and reaches a write, with its tenant shape."""
    found: list[KeyedWrite] = []
    for path in sorted((root / "domain" / "services").rglob("*.py")):
        module = "app." + ".".join(path.relative_to(root).with_suffix("").parts)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for klass in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            methods = {n.name: n for n in klass.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}
            for name, fn in methods.items():
                if name.startswith("_") or f"{module}::{klass.name}.{name}" not in writers:
                    continue
                if _loads_by_key(fn, methods, frozenset({name})):
                    found.append(KeyedWrite(klass.name, name, _shape(fn), _takes_platform_admin_strictly(fn)))
    return found


@cache
def _inventory() -> tuple[KeyedWrite, ...]:
    return tuple(keyed_writes(_APP, call_graph().writers()))


def _excused(write: KeyedWrite) -> bool:
    """Excused by class, by method, or as a global-catalogue write that takes the admin decision."""
    return (
        write.owner in _NOT_TENANT_DATA
        or write.qualname in _GLOBAL_METHODS
        or write.qualname in _NOT_TENANT_ADDRESSED
        or (write.qualname in _GLOBAL_CATALOGUE_WRITES and write.admin_gated)
    )


def _not_strict() -> set[str]:
    return {w.qualname for w in _inventory() if w.shape != "strict" and not _excused(w)}


# ── Single methods excused (#2107, IPM/task/plant slice) ────────────────────────────────────────────
#
# :data:`_NOT_TENANT_DATA` excuses whole classes. The classes below also hold tenant writes, which stay
# under the rule, so only the named method is excused — each with the reason, measured at file:line.

_IPM_CATALOGUE = (
    "global IPM catalogue (Pest/Disease/Treatment carry no tenant_key, app/domain/models/ipm.py); the service "
    "refuses anyone but a platform admin (IpmService._require_catalogue_admin, #1501)"
)

#: Writes to a global catalogue with no tenant: the decision is the platform-admin gate, which the method
#: must take as ``is_platform_admin`` keyword-only without a default — checked, not trusted
#: (:func:`test_every_global_catalogue_write_takes_the_admin_decision`).
_GLOBAL_CATALOGUE_WRITES: dict[str, str] = {
    "IpmService.update_pest": _IPM_CATALOGUE,
    "IpmService.delete_pest": _IPM_CATALOGUE,
    "IpmService.update_disease": _IPM_CATALOGUE,
    "IpmService.delete_disease": _IPM_CATALOGUE,
    "IpmService.update_treatment": _IPM_CATALOGUE,
    "IpmService.delete_treatment": _IPM_CATALOGUE,
}

_PHASE_CALLBACK = (
    "post-transition callback (register_on_transition, app/common/dependencies.py:{line}); invoked only by "
    "PhaseService.transition_phase with the plant key the transition engine just wrote "
    "(app/domain/services/phase_service.py:510) — no request hands it a key, and the tenant would be read off "
    "that same plant"
)

#: Keyed writes no request addresses with a key of its own choosing: internal callbacks, beat entry
#: points that take a loaded document, and cross-tenant platform-admin moderation.
_NOT_TENANT_ADDRESSED: dict[str, str] = {
    "TaskService.activate_dormant_tasks_for_phase": _PHASE_CALLBACK.format(line=535),
    "PlantInstanceService.handle_monocarpic_terminal_transition": _PHASE_CALLBACK.format(line=541),
    "SeasonStateService.evaluate_site": ("takes a loaded Site, not a key; delegates to evaluate_site_detailed"),
    "SeasonStateService.evaluate_site_detailed": (
        "takes a loaded Site, not a key; its only caller is the evaluate_season_states beat "
        "(app/tasks/season_tasks.py:61), which skips inactive tenants, and every read below is scoped by the "
        "site's own tenant (app/domain/services/season_state_service.py:97, :270)"
    ),
    "PestImageService.set_promotion": (
        "cross-tenant moderation of contributed pest images; the only route is behind require_platform_admin "
        "(app/api/v1/admin/pests/router.py:181)"
    ),
    "PestImageService.set_active": (
        "cross-tenant moderation of contributed pest images; the only route is behind require_platform_admin "
        "(app/api/v1/admin/pests/router.py:181)"
    ),
}


#: Measured 2026-10-05 after the first slices of #2107 (activity-plan apply, site,
#: nutrient plan): 150 entries. Re-measured 2026-10-11 after the planting-run and
#: tank slices: 136. Re-measured 2026-10-11 after the harvest, feeding,
#: watering, succession, import, post-harvest, activity-plan and
#: overwintering slice: 106. Re-measured 2026-10-11 after the actuator,
#: aquaponics and InvenTree slice (positional tenant → keyword-only, every
#: method of the class, see :data:`_WHOLE_CLASS_KEYWORD_ONLY`): 73. Re-measured
#: 2026-10-11 after the plant-photo gallery slice (every method of
#: ``PlantPhotoService``): 68. Re-measured 2026-10-12 after the catalogue slice
#: (species, cultivar and substrate writes strict; phase-history writes strict;
#: ``PhaseSequenceService`` and the global lifecycle methods of ``PhaseService``
#: classified as global): 40. Re-measured 2026-10-12 after the IPM, task, plant,
#: propagation, diary, quarter-climate and hardiness slice — 15 converted, 10
#: excused per method in :data:`_GLOBAL_CATALOGUE_WRITES` /
#: :data:`_NOT_TENANT_ADDRESSED`: 15 (both slices merged). Re-measured
#: 2026-10-12 after the Home Assistant publish slice (``HaPublishService``
#: set/bulk-set keyword-only, ownership checked in the service): 13. Re-measured
#: 2026-10-12 after the care-reminder slice (all 13 ``CareReminderService``
#: methods keyword-only, the plant verified in the service by ``_owned_plant``,
#: the beats passing the tenant they iterate): 0. The list is empty and stays
#: empty: a new keyed write takes ``*, tenant_key: str`` and checks ownership in
#: the method from the start (:func:`test_every_keyed_service_write_takes_the_tenant_keyword_only`).
_REMAINING: frozenset[str] = frozenset()


def test_every_keyed_service_write_takes_the_tenant_keyword_only() -> None:
    new = sorted(_not_strict() - _REMAINING)
    assert new == [], (
        "These service methods load a document by key and write, but the tenant can be omitted, "
        "defaulted or transposed. Take `*, tenant_key: str` (no default) and check ownership inside "
        f"the method, the way TaskService.get_task does (#2107): {new}"
    )


def test_the_remaining_list_only_shrinks() -> None:
    converted = sorted(_REMAINING - _not_strict())
    assert converted == [], f"Converted (or gone) since the list was pinned — drop them from _REMAINING: {converted}"


def test_every_excluded_class_still_has_a_keyed_write() -> None:
    """An exclusion that excuses nothing is a hole the next method in that class walks through."""
    owners = {w.owner for w in _inventory()}
    assert sorted(set(_NOT_TENANT_DATA) - owners) == []


def test_every_excused_method_is_still_a_keyed_write() -> None:
    """A stale method excuse is a name a new method of the same name would inherit unread."""
    names = {w.qualname for w in _inventory()}
    excused = set(_GLOBAL_CATALOGUE_WRITES) | set(_NOT_TENANT_ADDRESSED)
    assert sorted(excused - names) == []
    assert not set(_GLOBAL_CATALOGUE_WRITES) & set(_NOT_TENANT_ADDRESSED)
    assert not excused & set(_GLOBAL_METHODS)
    assert not {name.split(".")[0] for name in excused} & set(_NOT_TENANT_DATA)


def test_every_global_catalogue_write_takes_the_admin_decision() -> None:
    """The catalogue excuse holds only while the method takes ``is_platform_admin`` keyword-only, no default."""
    by_name = {w.qualname: w for w in _inventory()}
    loose = sorted(name for name in _GLOBAL_CATALOGUE_WRITES if not by_name[name].admin_gated)
    assert loose == [], f"is_platform_admin must be keyword-only without a default (#1501, #2107): {loose}"


def test_every_global_method_is_still_a_keyed_write_without_a_tenant() -> None:
    """A method-level exclusion is stale once the method is gone or takes a tenant — then it must leave."""
    shapes = {w.qualname: w.shape for w in _inventory()}
    stale = sorted(m for m in _GLOBAL_METHODS if shapes.get(m) in (None, "strict"))
    assert stale == [], f"No longer a tenant-less keyed write — drop them from _GLOBAL_METHODS: {stale}"


def test_the_inventory_is_not_vacuous() -> None:
    """Anti-vacuity: the selector reaches the services the audit named, strict and not."""
    names = {w.qualname for w in _inventory()}
    assert len(names) >= 250, len(names)
    assert {
        "SiteService.update_site",
        "FertilizerService.update_fertilizer",
        "TaskService.update_workflow_template",
        "TankService.update_tank",
    } <= names


# ── REQ-053 WP 4.3 (#2413): the atomic completion transition takes the tenant strictly ──────────────
#
# ``complete_task``, ``reopen_task`` and ``batch_status_change`` load by key (``get_task``) and, since WP 4.3, write the
# task, the care-log line and the specialist document in one stream transaction. The selector derives them already;
# this pins that it keeps seeing them — a refactor that moved the load behind a differently named helper would drop
# them from the inventory and the rule would pass by finding nothing — and that each takes the tenant keyword-only
# without a default, never positionally next to the task key.

_COMPLETION_TRANSITION = (
    "TaskService.complete_task",
    "TaskService.reopen_task",
    "TaskService.batch_status_change",
)


def test_the_task_completion_transition_is_a_keyed_write_and_takes_the_tenant_strictly() -> None:
    shapes = {w.qualname: w.shape for w in _inventory()}
    assert set(_COMPLETION_TRANSITION) <= set(shapes), sorted(set(_COMPLETION_TRANSITION) - set(shapes))
    assert {name: shapes[name] for name in _COMPLETION_TRANSITION} == dict.fromkeys(_COMPLETION_TRANSITION, "strict")
    assert not set(_COMPLETION_TRANSITION) & _REMAINING


def test_the_completion_repository_takes_the_tenant_in_every_method() -> None:
    """The port's methods are keyword-only on the tenant too: a transposed pair of keys is invisible to mypy."""
    tree = ast.parse((_APP / "domain" / "interfaces" / "task_completion_repository.py").read_text(encoding="utf-8"))
    (port,) = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ITaskCompletionRepository"]
    methods = [n for n in port.body if isinstance(n, ast.FunctionDef)]
    assert {m.name for m in methods} >= {"complete", "reopen", "task_event", "plant_location", "plants_in_locations"}
    assert [m.name for m in methods if not _takes_tenant_strictly(m)] == []


# ── Whole classes: no method takes the tenant positionally ───────────────────────────────────────────
#
# The rule above sees only keyed writes. In a service whose every signature read
# ``(key, tenant_key, data)`` the reads, lists and creates carried the same
# transposable shape: ``create_actuator(location_key, tenant_key, actuator)`` and
# ``list_schedules(actuator_key, tenant_key)`` put two ``str`` keys side by side, and
# a swapped pair is caught by no type checker. A class converted in full is listed
# here and held to it: every method, public or private, that takes ``tenant_key``
# takes it keyword-only without a default. The set may only grow.

_WHOLE_CLASS_KEYWORD_ONLY: dict[str, str] = {
    "ActuatorService": "actuator_service.py",
    "AquaponikService": "aquaponik_service.py",
    "InvenTreeService": "inventree_service.py",
    "PlantPhotoService": "plant_photo_service.py",
    "GardenPlanService": "garden_plan_service.py",
    "GardenResourceService": "garden_resource_service.py",
    "CareEventService": "care_event_service.py",
    "PlantingReservationService": "planting_reservation_service.py",
    # REQ-053 WP 5.2 (#2431): the JSON backup, the SVG and the PDF read a whole site and resolve it through
    # ``require_owned_site`` — no ``get…_by_key``, so the keyed-write selector is blind to them, and an export that
    # lost its ``tenant_key`` would hand out another tenant's plan. Read-only, hence no entry among the writers.
    "GardenPlanExportService": "garden_plan_export_service.py",
    "AdjacencyService": "adjacency_service.py",
    # REQ-053 WP 5.3 (#2432): the plan import resolves the site through ``require_owned_site`` and walks the
    # structure through the repository's site join - no ``get…_by_key`` - while it deletes and inserts a whole plan.
    "GardenPlanImportService": "garden_plan_import_service.py",
    "BedRotationService": "bed_rotation_service.py",
    # REQ-053 WP 3.7 (#2397): the plant states of a bed. Read-only and resolved through ``resolve_owned_location`` —
    # no ``get…_by_key`` — so a ``list_plant_states`` that lost its ``tenant_key`` would hand out the plants, tasks
    # and findings of another tenant's bed and no selector above would notice.
    "PlantStateService": "plant_state_service.py",
    # REQ-053 WP 4.5 (#2423): the combined history of a bed. Read-only; it takes the tenant like the other readers.
    "BedHistoryService": "bed_history_service.py",
    # REQ-053 WP 7.1 (#2467, GP-ACC-046): the irrigation zones. The zone carries its tenant; the site, the beds and the
    # water source of a body are resolved under it inside the service, never in the router.
    "IrrigationZoneService": "irrigation_zone_service.py",
}

#: Anti-vacuity floor per class: how many methods take a tenant at least. The large services carry
#: twenty and more; a smaller class is pinned at its measured count so an emptied match still fails.
_MIN_TENANT_METHODS: dict[str, int] = {
    "PlantPhotoService": 10,
    "GardenPlanService": 6,
    "GardenResourceService": 12,
    "CareEventService": 7,
    "PlantingReservationService": 6,
    "GardenPlanExportService": 5,
    "AdjacencyService": 3,
    "GardenPlanImportService": 5,
    "BedRotationService": 4,
    "PlantStateService": 1,
    "BedHistoryService": 1,
    "IrrigationZoneService": 9,
}
_DEFAULT_MIN_TENANT_METHODS = 20


def _tenant_taking_methods(
    services: Path, klass: str, filename: str
) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse((services / filename).read_text(encoding="utf-8"))
    (cls,) = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == klass]
    found: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    for fn in cls.body:
        if not isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        args = fn.args
        if "tenant_key" in {a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]}:
            found[fn.name] = fn
    return found


def _loose_in_whole_classes(services: Path) -> list[str]:
    return sorted(
        f"{klass}.{name}"
        for klass, filename in _WHOLE_CLASS_KEYWORD_ONLY.items()
        for name, fn in _tenant_taking_methods(services, klass, filename).items()
        if not _takes_tenant_strictly(fn)
    )


def test_a_converted_class_takes_the_tenant_keyword_only_in_every_method() -> None:
    loose = _loose_in_whole_classes(_SERVICES)
    assert loose == [], (
        "These methods of a fully converted service take `tenant_key` positionally or with a default, "
        f"where a swapped key is invisible to the type checker. Take `*, tenant_key: str` (#2107): {loose}"
    )


def test_the_whole_class_rule_is_not_vacuous() -> None:
    """Every listed class exists and takes a tenant in many methods, so an empty match cannot pass."""
    counts = {
        klass: len(_tenant_taking_methods(_SERVICES, klass, filename))
        for klass, filename in _WHOLE_CLASS_KEYWORD_ONLY.items()
    }
    assert set(_MIN_TENANT_METHODS) <= set(_WHOLE_CLASS_KEYWORD_ONLY)
    assert all(
        count >= _MIN_TENANT_METHODS.get(klass, _DEFAULT_MIN_TENANT_METHODS) for klass, count in counts.items()
    ), counts


def test_the_whole_class_rule_finds_a_planted_positional_tenant(tmp_path: Path) -> None:
    """End to end on a copy: one method put back to ``(key, tenant_key, data)`` is reported by name."""
    import shutil

    services = tmp_path / "services"
    shutil.copytree(_SERVICES, services, ignore=shutil.ignore_patterns("__pycache__"))
    assert _loose_in_whole_classes(services) == []  # the copy starts strict; a missed replace stays []
    target = services / "aquaponik_service.py"
    target.write_text(
        target.read_text(encoding="utf-8").replace(
            "def update_system(self, key: str, data: dict[str, Any], *, tenant_key: str)",
            "def update_system(self, key: str, tenant_key: str, data: dict[str, Any])",
        ),
        encoding="utf-8",
    )
    assert _loose_in_whole_classes(services) == ["AquaponikService.update_system"]


# ── REQ-053 WP 1.10 (#2329): the garden-plan services resolve ownership through the anchor ───────────
#
# ``GardenPlanService`` and ``GardenResourceService`` (and with them the slot and garden-object
# writes, which have no service of their own) load by walking ``location_ownership`` — ``_owned_site``,
# ``resolve_owned_location`` — and never name a ``get…_by_key``. The keyed-write selector above is
# therefore blind to them: ``apply_batch``, ``set_boundary``, ``change_bed_status``, ``delete_location``,
# ``patch_slot`` and ``replace_slots`` are writers (call graph) that it does not list, and a method that
# lost its ``tenant_key`` altogether would escape the whole-class rule too, which only looks at methods
# that still take one. This rule closes both holes for the two classes: **every public method takes the
# tenant strictly**, and **every public writer of these modules is among them**. A third class of the
# slice joins by being added to the dict.

_ANCHORED_SERVICES: dict[str, str] = {
    "GardenPlanService": "garden_plan_service.py",
    "GardenResourceService": "garden_resource_service.py",
    # REQ-053 WP 4.1 (#2400): the care log resolves the bed through ``resolve_owned_location`` and loads its own
    # events through ``repo.get`` — no ``get…_by_key`` — so the keyed-write selector above is blind to
    # create / supersede / void / redact too. ``build_event`` is no writer but is public API for the callers that
    # write in their own transaction, and it resolves the bed: it takes the tenant like the rest.
    "CareEventService": "care_event_service.py",
    # REQ-053 WP 3.2 (#2392): reservations resolve the bed through ``resolve_owned_location`` and the run through
    # ``verify_tenant_ownership`` on a run the service loaded with ``get_or_raise`` — the keyed-write selector sees
    # the load but not the layout / clearing writers, which reach the repository through write sets. Every public
    # method takes the tenant strictly.
    "PlantingReservationService": "planting_reservation_service.py",
    "GardenPlanExportService": "garden_plan_export_service.py",
    # REQ-053 WP 3.3 (#2393): the neighbourhood of a bed's slots. ``recompute`` resolves the bed through
    # ``resolve_owned_location`` and the manual edges resolve both slots through ``resolve_owned_slot`` — no
    # ``get…_by_key`` on a repository, so the keyed-write selector is blind to all three. The Celery task that
    # triggers ``recompute`` finds the tenant on the stored site and passes it in; nothing in the message does.
    "AdjacencyService": "adjacency_service.py",
    # REQ-053 WP 5.3 (#2432): ``import_plan`` anchors on ``require_owned_site`` and deletes/inserts a whole plan.
    "GardenPlanImportService": "garden_plan_import_service.py",
    # REQ-053 WP 3.4 (#2394): bed-level rotation hints and the history backfill. ``backfill`` resolves the bed through
    # ``resolve_owned_location`` and writes through ``CareEventService.create``, ``cancel_backfill`` loads the event
    # with ``repo.get`` and voids it — neither names a ``get…_by_key``, so the keyed-write selector is blind to both.
    # The reads (``validate_planting``, ``rotation_timeline``) take the tenant like the writers: the history of a bed
    # names the families a tenant grew.
    "BedRotationService": "bed_rotation_service.py",
    # REQ-053 WP 3.7 (#2397): ``list_plant_states`` resolves the bed through ``resolve_owned_location``; the class
    # has no writer, so it adds nothing to the expected set below, but its one public method takes the tenant strictly.
    "PlantStateService": "plant_state_service.py",
}
_EXPECTED_ANCHORED_WRITERS = frozenset(
    {
        "GardenPlanService.apply_batch",
        "GardenPlanService.set_boundary",
        "GardenResourceService.patch_location",
        "GardenResourceService.change_bed_status",
        "GardenResourceService.delete_location",
        "GardenResourceService.create_garden_object",
        "GardenResourceService.patch_garden_object",
        "GardenResourceService.delete_garden_object",
        "GardenResourceService.patch_slot",
        "GardenResourceService.replace_slots",
        "CareEventService.create",
        "CareEventService.supersede",
        "CareEventService.void",
        "CareEventService.redact",
        "PlantingReservationService.place_layout",
        "PlantingReservationService.plan_slots",
        "PlantingReservationService.release_slot",
        "PlantingReservationService.clear_bed",
        "PlantingReservationService.record_position_correction",
        "AdjacencyService.recompute",
        "AdjacencyService.set_manual_edge",
        "AdjacencyService.remove_manual_edge",
        "GardenPlanImportService.import_plan",
        "BedRotationService.backfill",
        "BedRotationService.cancel_backfill",
    }
)


def _public_methods(services: Path, klass: str, filename: str) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse((services / filename).read_text(encoding="utf-8"))
    (cls,) = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == klass]
    return {
        fn.name: fn
        for fn in cls.body
        if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef) and not fn.name.startswith("_")
    }


def _anchored_without_the_tenant(services: Path) -> list[str]:
    return sorted(
        f"{klass}.{name}"
        for klass, filename in _ANCHORED_SERVICES.items()
        for name, fn in _public_methods(services, klass, filename).items()
        if not _takes_tenant_strictly(fn)
    )


def _anchored_writers() -> set[str]:
    modules = {
        f"app.domain.services.{filename.removesuffix('.py')}": klass for klass, filename in _ANCHORED_SERVICES.items()
    }
    found: set[str] = set()
    for writer in call_graph().writers():
        module, _, qualname = writer.partition("::")
        owner, _, name = qualname.partition(".")
        if modules.get(module) == owner and not name.startswith("_"):
            found.add(qualname)
    return found


def test_every_public_method_of_an_anchored_service_takes_the_tenant_keyword_only() -> None:
    loose = _anchored_without_the_tenant(_SERVICES)
    assert loose == [], (
        "These public methods of a garden-plan service lack `*, tenant_key: str` (no default); the ownership "
        f"walk cannot run without it (#2107, #2329): {loose}"
    )


def test_every_public_writer_of_the_anchored_services_is_covered_and_none_is_missing() -> None:
    writers = _anchored_writers()
    assert writers == set(_EXPECTED_ANCHORED_WRITERS), sorted(writers ^ set(_EXPECTED_ANCHORED_WRITERS))
    covered = {
        f"{klass}.{name}"
        for klass, filename in _ANCHORED_SERVICES.items()
        for name in _public_methods(_SERVICES, klass, filename)
    }
    assert writers <= covered


def test_the_anchored_rule_finds_a_planted_missing_tenant(tmp_path: Path) -> None:
    """End to end on a copy: ``apply_batch`` put back to a tenant-less signature is reported by name."""
    import shutil

    services = tmp_path / "services"
    shutil.copytree(_SERVICES, services, ignore=shutil.ignore_patterns("__pycache__"))
    assert _anchored_without_the_tenant(services) == []
    target = services / "garden_plan_service.py"
    original = target.read_text(encoding="utf-8")
    head = "        *,\n"
    tail = "        user_key: str,\n        role: TenantRole,\n        expected_revision"
    signature = head + "        tenant_key: str,\n" + tail
    planted = original.replace(signature, head + tail)
    assert planted != original, "the planted replacement did not apply"
    target.write_text(planted, encoding="utf-8")
    assert _anchored_without_the_tenant(services) == ["GardenPlanService.apply_batch"]


class TestTheRuleSeesTheShapes:
    """Self-tests on :func:`_shape` and :func:`_loads_by_key`, the expressions the rule evaluates."""

    @staticmethod
    def _fn(source: str) -> ast.FunctionDef:
        node = ast.parse(source).body[0]
        assert isinstance(node, ast.FunctionDef)
        return node

    def test_the_shapes(self) -> None:
        assert _shape(self._fn("def f(self, key, *, tenant_key: str): ...")) == "strict"
        assert _shape(self._fn("def f(self, ctx: TenantContext, key): ...")) == "strict"
        assert _shape(self._fn('def f(self, key, *, tenant_key: str = ""): ...')) == "keyword-with-default"
        assert _shape(self._fn("def f(self, key, tenant_key: str): ...")) == "positional"
        assert _shape(self._fn('def f(self, key, tenant_key: str = ""): ...')) == "positional-with-default"
        assert _shape(self._fn("def f(self, key, ctx: TenantContext | None = None): ...")) == "none"
        assert _shape(self._fn("def f(self, key): ...")) == "none"

    def test_the_admin_decision_shapes(self) -> None:
        assert _takes_platform_admin_strictly(self._fn("def f(self, key, *, is_platform_admin: bool): ..."))
        assert not _takes_platform_admin_strictly(self._fn("def f(self, key, *, is_platform_admin: bool = False): ..."))
        assert not _takes_platform_admin_strictly(self._fn("def f(self, key, is_platform_admin: bool): ..."))
        assert not _takes_platform_admin_strictly(self._fn("def f(self, key): ..."))

    def test_a_load_through_a_same_class_helper_counts_and_a_self_getter_alone_does_not(self) -> None:
        klass = ast.parse(
            "class S:\n"
            "    def get_x(self, key):\n        return self._repo.get_x_or_raise(key)\n"
            "    def update_x(self, key):\n        self.get_x(key)\n        self._repo.update(key)\n"
            "    def touch(self, key):\n        self.get_by_key(key)\n"
        ).body[0]
        assert isinstance(klass, ast.ClassDef)
        methods = {n.name: n for n in klass.body if isinstance(n, ast.FunctionDef)}
        assert _loads_by_key(methods["update_x"], methods, frozenset({"update_x"}))
        assert not _loads_by_key(methods["touch"], methods, frozenset({"touch"}))

    def test_the_selector_finds_a_planted_check_then_act_write(self, tmp_path: Path) -> None:
        """End to end on a copy of the tree: the #948 shape is found, its strict twin passes."""
        import shutil

        root = tmp_path / "app"
        shutil.copytree(_APP, root, ignore=shutil.ignore_patterns("__pycache__"))
        target = root / "domain" / "services" / "site_service.py"
        planted = (
            "\n\nclass PlantedService:\n"
            "    def __init__(self, repo: ISiteRepository) -> None:\n        self._repo = repo\n\n"
            "    def rename(self, key: str, name: str) -> None:\n"
            "        site = self._repo.get_site_or_raise(key)\n"
            "        self._repo.update_site(key, site)\n"
        )
        target.write_text(target.read_text(encoding="utf-8") + planted, encoding="utf-8")
        writers = {"app.domain.services.site_service::PlantedService.rename"}
        assert [w.shape for w in keyed_writes(root, writers) if w.owner == "PlantedService"] == ["none"]

        target.write_text(
            target.read_text(encoding="utf-8").replace(
                "def rename(self, key: str, name: str)", "def rename(self, key: str, name: str, *, tenant_key: str)"
            ),
            encoding="utf-8",
        )
        assert [w.shape for w in keyed_writes(root, writers) if w.owner == "PlantedService"] == ["strict"]


# ── #2137: TenantService's service-account methods are strict despite the class exemption ──────────
#
# ``TenantService`` is in :data:`_NOT_TENANT_DATA` because its keys address tenants, memberships and
# invitations. Its service-account methods are different: they mint, revoke and list API keys scoped to
# one tenant and resolve an account inside it, so the exemption must not reach them. Selected by name
# (``service_account`` in a public method name), held strict: ``tenant_key`` keyword-only, no default.


def _service_account_methods() -> dict[str, ast.FunctionDef]:
    path = Path(__file__).resolve().parents[3] / "app" / "domain" / "services" / "tenant_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    (cls,) = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "TenantService"]
    return {
        n.name: n
        for n in cls.body
        if isinstance(n, ast.FunctionDef) and "service_account" in n.name and not n.name.startswith("_")
    }


def _takes_tenant_strictly(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    args = function.args
    positional = [a.arg for a in args.posonlyargs + args.args]
    for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        if arg.arg == "tenant_key":
            return default is None and "tenant_key" not in positional
    return False


def test_the_service_account_methods_take_the_tenant_keyword_only() -> None:
    methods = _service_account_methods()

    assert set(methods) == {
        "create_service_account",
        "list_service_accounts",
        "rotate_service_account_key",
        "remove_service_account",
    }, sorted(methods)
    loose = sorted(name for name, fn in methods.items() if not _takes_tenant_strictly(fn))
    assert loose == [], f"tenant_key must be keyword-only without a default (#2107 rule, #2137): {loose}"


def test_the_strictness_check_tells_the_shapes_apart() -> None:
    def fn(source: str) -> ast.FunctionDef:
        (node,) = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.FunctionDef)]
        return node

    assert _takes_tenant_strictly(fn("def f(self, key, *, tenant_key): ..."))
    assert not _takes_tenant_strictly(fn("def f(self, tenant_key, key): ..."))
    assert not _takes_tenant_strictly(fn("def f(self, key, *, tenant_key=''): ..."))
    assert not _takes_tenant_strictly(fn("def f(self, key): ..."))


# ── REQ-053 GP-ACC-046: the guard lists the garden-plan services ──────────────────────────────────────────
#
# GP-ACC-046 (spec v1.6) names ``garden_plan_service``, ``care_event_service`` and ``irrigation_zone_service``. The
# first two resolve their beds through ``location_ownership`` (no ``get…_by_key``), so the keyed-write selector does
# not see them and the whole-class rule above holds them; the zone service loads its zone by key, so it is held by
# both. Pinned by name, so a refactor that hid a load behind a helper the selector does not follow fails here
# instead of passing by finding nothing; each write takes the tenant keyword-only without a default.

_GP_ACC_046_SERVICES = ("GardenPlanService", "CareEventService", "IrrigationZoneService")
_ZONE_KEYED_WRITES = (
    "IrrigationZoneService.create_zone",
    "IrrigationZoneService.patch_zone",
    "IrrigationZoneService.delete_zone",
    "IrrigationZoneService.replace_locations",
)


def test_gp_acc_046_the_garden_plan_services_are_listed() -> None:
    assert set(_GP_ACC_046_SERVICES) <= set(_WHOLE_CLASS_KEYWORD_ONLY)


def test_gp_acc_046_the_zone_services_keyed_writes_are_seen_and_strict() -> None:
    shapes = {w.qualname: w.shape for w in _inventory()}

    assert set(_ZONE_KEYED_WRITES) <= set(shapes), sorted(set(_ZONE_KEYED_WRITES) - set(shapes))
    assert {name: shapes[name] for name in _ZONE_KEYED_WRITES} == dict.fromkeys(_ZONE_KEYED_WRITES, "strict")
    assert not set(_ZONE_KEYED_WRITES) & _REMAINING
