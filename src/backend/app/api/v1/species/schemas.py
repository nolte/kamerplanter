from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import GrowthHabit, RootType


class SpeciesCreate(BaseModel):
    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    family_key: str | None = None
    genus: str = ""
    hardiness_zones: list[str] = Field(default_factory=list)
    native_habitat: str = ""
    growth_habit: GrowthHabit = GrowthHabit.HERB
    root_type: RootType = RootType.FIBROUS
    allelopathy_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    base_temp: float = 10.0
    synonyms: list[str] = Field(default_factory=list)
    taxonomic_authority: str = ""
    taxonomic_status: str = ""
    description: str = ""

class SpeciesResponse(BaseModel):
    key: str
    scientific_name: str
    common_names: list[str]
    family_key: str | None
    genus: str
    hardiness_zones: list[str]
    native_habitat: str
    growth_habit: GrowthHabit
    root_type: RootType
    allelopathy_score: float
    base_temp: float
    synonyms: list[str] = Field(default_factory=list)
    taxonomic_authority: str = ""
    taxonomic_status: str = ""
    description: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

class SpeciesListResponse(BaseModel):
    items: list[SpeciesResponse]
    total: int
    offset: int
    limit: int
