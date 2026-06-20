from pydantic import BaseModel, Field

from app.common.enums import ExperienceLevel, ModuleVisibilityState


class UserPreferenceResponse(BaseModel):
    key: str
    user_key: str
    experience_level: ExperienceLevel
    onboarding_completed: bool
    locale: str
    theme: str
    watering_can_liters: float
    smart_home_enabled: bool
    module_visibility: dict[str, ModuleVisibilityState] = Field(default_factory=dict)


class UserPreferenceUpdate(BaseModel):
    experience_level: ExperienceLevel | None = None
    onboarding_completed: bool | None = None
    locale: str | None = None
    theme: str | None = None
    watering_can_liters: float | None = None
    smart_home_enabled: bool | None = None
    module_visibility: dict[str, ModuleVisibilityState] | None = None
