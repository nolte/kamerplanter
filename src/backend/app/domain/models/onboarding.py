from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import ExperienceLevel


class PlantConfig(BaseModel):
    """Per-species plant instance configuration chosen during onboarding."""

    species_key: str
    count: int = Field(default=1, ge=1, le=50)
    initial_phase: str = "germination"


class OnboardingState(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    completed: bool = False
    skipped: bool = False
    completed_at: datetime | None = None
    selected_kit_id: str | None = None
    selected_experience_level: ExperienceLevel | None = None
    wizard_step: int = Field(default=0, ge=0, le=6)
    created_entities: dict[str, list[str]] = Field(default_factory=dict)
    site_name: str = ""
    site_type: str | None = None
    selected_site_key: str | None = None
    plant_count: int | None = None
    plant_configs: list[PlantConfig] = Field(default_factory=list)
    favorite_species_keys: list[str] = Field(default_factory=list)
    favorite_nutrient_plan_keys: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
