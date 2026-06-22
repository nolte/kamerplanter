"""REQ-044 — admin pest-recognition (coverage + gallery + acquisition) DTOs."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import PestImageStatus


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


# ── REQ-010 — user-contributed pest image moderation (global promotion) ──


class PestContributionModerationItem(BaseModel):
    """A single user-contributed pest image, for cross-tenant moderation.

    ``content_uri`` / ``thumbnail_uri`` point at the global content endpoint
    so the admin can preview the pixels regardless of which tenant owns them.
    Provenance (``tenant_key`` / ``contributed_by`` / ``created_at``) supports
    the moderation decision.
    """

    id: str
    pest_key: str
    attachment_id: str
    content_uri: str
    thumbnail_uri: str | None = None
    status: PestImageStatus
    caption: str | None = None
    tenant_key: str
    contributed_by: str
    created_at: datetime | None = None
    promoted_at: datetime | None = None
    promoted_by: str | None = None


class PestContributionModerationList(BaseModel):
    pest_key: str
    count: int
    promoted_count: int
    images: list[PestContributionModerationItem] = Field(default_factory=list)


class PromotePestContributionRequest(BaseModel):
    """Moderation mutation for a single contribution (both fields optional).

    * ``promote`` — toggle global visibility (the recognition-index seam);
    * ``is_active`` — REQ-010 curation: deselect (hide) / re-include the image
      in the gallery *without* touching the recognition index.

    Both may be sent together or independently; an all-``None`` body is a no-op
    (idempotent). ``promote`` stays optional for backward compatibility with the
    original promote-only contract.
    """

    promote: bool | None = None
    is_active: bool | None = None


class PromotePestContributionResponse(BaseModel):
    id: str
    pest_key: str
    status: PestImageStatus
    is_active: bool = True
    promoted_at: datetime | None = None
    promoted_by: str | None = None
