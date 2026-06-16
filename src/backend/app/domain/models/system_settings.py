from datetime import datetime

from pydantic import BaseModel, Field


class HomeAssistantSettings(BaseModel):
    ha_url: str | None = None
    ha_access_token: str | None = None
    ha_timeout: int | None = None


class PlantIdentificationSettings(BaseModel):
    """Instance-wide plant identification settings (REQ-029 Phase 1).

    The Pl@ntNet API key applies to the whole instance (free-tier key,
    not tenant-scoped). An empty value means "fall back to the environment
    variable ``PLANTNET_API_KEY``" — see ``SystemSettingsService``.
    """

    plantnet_api_key: str = ""


class SystemSettings(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    home_assistant: HomeAssistantSettings = Field(default_factory=HomeAssistantSettings)
    plant_identification: PlantIdentificationSettings = Field(
        default_factory=PlantIdentificationSettings,
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
