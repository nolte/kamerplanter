from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import (
    FrostTolerance,
    GrowthHabit,
    NutrientDemand,
    PollinationType,
    RootDepth,
)
from app.domain.models.botanical_family import PhRange


class FamilyCreate(BaseModel):
    name: str
    common_name_de: str = ""
    common_name_en: str = ""
    order: str | None = None
    description: str = ""
    typical_nutrient_demand: NutrientDemand = NutrientDemand.MEDIUM
    nitrogen_fixing: bool = False
    typical_root_depth: RootDepth = RootDepth.MEDIUM
    soil_ph_preference: PhRange | None = None
    frost_tolerance: FrostTolerance = FrostTolerance.MODERATE
    typical_growth_forms: list[GrowthHabit] = Field(default_factory=lambda: [GrowthHabit.HERB])
    common_pests: list[str] = Field(default_factory=list)
    common_diseases: list[str] = Field(default_factory=list)
    pollination_type: list[PollinationType] = Field(default_factory=lambda: [PollinationType.INSECT])
    rotation_category: str = ""

    # The request schema mirrors the ``BotanicalFamily`` domain rules (#970): the
    # router builds the domain model from this body, and a domain ValidationError
    # raised there escapes the handler as a 500 rather than the 422 an invalid
    # input deserves. Rejecting the same shapes at the boundary keeps a bad family
    # name from ever reaching that construction site — the create/update routes
    # answer 422 with a field-anchored error, not INTERNAL_ERROR.
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
    def nitrogen_fixing_not_heavy(self) -> Self:
        if self.nitrogen_fixing and self.typical_nutrient_demand == NutrientDemand.HEAVY:
            msg = (
                "nitrogen_fixing=true ist inkompatibel mit typical_nutrient_demand='heavy'. "
                "Stickstofffixierende Familien sind Schwach- oder Mittelzehrer."
            )
            raise ValueError(msg)
        return self


class FamilyResponse(BaseModel):
    key: str
    name: str
    common_name_de: str
    common_name_en: str
    order: str | None
    description: str
    typical_nutrient_demand: NutrientDemand
    nitrogen_fixing: bool
    typical_root_depth: RootDepth
    soil_ph_preference: PhRange | None
    frost_tolerance: FrostTolerance
    typical_growth_forms: list[GrowthHabit]
    common_pests: list[str]
    common_diseases: list[str]
    pollination_type: list[PollinationType]
    rotation_category: str
    species_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
