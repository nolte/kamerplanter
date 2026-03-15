from pydantic import BaseModel, Field


class HASettingsUpdate(BaseModel):
    ha_url: str | None = None
    ha_access_token: str | None = None
    ha_timeout: int | None = Field(default=None, ge=1, le=120)


class HASettingsResponse(BaseModel):
    ha_url: str
    ha_access_token_masked: str
    ha_timeout: int
    source_ha_url: str
    source_ha_access_token: str
    source_ha_timeout: str


class SystemSettingsResponse(BaseModel):
    home_assistant: HASettingsResponse


class HATestRequest(BaseModel):
    ha_url: str | None = None
    ha_access_token: str | None = None
    ha_timeout: int | None = Field(default=None, ge=1, le=120)


class HATestResponse(BaseModel):
    success: bool
    message: str
    ha_version: str | None = None
