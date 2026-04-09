from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import CycleType, PhotoperiodType, StressTolerance


class PhaseDefinition(BaseModel):
    key: str | None = Field(default=None, alias="_key")
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
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class PhaseSequence(BaseModel):
    key: str | None = Field(default=None, alias="_key")
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
    vernalization_min_days: int | None = Field(default=None, ge=1)
    photoperiod_type: PhotoperiodType = PhotoperiodType.DAY_NEUTRAL
    critical_day_length_hours: float | None = Field(default=None, ge=0, le=24)
    is_system: bool = False
    tags: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class PhaseSequenceEntry(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    phase_sequence_key: str = ""
    phase_definition_key: str = ""
    sequence_order: int = Field(default=0, ge=0)
    override_duration_days: int | None = Field(default=None, ge=1)
    is_terminal: bool = False
    allows_harvest: bool = False
    is_recurring: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
