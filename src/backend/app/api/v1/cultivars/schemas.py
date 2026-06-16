from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import DtmReference, PlantTrait


class CultivarCreate(BaseModel):
    name: str
    species_key: str
    breeder: str | None = None
    breeding_year: int | None = None
    traits: list[PlantTrait] = Field(default_factory=list)
    patent_status: str = ""
    days_to_maturity: int | None = Field(default=None, ge=1, le=1095)
    dtm_reference: DtmReference | None = None
    bearing_start_year_min: int | None = Field(default=None, ge=1, le=20)
    bearing_start_year_max: int | None = Field(default=None, ge=1, le=20)
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
    dtm_reference: DtmReference | None = None
    bearing_start_year_min: int | None = None
    bearing_start_year_max: int | None = None
    disease_resistances: list[str]
    phase_watering_overrides: dict[str, int] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
