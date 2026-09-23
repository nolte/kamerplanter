"""Domain models for REQ-025 Privacy & GDPR data subject rights."""

from datetime import date, datetime
from typing import Literal, Self

from pydantic import BaseModel, EmailStr, Field, model_validator

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
    #: Collections of :attr:`DataExportEngine.USER_DATA_MANIFEST` that this run
    #: took into scope, written by the executor from the manifest it read. The
    #: Art. 15 record has to be able to say *which* sources were disclosed, and
    #: the only honest source for that is the manifest the run actually walked
    #: (#1622) — not a second list written beside it.
    manifest_collections: list[str] = Field(default_factory=list)
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
    """Manifest entry: declares one user-related data source for export.

    ``tenant_scoped`` marks a source whose documents carry ``tenant_key`` and
    are reached by a user-reference field rather than by ownership: the walk
    restricts those to the subject's own tenants, so a writer elsewhere cannot
    plant a document into another subject's disclosure by naming their key
    (#1662 SCR-001).

    ``disclosure_gap`` is the honest form of a source that **cannot** be
    disclosed by subject today: the manifest still names the category (Art.
    15(1) is a right to know which categories exist), the bundle carries the
    reason, and the walk never queries it — an empty result would read exactly
    like "no data here", which is the silence #1645 removes.

    ``attribution_gap`` is the partial form of the same honesty (#1669): the
    source *is* disclosed by ``filter_field``, but rows written before that
    field existed carry ``null`` there and can never be matched to the subject.
    The bundle states this beside the delivered records, so a subject who knows
    they harvested in 2025 learns why that harvest is not in the file rather
    than reading the section as complete.
    """

    collection: str
    label: str
    fields: list[str] = Field(default_factory=list)
    filter_field: str | None = None
    edge_collection: str | None = None
    tenant_scoped: bool = False
    disclosure_gap: str | None = None
    attribution_gap: str | None = None


#: Who removes an :class:`ErasureStep` at runtime. Closed on purpose: a step
#: whose executor is not one of these cannot be attributed, and an inventory of
#: personal data that cannot say who erases an entry is the documentation half
#: of the split #1622 measured. ``retention_worker`` is the **declared gap** —
#: the NFR-011 ArangoDB deletion worker does not exist yet, so a step carrying
#: it is enumerated but not executed, and says so.
type ErasureExecutor = Literal[
    "account_cascade",
    "membership_cascade",
    "pest_image_cleanup",
    "storage_cleanup",
    "reference_index_cleanup",
    "retention_worker",
]


#: The two endpoint attributes an ArangoDB edge can reach a vertex through.
_EDGE_ENDPOINTS: frozenset[str] = frozenset({"_from", "_to"})


class ErasureStep(BaseModel):
    """One entry of the single declared erasure inventory.

    ``kind`` distinguishes what the executor has to do with the name:
    ``edge`` and ``document`` are ArangoDB collections filtered by the user
    reference, ``user`` is the user document itself, and ``phase`` is a
    non-collection stage (object storage, reference index, audit hashing)
    whose own rules live in the matching engine constant.

    ``user_field`` is how the executor finds the subject's rows (#1663). It is
    required for ``edge`` and ``document`` and forbidden for ``user`` and
    ``phase``. Before #1663 the step had no such field: the one executor that
    ran hard-coded ``doc.user_key`` / ``e._from`` for its slice, and any other
    executor would have had to guess — a guessed filter on the wrong field
    deletes somebody else's rows.

    * ``document`` — the model field carrying the user key (``user_key``,
      ``contributed_by`` …); the executor matches ``doc.<user_field> == key``.
    * ``edge`` — the endpoint (``_from`` / ``_to``). Without ``via`` that
      endpoint *is* ``users/<key>``. With ``via`` it points into the named
      document collection instead, and the edge belongs to the subject when the
      document it points at does — as matched by that collection's own
      ``document`` step, which therefore has to come *after* the edge in the
      inventory (``membership_in`` runs ``memberships -> tenants`` and never
      touches ``users``; the pest-detection edges start at ``pest_detections``).
    """

    collection: str
    kind: Literal["edge", "document", "user", "phase"]
    executor: ErasureExecutor
    user_field: str | None = None
    via: str | None = None
    note: str = ""

    @model_validator(mode="after")
    def _user_field_matches_kind(self) -> Self:
        if self.kind in ("user", "phase"):
            if self.user_field is not None or self.via is not None:
                msg = f"{self.kind} step '{self.collection}' filters nothing and takes no user_field/via"
                raise ValueError(msg)
            return self
        if not self.user_field:
            msg = f"{self.kind} step '{self.collection}' must declare the user_field it filters the subject on"
            raise ValueError(msg)
        if self.kind == "edge":
            if self.user_field not in _EDGE_ENDPOINTS:
                msg = f"edge step '{self.collection}' reaches the subject through _from or _to, not '{self.user_field}'"
                raise ValueError(msg)
        else:
            if self.user_field in _EDGE_ENDPOINTS:
                msg = f"document step '{self.collection}' cannot be keyed on an edge endpoint"
                raise ValueError(msg)
            if self.via is not None:
                msg = f"document step '{self.collection}' is keyed directly; via applies to edges only"
                raise ValueError(msg)
        return self


class AnonymizationRule(BaseModel):
    """Rule for removing a user's identity from a document that is retained.

    ``user_field`` is the field the executor **matches** the subject on and then
    rewrites; it must therefore carry a user key, never free text — a rule
    keyed on a typed-in name matches whatever was typed and is inert with
    respect to the account being erased (#1663, measured on #1662).

    ``replacement_strategy`` says what the key becomes: ``"marker"`` writes
    ``anonymized_value``; ``"tombstone_hash"`` writes the deterministic
    :meth:`ErasureEngine.compute_tombstone_hash`, so the erased user's
    retained records stay linkable to *each other* (CanG / PflSchG audit) while
    no longer naming anyone.

    ``clear_fields`` are the free-text companions of the key (``harvester``,
    ``inspector``, ``applied_by``) that are emptied in the same write: a display
    name is personal data on its own and would otherwise outlive the account.
    """

    collection: str
    user_field: str
    anonymized_value: str = "[deleted]"
    replacement_strategy: Literal["marker", "tombstone_hash"] = "marker"
    clear_fields: list[str] = Field(default_factory=list)
    reason: str


class PseudonymizationRule(BaseModel):
    """Rule for replacing user references with a deterministic tombstone hash."""

    collection: str
    user_field: str
    replacement_strategy: Literal["tombstone_hash"] = "tombstone_hash"
    reason: str


class StorageCleanupRule(BaseModel):
    """Object-storage cleanup rule (Phase 0 of the erasure pipeline)."""

    scope: Literal["user_personal", "user_diary_attachments", "user_pest_reference_images"]
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
    #: The attributed inventory. ``delete`` below is the bare name sequence
    #: derived from it and kept for readers that only need the order.
    steps: list[ErasureStep] = Field(default_factory=list)
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
