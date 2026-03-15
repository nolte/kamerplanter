from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import ActivityCategory, SkillLevel, StressLevel


class ActivityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    name_de: str = ""
    description: str = ""
    description_de: str = ""
    category: ActivityCategory = ActivityCategory.GENERAL
    stress_level: StressLevel = StressLevel.NONE
    skill_level: SkillLevel = SkillLevel.BEGINNER
    recovery_days_default: int = Field(default=0, ge=0)
    recovery_days_by_species: dict[str, int] = Field(default_factory=dict)
    forbidden_phases: list[str] = Field(default_factory=list)
    restricted_sub_phases: list[str] = Field(default_factory=list)
    tools_required: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    requires_photo: bool = False
    species_compatible: list[str] = Field(default_factory=list)
    sort_order: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)


class ActivityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    name_de: str | None = None
    description: str | None = None
    description_de: str | None = None
    category: ActivityCategory | None = None
    stress_level: StressLevel | None = None
    skill_level: SkillLevel | None = None
    recovery_days_default: int | None = Field(default=None, ge=0)
    recovery_days_by_species: dict[str, int] | None = None
    forbidden_phases: list[str] | None = None
    restricted_sub_phases: list[str] | None = None
    tools_required: list[str] | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    requires_photo: bool | None = None
    species_compatible: list[str] | None = None
    sort_order: int | None = Field(default=None, ge=0)
    tags: list[str] | None = None


class ActivityResponse(BaseModel):
    key: str
    tenant_key: str = ""
    name: str
    name_de: str = ""
    description: str = ""
    description_de: str = ""
    category: ActivityCategory
    stress_level: StressLevel
    skill_level: SkillLevel
    recovery_days_default: int = 0
    recovery_days_by_species: dict[str, int] = Field(default_factory=dict)
    forbidden_phases: list[str] = Field(default_factory=list)
    restricted_sub_phases: list[str] = Field(default_factory=list)
    tools_required: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int | None = None
    requires_photo: bool = False
    species_compatible: list[str] = Field(default_factory=list)
    is_system: bool = False
    sort_order: int = 0
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
