from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HomeAssistantSettings(BaseModel):
    ha_url: str | None = None
    ha_access_token: str | None = None
    ha_timeout: int | None = None


class SystemSettings(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    home_assistant: HomeAssistantSettings = Field(default_factory=HomeAssistantSettings)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
