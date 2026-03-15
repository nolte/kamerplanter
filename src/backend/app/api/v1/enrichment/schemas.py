from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime

    from app.common.enums import AuthType, SyncStatus, SyncTrigger


class SourceResponse(BaseModel):
    key: str
    name: str
    source_key: str
    base_url: str
    auth_type: AuthType
    rate_limit_per_minute: int
    priority: int
    enabled: bool


class SyncTriggerRequest(BaseModel):
    full_sync: bool = False


class SyncTriggerResponse(BaseModel):
    key: str
    source_key: str
    status: SyncStatus
    triggered_by: SyncTrigger
    full_sync: bool
    started_at: datetime | None = None


class SyncRunResponse(BaseModel):
    key: str
    source_key: str
    status: SyncStatus
    triggered_by: SyncTrigger
    full_sync: bool
    total_processed: int
    new_mappings: int
    updated_mappings: int
    errors: list[str]
    started_at: datetime | None = None
    finished_at: datetime | None = None


class FieldMappingResponse(BaseModel):
    external_value: str | float | int | bool | list[str] | None = None
    local_value: str | float | int | bool | list[str] | None = None
    confidence: float
    accepted: bool
    accepted_at: datetime | None = None


class EnrichmentResponse(BaseModel):
    key: str
    internal_collection: str
    internal_key: str
    source_key: str
    external_id: str
    field_mappings: dict[str, FieldMappingResponse]


class AcceptFieldsRequest(BaseModel):
    fields: list[str] = Field(min_length=1)


class RejectFieldsRequest(BaseModel):
    fields: list[str] = Field(min_length=1)


class ExternalSearchRequest(BaseModel):
    source_key: str
    query: str


class ExternalSpeciesResponse(BaseModel):
    external_id: str
    scientific_name: str
    common_names: list[str]
    genus: str
    family_name: str
    growth_habit: str
    native_habitat: str
    hardiness_zones: list[str]
    description: str
    image_url: str
    canonical_name: str = ""
    synonyms: list[str] = Field(default_factory=list)
    taxonomic_authority: str = ""
    taxonomic_status: str = ""


class SourceHealthResponse(BaseModel):
    source_key: str
    healthy: bool
