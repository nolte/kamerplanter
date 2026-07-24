from datetime import date

from pydantic import BaseModel, Field


class MixingProtocolRequest(BaseModel):
    target_volume_liters: float = Field(gt=0)
    target_ec_ms: float = Field(gt=0, le=10)
    target_ph: float = Field(ge=0, le=14)
    # Aligned with EcBudgetRequest (le=2.0 for blended base water).
    base_water_ec: float = Field(ge=0, le=5)
    base_water_ph: float = Field(ge=0, le=14)
    fertilizer_keys: list[str] = Field(min_length=1)
    substrate_type: str = "coco"
    # ── Additive REQ-004-A fields (default to previous behaviour) ──
    alkalinity_ppm: float = Field(default=0, ge=0, le=500)
    phase: str = "vegetative"
    recipe_ml_per_liter: dict[str, float] | None = None


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


# ── Mixing-protocol response (legacy-compatible adapter over EC budget) ──


class MixingProtocolDosage(BaseModel):
    fertilizer_key: str | None = None
    product_name: str
    ml_per_liter: float
    total_ml: float
    ec_contribution: float


class PhAdjustmentResponse(BaseModel):
    needed: bool
    direction: str
    delta: float


class MixingProtocolResponse(BaseModel):
    dosages: list[MixingProtocolDosage] = []
    calculated_ec: float
    ph_adjustment: PhAdjustmentResponse
    warnings: list[str] = []
    instructions: list[str] = []
    # Additive REQ-004-A transparency fields
    ec_net: float
    ec_ph_reserve: float
    valid: bool


# ── Area-based dosing schemas (REQ-004 W-013, AP-11) ─────────────────


class AreaDosingRequest(BaseModel):
    fertilizer_keys: list[str] = Field(min_length=1)
    area_m2: float | None = Field(default=None, gt=0)
    location_key: str | None = None
    demand_level: str | None = None


class AreaDosingItemResponse(BaseModel):
    fertilizer_key: str | None = None
    product_name: str
    rate_g_per_m2: float | None = None
    rate_l_per_m2: float | None = None
    total_grams: float | None = None
    total_liters: float | None = None
    dilution_ratio: str | None = None
    nutrient_release_speed: str | None = None
    note: str | None = None


class AreaDosingResponse(BaseModel):
    area_m2: float
    items: list[AreaDosingItemResponse] = []
    warnings: list[str] = []
    instructions: list[str] = []


# ── Flushing / runoff / mixing-safety response schemas ────────────────


class FlushScheduleStep(BaseModel):
    """One day of a pre-harvest flushing schedule."""

    day: int = Field(description="Day index within the flush window (1-based).")
    absolute_day: int = Field(description="Day index counted from the plan start.")
    target_ec_ms: float = Field(description="Target solution EC for the day, in mS/cm.")
    action: str = Field(description="Human-readable flushing action for the day.")
    dosage_percent: int = Field(description="Nutrient strength for the day, in percent of full dose.")


class FlushingResponse(BaseModel):
    """Recommended pre-harvest flushing protocol."""

    substrate_type: str = Field(description="Substrate the protocol was computed for.")
    recommended_flush_days: int = Field(description="Recommended flush duration, in days.")
    flush_start_day: int = Field(description="Day (relative to now) on which flushing should start.")
    current_ec_ms: float = Field(description="Current solution EC used as the starting point, in mS/cm.")
    schedule: list[FlushScheduleStep] = Field(description="Per-day flushing schedule.")


class RunoffAnalysisResponse(BaseModel):
    """Drain-to-waste runoff analysis result."""

    ec_delta: float = Field(description="Runoff EC minus input EC, in mS/cm.")
    ec_status: str = Field(description="EC classification (OK, WARNING, SALT_BUILDUP, UNDERFED).")
    ec_message: str = Field(description="Human-readable EC assessment.")
    ph_delta: float = Field(description="Runoff pH minus input pH.")
    ph_status: str = Field(description="pH classification (OK, DRIFT).")
    ph_message: str = Field(description="Human-readable pH assessment.")
    runoff_percent: float = Field(description="Runoff volume as a percentage of the input volume.")
    volume_status: str = Field(description="Runoff-volume classification (OK, LOW, HIGH).")
    volume_message: str = Field(description="Human-readable runoff-volume assessment.")
    overall_health: str = Field(description="Overall runoff health rating (GOOD, FAIR, POOR).")


class MixingSafetyResponse(BaseModel):
    """Fertilizer mixing-safety validation result."""

    safe: bool = Field(description="Whether the combination is free of mixing-safety warnings.")
    warnings: list[str] = Field(description="Mixing-safety warnings for the combination (empty when safe).")
