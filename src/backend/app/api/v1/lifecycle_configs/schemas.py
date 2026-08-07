from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from app.common.enums import CycleType, FloweringStrategy, GrowthDeterminacy, PhotoperiodType


class LifecycleCreate(BaseModel):
    """Write body for a species' lifecycle configuration (POST and PUT).

    ``cycle_type`` is **required** on purpose (issue #949). It used to default to
    ``annual``, which meant a caller that simply did not know the botanical cycle
    got the strongest possible assertion recorded on its behalf — and the phase
    sequence resolver keys on exactly this field. A missing cycle is now a ``422``:
    an explicit refusal beats a silent, wrong answer.
    """

    species_key: str
    cycle_type: CycleType = Field(
        description="Botanical lifespan. Required — there is deliberately no default, "
        "because guessing 'annual' schedules a terminal harvest for a perennial.",
    )
    cultivation_cycle_type: CycleType | None = None
    flowering_strategy: FloweringStrategy | None = None
    growth_determinacy: GrowthDeterminacy | None = None
    typical_lifespan_years: int | None = None
    dormancy_required: bool = False
    vernalization_required: bool = False
    vernalization_min_days: int | None = Field(default=None, ge=1)
    photoperiod_type: PhotoperiodType = PhotoperiodType.DAY_NEUTRAL
    critical_day_length_hours: float | None = Field(default=None, ge=0, le=24)
    phase_sequence_key: str | None = Field(
        default=None,
        description="Bind the species to this phase sequence. Omit to leave the current "
        "binding untouched; it is never cleared by omission. Discover keys with "
        "GET /api/v1/phase-sequences.",
    )


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
