from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from app.common.enums import CycleType, FloweringStrategy, GrowthDeterminacy, PhotoperiodType


class LifecycleCreate(BaseModel):
    species_key: str
    cycle_type: CycleType = CycleType.ANNUAL
    cultivation_cycle_type: CycleType | None = None
    flowering_strategy: FloweringStrategy | None = None
    growth_determinacy: GrowthDeterminacy | None = None
    typical_lifespan_years: int | None = None
    dormancy_required: bool = False
    vernalization_required: bool = False
    vernalization_min_days: int | None = Field(default=None, ge=1)
    photoperiod_type: PhotoperiodType = PhotoperiodType.DAY_NEUTRAL
    critical_day_length_hours: float | None = Field(default=None, ge=0, le=24)


class LifecycleResponse(BaseModel):
    key: str
    species_key: str
    cycle_type: CycleType
    cultivation_cycle_type: CycleType | None = None
    flowering_strategy: FloweringStrategy | None = None
    growth_determinacy: GrowthDeterminacy | None = None
    typical_lifespan_years: int | None
    dormancy_required: bool
    vernalization_required: bool
    vernalization_min_days: int | None
    photoperiod_type: PhotoperiodType
    critical_day_length_hours: float | None
    phase_sequence_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def grown_as_annual(self) -> bool:
        """Species is cultivated as a (tender) annual.

        True when the cultivation cycle is annual while the botanical cycle is
        not — e.g. tomato: botanically perennial, grown as an annual. Derived
        read-only; never persisted on the domain model.
        """
        return self.cultivation_cycle_type == CycleType.ANNUAL and self.cycle_type != CycleType.ANNUAL
