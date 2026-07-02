from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.common.enums import (
    CycleType,
    FloweringStrategy,
    GrowthDeterminacy,
    PhotoperiodType,
    StressTolerance,
)


class GrowthPhase(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    display_name: str = ""
    description: str = ""
    lifecycle_key: str = ""
    typical_duration_days: int = Field(ge=1)
    sequence_order: int = Field(ge=0)
    is_terminal: bool = False
    allows_harvest: bool = False
    is_recurring: bool = False
    stress_tolerance: StressTolerance = StressTolerance.MEDIUM
    watering_interval_days: int | None = Field(default=None, ge=1, le=90)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class LifecycleConfig(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    species_key: str = ""
    cycle_type: CycleType = CycleType.ANNUAL
    # ── Lebensdauer in Kultur vs. botanisch (REQ-001/REQ-003, Plan WP-3) ──
    # cycle_type is the BOTANICAL lifespan; cultivation_cycle_type is how the species is
    # actually grown (e.g. tomato: botanically perennial, grown as an annual = "tender perennial").
    cultivation_cycle_type: CycleType | None = Field(
        default=None,
        description="Practised lifespan in cultivation; overrides cycle_type for season/overwintering "
        "hints. None = same as the botanical cycle_type.",
    )
    # ── Blüh-Strategie (REQ-003, Plan WP-4) — orthogonal to lifespan ──
    flowering_strategy: FloweringStrategy | None = Field(
        default=None,
        description="monocarpic = flowers once then dies (agave, many bamboos); polycarpic = repeated.",
    )
    # ── Wuchs-Determiniertheit (REQ-003 E4) — orthogonal to lifespan/flowering ──
    growth_determinacy: GrowthDeterminacy | None = Field(
        default=None,
        description="indeterminate species stay in a stable productive phase (fruiting/flowering_fruit, "
        "recurring) with concurrent veg/flower/fruit growth (harvest_pattern='continuous'); determinate "
        "follows the linear path to a terminal phase. None = treat as determinate.",
    )
    typical_lifespan_years: int | None = None
    dormancy_required: bool = False
    vernalization_required: bool = False
    vernalization_min_days: int | None = Field(default=None, ge=1)
    photoperiod_type: PhotoperiodType = PhotoperiodType.DAY_NEUTRAL
    critical_day_length_hours: float | None = Field(default=None, ge=0, le=24)
    cycle_restart_phase_order: int | None = Field(
        default=None,
        description="For perennials: sequence_order at which the cycle restarts after the terminal phase.",
    )
    # ── Cyclic lifecycle bounds & maturity (REQ-003 D1/D4/D6/D10) ──
    max_seasons: int | None = Field(
        default=None,
        ge=1,
        description="Number of seasons before the cycle terminates (2 = biennial); None = unbounded "
        "(polycarpic perennial). Defaults to 2 for BIENNIAL when unset.",
    )
    first_bearing_year: int | None = Field(
        default=None,
        ge=1,
        le=30,
        description="Earliest standing year a perennial bears a usable yield; below it the plant is juvenile "
        "and reproductive phases are skipped (D4).",
    )
    expected_productive_years: int | None = Field(
        default=None,
        ge=1,
        description="Number of productive years after first bearing; beyond it the plant is 'declining'.",
    )
    phase_sequence_key: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_biennial_vernalization(self) -> LifecycleConfig:
        if self.cycle_type == CycleType.BIENNIAL and not self.vernalization_required:
            raise ValueError("Biennial plants must have vernalization_required=True")
        return self
