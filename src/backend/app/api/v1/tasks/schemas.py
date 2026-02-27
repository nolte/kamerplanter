from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    created_by: str = ""
    version: str = "1.0"
    species_compatible: list[str] = Field(default_factory=list)
    growth_system: str | None = None
    difficulty_level: str = "intermediate"
    category: str = "maintenance"
    tags: list[str] = Field(default_factory=list)
    is_system: bool = False


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
    created_at: datetime | None = None
    updated_at: datetime | None = None


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
    tools_required: list[str] = Field(default_factory=list)
    skill_level: str = "beginner"
    optimal_time_of_day: str | None = None
    workflow_template_key: str | None = None
    sequence_order: int = 0


class TaskTemplateResponse(BaseModel):
    key: str
    name: str
    instruction: str
    category: str
    trigger_type: str
    trigger_phase: str | None = None
    days_offset: int
    stress_level: str
    estimated_duration_minutes: int | None = None
    requires_photo: bool
    tools_required: list[str]
    skill_level: str
    optimal_time_of_day: str | None = None
    workflow_template_key: str | None = None
    sequence_order: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    instruction: str = ""
    category: str = "maintenance"
    plant_key: str | None = None
    due_date: datetime | None = None
    priority: str = "medium"
    estimated_duration_minutes: int | None = None
    requires_photo: bool = False


class TaskUpdate(BaseModel):
    name: str | None = None
    instruction: str | None = None
    category: str | None = None
    due_date: datetime | None = None
    priority: str | None = None
    estimated_duration_minutes: int | None = None
    requires_photo: bool | None = None


class TaskResponse(BaseModel):
    key: str
    name: str
    instruction: str
    category: str
    plant_key: str | None = None
    due_date: datetime | None = None
    status: str
    priority: str
    estimated_duration_minutes: int | None = None
    actual_duration_minutes: int | None = None
    requires_photo: bool
    photo_refs: list[str]
    completion_notes: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    template_key: str | None = None
    workflow_execution_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TaskCompleteRequest(BaseModel):
    completion_notes: str | None = None
    actual_duration_minutes: int | None = None


class HSTValidateRequest(BaseModel):
    task_name: str
    current_phase: str
    recent_hst_tasks: list[dict] = Field(default_factory=list)
    species_name: str = ""


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
