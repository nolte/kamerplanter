
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.common.enums import SiteType

if TYPE_CHECKING:
    from datetime import date, datetime

# ── Water config schemas ──────────────────────────────────────────────


class TapWaterProfileSchema(BaseModel):
    ec_ms: float = Field(ge=0, le=2.0)
    ph: float = Field(ge=3.0, le=10.0)
    alkalinity_ppm: float = Field(default=0, ge=0, le=500)
    gh_ppm: float = Field(default=0, ge=0, le=1000)
    calcium_ppm: float = Field(default=0, ge=0, le=500)
    magnesium_ppm: float = Field(default=0, ge=0, le=200)
    chlorine_ppm: float = Field(default=0, ge=0, le=5)
    chloramine_ppm: float = Field(default=0, ge=0, le=5)
    measurement_date: date | None = None
    source_note: str | None = None


class RoWaterProfileSchema(BaseModel):
    ec_ms: float = Field(default=0.02, ge=0, le=0.5)
    ph: float = Field(default=6.5, ge=3.0, le=10.0)


class SiteWaterConfigSchema(BaseModel):
    has_ro_system: bool = False
    tap_water_profile: TapWaterProfileSchema | None = None
    ro_water_profile: RoWaterProfileSchema | None = None


class WaterSourceWarningSchema(BaseModel):
    code: str
    message: str
    severity: str


# ── Site schemas ──────────────────────────────────────────────────────


class SiteCreate(BaseModel):
    name: str
    type: SiteType = SiteType.INDOOR
    gps_coordinates: tuple[float, float] | None = None
    climate_zone: str = ""
    total_area_m2: float = Field(default=0.0, ge=0)
    timezone: str = "UTC"
    water_config: SiteWaterConfigSchema | None = None
    last_frost_date_avg: date | None = None
    first_frost_date_avg: date | None = None
    eisheilige_date: date | None = None


class SiteResponse(BaseModel):
    key: str
    name: str
    type: SiteType
    gps_coordinates: tuple[float, float] | None
    climate_zone: str
    total_area_m2: float
    timezone: str = "UTC"
    water_config: SiteWaterConfigSchema | None = None
    water_config_warnings: list[WaterSourceWarningSchema] = []
    last_frost_date_avg: date | None = None
    first_frost_date_avg: date | None = None
    eisheilige_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
