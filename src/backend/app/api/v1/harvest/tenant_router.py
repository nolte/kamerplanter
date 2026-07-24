from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.mapping import to_response
from app.api.v1.harvest.schemas import (
    HarvestBatchCreate,
    HarvestBatchResponse,
    HarvestBatchUpdate,
    HarvestCompleteRequest,
    HarvestCompleteResponse,
    HarvestIndicatorCreate,
    HarvestIndicatorResponse,
    ObservationCreate,
    ObservationResponse,
    QualityAssessmentCreate,
    QualityAssessmentResponse,
    RunHarvestCompleteResponse,
    YieldMetricCreate,
    YieldMetricResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_harvest_service
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.harvest import (
    HarvestBatch,
    HarvestIndicator,
    HarvestObservation,
    QualityAssessment,
    YieldMetric,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.harvest_service import HarvestService

router = APIRouter(prefix="/harvest", tags=["harvest"], responses=NOT_FOUND_RESPONSE)


def _indicator_response(i: HarvestIndicator) -> HarvestIndicatorResponse:
    return to_response(i, HarvestIndicatorResponse)


def _observation_response(o: HarvestObservation) -> ObservationResponse:
    return to_response(o, ObservationResponse)


def _batch_response(b: HarvestBatch) -> HarvestBatchResponse:
    return to_response(b, HarvestBatchResponse)


def _quality_response(q: QualityAssessment) -> QualityAssessmentResponse:
    return to_response(q, QualityAssessmentResponse)


def _yield_response(y: YieldMetric) -> YieldMetricResponse:
    return to_response(y, YieldMetricResponse)


@router.get("/indicators", response_model=list[HarvestIndicatorResponse])
def list_indicators(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """List harvest-readiness indicators (paginated)."""
    indicators, _ = service.list_indicators(pagination.offset, pagination.limit)
    return [_indicator_response(i) for i in indicators]


@router.post("/indicators", response_model=HarvestIndicatorResponse, status_code=201)
def create_indicator(
    body: HarvestIndicatorCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Create a harvest-readiness indicator."""
    indicator = HarvestIndicator(**body.model_dump())
    created = service.create_indicator(indicator)
    return _indicator_response(created)


@router.get("/species/{species_key}/indicators", response_model=list[HarvestIndicatorResponse])
def get_indicators_for_species(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """List the harvest-readiness indicators defined for a species."""
    indicators = service.get_indicators_for_species(species_key)
    return [_indicator_response(i) for i in indicators]


@router.post("/plants/{plant_key}/observations", response_model=ObservationResponse, status_code=201)
def create_observation(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: ObservationCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Record a harvest-readiness observation for a plant."""
    observation = HarvestObservation(**body.model_dump())
    created = service.record_observation(plant_key, observation)
    return _observation_response(created)


@router.get("/plants/{plant_key}/observations", response_model=list[ObservationResponse])
def list_observations(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """List a plant's harvest-readiness observations (paginated)."""
    observations, _ = service.get_observations(plant_key, pagination.offset, pagination.limit)
    return [_observation_response(o) for o in observations]


@router.get("/plants/{plant_key}/readiness")
def assess_readiness(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Assess a plant's current harvest readiness."""
    return service.assess_readiness(plant_key)


@router.get("/batches", response_model=list[HarvestBatchResponse])
def list_batches(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """List the tenant's harvest batches (paginated)."""
    batches, _ = service.list_batches(pagination.offset, pagination.limit, tenant_key=ctx.tenant_key)
    return [_batch_response(b) for b in batches]


@router.post("/plants/{plant_key}/batches", response_model=HarvestBatchResponse, status_code=201)
def create_batch(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: HarvestBatchCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Create a harvest batch for a plant."""
    batch = HarvestBatch(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_harvest_batch(plant_key, batch)
    return _batch_response(created)


@router.post("/plants/{plant_key}/complete", response_model=HarvestCompleteResponse)
def complete_harvest(
    plant_key: Annotated[str, Path(description="Document key of the plant instance.")],
    body: HarvestCompleteRequest | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """REQ-007 — explicit 'Ernte abschließen': end the plant's lifecycle as harvested."""
    on_date = body.on_date if body else None
    plant = service.complete_harvest(plant_key, tenant_key=ctx.tenant_key, on_date=on_date)
    return HarvestCompleteResponse(
        plant_key=plant.key or plant_key,
        termination_type=plant.termination_type.value if plant.termination_type else None,
        removed_on=plant.removed_on,
    )


@router.post("/runs/{run_key}/complete", response_model=RunHarvestCompleteResponse)
def complete_run_harvest(
    run_key: Annotated[str, Path(description="Document key of the planting run.")],
    body: HarvestCompleteRequest | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """REQ-007 — explicit 'Ernte abschließen' for a whole run: terminate all active instances."""
    on_date = body.on_date if body else None
    result = service.complete_harvest_for_run(run_key, tenant_key=ctx.tenant_key, on_date=on_date)
    return RunHarvestCompleteResponse(**result)


@router.get("/batches/{key}", response_model=HarvestBatchResponse)
def get_batch(
    key: Annotated[str, Path(description="Document key of the harvest batch.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Return a single harvest batch by key."""
    return _batch_response(service.get_batch(key, tenant_key=ctx.tenant_key))


@router.put("/batches/{key}", response_model=HarvestBatchResponse)
def update_batch(
    key: Annotated[str, Path(description="Document key of the harvest batch.")],
    body: HarvestBatchUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Update a harvest batch."""
    service.get_batch(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_batch(key, data)
    return _batch_response(updated)


@router.post("/batches/{batch_key}/quality", response_model=QualityAssessmentResponse, status_code=201)
def create_quality_assessment(
    batch_key: Annotated[str, Path(description="Document key of the harvest batch.")],
    body: QualityAssessmentCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Record a quality assessment for a harvest batch."""
    service.get_batch(batch_key, tenant_key=ctx.tenant_key)
    assessment = QualityAssessment(**body.model_dump())
    created = service.create_quality_assessment(batch_key, assessment)
    return _quality_response(created)


@router.get("/batches/{batch_key}/quality", response_model=QualityAssessmentResponse | None)
def get_quality(
    batch_key: Annotated[str, Path(description="Document key of the harvest batch.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Return the quality assessment of a harvest batch, if any."""
    service.get_batch(batch_key, tenant_key=ctx.tenant_key)
    q = service.get_quality(batch_key)
    return _quality_response(q) if q else None


@router.post("/batches/{batch_key}/yield", response_model=YieldMetricResponse, status_code=201)
def create_yield_metric(
    batch_key: Annotated[str, Path(description="Document key of the harvest batch.")],
    body: YieldMetricCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Record a yield metric for a harvest batch."""
    service.get_batch(batch_key, tenant_key=ctx.tenant_key)
    metric = YieldMetric(**body.model_dump())
    created = service.create_yield_metric(batch_key, metric)
    return _yield_response(created)


@router.get("/batches/{batch_key}/yield", response_model=YieldMetricResponse | None)
def get_yield(
    batch_key: Annotated[str, Path(description="Document key of the harvest batch.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Return the yield metric of a harvest batch, if any."""
    service.get_batch(batch_key, tenant_key=ctx.tenant_key)
    y = service.get_yield(batch_key)
    return _yield_response(y) if y else None


@router.get("/species/{species_key}/yield-stats")
def get_yield_stats(
    species_key: Annotated[str, Path(description="Document key of the species.")],
    days_back: int = Query(365, ge=1, description="Look-back window in days for the statistics."),
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    """Return aggregated yield statistics for a species."""
    return service.get_yield_stats(species_key, days_back)
