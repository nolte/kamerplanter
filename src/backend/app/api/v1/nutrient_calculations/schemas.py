from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class MixingProtocolRequest(BaseModel):
    target_volume_liters: float = Field(gt=0)
    target_ec_ms: float = Field(gt=0, le=10)
    target_ph: float = Field(ge=0, le=14)
    base_water_ec: float = Field(ge=0, le=1.5)
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


# ── Water mix schemas ─────────────────────────────────────────────────


class WaterMixTapProfileRequest(BaseModel):
    ec_ms: float = Field(ge=0, le=2.0)
    ph: float = Field(ge=3.0, le=10.0)
    alkalinity_ppm: float = Field(default=0, ge=0, le=500)
    gh_ppm: float = Field(default=0, ge=0, le=1000)
    calcium_ppm: float = Field(default=0, ge=0, le=500)
    magnesium_ppm: float = Field(default=0, ge=0, le=200)
    chlorine_ppm: float = Field(default=0, ge=0, le=5)
    chloramine_ppm: float = Field(default=0, ge=0, le=5)
    measurement_date: date | None = None


class WaterMixRoProfileRequest(BaseModel):
    ec_ms: float = Field(default=0.02, ge=0, le=0.5)
    ph: float = Field(default=6.5, ge=3.0, le=10.0)


class WaterMixRequest(BaseModel):
    tap_profile: WaterMixTapProfileRequest
    ro_profile: WaterMixRoProfileRequest = WaterMixRoProfileRequest()
    ro_percent: int = Field(ge=0, le=100)
    target_ca_ppm: float = Field(default=0, ge=0, le=500)
    target_mg_ppm: float = Field(default=0, ge=0, le=200)


class EffectiveWaterProfileResponse(BaseModel):
    ec_ms: float
    ph: float
    alkalinity_ppm: float
    calcium_ppm: float
    magnesium_ppm: float
    chlorine_ppm: float
    chloramine_ppm: float


class CalMagCorrectionResponse(BaseModel):
    calcium_deficit_ppm: float
    magnesium_deficit_ppm: float
    ca_mg_ratio: float | None = None
    ca_mg_ratio_warning: str | None = None
    needs_correction: bool


class WaterSourceWarningResponse(BaseModel):
    code: str
    message: str
    severity: str


class WaterMixResponse(BaseModel):
    effective_profile: EffectiveWaterProfileResponse
    calmag_correction: CalMagCorrectionResponse | None = None
    warnings: list[WaterSourceWarningResponse] = []


# ── Reverse water mix schemas ────────────────────────────────────────


class WaterMixReverseRequest(BaseModel):
    tap_profile: WaterMixTapProfileRequest
    ro_profile: WaterMixRoProfileRequest = WaterMixRoProfileRequest()
    target_base_ec_ms: float = Field(gt=0, le=2.0)


class WaterMixReverseResponse(BaseModel):
    ro_percent: int
    effective_profile: EffectiveWaterProfileResponse


# ── EC Budget schemas ────────────────────────────────────────────────


class EcBudgetFertilizerRequest(BaseModel):
    key: str
    recipe_ml_per_liter: float | None = Field(default=None, ge=0)


class EcBudgetRequest(BaseModel):
    base_water_ec: float = Field(ge=0, le=2.0)
    alkalinity_ppm: float = Field(default=0, ge=0, le=500)
    target_ec: float = Field(gt=0, le=10)
    substrate: str = "coco"
    phase: str = "vegetative"
    volume_liters: float = Field(gt=0)
    fertilizer_keys: list[EcBudgetFertilizerRequest] = Field(default_factory=list)
    calmag_key: str | None = None
    calmag_dose_ml_per_liter: float | None = Field(default=None, ge=0)
    silicate_key: str | None = None
    silicate_dose_ml_per_liter: float | None = Field(default=None, ge=0)
    substrate_cycles_used: int | None = Field(default=None, ge=0)
    measured_ec: float | None = Field(default=None, ge=0)
    measured_temp_celsius: float | None = None


class EcSegmentResponse(BaseModel):
    label: str
    ec_contribution: float
    color_hint: str
    ml_per_liter: float = 0
    total_ml: float = 0
    warning: str | None = None


class EcBudgetResponse(BaseModel):
    ec_mix: float
    ec_net: float
    ec_silicate: float = 0
    ec_calmag: float = 0
    ec_fertilizers: float = 0
    ec_ph_reserve: float = 0
    ec_final: float = 0
    ec_max: float
    ec_target: float
    ec_at_25_corrected: float | None = None
    tolerance: float
    valid: bool
    living_soil_bypass: bool = False
    segments: list[EcSegmentResponse] = []
    warnings: list[str] = []
    dosage_table: list[dict] = []
    dosage_instructions: list[str] = []
