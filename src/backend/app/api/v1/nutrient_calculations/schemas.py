from pydantic import BaseModel, Field


class MixingProtocolRequest(BaseModel):
    target_volume_liters: float = Field(gt=0)
    target_ec_ms: float = Field(gt=0, le=10)
    target_ph: float = Field(ge=0, le=14)
    base_water_ec: float = Field(ge=0)
    base_water_ph: float = Field(ge=0, le=14)
    fertilizer_keys: list[str] = Field(min_length=1)
    substrate_type: str = "coco"


class FlushingRequest(BaseModel):
    current_ec_ms: float = Field(ge=0)
    days_until_harvest: int = Field(gt=0)
    substrate_type: str = "coco"


class RunoffRequest(BaseModel):
    input_ec_ms: float = Field(ge=0)
    runoff_ec_ms: float = Field(ge=0)
    input_ph: float = Field(ge=0, le=14)
    runoff_ph: float = Field(ge=0, le=14)
    input_volume_liters: float = Field(gt=0)
    runoff_volume_liters: float = Field(ge=0)


class MixingSafetyRequest(BaseModel):
    fertilizer_keys: list[str] = Field(min_length=1)
