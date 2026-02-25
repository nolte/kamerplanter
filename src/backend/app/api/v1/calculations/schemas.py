from pydantic import BaseModel, Field


class VPDRequest(BaseModel):
    temp_c: float
    humidity_percent: float = Field(ge=0, le=100)
    phase: str = "vegetative"

class VPDResponse(BaseModel):
    vpd_kpa: float
    status: str
    recommendation: str

class GDDRequest(BaseModel):
    daily_temps: list[tuple[float, float]]
    base_temp_c: float = 10.0

class GDDResponse(BaseModel):
    accumulated_gdd: float
    days_counted: int

class PhotoperiodTransitionRequest(BaseModel):
    current_hours: float = Field(ge=0, le=24)
    target_hours: float = Field(ge=0, le=24)
    transition_days: int = Field(default=7, ge=1)
    ppfd: int = Field(default=400, ge=0)

class SlotCapacityRequest(BaseModel):
    area_m2: float = Field(gt=0)
    plant_spacing_cm: float = Field(gt=0)

class SlotCapacityResponse(BaseModel):
    max_capacity: int
    optimal_range: tuple[int, int]
    plants_per_m2: float
