from dataclasses import asdict
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.responses import Response

from app.api.mapping import to_response
from app.api.v1.attachments.schemas import ThumbnailUris
from app.api.v1.auth.router import limiter, tenant_rate_limit_key, user_rate_limit_key
from app.api.v1.garden_plan.export_options import PLAN_EXPORT_TENANT_SCOPE
from app.api.v1.locations.schemas import (
    BackfillRequest,
    BackfillResponse,
    BedHistoryItemResponse,
    BedListItemResponse,
    BedSummaryResponse,
    ClearBedRequest,
    ClearBedResponse,
    CompanionDecidingPairResponse,
    CompanionEdgeResponse,
    CompanionEdgesResponse,
    CompanionEndpointResponse,
    FrostWarningResponse,
    LimingHintResponse,
    LocationCoverRequest,
    LocationCreate,
    LocationPatch,
    LocationPatchResponse,
    LocationPhotoRequest,
    LocationPhotoResponse,
    LocationPhotosResponse,
    LocationResponse,
    LocationStatusRequest,
    NeighbourHintResponse,
    NutrientHintResponse,
    PlanPointResponse,
    PlantingItemResponse,
    PlantingLayoutPreviewRequest,
    PlantingLayoutPreviewResponse,
    PlantStateResponse,
    QuickPlantingRequest,
    QuickPlantingResponse,
    RotationFindingResponse,
    RotationTimelineResponse,
    SoilAnalysesResponse,
    SoilAnalysisPointResponse,
    SoilAnalysisSeriesItemResponse,
    SoilMethodChangeResponse,
    SuccessionBasisResponse,
    SuccessionFamilyResponse,
    SuccessionHeldBackResponse,
    SuccessionRecommendationResponse,
    SuccessionSpeciesResponse,
    ValidatePlantingRequest,
    ValidatePlantingResponse,
    rotation_year_responses,
)
from app.api.v1.slots.schemas import SlotBatchRequest, SlotBatchResponse
from app.api.v1.tanks.schemas import LiveStateResponse, SensorCreate, SensorResponse, SensorUpdate
from app.common.auth import get_budgeted_tenant, get_current_tenant, require_permission
from app.common.csv_download import CsvDelimiter, csv_download, csv_not_requested
from app.common.datetimes import utc_range
from app.common.dependencies import (
    get_bed_history_service,
    get_bed_rotation_service,
    get_companion_overlay_service,
    get_garden_resource_service,
    get_location_photo_service,
    get_plant_state_service,
    get_planting_reservation_service,
    get_planting_run_service,
    get_sensor_service,
    get_site_service,
    get_soil_analysis_service,
)
from app.common.enums import BedStatus
from app.common.exceptions import PlanError, ValidationError
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
from app.domain.engines.bed_list_csv_engine import ERROR_BEDS_ONLY, bed_list_csv_rows, resolve_bed_list_columns
from app.domain.engines.storage.thumbnail_generator import THUMBNAIL_SIZES, can_render
from app.domain.interfaces.bed_history_repository import BedHistoryFilter
from app.domain.models.care_event import CARE_EVENT_CATEGORIES
from app.domain.models.location_photo import LocationPhoto, LocationPhotoGallery
from app.domain.models.sensor import Sensor
from app.domain.models.site import MAX_PHOTO_REF_LENGTH, Location
from app.domain.models.tenant_context import TenantContext
from app.domain.services.bed_history_service import BedHistoryService
from app.domain.services.bed_rotation_service import BedRotationService
from app.domain.services.companion_overlay_service import CompanionEndpoint, CompanionOverlayService
from app.domain.services.garden_resource_service import GardenResourceService
from app.domain.services.location_photo_service import LocationPhotoService
from app.domain.services.plant_state_service import PlantStateService
from app.domain.services.planting_reservation_service import PlantingReservationService
from app.domain.services.planting_run_service import PlantingRunService
from app.domain.services.sensor_service import SensorService
from app.domain.services.site_service import SiteService
from app.domain.services.soil_analysis_service import DEFAULT_ANALYSES, MAX_ANALYSES, SoilAnalysisService

router = APIRouter(prefix="/locations", tags=["locations"], responses=NOT_FOUND_RESPONSE)


def _verify_location_tenant(key: str, ctx: TenantContext, service: SiteService) -> Location:
    """The location ``key`` if its site is the tenant's, else 404 as ``Location`` (#1871 B13).

    Resolved in one step through the parent site. The two-step form (location
    unscoped, then its site) answered a foreign location with ``No Site with key
    '<the other tenant's site>'`` and an unknown one with ``No Location`` — an
    existence oracle that echoed the other tenant's site key.
    """
    return service.get_location(key, tenant_key=ctx.tenant_key)


@router.get(
    "",
    response_model=list[BedListItemResponse],
    responses={
        **FORBIDDEN_RESPONSE,
        200: {"content": {"text/csv": {}}, "description": "`format=csv`: the bed list as a UTF-8 CSV with BOM."},
        422: {
            "description": (
                "`export.unknown_column` / `export.no_columns`: the column selection; `export.beds_only`: "
                "`format=csv` with `is_bed=false`; `export.too_many_rows`: more than 2 000 beds."
            )
        },
    },
)
@limiter.limit(settings.rate_limit_plan_export, key_func=user_rate_limit_key, exempt_when=csv_not_requested)
@limiter.shared_limit(
    settings.rate_limit_plan_export_tenant,
    scope=PLAN_EXPORT_TENANT_SCOPE,
    key_func=tenant_rate_limit_key,
    exempt_when=csv_not_requested,
)
def list_locations(
    request: Request,
    site_key: str = Query(..., description="Document key of the site to list locations for."),
    parent_location_key: str | None = Query(
        None, description="If set, list the child locations of this parent instead."
    ),
    is_bed: bool | None = Query(
        None, description="Only locations whose type is (true) or is not (false) a bed; adds the counters (GP-API-011)."
    ),
    bed_status: BedStatus | None = Query(None, description="Only beds in this status; adds the counters (GP-API-011)."),
    export_format: Literal["json", "csv"] = Query(
        "json", alias="format", description="`csv` downloads the bed list as a file (GP-FR-145) instead of JSON."
    ),
    columns: str | None = Query(
        None,
        max_length=1000,
        description=(
            "`format=csv` only: comma-separated columns. Default `name,type,area_m2,status,soil_texture,"
            "irrigation_zone,active_plants`; selectable besides: the site features `sun_exposure`, `sun_window`, "
            "`direct_sun_hours_summer`, `foliage_shade_in_summer`, `frost_risk`, `cold_air_pocket`, "
            "`heat_retention`, `wind_exposure`, `slope_deg`, `aspect_deg`, `access_sides`, `site_flags` (GP-FR-175) "
            "and the derived `nearest_water_source_m` (metres to the nearest water source, empty without one; "
            "GP-FR-167)."
        ),
    ),
    include_assignment: bool = Query(
        False,
        description=(
            "`format=csv` only: add the column `assigned_to` with the display names of the members a bed is "
            "assigned to. Off by default (SR-024): personal data enters the file only on request."
        ),
    ),
    delimiter: CsvDelimiter = Query(
        "comma",
        description="`format=csv` only: `semicolon` is the Excel variant (semicolon delimiter, decimal comma).",
    ),
    locale: Literal["de", "en"] = Query("de", description="`format=csv` only: the language of the type names."),
    # The verified tenant is recorded for the per-tenant export budget (GP-NFR-056); otherwise get_current_tenant.
    ctx: TenantContext = Depends(get_budgeted_tenant),
    service: SiteService = Depends(get_site_service),
    resources: GardenResourceService = Depends(get_garden_resource_service),
) -> list[BedListItemResponse] | Response:
    """List a site's locations, or the children of a parent location.

    With ``is_bed`` or ``bed_status`` the rows carry ``active_plant_count``, ``open_task_count`` and
    ``next_due_at`` (GP-API-011). When beds are listed (``is_bed=true`` or ``bed_status``) they also carry
    ``nearest_water_source_m`` (GP-FR-167): metres from the bed's edge to the nearest water source of the site,
    ``null`` without a geometry or without a water source.

    ``format=csv`` (GP-FR-145/175) downloads the **beds** of the site (types with ``is_bed``; ``is_bed=false`` is
    422 ``export.beds_only``), sorted by name: UTF-8 with BOM, RFC 4180 quoting, cells that look like a formula
    prefixed with ``'`` (SR-016). The header row holds the column ids and enum cells the API's values (as the care-log
    CSV). The columns are chosen with ``columns``; the member names of a bed only with ``include_assignment=true``
    (SR-024). An unknown column is 422 ``export.unknown_column``. Rate-limited per account and per tenant (the
    budget of the garden-plan exports); the JSON list is not counted.
    """
    if export_format == "csv":
        if is_bed is False:
            raise PlanError(
                ERROR_BEDS_ONLY, "The CSV lists beds only; drop is_bed=false.", status_code=422, field="is_bed"
            )
        selected = resolve_bed_list_columns(columns, include_assignment=include_assignment)
        exported = resources.export_bed_list(
            site_key,
            tenant_key=ctx.tenant_key,
            columns=selected,
            bed_status=bed_status,
            parent_location_key=parent_location_key,
            locale=locale,
        )
        return csv_download(
            selected,
            bed_list_csv_rows(exported, selected, decimal_comma=delimiter == "semicolon"),
            delimiter=delimiter,
            filename_stem="bed-list",
        )
    if is_bed is not None or bed_status is not None:
        rows = resources.list_beds(site_key, tenant_key=ctx.tenant_key, is_bed=is_bed, bed_status=bed_status)
        if parent_location_key:
            rows = [row for row in rows if row.location.parent_location_key == parent_location_key]
        return [
            to_response(
                row.location,
                BedListItemResponse,
                active_plant_count=row.counters.active_plant_count if row.counters else None,
                open_task_count=row.counters.open_task_count if row.counters else None,
                overdue_task_count=row.counters.overdue_task_count if row.counters else None,
                next_due_at=row.counters.next_due_at if row.counters else None,
                nearest_water_source_m=row.nearest_water_source_m,
            )
            for row in rows
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
    """The head data of the bed view: area, type, status, soil, sun, plants, tasks, last care (GP-API-012).

    A bed also carries `nutrient_hint` (GP-FR-125): `ok`, `check`, `likely_deficit` or `insufficient_data` with
    reason codes, never a number. Thresholds without a source take no part (E-10).
    `nearest_water_source_m` (GP-FR-167) is the distance in metres from the bed's edge to the nearest water source of
    its site; `null` for a location that is no bed, without a geometry or without a water source.
    `path_access` (GP-FR-166) is the access the site's paths give the bed (`both` | `one` | `none`, within the site's
    `reach_thresholds.path_access_max_distance_m`); `null` for a location that is no bed or has no geometry.
    """
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
        nutrient_hint=NutrientHintResponse.from_hint(view.nutrient_hint),
        nearest_water_source_m=view.nearest_water_source_m,
        path_access=view.path_access,
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
async def delete_location(
    key: Annotated[str, Path(description="Document key of the location.")],
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.DELETE)),
    service: GardenResourceService = Depends(get_garden_resource_service),
) -> None:
    """Delete a location with its slots and everything below it (lead only).

    409 ``location.has_active_plants`` with ``details[0].active_plant_count`` while a plant stands in it
    (V-09, GP-ACC-012); the deletion is audited and raises the site's ``plan_revision``. The bed's photo
    references go with it; each photo is deleted unless something else still names it (WP 8.18).
    """
    await service.delete_bed(key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role)


# ── Bed photos (REQ-053 GP-FR-051, WP 8.18) ─────────────────────────────────────


def _photo_response(photo: LocationPhoto, tenant_slug: str) -> LocationPhotoResponse:
    attachment = photo.attachment
    attachment_id = attachment.key or ""
    uri = f"/api/v1/t/{tenant_slug}/attachments/{attachment_id}"
    thumbnail_uris: ThumbnailUris | None = None
    if can_render(attachment.mime_type):
        small, medium, large = THUMBNAIL_SIZES
        thumbnail_uris = ThumbnailUris(
            small=f"{uri}/thumbnails/{small}",
            medium=f"{uri}/thumbnails/{medium}",
            large=f"{uri}/thumbnails/{large}",
        )
    return LocationPhotoResponse(
        attachment_id=attachment_id,
        uri=uri,
        thumbnail_uris=thumbnail_uris,
        mime_type=attachment.mime_type,
        byte_size=attachment.byte_size,
        caption=attachment.caption,
        taken_on=attachment.taken_on,
        created_at=attachment.created_at,
        is_cover=photo.is_cover,
        can_remove=photo.can_remove,
    )


#: An ArangoDB document key is at most 254 bytes; the photo routes refuse a longer ``key`` before any lookup (SEC-003).
_MAX_DOCUMENT_KEY_LENGTH = 254

#: The ``key`` path parameter of the bed photo routes.
BedKeyPath = Annotated[str, Path(description="Document key of the bed.", max_length=_MAX_DOCUMENT_KEY_LENGTH)]


def _photos_response(view: LocationPhotoGallery, tenant_slug: str) -> LocationPhotosResponse:
    return LocationPhotosResponse(
        location_key=view.location_key,
        cover_photo_ref=view.cover_photo_ref,
        photos=[_photo_response(photo, tenant_slug) for photo in view.photos],
        max_photos=view.max_photos,
    )


@router.get("/{key}/photos", response_model=LocationPhotosResponse)
def list_location_photos(
    key: BedKeyPath,
    ctx: TenantContext = Depends(get_current_tenant),
    service: LocationPhotoService = Depends(get_location_photo_service),
) -> LocationPhotosResponse:
    """The bed's photos, newest first, with the cover marked and `can_remove` for the caller (every member reads).

    At most `max_photos` (50) photos; a reference whose attachment is gone is skipped.
    """
    view = service.list_photos(key, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role)
    return _photos_response(view, ctx.tenant_slug)


@router.post(
    "/{key}/photos",
    response_model=LocationPhotosResponse,
    status_code=201,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
def add_location_photo(
    key: BedKeyPath,
    body: LocationPhotoRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: LocationPhotoService = Depends(get_location_photo_service),
) -> LocationPhotosResponse:
    """Link an uploaded `location` photo to the bed, newest first (from `grower`); the first one becomes the cover.

    Upload the file first through `POST /attachments` with `category=location` (EXIF/GPS is stripped there).
    422 `reference.not_found` for an attachment that is not the caller's own bed photo; 422
    `location.photo_limit_reached` at 50 photos. Linking a photo the bed already shows changes nothing.
    """
    view = service.add_photo(key, body.attachment_id, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role)
    return _photos_response(view, ctx.tenant_slug)


@router.put(
    "/{key}/photos/cover",
    response_model=LocationPhotosResponse,
    responses={**FORBIDDEN_RESPONSE, **VALIDATION_RESPONSE},
)
def set_location_cover_photo(
    key: BedKeyPath,
    body: LocationCoverRequest,
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: LocationPhotoService = Depends(get_location_photo_service),
) -> LocationPhotosResponse:
    """Choose the bed's cover photo from its photos, or clear it with `null` (from `grower`).

    422 `location.cover_not_a_photo` for an id that is not one of the bed's photos.
    """
    view = service.set_cover(key, body.attachment_id, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role)
    return _photos_response(view, ctx.tenant_slug)


@router.delete(
    "/{key}/photos/{attachment_id}",
    response_model=LocationPhotosResponse,
    responses={**FORBIDDEN_RESPONSE},
)
async def remove_location_photo(
    key: BedKeyPath,
    attachment_id: Annotated[str, Path(description="The photo's attachment id.", max_length=MAX_PHOTO_REF_LENGTH)],
    ctx: TenantContext = Depends(require_permission(ResourceType.LOCATION, Action.UPDATE)),
    service: LocationPhotoService = Depends(get_location_photo_service),
) -> LocationPhotosResponse:
    """Remove a photo from the bed (own upload from `grower`, another member's as `lead`); 404 if the bed lacks it.

    When it was the cover, the newest remaining photo becomes the cover (none when it was the last). The attachment
    is deleted unless another bed, gallery, task or care event still names it, and its stored object only when no
    other record holds it.
    """
    view = await service.remove_photo(
        key, attachment_id, tenant_key=ctx.tenant_key, user_key=ctx.user_key, role=ctx.role
    )
    return _photos_response(view, ctx.tenant_slug)


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


def _endpoint_response(endpoint: CompanionEndpoint) -> CompanionEndpointResponse:
    position = endpoint.position
    return CompanionEndpointResponse(
        slot_key=endpoint.slot_key,
        position=PlanPointResponse(x=position[0], y=position[1]) if position is not None else None,
        species_keys=endpoint.species_keys,
        species_truncated=endpoint.species_truncated,
    )


@router.get(
    "/{key}/companion-edges",
    response_model=CompanionEdgesResponse,
    summary="The companion-planting layer of a bed: one judged line per neighbouring pair",
)
def get_companion_edges(
    key: Annotated[str, Path(description="Document key of the bed.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: CompanionOverlayService = Depends(get_companion_overlay_service),
) -> CompanionEdgesResponse:
    """Every `adjacent_to` pair of the bed's slots in which both slots hold a species (GP-FR-134, REQ-028 §7.3).

    A species counts when a plant stands in the slot (`removed_on = null`) or a live planting run plans it there - the
    set the planting dialog reads. Each pair is `compatible`, `incompatible` or `unknown` by the same rule as
    `POST …/validate-planting`: an incompatible edge wins, else a compatible edge with its score, else unknown. Several
    species per slot and both edge directions are folded with that precedence. Positions are the slot anchors in plan
    coordinates. The work is bounded: at most 2000 pairs (the first by slot keys) and 8 species per slot are judged;
    of those at most 500 are answered, `incompatible` first, then `compatible`, then `unknown`, each by slot keys.
    `total` counts every pair exactly; `truncated` says pairs were left out. Readable by every role; another tenant's
    bed is a 404.
    """
    result = service.companion_edges(key, tenant_key=ctx.tenant_key)
    return CompanionEdgesResponse(
        location_key=result.location_key,
        edges=[
            CompanionEdgeResponse(
                slot_a=_endpoint_response(edge.slot_a),
                slot_b=_endpoint_response(edge.slot_b),
                status=edge.status,
                reason_code=edge.reason_code,
                reason=edge.reason,
                score=edge.score,
                deciding=CompanionDecidingPairResponse(**asdict(edge.deciding)) if edge.deciding is not None else None,
                distance_cm=edge.distance_cm,
            )
            for edge in result.edges
        ],
        total=result.total,
        truncated=result.truncated,
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
    return RotationTimelineResponse(
        location_key=timeline.location_key,
        years=timeline.years,
        rotation_applicable=timeline.applicable,
        not_applicable_reason=timeline.not_applicable_reason,
        rotation_reset_at=timeline.rotation_reset_at,
        timeline=rotation_year_responses(timeline.entries, range(timeline.to_year, timeline.from_year - 1, -1)),
    )


@router.get(
    "/{key}/succession-recommendation",
    response_model=SuccessionRecommendationResponse,
    responses={**VALIDATION_RESPONSE},
)
def get_succession_recommendation(
    key: Annotated[str, Path(description="Document key of the bed.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: BedRotationService = Depends(get_bed_rotation_service),
) -> SuccessionRecommendationResponse:
    """Families and species for the next year of the bed (GP-FR-133), all roles - **order only, no amounts**.

    The step after the latest recorded year follows heavy -> medium -> light feeder -> green manure / fallow ->
    heavy (`nutrient_demand` and `plan_role`); candidates are the `rotation_after` successors of that year's
    families, minus those whose pause in this bed is not over (`held_back`). A species appears only with a stored
    `nutrient_demand` (or `green_manure_suitable` for the restoring step) - nothing is defaulted. `status` explains
    an empty list (`no_history`, `demand_unknown`, `no_successor_data`, `no_matching_species`, `not_applicable`).
    """
    result = service.succession_recommendation(key, tenant_key=ctx.tenant_key)
    previous = result.previous
    return SuccessionRecommendationResponse(
        location_key=result.location_key,
        rotation_applicable=result.applicable,
        not_applicable_reason=result.not_applicable_reason,
        status=result.status,
        previous=(
            SuccessionBasisResponse(
                year=previous.year,
                step=previous.step,
                nutrient_demand=previous.nutrient_demand,
                family_keys=list(previous.family_keys),
            )
            if previous is not None
            else None
        ),
        target=result.target,
        families=[
            SuccessionFamilyResponse(
                family_key=family.family_key,
                family_name=family.family_name,
                benefit_score=family.benefit_score,
                benefit_reason=family.benefit_reason,
                pause_years=family.pause_years,
                species=[SuccessionSpeciesResponse(**asdict(species)) for species in family.species],
            )
            for family in result.families
        ],
        held_back=[SuccessionHeldBackResponse(**asdict(held)) for held in result.held_back],
        fallow_option=result.fallow_option,
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


@router.get(
    "/{key}/soil-analyses",
    response_model=SoilAnalysesResponse,
    summary="The soil analyses of a bed as series per method",
    responses={**VALIDATION_RESPONSE},
)
def get_soil_analyses(
    key: Annotated[str, Path(description="Document key of the bed.")],
    parameter: Literal["ph", "ec", "n_min", "p", "k", "mg", "humus", "caco3", "moisture"] | None = Query(
        None, description="Only this parameter."
    ),
    performed_from: datetime | None = Query(None, alias="from", description="`performed_at` from (inclusive)."),
    performed_to: datetime | None = Query(None, alias="to", description="`performed_at` until (inclusive)."),
    limit: int = Query(
        DEFAULT_ANALYSES,
        ge=1,
        le=MAX_ANALYSES,
        description="At most this many analyses, newest first; `truncated` says older ones were left out.",
    ),
    ctx: TenantContext = Depends(get_current_tenant),
    service: SoilAnalysisService = Depends(get_soil_analysis_service),
) -> SoilAnalysesResponse:
    """Series of the bed's `soil_analysis` measurements per parameter **and method** (GP-FR-122, U-002/U-003).

    A conductivity is read per `ec_method`, a pH per `ph_method`, the rest per `extraction_method`; `unknown` is its
    own method. Where the method of a parameter changes between two analyses the change is listed in
    `method_changes`. Values of different methods are never merged, compared or converted. `liming_hint` is the
    "liming likely" text of the current profile - never an amount. Readable by every role.
    """
    performed_from, performed_to = utc_range(performed_from, performed_to)
    result = service.series(
        key,
        tenant_key=ctx.tenant_key,
        parameter=parameter,
        performed_from=performed_from,
        performed_to=performed_to,
        limit=limit,
    )
    return SoilAnalysesResponse(
        location_key=key,
        series=[
            SoilAnalysisSeriesItemResponse(
                parameter=item.parameter,
                method=item.method,
                unit=item.unit,
                points=[
                    SoilAnalysisPointResponse(
                        performed_at=point.performed_at,
                        value=point.value,
                        unit=point.unit,
                        source=point.source,
                        sample_depth_cm=point.sample_depth_cm,
                        content_class=point.content_class,
                        event_key=point.event_key,
                    )
                    for point in item.points
                ],
            )
            for item in result.series
        ],
        method_changes=[
            SoilMethodChangeResponse(
                parameter=change.parameter, at=change.at, from_method=change.from_method, to_method=change.to_method
            )
            for change in result.method_changes
        ],
        analyses=result.analyses,
        truncated=result.truncated,
        liming_hint=LimingHintResponse(status=result.liming_hint.status, reason=result.liming_hint.reason),
    )


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
