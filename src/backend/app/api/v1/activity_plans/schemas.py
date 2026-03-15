from pydantic import BaseModel, Field


class ActivityPlanGenerateRequest(BaseModel):
    species_key: str
    lifecycle_key: str | None = None
    growth_system: str | None = None
    skill_level: str | None = None
    force_regenerate: bool = False


class TaskTemplateResponse(BaseModel):
    key: str
    name: str
    name_de: str = ""
    instruction: str = ""
    instruction_de: str = ""
    trigger_phase: str | None = None
    phase_display_name: str = ""
    phase_duration_days: int = 0
    phase_stress_tolerance: str = ""
    days_offset: int = 0
    rationale: str = ""
    rationale_de: str = ""
    category: str = ""
    stress_level: str = ""
    skill_level: str = ""
    estimated_duration_minutes: int | None = None
    tools_required: list[str] = Field(default_factory=list)
    recovery_days: int = 0
    is_optional: bool = False
    enabled: bool = True
    activity_key: str | None = None
    description: str = ""
    description_de: str = ""


class ActivityPlanResponse(BaseModel):
    workflow_template_key: str
    name: str
    species_name: str = ""
    species_key: str | None = None
    auto_generated: bool = True
    growth_system: str | None = None
    skill_level_filter: str | None = None
    total_activities: int = 0
    total_duration_days: int = 0
    templates: list[TaskTemplateResponse] = Field(default_factory=list)


class ActivityPlanApplyRequest(BaseModel):
    workflow_template_key: str
    plant_key: str | None = None
    run_key: str | None = None
    tenant_key: str = ""


class ActivityPlanApplyResponse(BaseModel):
    created_count: int = 0
    task_keys: list[str] = Field(default_factory=list)
    plant_count: int | None = None
    total_tasks: int | None = None


class TaskTemplateUpdateRequest(BaseModel):
    enabled: bool | None = None
    days_offset: int | None = None
    trigger_phase: str | None = None
