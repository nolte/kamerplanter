from datetime import datetime

from pydantic import BaseModel, Field


class LocationType(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    name_en: str | None = None
    icon: str | None = None
    is_indoor: bool = False
    is_system: bool = False
    sort_order: int = 0
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
