from pydantic import BaseModel, Field

from app.common.enums import ExperienceLevel, ModuleVisibilityState
from app.domain.models.user_preference import DashboardLayout


class UserPreferenceResponse(BaseModel):
    #: ``""`` until the row exists. Reading preferences no longer creates it
    #: (#1461): a user who has never stated a preference gets the defaults, and
    #: the first PATCH materialises the document. Every other field carries the
    #: same value it would have carried had the read written one, so the response
    #: shape is unchanged — ``to_response`` already coalesces an absent key to
    #: ``""`` everywhere in this API, which is why this stays a required ``str``
    #: rather than becoming nullable and forcing every client to re-type it.
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
