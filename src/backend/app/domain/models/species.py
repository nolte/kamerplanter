from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.enums import GrowthHabit, PlantTrait, RootType


class Cultivar(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    species_key: str
    breeder: str | None = None
    breeding_year: int | None = None
    traits: list[PlantTrait] = Field(default_factory=list)
    patent_status: str = ""
    days_to_maturity: int | None = Field(default=None, ge=1, le=365)
    disease_resistances: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class Species(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    family_key: str | None = None
    genus: str = ""
    hardiness_zones: list[str] = Field(default_factory=list)
    native_habitat: str = ""
    growth_habit: GrowthHabit = GrowthHabit.HERB
    root_type: RootType = RootType.FIBROUS
    allelopathy_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    base_temp: float = Field(default=10.0, description="Base temperature for GDD calculation (Celsius)")
    synonyms: list[str] = Field(default_factory=list)
    taxonomic_authority: str = ""
    taxonomic_status: str = ""
    description: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("scientific_name")
    @classmethod
    def validate_binomial(cls, v: str) -> str:
        parts = v.strip().split()
        if len(parts) < 2:
            raise ValueError("Scientific name must follow binomial nomenclature (e.g., 'Genus species')")
        return v.strip()

    @field_validator("hardiness_zones")
    @classmethod
    def validate_hardiness_zones(cls, v: list[str]) -> list[str]:
        import re

        for zone in v:
            if not re.match(r"^\d{1,2}[ab]?$", zone):
                raise ValueError(f"Invalid USDA hardiness zone format: '{zone}'")
        return v
