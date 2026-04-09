from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import CycleType, PhotoperiodType, StressTolerance

# ── PhaseDefinition schemas ──


class PhaseDefinitionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    display_name: str = ""
    display_name_de: str = ""
    description: str = ""
    description_de: str = ""
    typical_duration_days: int = Field(ge=1, default=1)
    stress_tolerance: StressTolerance = StressTolerance.MEDIUM
    watering_interval_days: int | None = Field(default=None, ge=1, le=90)
    illustration: str = ""
    tags: list[str] = Field(default_factory=list)
    is_system: bool = False


class PhaseDefinitionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    display_name: str | None = None
    display_name_de: str | None = None
    description: str | None = None
    description_de: str | None = None
    typical_duration_days: int | None = Field(default=None, ge=1)
    stress_tolerance: StressTolerance | None = None
    watering_interval_days: int | None = Field(default=None, ge=1, le=90)
    illustration: str | None = None
    tags: list[str] | None = None


class PhaseDefinitionResponse(BaseModel):
    key: str
    name: str
    display_name: str = ""
    display_name_de: str = ""
    description: str = ""
    description_de: str = ""
    typical_duration_days: int = 1
    stress_tolerance: StressTolerance = StressTolerance.MEDIUM
    watering_interval_days: int | None = None
    illustration: str = ""
    tags: list[str] = Field(default_factory=list)
    is_system: bool = False
    usage_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── PhaseSequence schemas ──


class PhaseSequenceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    display_name: str = ""
    display_name_de: str = ""
    description: str = ""
    description_de: str = ""
    species_key: str = ""
    cycle_type: CycleType = CycleType.ANNUAL
    is_repeating: bool = False
    cycle_restart_entry_order: int | None = None
    typical_lifespan_years: int | None = None
    dormancy_required: bool = False
    vernalization_required: bool = False
    vernalization_min_days: int | None = None
    photoperiod_type: PhotoperiodType = PhotoperiodType.DAY_NEUTRAL
    critical_day_length_hours: float | None = None
    is_system: bool = False
    tags: list[str] = Field(default_factory=list)


class PhaseSequenceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    display_name: str | None = None
    display_name_de: str | None = None
    description: str | None = None
    description_de: str | None = None
    species_key: str | None = None
    cycle_type: CycleType | None = None
    is_repeating: bool | None = None
    cycle_restart_entry_order: int | None = None
    typical_lifespan_years: int | None = None
    dormancy_required: bool | None = None
    vernalization_required: bool | None = None
    vernalization_min_days: int | None = None
    photoperiod_type: PhotoperiodType | None = None
    critical_day_length_hours: float | None = None
    tags: list[str] | None = None


class PhaseSequenceEntryResponse(BaseModel):
    key: str
    phase_sequence_key: str = ""
    phase_definition_key: str = ""
    sequence_order: int = 0
    override_duration_days: int | None = None
    effective_duration_days: int = 1
    is_terminal: bool = False
    allows_harvest: bool = False
    is_recurring: bool = False
    phase_definition: PhaseDefinitionResponse | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PhaseSequenceResponse(BaseModel):
    key: str
    name: str
    display_name: str = ""
    display_name_de: str = ""
    description: str = ""
    description_de: str = ""
    species_key: str = ""
    cycle_type: CycleType = CycleType.ANNUAL
    is_repeating: bool = False
    cycle_restart_entry_order: int | None = None
    typical_lifespan_years: int | None = None
    dormancy_required: bool = False
    vernalization_required: bool = False
    vernalization_min_days: int | None = None
    photoperiod_type: PhotoperiodType = PhotoperiodType.DAY_NEUTRAL
    critical_day_length_hours: float | None = None
    is_system: bool = False
    tags: list[str] = Field(default_factory=list)
    entries: list[PhaseSequenceEntryResponse] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


# ── PhaseSequenceEntry schemas ──


class PhaseSequenceEntryCreate(BaseModel):
    phase_definition_key: str = Field(min_length=1)
    sequence_order: int = Field(default=0, ge=0)
    override_duration_days: int | None = Field(default=None, ge=1)
    is_terminal: bool = False
    allows_harvest: bool = False
    is_recurring: bool = False


class PhaseSequenceEntryUpdate(BaseModel):
    phase_definition_key: str | None = None
    sequence_order: int | None = Field(default=None, ge=0)
    override_duration_days: int | None = Field(default=None, ge=1)
    is_terminal: bool | None = None
    allows_harvest: bool | None = None
    is_recurring: bool | None = None


# ── Reorder schemas ──


class EntryReorderItem(BaseModel):
    key: str
    sequence_order: int = Field(ge=0)


class EntryReorderRequest(BaseModel):
    entries: list[EntryReorderItem] = Field(min_length=1)
