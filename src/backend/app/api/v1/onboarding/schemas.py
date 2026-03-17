from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import ExperienceLevel
from app.domain.models.onboarding import PlantConfig


class OnboardingStateResponse(BaseModel):
    key: str
    user_key: str
    completed: bool
    skipped: bool
    completed_at: datetime | None = None
    selected_kit_id: str | None = None
    selected_experience_level: ExperienceLevel | None = None
    wizard_step: int
    created_entities: dict[str, list[str]]
    site_name: str = ""
    site_type: str | None = None
    selected_site_key: str | None = None
    plant_count: int | None = None
    plant_configs: list[PlantConfig] = Field(default_factory=list)
    favorite_species_keys: list[str] = Field(default_factory=list)
    favorite_nutrient_plan_keys: list[str] = Field(default_factory=list)


class PlantConfigSchema(BaseModel):
    species_key: str
    count: int = Field(default=1, ge=1, le=50)
    initial_phase: str = "germination"


class OnboardingCompleteRequest(BaseModel):
    kit_id: str | None = None
    experience_level: ExperienceLevel | None = None
    site_name: str = ""
    selected_site_key: str | None = None
    plant_count: int = Field(default=3, ge=1, le=50)
    plant_configs: list[PlantConfigSchema] = Field(default_factory=list)
    has_ro_system: bool | None = None
    tap_water_ec_ms: float | None = Field(default=None, ge=0, le=2.0)
    tap_water_ph: float | None = Field(default=None, ge=3.0, le=10.0)
    favorite_species_keys: list[str] = Field(default_factory=list)
    favorite_nutrient_plan_keys: list[str] = Field(default_factory=list)
    smart_home_enabled: bool | None = None


class OnboardingProgressUpdate(BaseModel):
    wizard_step: int = Field(ge=0, le=6)
    selected_kit_id: str | None = None
    selected_experience_level: ExperienceLevel | None = None
    site_name: str | None = None
    site_type: str | None = None
    selected_site_key: str | None = None
    plant_count: int | None = Field(default=None, ge=1, le=50)
    plant_configs: list[PlantConfigSchema] | None = None
    favorite_species_keys: list[str] | None = None
    favorite_nutrient_plan_keys: list[str] | None = None
    smart_home_enabled: bool | None = None
