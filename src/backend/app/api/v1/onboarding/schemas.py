
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime

    from app.common.enums import ExperienceLevel


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


class OnboardingCompleteRequest(BaseModel):
    kit_id: str | None = None
    experience_level: ExperienceLevel | None = None
    site_name: str = ""
    plant_count: int = Field(default=3, ge=1, le=50)
    has_ro_system: bool | None = None
    tap_water_ec_ms: float | None = Field(default=None, ge=0, le=2.0)
    tap_water_ph: float | None = Field(default=None, ge=3.0, le=10.0)


class OnboardingProgressUpdate(BaseModel):
    wizard_step: int = Field(ge=0, le=5)
    selected_kit_id: str | None = None
    selected_experience_level: ExperienceLevel | None = None
