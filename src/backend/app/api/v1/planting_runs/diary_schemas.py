from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import DiaryEntryType


class DiaryEntryCreateRequest(BaseModel):
    entry_type: DiaryEntryType
    title: str | None = Field(default=None, max_length=200)
    text: str = Field(min_length=1, max_length=5000)
    photo_refs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    measurements: dict | None = None


class DiaryEntryUpdateRequest(BaseModel):
    entry_type: DiaryEntryType | None = None
    title: str | None = Field(default=None, max_length=200)
    text: str | None = Field(default=None, min_length=1, max_length=5000)
    photo_refs: list[str] | None = None
    tags: list[str] | None = None
    measurements: dict | None = None


class DiaryEntryResponse(BaseModel):
    key: str
    plant_key: str
    entry_type: DiaryEntryType
    title: str | None
    text: str
    photo_refs: list[str]
    tags: list[str]
    measurements: dict | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class RunDiaryEntryResponse(BaseModel):
    plant_key: str
    plant_id: str
    plant_name: str | None
    diary_entry: DiaryEntryResponse
