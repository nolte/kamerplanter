from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request

from app.api.mapping import to_response
from app.api.v1.auth.router import limiter, user_rate_limit_key
from app.api.v1.locations.schemas import (
    BedListItemResponse,
    BedSummaryResponse,
    FrostWarningResponse,
    LocationCreate,
    LocationPatch,
    LocationPatchResponse,
    LocationResponse,
    LocationStatusRequest,
    PlantingLayoutPreviewRequest,
    PlantingLayoutPreviewResponse,
    PlantingLayoutSlotResponse,
    PlantingLayoutWarningResponse,
)
from app.api.v1.slots.schemas import SlotBatchRequest, SlotBatchResponse
from app.api.v1.tanks.schemas import LiveStateResponse, SensorCreate, SensorResponse, SensorUpdate
from app.common.auth import get_current_tenant, require_permission
from app.common.dependencies import get_garden_resource_service, get_sensor_service, get_site_service
from app.common.enums import BedStatus
from app.common.openapi_responses import (
    CONFLICT_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    VALIDATION_RESPONSE,
)
from app.config.settings import settings
from app.core.permissions import Action, ResourceType
from app.domain.calculators.planting_layout_calculator import EntryLayout
from app.domain.models.sensor import Sensor
from app.domain.models.site import Location
from app.domain.models.tenant_context import TenantContext
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.sensor_service import SensorService
from app.domain.services.site_service import SiteService

router = APIRouter(prefix="/locations", tags=["locations"], responses=NOT_FOUND_RESPONSE)


def _verify_location_tenant(key: str, ctx: TenantContext, service: SiteService) -> Location:
    """The location ``key`` if its site is the tenant's, else 404 as ``Location`` (#1871 B13).

    Resolved in one step through the parent site. The two-step form (location
    unscoped, then its site) answered a foreign location with ``No Site with key
    '<the other tenant's site>'`` and an unknown one with ``No Location`` — an
    existence oracle that echoed the other tenant's site key.
    """
    return service.get_location(key, tenant_key=ctx.tenant_key)


@router.get("", response_model=list[BedListItemResponse])
def list_locations(
    site_key: str = Query(..., description="Document key of the site to list locations for."),
    parent_location_key: str | None = Query(
        None, description="If set, list the child locations of this parent instead."
    ),
    is_bed: bool | None = Query(
        None, description="Only locations whose type is (true) or is not (false) a bed; adds the counters (GP-API-011)."
    ),
    bed_status: BedStatus | None = Query(None, description="Only beds in this status; adds the counters (GP-API-011)."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
    resources: GardenResourceService = Depends(get_garden_resource_service),
):
    """List a site's locations, or the children of a parent location.

    With ``is_bed`` or ``bed_status`` the rows carry ``active_plant_count``, ``open_task_count`` and
    ``next_due_at`` (GP-API-011).
    """
    if is_bed is not None or bed_status is not None:
        rows = resources.list_beds(site_key, tenant_key=ctx.tenant_key, is_bed=is_bed, bed_status=bed_status)
        if parent_location_key:
            rows = [(loc, counters) for loc, counters in rows if loc.parent_location_key == parent_location_key]
        return [
            to_response(
                loc,
                BedListItemResponse,
                active_plant_count=counters.active_plant_count if counters else None,
                open_task_count=counters.open_task_count if counters else None,
                overdue_task_count=counters.overdue_task_count if counters else None,
                next_due_at=counters.next_due_at if counters else None,
            )
            for loc, counters in rows
        ]
    service.get_site(site_key, tenant_key=ctx.tenant_key)
    if parent_location_key:
        # The parent is resolved under the tenant too (#1871 B14): checking only
        # the site listed the children of any tenant's location. The service does
        # it itself since #2107.
        items = service.list_location_children(parent_location_key, tenant_key=ctx.tenant_key)
    else:
        items = service.list_locations(site_key, tenant_key=ctx.tenant_key)
    return [to_response(loc, BedListItemResponse) for loc in items]


@router.get("/{key}", response_model=LocationResponse)
def get_location(
    key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    """Return a single location by key."""
    loc = _verify_location_tenant(key, ctx, service)
    return to_response(loc, LocationResponse)


@router.get("/{key}/children", response_model=list[LocationResponse])
def list_location_children(
    key: Annotated[str, Path(description="Document key of the parent location.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
):
    """List the child locations of a location."""
    items = service.list_location_children(key, tenant_key=ctx.tenant_key)
    return [to_response(loc, LocationResponse) for loc in items]


@router.post("", response_model=LocationResponse, status_code=201)
def create_location(
    body: LocationCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.CREATE)),
    service: SiteService = Depends(get_site_service),
):
    """Create a location within a site."""
    location = Location(**body.model_dump())
    created = service.create_location(location, tenant_key=ctx.tenant_key)
    return to_response(created, LocationResponse)


@router.put("/{key}", response_model=LocationResponse)
def update_location(
    key: Annotated[str, Path(description="Document key of the location.")],
    body: LocationCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: SiteService = Depends(get_site_service),
):
    """Update a location."""
    location = Location(**body.model_dump())
    updated = service.update_location(key, location, tenant_key=ctx.tenant_key)
    return to_response(updated, LocationResponse)


@router.patch(
    "/{key}",
    response_model=LocationPatchResponse,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
def patch_location(
    key: Annotated[str, Path(description="Document key of the location.")],
    body: LocationPatch,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> LocationPatchResponse:
    """Change the fields present in the body (GP-API-010).

    A new geometry goes through the plan's rules (containment, overlap, lock) and raises the site's
    ``plan_revision``; the other fields do not (GP-NFR-007). ``bed_status`` is a transition (V-10): 422
    ``bed_status.invalid_transition``, and ``retired`` needs ``status_reason`` and the lead role.
    """
    stored, revision = service.patch_location(
        key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role, patch=body
    )
    return to_response(stored, LocationPatchResponse, plan_revision=revision)


@router.get("/{key}/summary", response_model=BedSummaryResponse)
def get_location_summary(
    key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> BedSummaryResponse:
    """The head data of the bed view: area, type, status, soil, sun, plants, tasks, last care (GP-API-012)."""
    view = service.get_summary(key, tenant_key=ctx.tenant_key)
    counters = view.counters
    return to_response(
        view.location,
        BedSummaryResponse,
        is_bed=view.is_bed,
        season_state=view.season_state,
        active_plant_count=counters.active_plant_count,
        species_keys=counters.species_keys,
        open_task_count=counters.open_task_count,
        overdue_task_count=counters.overdue_task_count,
        next_due_at=counters.next_due_at,
        last_care_at=counters.last_care_at,
    )


@router.post(
    "/{key}/status",
    response_model=LocationPatchResponse,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
def change_location_status(
    key: Annotated[str, Path(description="Document key of the bed.")],
    body: LocationStatusRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> LocationPatchResponse:
    """Move a bed through its lifecycle and log it as a care event (GP-API-018, GP-FR-046).

    Allowed: ``planned`` to ``active`` or ``retired``, ``active`` to ``retired``, ``retired`` to ``active``;
    anything else is 422 ``bed_status.invalid_transition`` (V-10). ``retired`` and the reactivation are the
    lead's; ``retired`` needs ``reason`` and a bed without plants (409 ``location.has_active_plants``, V-09).
    """
    stored, revision = service.change_bed_status(
        key,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        role=ctx.role,
        bed_status=body.bed_status,
        reason=body.reason,
    )
    return to_response(stored, LocationPatchResponse, plan_revision=revision)


@router.delete("/{key}", status_code=204, responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE})
def delete_location(
    key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.DELETE)),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> None:
    """Delete a location with its slots and everything below it (lead only).

    409 ``location.has_active_plants`` with ``details[0].active_plant_count`` while a plant stands in it
    (V-09, GP-ACC-012); the deletion is audited and raises the site's ``plan_revision``.
    """
    service.delete_location(key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role)


@router.post(
    "/{key}/slots/batch",
    response_model=SlotBatchResponse,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_plan_batch, key_func=user_rate_limit_key)
def apply_slot_batch(
    request: Request,
    key: Annotated[str, Path(description="Document key of the bed.")],
    body: SlotBatchRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> SlotBatchResponse:
    """Replace the bed's unoccupied slots or append to them, in one transaction (GP-API-015).

    Outside the plan revision (GP-NFR-007). V-04 ``slot.outside_bed``, V-06 ``slot.overlap`` and V-20
    (``slot.duplicate_id``) refuse the whole batch; at most 2 000 positions (``layout.too_many_positions``).
    """
    result = service.replace_slots(key, tenant_key=ctx.tenant_key, role=ctx.role, request=body)
    return SlotBatchResponse(
        created_keys=result.created_keys, deleted_count=result.deleted_count, kept_count=result.kept_count
    )


@router.post(
    "/{key}/planting-layout/preview",
    response_model=PlantingLayoutPreviewResponse,
    responses={**VALIDATION_RESPONSE},
)
def preview_planting_layout(
    key: Annotated[str, Path(description="Document key of the bed.")],
    body: PlantingLayoutPreviewRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.READ)),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> PlantingLayoutPreviewResponse:
    """Where an entry's plants would stand in the bed, without persisting anything (GP-API-016, GP-FR-063).

    Slots are in the bed frame (§9.2). 422 ``layout.too_many_positions {estimated, limit}`` when the
    area-based pre-estimate exceeds 2 000 positions (GP-FR-062); that check runs before a point exists.
    ``warnings`` carry hints only: spacing below 70 % of the mature width, positions closer than
    ``spacing_cm`` (V-07), nothing fits, a zone margin that could not be applied. The server answer is
    authoritative over the client-side preview (GP-FR-063).
    """
    entry = body.entry
    layout = EntryLayout(
        layout_strategy=entry.layout_strategy,
        spacing_cm=entry.spacing_cm,
        row_spacing_cm=entry.row_spacing_cm,
        row_direction=entry.row_direction,
        edge_margin_along_cm=entry.edge_margin_along_cm,
        edge_margin_across_cm=entry.edge_margin_across_cm,
        row_assignment=None if entry.row_assignment is None else tuple(entry.row_assignment),
        mature_width_cm=entry.mature_width_cm,
    )
    result = service.preview_planting_layout(key, tenant_key=ctx.tenant_key, entry=layout, max_count=entry.max_count)
    slots = [
        PlantingLayoutSlotResponse.model_validate(
            {
                "slot_role": slot.slot_role,
                "geometry": (
                    {"kind": "point", "origin": list(slot.point)}
                    if slot.point is not None
                    else {"kind": "polygon", "points": [list(p) for p in slot.outline or ()]}
                ),
                "row_index": slot.row_index,
                "sequence": slot.sequence,
                "capacity_plants": slot.capacity_plants,
            }
        )
        for slot in result.slots
    ]
    return PlantingLayoutPreviewResponse(
        slots=slots,
        count=result.count,
        capacity_max=result.capacity_max,
        warnings=[PlantingLayoutWarningResponse(code=w.code, detail=w.detail) for w in result.warnings],
    )


# ── Sensors ──────────────────────────────────────────────────────────


@router.get("/{key}/sensors", response_model=list[SensorResponse])
def get_location_sensors(
    key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    """List the sensors attached to a location."""
    _verify_location_tenant(key, ctx, service)
    sensors = sensor_service.get_sensors_for_location(key)
    return [to_response(s, SensorResponse) for s in sensors]


@router.post("/{key}/sensors", response_model=SensorResponse, status_code=201)
def create_location_sensor(
    key: Annotated[str, Path(description="Document key of the location.")],
    body: SensorCreate,
    ctx: TenantContext = Depends(require_permission(ResourceType.SENSOR, Action.CREATE)),
    service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    """Attach a sensor to a location."""
    _verify_location_tenant(key, ctx, service)
    sensor = Sensor(
        name=body.name,
        metric_type=body.metric_type,
        ha_entity_id=body.ha_entity_id,
        mqtt_topic=body.mqtt_topic,
        location_key=key,
    )
    created = sensor_service.create_sensor(sensor, tenant_key=ctx.tenant_key)
    return to_response(created, SensorResponse)


@router.put("/{key}/sensors/{sensor_key}", response_model=SensorResponse)
def update_location_sensor(
    key: Annotated[str, Path(description="Document key of the location.")],
    sensor_key: Annotated[str, Path(description="Document key of the sensor.")],
    body: SensorUpdate,
    ctx: TenantContext = Depends(require_permission(ResourceType.SENSOR, Action.UPDATE)),
    service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    """Update a sensor attached to a location (REQ-005 §2, #1339).

    Scoped by the location on purpose: a sensor carries no ``tenant_key``, and
    neither does a location — the tenant anchor is the location's site, which
    ``_verify_location_tenant`` resolves. The service then refuses a sensor that
    hangs off anything but this location.
    """
    _verify_location_tenant(key, ctx, service)
    updated = sensor_service.update_sensor(
        sensor_key,
        # `exclude_unset`, not `exclude_none`: an explicit `null` is how the
        # client *clears* `ha_entity_id` / `mqtt_topic` / `unit_of_measurement`,
        # and `exclude_none` dropped exactly those keys — the write returned 200
        # and kept the old value (#1339 review).
        body.model_dump(exclude_unset=True),
        parent_field="location_key",
        parent_key=key,
        tenant_key=ctx.tenant_key,
    )
    return to_response(updated, SensorResponse)


@router.delete("/{key}/sensors/{sensor_key}", status_code=204)
def delete_location_sensor(
    key: Annotated[str, Path(description="Document key of the location.")],
    sensor_key: Annotated[str, Path(description="Document key of the sensor.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.SENSOR, Action.DELETE)),
    service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    """Delete a sensor of a location, with its edges (REQ-005 §2, #1339)."""
    _verify_location_tenant(key, ctx, service)
    sensor_service.delete_sensor(sensor_key, parent_field="location_key", parent_key=key, tenant_key=ctx.tenant_key)


@router.get("/{key}/sensors/live", response_model=LiveStateResponse)
def get_location_sensors_live(
    key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    """Return the latest live readings for a location's sensors."""
    _verify_location_tenant(key, ctx, service)
    sensors = sensor_service.get_sensors_for_location(key)
    result = sensor_service.get_live_state_for_sensors(sensors, tenant_key=ctx.tenant_key)
    return LiveStateResponse(**result)


@router.get("/{key}/frost-warning", response_model=FrostWarningResponse)
def get_location_frost_warning(
    key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: SiteService = Depends(get_site_service),
    sensor_service: SensorService = Depends(get_sensor_service),
):
    """Reactive frost-warning state for a location (Home Assistant read path).

    Backs ``binary_sensor.kp_{location}_frost_warning``: the HA coordinator
    learns which locations to surface from ``/ha-publish/enabled-keys/location``
    (opt-in) and polls this route per location. The reactive ``frost_warning`` is
    derived from the location's latest ambient temperature; it is ``null`` when no
    temperature reading is available.

    The proactive forecast early-warning is served once per site — not per
    location — via ``GET /sites/{site_key}/weather-forecast`` (Issue #409, F1), so
    a site with N locations no longer triggers N identical forecast reads on this
    hot path.
    """
    _verify_location_tenant(key, ctx, service)
    result = sensor_service.get_location_frost_warning(key, tenant_key=ctx.tenant_key)
    return FrostWarningResponse(**result)
