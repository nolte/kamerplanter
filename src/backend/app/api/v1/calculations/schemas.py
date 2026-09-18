"""Request/response schemas for /calculations (REQ-003, REQ-018).

``VPDRequest.phase`` carries ``PhaseName``, not ``str`` (#1520, review SCR-004).
The classifier looks the phase up with ``vpd_ranges.get(phase, (0.8, 1.2))``, so
a misspelt phase never raised — it silently classified the reading against the
vegetative default and quoted the misspelling back in the recommendation. That is
the quiet half of the same class: a wrong answer instead of an error.
"""

from datetime import date

from pydantic import BaseModel, Field

from app.common.enums import PhaseName


class VPDRequest(BaseModel):
    temp_c: float
    humidity_percent: float = Field(ge=0, le=100)
    phase: PhaseName = PhaseName.VEGETATIVE


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
    lights_on_time: str = "06:00"


class SunTimesRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    date: date
    timezone: str = "UTC"


class SunTimesResponse(BaseModel):
    date: str
    sunrise: str
    sunset: str
    dawn: str
    dusk: str
    day_length_hours: float


class SunTimesRangeRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    start_date: date
    end_date: date
    timezone: str = "UTC"


class SlotCapacityRequest(BaseModel):
    area_m2: float = Field(gt=0)
    plant_spacing_cm: float = Field(gt=0)


class SlotCapacityResponse(BaseModel):
    max_capacity: int
    optimal_range: tuple[int, int]
    plants_per_m2: float


class VernalizationRequest(BaseModel):
    cold_days_accumulated: int = Field(ge=0)
    required_min_days: int = Field(ge=0)


class VernalizationResponse(BaseModel):
    progress_percent: float
    days_remaining: int
    is_complete: bool


class PhotoperiodTransitionStep(BaseModel):
    """One day of the gradual photoperiod-transition schedule."""

    day: int
    photoperiod_hours: float
    lights_on: str
    lights_off: str
    dli: float


class PhotoperiodTransitionResponse(BaseModel):
    """Day-by-day photoperiod-transition schedule with the resulting DLI."""

    schedule: list[PhotoperiodTransitionStep]
