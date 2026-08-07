"""Response mapping shared by the global and the tenant-scoped activity-plan routers.

The two routers serve the same ``TaskTemplateResponse``: the global one inside a
generated plan, the tenant-scoped one after an edit (#992). The mapping lives
here so moving the write routes under ``/t/{tenant_slug}/`` did not fork it.
"""

from app.api.v1.activity_plans.schemas import TaskTemplateResponse
from app.domain.models.task import TaskTemplate


def _enum_value(value: object) -> str:
    """Render an enum-or-string field as the plain string the schema declares."""
    return value.value if hasattr(value, "value") else str(value)


def task_template_response(template: TaskTemplate) -> TaskTemplateResponse:
    """Map a ``TaskTemplate`` onto the activity plan's response schema."""
    return TaskTemplateResponse(
        key=template.key or "",
        name=template.name,
        name_de=template.name_de,
        instruction=template.instruction,
        instruction_de=template.instruction_de,
        trigger_phase=template.trigger_phase,
        phase_display_name=template.phase_display_name,
        phase_duration_days=template.phase_duration_days,
        phase_stress_tolerance=template.phase_stress_tolerance,
        days_offset=template.days_offset,
        rationale=template.rationale,
        rationale_de=template.rationale_de,
        category=_enum_value(template.category),
        stress_level=_enum_value(template.stress_level),
        skill_level=_enum_value(template.skill_level),
        estimated_duration_minutes=template.estimated_duration_minutes,
        tools_required=list(template.tools_required),
        recovery_days=template.recovery_days,
        is_optional=template.is_optional,
        enabled=template.enabled,
        activity_key=template.activity_key,
        description=template.description,
        description_de=template.description_de,
    )
