from dataclasses import asdict
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request

from app.api.mapping import to_response
from app.api.v1.auth.router import limiter, user_rate_limit_key
from app.api.v1.locations.schemas import (
    BackfillRequest,
    BackfillResponse,
    BedHistoryItemResponse,
    BedListItemResponse,
    BedSummaryResponse,
    ClearBedRequest,
    ClearBedResponse,
    FrostWarningResponse,
    LocationCreate,
    LocationPatch,
    LocationPatchResponse,
    LocationResponse,
    LocationStatusRequest,
    NeighbourHintResponse,
    PlantingItemResponse,
    PlantingLayoutPreviewRequest,
    PlantingLayoutPreviewResponse,
    PlantStateResponse,
    QuickPlantingRequest,
    QuickPlantingResponse,
    RotationFindingResponse,
    RotationPlantingResponse,
    RotationTimelineResponse,
    RotationYearResponse,
    ValidatePlantingRequest,
    ValidatePlantingResponse,
)
from app.api.v1.slots.schemas import SlotBatchRequest, SlotBatchResponse
from app.api.v1.tanks.schemas import LiveStateResponse, SensorCreate, SensorResponse, SensorUpdate
from app.common.auth import get_current_tenant, require_permission
from app.common.datetimes import utc_range
from app.common.dependencies import (
    get_bed_history_service,
    get_bed_rotation_service,
    get_garden_resource_service,
    get_plant_state_service,
    get_planting_reservation_service,
    get_planting_run_service,
    get_sensor_service,
    get_site_service,
)
from app.common.enums import BedStatus
from app.common.exceptions import ValidationError
from app.common.openapi_responses import (
    CONFLICT_RESPONSE,
    FORBIDDEN_RESPONSE,
    NOT_FOUND_RESPONSE,
    VALIDATION_RESPONSE,
)
from app.common.pagination import PaginationParams, get_pagination
from app.config.constants import MAX_ROTATION_TIMELINE_YEARS
from app.config.settings import settings
from app.core.permissions import Action, ResourceType
from app.domain.interfaces.bed_history_repository import BedHistoryFilter
from app.domain.models.care_event import CARE_EVENT_CATEGORIES
from app.domain.models.sensor import Sensor
from app.domain.models.site import Location
from app.domain.models.tenant_context import TenantContext
from app.domain.services.bed_history_service import BedHistoryService
from app.domain.services.bed_rotation_service import BedRotationService
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.plant_state_service import PlantStateService
from app.domain.services.planting_reservation_service import PlantingReservationService
from app.domain.services.planting_run_service import PlantingRunService
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
    ``rotation_enabled`` switches the crop-rotation check of this bed on (``true``), off (``false``) or back to the
    type default (``null``; off for planter/tent/shelf, GP-FR-137); with ``rotation_exempt`` true (sent or stored)
    a switch-on is 422 ``patch.rotation_exempt_and_enabled``.
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
    result = service.preview_planting_layout(
        key, tenant_key=ctx.tenant_key, entry=body.entry.to_layout(), max_count=body.entry.max_count
    )
    return PlantingLayoutPreviewResponse.from_result(result)


@router.get("/{key}/plantings", response_model=list[PlantingItemResponse])
def list_plantings(
    key: Annotated[str, Path(description="Document key of the bed.")],
    state: Annotated[
        str | None,
        Query(description="`planned`, `active`, `harvested` or `historical` (§11.3); all states when omitted."),
    ] = None,
    year: Annotated[
        int | None, Query(ge=1900, le=2200, description="Only plantings whose time window touches this year.")
    ] = None,
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantingReservationService = Depends(get_planting_reservation_service),
) -> list[PlantingItemResponse]:
    """The planned positions and the plants of a bed by state (GP-API-024, §11.3), all roles.

    `planned`: a reservation (`run_planned_at`) of a live run with no plant of that run in the slot yet.
    `active`: a plant that stands. `harvested`: a plant that ended by harvest. `historical`: any plant that
    has been removed. 422 `plantings.unknown_state` for another value of `state`.
    """
    rows = service.list_plantings(
        key,
        tenant_key=ctx.tenant_key,
        state=state,
        year=year,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    return [PlantingItemResponse.from_row(row) for row in rows]


@router.get("/{key}/plant-states", response_model=list[PlantStateResponse])
def list_plant_states(
    key: Annotated[str, Path(description="Document key of the bed.")],
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PlantStateService = Depends(get_plant_state_service),
) -> list[PlantStateResponse]:
    """The standing plants of a bed with their visual state and the facts of the info bubble (GP-API-054), all roles.

    One request per bed instead of one per plant (GP-FR-191): the plan draws the marker channels and answers
    hover, focus and tap from this list. Ordered by plant key; `limit` is at most 200 and a client pages until a
    page comes back shorter. Only the fields of the plant info are returned — no notes, no user names.
    """
    entries = service.list_plant_states(
        key, tenant_key=ctx.tenant_key, offset=pagination.offset, limit=pagination.limit
    )
    return [PlantStateResponse.from_entry(entry) for entry in entries]


@router.post(
    "/{key}/clear",
    response_model=ClearBedResponse,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_bed_actions, key_func=user_rate_limit_key)
def clear_location(
    request: Request,
    key: Annotated[str, Path(description="Document key of the bed.")],
    body: ClearBedRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: PlantingReservationService = Depends(get_planting_reservation_service),
) -> ClearBedResponse:
    """Clear the bed at the end of the season (GP-API-019, GP-FR-055): one transaction.

    Every standing plant gets `removed_on` = today and the chosen `termination_type`, every active or
    harvesting run ends (`completed`, or `cancelled` for `cancelled`), the slots they used become history
    (`archived_at`) unless a later run has reserved them, and a `clearing` care event is written. Planned runs
    keep their reservations. Archived slots block neither V-06 nor V-08.
    """
    outcome = service.clear_bed(
        key,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        role=ctx.role,
        termination_type=body.termination_type,
        reason=body.reason,
    )
    return ClearBedResponse(
        plants_removed=outcome.plants_removed,
        runs_completed=outcome.runs_completed,
        slots_archived=outcome.slots_archived,
        slots_released=outcome.slots_released,
        care_event_key=outcome.care_event_key,
    )


@router.post(
    "/{key}/quick-planting",
    response_model=QuickPlantingResponse,
    status_code=201,
    responses={**FORBIDDEN_RESPONSE, **CONFLICT_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_bed_actions, key_func=user_rate_limit_key)
def quick_plant(
    request: Request,
    key: Annotated[str, Path(description="Document key of the bed.")],
    body: QuickPlantingRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.PLANT, Action.CREATE)),
    service: PlantingRunService = Depends(get_planting_run_service),
) -> QuickPlantingResponse:
    """Field-mode shortcut: *I planted n of this species here* (GP-API-017, GP-UX-027).

    Run, entry, slots and plants are created in one transaction outside the plan revision; the run is
    `active` with `source = field_mode`. At most 500 plants (422 `plan.quota_exceeded`). With
    `layout_strategy` and `spacing_cm` on a bed with geometry the plants stand on a computed layout; otherwise,
    or beyond what the bed holds, they are recorded without a position and `warnings` says why.
    """
    result = service.quick_plant(key, tenant_key=ctx.tenant_key, role=ctx.role, request=body)
    return QuickPlantingResponse(
        run_key=result.run_key,
        entry_key=result.entry_key,
        slot_keys=result.created_slot_keys,
        plant_keys=result.plant_keys,
        instance_ids=result.instance_ids,
        warnings=result.warnings,
    )


@router.post(
    "/{key}/validate-planting",
    response_model=ValidatePlantingResponse,
    responses={**VALIDATION_RESPONSE},
)
def validate_planting(
    key: Annotated[str, Path(description="Document key of the bed.")],
    body: ValidatePlantingRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.READ)),
    service: BedRotationService = Depends(get_bed_rotation_service),
) -> ValidatePlantingResponse:
    """Crop-rotation and companion hints for planting a species in a bed (GP-API-025, GP-FR-131/132), all roles.

    **Hints with a strength, never a blocker** (D-09): a violation is a `WARNING` or `CRITICAL` finding in a 200,
    not an error. The history of every slot of the bed counts, from `rotation_reset_at` on; the pause comes from the
    species, else its family, else `rotation_window_years` (default 3, at most 8). Off (`rotation_applicable:
    false`) for `rotation_exempt` beds, for beds switched off (`rotation_enabled: false`) and for planters, tents
    and shelves unless switched on (`rotation_enabled: true`, GP-FR-137). With `slot_key` the neighbours of that slot
    (`adjacent_to`) are checked, otherwise every species standing or planned in the bed. 422
    `reference.not_found` for a species or slot the tenant cannot see.
    """
    result = service.validate_planting(
        key,
        body.species_key,
        tenant_key=ctx.tenant_key,
        slot_key=body.slot_key,
        rotation_window_years=body.rotation_window_years,
    )
    return ValidatePlantingResponse(
        location_key=result.rotation.location_key,
        species_key=result.rotation.species_key,
        severity=result.severity,
        rotation_applicable=result.rotation.applicable,
        not_applicable_reason=result.rotation.not_applicable_reason,
        rotation_window_years=result.rotation.rotation_window_years,
        rotation_reset_at=result.rotation.rotation_reset_at,
        rotation=[RotationFindingResponse(**asdict(f)) for f in result.rotation.findings],
        neighbour_scope=result.neighbour_scope,
        neighbours=[NeighbourHintResponse(**asdict(h)) for h in result.neighbours],
    )


@router.get("/{key}/history", response_model=list[BedHistoryItemResponse], responses={**VALIDATION_RESPONSE})
def get_bed_history(
    key: Annotated[str, Path(description="Document key of the bed.")],
    category: str | None = Query(
        None, description="Only this category (`planting` / `removal` for plant and run events)."
    ),
    plant_key: str | None = Query(None, description="Only the events that name this plant."),
    performed_from: datetime | None = Query(None, alias="from", description="Events from this instant (inclusive)."),
    performed_to: datetime | None = Query(None, alias="to", description="Events until this instant (inclusive)."),
    performed_by: str | None = Query(
        None,
        description=(
            "Account key of a member, as the member list names it. A viewer or grower may name only themselves; "
            "a lead or a member with the management scope may name anyone (403 otherwise). Plant and run events "
            "have no performer and are left out."
        ),
    ),
    include_corrections: bool = Query(
        False, description="Also the entries a correction replaced and the `position_corrected` entries."
    ),
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: BedHistoryService = Depends(get_bed_history_service),
) -> list[BedHistoryItemResponse]:
    """The history of a bed, newest first, 50 per page (GP-API-038, GP-FR-102), all roles.

    The stored care events of the bed and the planting events derived from its plants and runs (`plant_planted`,
    `plant_removed`, `run_started`, `run_completed`) in one list. `performed_by` follows the care log's rule
    (E-16): a viewer or grower names only themselves. 404 for a foreign or absent bed; 422 for an unknown
    category or a `to` before `from`.
    """
    if category is not None and category not in CARE_EVENT_CATEGORIES:
        raise ValidationError(
            f"Unknown category '{category}'.", details=[{"field": "category", "message": "unknown category"}]
        )
    performed_from, performed_to = utc_range(performed_from, performed_to)
    criteria = BedHistoryFilter(
        category=category,
        plant_key=plant_key,
        performed_from=performed_from,
        performed_to=performed_to,
        performed_by=performed_by,
        include_corrections=include_corrections,
    )
    items = service.list_history(
        key,
        criteria,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        role=ctx.role,
        admin_scopes=ctx.admin_scopes,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    return [BedHistoryItemResponse.from_item(item) for item in items]


@router.get("/{key}/rotation", response_model=RotationTimelineResponse, responses={**VALIDATION_RESPONSE})
def get_rotation_timeline(
    key: Annotated[str, Path(description="Document key of the bed.")],
    years: Annotated[
        int | None,
        Query(
            ge=1,
            le=MAX_ROTATION_TIMELINE_YEARS,
            description="Look-back in years; default `max(pause of the families involved, 5)`, at most 10.",
        ),
    ] = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: BedRotationService = Depends(get_bed_rotation_service),
) -> RotationTimelineResponse:
    """What stood in the bed per year: family, `nutrient_demand` and `plan_role` (GP-API-039, GP-FR-103), all roles.

    Plants of every slot of the bed and the years filled in afterwards (`POST …/history/backfill`); history before
    `rotation_reset_at` is left out. Every year of the look-back is listed, newest first — an empty `plantings` list
    is a year nobody recorded. A `years` above 10 is a 422.
    """
    timeline = service.rotation_timeline(key, tenant_key=ctx.tenant_key, years=years)
    by_year: dict[int, list[RotationPlantingResponse]] = {
        y: [] for y in range(timeline.to_year, timeline.from_year - 1, -1)
    }
    for entry in timeline.entries:
        by_year.setdefault(entry.year, []).append(
            RotationPlantingResponse(
                season=entry.season,
                family_key=entry.family_key,
                family_name=entry.family_name,
                species_key=entry.species_key,
                nutrient_demand=entry.nutrient_demand,
                plan_role=entry.plan_role,
                source=entry.source,
                care_event_key=entry.event_key,
            )
        )
    return RotationTimelineResponse(
        location_key=timeline.location_key,
        years=timeline.years,
        rotation_applicable=timeline.applicable,
        not_applicable_reason=timeline.not_applicable_reason,
        rotation_reset_at=timeline.rotation_reset_at,
        timeline=[RotationYearResponse(year=year, plantings=rows) for year, rows in by_year.items()],
    )


@router.post(
    "/{key}/history/backfill",
    response_model=BackfillResponse,
    status_code=201,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_bed_actions, key_func=user_rate_limit_key)
def backfill_history(
    request: Request,
    key: Annotated[str, Path(description="Document key of the bed.")],
    body: BackfillRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.CARE_EVENT, Action.CREATE)),
    service: BedRotationService = Depends(get_bed_rotation_service),
) -> BackfillResponse:
    """Record what stood in the bed in an earlier year — *"Was stand hier {Jahr}?"* (GP-API-042), grower and above.

    The server writes `care_event(category = planting, trigger = backfill)` at the middle of the season (1 July
    without one); the client never sends the trigger (SR-009). V-11 does not apply to it, the year range does:
    current year minus 10 up to minus 1 (422 `backfill.year_out_of_range`). A species names its family; a given
    `family_key` must agree (422 `backfill.family_mismatch`). Only a fallow year may omit both.
    """
    outcome = service.backfill(
        key,
        tenant_key=ctx.tenant_key,
        user_key=ctx.user_key,
        role=ctx.role,
        year=body.year,
        season=body.season,
        species_key=body.species_key,
        family_key=body.family_key,
        plan_role=body.plan_role,
    )
    return BackfillResponse(
        care_event_key=outcome.care_event_key,
        year=outcome.entry.year,
        season=outcome.entry.season,
        performed_at=outcome.performed_at,
        family_key=outcome.entry.family_key,
        species_key=outcome.entry.species_key,
        plan_role=outcome.entry.plan_role.value,
    )


@router.delete(
    "/{key}/history/backfill/{care_event_key}",
    status_code=204,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
@limiter.limit(settings.rate_limit_bed_actions, key_func=user_rate_limit_key)
def cancel_backfill(
    request: Request,
    key: Annotated[str, Path(description="Document key of the bed.")],
    care_event_key: Annotated[str, Path(description="Key of the backfilled care event.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.CARE_EVENT, Action.UPDATE)),
    service: BedRotationService = Depends(get_bed_rotation_service),
) -> None:
    """Take a backfilled year back (`void_reason = backfill_error`, GP-API-042): its author or a lead.

    404 for anything that is not a backfill of this bed — an absent, a foreign and an ordinary care event alike.
    """
    service.cancel_backfill(key, care_event_key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role)


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
