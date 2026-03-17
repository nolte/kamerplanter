"""Tenant-scoped IPM router.

Only Inspection and TreatmentApplication are tenant-scoped.
Pest, Disease, Treatment remain global reference data.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.v1.ipm.router import _application_response, _inspection_response
from app.api.v1.ipm.schemas import (
    HarvestSafetyResponse,
    InspectionCreate,
    InspectionResponse,
    KarenzPeriodResponse,
    TreatmentApplicationCreate,
    TreatmentApplicationResponse,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_ipm_service
from app.domain.models.ipm import Inspection, TreatmentApplication
from app.domain.models.tenant_context import TenantContext
from app.domain.services.ipm_service import IpmService

router = APIRouter(prefix="/ipm", tags=["ipm"])


@router.post("/plants/{plant_key}/inspections", response_model=InspectionResponse, status_code=201)
def create_inspection(
    plant_key: str,
    body: InspectionCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    inspection = Inspection(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_inspection(plant_key, inspection)
    return _inspection_response(created)


@router.get("/plants/{plant_key}/inspections", response_model=list[InspectionResponse])
def list_inspections(
    plant_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    inspections, _ = service.get_inspections(plant_key, offset, limit)
    return [_inspection_response(i) for i in inspections]


@router.post(
    "/plants/{plant_key}/treatment-applications",
    response_model=TreatmentApplicationResponse,
    status_code=201,
)
def create_treatment_application(
    plant_key: str,
    body: TreatmentApplicationCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    app = TreatmentApplication(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_treatment_application(plant_key, app)
    return _application_response(created)


@router.get("/plants/{plant_key}/treatment-applications", response_model=list[TreatmentApplicationResponse])
def list_treatment_applications(
    plant_key: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    apps, _ = service.get_applications(plant_key, offset, limit)
    return [_application_response(a) for a in apps]


@router.get("/plants/{plant_key}/karenz", response_model=list[KarenzPeriodResponse])
def get_karenz_periods(
    plant_key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    return service.get_karenz_periods(plant_key)


@router.get("/plants/{plant_key}/harvest-safety", response_model=HarvestSafetyResponse)
def check_harvest_safety(
    plant_key: str,
    planned_date: str | None = None,
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    pd = datetime.fromisoformat(planned_date) if planned_date else None
    can_harvest, blocking = service.check_harvest_safety(plant_key, pd)
    return HarvestSafetyResponse(can_harvest=can_harvest, blocking_treatments=blocking)


@router.get("/plants/{plant_key}/inspection-schedule")
def get_inspection_schedule(
    plant_key: str,
    current_phase: str = Query("vegetative"),
    pressure_level: str = Query("none"),
    ctx: TenantContext = Depends(get_current_tenant),
    service: IpmService = Depends(get_ipm_service),
):
    return service.get_inspection_schedule(plant_key, current_phase, pressure_level)
