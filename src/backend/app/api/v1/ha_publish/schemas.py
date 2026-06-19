from pydantic import BaseModel, Field

from app.domain.models.ha_publish_setting import HaPublishEntityType


class HaPublishSettingResponse(BaseModel):
    entity_type: HaPublishEntityType
    entity_key: str
    enabled: bool


class HaPublishSettingUpdate(BaseModel):
    enabled: bool


class HaPublishBulkEntry(BaseModel):
    entity_key: str
    enabled: bool


class HaPublishBulkUpdate(BaseModel):
    entity_type: HaPublishEntityType
    entries: list[HaPublishBulkEntry] = Field(min_length=1)


class HaPublishEnabledKeysResponse(BaseModel):
    entity_type: HaPublishEntityType
    entity_keys: list[str]
