"""Global activity-plan routes: apply a plan to a run or plant.

The two *write* routes on a plan's task templates (``PATCH``/``DELETE
/templates/{key}``) used to live here as well, unanchored — see
``app/api/v1/activity_plans/tenant_router.py``, which now serves them under
``/t/{tenant_slug}/`` with a tenant context to verify against (#992).

``POST /generate`` followed them there (#1003). It reads and writes the plan a
tenant sees, and under copy-on-write that plan is *per caller*: the shared
template until the tenant has edited it, their private copy afterwards. A route
that does not know its caller's tenant cannot answer that question, so the
lookup ``ActivityPlanService.get_or_generate_for_species`` performs would have
kept handing every tenant the same shared row — which is #1003 itself.

``POST /apply`` stays here: it takes its tenant from the request body, which is
its own open defect (#1000) and a different change from this one.
"""

from fastapi import APIRouter, Depends

from app.api.v1.activity_plans.schemas import (
    ActivityPlanApplyRequest,
    ActivityPlanApplyResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_activity_plan_service
from app.common.exceptions import ValidationError
from app.common.openapi_responses import AUTH_RESPONSES, NOT_FOUND_RESPONSE
from app.domain.services.activity_plan_service import ActivityPlanService

router = APIRouter(
    prefix="/activity-plans",
    tags=["activity-plans"],
    dependencies=[Depends(get_current_user)],
    responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE},
)


@router.post("/apply", response_model=ActivityPlanApplyResponse)
def apply_plan(
    body: ActivityPlanApplyRequest,
    service: ActivityPlanService = Depends(get_activity_plan_service),
) -> ActivityPlanApplyResponse:
    """Apply an activity plan to a planting run or a single plant."""
    if body.run_key:
        result = service.apply_plan_to_run(
            body.workflow_template_key,
            body.run_key,
            body.tenant_key,
        )
        return ActivityPlanApplyResponse(
            created_count=result["total_tasks"],
            task_keys=result["task_keys"],
            plant_count=result["plant_count"],
            total_tasks=result["total_tasks"],
        )

    if body.plant_key:
        result = service.apply_plan_to_plant(
            body.workflow_template_key,
            body.plant_key,
            body.tenant_key,
        )
        return ActivityPlanApplyResponse(
            created_count=result["created_count"],
            task_keys=result["task_keys"],
        )

    raise ValidationError("Either plant_key or run_key must be provided.")
