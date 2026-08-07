from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import (
    DataOrigin,
    EfficacyRating,
    PathogenType,
    PestPressureLevel,
    PestSeverity,
    PlantPart,
    TreatmentApplicationMethod,
    TreatmentType,
)


class Pest(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    scientific_name: str = Field(min_length=1, max_length=200)
    common_name: str = Field(min_length=1, max_length=200)
    common_name_de: str | None = Field(default=None, max_length=200)
    pest_type: str = Field(default="insect", max_length=50)
    lifecycle_days: int | None = Field(default=None, ge=1)
    optimal_temp_min: float | None = Field(default=None, ge=-10, le=60)
    optimal_temp_max: float | None = Field(default=None, ge=-10, le=60)
    detection_difficulty: str = Field(default="medium", max_length=50)
    description: str | None = None
    description_de: str | None = None
    # ── Detailseiten-Felder (REQ-010, additiv & abwärtskompatibel) ──
    # Mehrsprachig: Basisfeld = EN (Fallback), *_de = deutsche Variante
    # (Anzeige über useLocalizedField, Muster wie Treatment).
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
    optimal_humidity_min: float | None = Field(default=None, ge=0, le=100)
    optimal_humidity_max: float | None = Field(default=None, ge=0, le=100)
    # Brücke zur Erkennungs-Taxonomie (PestTaxon.slug, REQ-044) — verknüpft den
    # Stammdatensatz mit der Bilderkennungs-Klasse (Symptom-Hint, Nützlings-Lookup).
    detection_slug: str | None = Field(default=None, max_length=80)
    # Kuratierte Referenzbilder (Object-Storage-Refs; Admin-gepflegt, NFR-013).
    reference_image_refs: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class Disease(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    scientific_name: str = Field(min_length=1, max_length=200)
    common_name: str = Field(min_length=1, max_length=200)
    pathogen_type: PathogenType
    incubation_period_days: int | None = Field(default=None, ge=1)
    environmental_triggers: list[str] = Field(default_factory=list)
    affected_plant_parts: list[PlantPart] = Field(default_factory=list)
    description: str | None = None
    # Data provenance (REQ-001/REQ-010, UI-NFR-018): seeded IPM data is 'system'
    # (read-only), user-created records are 'tenant'. Server-managed.
    origin: DataOrigin = Field(default=DataOrigin.SYSTEM)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class Treatment(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str = Field(min_length=1, max_length=200)
    # name (englisch) ist der stabile Schlüssel für Seed-Edges; name_de ist die
    # deutsche Anzeige-Variante (Muster wie task/substrate, useLocalizedField).
    name_de: str | None = Field(default=None, max_length=200)
    treatment_type: TreatmentType
    active_ingredient: str | None = None
    application_method: TreatmentApplicationMethod = TreatmentApplicationMethod.SPRAY
    safety_interval_days: int = Field(default=0, ge=0)
    dosage_per_liter: float | None = Field(default=None, gt=0)
    protective_equipment: list[str] = Field(default_factory=list)
    description: str | None = None
    description_de: str | None = None
    # ── Detailseiten-Felder (REQ-010, mehrsprachig: Basis = EN, _de = DE) ──
    how_to_apply: str | None = None
    how_to_apply_de: str | None = None
    mode_of_action: str | None = None
    mode_of_action_de: str | None = None
    precautions: str | None = None
    precautions_de: str | None = None
    # Data provenance (REQ-001/REQ-010, UI-NFR-018): seeded IPM data is 'system'
    # (read-only), user-created records are 'tenant'. Server-managed.
    origin: DataOrigin = Field(default=DataOrigin.SYSTEM)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def check_chemical_safety_interval(self) -> Treatment:
        if self.treatment_type == TreatmentType.CHEMICAL and self.safety_interval_days <= 0:
            raise ValueError("Chemical treatments must have a safety_interval_days > 0")
        return self


class InspectionFinding(BaseModel):
    """One structured observation inside an inspection (REQ-033 §2.2).

    ``symptoms_observed`` is a list of bare strings and always was. That is enough
    for a human filling in a form, but it drops the two things an image-analysis
    agent actually produces alongside a symptom: **how sure it is** and **which
    part of the plant** it saw. Folding those into the string ("webbing on leaves
    (0.82)") would push the structure into prose that the next reader has to parse
    back out — the lossy remapping REQ-033's ``create_inspection`` explicitly must
    not require.

    ``confidence`` is bounded to 0.0–1.0 to match ``DiaryFinding`` (REQ-050 §5),
    so a finding keeps the same meaning whether it arrives through
    ``submit_diary_analysis`` or through ``create_inspection``.

    ``pest_key`` / ``disease_key`` are optional: an agent frequently sees a
    symptom it cannot yet attribute, and forcing an attribution would turn a
    hedged observation into a false certainty.
    """

    symptom: str = Field(min_length=1, max_length=500)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    affected_plant_part: PlantPart | None = None
    pest_key: str | None = None
    disease_key: str | None = None
    rationale: str | None = Field(default=None, max_length=2000)


class Inspection(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    plant_key: str = ""
    inspector: str = Field(default="", max_length=200)
    inspected_at: datetime | None = None
    pressure_level: PestPressureLevel = PestPressureLevel.NONE
    detected_pest_keys: list[str] = Field(default_factory=list)
    detected_disease_keys: list[str] = Field(default_factory=list)
    symptoms_observed: list[str] = Field(default_factory=list)
    # Additive and defaulted, so every inspection written before this field
    # existed still validates and round-trips unchanged. ``symptoms_observed``
    # stays the canonical flat list — a writer that fills ``findings`` mirrors the
    # symptom strings into it, so no existing reader loses anything.
    findings: list[InspectionFinding] = Field(default_factory=list)
    environmental_conditions: dict | None = None
    photo_refs: list[str] = Field(default_factory=list)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TreatmentApplication(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    treatment_key: str = ""
    plant_key: str = ""
    applied_at: datetime | None = None
    dosage: float | None = Field(default=None, gt=0)
    water_volume_liters: float | None = Field(default=None, gt=0)
    efficacy_rating: EfficacyRating | None = None
    applied_by: str = Field(default="", max_length=200)
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
