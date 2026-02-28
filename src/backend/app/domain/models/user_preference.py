from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import ExperienceLevel


class UserPreference(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    user_key: str
    experience_level: ExperienceLevel = ExperienceLevel.BEGINNER
    onboarding_completed: bool = False
    locale: str = "de"
    theme: str = "system"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
