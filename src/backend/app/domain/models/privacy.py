"""Domain models for REQ-025 Privacy & GDPR data subject rights."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# ── Type aliases ───────────────────────────────────────────────────

type DataExportRequestKey = str
type ConsentRecordKey = str
type ProcessingRestrictionKey = str
type ErasureRequestKey = str
type EmailChangeRequestKey = str

# ── Status / reason literals ───────────────────────────────────────

type DataExportStatus = Literal["pending", "processing", "completed", "expired", "failed"]
type ErasureStatus = Literal["scheduled", "in_progress", "completed", "partially_completed"]
type EmailChangeStatus = Literal["pending", "confirmed", "expired"]
type RestrictionReason = Literal[
    "accuracy_contested",
    "unlawful_processing",
    "purpose_expired",
    "objection_pending",
]


# ── Core node models ───────────────────────────────────────────────


class DataExportRequest(BaseModel):
    """Art. 15/20: User-initiated data export job."""

    key: str | None = Field(default=None, alias="_key")
    user_key: str
    status: DataExportStatus = "pending"
    file_path: str | None = None
    file_size_bytes: int | None = None
    requested_at: datetime | None = None
    processing_started_at: datetime | None = None
    completed_at: datetime | None = None
    expires_at: datetime | None = None
    error_message: str | None = None
    download_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class ConsentRecord(BaseModel):
    """Tracks consent state per user and processing purpose."""

    key: str | None = Field(default=None, alias="_key")
    user_key: str
    purpose: str
    granted: bool
    granted_at: datetime | None = None
    revoked_at: datetime | None = None
    ip_address: str | None = None
    ip_anonymized_at: datetime | None = None
    user_agent: str | None = None
    consent_version: str = "1.0"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class ProcessingRestriction(BaseModel):
    """Art. 18: User-set processing restriction for a given scope."""

    key: str | None = Field(default=None, alias="_key")
    user_key: str
    scope: str
    reason: RestrictionReason
    notes: str | None = None
    lifted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class ErasureRequest(BaseModel):
    """Art. 17: Account-deletion request, executed asynchronously after 90d."""

    key: str | None = Field(default=None, alias="_key")
    user_key: str
    status: ErasureStatus = "scheduled"
    requested_at: datetime | None = None
    soft_deleted_at: datetime | None = None
    hard_delete_scheduled_at: datetime | None = None
    completed_at: datetime | None = None
    anonymized_collections: list[str] = Field(default_factory=list)
    deleted_collections: list[str] = Field(default_factory=list)
    pseudonymized_collections: list[str] = Field(default_factory=list)
    storage_cleanup_scopes: list[str] = Field(default_factory=list)
    retained_reason: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class EmailChangeRequest(BaseModel):
    """Art. 16: Two-step email-change verification."""

    key: str | None = Field(default=None, alias="_key")
    user_key: str
    new_email: EmailStr
    verification_token_hash: str
    status: EmailChangeStatus = "pending"
    requested_at: datetime | None = None
    expires_at: datetime
    confirmed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


# ── Engine / service support models ────────────────────────────────


class ConsentPurpose(BaseModel):
    """Static definition of a processing purpose recognised by the system."""

    key: str
    label_de: str
    label_en: str
    description_de: str
    description_en: str
    legal_basis: str
    required: bool = False


class ConsentWithPurpose(BaseModel):
    """Consent state combined with its purpose definition (for UI listings)."""

    purpose: str
    label: str
    description: str
    legal_basis: str
    required: bool
    granted: bool
    granted_at: datetime | None = None
    revoked_at: datetime | None = None


class DataSourceDefinition(BaseModel):
    """Manifest entry: declares one user-related data source for export."""

    collection: str
    label: str
    fields: list[str] = Field(default_factory=list)
    filter_field: str | None = None
    edge_collection: str | None = None


class AnonymizationRule(BaseModel):
    """Rule for replacing user references with an anonymous marker."""

    collection: str
    user_field: str
    anonymized_value: str = "[deleted]"
    reason: str


class PseudonymizationRule(BaseModel):
    """Rule for replacing user references with a deterministic tombstone hash."""

    collection: str
    user_field: str
    replacement_strategy: Literal["tombstone_hash"] = "tombstone_hash"
    reason: str


class StorageCleanupRule(BaseModel):
    """Object-storage cleanup rule (Phase 0 of the erasure pipeline)."""

    scope: Literal["user_personal", "user_diary_attachments"]
    description: str
    action: Literal["hard_delete", "anonymize_metadata_and_strip_exif"]
    ref: str


class ReferenceIndexCleanupRule(BaseModel):
    """pgvector reference-index cleanup rule (Phase 0.5 of the erasure pipeline).

    REQ-034 §5 / REQ-025 §3.1 (SR-003). Removes user-contributed DINOv2
    embeddings (``source == 'user_contributed'``) from the reference index by
    provenance (``contributed_by`` for user erasure, ``tenant_key`` for tenant
    erasure). The index lives in pgvector, outside ArangoDB, so it needs its
    own cleanup path that runs before the generic ArangoDB deletion (Phase 1).
    """

    store: Literal["pgvector"] = "pgvector"
    collection: str
    filter: str
    action: Literal["hard_delete"] = "hard_delete"
    ref: str


class ErasurePlan(BaseModel):
    """Aggregated plan that the erasure executor processes step by step."""

    user_key: str
    storage_cleanup: list[StorageCleanupRule] = Field(default_factory=list)
    reference_index_cleanup: list[ReferenceIndexCleanupRule] = Field(default_factory=list)
    anonymize: list[AnonymizationRule] = Field(default_factory=list)
    pseudonymize_audit: list[PseudonymizationRule] = Field(default_factory=list)
    delete: list[str] = Field(default_factory=list)
    soft_delete_immediate: bool = True
    hard_delete_after_days: int = 90


# ── Privacy-policy response models ─────────────────────────────────


class RetentionCategoryInfo(BaseModel):
    category: str
    description: str
    retention_period: str


class DataControllerInfo(BaseModel):
    name: str
    contact_email: str
    address: str | None = None


class RightInfo(BaseModel):
    article: str
    title: str
    description: str


class PrivacyPolicyInfo(BaseModel):
    """Public privacy-policy snapshot (no auth required)."""

    version: str
    effective_date: date
    purposes: list[ConsentPurpose]
    retention_summary: list[RetentionCategoryInfo]
    data_controller: DataControllerInfo
    rights_summary: list[RightInfo]
