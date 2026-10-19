from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import (
    FrostTolerance,
    GrowthHabit,
    NutrientDemand,
    PollinationType,
    RootDepth,
)


class PhRange(BaseModel):
    min_ph: float = Field(ge=3.0, le=9.0)
    max_ph: float = Field(ge=3.0, le=9.0)


class BotanicalFamily(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    common_name_de: str = ""
    common_name_en: str = ""
    order: str | None = None
    description: str = ""
    typical_nutrient_demand: NutrientDemand = NutrientDemand.MEDIUM_FEEDER
    nitrogen_fixing: bool = False
    #: REQ-053 GP-FR-131 / K-004 (M6, #2325): years before the same family may return
    #: to a bed; ``None`` = unsourced (E-10). Read by ``CropRotationValidator.validate_planting_in_location``
    #: (WP 3.4): ``Species.rotation_pause_years`` overrides it, ``None`` falls back to the caller's
    #: ``rotation_window_years`` (at most 8). 0 = no pause needed.
    rotation_pause_years: int | None = Field(default=None, ge=0, le=8)
    typical_root_depth: RootDepth = RootDepth.MEDIUM
    soil_ph_preference: PhRange | None = None
    frost_tolerance: FrostTolerance = FrostTolerance.MODERATE
    typical_growth_forms: list[GrowthHabit] = Field(default_factory=lambda: [GrowthHabit.HERB])
    common_pests: list[str] = Field(default_factory=list)
    common_diseases: list[str] = Field(default_factory=list)
    pollination_type: list[PollinationType] = Field(default_factory=lambda: [PollinationType.INSECT])
    rotation_category: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("name")
    @classmethod
    def name_must_end_with_aceae(cls, v: str) -> str:
        if not v.endswith("aceae"):
            msg = f"Familienname '{v}' muss auf '-aceae' enden"
            raise ValueError(msg)
        return v

    @field_validator("order")
    @classmethod
    def order_must_end_with_ales(cls, v: str | None) -> str | None:
        if v is not None and not v.endswith("ales"):
            msg = f"Ordnungsname '{v}' muss auf '-ales' enden"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def nitrogen_fixing_not_heavy(self) -> BotanicalFamily:
        if self.nitrogen_fixing and self.typical_nutrient_demand == NutrientDemand.HEAVY_FEEDER:
            msg = (
                "nitrogen_fixing=true ist inkompatibel mit typical_nutrient_demand='heavy_feeder'. "
                "Stickstofffixierende Familien sind Schwach- oder Mittelzehrer."
            )
            raise ValueError(msg)
        return self
