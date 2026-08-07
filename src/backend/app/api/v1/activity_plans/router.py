"""Global activity-plan routes: generate a plan, apply it to a run or plant.

The two *write* routes on a plan's task templates (``PATCH``/``DELETE
/templates/{key}``) used to live here as well, unanchored — see
``app/api/v1/activity_plans/tenant_router.py``, which now serves them under
``/t/{tenant_slug}/`` with a tenant context to verify against (#992).
"""

from fastapi import APIRouter, Depends

from app.api.v1.activity_plans.mapping import task_template_response
from app.api.v1.activity_plans.schemas import (
    ActivityPlanApplyRequest,
    ActivityPlanApplyResponse,
    ActivityPlanGenerateRequest,
    ActivityPlanResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_activity_plan_service, get_task_repo
from app.common.exceptions import ValidationError
from app.common.openapi_responses import AUTH_RESPONSES, NOT_FOUND_RESPONSE
from app.domain.services.activity_plan_service import ActivityPlanService

router = APIRouter(
    prefix="/activity-plans",
    tags=["activity-plans"],
    dependencies=[Depends(get_current_user)],
    responses={**AUTH_RESPONSES, **NOT_FOUND_RESPONSE},
)


def _build_response(
    wt,
    templates: list | None = None,
    task_repo=None,
) -> ActivityPlanResponse:
    """Build ActivityPlanResponse from a WorkflowTemplate and its TaskTemplates."""
    if templates is None and task_repo and wt.key:
        templates = task_repo.get_task_templates_for_workflow(wt.key)

    tt_responses = [task_template_response(tt) for tt in (templates or [])]

    return ActivityPlanResponse(
        workflow_template_key=wt.key or "",
        name=wt.name,
        species_name=wt.name,
        species_key=wt.species_key,
        auto_generated=wt.auto_generated,
        growth_system=wt.growth_system,
        skill_level_filter=wt.skill_level_filter,
        total_activities=len(tt_responses),
        total_duration_days=wt.total_duration_days,
        templates=tt_responses,
    )


@router.post("/generate", response_model=ActivityPlanResponse)
def generate_plan(
    body: ActivityPlanGenerateRequest,
    service: ActivityPlanService = Depends(get_activity_plan_service),
    task_repo=Depends(get_task_repo),
) -> ActivityPlanResponse:
    """Generate or fetch the workflow-template activity plan for a species."""
    if body.force_regenerate:
        wt = service.regenerate_for_species(
            species_key=body.species_key,
            lifecycle_key=body.lifecycle_key,
            growth_system=body.growth_system,
            skill_level=body.skill_level,
        )
    else:
        wt = service.get_or_generate_for_species(
            species_key=body.species_key,
            lifecycle_key=body.lifecycle_key,
            growth_system=body.growth_system,
            skill_level=body.skill_level,
        )
    return _build_response(wt, task_repo=task_repo)


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
