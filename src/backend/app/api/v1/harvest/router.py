from fastapi import APIRouter, Depends, Query

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
from app.common.dependencies import get_harvest_service
from app.domain.models.harvest import (
    HarvestBatch,
    HarvestIndicator,
    HarvestObservation,
    QualityAssessment,
    YieldMetric,
)
from app.domain.services.harvest_service import HarvestService

router = APIRouter(prefix="/harvest", tags=["harvest"])


def _indicator_response(i: HarvestIndicator) -> HarvestIndicatorResponse:
    return HarvestIndicatorResponse(key=i.key or "", **i.model_dump(exclude={"key"}))


def _observation_response(o: HarvestObservation) -> ObservationResponse:
    return ObservationResponse(key=o.key or "", **o.model_dump(exclude={"key"}))


def _batch_response(b: HarvestBatch) -> HarvestBatchResponse:
    return HarvestBatchResponse(key=b.key or "", **b.model_dump(exclude={"key"}))


def _quality_response(q: QualityAssessment) -> QualityAssessmentResponse:
    return QualityAssessmentResponse(key=q.key or "", **q.model_dump(exclude={"key"}))


def _yield_response(y: YieldMetric) -> YieldMetricResponse:
    return YieldMetricResponse(key=y.key or "", **y.model_dump(exclude={"key"}))


# ── Indicators ──


@router.get("/indicators", response_model=list[HarvestIndicatorResponse])
def list_indicators(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: HarvestService = Depends(get_harvest_service),
):
    indicators, _ = service.list_indicators(offset, limit)
    return [_indicator_response(i) for i in indicators]


@router.post("/indicators", response_model=HarvestIndicatorResponse, status_code=201)
def create_indicator(body: HarvestIndicatorCreate, service: HarvestService = Depends(get_harvest_service)):
    indicator = HarvestIndicator(**body.model_dump())
    created = service.create_indicator(indicator)
    return _indicator_response(created)


@router.get("/species/{species_key}/indicators", response_model=list[HarvestIndicatorResponse])
def get_indicators_for_species(species_key: str, service: HarvestService = Depends(get_harvest_service)):
    indicators = service.get_indicators_for_species(species_key)
    return [_indicator_response(i) for i in indicators]


# ── Observations ──


@router.post("/plants/{plant_key}/observations", response_model=ObservationResponse, status_code=201)
def create_observation(
    plant_key: str,
    body: ObservationCreate,
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
    service: HarvestService = Depends(get_harvest_service),
):
    observations, _ = service.get_observations(plant_key, offset, limit)
    return [_observation_response(o) for o in observations]


# ── Readiness ──


@router.get("/plants/{plant_key}/readiness")
def assess_readiness(plant_key: str, service: HarvestService = Depends(get_harvest_service)):
    return service.assess_readiness(plant_key)


# ── Harvest Batches ──


@router.get("/batches", response_model=list[HarvestBatchResponse])
def list_batches(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: HarvestService = Depends(get_harvest_service),
):
    batches, _ = service.list_batches(offset, limit)
    return [_batch_response(b) for b in batches]


@router.post("/plants/{plant_key}/batches", response_model=HarvestBatchResponse, status_code=201)
def create_batch(
    plant_key: str,
    body: HarvestBatchCreate,
    service: HarvestService = Depends(get_harvest_service),
):
    batch = HarvestBatch(**body.model_dump())
    created = service.create_harvest_batch(plant_key, batch)
    return _batch_response(created)


@router.get("/batches/{key}", response_model=HarvestBatchResponse)
def get_batch(key: str, service: HarvestService = Depends(get_harvest_service)):
    return _batch_response(service.get_batch(key))


@router.put("/batches/{key}", response_model=HarvestBatchResponse)
def update_batch(key: str, body: HarvestBatchUpdate, service: HarvestService = Depends(get_harvest_service)):
    data = body.model_dump(exclude_none=True)
    updated = service.update_batch(key, data)
    return _batch_response(updated)


# ── Quality Assessment ──


@router.post("/batches/{batch_key}/quality", response_model=QualityAssessmentResponse, status_code=201)
def create_quality_assessment(
    batch_key: str,
    body: QualityAssessmentCreate,
    service: HarvestService = Depends(get_harvest_service),
):
    assessment = QualityAssessment(**body.model_dump())
    created = service.create_quality_assessment(batch_key, assessment)
    return _quality_response(created)


@router.get("/batches/{batch_key}/quality", response_model=QualityAssessmentResponse | None)
def get_quality(batch_key: str, service: HarvestService = Depends(get_harvest_service)):
    q = service.get_quality(batch_key)
    return _quality_response(q) if q else None


# ── Yield Metrics ──


@router.post("/batches/{batch_key}/yield", response_model=YieldMetricResponse, status_code=201)
def create_yield_metric(
    batch_key: str,
    body: YieldMetricCreate,
    service: HarvestService = Depends(get_harvest_service),
):
    metric = YieldMetric(**body.model_dump())
    created = service.create_yield_metric(batch_key, metric)
    return _yield_response(created)


@router.get("/batches/{batch_key}/yield", response_model=YieldMetricResponse | None)
def get_yield(batch_key: str, service: HarvestService = Depends(get_harvest_service)):
    y = service.get_yield(batch_key)
    return _yield_response(y) if y else None


@router.get("/species/{species_key}/yield-stats")
def get_yield_stats(
    species_key: str,
    days_back: int = Query(365, ge=1),
    service: HarvestService = Depends(get_harvest_service),
):
    return service.get_yield_stats(species_key, days_back)
