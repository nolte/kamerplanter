from datetime import datetime

from pydantic import BaseModel, Field

# ── Checklist ──


class ChecklistItemSchema(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    done: bool = False
    order: int = Field(default=0, ge=0)


# ── Workflow Templates ──


class WorkflowTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    created_by: str = ""
    version: str = "1.0"
    species_compatible: list[str] = Field(default_factory=list)
    species_key: str | None = None
    growth_system: str | None = None
    difficulty_level: str = "intermediate"
    category: str = "maintenance"
    tags: list[str] = Field(default_factory=list)
    is_system: bool = False


class WorkflowTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    version: str | None = None
    species_compatible: list[str] | None = None
    growth_system: str | None = None
    difficulty_level: str | None = None
    category: str | None = None
    tags: list[str] | None = None


class WorkflowTemplateResponse(BaseModel):
    key: str
    name: str
    description: str | None = None
    created_by: str
    version: str
    species_compatible: list[str]
    growth_system: str | None = None
    difficulty_level: str
    category: str
    tags: list[str]
    is_system: bool
    auto_generated: bool = False
    species_key: str | None = None
    species_name: str = ""
    total_duration_days: int = 0
    assigned_plant_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Task Templates ──


class TaskTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    instruction: str = ""
    category: str = "maintenance"
    trigger_type: str = "manual"
    trigger_phase: str | None = None
    days_offset: int = 0
    stress_level: str = "none"
    estimated_duration_minutes: int | None = None
    requires_photo: bool = False
    timer_duration_seconds: int | None = None
    timer_label: str | None = None
    tools_required: list[str] = Field(default_factory=list)
    skill_level: str = "beginner"
    optimal_time_of_day: str | None = None
    workflow_template_key: str | None = None
    sequence_order: int = 0
    default_checklist: list[ChecklistItemSchema] = Field(default_factory=list)
    require_all_checklist_items: bool = False


class TaskTemplateUpdate(BaseModel):
    name: str | None = None
    instruction: str | None = None
    category: str | None = None
    trigger_type: str | None = None
    trigger_phase: str | None = None
    days_offset: int | None = None
    stress_level: str | None = None
    estimated_duration_minutes: int | None = None
    requires_photo: bool | None = None
    timer_duration_seconds: int | None = None
    timer_label: str | None = None
    tools_required: list[str] | None = None
    skill_level: str | None = None
    optimal_time_of_day: str | None = None
    sequence_order: int | None = None
    default_checklist: list[ChecklistItemSchema] | None = None
    require_all_checklist_items: bool | None = None


class TaskTemplateResponse(BaseModel):
    key: str
    name: str
    name_de: str = ""
    instruction: str
    instruction_de: str = ""
    description: str = ""
    description_de: str = ""
    rationale: str = ""
    rationale_de: str = ""
    category: str
    trigger_type: str
    trigger_phase: str | None = None
    phase_display_name: str = ""
    phase_duration_days: int = 0
    phase_stress_tolerance: str = ""
    days_offset: int
    stress_level: str
    estimated_duration_minutes: int | None = None
    requires_photo: bool
    timer_duration_seconds: int | None = None
    timer_label: str | None = None
    tools_required: list[str]
    skill_level: str
    optimal_time_of_day: str | None = None
    workflow_template_key: str | None = None
    activity_key: str | None = None
    sequence_order: int
    recovery_days: int = 0
    is_optional: bool = False
    enabled: bool = True
    default_checklist: list[ChecklistItemSchema] = Field(default_factory=list)
    require_all_checklist_items: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Tasks ──


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    name_de: str = ""
    instruction: str = ""
    instruction_de: str = ""
    category: str = "maintenance"
    plant_key: str | None = None
    due_date: datetime | None = None
    scheduled_time: str | None = None
    priority: str = "medium"
    skill_level: str = "beginner"
    stress_level: str = "none"
    estimated_duration_minutes: int | None = None
    requires_photo: bool = False
    timer_duration_seconds: int | None = None
    timer_label: str | None = None
    tags: list[str] = Field(default_factory=list)
    checklist: list[ChecklistItemSchema] = Field(default_factory=list)
    assigned_to_user_key: str | None = None
    recurrence_rule: str | None = None
    recurrence_end_date: datetime | None = None
    trigger_phase: str | None = None


class TaskUpdate(BaseModel):
    name: str | None = None
    instruction: str | None = None
    category: str | None = None
    plant_key: str | None = None
    due_date: datetime | None = None
    scheduled_time: str | None = None
    priority: str | None = None
    skill_level: str | None = None
    stress_level: str | None = None
    estimated_duration_minutes: int | None = None
    requires_photo: bool | None = None
    timer_duration_seconds: int | None = None
    timer_label: str | None = None
    tags: list[str] | None = None
    checklist: list[ChecklistItemSchema] | None = None
    assigned_to_user_key: str | None = None
    recurrence_rule: str | None = None
    recurrence_end_date: datetime | None = None
    trigger_phase_override: str | None = None


class TaskResponse(BaseModel):
    key: str
    name: str
    name_de: str = ""
    instruction: str
    instruction_de: str = ""
    category: str
    plant_key: str | None = None
    due_date: datetime | None = None
    scheduled_time: str | None = None
    status: str
    priority: str
    skill_level: str = "beginner"
    stress_level: str = "none"
    estimated_duration_minutes: int | None = None
    actual_duration_minutes: int | None = None
    requires_photo: bool
    photo_refs: list[str]
    timer_duration_seconds: int | None = None
    timer_label: str | None = None
    completion_notes: str | None = None
    difficulty_rating: int | None = None
    quality_rating: int | None = None
    tags: list[str] = Field(default_factory=list)
    checklist: list[ChecklistItemSchema] = Field(default_factory=list)
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
    planting_run_key: str | None = None
    watering_event_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PhotoUploadResponse(BaseModel):
    url: str
    filename: str
    size_bytes: int


class TaskCompleteRequest(BaseModel):
    completion_notes: str | None = None
    actual_duration_minutes: int | None = None
    photo_refs: list[str] = Field(default_factory=list)
    difficulty_rating: int | None = Field(default=None, ge=1, le=5)
    quality_rating: int | None = Field(default=None, ge=1, le=5)


class TaskCloneRequest(BaseModel):
    target_plant_key: str | None = None
    due_date_offset_days: int | None = None


class TaskReopenRequest(BaseModel):
    """Empty body — action is implied by the endpoint."""


# ── Batch Operations ──


class BatchStatusRequest(BaseModel):
    task_keys: list[str] = Field(min_length=1)
    action: str = Field(description="start, complete, or skip")
    completion_notes: str | None = None


class BatchDeleteRequest(BaseModel):
    task_keys: list[str] = Field(min_length=1)


class BatchAssignRequest(BaseModel):
    task_keys: list[str] = Field(min_length=1)
    assigned_to_user_key: str


class BatchResultItem(BaseModel):
    key: str
    error: str


class BatchResponse(BaseModel):
    succeeded: list[str]
    failed: list[BatchResultItem]


# ── Comments ──


class TaskCommentCreate(BaseModel):
    comment_text: str = Field(min_length=1, max_length=2000)


class TaskCommentUpdate(BaseModel):
    comment_text: str = Field(min_length=1, max_length=2000)


class TaskCommentResponse(BaseModel):
    key: str
    task_key: str
    comment_text: str
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── Audit / History ──


class TaskAuditEntryResponse(BaseModel):
    key: str
    task_key: str
    changed_at: datetime | None = None
    changed_by: str
    action: str
    field: str | None = None
    old_value: str | None = None
    new_value: str | None = None


# ── HST Validation ──


class HSTValidateRequest(BaseModel):
    task_name: str
    current_phase: str
    recent_hst_tasks: list[dict] = Field(default_factory=list)
    species_name: str = ""


# ── Workflows ──


class WorkflowInstantiateRequest(BaseModel):
    plant_key: str


class WorkflowExecutionResponse(BaseModel):
    key: str
    workflow_template_key: str
    plant_key: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    completion_percentage: float
    on_schedule: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkflowAddTaskRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    instruction: str = ""
    category: str = "maintenance"
    due_date: datetime | None = None
    priority: str = "medium"
    trigger_phase: str | None = None
    estimated_duration_minutes: int | None = None
    tags: list[str] = Field(default_factory=list)
    checklist: list[ChecklistItemSchema] = Field(default_factory=list)
