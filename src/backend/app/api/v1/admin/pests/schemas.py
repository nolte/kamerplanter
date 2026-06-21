"""REQ-044 — admin pest-recognition (coverage + gallery + acquisition) DTOs."""

from pydantic import BaseModel, Field


class PestCoverageEntry(BaseModel):
    label: str
    common_name: str
    category: str
    scientific_name: str
    gbif_taxon_key: str | None = None
    total: int = 0  # indexed prototypes
    active: int = 0  # active (curated-in) prototypes
    target: int = 0  # min usable per class
    usable: bool = False  # active >= target


class PestRecognitionStatusResponse(BaseModel):
    feature_enabled: bool
    service_ready: bool
    index_count: int
    target_per_class: int
    classes: list[PestCoverageEntry] = Field(default_factory=list)


class PestAcquireResponse(BaseModel):
    status: str  # "queued"
    task_id: str | None = None


class PestCurationImage(BaseModel):
    id: int
    source_url: str
    license: str | None = None
    attribution: str | None = None
    source: str | None = None
    source_record_id: str | None = None
    is_active: bool = True
    exclusion_reason: str | None = None


class PestCurationImageList(BaseModel):
    label: str
    count: int
    active_count: int
    images: list[PestCurationImage] = Field(default_factory=list)


class SetPestImageActiveRequest(BaseModel):
    is_active: bool
    reason: str | None = None


class SetPestImageActiveResponse(BaseModel):
    label: str
    id: int
    is_active: bool
