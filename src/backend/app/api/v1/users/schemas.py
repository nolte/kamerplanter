from pydantic import BaseModel, Field


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    avatar_url: str | None = None
    locale: str | None = None
    timezone: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str | None = None  # None allowed for SSO-only users setting initial password
    new_password: str = Field(min_length=10, max_length=128)
