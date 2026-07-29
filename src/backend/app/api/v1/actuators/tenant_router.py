"""REQ-018 Environment-control tenant-scoped router.

Mounted under ``/t/{tenant_slug}``. Every endpoint resolves the tenant via
:func:`get_current_tenant`; the service verifies actuator/location ownership
against ``tenant_key`` before any child resource is touched (SEC-B4).

Auth (REQ-018 §4): reads require membership, state-changing writes (create,
command, override, rules, schedules, emergency-stop) require GROWER, and
actuator deletion requires ADMIN.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.actuators.schemas import (
    ActuatorCreate,
    ActuatorEventStatsResponse,
    ActuatorResponse,
    ActuatorStateResponse,
    ActuatorUpdate,
    ApplyProfileRequest,
    CommandRequest,
    ControlEventResponse,
    EmergencyStopRequest,
    EmergencyStopResponse,
    OverrideCreate,
    OverrideCreatedResponse,
    PhaseControlProfileCreate,
    PhaseControlProfileResponse,
    PhaseControlProfileUpdate,
    RuleCreate,
    RuleResponse,
    RuleTestRequest,
    RuleTestResponse,
    RuleUpdate,
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)
from app.common.auth import get_current_tenant, require_tenant_role
from app.common.dependencies import get_actuator_service
from app.common.enums import TenantRole
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.actuator import (
    Actuator,
    ControlRule,
    ControlSchedule,
    ManualOverride,
    PhaseControlProfile,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.actuator_service import ActuatorService

router = APIRouter(tags=["actuators"], responses=NOT_FOUND_RESPONSE)


# ── Actuators CRUD ───────────────────────────────────────────────────────


@router.post("/locations/{location_key}/actuators", response_model=ActuatorResponse, status_code=201)
def create_actuator(
    location_key: Annotated[str, Path(description="Document key of the location.")],
    body: ActuatorCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Create an actuator attached to a location."""
    actuator = Actuator(**body.model_dump())
    created = service.create_actuator(location_key, ctx.tenant_key, actuator)
    return to_response(created, ActuatorResponse)


@router.get("/locations/{location_key}/actuators", response_model=list[ActuatorResponse])
def list_location_actuators(
    location_key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """List the actuators attached to a location."""
    actuators = service.list_for_location(location_key, ctx.tenant_key)
    return [to_response(a, ActuatorResponse) for a in actuators]


@router.get("/actuators", response_model=list[ActuatorResponse])
def list_actuators(
    actuator_type: str | None = Query(default=None, description="Filter by actuator type."),
    protocol: str | None = Query(default=None, description="Filter by control protocol."),
    is_online: bool | None = Query(default=None, description="Filter by online/offline state."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """List all of the tenant's actuators, optionally filtered."""
    actuators = service.list_for_tenant(ctx.tenant_key, actuator_type, protocol, is_online)
    return [to_response(a, ActuatorResponse) for a in actuators]


@router.get("/actuators/{actuator_key}", response_model=ActuatorResponse)
def get_actuator(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Return a single actuator by key."""
    return to_response(service.get_actuator(actuator_key, ctx.tenant_key), ActuatorResponse)


@router.put("/actuators/{actuator_key}", response_model=ActuatorResponse)
def update_actuator(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    body: ActuatorUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Update an actuator's configuration."""
    updated = service.update_actuator(actuator_key, ctx.tenant_key, body.model_dump(exclude_none=True))
    return to_response(updated, ActuatorResponse)


@router.delete("/actuators/{actuator_key}", status_code=204)
def delete_actuator(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.LEAD)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Delete an actuator."""
    service.delete_actuator(actuator_key, ctx.tenant_key)


# ── Command & override ───────────────────────────────────────────────────


@router.post("/actuators/{actuator_key}/command", response_model=ControlEventResponse, status_code=201)
def send_command(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    body: CommandRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Send a manual command to an actuator."""
    event = service.send_command(actuator_key, ctx.tenant_key, body.command, body.value, user=ctx.user_key)
    return to_response(event, ControlEventResponse)


@router.post("/actuators/{actuator_key}/override", response_model=OverrideCreatedResponse, status_code=201)
def set_override(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    body: OverrideCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Set a manual override on an actuator, suspending automatic control."""
    from datetime import UTC, datetime

    override = ManualOverride(
        started_at=datetime.now(UTC),
        expires_at=body.expires_at,
        override_value=body.override_value,
        override_state=body.override_state,
        reason=body.reason,
        created_by=ctx.user_key,
    )
    created = service.set_override(actuator_key, ctx.tenant_key, override, ctx.user_key)
    return {"key": created.key, "expires_at": created.expires_at, "is_active": created.is_active}


@router.delete("/actuators/{actuator_key}/override", status_code=204)
def clear_override(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Clear an actuator's manual override."""
    service.clear_override(actuator_key, ctx.tenant_key)


@router.get("/actuators/{actuator_key}/state", response_model=ActuatorStateResponse)
def get_actuator_state(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Return an actuator's current state snapshot."""
    return service.get_state(actuator_key, ctx.tenant_key)


# ── Schedules ────────────────────────────────────────────────────────────


@router.post("/actuators/{actuator_key}/schedules", response_model=ScheduleResponse, status_code=201)
def create_schedule(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    body: ScheduleCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Create a control schedule for an actuator."""
    schedule = ControlSchedule(**body.model_dump())
    created = service.create_schedule(actuator_key, ctx.tenant_key, schedule)
    return to_response(created, ScheduleResponse)


@router.get("/actuators/{actuator_key}/schedules", response_model=list[ScheduleResponse])
def list_schedules(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """List an actuator's control schedules."""
    schedules = service.list_schedules(actuator_key, ctx.tenant_key)
    return [to_response(s, ScheduleResponse) for s in schedules]


@router.put("/actuators/{actuator_key}/schedules/{schedule_key}", response_model=ScheduleResponse)
def update_schedule(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    schedule_key: Annotated[str, Path(description="Document key of the control schedule.")],
    body: ScheduleUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Update a control schedule of an actuator."""
    updated = service.update_schedule(actuator_key, schedule_key, ctx.tenant_key, body.model_dump(exclude_none=True))
    return to_response(updated, ScheduleResponse)


@router.delete("/actuators/{actuator_key}/schedules/{schedule_key}", status_code=204)
def delete_schedule(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    schedule_key: Annotated[str, Path(description="Document key of the control schedule.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Delete a control schedule of an actuator."""
    service.delete_schedule(actuator_key, schedule_key, ctx.tenant_key)


@router.post("/actuators/{actuator_key}/schedules/{schedule_key}/toggle", response_model=ScheduleResponse)
def toggle_schedule(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    schedule_key: Annotated[str, Path(description="Document key of the control schedule.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Toggle a control schedule's active state."""
    return to_response(service.toggle_schedule(actuator_key, schedule_key, ctx.tenant_key), ScheduleResponse)


# ── Rules ────────────────────────────────────────────────────────────────


@router.post("/actuators/{actuator_key}/rules", response_model=RuleResponse, status_code=201)
def create_rule(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    body: RuleCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Create a sensor-driven control rule for an actuator."""
    rule = ControlRule(**body.model_dump())
    created = service.create_rule(actuator_key, ctx.tenant_key, rule)
    return to_response(created, RuleResponse)


@router.get("/actuators/{actuator_key}/rules", response_model=list[RuleResponse])
def list_actuator_rules(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """List an actuator's control rules."""
    rules = service.list_rules(actuator_key, ctx.tenant_key)
    return [to_response(r, RuleResponse) for r in rules]


@router.get("/rules", response_model=list[RuleResponse])
def list_rules(
    sensor_parameter: str | None = Query(default=None, description="Filter by driving sensor parameter."),
    is_active: bool | None = Query(default=None, description="Filter by active/inactive state."),
    is_safety: bool | None = Query(default=None, description="Filter by safety-rule flag."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """List all of the tenant's control rules, optionally filtered."""
    rules = service.list_rules_for_tenant(ctx.tenant_key, sensor_parameter, is_active, is_safety)
    return [to_response(r, RuleResponse) for r in rules]


@router.put("/actuators/{actuator_key}/rules/{rule_key}", response_model=RuleResponse)
def update_rule(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    rule_key: Annotated[str, Path(description="Document key of the control rule.")],
    body: RuleUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Update a control rule of an actuator."""
    updated = service.update_rule(actuator_key, rule_key, ctx.tenant_key, body.model_dump(exclude_none=True))
    return to_response(updated, RuleResponse)


@router.delete("/actuators/{actuator_key}/rules/{rule_key}", status_code=204)
def delete_rule(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    rule_key: Annotated[str, Path(description="Document key of the control rule.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Delete a control rule of an actuator."""
    service.delete_rule(actuator_key, rule_key, ctx.tenant_key)


@router.post("/actuators/{actuator_key}/rules/{rule_key}/toggle", response_model=RuleResponse)
def toggle_rule(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    rule_key: Annotated[str, Path(description="Document key of the control rule.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Toggle a control rule's active state."""
    return to_response(service.toggle_rule(actuator_key, rule_key, ctx.tenant_key), RuleResponse)


@router.post("/rules/{rule_key}/test", response_model=RuleTestResponse, response_model_exclude_unset=True)
def test_rule(
    rule_key: Annotated[str, Path(description="Document key of the control rule.")],
    body: RuleTestRequest,
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Dry-run a control rule against supplied sensor readings, without side effects."""
    return service.test_rule(rule_key, ctx.tenant_key, body.sensor_readings)


# ── Events & stats ───────────────────────────────────────────────────────


@router.get("/actuators/{actuator_key}/events", response_model=list[ControlEventResponse])
def list_events(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """List an actuator's control events (paginated, newest first)."""
    events = service.list_events(actuator_key, ctx.tenant_key, pagination.offset, pagination.limit)
    return [to_response(e, ControlEventResponse) for e in events]


@router.get("/actuators/{actuator_key}/events/stats", response_model=ActuatorEventStatsResponse)
def get_event_stats(
    actuator_key: Annotated[str, Path(description="Document key of the actuator.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Return aggregated control-event statistics for an actuator."""
    return service.get_event_stats(actuator_key, ctx.tenant_key)


@router.get("/locations/{location_key}/control-events", response_model=list[ControlEventResponse])
def list_location_events(
    location_key: Annotated[str, Path(description="Document key of the location.")],
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """List control events across all actuators of a location (paginated)."""
    events = service.list_location_events(location_key, ctx.tenant_key, pagination.offset, pagination.limit)
    return [to_response(e, ControlEventResponse) for e in events]


@router.get("/locations/{location_key}/control-status")
def get_location_control_status(
    location_key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Return an actuator online/offline summary for a location."""
    actuators = service.list_for_location(location_key, ctx.tenant_key)
    return {
        "location_key": location_key,
        "actuator_count": len(actuators),
        "online": sum(1 for a in actuators if a.is_online),
        "actuators": [to_response(a, ActuatorResponse).model_dump(by_alias=True) for a in actuators],
    }


@router.get("/locations/{location_key}/energy")
def get_location_energy(
    location_key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Return the estimated daily energy use for a location's actuators."""
    return service.get_location_energy(location_key, ctx.tenant_key)


# ── Phase control profiles ───────────────────────────────────────────────


@router.post("/phase-control-profiles", response_model=PhaseControlProfileResponse, status_code=201)
def create_profile(
    body: PhaseControlProfileCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Create a phase-control profile of environmental targets."""
    profile = PhaseControlProfile(**body.model_dump())
    created = service.create_profile(ctx.tenant_key, profile)
    return to_response(created, PhaseControlProfileResponse)


@router.get("/phase-control-profiles", response_model=list[PhaseControlProfileResponse])
def list_profiles(
    is_template: bool | None = Query(default=None, description="Filter by template flag."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """List the tenant's phase-control profiles."""
    profiles = service.list_profiles(ctx.tenant_key, is_template)
    return [to_response(p, PhaseControlProfileResponse) for p in profiles]


@router.get("/phase-control-profiles/{profile_key}", response_model=PhaseControlProfileResponse)
def get_profile(
    profile_key: Annotated[str, Path(description="Document key of the phase-control profile.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Return a single phase-control profile by key."""
    return to_response(service.get_profile(profile_key, ctx.tenant_key), PhaseControlProfileResponse)


@router.put("/phase-control-profiles/{profile_key}", response_model=PhaseControlProfileResponse)
def update_profile(
    profile_key: Annotated[str, Path(description="Document key of the phase-control profile.")],
    body: PhaseControlProfileUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Update a phase-control profile."""
    updated = service.update_profile(profile_key, ctx.tenant_key, body.model_dump(exclude_none=True))
    return to_response(updated, PhaseControlProfileResponse)


@router.delete("/phase-control-profiles/{profile_key}", status_code=204)
def delete_profile(
    profile_key: Annotated[str, Path(description="Document key of the phase-control profile.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Delete a phase-control profile."""
    service.delete_profile(profile_key, ctx.tenant_key)


@router.post("/phase-control-profiles/{profile_key}/apply")
def apply_profile(
    profile_key: Annotated[str, Path(description="Document key of the phase-control profile.")],
    body: ApplyProfileRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Apply a phase-control profile's targets to a location's actuators."""
    return service.apply_profile(profile_key, ctx.tenant_key, body.location_key)


# ── Home Assistant integration (admin-gated) ─────────────────────────────


@router.get("/integrations/home-assistant/status")
def ha_status(
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.LEAD)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Return the Home Assistant integration connection status."""
    return service.ha_status()


@router.get("/integrations/home-assistant/entities")
def ha_entities(
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.LEAD)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """List the controllable Home Assistant entities."""
    return service.ha_entities()


@router.post("/integrations/home-assistant/test")
def ha_test(
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.LEAD)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Test the Home Assistant integration connection."""
    return service.ha_status()


# ── Emergency stop ───────────────────────────────────────────────────────


@router.post("/emergency-stop", response_model=EmergencyStopResponse)
def emergency_stop(
    body: EmergencyStopRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: ActuatorService = Depends(get_actuator_service),
):
    """Switch off the actuators affected by a predefined emergency scenario."""
    return service.emergency_stop(ctx.tenant_key, body.scenario.value, ctx.user_key)
