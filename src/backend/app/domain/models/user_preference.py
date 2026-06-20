from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.enums import ExperienceLevel, ModuleVisibilityState

CORE_MODULE_KEYS: frozenset[str] = frozenset({"dashboard", "plants", "locations", "settings", "onboarding"})


class UserPreference(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    experience_level: ExperienceLevel = ExperienceLevel.BEGINNER
    onboarding_completed: bool = False
    locale: str = "de"
    theme: str = "system"
    temperature_unit: str = "celsius"
    watering_can_liters: float = 10.0
    smart_home_enabled: bool = False
    module_visibility: dict[str, ModuleVisibilityState] = Field(
        default_factory=dict,
        description=(
            "Personal per-module visibility overrides. Key = module key from the "
            "frontend catalog; value = explicit visibility. Modules without an "
            "entry follow the experience level (REQ-021). Core modules are ignored."
        ),
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("module_visibility", mode="after")
    @classmethod
    def _drop_core_overrides(cls, value: dict[str, ModuleVisibilityState]) -> dict[str, ModuleVisibilityState]:
        return {k: v for k, v in value.items() if k not in CORE_MODULE_KEYS}
