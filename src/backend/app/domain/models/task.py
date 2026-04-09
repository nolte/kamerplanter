from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import (
    SkillLevel,
    StressLevel,
    TaskCategory,
    TaskPriority,
    TaskStatus,
    TaskTriggerType,
    TimeOfDay,
)


class ChecklistItem(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    done: bool = False
    order: int = Field(default=0, ge=0)


class WorkflowTemplate(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    created_by: str = Field(default="", max_length=200)
    version: str = Field(default="1.0", max_length=20)
    species_compatible: list[str] = Field(default_factory=list)
    growth_system: str | None = None
    difficulty_level: SkillLevel = SkillLevel.INTERMEDIATE
    category: TaskCategory = TaskCategory.MAINTENANCE
    tags: list[str] = Field(default_factory=list)
    is_system: bool = False
    auto_generated: bool = False
    species_key: str | None = None
    lifecycle_key: str | None = None
    phase_sequence_key: str | None = None
    skill_level_filter: str | None = None
    total_duration_days: int = 0
    target_entity_types: list[str] = Field(default_factory=lambda: ["plant_instance"])
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class WorkflowPhase(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    workflow_template_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    phase_order: int = Field(default=0, ge=0)
    duration_days: int = Field(default=0, ge=0)
    stress_tolerance: str = ""
    trigger_phase: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TaskTemplate(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str = Field(min_length=1, max_length=200)
    name_de: str = ""
    instruction: str = ""
    instruction_de: str = ""
    description: str = ""
    description_de: str = ""
    category: TaskCategory = TaskCategory.MAINTENANCE
    trigger_type: TaskTriggerType = TaskTriggerType.MANUAL
    trigger_phase: str | None = None
    days_offset: int = Field(default=0, ge=0)
    stress_level: StressLevel = StressLevel.NONE
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    requires_photo: bool = False
    timer_duration_seconds: int | None = Field(default=None, ge=1)
    timer_label: str | None = None
    tools_required: list[str] = Field(default_factory=list)
    skill_level: SkillLevel = SkillLevel.BEGINNER
    optimal_time_of_day: TimeOfDay | None = None
    activity_key: str | None = None
    workflow_template_key: str | None = None
    workflow_phase_key: str | None = None
    phase_definition_key: str | None = None
    sequence_order: int = Field(default=0, ge=0)
    default_checklist: list[ChecklistItem] = Field(default_factory=list)
    require_all_checklist_items: bool = False
    rationale: str = ""
    rationale_de: str = ""
    recovery_days: int = 0
    is_optional: bool = False
    enabled: bool = True
    phase_display_name: str = ""
    phase_duration_days: int = 0
    phase_stress_tolerance: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class Task(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    name: str = Field(min_length=1, max_length=200)
    name_de: str = ""
    instruction: str = ""
    instruction_de: str = ""
    category: TaskCategory = TaskCategory.MAINTENANCE
    entity_key: str | None = None
    entity_type: str | None = None
    due_date: datetime | None = None
    scheduled_time: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    skill_level: SkillLevel = SkillLevel.BEGINNER
    stress_level: StressLevel = StressLevel.NONE
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    actual_duration_minutes: int | None = Field(default=None, ge=0)
    requires_photo: bool = False
    photo_refs: list[str] = Field(default_factory=list)
    timer_duration_seconds: int | None = Field(default=None, ge=1)
    timer_label: str | None = None
    completion_notes: str | None = None
    difficulty_rating: int | None = Field(default=None, ge=1, le=5)
    quality_rating: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)
    checklist: list[ChecklistItem] = Field(default_factory=list)
    assigned_to_user_key: str | None = None
    recurrence_rule: str | None = None
    recurrence_end_date: datetime | None = None
    parent_recurring_task_key: str | None = None
    trigger_phase: str | None = None
    trigger_phase_override: str | None = None
    reopened_at: datetime | None = None
    reopened_from_status: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    activity_key: str | None = None
    template_key: str | None = None
    workflow_execution_key: str | None = None
    watering_event_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TaskComment(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    task_key: str = ""
    comment_text: str = Field(min_length=1, max_length=2000)
    created_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TaskAuditEntry(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    task_key: str = ""
    changed_at: datetime | None = None
    changed_by: str = ""
    action: str = ""
    field: str | None = None
    old_value: str | None = None
    new_value: str | None = None

    model_config = {"populate_by_name": True}


class WorkflowExecution(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    workflow_template_key: str = ""
    entity_key: str = ""
    entity_type: str = "plant_instance"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    completion_percentage: float = Field(default=0, ge=0, le=100)
    on_schedule: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
