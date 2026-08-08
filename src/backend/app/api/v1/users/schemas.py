from pydantic import BaseModel, Field

from app.common.validators import DisplayName


class ProfileUpdateRequest(BaseModel):
    display_name: DisplayName | None = None
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str | None = None  # None allowed for SSO-only users setting initial password
    new_password: str = Field(min_length=10, max_length=128)
