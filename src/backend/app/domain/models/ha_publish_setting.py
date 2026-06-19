"""Home Assistant publish selection.

A tenant decides which entities are exported to Home Assistant as sensors.
Selection is stored centrally (one document per tenant + entity), not as a
flag on each domain model, so the export surface stays decoupled from the
plant/tank/location schemas.

Policy is **opt-in**: an entity is published only when a setting exists with
``enabled=True``. The absence of a setting means "not published".
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class HaPublishEntityType(StrEnum):
    """Entity kinds that can be published to Home Assistant."""

    PLANT = "plant"
    TANK = "tank"
    LOCATION = "location"


class HaPublishSetting(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    entity_type: HaPublishEntityType
    entity_key: str
    enabled: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
