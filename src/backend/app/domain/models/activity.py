from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import ActivityCategory, SkillLevel, StressLevel


class Activity(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
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
    applicable_growth_habits: list[str] = Field(
        default_factory=list,
        description="GrowthHabit values this activity applies to (empty = all)",
    )
    applicable_families: list[str] = Field(
        default_factory=list,
        description="Botanical family common names this activity applies to (empty = all)",
    )
    requires_support: bool | None = Field(
        default=None,
        description="If True, only for species with support_required=True",
    )
    requires_container: bool | None = Field(
        default=None,
        description="If True, only for container-suitable species",
    )
    is_system: bool = False
    sort_order: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
