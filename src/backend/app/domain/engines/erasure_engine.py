"""Pure logic for REQ-025 erasure orchestration (Art. 17)."""

import hashlib

from app.domain.models.privacy import (
    AnonymizationRule,
    ErasureExecutor,
    ErasurePlan,
    ErasureStep,
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

    Pure-logic engine. No I/O. ``PrivacyService.erase_account`` executes the
    plan in declared order: storage cleanup -> edges -> documents ->
    anonymisation -> audit-log pseudonymisation -> user document. The ArangoDB
    part runs in ``ArangoErasureExecutor`` (#1664).
    """

    #: Names of the two ArangoDB phase steps in :attr:`DELETE_STEPS`. The
    #: executor recognises a phase by these names; the inventory spells them as
    #: literals because ``scripts/check_privacy_inventory.py`` reads it without
    #: importing it, and ``test_privacy_engines.py`` pins that both agree.
    ANONYMIZE_PHASE = "_anonymize_collections"
    PSEUDONYMIZE_AUDIT_PHASE = "_pseudonymize_audit_collections"

    # Collections whose user references must be retained — either for legal
    # compliance (CanG, PflSchG) or because the document belongs to a record of
    # a possibly shared tenant. The user reference is replaced with an anonymous
    # marker; the document itself survives. A collection may appear more than
    # once when it carries several user references (see ``plant_diary_entries``).
    #
    # The four retention rules key on the server-set ``*_by_key`` fields (#1669;
    # ``quality_assessments.assessed_by_key`` since #1663). Until then they
    # keyed on ``harvester`` / ``applied_by`` / ``inspector`` — free text typed
    # by the user — and were inert: a rule that matches "whatever was typed"
    # never finds the account being erased (measured on #1662, recorded on
    # #1663). Those rules are **replaced**, not kept beside these, so no reader
    # can mistake the old shape for a second path. Rows written before #1669
    # (#1663 for quality assessments) carry ``null`` in the key field and are
    # not reached by design — guessing an owner from the free text is exactly
    # the backfill the issue forbids.
    ANONYMIZE_COLLECTIONS: list[AnonymizationRule] = [
        AnonymizationRule(
            collection="harvest_batches",
            user_field="harvested_by_key",
            replacement_strategy="tombstone_hash",
            clear_fields=["harvester"],
            reason=(
                "CanG: 5-year retention for harvest documentation. The account key becomes a "
                "tombstone hash so the erased user's harvests stay linkable to each other for "
                "the audit; the free-text harvester name is cleared."
            ),
        ),
        AnonymizationRule(
            # #1663 — the assessment belongs to the harvest record (NFR-011
            # R-16 lists ``quality_assessments`` beside ``harvest_batches``).
            # ``yield_metrics`` is R-16 too but carries no user field at all
            # (``models/harvest.py::YieldMetric``), so it needs no rule.
            collection="quality_assessments",
            user_field="assessed_by_key",
            replacement_strategy="tombstone_hash",
            clear_fields=["assessed_by"],
            reason=(
                "NFR-011 R-16 / CanG: 5-year retention for harvest documentation, including the "
                "quality assessment. Key pseudonymised, free-text assessor name cleared."
            ),
        ),
        AnonymizationRule(
            # ``applied_by`` — NOT ``applicator``. The model
            # (``domain/models/ipm.py::TreatmentApplication``) has never carried
            # an ``applicator`` field, so an earlier rule addressed a field that
            # does not exist and would have left the real user reference in place.
            collection="treatment_applications",
            user_field="applied_by_key",
            replacement_strategy="tombstone_hash",
            clear_fields=["applied_by"],
            reason=(
                "PflSchG section 11: 3-year retention for treatment records. Key pseudonymised, "
                "free-text applicator name cleared."
            ),
        ),
        AnonymizationRule(
            # #1622 — ``tasks`` was declared personal data by the *export*
            # manifest (``assigned_to_user_key``) and appeared in no erasure
            # enumeration at all: neither the plan nor the executing cascade.
            # The task document belongs to the tenant's plan of work, which may
            # be a shared garden, so it is retained and the assignee reference
            # is removed — the same argument as ``plant_diary_entries`` below.
            collection="tasks",
            user_field="assigned_to_user_key",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-024: the task belongs to the work plan of a possibly shared tenant "
                "and is retained; only the assignee reference is removed."
            ),
        ),
        AnonymizationRule(
            collection="inspections",
            user_field="inspected_by_key",
            replacement_strategy="tombstone_hash",
            clear_fields=["inspector"],
            reason=(
                "PflSchG section 11: 3-year retention for inspection records. Key pseudonymised, "
                "free-text inspector name cleared."
            ),
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

    # ── The single declared inventory of a user's personal data in ArangoDB ──
    #
    # Before #1622 this was ``DELETE_ORDER``, a bare list of names that nothing
    # read, while :meth:`ArangoUserRepository.delete` hand-wrote its own eight
    # collections. Measured against each other the two enumerations differed by
    # 23 entries. Two lists that must agree and are never compared drift, and
    # these had: four collections the cascade removes (``api_keys``,
    # ``user_preferences``, ``onboarding_states``, ``memberships``) were named
    # in neither the plan nor the export manifest, so the documented inventory
    # understated what the system holds.
    #
    # There is now one list, and every entry says who removes it. Since #1664
    # every ArangoDB entry — whatever its attribution — is executed by
    # ``ArangoErasureExecutor`` whenever ``PrivacyService.erase_account`` runs,
    # which the platform-admin delete does. The attribution still carries one
    # distinction: ``retention_worker`` marks the entries the *scheduled
    # self-service* Art. 17 path (``PrivacyService._finalize_erasure``) does not
    # execute yet, because it does not call ``erase_account`` (#1645). That path
    # reads this slice as its own outstanding gap, so re-attributing an entry
    # away from ``retention_worker`` before #1645 wires the call would make it
    # report ``completed`` for an erasure that deleted nothing.
    #
    # Order is load-bearing: phases first, then edges, then documents, then the
    # user document, so no orphan edge survives its endpoint.
    DELETE_STEPS: list[ErasureStep] = [
        ErasureStep(collection="_storage_cleanup", kind="phase", executor="storage_cleanup"),
        ErasureStep(
            collection="_reference_index_cleanup",
            kind="phase",
            executor="reference_index_cleanup",
        ),
        # Every edge below that has no ``via`` runs ``users -> <document>``: the
        # graph definition in ``collections.py`` declares ``USERS`` as its only
        # ``from`` collection and each repository inserts it with the user id as
        # ``_from`` (e.g. ``data_export_repository.py`` ``create_edge(REQUESTED_EXPORT,
        # user_id, export_id)``). ``test_privacy_engines.py`` pins every endpoint
        # against the graph definition rather than trusting this comment.
        ErasureStep(collection="requested_export", kind="edge", executor="retention_worker", user_field="_from"),
        ErasureStep(collection="has_consent", kind="edge", executor="retention_worker", user_field="_from"),
        ErasureStep(collection="has_restriction", kind="edge", executor="retention_worker", user_field="_from"),
        ErasureStep(collection="requested_erasure", kind="edge", executor="retention_worker", user_field="_from"),
        ErasureStep(
            collection="requested_email_change",
            kind="edge",
            executor="retention_worker",
            user_field="_from",
        ),
        ErasureStep(
            # #1663 — written by ``FavoritesService`` (``_from`` = the user,
            # ``_to`` = species / nutrient plan / fertilizer) and named in no
            # erasure enumeration until now.
            collection="user_favorites",
            kind="edge",
            executor="retention_worker",
            user_field="_from",
        ),
        ErasureStep(collection="has_auth_provider", kind="edge", executor="account_cascade", user_field="_from"),
        ErasureStep(collection="has_session", kind="edge", executor="account_cascade", user_field="_from"),
        ErasureStep(
            # #1663 — ``api_key_repository.create`` writes this edge beside every
            # key; the cascade removed the ``api_keys`` documents and left the
            # edges pointing at nothing.
            collection="has_api_key",
            kind="edge",
            executor="account_cascade",
            user_field="_from",
        ),
        ErasureStep(
            # #1663 — ``users -> memberships``; ``delete_all_for_user`` has always
            # removed it, the inventory never named it.
            collection="has_membership",
            kind="edge",
            executor="membership_cascade",
            user_field="_from",
        ),
        ErasureStep(
            collection="membership_in",
            kind="edge",
            executor="membership_cascade",
            user_field="_from",
            via="memberships",
            note="memberships -> tenants; never touches users (membership_repository.create).",
        ),
        ErasureStep(collection="memberships", kind="document", executor="membership_cascade", user_field="user_key"),
        ErasureStep(
            collection="data_export_requests",
            kind="document",
            executor="retention_worker",
            user_field="user_key",
        ),
        ErasureStep(collection="consent_records", kind="document", executor="retention_worker", user_field="user_key"),
        ErasureStep(
            collection="processing_restrictions",
            kind="document",
            executor="retention_worker",
            user_field="user_key",
        ),
        ErasureStep(
            collection="email_change_requests",
            kind="document",
            executor="retention_worker",
            user_field="user_key",
        ),
        ErasureStep(collection="auth_providers", kind="document", executor="account_cascade", user_field="user_key"),
        ErasureStep(collection="refresh_tokens", kind="document", executor="account_cascade", user_field="user_key"),
        ErasureStep(collection="api_keys", kind="document", executor="account_cascade", user_field="user_key"),
        ErasureStep(collection="user_preferences", kind="document", executor="account_cascade", user_field="user_key"),
        ErasureStep(collection="onboarding_states", kind="document", executor="account_cascade", user_field="user_key"),
        ErasureStep(
            collection="identification_requests",
            kind="document",
            executor="retention_worker",
            user_field="user_key",
        ),
        # REQ-044 §8 — pest detections are deleted (no legal retention basis);
        # edges first, then the document. ``beneficials`` is global reference
        # data, not personal, and is intentionally left untouched. The three
        # edges start at the detection, not at the user, so they are reached
        # ``via`` the subject's ``pest_detections`` (pest_detection_repository.create).
        ErasureStep(
            collection="pest_detection_of",
            kind="edge",
            executor="retention_worker",
            user_field="_from",
            via="pest_detections",
        ),
        ErasureStep(
            collection="pest_detection_flagged",
            kind="edge",
            executor="retention_worker",
            user_field="_from",
            via="pest_detections",
        ),
        ErasureStep(
            collection="pest_detection_suggested_inspection",
            kind="edge",
            executor="retention_worker",
            user_field="_from",
            via="pest_detections",
        ),
        ErasureStep(collection="pest_detections", kind="document", executor="retention_worker", user_field="user_key"),
        # REQ-010 §8 — user-contributed pest reference images are deleted (no
        # legal retention basis). Their attachment bytes are hard-deleted by the
        # ``user_pest_reference_images`` storage-cleanup rule (Phase 0); this
        # removes the link documents. A *promoted* contribution is still deleted
        # on erasure — global visibility does not create a retention basis.
        ErasureStep(
            collection="pest_image_contributions",
            kind="document",
            executor="pest_image_cleanup",
            user_field="contributed_by",
            note="Not user_key: the model has none (pest_image_repository.list_for_user).",
        ),
        ErasureStep(
            collection="_anonymize_collections",
            kind="phase",
            executor="retention_worker",
        ),
        ErasureStep(
            collection="_pseudonymize_audit_collections",
            kind="phase",
            executor="retention_worker",
        ),
        ErasureStep(collection="users", kind="user", executor="account_cascade"),
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
            steps=list(self.DELETE_STEPS),
            delete=self.delete_order(),
            soft_delete_immediate=True,
            hard_delete_after_days=self.HARD_DELETE_AFTER_DAYS,
        )

    @classmethod
    def delete_order(cls) -> list[str]:
        """The bare name sequence of :attr:`DELETE_STEPS`, in declared order.

        Derived, never maintained: a reader that only needs the order (the
        ``ErasurePlan.delete`` field, the REQ-010 wiring test) gets it from the
        one inventory rather than from a second list beside it.
        """
        return [step.collection for step in cls.DELETE_STEPS]

    @classmethod
    def steps_for(cls, executor: ErasureExecutor) -> list[ErasureStep]:
        """The inventory entries *executor* is responsible for, in declared order.

        This is how an executing path obtains its collection names. It must not
        write them down again: a second copy is precisely the split #1622
        measured, and ``scripts/check_privacy_inventory.py`` refuses one.
        """
        return [step for step in cls.DELETE_STEPS if step.executor == executor]

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
