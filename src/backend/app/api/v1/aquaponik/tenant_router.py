"""REQ-026 Aquaponics tenant-scoped router.

Mounted under ``/t/{tenant_slug}/aquaponics``. Every endpoint resolves the
tenant via :func:`get_current_tenant` and the service verifies system ownership
against ``tenant_key`` before touching any child resource (SEC-B4).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.mapping import to_response
from app.api.v1.aquaponik.schemas import (
    AquaponicSystemCreate,
    AquaponicSystemResponse,
    AquaponicSystemUpdate,
    BiomassHistoryResponse,
    CyclingProgressResponse,
    CyclingStatusUpdate,
    DeficiencyReportResponse,
    FcrAnalysisResponse,
    FeedingRecommendationResponse,
    FishFeedingEventCreate,
    FishFeedingEventResponse,
    FishStockCreate,
    FishStockResponse,
    FishStockUpdate,
    HealthAlertResponse,
    MortalityCreate,
    MortalityRateResponse,
    NitrogenCyclePoint,
    SafetyStatusResponse,
    SupplementationEventCreate,
    SupplementationEventResponse,
    WaterQualityEvaluationResponse,
    WaterTestCreate,
    WaterTestResponse,
)
from app.common.auth import get_current_tenant, require_tenant_role
from app.common.dependencies import get_aquaponik_service
from app.common.enums import TenantRole
from app.common.openapi_responses import NOT_FOUND_RESPONSE
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.aquaponik import (
    AquaponicSystem,
    FishFeedingEvent,
    FishStock,
    SupplementationEvent,
    WaterTest,
)
from app.domain.models.tenant_context import TenantContext
from app.domain.services.aquaponik_service import AquaponikService

router = APIRouter(prefix="/aquaponics", tags=["aquaponics"], responses=NOT_FOUND_RESPONSE)


# ── Systems ─────────────────────────────────────────────────────────────


@router.get("/systems", response_model=list[AquaponicSystemResponse])
def list_systems(
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """List the tenant's aquaponic systems."""
    systems = service.list_systems(ctx.tenant_key)
    return [to_response(s, AquaponicSystemResponse) for s in systems]


@router.post("/systems", response_model=AquaponicSystemResponse, status_code=201)
def create_system(
    body: AquaponicSystemCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Create a new aquaponic system."""
    system = AquaponicSystem(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_system(system)
    return to_response(created, AquaponicSystemResponse)


@router.get("/systems/{system_key}", response_model=AquaponicSystemResponse)
def get_system(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return a single aquaponic system by key."""
    system = service.get_system(system_key, ctx.tenant_key)
    return to_response(system, AquaponicSystemResponse)


@router.patch("/systems/{system_key}", response_model=AquaponicSystemResponse)
def update_system(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    body: AquaponicSystemUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Update an aquaponic system."""
    updated = service.update_system(system_key, ctx.tenant_key, body.model_dump(exclude_none=True))
    return to_response(updated, AquaponicSystemResponse)


@router.delete("/systems/{system_key}", status_code=204)
def delete_system(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.LEAD)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Delete an aquaponic system."""
    service.delete_system(system_key, ctx.tenant_key)


@router.post("/systems/{system_key}/cycling-status", response_model=AquaponicSystemResponse)
def set_cycling_status(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    body: CyclingStatusUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Set the nitrogen-cycling status of an aquaponic system."""
    updated = service.set_cycling_status(system_key, ctx.tenant_key, body.cycling_status)
    return to_response(updated, AquaponicSystemResponse)


# ── Fish stocks ─────────────────────────────────────────────────────────


@router.post("/systems/{system_key}/fish-stocks", response_model=FishStockResponse, status_code=201)
def create_stock(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    body: FishStockCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Add a fish stock to an aquaponic system."""
    stock = FishStock(**body.model_dump(), initial_count=body.count)
    created = service.create_stock(system_key, ctx.tenant_key, stock)
    return to_response(created, FishStockResponse)


@router.get("/systems/{system_key}/fish-stocks", response_model=list[FishStockResponse])
def list_stocks(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """List the fish stocks of an aquaponic system."""
    stocks = service.list_stocks(system_key, ctx.tenant_key)
    return [to_response(s, FishStockResponse) for s in stocks]


@router.patch("/systems/{system_key}/fish-stocks/{stock_key}", response_model=FishStockResponse)
def update_stock(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    stock_key: Annotated[str, Path(description="Document key of the fish stock.")],
    body: FishStockUpdate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Update a fish stock."""
    updated = service.update_stock(system_key, stock_key, ctx.tenant_key, body.model_dump(exclude_none=True))
    return to_response(updated, FishStockResponse)


@router.delete("/systems/{system_key}/fish-stocks/{stock_key}", status_code=204)
def delete_stock(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    stock_key: Annotated[str, Path(description="Document key of the fish stock.")],
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.LEAD)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Delete a fish stock."""
    service.delete_stock(system_key, stock_key, ctx.tenant_key)


@router.post("/systems/{system_key}/fish-stocks/{stock_key}/mortality", response_model=FishStockResponse)
def record_mortality(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    stock_key: Annotated[str, Path(description="Document key of the fish stock.")],
    body: MortalityCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Record fish deaths against a stock."""
    updated = service.record_mortality(system_key, stock_key, ctx.tenant_key, body.deaths)
    return to_response(updated, FishStockResponse)


@router.get("/systems/{system_key}/fish-stocks/{stock_key}/biomass-history", response_model=BiomassHistoryResponse)
def get_biomass_history(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    stock_key: Annotated[str, Path(description="Document key of the fish stock.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return the current biomass snapshot for a fish stock."""
    return service.get_biomass_history(system_key, stock_key, ctx.tenant_key)


@router.get("/systems/{system_key}/fish-stocks/{stock_key}/mortality-rate", response_model=MortalityRateResponse)
def get_mortality_rate(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    stock_key: Annotated[str, Path(description="Document key of the fish stock.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return the cumulative mortality rate for a fish stock."""
    return service.get_mortality_rate(system_key, stock_key, ctx.tenant_key)


# ── Water tests ─────────────────────────────────────────────────────────


@router.post("/systems/{system_key}/water-tests", response_model=WaterTestResponse, status_code=201)
def record_water_test(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    body: WaterTestCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Record a water-quality measurement for an aquaponic system."""
    water_test = WaterTest(**body.model_dump())
    created = service.record_water_test(system_key, ctx.tenant_key, water_test)
    return to_response(created, WaterTestResponse)


@router.get("/systems/{system_key}/water-tests", response_model=list[WaterTestResponse])
def list_water_tests(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """List an aquaponic system's water tests (paginated, newest first)."""
    tests = service.list_water_tests(system_key, ctx.tenant_key, pagination.offset, pagination.limit)
    return [to_response(t, WaterTestResponse) for t in tests]


@router.get(
    "/systems/{system_key}/water-quality-status",
    response_model=list[WaterQualityEvaluationResponse],
)
def get_water_quality_status(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Evaluate the latest water test against species-specific thresholds."""
    evaluations = service.get_water_quality_status(system_key, ctx.tenant_key)
    return [WaterQualityEvaluationResponse(**e.model_dump()) for e in evaluations]


@router.get("/systems/{system_key}/nitrogen-cycle-chart", response_model=list[NitrogenCyclePoint])
def get_nitrogen_cycle_chart(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return the nitrogen-cycle water-parameter time series for charting."""
    return service.get_nitrogen_cycle_chart(system_key, ctx.tenant_key)


@router.get("/systems/{system_key}/cycling-progress", response_model=CyclingProgressResponse)
def get_cycling_progress(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return the estimated nitrogen-cycling progress of a system."""
    progress = service.get_cycling_progress(system_key, ctx.tenant_key)
    return CyclingProgressResponse(**progress.model_dump())


# ── Feeding ─────────────────────────────────────────────────────────────


@router.post(
    "/systems/{system_key}/fish-stocks/{stock_key}/feeding-events",
    response_model=FishFeedingEventResponse,
    status_code=201,
)
def record_feeding(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    stock_key: Annotated[str, Path(description="Document key of the fish stock.")],
    body: FishFeedingEventCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Record a feeding event for a fish stock."""
    feeding = FishFeedingEvent(**body.model_dump())
    created = service.record_feeding(system_key, stock_key, ctx.tenant_key, feeding)
    return to_response(created, FishFeedingEventResponse)


@router.get("/systems/{system_key}/feeding-events", response_model=list[FishFeedingEventResponse])
def list_feedings(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """List an aquaponic system's feeding events (paginated, newest first)."""
    feedings = service.list_feedings(system_key, ctx.tenant_key, pagination.offset, pagination.limit)
    return [to_response(f, FishFeedingEventResponse) for f in feedings]


@router.get("/systems/{system_key}/feeding-recommendation", response_model=FeedingRecommendationResponse)
def get_feeding_recommendation(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return a daily feed recommendation based on biomass and water temperature."""
    recommendation = service.get_feeding_recommendation(system_key, ctx.tenant_key)
    return FeedingRecommendationResponse(**recommendation.model_dump())


@router.get("/systems/{system_key}/fcr-analysis", response_model=FcrAnalysisResponse)
def get_fcr_analysis(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return the feed-conversion-ratio analysis for an aquaponic system."""
    return service.get_fcr_analysis(system_key, ctx.tenant_key)


# ── Supplementation ─────────────────────────────────────────────────────


@router.post(
    "/systems/{system_key}/supplementation-events",
    response_model=SupplementationEventResponse,
    status_code=201,
)
def record_supplementation(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    body: SupplementationEventCreate,
    ctx: TenantContext = Depends(require_tenant_role(TenantRole.GROWER)),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Record a nutrient-supplementation event for an aquaponic system."""
    event = SupplementationEvent(**body.model_dump())
    created = service.record_supplementation(system_key, ctx.tenant_key, event)
    return to_response(created, SupplementationEventResponse)


@router.get(
    "/systems/{system_key}/supplementation-events",
    response_model=list[SupplementationEventResponse],
)
def list_supplementations(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """List an aquaponic system's supplementation events (paginated, newest first)."""
    events = service.list_supplementations(system_key, ctx.tenant_key, pagination.offset, pagination.limit)
    return [to_response(e, SupplementationEventResponse) for e in events]


@router.get("/systems/{system_key}/deficiency-check", response_model=DeficiencyReportResponse)
def get_deficiency_check(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return a nutrient-deficiency report derived from the latest water test."""
    report = service.get_deficiency_check(system_key, ctx.tenant_key)
    return DeficiencyReportResponse(**report.model_dump())


# ── Safety, alerts & health ─────────────────────────────────────────────


@router.get("/systems/{system_key}/safety-status", response_model=SafetyStatusResponse)
def get_safety_status(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """Return the aggregated safety status (water quality + stocking validation)."""
    return service.get_safety_status(system_key, ctx.tenant_key)


@router.get("/systems/{system_key}/alerts", response_model=list[WaterQualityEvaluationResponse])
def get_alerts(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """List actionable water-quality alerts for an aquaponic system."""
    alerts = service.get_alerts(system_key, ctx.tenant_key)
    return [WaterQualityEvaluationResponse(**a.model_dump()) for a in alerts]


@router.get("/systems/{system_key}/fish-health", response_model=list[HealthAlertResponse])
def get_fish_health(
    system_key: Annotated[str, Path(description="Document key of the aquaponic system.")],
    ctx: TenantContext = Depends(get_current_tenant),
    service: AquaponikService = Depends(get_aquaponik_service),
):
    """List fish-health alerts derived from feeding, water and mortality trends."""
    alerts = service.get_fish_health(system_key, ctx.tenant_key)
    return [HealthAlertResponse(**a.model_dump()) for a in alerts]
