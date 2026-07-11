"""REQ-008 Post-Harvest tenant-scoped router.

Mounted under ``/t/{tenant_slug}`` — every endpoint requires authentication and
tenant membership (REQ-023/024). Reads accept any membership
(``get_current_tenant``); writes require at least the ``grower`` role
(``require_tenant_role`` — REQ-024 viewer is read-only), and the destructive
delete stays admin-only. All post-harvest data is tenant-scoped; the service
enforces ownership on each batch, so no query can cross tenants.
"""

from fastapi import APIRouter, Depends, Query

from app.api.mapping import to_response
from app.api.v1.post_harvest.schemas import (
    AdvanceStageRequest,
    DryingProgressCreate,
    DryingProgressResponse,
    MoldAlertResponse,
    ObservationCreate,
    PostHarvestBatchDetailResponse,
    PostHarvestBatchResponse,
    StartDryingRequest,
    StorageObservationResponse,
)
from app.common.auth import get_current_tenant, require_tenant_role
from app.common.dependencies import get_post_harvest_service
from app.common.enums import (
    DryingMethod,
    PostHarvestSpeciesType,
    PostHarvestStage,
    StorageAromaQuality,
    StorageVisualCondition,
    TenantRole,
)
from app.common.exceptions import ValidationError
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.post_harvest import (
    DryingProgress,
    MoldAlert,
    PostHarvestBatch,
    StorageObservation,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.post_harvest_service import PostHarvestService

router = APIRouter(prefix="/post-harvest", tags=["post-harvest"])


def _parse_enum[E](enum_cls: type[E], value: str, field: str) -> E:
    """Coerce a request string onto an enum, raising 422 on an invalid value."""
    try:
        return enum_cls(value)  # type: ignore[call-arg]
    except ValueError as exc:
        raise ValidationError(f"Invalid {field}: '{value}'.") from exc


def _batch_response(b: PostHarvestBatch) -> PostHarvestBatchResponse:
    return to_response(b, PostHarvestBatchResponse)


def _progress_response(p: DryingProgress) -> DryingProgressResponse:
    return to_response(p, DryingProgressResponse)


def _observation_response(o: StorageObservation) -> StorageObservationResponse:
    return to_response(o, StorageObservationResponse)


def _alert_response(a: MoldAlert) -> MoldAlertResponse:
    return to_response(a, MoldAlertResponse)


@router.get("", response_model=list[PostHarvestBatchResponse])
def list_batches(
    harvest_batch: str | None = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: PostHarvestService = Depends(get_post_harvest_service),
):
    if harvest_batch:
        batches = service.list_for_batch(harvest_batch, ctx.tenant_key)
    else:
        batches, _ = service.list_batches(ctx.tenant_key, pagination.offset, pagination.limit)
    return [_batch_response(b) for b in batches]


@router.post("/start-drying", response_model=PostHarvestBatchResponse, status_code=201)
def start_drying(
    body: StartDryingRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PostHarvestService = Depends(get_post_harvest_service),
):
    """Take a HarvestBatch into post-harvest tracking at stage ``drying``."""
    created = service.start_drying(
        ctx.tenant_key,
        body.harvest_batch_key,
        species_type=_parse_enum(PostHarvestSpeciesType, body.species_type, "species_type"),
        drying_method=_parse_enum(DryingMethod, body.drying_method, "drying_method"),
        start_weight_g=body.start_weight_g,
        target_moisture_percent=body.target_moisture_percent,
        notes=body.notes,
    )
    return _batch_response(created)


@router.get("/{key}", response_model=PostHarvestBatchDetailResponse)
def get_batch(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PostHarvestService = Depends(get_post_harvest_service),
):
    batch = service.get_batch(key, ctx.tenant_key)
    latest = service.get_latest_drying_progress(key, ctx.tenant_key)
    open_alerts = sum(1 for a in service.list_mold_alerts(key, ctx.tenant_key) if a.resolved_at is None)
    return PostHarvestBatchDetailResponse(
        batch=_batch_response(batch),
        latest_drying_progress=_progress_response(latest) if latest else None,
        open_mold_alerts=open_alerts,
    )


@router.post("/{key}/advance", response_model=PostHarvestBatchResponse)
def advance_stage(
    key: str,
    body: AdvanceStageRequest,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PostHarvestService = Depends(get_post_harvest_service),
):
    """Advance a batch to the next stage (forward-only; 422 on invalid step)."""
    target = _parse_enum(PostHarvestStage, body.target_stage, "target_stage")
    updated = service.advance_stage(key, ctx.tenant_key, target)
    return _batch_response(updated)


@router.post("/{key}/drying-progress", response_model=DryingProgressResponse, status_code=201)
def record_drying_progress(
    key: str,
    body: DryingProgressCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PostHarvestService = Depends(get_post_harvest_service),
):
    created = service.record_drying_progress(
        key,
        ctx.tenant_key,
        body.current_weight_g,
        water_activity=body.water_activity,
        co2_ppm=body.co2_ppm,
        snap_test_passed=body.snap_test_passed,
        notes=body.notes,
    )
    return _progress_response(created)


@router.get("/{key}/drying-progress", response_model=list[DryingProgressResponse])
def list_drying_progress(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PostHarvestService = Depends(get_post_harvest_service),
):
    return [_progress_response(p) for p in service.list_drying_progress(key, ctx.tenant_key)]


@router.post("/{key}/observations", response_model=StorageObservationResponse, status_code=201)
def record_observation(
    key: str,
    body: ObservationCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: PostHarvestService = Depends(get_post_harvest_service),
):
    observation = StorageObservation(
        weight_g=body.weight_g,
        temperature_c=body.temperature_c,
        rh_percent=body.rh_percent,
        water_activity=body.water_activity,
        co2_ppm=body.co2_ppm,
        visual_condition=_parse_enum(StorageVisualCondition, body.visual_condition, "visual_condition"),
        aroma_quality=_parse_enum(StorageAromaQuality, body.aroma_quality, "aroma_quality"),
        defects_observed=body.defects_observed,
        observer=body.observer,
        notes=body.notes,
    )
    created = service.record_observation(key, ctx.tenant_key, observation)
    return _observation_response(created)


@router.get("/{key}/observations", response_model=list[StorageObservationResponse])
def list_observations(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PostHarvestService = Depends(get_post_harvest_service),
):
    return [_observation_response(o) for o in service.list_observations(key, ctx.tenant_key)]


@router.get("/{key}/mold-alerts", response_model=list[MoldAlertResponse])
def list_mold_alerts(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: PostHarvestService = Depends(get_post_harvest_service),
):
    return [_alert_response(a) for a in service.list_mold_alerts(key, ctx.tenant_key)]


@router.delete("/{key}", status_code=204)
def delete_batch(
    key: str,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.ADMIN)),
    service: PostHarvestService = Depends(get_post_harvest_service),
):
    """Delete a post-harvest batch (REQ-008 §4 — Admin only)."""
    service.delete_batch(key, ctx.tenant_key)
