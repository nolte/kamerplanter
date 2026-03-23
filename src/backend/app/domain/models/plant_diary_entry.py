from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import DiaryEntryType


class PlantDiaryEntry(BaseModel):
    """A diary entry for a plant instance, tracking observations, problems, and milestones."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    plant_key: str = ""
    entry_type: DiaryEntryType
    title: str | None = Field(default=None, max_length=200)
    text: str = Field(min_length=1, max_length=5000)
    photo_refs: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    measurements: dict | None = None
    created_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
