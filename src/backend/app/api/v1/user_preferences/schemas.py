from pydantic import BaseModel, Field

from app.common.enums import ExperienceLevel, ModuleVisibilityState
from app.domain.models.user_preference import DashboardLayout


class UserPreferenceResponse(BaseModel):
    key: str
    user_key: str
    experience_level: ExperienceLevel
    onboarding_completed: bool
    locale: str
    theme: str
    watering_can_liters: float
    smart_home_enabled: bool
    # UI-NFR-019 Kiosk mode.
    kiosk_enabled: bool = False
    high_contrast: bool = False
    module_visibility: dict[str, ModuleVisibilityState] = Field(default_factory=dict)
    dashboard_layout: DashboardLayout | None = None


class UserPreferenceUpdate(BaseModel):
    experience_level: ExperienceLevel | None = None
    onboarding_completed: bool | None = None
    locale: str | None = None
    theme: str | None = None
    watering_can_liters: float | None = None
    smart_home_enabled: bool | None = None
    # UI-NFR-019 Kiosk mode.
    kiosk_enabled: bool | None = None
    high_contrast: bool | None = None
    module_visibility: dict[str, ModuleVisibilityState] | None = None
    # REQ-045 — explicit null resets to the experience-level default; a field
    # left unset leaves the stored layout untouched. The router therefore dumps
    # with exclude_unset so a deliberate null is not swallowed.
    dashboard_layout: DashboardLayout | None = None
