from fastapi import APIRouter, Depends

from app.api.mapping import to_response
from app.api.v1.succession_plans.schemas import (
    GenerateNextRunResponse,
    GenerateRunsResponse,
    GenerateRunSummary,
    SuccessionPlanCreate,
    SuccessionPlanResponse,
    SuccessionPlanUpdate,
)
from app.common.auth import get_current_tenant
from app.common.dependencies import get_succession_plan_service
from app.common.pagination import PaginationParams, get_pagination
from app.domain.models.planting_run import PlantingRun
from app.domain.models.succession_plan import SuccessionPlan
from app.domain.models.tenant_context import TenantContext
from app.domain.services.succession_plan_service import SuccessionPlanService

router = APIRouter(prefix="/succession-plans", tags=["succession-plans"])


def _plan_response(plan: SuccessionPlan) -> SuccessionPlanResponse:
    return to_response(plan, SuccessionPlanResponse)


def _run_summary(run: PlantingRun) -> GenerateRunSummary:
    return GenerateRunSummary(
        run_key=run.key or "",
        name=run.name,
        succession_sequence=run.succession_sequence,
        succession_total=run.succession_total,
        planned_start_date=run.planned_start_date,
    )


@router.get("", response_model=list[SuccessionPlanResponse])
def list_succession_plans(
    pagination: PaginationParams = Depends(get_pagination),
    ctx: TenantContext = Depends(get_current_tenant),
    service: SuccessionPlanService = Depends(get_succession_plan_service),
):
    items, _total = service.list_plans(pagination.offset, pagination.limit, tenant_key=ctx.tenant_key)
    return [_plan_response(p) for p in items]


@router.post("", response_model=SuccessionPlanResponse, status_code=201)
def create_succession_plan(
    body: SuccessionPlanCreate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SuccessionPlanService = Depends(get_succession_plan_service),
):
    plan = SuccessionPlan(**body.model_dump(), tenant_key=ctx.tenant_key)
    created = service.create_plan(plan)
    return _plan_response(created)


@router.get("/{key}", response_model=SuccessionPlanResponse)
def get_succession_plan(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SuccessionPlanService = Depends(get_succession_plan_service),
):
    plan = service.get_plan(key, tenant_key=ctx.tenant_key)
    return _plan_response(plan)


@router.put("/{key}", response_model=SuccessionPlanResponse)
def update_succession_plan(
    key: str,
    body: SuccessionPlanUpdate,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SuccessionPlanService = Depends(get_succession_plan_service),
):
    data = body.model_dump(exclude_unset=True)
    updated = service.update_plan(key, data, tenant_key=ctx.tenant_key)
    return _plan_response(updated)


@router.delete("/{key}", status_code=204)
def delete_succession_plan(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SuccessionPlanService = Depends(get_succession_plan_service),
):
    service.delete_plan(key, tenant_key=ctx.tenant_key)


@router.post("/{key}/generate", response_model=GenerateRunsResponse, status_code=201)
def generate_runs(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SuccessionPlanService = Depends(get_succession_plan_service),
):
    plan, runs = service.generate_runs(key, tenant_key=ctx.tenant_key)
    return GenerateRunsResponse(
        plan=_plan_response(plan),
        generated_count=len(runs),
        runs=[_run_summary(r) for r in runs],
    )


@router.post("/{key}/generate-next", response_model=GenerateNextRunResponse, status_code=201)
def generate_next_run(
    key: str,
    ctx: TenantContext = Depends(get_current_tenant),
    service: SuccessionPlanService = Depends(get_succession_plan_service),
):
    plan, run = service.generate_next_run(key, tenant_key=ctx.tenant_key)
    return GenerateNextRunResponse(
        plan=_plan_response(plan),
        generated=run is not None,
        run=_run_summary(run) if run is not None else None,
    )
