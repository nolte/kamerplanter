
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime

    from app.common.enums import PlantTrait


class CultivarCreate(BaseModel):
    name: str
    species_key: str
    breeder: str | None = None
    breeding_year: int | None = None
    traits: list[PlantTrait] = Field(default_factory=list)
    patent_status: str = ""
    days_to_maturity: int | None = Field(default=None, ge=1, le=365)
    disease_resistances: list[str] = Field(default_factory=list)
    phase_watering_overrides: dict[str, int] | None = None

class CultivarResponse(BaseModel):
    key: str
    name: str
    species_key: str
    breeder: str | None
    breeding_year: int | None
    traits: list[PlantTrait]
    patent_status: str
    days_to_maturity: int | None
    disease_resistances: list[str]
    phase_watering_overrides: dict[str, int] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
