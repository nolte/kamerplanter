from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.common.enums import AuthType, SyncStatus, SyncTrigger

if TYPE_CHECKING:
    from datetime import datetime


class FieldMapping(BaseModel):
    external_value: str | float | int | bool | list[str] | None = None
    local_value: str | float | int | bool | list[str] | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    accepted: bool = False
    accepted_at: datetime | None = None


class ExternalSource(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    name: str
    source_key: str
    base_url: str
    auth_type: AuthType = AuthType.NONE
    rate_limit_per_minute: int = 60
    priority: int = Field(default=0, ge=0)
    enabled: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class ExternalMapping(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    internal_collection: str
    internal_key: str
    source_key: str
    external_id: str
    field_mappings: dict[str, FieldMapping] = Field(default_factory=dict)
    checksum: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class SyncRun(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    source_key: str
    status: SyncStatus = SyncStatus.RUNNING
    triggered_by: SyncTrigger = SyncTrigger.MANUAL
    full_sync: bool = False
    total_processed: int = 0
    new_mappings: int = 0
    updated_mappings: int = 0
    errors: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class GBIFMatchResult(BaseModel):
    usage_key: int
    scientific_name: str
    canonical_name: str
    authorship: str = ""
    rank: str = "SPECIES"
    taxonomic_status: str
    confidence: int = Field(ge=0, le=100)
    match_type: str
    kingdom: str = ""
    family: str = ""
    genus: str = ""
    accepted_key: int | None = None
    accepted_name: str | None = None


class ExternalSpeciesData(BaseModel):
    external_id: str
    scientific_name: str
    common_names: list[str] = Field(default_factory=list)
    genus: str = ""
    family_name: str = ""
    growth_habit: str = ""
    native_habitat: str = ""
    hardiness_zones: list[str] = Field(default_factory=list)
    description: str = ""
    image_url: str = ""
    sunlight: list[str] = Field(default_factory=list)
    watering: str = ""
    cycle: str = ""
    synonyms: list[str] = Field(default_factory=list)
    taxonomic_authority: str = ""
    taxonomic_status: str = ""
    canonical_name: str = ""


class ExternalCultivarData(BaseModel):
    external_id: str
    name: str
    species_external_id: str
    description: str = ""


class SyncResult(BaseModel):
    total_processed: int = 0
    new_mappings: int = 0
    updated_mappings: int = 0
    errors: list[str] = Field(default_factory=list)
