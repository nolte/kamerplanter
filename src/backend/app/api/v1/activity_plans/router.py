from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from app.api.v1.activity_plans.schemas import (
    ActivityPlanApplyRequest,
    ActivityPlanApplyResponse,
    ActivityPlanGenerateRequest,
    ActivityPlanResponse,
    TaskTemplateResponse,
    TaskTemplateUpdateRequest,
)
from app.common.dependencies import get_activity_plan_service, get_task_repo
from app.common.exceptions import NotFoundError, ValidationError

if TYPE_CHECKING:
    from app.domain.services.activity_plan_service import ActivityPlanService

router = APIRouter(prefix="/activity-plans", tags=["activity-plans"])


def _build_response(
    wt,
    templates: list | None = None,
    task_repo=None,
) -> ActivityPlanResponse:
    """Build ActivityPlanResponse from a WorkflowTemplate and its TaskTemplates."""
    if templates is None and task_repo and wt.key:
        templates = task_repo.get_task_templates_for_workflow(wt.key)

    tt_responses = [
        TaskTemplateResponse(
            key=tt.key or "",
            name=tt.name,
            name_de=tt.name_de,
            instruction=tt.instruction,
            instruction_de=tt.instruction_de,
            trigger_phase=tt.trigger_phase,
            phase_display_name=tt.phase_display_name,
            phase_duration_days=tt.phase_duration_days,
            phase_stress_tolerance=tt.phase_stress_tolerance,
            days_offset=tt.days_offset,
            rationale=tt.rationale,
            rationale_de=tt.rationale_de,
            category=tt.category.value if hasattr(tt.category, "value") else str(tt.category),
            stress_level=tt.stress_level.value if hasattr(tt.stress_level, "value") else str(tt.stress_level),
            skill_level=tt.skill_level.value if hasattr(tt.skill_level, "value") else str(tt.skill_level),
            estimated_duration_minutes=tt.estimated_duration_minutes,
            tools_required=list(tt.tools_required),
            recovery_days=tt.recovery_days,
            is_optional=tt.is_optional,
            enabled=tt.enabled,
            activity_key=tt.activity_key,
            description=tt.description,
            description_de=tt.description_de,
        )
        for tt in (templates or [])
    ]

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
    if body.run_key:
        result = service.apply_plan_to_run(
            body.workflow_template_key, body.run_key, body.tenant_key,
        )
        return ActivityPlanApplyResponse(
            created_count=result["total_tasks"],
            task_keys=result["task_keys"],
            plant_count=result["plant_count"],
            total_tasks=result["total_tasks"],
        )

    if body.plant_key:
        result = service.apply_plan_to_plant(
            body.workflow_template_key, body.plant_key, body.tenant_key,
        )
        return ActivityPlanApplyResponse(
            created_count=result["created_count"],
            task_keys=result["task_keys"],
        )

    raise ValidationError("Either plant_key or run_key must be provided.")


@router.patch("/templates/{key}", response_model=TaskTemplateResponse)
def update_task_template(
    key: str,
    body: TaskTemplateUpdateRequest,
    task_repo=Depends(get_task_repo),
) -> TaskTemplateResponse:
    existing = task_repo.get_task_template_by_key(key)
    if not existing:
        raise NotFoundError("TaskTemplate", key)

    if body.enabled is not None:
        existing.enabled = body.enabled
    if body.days_offset is not None:
        existing.days_offset = body.days_offset
    if body.trigger_phase is not None:
        existing.trigger_phase = body.trigger_phase

    updated = task_repo.update_task_template(key, existing)

    return TaskTemplateResponse(
        key=updated.key or "",
        name=updated.name,
        name_de=updated.name_de,
        instruction=updated.instruction,
        instruction_de=updated.instruction_de,
        trigger_phase=updated.trigger_phase,
        phase_display_name=updated.phase_display_name,
        phase_duration_days=updated.phase_duration_days,
        phase_stress_tolerance=updated.phase_stress_tolerance,
        days_offset=updated.days_offset,
        rationale=updated.rationale,
        rationale_de=updated.rationale_de,
        category=updated.category.value if hasattr(updated.category, "value") else str(updated.category),
        stress_level=(
            updated.stress_level.value if hasattr(updated.stress_level, "value")
            else str(updated.stress_level)
        ),
        skill_level=updated.skill_level.value if hasattr(updated.skill_level, "value") else str(updated.skill_level),
        estimated_duration_minutes=updated.estimated_duration_minutes,
        tools_required=list(updated.tools_required),
        recovery_days=updated.recovery_days,
        is_optional=updated.is_optional,
        enabled=updated.enabled,
        activity_key=updated.activity_key,
        description=updated.description,
        description_de=updated.description_de,
    )


@router.delete("/templates/{key}", status_code=204)
def delete_task_template(
    key: str,
    task_repo=Depends(get_task_repo),
) -> None:
    existing = task_repo.get_task_template_by_key(key)
    if not existing:
        raise NotFoundError("TaskTemplate", key)
    task_repo.delete_task_template(key)
