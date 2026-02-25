from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import BufferCapacity, SubstrateType, WaterRetention


class SubstrateCreate(BaseModel):
    type: SubstrateType = SubstrateType.SOIL
    brand: str | None = None
    ph_base: float = Field(default=6.5, ge=0, le=14)
    ec_base_ms: float = Field(default=0.5, ge=0)
    water_retention: WaterRetention = WaterRetention.MEDIUM
    air_porosity_percent: float = Field(default=25.0, ge=0, le=100)
    composition: dict[str, float] = Field(default_factory=dict)
    buffer_capacity: BufferCapacity = BufferCapacity.MEDIUM
    reusable: bool = False
    max_reuse_cycles: int = Field(default=3, ge=1)

class SubstrateResponse(BaseModel):
    key: str
    type: SubstrateType
    brand: str | None
    ph_base: float
    ec_base_ms: float
    water_retention: WaterRetention
    air_porosity_percent: float
    composition: dict[str, float]
    buffer_capacity: BufferCapacity
    reusable: bool
    max_reuse_cycles: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

class BatchCreate(BaseModel):
    batch_id: str
    substrate_key: str
    volume_liters: float = Field(ge=0)
    mixed_on: date

class BatchResponse(BaseModel):
    key: str
    batch_id: str
    substrate_key: str
    volume_liters: float
    mixed_on: date
    last_amended: date | None
    cycles_used: int
    ph_current: float | None
    ec_current_ms: float | None
    created_at: datetime | None = None
    updated_at: datetime | None = None

class ReusabilityResponse(BaseModel):
    can_reuse: bool
    treatments: list[str]
