
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime

    from app.common.enums import ExperienceLevel


class OnboardingState(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    completed: bool = False
    skipped: bool = False
    completed_at: datetime | None = None
    selected_kit_id: str | None = None
    selected_experience_level: ExperienceLevel | None = None
    wizard_step: int = Field(default=0, ge=0, le=5)
    created_entities: dict[str, list[str]] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
