from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import BufferCapacity, IrrigationStrategy, SubstrateType, WaterRetention


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
    water_holding_capacity_percent: float | None = Field(default=None, ge=0, le=100)
    easily_available_water_percent: float | None = Field(default=None, ge=0, le=100)
    cec_meq_per_100g: float | None = Field(default=None, ge=0)
    particle_size_mm: float | None = Field(default=None, ge=0)
    bulk_density_g_per_l: float | None = Field(default=None, ge=0)
    irrigation_strategy: IrrigationStrategy | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_composition(self) -> "Substrate":
        if self.type == SubstrateType.NONE:
            if self.composition:
                msg = "Composition must be empty for substrate type 'none'."
                raise ValueError(msg)
            return self
        if self.composition:
            total = sum(self.composition.values())
            if abs(total - 1.0) > 0.01:
                msg = f"Composition fractions must sum to 1.0 (±0.01), got {total:.4f}."
                raise ValueError(msg)
        return self


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
    temperature_c: float | None = None
    ph_history: list[float] = Field(default_factory=list)
    ec_history: list[float] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
