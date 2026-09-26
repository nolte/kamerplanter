"""#1864/#1867/#1868 — a key the caller supplies is resolved under the caller's tenant before it is used.

The defect class of this bundle: a key of another entity reaches a write — from
the path or from the body — and is stored, linked or acted on without being
resolved under the caller's tenant. Found as #1864 (assign-slot), #1867 (child
keys verified only through their parent), #1868 (a run's substrate batch), and
by the sweep they triggered (location parent, tank location, watering
confirmation task, task clone, calendar site; B #1871 and C #1872 for the rest).

**Why the #1619 hook did not catch them.** ``scripts/check_plant_scoped_route_tenant.py``
asks, for each *non-terminal* path key whose name is in ``OWNABLE_PARAMS``
(plant, run, observation, fertilizer, tank, equipment, cultivar), whether the
handler passes it on with a tenant argument. Terminal child keys
(``entry_key``, ``skey``, ``other_key``, ``slot_key``) are outside it by design,
keys of other collections (``batch_key``, ``slot_key``) are outside its
allowlist, a route that resolves no tenant has nothing to scope with, and body
fields are not path keys at all.

This guard holds the class in two halves, each enumerating rather than listing
today's sites:

1. **Path keys.** Every write route of the assembled app that resolves a tenant
   must hand each non-tenant path key to a call that also carries the tenant
   (``tenant_key=`` / ``ctx``) — read off the handler's AST — or be listed in
   :data:`_PATH_KEYS_VERIFIED_ELSEWHERE` with the mechanism that verifies it
   (a router dependency, a repository guard, the parent). Routes resolving no
   tenant are held by ``test_keyed_writes_resolve_a_tenant``.
2. **Stored reference fields.** Every field of a tenant-owned model
   (``tenant_key`` in its fields) that names another entity (``*_key`` /
   ``*_keys``) is classified in :data:`_REFERENCE_FIELDS`. A new field fails
   until someone decides what it is. The open ones carry their issue (#1871 /
   #1872); an open one that has since been declared an owned reference in a
   repository (``_owned_reference_fields``) is reported as stale.

What neither half sees, named: a handler that passes the tenant to a call that
does not use it for the key (half 1 is structural); a body key that is stored
only as a graph edge and not as a model field (``source_tank_key`` of
feeds-from, #1871 B5) — neither a path key nor a field; and whether a
``verified`` classification is still true (half 2 is a register — the route and
service tests of each fix hold the behaviour).
"""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil
import textwrap
from typing import Any

import pytest
from fastapi.dependencies.utils import get_dependant
from fastapi.routing import APIRoute
from pydantic import BaseModel

# ── half 1: path keys on tenant-resolving write routes ────────────────────────

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_TENANT_WORDS = {"tenant_key", "ctx", "tenant", "tenant_slug"}

_REQUIRE_OWNED_PLANT = "router dependency require_owned_plant resolves the plant under the active tenant (#1402)"
_PARENT_SENSOR = "the parent is resolved under the tenant; get_sensor_in_parent 404s a sensor of another parent"
_REPO_PLANT_GUARD = "the repository verifies plant_key with verify_entity_ownership before the insert"

#: ``(method, path, key)`` → how the key is verified although the handler passes
#: it on without a tenant argument. From the #1864 triage (read into service and
#: repository); every entry is a VERIFIED or GLOBAL verdict, never a gap.
_PATH_KEYS_VERIFIED_ELSEWHERE: dict[tuple[str, str, str], str] = {
    ("PUT", "/api/v1/botanical-families/{key}", "key"): "global catalogue row; platform-admin gate in the handler",
    ("POST", "/api/v1/species/{species_key}/cultivars/{cultivar_key}/grants", "species_key"): (
        "unused; the cultivar is resolved and authorised under the tenant (species_service._authorize_cultivar_write)"
    ),
    ("DELETE", "/api/v1/species/{species_key}/cultivars/{cultivar_key}/grants/{grantee_key}", "species_key"): (
        "unused; the cultivar is resolved and authorised under the tenant"
    ),
    ("POST", "/api/v1/plant-instances/{plant_key}/phases/transition", "plant_key"): _REQUIRE_OWNED_PLANT,
    ("PATCH", "/api/v1/plant-instances/{plant_key}/phases/history/{history_key}", "plant_key"): _REQUIRE_OWNED_PLANT,
    ("PATCH", "/api/v1/plant-instances/{plant_key}/phases/history/{history_key}", "history_key"): (
        "resolved within the owned plant's history (phase_service)"
    ),
    ("DELETE", "/api/v1/plant-instances/{plant_key}/phases/history/{history_key}", "plant_key"): _REQUIRE_OWNED_PLANT,
    ("DELETE", "/api/v1/plant-instances/{plant_key}/phases/history/{history_key}", "history_key"): (
        "resolved within the owned plant's history (phase_service)"
    ),
    ("PUT", "/api/v1/t/{tenant_slug}/sites/{key}/sensors/{sensor_key}", "sensor_key"): _PARENT_SENSOR,
    ("PUT", "/api/v1/t/{tenant_slug}/locations/{key}/sensors/{sensor_key}", "sensor_key"): _PARENT_SENSOR,
    ("PUT", "/api/v1/t/{tenant_slug}/tanks/{key}/sensors/{sensor_key}", "sensor_key"): _PARENT_SENSOR,
    ("POST", "/api/v1/t/{tenant_slug}/harvest/plants/{plant_key}/batches", "plant_key"): (
        "create_harvest_batch runs check_harvest_safety → verify_plant_ownership before writing"
    ),
    ("PUT", "/api/v1/t/{tenant_slug}/tasks/phases/{key}", "key"): (
        "the phase's workflow template is resolved under the tenant (own or global); system templates refused"
    ),
    ("DELETE", "/api/v1/t/{tenant_slug}/tasks/phases/{key}", "key"): (
        "the phase's workflow template is resolved under the tenant (own or global); system templates refused"
    ),
    ("POST", "/api/v1/t/{tenant_slug}/ipm/plants/{plant_key}/inspections", "plant_key"): _REPO_PLANT_GUARD,
    ("POST", "/api/v1/t/{tenant_slug}/ipm/plants/{plant_key}/treatment-applications", "plant_key"): (
        _REPO_PLANT_GUARD + " (the resistance read before it is the oracle tracked as B7 in #1871)"
    ),
    ("DELETE", "/api/v1/t/{tenant_slug}/ipm/pests/{pest_key}/images/{image_id}", "pest_key"): (
        "global pest catalogue; the contribution is resolved and deleted by (id, tenant_key)"
    ),
    ("DELETE", "/api/v1/t/{tenant_slug}/favorites/{target_key}", "target_key"): (
        "removes only the caller's own favourite edge, anchored on ctx.user_key; the key is never resolved (#1538)"
    ),
    ("POST", "/api/v1/t/{tenant_slug}/planting-runs/{key}/plants/{plant_key}/diary", "plant_key"): (
        "the run is resolved under the tenant; plant_diary_service.create_entry requires the plant to be one of "
        "that run's plants"
    ),
    ("PATCH", "/api/v1/care-reminders/plants/{plant_key}/profile", "plant_key"): _REQUIRE_OWNED_PLANT,
    ("POST", "/api/v1/care-reminders/plants/{plant_key}/snooze", "plant_key"): _REQUIRE_OWNED_PLANT,
    ("POST", "/api/v1/care-reminders/plants/{plant_key}/reset-profile", "plant_key"): _REQUIRE_OWNED_PLANT,
}


def _routes(routes: list[Any], prefix: str = "", inherited: tuple[Any, ...] = ()) -> list[tuple[str, APIRoute, list]]:
    out = []
    for route in routes:
        if isinstance(route, APIRoute):
            path = prefix + route.path_format
            out.append((path, route, [route.dependant, *(get_dependant(path=path, call=c) for c in inherited)]))
        elif hasattr(route, "original_router"):
            ctx = route.include_context
            calls = tuple(d.dependency for d in ctx.dependencies)
            out.extend(_routes(route.original_router.routes, prefix + ctx.prefix, inherited + calls))
    return out


def _calls(dependants: list[Any]) -> set[Any]:
    found: set[Any] = set()
    stack = list(dependants)
    while stack:
        dependant = stack.pop()
        found.add(dependant.call)
        stack.extend(dependant.dependencies)
    return found


def _is_tenant_value(node: ast.AST) -> bool:
    """``ctx.tenant_key``, ``<anything>.tenant_key``, or a bare ``tenant_key`` / ``tenant`` name."""
    if isinstance(node, ast.Attribute):
        return node.attr == "tenant_key"
    if isinstance(node, ast.Name):
        return node.id in {"tenant_key", "tenant"}
    return False


def _carries_the_tenant(call: ast.Call) -> bool:
    """The call hands the tenant itself on — not merely something off ``ctx``.

    Counted: a ``tenant_key=`` / ``tenant=`` keyword whose value is a tenant
    value, a positional tenant value, or ``ctx`` itself passed positionally (the
    callee then reads the tenant). Not counted: ``caller_role=ctx.role``,
    ``ctx=None``, ``logger.info(..., ctx=ctx)`` — the bypasses the security
    review of this bundle named.
    """
    for keyword in call.keywords:
        if keyword.arg in {"tenant_key", "tenant"} and _is_tenant_value(keyword.value):
            return True
    return any(_is_tenant_value(arg) or (isinstance(arg, ast.Name) and arg.id == "ctx") for arg in call.args)


def _passes_with_a_tenant(tree: ast.AST, param: str) -> bool:
    """Whether some call hands ``param`` on together with the tenant."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        args = [*node.args, *(k.value for k in node.keywords)]
        if any(isinstance(a, ast.Name) and a.id == param for a in args) and _carries_the_tenant(node):
            return True
    return False


def _unscoped_path_keys(app: Any) -> tuple[list[tuple[str, str, str]], int]:
    from app.common import auth

    resolvers = {auth.get_current_tenant, auth.get_active_tenant_key, auth.get_active_tenant_context}
    out, keyed = [], 0
    for path, route, dependants in _routes(app.routes):
        methods = sorted(route.methods & _WRITE_METHODS)
        keys = [p.name for p in route.dependant.path_params if p.name != "tenant_slug"]
        if not methods or not keys or not (_calls(dependants) & resolvers):
            continue
        keyed += 1
        tree = ast.parse(textwrap.dedent(inspect.getsource(route.endpoint)))
        out.extend((m, path, k) for m in methods for k in keys if not _passes_with_a_tenant(tree, k))
    return out, keyed


def test_every_path_key_is_handed_on_with_the_tenant_or_verified_elsewhere() -> None:
    from app.main import app

    unscoped, keyed = _unscoped_path_keys(app)
    unexplained = sorted(set(unscoped) - set(_PATH_KEYS_VERIFIED_ELSEWHERE))
    stale = sorted(set(_PATH_KEYS_VERIFIED_ELSEWHERE) - set(unscoped))

    assert keyed > 200, keyed  # non-vacuity: the walk reaches the nested tenant routers
    assert unexplained == [], (
        "write routes that pass a path key on without the tenant and verify it nowhere visible "
        f"(#1867 class): {unexplained}"
    )
    assert stale == [], f"listed keys that are now handed on with the tenant — drop the entry: {stale}"


def test_the_path_key_scan_sees_a_child_key_loaded_alone() -> None:
    source = textwrap.dedent(
        """
        def update_entry(key, entry_key, body, ctx, service):
            service.get_run(key, tenant_key=ctx.tenant_key)
            return service.update_entry(key, entry_key, body)
        """
    )
    fixed = source.replace(
        "update_entry(key, entry_key, body)", "update_entry(key, entry_key, body, tenant_key=ctx.tenant_key)"
    )

    assert _passes_with_a_tenant(ast.parse(source), "entry_key") is False
    assert _passes_with_a_tenant(ast.parse(fixed), "entry_key") is True


@pytest.mark.parametrize(
    "call",
    [
        "service.delete_batch(key, caller_role=ctx.role, is_platform_admin=admin)",
        "service.update_entry(key, entry_key, ctx=None)",
        "logger.info('x', key=key, entry_key=entry_key, ctx=ctx)",
        "service.update_entry(key, entry_key, tenant_key='')",
    ],
    ids=["role-off-ctx", "ctx-none", "log-line", "empty-literal"],
)
def test_the_path_key_scan_is_not_fooled_by_a_ctx_mention(call: str) -> None:
    tree = ast.parse(f"def handler(key, entry_key, ctx, service, admin, logger):\n    {call}\n")

    assert _passes_with_a_tenant(tree, "entry_key" if "entry_key" in call else "key") is False


@pytest.mark.parametrize(
    "call",
    [
        "service.update_entry(key, entry_key, tenant_key=ctx.tenant_key)",
        "service.get_run(entry_key, ctx.tenant_key)",
        "service.update_entry(entry_key, ctx)",
        "service.update_entry(entry_key, tenant=tenant)",
    ],
)
def test_the_path_key_scan_accepts_the_tenant_handed_on(call: str) -> None:
    tree = ast.parse(f"def handler(entry_key, ctx, service, tenant):\n    {call}\n")

    assert _passes_with_a_tenant(tree, "entry_key") is True


# ── half 2: stored reference fields of tenant-owned models ────────────────────

_V, _G, _I, _A, _N = "verified", "global", "internal", "actor", "not-persisted"


def _gap(issue: int, item: str) -> str:
    return f"gap:#{issue}:{item}"


#: ``"module.Model.field"`` → classification. ``verified`` = resolved under the
#: tenant on every write path; ``global`` = the target has no tenant owner;
#: ``internal`` = set only by server code; ``actor`` = the caller's own user key;
#: ``not-persisted`` = query or projection model; ``gap:#<issue>:<item>`` = open.
_REFERENCE_FIELDS: dict[str, str] = {
    "actuator.Actuator.location_key": _V,
    "actuator.ControlEvent.actuator_key": _I,
    "actuator.ControlEvent.location_key": _I,
    "actuator.ControlEvent.triggered_by_rule_key": _I,
    "actuator.ControlEvent.triggered_by_schedule_key": _I,
    "actuator.ControlRule.actuator_key": _V,
    "actuator.ControlRule.sensor_location_key": _gap(1872, "C5"),
    "actuator.ControlSchedule.actuator_key": _V,
    "actuator.ManualOverride.actuator_key": _V,
    "ai_assistant.AiAuditLogEntry.user_key": _A,
    "ai_assistant.AiAuditLogEntry.context_key": _gap(1872, "C9"),
    "ai_assistant.AiConversation.user_key": _A,
    "ai_assistant.AiConversation.context_key": _gap(1872, "C9"),
    "ai_assistant.AiConversation.provider_key": _V,
    "ai_assistant.AiTipCard.context_key": _gap(1872, "C9"),
    "ai_assistant.AiTipCard.provider_key": _I,
    "aquaponik.FishFeedingEvent.system_key": _V,
    "aquaponik.FishFeedingEvent.stock_key": _V,
    "aquaponik.FishStock.system_key": _V,
    "aquaponik.FishStock.species_key": _G,
    "aquaponik.SupplementationEvent.system_key": _V,
    "aquaponik.WaterTest.system_key": _V,
    "attachment.Attachment.storage_key": _I,
    "calendar.CalendarEventsQuery.site_key": _N,
    "calendar.CalendarFeed.user_key": _A,
    "feeding_event.FeedingEvent.plant_key": _V,
    "feeding_event.FeedingEvent.tank_fill_event_key": _gap(1872, "C6"),
    "feeding_event.FeedingEvent.watering_event_key": _I,
    "fertilizer.FertilizerStock.fertilizer_key": _V,
    "ha_publish_setting.HaPublishSetting.entity_key": _gap(1872, "C8"),
    "harvest.HarvestBatch.plant_key": _V,
    "harvest.HarvestBatch.harvested_by_key": _A,
    "identification.IdentificationRequest.user_key": _A,
    "identification.IdentificationRequest.adapter_key": _I,
    "identification.IdentificationRequest.plant_instance_key": _V,
    "inventree.Equipment.location_key": _gap(1871, "B2"),
    "inventree.InvenTreeReference.entity_key": _V,
    "inventree.StockTransaction.reference_key": _I,
    "inventree.StockTransaction.source_event_key": _I,
    "invitation.Invitation.invited_by_user_key": _A,
    "invitation.Invitation.accepted_by_user_key": _A,
    "ipm.Inspection.plant_key": _V,
    "ipm.Inspection.inspected_by_key": _A,
    "ipm.Inspection.detected_pest_keys": _G,
    "ipm.Inspection.detected_disease_keys": _G,
    "ipm.TreatmentApplication.treatment_key": _G,
    "ipm.TreatmentApplication.plant_key": _gap(1871, "B7"),
    "ipm.TreatmentApplication.applied_by_key": _A,
    "irrigation_demand.IrrigationDemand.site_key": _I,
    "irrigation_demand.IrrigationDemand.run_key": _I,
    "location_assignment.LocationAssignment.membership_key": _V,
    "location_assignment.LocationAssignment.location_key": _gap(1871, "B3"),
    "mcp.McpAuditLog.service_account_key": _A,
    "mcp.McpIdempotencyRecord.service_account_key": _A,
    "mcp.McpIdempotencyRecord.idempotency_key": _I,
    "membership.Membership.user_key": _I,
    "membership.UserMembershipInfo.membership_key": _N,
    "notification.Notification.user_key": _gap(1871, "B9"),
    "notification.Notification.group_key": _I,
    "notification.Notification.parent_notification_key": _I,
    "nutrient_plan.NutrientPlan.species_keys": _V,
    "nutrient_plan.NutrientPlan.cloned_from_key": _V,
    "observation.AggregatedReading.sensor_key": _N,
    "observation.SensorReading.sensor_key": _gap(1871, "B6"),
    "overwintering_profile.OverwinteringProfile.plant_key": _V,
    "overwintering_profile.OverwinteringProfile.planting_run_key": _V,
    "overwintering_profile.OverwinteringProfile.winter_quarter_key": _V,
    "overwintering_profile.OverwinteringProfile.source_template_key": _I,
    "pest_detection.PestDetection.user_key": _A,
    "pest_detection.PestDetection.plant_instance_key": _V,
    "pest_detection.PestDetection.planting_run_key": _I,
    "pest_detection.PestDetection.adapter_key": _I,
    "pest_image.PestImageContribution.pest_key": _G,
    "plant_diagnosis_request.PlantDiagnosisRequest.user_key": _A,
    "plant_diagnosis_request.PlantDiagnosisRequest.plant_instance_key": _V,
    "plant_diagnosis_request.PlantDiagnosisRequest.planting_run_key": _V,
    "plant_diagnosis_request.PlantDiagnosisRequest.inspection_key": _I,
    "plant_diagnosis_request.PlantDiagnosisRequest.harvest_observation_key": _V,
    "plant_diagnosis_request.PlantDiagnosisRequest.adapter_key": _I,
    "plant_diary_entry.PlantDiaryEntry.plant_key": _V,
    "plant_instance.PlantInstance.species_key": _gap(1871, "B11"),
    "plant_instance.PlantInstance.cultivar_key": _V,
    "plant_instance.PlantInstance.site_key": _V,
    "plant_instance.PlantInstance.location_key": _V,
    "plant_instance.PlantInstance.slot_key": _V,
    "plant_instance.PlantInstance.substrate_batch_key": _V,
    "plant_instance.PlantInstance.substrate_key": _V,
    "plant_instance.PlantInstance.current_phase_key": _G,
    "plant_instance.PlantInstance.mother_key": _I,
    "planting_run.PlantingRun.current_phase_key": _I,
    "planting_run.PlantingRun.lifecycle_config_key": _G,
    "planting_run.PlantingRun.location_key": _V,
    "planting_run.PlantingRun.substrate_batch_key": _V,  # #1868
    "planting_run.PlantingRun.source_plant_key": _gap(1872, "C1"),
    "planting_run.PlantingRun.nutrient_plan_key": _V,
    "planting_run.PlantingRun.succession_plan_key": _I,
    "planting_run.PlantingRun.clone_from_run_key": _I,
    "planting_run.PlantingRunEntry.run_key": _V,  # #1867
    "planting_run.PlantingRunEntry.species_key": _gap(1871, "B11"),
    "planting_run.PlantingRunEntry.cultivar_key": _V,  # bundle A (B12): entries stamped on create
    "post_harvest.PostHarvestBatch.harvest_batch_key": _V,
    "post_harvest.PostHarvestBatch.plant_key": _I,
    "privacy.PersonalTenantErasure.tenant_erasure_record_key": _I,
    "propagation.PhenotypeNote.plant_key": _V,
    "propagation.PropagationBatch.target_planting_run_key": _gap(1872, "C3"),
    "propagation.PropagationEvent.parent_plant_keys": _gap(1872, "C2"),
    "propagation.PropagationEvent.child_plant_keys": _gap(1872, "C2"),
    "propagation.PropagationEvent.species_key": _gap(1872, "C11"),
    "propagation.PropagationEvent.cultivar_key": _V,
    "propagation.PropagationEvent.protocol_key": _gap(1872, "C2"),
    "propagation.PropagationEvent.batch_key": _gap(1872, "C2"),
    "propagation.RootingProtocol.recommended_species_keys": _gap(1872, "C12"),
    "season_state.SeasonState.site_key": _I,
    "season_state.SeasonState.trigger_reason_i18n_key": _I,
    "site.Location.site_key": _V,
    "site.Location.parent_location_key": _gap(1872, "C4"),  # create verified (bundle A, L1); update open
    "site.Location.location_type_key": _G,
    "site.Location.tank_key": _gap(1872, "C4"),
    "site.Slot.location_key": _gap(1871, "B1"),
    "species.Cultivar.species_key": _V,
    "species.Species.family_key": _G,
    "species.Species.default_nutrient_plan_key": _gap(1872, "C14"),
    "substrate.SubstrateBatch.substrate_key": _gap(1872, "C15"),
    "succession_plan.SuccessionPlan.species_key": _gap(1872, "C13"),
    "succession_plan.SuccessionPlan.cultivar_key": _V,
    "succession_plan.SuccessionPlan.location_key": _V,
    "tank.Tank.location_key": _V,  # bundle A, L3
    "task.Task.entity_key": _gap(1872, "C10"),  # guarded for the edge-writing types, incl. clone (bundle A)
    "task.Task.planting_run_key": _I,
    "task.Task.assigned_to_user_key": _gap(1871, "B9"),
    "task.Task.parent_recurring_task_key": _I,
    "task.Task.activity_key": _I,
    "task.Task.template_key": _I,
    "task.Task.workflow_execution_key": _V,
    "task.Task.watering_event_key": _I,
    "task.TaskTemplate.activity_key": _I,
    "task.TaskTemplate.workflow_template_key": _V,
    "task.TaskTemplate.workflow_phase_key": _V,
    "task.TaskTemplate.phase_definition_key": _I,
    "task.TaskTemplate.source_template_key": _I,
    "task.WorkflowTemplate.species_key": _gap(1871, "B10"),
    "task.WorkflowTemplate.lifecycle_key": _G,
    "task.WorkflowTemplate.phase_sequence_key": _I,
    "task.WorkflowTemplate.source_workflow_key": _I,
    "tenant_context.TenantContext.user_key": _N,
    "tenant_erasure.TenantErasurePlan.known_parent_keys": _I,
    "tenant_erasure.TenantErasureRecord.parent_keys": _I,
    "watering_event.WateringEvent.slot_keys": _I,
    "watering_event.WateringEvent.plant_keys": _V,
    "watering_event.WateringEvent.tank_fill_event_key": _gap(1872, "C6"),
    "watering_event.WateringEvent.nutrient_plan_key": _gap(1872, "C7"),
    "watering_event.WateringEvent.task_key": _V,  # bundle A, L8
    "watering_log.WateringLog.plant_keys": _V,
    "watering_log.WateringLog.slot_keys": _gap(1871, "B4"),
    "watering_log.WateringLog.tank_fill_event_key": _gap(1872, "C6"),
    "watering_log.WateringLog.nutrient_plan_key": _gap(1872, "C7"),
    "watering_log.WateringLog.task_key": _V,  # bundle A, L8
    "weather.ClimateNormal.site_key": _I,
    "weather.WeatherForecast.site_key": _I,
    "weather.WeatherSourceConfig.site_key": _V,
}


def _reference_fields() -> set[str]:
    import app.domain.models as models_pkg

    found: set[str] = set()
    for info in pkgutil.iter_modules(models_pkg.__path__):
        module = importlib.import_module(f"app.domain.models.{info.name}")
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if not issubclass(cls, BaseModel) or cls.__module__ != module.__name__:
                continue
            if "tenant_key" not in cls.model_fields:
                continue
            for field in cls.model_fields:
                if field != "tenant_key" and (field.endswith("_key") or field.endswith("_keys")):
                    found.add(f"{info.name}.{name}.{field}")
    return found


def _bound_model(cls: type) -> type | None:
    """The Pydantic model a repository binds — ``_model_cls`` or ``BaseArangoRepository[Model]``."""
    model = cls.__dict__.get("_model_cls")
    if isinstance(model, type):
        return model
    for base in getattr(cls, "__orig_bases__", ()):
        for arg in getattr(base, "__args__", ()):
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                return arg
    return None


def _owned_reference_declarations() -> set[str]:
    """``module.Model.field`` for every field a repository declares as an owned reference."""
    import app.data_access as data_access_pkg

    declared: set[str] = set()
    for info in pkgutil.walk_packages(data_access_pkg.__path__, prefix="app.data_access."):
        module = importlib.import_module(info.name)
        for _name, cls in inspect.getmembers(module, inspect.isclass):
            fields = cls.__dict__.get("_owned_reference_fields")
            if not fields:
                continue
            model = _bound_model(cls)
            assert model is not None, f"{cls.__qualname__} declares owned references but binds no model"
            short = model.__module__.rsplit(".", 1)[-1]
            declared.update(f"{short}.{model.__name__}.{field}" for field in fields)
    return declared


def test_every_reference_field_of_a_tenant_owned_model_is_classified() -> None:
    found = _reference_fields()
    unclassified = sorted(found - set(_REFERENCE_FIELDS))
    vanished = sorted(set(_REFERENCE_FIELDS) - found)

    assert len(found) > 120, len(found)  # non-vacuity: the model scan reaches the domain models
    assert unclassified == [], (
        "a tenant-owned model stores another entity's key and nobody decided whether it is resolved "
        f"under the tenant — classify it (verified/global/internal/actor/not-persisted/gap): {unclassified}"
    )
    assert vanished == [], f"classified fields that no longer exist — drop the entry: {vanished}"


def test_every_open_gap_names_an_open_issue_item() -> None:
    gaps = {field: value for field, value in _REFERENCE_FIELDS.items() if value.startswith("gap:")}

    assert gaps, "the register carries the open hits of #1871/#1872"
    assert all(value.split(":")[1] in {"#1871", "#1872"} for value in gaps.values()), gaps


def test_a_gap_declared_as_an_owned_reference_is_reported_as_stale() -> None:
    declared = _owned_reference_declarations()

    # Non-vacuity: the declarations that exist today are found (plant_key on
    # feeding events, cultivar_key on plant instances …), so an empty scan fails.
    assert {"feeding_event.FeedingEvent.plant_key", "plant_instance.PlantInstance.cultivar_key"} <= declared, declared
    stale = sorted(
        field for field, value in _REFERENCE_FIELDS.items() if value.startswith("gap:") and field in declared
    )

    assert stale == [], f"these open gaps are now verified by a repository — reclassify them: {stale}"
