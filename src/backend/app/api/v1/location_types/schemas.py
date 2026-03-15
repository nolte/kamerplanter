
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class LocationTypeCreate(BaseModel):
    name: str
    name_en: str | None = None
    icon: str | None = None
    is_indoor: bool = False
    sort_order: int = 0
    description: str | None = None


class LocationTypeUpdate(BaseModel):
    name: str
    name_en: str | None = None
    icon: str | None = None
    is_indoor: bool = False
    sort_order: int = 0
    description: str | None = None


class LocationTypeResponse(BaseModel):
    key: str
    name: str
    name_en: str | None = None
    icon: str | None = None
    is_indoor: bool = False
    is_system: bool = False
    sort_order: int = 0
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
