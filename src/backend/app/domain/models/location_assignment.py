
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class LocationAssignment(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    membership_key: str
    location_key: str
    tenant_key: str
    can_edit: bool = True
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
