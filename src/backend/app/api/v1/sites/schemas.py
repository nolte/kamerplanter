from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import SiteType


class SiteCreate(BaseModel):
    name: str
    type: SiteType = SiteType.INDOOR
    gps_coordinates: tuple[float, float] | None = None
    climate_zone: str = ""
    total_area_m2: float = Field(default=0.0, ge=0)

class SiteResponse(BaseModel):
    key: str
    name: str
    type: SiteType
    gps_coordinates: tuple[float, float] | None
    climate_zone: str
    total_area_m2: float
    created_at: datetime | None = None
    updated_at: datetime | None = None
