
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.common.enums import (
    FrostTolerance,
    GrowthHabit,
    NutrientDemand,
    PollinationType,
    RootDepth,
)

if TYPE_CHECKING:
    from datetime import datetime

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
    pollination_type: list[PollinationType] = Field(
        default_factory=lambda: [PollinationType.INSECT]
    )
    rotation_category: str = ""


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
