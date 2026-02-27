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


class WorkflowTemplate(BaseModel):
    key: str | None = Field(default=None, alias="_key")
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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TaskTemplate(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str = Field(min_length=1, max_length=200)
    instruction: str = ""
    category: TaskCategory = TaskCategory.MAINTENANCE
    trigger_type: TaskTriggerType = TaskTriggerType.MANUAL
    trigger_phase: str | None = None
    days_offset: int = Field(default=0, ge=0)
    stress_level: StressLevel = StressLevel.NONE
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    requires_photo: bool = False
    tools_required: list[str] = Field(default_factory=list)
    skill_level: SkillLevel = SkillLevel.BEGINNER
    optimal_time_of_day: TimeOfDay | None = None
    workflow_template_key: str | None = None
    sequence_order: int = Field(default=0, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class Task(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str = Field(min_length=1, max_length=200)
    instruction: str = ""
    category: TaskCategory = TaskCategory.MAINTENANCE
    plant_key: str | None = None
    due_date: datetime | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    actual_duration_minutes: int | None = Field(default=None, ge=0)
    requires_photo: bool = False
    photo_refs: list[str] = Field(default_factory=list)
    completion_notes: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    template_key: str | None = None
    workflow_execution_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class WorkflowExecution(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    workflow_template_key: str = ""
    plant_key: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    completion_percentage: float = Field(default=0, ge=0, le=100)
    on_schedule: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
