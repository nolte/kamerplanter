from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import IrrigationSystem, LightType, Orientation


class LocationCreate(BaseModel):
    name: str
    site_key: str
    area_m2: float = Field(ge=0)
    orientation: Orientation | None = None
    light_type: LightType = LightType.NATURAL
    irrigation_system: IrrigationSystem = IrrigationSystem.MANUAL
    dimensions: tuple[float, float, float] = (0.0, 0.0, 0.0)
    lights_on: str | None = None
    lights_off: str | None = None
    use_dynamic_sunrise: bool = False

class LocationResponse(BaseModel):
    key: str
    name: str
    site_key: str
    area_m2: float
    orientation: Orientation | None
    light_type: LightType
    irrigation_system: IrrigationSystem
    dimensions: tuple[float, float, float]
    lights_on: str | None = None
    lights_off: str | None = None
    use_dynamic_sunrise: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
