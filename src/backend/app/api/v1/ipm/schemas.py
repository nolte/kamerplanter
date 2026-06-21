from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import PestSeverity, PlantPart


class PestCreate(BaseModel):
    scientific_name: str = Field(min_length=1, max_length=200)
    common_name: str = Field(min_length=1, max_length=200)
    common_name_de: str | None = None
    pest_type: str = "insect"
    lifecycle_days: int | None = None
    optimal_temp_min: float | None = None
    optimal_temp_max: float | None = None
    detection_difficulty: str = "medium"
    description: str | None = None
    description_de: str | None = None
    damage_symptoms: str | None = None
    damage_symptoms_de: str | None = None
    affected_plant_parts: list[PlantPart] = Field(default_factory=list)
    host_plants: list[str] = Field(default_factory=list)
    host_plants_de: list[str] = Field(default_factory=list)
    prevention_tips: str | None = None
    prevention_tips_de: str | None = None
    monitoring_hints: str | None = None
    monitoring_hints_de: str | None = None
    severity: PestSeverity | None = None
    optimal_humidity_min: float | None = None
    optimal_humidity_max: float | None = None
    detection_slug: str | None = None
    reference_image_refs: list[str] = Field(default_factory=list)


class PestUpdate(BaseModel):
    scientific_name: str | None = None
    common_name: str | None = None
    common_name_de: str | None = None
    pest_type: str | None = None
    lifecycle_days: int | None = None
    optimal_temp_min: float | None = None
    optimal_temp_max: float | None = None
    detection_difficulty: str | None = None
    description: str | None = None
    description_de: str | None = None
    damage_symptoms: str | None = None
    damage_symptoms_de: str | None = None
    affected_plant_parts: list[PlantPart] | None = None
    host_plants: list[str] | None = None
    host_plants_de: list[str] | None = None
    prevention_tips: str | None = None
    prevention_tips_de: str | None = None
    monitoring_hints: str | None = None
    monitoring_hints_de: str | None = None
    severity: PestSeverity | None = None
    optimal_humidity_min: float | None = None
    optimal_humidity_max: float | None = None
    detection_slug: str | None = None
    reference_image_refs: list[str] | None = None


class PestResponse(BaseModel):
    key: str
    scientific_name: str
    common_name: str
    common_name_de: str | None = None
    pest_type: str
    lifecycle_days: int | None = None
    optimal_temp_min: float | None = None
    optimal_temp_max: float | None = None
    detection_difficulty: str
    description: str | None = None
    description_de: str | None = None
    damage_symptoms: str | None = None
    damage_symptoms_de: str | None = None
    affected_plant_parts: list[PlantPart] = Field(default_factory=list)
    host_plants: list[str] = Field(default_factory=list)
    host_plants_de: list[str] = Field(default_factory=list)
    prevention_tips: str | None = None
    prevention_tips_de: str | None = None
    monitoring_hints: str | None = None
    monitoring_hints_de: str | None = None
    severity: PestSeverity | None = None
    optimal_humidity_min: float | None = None
    optimal_humidity_max: float | None = None
    detection_slug: str | None = None
    reference_image_refs: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DiseaseCreate(BaseModel):
    scientific_name: str = Field(min_length=1, max_length=200)
    common_name: str = Field(min_length=1, max_length=200)
    pathogen_type: str
    incubation_period_days: int | None = None
    environmental_triggers: list[str] = Field(default_factory=list)
    affected_plant_parts: list[str] = Field(default_factory=list)
    description: str | None = None


class DiseaseUpdate(BaseModel):
    scientific_name: str | None = None
    common_name: str | None = None
    pathogen_type: str | None = None
    incubation_period_days: int | None = None
    environmental_triggers: list[str] | None = None
    affected_plant_parts: list[str] | None = None
    description: str | None = None


class DiseaseResponse(BaseModel):
    key: str
    scientific_name: str
    common_name: str
    pathogen_type: str
    incubation_period_days: int | None = None
    environmental_triggers: list[str]
    affected_plant_parts: list[str]
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TreatmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    name_de: str | None = None
    treatment_type: str
    active_ingredient: str | None = None
    application_method: str = "spray"
    safety_interval_days: int = 0
    dosage_per_liter: float | None = None
    protective_equipment: list[str] = Field(default_factory=list)
    description: str | None = None
    description_de: str | None = None
    how_to_apply: str | None = None
    how_to_apply_de: str | None = None
    mode_of_action: str | None = None
    mode_of_action_de: str | None = None
    precautions: str | None = None
    precautions_de: str | None = None


class TreatmentUpdate(BaseModel):
    name: str | None = None
    name_de: str | None = None
    treatment_type: str | None = None
    active_ingredient: str | None = None
    application_method: str | None = None
    safety_interval_days: int | None = None
    dosage_per_liter: float | None = None
    protective_equipment: list[str] | None = None
    description: str | None = None
    description_de: str | None = None
    how_to_apply: str | None = None
    how_to_apply_de: str | None = None
    mode_of_action: str | None = None
    mode_of_action_de: str | None = None
    precautions: str | None = None
    precautions_de: str | None = None


class TreatmentResponse(BaseModel):
    key: str
    name: str
    name_de: str | None = None
    treatment_type: str
    active_ingredient: str | None = None
    application_method: str
    safety_interval_days: int
    dosage_per_liter: float | None = None
    protective_equipment: list[str]
    description: str | None = None
    description_de: str | None = None
    how_to_apply: str | None = None
    how_to_apply_de: str | None = None
    mode_of_action: str | None = None
    mode_of_action_de: str | None = None
    precautions: str | None = None
    precautions_de: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InspectionCreate(BaseModel):
    inspector: str = ""
    pressure_level: str = "none"
    detected_pest_keys: list[str] = Field(default_factory=list)
    detected_disease_keys: list[str] = Field(default_factory=list)
    symptoms_observed: list[str] = Field(default_factory=list)
    environmental_conditions: dict | None = None
    photo_refs: list[str] = Field(default_factory=list)
    notes: str | None = None


class InspectionResponse(BaseModel):
    key: str
    plant_key: str
    inspector: str
    inspected_at: datetime | None = None
    pressure_level: str
    detected_pest_keys: list[str]
    detected_disease_keys: list[str]
    symptoms_observed: list[str]
    environmental_conditions: dict | None = None
    photo_refs: list[str]
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TreatmentApplicationCreate(BaseModel):
    treatment_key: str
    dosage: float | None = None
    water_volume_liters: float | None = None
    efficacy_rating: str | None = None
    applied_by: str = ""
    notes: str | None = None


class TreatmentApplicationResponse(BaseModel):
    key: str
    treatment_key: str
    plant_key: str
    applied_at: datetime | None = None
    dosage: float | None = None
    water_volume_liters: float | None = None
    efficacy_rating: str | None = None
    applied_by: str
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BeneficialResponse(BaseModel):
    key: str
    slug: str
    common_name: str
    scientific_name: str
    description: str | None = None
    preys_on: list[str] = Field(default_factory=list)


class PestDetailResponse(BaseModel):
    """Aggregierte Schädlings-Detailseite (REQ-010).

    Bündelt Stammdaten + Gegenmaßnahmen (nach IPM-Hierarchie sortiert:
    cultural → biological → mechanical → chemical) + passende Nützlinge +
    den Schadbild-Hinweis aus der Erkennungs-Taxonomie (REQ-044).
    """

    pest: PestResponse
    treatments: list[TreatmentResponse] = Field(default_factory=list)
    beneficials: list[BeneficialResponse] = Field(default_factory=list)
    detection_symptom_hint: str | None = None


class TreatmentTargetRef(BaseModel):
    """Schlanke Referenz auf einen behandelten Schädling/eine Krankheit."""

    key: str
    common_name: str
    common_name_de: str | None = None
    scientific_name: str


class TreatmentDetailResponse(BaseModel):
    """Aggregierte Behandlungs-Detailseite (REQ-010) — Stammdaten der Maßnahme
    plus die Schädlinge und Krankheiten, gegen die sie eingesetzt wird."""

    treatment: TreatmentResponse
    targeted_pests: list[TreatmentTargetRef] = Field(default_factory=list)
    targeted_diseases: list[TreatmentTargetRef] = Field(default_factory=list)


class KarenzPeriodResponse(BaseModel):
    active_ingredient: str | None = None
    treatment_name: str | None = None
    applied_at: str | None = None
    safety_interval_days: int | None = None
    safe_date: str | None = None


class HarvestSafetyResponse(BaseModel):
    can_harvest: bool
    blocking_treatments: list[dict] = Field(default_factory=list)
