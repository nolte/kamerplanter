"""Pure logic for REQ-025 erasure orchestration (Art. 17)."""

import hashlib

from app.domain.models.privacy import (
    AnonymizationRule,
    ErasurePlan,
    PseudonymizationRule,
    StorageCleanupRule,
)


class ErasureEngine:
    """Defines the deletion order, anonymisation rules and storage-cleanup steps.

    Pure-logic engine. No I/O. The Celery task that executes the plan walks
    the steps in declared order: storage cleanup -> edges -> documents ->
    audit-log pseudonymisation -> user document.
    """

    # Collections whose user references must be retained for legal compliance
    # (CanG, PflSchG). The user reference is replaced with an anonymous marker.
    ANONYMIZE_COLLECTIONS: list[AnonymizationRule] = [
        AnonymizationRule(
            collection="harvest_batches",
            user_field="harvester",
            anonymized_value="[deleted]",
            reason="CanG: 5-year retention for harvest documentation.",
        ),
        AnonymizationRule(
            collection="treatment_applications",
            user_field="applicator",
            anonymized_value="[deleted]",
            reason="PflSchG section 11: 3-year retention for treatment records.",
        ),
        AnonymizationRule(
            collection="inspections",
            user_field="inspector",
            anonymized_value="[deleted]",
            reason="PflSchG section 11: 3-year retention for inspection records.",
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
    ]

    # Deletion order. The list is informational — actual deletion is split
    # into edge-collections, document-collections and the user-collection step
    # by the executor. The order encodes the legal/architectural dependency:
    # delete edges and child documents before the user document so that no
    # orphan edges remain.
    DELETE_ORDER: list[str] = [
        "_storage_cleanup",
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
            anonymize=list(self.ANONYMIZE_COLLECTIONS),
            pseudonymize_audit=list(self.PSEUDONYMIZE_AUDIT_COLLECTIONS),
            delete=list(self.DELETE_ORDER),
            soft_delete_immediate=True,
            hard_delete_after_days=self.HARD_DELETE_AFTER_DAYS,
        )

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
