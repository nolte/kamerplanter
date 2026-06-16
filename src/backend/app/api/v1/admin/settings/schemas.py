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


class PlantIdentificationSettingsResponse(BaseModel):
    """Masked Pl@ntNet key plus its source (``db``/``env``/``none``)."""

    plantnet_api_key_masked: str
    source_plantnet_api_key: str


class SystemSettingsResponse(BaseModel):
    home_assistant: HASettingsResponse
    plant_identification: PlantIdentificationSettingsResponse


class HATestRequest(BaseModel):
    ha_url: str | None = None
    ha_access_token: str | None = None
    ha_timeout: int | None = Field(default=None, ge=1, le=120)


class HATestResponse(BaseModel):
    success: bool
    message: str
    ha_version: str | None = None


class PlantIdentificationSettingsUpdate(BaseModel):
    plantnet_api_key: str | None = None


class PlantIdentificationTestRequest(BaseModel):
    plantnet_api_key: str | None = None


class PlantIdentificationTestResponse(BaseModel):
    success: bool
    message: str
