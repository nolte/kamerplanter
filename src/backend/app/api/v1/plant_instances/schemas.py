from datetime import date, datetime

from pydantic import BaseModel, Field

from app.common.enums import SubstrateType, TerminationCause, TerminationType


class PlantCreate(BaseModel):
    instance_id: str
    species_key: str
    cultivar_key: str | None = None
    site_key: str | None = None
    location_key: str | None = None
    slot_key: str | None = None
    substrate_batch_key: str | None = None
    substrate_key: str | None = None
    plant_name: str | None = None
    planted_on: date
    current_phase_key: str | None = None
    container_volume_liters: float | None = Field(default=None, ge=0.1, le=500)
    substrate_type_override: SubstrateType | None = None


class RemovePlantRequest(BaseModel):
    """Optional body for POST /{key}/remove (REQ-003 E5).

    Backward compatible: an empty body keeps the previous plain-removal behaviour.
    ``termination_cause`` is only valid together with ``termination_type='died'``.
    """

    termination_type: TerminationType | None = None
    termination_cause: TerminationCause | None = None


class SpeciesSummary(BaseModel):
    """Denormalized species fields for human-readable plant labels."""

    scientific_name: str
    common_names: list[str] = Field(default_factory=list)


class CultivarSummary(BaseModel):
    """Denormalized cultivar fields for human-readable plant labels."""

    name: str


class PlantResponse(BaseModel):
    key: str
    instance_id: str
    species_key: str
    cultivar_key: str | None
    site_key: str | None = None
    location_key: str | None = None
    slot_key: str | None
    substrate_batch_key: str | None
    substrate_key: str | None = None
    plant_name: str | None
    planted_on: date
    removed_on: date | None
    termination_type: TerminationType | None = None
    termination_cause: TerminationCause | None = None
    current_phase: str = ""
    current_phase_key: str | None = None
    current_phase_started_at: datetime | None = None
    container_volume_liters: float | None = None
    substrate_type_override: SubstrateType | None = None
    species: SpeciesSummary | None = None
    cultivar: CultivarSummary | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TerminationTypeCountResponse(BaseModel):
    termination_type: TerminationType
    count: int


class TerminationCauseCountResponse(BaseModel):
    termination_cause: TerminationCause
    count: int


class PhaseLossCountResponse(BaseModel):
    phase_name: str
    count: int


class SurvivalStatsResponse(BaseModel):
    """Survival-rate / failure-cause analytics for the tenant (REQ-003 G1)."""

    total: int
    terminated: int
    active: int
    died: int
    survived: int
    survival_rate: float
    by_termination_type: list[TerminationTypeCountResponse] = Field(default_factory=list)
    by_termination_cause: list[TerminationCauseCountResponse] = Field(default_factory=list)
    loss_by_phase: list[PhaseLossCountResponse] = Field(default_factory=list)


class ValidatePlantingRequest(BaseModel):
    species_key: str


class ValidatePlantingResponse(BaseModel):
    valid: bool
    warnings: list[str]
    benefits: list[str]


class ActiveChannelDosage(BaseModel):
    fertilizer_key: str
    product_name: str
    ml_per_liter: float
    optional: bool = False
    mixing_priority: int = 50


class ActiveChannelResponse(BaseModel):
    channel_id: str
    label: str
    application_method: str
    target_ec_ms: float | None = None
    target_ph: float | None = None
    plan_key: str
    plan_name: str
    entry_key: str | None = None
    phase_name: str
    week_start: int
    week_end: int
    dosages: list[ActiveChannelDosage] = Field(default_factory=list)


class AssignNutrientPlanRequest(BaseModel):
    plan_key: str
    assigned_by: str = ""
