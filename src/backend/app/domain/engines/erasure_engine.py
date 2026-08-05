"""Pure logic for REQ-025 erasure orchestration (Art. 17)."""

import hashlib

from app.domain.models.privacy import (
    AnonymizationRule,
    ErasurePlan,
    PseudonymizationRule,
    ReferenceIndexCleanupRule,
    StorageCleanupRule,
)

#: Marker written into a user reference that outlives the erased user. Mirrors
#: ``attachment_repository.ANONYMIZED_MARKER`` — the *same* value is required by
#: REQ-025 AK-OS-02 (attachments) and AK-DA-01 (diary entries), and the two must
#: not drift apart. Declared here rather than imported so the domain layer stays
#: free of a data-access import (NFR-001).
ANONYMIZED_MARKER = "_anonymized"


class ErasureEngine:
    """Defines the deletion order, anonymisation rules and storage-cleanup steps.

    Pure-logic engine. No I/O. The Celery task that executes the plan walks
    the steps in declared order: storage cleanup -> edges -> documents ->
    audit-log pseudonymisation -> user document.
    """

    # Collections whose user references must be retained — either for legal
    # compliance (CanG, PflSchG) or because the document belongs to a record of
    # a possibly shared tenant. The user reference is replaced with an anonymous
    # marker; the document itself survives. A collection may appear more than
    # once when it carries several user references (see ``plant_diary_entries``).
    ANONYMIZE_COLLECTIONS: list[AnonymizationRule] = [
        AnonymizationRule(
            collection="harvest_batches",
            user_field="harvester",
            anonymized_value="[deleted]",
            reason="CanG: 5-year retention for harvest documentation.",
        ),
        AnonymizationRule(
            # ``applied_by`` — NOT ``applicator``. The model
            # (``domain/models/ipm.py::TreatmentApplication``) has never carried
            # an ``applicator`` field, so this rule addressed a field that does
            # not exist and would have left the real user reference in place.
            collection="treatment_applications",
            user_field="applied_by",
            anonymized_value="[deleted]",
            reason="PflSchG section 11: 3-year retention for treatment records.",
        ),
        AnonymizationRule(
            collection="inspections",
            user_field="inspector",
            anonymized_value="[deleted]",
            reason="PflSchG section 11: 3-year retention for inspection records.",
        ),
        # REQ-050 §7.4 / REQ-025 AK-DA-01 — the diary entry document itself.
        # Until now only the *attachments* of a diary entry were anonymised
        # (storage scope ``user_diary_attachments`` below); the
        # ``plant_diary_entries`` document carried no rule at all, so the free
        # text of an erased user stayed attributable by name. The document is
        # kept — it belongs to the plant record of a possibly shared tenant —
        # and all three user references on it are replaced.
        AnonymizationRule(
            collection="plant_diary_entries",
            user_field="created_by",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-050 section 7.4: the diary entry belongs to the plant record of a "
                "possibly shared tenant and is retained; only the author reference is removed."
            ),
        ),
        AnonymizationRule(
            collection="plant_diary_entries",
            user_field="analysis_requested_by",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-050 section 7.3/7.4: who marked an entry for AI analysis is kept for "
                "traceability, but must not remain a personal identifier after erasure."
            ),
        ),
        AnonymizationRule(
            collection="plant_diary_entries",
            user_field="analysis_claimed_by",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-050 section 7.3/7.4: the claiming worker id may carry the user's "
                "device or account name and is anonymised together with the entry."
            ),
        ),
    ]

    # Object-storage cleanup rules (Phase 0). Must run before ArangoDB edge
    # deletion, because the cleanup uses attachments.created_by metadata to
    # locate user-owned files.
    STORAGE_CLEANUP_RULES: list[StorageCleanupRule] = [
        StorageCleanupRule(
            scope="user_personal",
            description=(
                "Hard-delete all attachments where created_by == user_key AND "
                "category in {'profile', 'user_notes'}. Examples: profile photo "
                "and personal notes without retention obligation."
            ),
            action="hard_delete",
            ref="NFR-013 section 6.2 item 2",
        ),
        StorageCleanupRule(
            scope="user_diary_attachments",
            description=(
                "Anonymise metadata for attachments where created_by == user_key "
                "AND category in {'diary', 'inspection', 'treatment', 'harvest'}. "
                "Files stay attached to the tenant record (potential retention via "
                "NFR-011 R-16/R-17/R-18). The created_by metadata becomes "
                "'_anonymized'. If STORAGE_KEEP_EXIF_<category>=true, EXIF data is "
                "additionally stripped from the file (NFR-013 section 4.2)."
            ),
            action="anonymize_metadata_and_strip_exif",
            ref="NFR-013 section 6.2 items 3+4 and 6.4",
        ),
        StorageCleanupRule(
            scope="user_pest_reference_images",
            description=(
                "Hard-delete all attachments where created_by == user_key AND "
                "category == 'pest_reference' (REQ-010 user-contributed pest "
                "reference images). Unlike documentation photos these carry no "
                "legal retention obligation, so the binary objects are removed "
                "outright. The matching pest_image_contributions link documents "
                "are removed by the ArangoDB pass (DELETE_ORDER below)."
            ),
            action="hard_delete",
            ref="REQ-010 Phase 2, REQ-025 section 3.1",
        ),
    ]

    # Reference-index cleanup rules (Phase 0.5). The DINOv2 reference index
    # (REQ-029-A species_embeddings) lives in pgvector, outside ArangoDB, so the
    # generic delete pipeline never reaches it. User-contributed embeddings
    # (source='user_contributed') carry the provenance fields contributed_by /
    # tenant_key and are removed here. Curated references (source !=
    # 'user_contributed') are not personal data and stay untouched. Must run
    # before Phase 1, like Phase 0.
    REFERENCE_INDEX_CLEANUP_RULES: list[ReferenceIndexCleanupRule] = [
        ReferenceIndexCleanupRule(
            store="pgvector",
            collection="species_embeddings",
            filter="source == 'user_contributed' AND contributed_by == user_key",
            action="hard_delete",
            ref="REQ-029-A section 5.1, REQ-034 section 5",
        ),
    ]

    # Deletion order. The list is informational — actual deletion is split
    # into edge-collections, document-collections and the user-collection step
    # by the executor. The order encodes the legal/architectural dependency:
    # delete edges and child documents before the user document so that no
    # orphan edges remain.
    DELETE_ORDER: list[str] = [
        "_storage_cleanup",
        "_reference_index_cleanup",
        "requested_export",
        "has_consent",
        "has_restriction",
        "requested_erasure",
        "requested_email_change",
        "has_auth_provider",
        "has_session",
        "membership_in",
        "data_export_requests",
        "consent_records",
        "processing_restrictions",
        "email_change_requests",
        "auth_providers",
        "refresh_tokens",
        "identification_requests",
        # REQ-044 §8 — pest detections are deleted (no legal retention basis);
        # edges first, then the document. ``beneficials`` is global reference
        # data, not personal, and is intentionally left untouched.
        "pest_detection_of",
        "pest_detection_flagged",
        "pest_detection_suggested_inspection",
        "pest_detections",
        # REQ-010 §8 — user-contributed pest reference images are deleted (no
        # legal retention basis). Their attachment bytes are hard-deleted by the
        # ``user_pest_reference_images`` storage-cleanup rule (Phase 0); this
        # removes the link documents. A *promoted* contribution is still deleted
        # on erasure — global visibility does not create a retention basis.
        "pest_image_contributions",
        "_pseudonymize_audit_collections",
        "users",
    ]

    # Audit-log pseudonymisation (W-002). NFR-011 R-06 requires the erasure
    # audit log to be retained for one year. After hard-delete the user_key
    # must no longer be a personal identifier, so it is replaced with a
    # one-way hash before the user document itself is deleted.
    PSEUDONYMIZE_AUDIT_COLLECTIONS: list[PseudonymizationRule] = [
        PseudonymizationRule(
            collection="erasure_requests",
            user_field="user_key",
            replacement_strategy="tombstone_hash",
            reason=(
                "Erasure audit logs are retained for 1 year (NFR-011 R-06, "
                "Art. 5(2) accountability principle). After hard-delete the "
                "user_key must no longer be stored as a personal identifier "
                "(Art. 5(1)(e) storage limitation)."
            ),
        ),
    ]

    HARD_DELETE_AFTER_DAYS: int = 90

    def build_erasure_plan(self, user_key: str) -> ErasurePlan:
        """Build a deterministic erasure plan for the given user.

        Returned plan is a snapshot of the engine constants — the executor
        walks each list in order and performs the corresponding I/O.
        """
        return ErasurePlan(
            user_key=user_key,
            storage_cleanup=list(self.STORAGE_CLEANUP_RULES),
            reference_index_cleanup=list(self.REFERENCE_INDEX_CLEANUP_RULES),
            anonymize=list(self.ANONYMIZE_COLLECTIONS),
            pseudonymize_audit=list(self.PSEUDONYMIZE_AUDIT_COLLECTIONS),
            delete=list(self.DELETE_ORDER),
            soft_delete_immediate=True,
            hard_delete_after_days=self.HARD_DELETE_AFTER_DAYS,
        )

    def anonymized_collection_names(self) -> list[str]:
        """Collection names touched by :attr:`ANONYMIZE_COLLECTIONS`, each once.

        The erasure confirmation shown to the user (REQ-025 AK-08a) lists
        *categories*, not rules. Since REQ-050 a single collection can carry
        several rules (``plant_diary_entries`` has three user references), so a
        plain ``[rule.collection for rule in ...]`` would repeat the same name
        three times in that list. Order follows the rule declaration.
        """
        names: list[str] = []
        for rule in self.ANONYMIZE_COLLECTIONS:
            if rule.collection not in names:
                names.append(rule.collection)
        return names

    @staticmethod
    def compute_tombstone_hash(user_key: str, salt: str) -> str:
        """Produce a non-reversible tombstone hash for a deleted user_key.

        Format: 'anon_' + first 16 hex chars of sha256(user_key + salt).

        Properties:
          - Deterministic (same inputs -> same hash) so audit-log records
            for the same erased user remain linkable.
          - One-way (sha256 cannot be inverted).
          - Salt-isolated: without the per-instance salt no brute-force
            re-identification against the user-key space is feasible.

        Raises:
          ValueError: if salt is empty or shorter than 32 characters
            (NFR-011 minimum entropy requirement).
        """
        if not salt or len(salt) < 32:
            msg = "ERASURE_TOMBSTONE_SALT must be at least 32 characters (see NFR-011 section 4)."
            raise ValueError(msg)
        digest = hashlib.sha256((user_key + salt).encode("utf-8")).hexdigest()
        return f"anon_{digest[:16]}"
