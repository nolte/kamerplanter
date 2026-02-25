from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import BufferCapacity, SubstrateType, WaterRetention


class Substrate(BaseModel):
    key: str | None = Field(default=None, alias="_key")
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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class SubstrateBatch(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    batch_id: str
    substrate_key: str = ""
    volume_liters: float = Field(ge=0)
    mixed_on: date
    last_amended: date | None = None
    cycles_used: int = Field(default=0, ge=0)
    ph_current: float | None = Field(default=None, ge=0, le=14)
    ec_current_ms: float | None = Field(default=None, ge=0)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
