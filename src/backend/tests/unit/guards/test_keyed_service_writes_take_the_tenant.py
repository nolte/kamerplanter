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
    "ActivityService": "global activity catalogue, written only behind require_platform_admin (#2119 owns tenant rows)",
    "LocationTypeService": "global location-type catalogue, written only behind require_platform_admin",
}


@dataclass(frozen=True)
class KeyedWrite:
    owner: str
    name: str
    shape: str

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
                    found.append(KeyedWrite(klass.name, name, _shape(fn)))
    return found


@cache
def _inventory() -> tuple[KeyedWrite, ...]:
    return tuple(keyed_writes(_APP, call_graph().writers()))


def _not_strict() -> set[str]:
    return {w.qualname for w in _inventory() if w.shape != "strict" and w.owner not in _NOT_TENANT_DATA}


#: Measured 2026-10-05 after the slices of #2107 that landed (activity-plan apply,
#: site, nutrient plan). Each line is a keyed write that can still be called
#: without a tenant, or with a defaulted / positional one. Convert the method to
#: ``*, tenant_key: str`` (and drop the router's pre-check), then delete the line.
_REMAINING: frozenset[str] = frozenset(
    {
        "ActivityPlanService.generate_plan",
        "ActivityPlanService.get_or_generate_for_species",
        "ActivityPlanService.regenerate_for_species",
        "ActuatorService.apply_profile",
        "ActuatorService.clear_override",
        "ActuatorService.create_rule",
        "ActuatorService.create_schedule",
        "ActuatorService.delete_actuator",
        "ActuatorService.delete_profile",
        "ActuatorService.delete_rule",
        "ActuatorService.delete_schedule",
        "ActuatorService.send_command",
        "ActuatorService.set_override",
        "ActuatorService.toggle_rule",
        "ActuatorService.toggle_schedule",
        "ActuatorService.update_actuator",
        "ActuatorService.update_profile",
        "ActuatorService.update_rule",
        "ActuatorService.update_schedule",
        "AquaponikService.create_stock",
        "AquaponikService.delete_stock",
        "AquaponikService.delete_system",
        "AquaponikService.record_feeding",
        "AquaponikService.record_mortality",
        "AquaponikService.record_supplementation",
        "AquaponikService.record_water_test",
        "AquaponikService.set_cycling_status",
        "AquaponikService.update_stock",
        "AquaponikService.update_system",
        "CalendarService.delete_feed",
        "CalendarService.regenerate_token",
        "CalendarService.update_feed",
        "CareReminderService.advance_watering_task_after_log",
        "CareReminderService.complete_care_task_with_log",
        "CareReminderService.confirm_reminder",
        "CareReminderService.ensure_next_watering_task",
        "CareReminderService.ensure_seasonal_winter_tasks",
        "CareReminderService.get_care_dashboard",
        "CareReminderService.get_care_dashboard_for_tenant",
        "CareReminderService.get_or_create_profile",
        "CareReminderService.record_care_task_completion",
        "CareReminderService.record_care_task_skip",
        "CareReminderService.reset_profile",
        "CareReminderService.snooze_reminder",
        "CareReminderService.update_profile",
        "FeedingService.delete_event",
        "FeedingService.update_event",
        "HaPublishService.bulk_set_published",
        "HaPublishService.set_published",
        "HardinessZoneService.resolve_for_site",
        "HarvestService.complete_harvest",
        "HarvestService.complete_harvest_for_run",
        "HarvestService.create_quality_assessment",
        "HarvestService.create_yield_metric",
        "HarvestService.update_batch",
        "ImportService.confirm",
        "InvenTreeService.delete_connection",
        "InvenTreeService.delete_equipment",
        "InvenTreeService.health_check",
        "InvenTreeService.sync_reference",
        "InvenTreeService.unlink_entity",
        "InvenTreeService.update_connection",
        "InvenTreeService.update_equipment",
        "IpmService.create_treatment_application",
        "IpmService.delete_disease",
        "IpmService.delete_pest",
        "IpmService.delete_treatment",
        "IpmService.update_disease",
        "IpmService.update_pest",
        "IpmService.update_treatment",
        "OverwinteringProfileService.auto_generate_profile",
        "OverwinteringProfileService.create_profile",
        "OverwinteringProfileService.delete_profile",
        "OverwinteringProfileService.link_shared_template",
        "OverwinteringProfileService.unlink_shared_template",
        "OverwinteringProfileService.update_profile",
        "PestImageService.set_active",
        "PestImageService.set_promotion",
        "PhaseSequenceService.clone_sequence",
        "PhaseSequenceService.create_entry",
        "PhaseSequenceService.delete_definition",
        "PhaseSequenceService.delete_entry",
        "PhaseSequenceService.delete_sequence",
        "PhaseSequenceService.reorder_entries",
        "PhaseSequenceService.update_definition",
        "PhaseSequenceService.update_entry",
        "PhaseSequenceService.update_sequence",
        "PhaseService.assign_phase_sequence",
        "PhaseService.delete_phase",
        "PhaseService.delete_phase_history",
        "PhaseService.generate_default_profiles",
        "PhaseService.update_lifecycle",
        "PhaseService.update_phase",
        "PhaseService.update_phase_history_dates",
        "PlantDiaryService.delete_entry",
        "PlantInstanceService.create_plant",
        "PlantInstanceService.handle_monocarpic_terminal_transition",
        "PlantInstanceService.remove_plant",
        "PlantInstanceService.update_plant",
        "PlantPhotoService.assess_photo",
        "PlantPhotoService.delete_photo",
        "PlantPhotoService.link_photo",
        "PlantPhotoService.set_cover",
        "PlantPhotoService.update_photo_metadata",
        "PlantingRunService.add_entry",
        "PlantingRunService.batch_remove",
        "PlantingRunService.batch_update_phase_dates",
        "PlantingRunService.create_plants",
        "PlantingRunService.create_run",
        "PlantingRunService.delete_run",
        "PlantingRunService.remove_nutrient_plan",
        "PlantingRunService.transition",
        "PlantingRunService.update_run",
        "PostHarvestService.advance_stage",
        "PostHarvestService.delete_batch",
        "PostHarvestService.record_drying_progress",
        "PostHarvestService.record_observation",
        "PostHarvestService.start_drying",
        "PropagationService.create_batch",
        "PropagationService.finalize_batch",
        "QuarterClimateService.evaluate_plant",
        "SeasonStateService.evaluate_site",
        "SeasonStateService.evaluate_site_detailed",
        "SpeciesService.create_cultivar",
        "SpeciesService.create_species",
        "SpeciesService.delete_cultivar",
        "SpeciesService.delete_species",
        "SpeciesService.update_cultivar",
        "SpeciesService.update_species",
        "SubstrateService.create_batch",
        "SubstrateService.create_mix",
        "SubstrateService.delete_batch",
        "SubstrateService.delete_substrate",
        "SubstrateService.update_batch",
        "SubstrateService.update_substrate",
        "SuccessionPlanService.delete_plan",
        "SuccessionPlanService.generate_next_run",
        "SuccessionPlanService.generate_runs",
        "SuccessionPlanService.update_plan",
        "TankService.create_schedule",
        "TankService.delete_tank",
        "TankService.log_maintenance",
        "TankService.record_fill_event",
        "TankService.record_state",
        "TaskService.activate_dormant_tasks_for_phase",
        "TaskService.create_workflow_phase",
        "TaskService.delete_workflow_phase",
        "TaskService.duplicate_workflow_template",
        "TaskService.update_workflow_phase",
        "WateringLogService.create_log",
        "WateringLogService.delete_log",
        "WateringLogService.update_log",
        "WateringService.create_event",
    }
)


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


def _takes_tenant_strictly(function: ast.FunctionDef) -> bool:
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
