"""Domain models for REQ-025 Privacy & GDPR data subject rights."""

from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, EmailStr, Field, StringConstraints, model_validator

# ── Type aliases ───────────────────────────────────────────────────

type DataExportRequestKey = str
type ConsentRecordKey = str
type ProcessingRestrictionKey = str
type ErasureRequestKey = str
type EmailChangeRequestKey = str

# ── Status / reason literals ───────────────────────────────────────

type DataExportStatus = Literal["pending", "processing", "completed", "expired", "failed"]
type ErasureStatus = Literal["scheduled", "in_progress", "completed", "partially_completed"]
#: Which entry point created an erasure request (#1767). ``self_service`` is the
#: Art. 17 request with its 90-day grace; ``platform_admin`` and
#: ``unverified_cleanup`` are due at once but keep the same record, gate and retry.
type ErasureOrigin = Literal["self_service", "platform_admin", "unverified_cleanup"]
#: How the person who asked for an erasure re-authenticated (#1813, #1814):
#: ``password`` — the requester's current password; ``oidc_reauth`` — an account
#: without a local password signed in again at its identity provider (#1815);
#: ``email_code`` — one whose providers cannot do that entered the code mailed to it.
#: ``echo`` is written no more: it marks records from before #1815, when such an
#: account confirmed by typing the target's e-mail back alone — kept readable.
#: ``None`` on records of the unverified-account cleanup and on older records.
type ErasureStepUp = Literal["oidc_reauth", "email_code", "echo", "password"]
#: What an account erasure did with one personal tenant of the subject (#1788).
#: ``erased`` — the subject was its only active member, and the tenant-erasure
#: inventory (#1769) completed on it; ``retained_other_members`` — another active
#: member uses it, so it is kept and only the owner reference goes (the spec names
#: no successor, #1788); ``absent`` — neither the tenant nor a deletion record of
#: it exists any more.
type PersonalTenantOutcome = Literal["erased", "retained_other_members", "absent"]
#: ``cancelled`` — withdrawn because the owner took the account back (password
#: reset, password change, signing out everywhere) while it was pending (#1841).
type EmailChangeStatus = Literal["pending", "confirmed", "expired", "cancelled", "reverted"]
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


class PersonalTenantErasure(BaseModel):
    """One personal tenant of an erased account, and what the erasure did with it (#1788).

    Carries no name, slug or owner: a personal tenant is named after its owner.
    ``tenant_erasure_record_key`` points at the tenant deletion's own proof
    (``tenant_erasure_records``), which outlives the tenant.
    """

    tenant_key: str
    outcome: PersonalTenantOutcome
    tenant_erasure_record_key: str | None = None
    reason: str | None = None


class ErasureRequest(BaseModel):
    """Art. 17: Account-deletion request, executed asynchronously after 90d."""

    key: str | None = Field(default=None, alias="_key")
    user_key: str
    status: ErasureStatus = "scheduled"
    #: Records written before #1767 carry no origin; they are all self-service.
    origin: ErasureOrigin = "self_service"
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
    #: Retry lifecycle of the scheduled erasure (#1666). ``attempt_count`` counts
    #: failed runs; ``next_attempt_at`` is the backoff horizon before which the
    #: daily beat leaves the request alone. The request stays selected — the
    #: Art. 17 duty is deferred, never dropped.
    attempt_count: int = Field(default=0, ge=0)
    last_attempt_at: datetime | None = None
    next_attempt_at: datetime | None = None
    #: Set once export cleanup, Phase 0 and Phase 0.5 finished for this request;
    #: a retry then runs only the ArangoDB plan (#1666).
    pre_arango_completed_at: datetime | None = None
    #: Which reference-index store Phase 0.5 ran against (``"inference_service"``
    #: / ``"noop"``) and how many contributed vectors it removed, recorded with
    #: the pre-ArangoDB checkpoint (#1753). Neither names the subject.
    reference_index_binding: str | None = None
    reference_index_removed: int | None = Field(default=None, ge=0)
    #: The same for the contributed pest-recognition prototypes (#1759).
    pest_prototype_binding: str | None = None
    pest_prototypes_removed: int | None = Field(default=None, ge=0)
    #: The step-up the request was confirmed with (#1813, #1814).
    step_up: ErasureStepUp | None = None
    #: Who asked, when it was not the subject (``platform_admin``): the salted
    #: ``ErasureEngine.log_subject`` reference, never the account key — the record
    #: outlives both accounts (#1814, the #1791 shape).
    requested_by_subject: str | None = None
    #: Phase 0 hard-delete outcome (#1770): stored objects deleted, and objects
    #: kept because another member's record still holds the same bytes.
    storage_objects_removed: int | None = Field(default=None, ge=0)
    storage_objects_retained_shared: int | None = Field(default=None, ge=0)
    #: Of those kept, objects no record held any more after the ArangoDB plan,
    #: released then (#1770); recorded with ``completed``.
    storage_objects_released: int | None = Field(default=None, ge=0)
    #: The subject's personal tenants, resolved (by owner) before the first one
    #: is erased (#1788). Persisted first because the account plan replaces the
    #: owner reference and a deleted tenant cannot be listed again, so a retry
    #: still knows which tenant deletions this request depends on.
    personal_tenant_keys: list[str] = Field(default_factory=list)
    #: What the erasure did with each of them; written with ``completed``.
    personal_tenants: list[PersonalTenantErasure] = Field(default_factory=list)
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
    #: The address the account left at confirmation, and the hash of the one-time
    #: token mailed to it that takes the account back (#1848). Both exist only
    #: until ``revert_expires_at``; the R-07 task clears them after (NFR-011).
    previous_email: EmailStr | None = None
    revert_token_hash: str | None = None
    revert_expires_at: datetime | None = None
    reverted_at: datetime | None = None
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


class DisclosureExclusion(BaseModel):
    """An erasure target deliberately not disclosed under Art. 15 (#1719).

    The erasure inventory removes or anonymises a collection *because* it holds
    the subject's data, so by default the Art. 15 bundle discloses it too
    (``scripts/check_privacy_inventory.py`` R2, reverse direction). An entry
    here is the written exception: a collection whose rows carry no information
    about the subject beyond what a disclosed source already delivers — the
    graph edge between the account and a disclosed document, or an edge whose
    attributes are a copy of fields on one. ``reason`` is the claim a reviewer
    checks against the write path.
    """

    collection: str
    reason: str = Field(min_length=1)


#: Who removes an :class:`ErasureStep` at runtime. Closed on purpose: a step
#: whose executor is not one of these cannot be attributed, and an inventory of
#: personal data that cannot say who erases an entry is the documentation half
#: of the split #1622 measured. Every name has a runtime reader (#1645):
#:
#: * ``account_erasure`` — ``ArangoErasureExecutor`` as run by
#:   ``PrivacyService.erase_account``, the one entry both account-deletion paths
#:   share (platform-admin delete, #1664; scheduled self-service Art. 17,
#:   #1645). No narrower path runs these steps.
#: * ``account_cascade`` — the same executor, and additionally the slice
#:   ``ArangoUserRepository.delete`` runs for the unverified-account cleanup.
#: * ``pest_image_cleanup`` — ``PrivacyService._run_pest_image_document_cleanup``
#:   (retracts a promoted image's embedding first); the executor's own pass is
#:   the safety net.
#: * ``storage_cleanup`` / ``reference_index_cleanup`` — the object-storage and
#:   pgvector phases ``erase_account`` runs before the ArangoDB transaction.
#:
#: Until #1645 this set also carried ``retention_worker`` ("declared, not yet
#: executed by the self-service path") and ``membership_cascade`` (a membership
#: repository cascade #1664 removed). Neither named a runtime executor any
#: more, so both were folded into ``account_erasure``.
#: ``scripts/check_privacy_inventory.py`` reads this alias as its closed set.
type ErasureExecutor = Literal[
    "account_cascade",
    "account_erasure",
    "pest_image_cleanup",
    "storage_cleanup",
    "reference_index_cleanup",
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
    * ``document`` with ``via`` (#1700) — the row carries no account key, only
      the ``_key`` of a parent row that does: ``location_assignments.membership_key``
      points at the subject's ``memberships``. The executor matches
      ``doc.<user_field> IN <keys of the parent rows>``; the parent's own step
      comes *after* this one, like an edge's.
    """

    collection: str
    kind: Literal["edge", "document", "user", "phase"]
    executor: ErasureExecutor
    user_field: str | None = None
    via: str | None = None
    #: Extra equality predicates a ``document`` row must also satisfy (#1700).
    #: ``attachments`` is removed only for ``category == pest_reference`` — the
    #: rows whose bytes the storage phase hard-deleted; the other categories are
    #: tenant records and are anonymised instead.
    where: dict[str, str] = Field(default_factory=dict)
    note: str = ""

    @model_validator(mode="after")
    def _user_field_matches_kind(self) -> Self:
        if self.kind in ("user", "phase"):
            if self.user_field is not None or self.via is not None or self.where:
                msg = f"{self.kind} step '{self.collection}' filters nothing and takes no user_field/via/where"
                raise ValueError(msg)
            return self
        if self.kind == "edge" and self.where:
            msg = f"edge step '{self.collection}' is matched by its endpoint only; where applies to documents"
            raise ValueError(msg)
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
    #: Fields rewritten to ``<ANONYMIZED_KEY_PREFIX><doc._key>`` rather than
    #: emptied (#1700): a value that must stay non-empty and unique (a tenant's
    #: ``slug`` has a unique index) but was derived from the subject (a personal
    #: tenant's ``name``/``slug`` come from the display name).
    rename_fields: list[str] = Field(default_factory=list)
    #: Equality predicates a row must satisfy for :attr:`rename_fields` to apply;
    #: empty means every matched row. The key reference is replaced either way.
    rename_when: dict[str, str] = Field(default_factory=dict)
    reason: str


class ErasureExclusion(BaseModel):
    """A stored user-reference field the erasure deliberately does not touch (#1700).

    ``scripts/check_privacy_inventory.py`` (R6) requires every persisted model
    field shaped like an account key to be reached by the inventory or named
    here. The reason is the claim: typically that the field is free text typed
    by the caller and never an account key, so matching on it would erase
    whatever was typed (the class #1663 measured on ``harvester``).
    """

    collection: str
    user_field: str
    reason: str = Field(min_length=1)


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

    #: Never empty (#1664): every executor filter is ``doc[@field] == @user_key``,
    #: and unattributed rows carry ``""`` (``pest_detections.user_key`` defaults
    #: to it) — a blank key would erase other users' rows, not nobody's.
    user_key: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
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


class ErasureStepOutcome(BaseModel):
    """How many rows one declared :class:`ErasureStep` reached (#1664).

    ``affected`` is what the store reported for the write — removed rows for an
    ``edge`` / ``document`` / ``user`` step, rewritten rows (summed over the
    phase's rules) for the two ArangoDB phases. It is a measurement, never a
    status: a step that ran and matched nothing reports ``0``, and the reach
    test fails on exactly that.
    """

    collection: str
    kind: Literal["edge", "document", "user", "phase"]
    executor: ErasureExecutor
    affected: int = 0


class ErasureRuleOutcome(BaseModel):
    """Rows one anonymisation or pseudonymisation rule rewrote (#1664).

    A collection can carry several rules (``plant_diary_entries`` has three user
    references), so the rule is identified by ``collection`` + ``user_field``.
    """

    phase: str
    collection: str
    user_field: str
    affected: int = 0


class ErasureExecutionReport(BaseModel):
    """What one run of the ArangoDB erasure executor did, step by step (#1664).

    ``steps`` follows the declared order of :attr:`ErasurePlan.steps` and holds
    only the steps this executor ran — a phase owned by another executor
    (object storage, reference index) appears in ``delegated`` instead, so a
    reader can tell "ran and found nothing" from "not this executor's slice".
    Carries no user key: it is logged, and the logs must not name the subject
    beyond what the calling path already logs.
    """

    steps: list[ErasureStepOutcome] = Field(default_factory=list)
    rules: list[ErasureRuleOutcome] = Field(default_factory=list)
    delegated: list[str] = Field(default_factory=list)
    #: Declared collections the database does not have. They hold no rows, so
    #: nothing is lost by skipping them; they are listed so the skip is visible.
    absent_collections: list[str] = Field(default_factory=list)

    def affected(self, collection: str) -> int:
        """Rows the step named *collection* reached (``0`` when it did not run)."""
        return sum(step.affected for step in self.steps if step.collection == collection)


class AccountErasureReport(BaseModel):
    """The full account-erasure run: pre-ArangoDB phases plus the executor (#1664).

    Returned by :meth:`PrivacyService.erase_account`, the one entry both
    account-deletion paths share. ``delegated_removed`` holds, per declared
    step, the rows an executor *other* than the ArangoDB one removed — today the
    REQ-010 pest-image cleanup (``pest_image_cleanup``), which drops the link
    documents itself because it must retract a promoted image's recognition
    embedding first. The executor's own pass over the same step is the safety
    net and normally finds nothing left.
    """

    storage_cleanup_scopes: list[str] = Field(default_factory=list)
    #: Phase 0 hard-delete outcome per record of the subject (#1770): objects
    #: deleted, and objects kept because a record outside this erasure — another
    #: member's upload of the same bytes — still holds them.
    storage_objects_removed: int = 0
    storage_objects_retained_shared: int = 0
    #: Objects Phase 0 kept for another member whose record went before the
    #: ArangoDB plan; released after the plan (#1770).
    storage_objects_released: int = 0
    reference_index_removed: int = 0
    #: The store Phase 0.5 ran against in *this* call (``"inference_service"`` /
    #: ``"noop"``); ``None`` when it did not run — no store wired, or a retry
    #: that skipped the pre-ArangoDB phases (#1753).
    reference_index_binding: str | None = None
    #: Contributed pest-recognition prototypes deleted, and the store that ran
    #: (``"inference_service"`` / ``"noop"``); ``None`` when the pest-image step
    #: did not run in this call (#1759).
    pest_prototypes_removed: int = 0
    pest_prototype_binding: str | None = None
    export_files_removed: int = 0
    delegated_removed: dict[str, int] = Field(default_factory=dict)
    #: The personal-tenant phase (#1788): one entry per personal tenant of the
    #: subject. ``None`` when the phase did not run — an erasure that skipped it
    #: must not be recorded ``completed``.
    personal_tenants: list[PersonalTenantErasure] | None = None
    arango: ErasureExecutionReport = Field(default_factory=ErasureExecutionReport)

    def affected(self, collection: str) -> int:
        """Rows every phase together removed from the declared step *collection*."""
        return self.arango.affected(collection) + self.delegated_removed.get(collection, 0)

    def unreached(self, declared: list[str]) -> list[str]:
        """The names of *declared* steps this run neither executed nor delegated (#1645).

        A step the executor ran appears in ``arango.steps`` (``affected`` may be
        ``0`` — "ran and found nothing" is a finished step); a non-ArangoDB phase
        appears in ``arango.delegated``. Anything else was not run, and an
        erasure that skipped a declared step must not be recorded ``completed``.
        """
        covered = {step.collection for step in self.arango.steps} | set(self.arango.delegated)
        return [name for name in declared if name not in covered]


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
