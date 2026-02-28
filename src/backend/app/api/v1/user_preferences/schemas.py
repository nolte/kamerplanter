from pydantic import BaseModel

from app.common.enums import ExperienceLevel


class UserPreferenceResponse(BaseModel):
    key: str
    user_key: str
    experience_level: ExperienceLevel
    onboarding_completed: bool
    locale: str
    theme: str


class UserPreferenceUpdate(BaseModel):
    experience_level: ExperienceLevel | None = None
    onboarding_completed: bool | None = None
    locale: str | None = None
    theme: str | None = None
