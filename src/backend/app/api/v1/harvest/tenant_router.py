from fastapi import APIRouter, Depends, Query

from app.api.v1.harvest.router import (
    _batch_response,
    _indicator_response,
    _observation_response,
    _quality_response,
    _yield_response,
)
from app.api.v1.harvest.schemas import (
    HarvestBatchCreate,
    HarvestBatchResponse,
    HarvestBatchUpdate,
    HarvestIndicatorCreate,
    HarvestIndicatorResponse,
    ObservationCreate,
    ObservationResponse,
    QualityAssessmentCreate,
    QualityAssessmentResponse,
    YieldMetricCreate,
    YieldMetricResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_harvest_service
from app.domain.models.harvest import (
    HarvestBatch,
    HarvestIndicator,
    HarvestObservation,
    QualityAssessment,
    YieldMetric,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.harvest_service import HarvestService

router = APIRouter(prefix="/harvest", tags=["harvest"])


@router.get("/indicators", response_model=list[HarvestIndicatorResponse])
def list_indicators(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    indicators, _ = service.list_indicators(offset, limit)
    return [_indicator_response(i) for i in indicators]


@router.post("/indicators", response_model=HarvestIndicatorResponse, status_code=201)
def create_indicator(
    body: HarvestIndicatorCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    indicator = HarvestIndicator(**body.model_dump())
    created = service.create_indicator(indicator)
    return _indicator_response(created)


@router.get("/species/{species_key}/indicators", response_model=list[HarvestIndicatorResponse])
def get_indicators_for_species(
    species_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    indicators = service.get_indicators_for_species(species_key)
    return [_indicator_response(i) for i in indicators]


@router.post("/plants/{plant_key}/observations", response_model=ObservationResponse, status_code=201)
def create_observation(
    plant_key: str,
    body: ObservationCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    observation = HarvestObservation(**body.model_dump())
    created = service.record_observation(plant_key, observation)
    return _observation_response(created)


@router.get("/plants/{plant_key}/observations", response_model=list[ObservationResponse])
def list_observations(
    plant_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    observations, _ = service.get_observations(plant_key, offset, limit)
    return [_observation_response(o) for o in observations]


@router.get("/plants/{plant_key}/readiness")
def assess_readiness(
    plant_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    return service.assess_readiness(plant_key)


@router.get("/batches", response_model=list[HarvestBatchResponse])
def list_batches(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    batches, _ = service.list_batches(offset, limit, tenant_key=ctx.tenant_key)
    return [_batch_response(b) for b in batches]


@router.post("/plants/{plant_key}/batches", response_model=HarvestBatchResponse, status_code=201)
def create_batch(
    plant_key: str,
    body: HarvestBatchCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    batch = HarvestBatch(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_harvest_batch(plant_key, batch)
    return _batch_response(created)


@router.get("/batches/{key}", response_model=HarvestBatchResponse)
def get_batch(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    return _batch_response(service.get_batch(key, tenant_key=ctx.tenant_key))


@router.put("/batches/{key}", response_model=HarvestBatchResponse)
def update_batch(
    key: str,
    body: HarvestBatchUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    service.get_batch(key, tenant_key=ctx.tenant_key)
    data = body.model_dump(exclude_none=True)
    updated = service.update_batch(key, data)
    return _batch_response(updated)


@router.post("/batches/{batch_key}/quality", response_model=QualityAssessmentResponse, status_code=201)
def create_quality_assessment(
    batch_key: str,
    body: QualityAssessmentCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    service.get_batch(batch_key, tenant_key=ctx.tenant_key)
    assessment = QualityAssessment(**body.model_dump())
    created = service.create_quality_assessment(batch_key, assessment)
    return _quality_response(created)


@router.get("/batches/{batch_key}/quality", response_model=QualityAssessmentResponse | None)
def get_quality(
    batch_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    service.get_batch(batch_key, tenant_key=ctx.tenant_key)
    q = service.get_quality(batch_key)
    return _quality_response(q) if q else None


@router.post("/batches/{batch_key}/yield", response_model=YieldMetricResponse, status_code=201)
def create_yield_metric(
    batch_key: str,
    body: YieldMetricCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    service.get_batch(batch_key, tenant_key=ctx.tenant_key)
    metric = YieldMetric(**body.model_dump())
    created = service.create_yield_metric(batch_key, metric)
    return _yield_response(created)


@router.get("/batches/{batch_key}/yield", response_model=YieldMetricResponse | None)
def get_yield(
    batch_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    service.get_batch(batch_key, tenant_key=ctx.tenant_key)
    y = service.get_yield(batch_key)
    return _yield_response(y) if y else None


@router.get("/species/{species_key}/yield-stats")
def get_yield_stats(
    species_key: str,
    days_back: int = Query(365, ge=1),
    ctx: TenantContext = Depends(get_current_tenant),
    service: HarvestService = Depends(get_harvest_service),
):
    return service.get_yield_stats(species_key, days_back)
