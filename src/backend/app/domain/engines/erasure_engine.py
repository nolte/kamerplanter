"""Pure logic for REQ-025 erasure orchestration (Art. 17)."""

import hashlib
import re

from app.domain.models.privacy import (
    AnonymizationRule,
    ErasureExclusion,
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

#: Prefix of the value an :class:`AnonymizationRule` writes into its
#: ``rename_fields`` (#1700): ``<prefix>`` + :meth:`ErasureEngine.anonymized_rename_value`.
#: The namespace is reserved — ``TenantEngine.generate_slug`` never produces a
#: slug inside it — so a registration cannot occupy the value first.
ANONYMIZED_KEY_PREFIX = "anonymized-"

#: The exact shape :meth:`ErasureEngine.compute_tombstone_hash` produces.
_TOMBSTONE_PATTERN = re.compile(r"anon_[0-9a-f]{16}")


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
        # ── #1700: user references that were in neither inventory ──────────
        # Each was found by R6 of ``scripts/check_privacy_inventory.py``, which
        # anchors on the model fields rather than on the two lists.
        AnonymizationRule(
            # ``tasks/tenant_router.py`` stamps ``created_by=ctx.user_key``. The
            # comment belongs to the task of a possibly shared tenant — the same
            # argument as ``tasks.assigned_to_user_key`` (NFR-011 R-22) and the
            # diary entry (REQ-050 section 7.4): text kept, author removed.
            collection="task_comments",
            user_field="created_by",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-024: a task comment belongs to the work plan of a possibly shared tenant "
                "and is retained; only the author reference is removed (as NFR-011 R-22 for tasks)."
            ),
        ),
        AnonymizationRule(
            # A pending invitation the subject sent is the tenant's, not theirs:
            # it stays valid for the invitee. Accepted invitations *to* the
            # subject are removed by the ``invitations`` delete step instead.
            collection="invitations",
            user_field="invited_by_user_key",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-024: an invitation belongs to the inviting tenant; NFR-011 R-12 governs its "
                "expiry. The inviter reference is removed, the invitation keeps working."
            ),
        ),
        AnonymizationRule(
            # REQ-010 promotion audit: the key of the *platform admin* who
            # released someone else's contribution. The contribution is its
            # contributor's and is deleted with *their* account, not the admin's.
            collection="pest_image_contributions",
            user_field="promoted_by",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-010: a promoted reference image belongs to its contributor; erasing the "
                "promoting admin removes the admin reference and keeps the promotion."
            ),
        ),
        AnonymizationRule(
            # Runs after the storage phase and after the ``pest_reference``
            # delete step: what is left are documentation photos of the tenant
            # (diary, ipm, harvest, task, plant — already anonymised by the
            # storage phase, a no-op here) plus the categories no storage scope
            # names (import, export, id_recognition, tenant_export). Same marker
            # as the storage phase (REQ-025 AK-OS-02).
            collection="attachments",
            user_field="created_by",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "NFR-013 section 6.2 / REQ-025 AK-OS-02: attachments of a tenant record are "
                "retained with the uploader reference replaced; bytes follow their own storage rule."
            ),
        ),
        AnonymizationRule(
            # REQ-031 section 7.5 prescribes exactly this: "user_key -> null,
            # hashes stay". The marker is the executor's null; the entry keeps
            # its question hash for the 30-day audit window.
            collection="ai_audit_log",
            user_field="user_key",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-031 section 7.5: AI audit entries are retained for their 30-day window "
                "(section 7.4) with the user reference removed; the hashes stay."
            ),
        ),
        AnonymizationRule(
            # ``imports/router.py`` stamps ``uploaded_by=ctx.user_key``. The
            # import job records what entered the tenant's master data.
            collection="import_jobs",
            user_field="uploaded_by",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-012: an import job documents what entered the tenant's data and is "
                "retained; only the uploader reference is removed."
            ),
        ),
        AnonymizationRule(
            # ``weather_source_service`` stamps ``updated_by=user_key`` on the
            # per-site configuration (1:1 per site, a tenant setting).
            collection="weather_source_configs",
            user_field="updated_by",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-046: the weather-source configuration belongs to the tenant's site and "
                "is retained; only the last-editor reference is removed."
            ),
        ),
        AnonymizationRule(
            # REQ-031 section 7.5. A tip card is the tenant's, not the member's:
            # ``AiAssistantService.dismiss_daily_tip`` hides it for the whole
            # tenant. Deleting the subject's dismissed rows (the first #1700
            # draft) re-showed the tip to every other member of a shared tenant;
            # only the dismisser reference goes, ``dismissed_at`` stays.
            collection="ai_tip_cache",
            user_field="dismissed_by",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-031 section 7.5: a dismissed tip stays dismissed for the tenant; only the "
                "reference to the member who dismissed it is removed."
            ),
        ),
        AnonymizationRule(
            # ``actuators/tenant_router.py`` stamps ``created_by=ctx.user_key``.
            collection="manual_overrides",
            user_field="created_by",
            anonymized_value=ANONYMIZED_MARKER,
            reason=(
                "REQ-018 / NFR-011 R-15: manual overrides are part of the tenant's actuator "
                "history and are retained; only the operator reference is removed."
            ),
        ),
        AnonymizationRule(
            # The personal tenant (``tenant_service.create_personal_tenant``)
            # carries the subject as owner and takes ``name``/``slug`` from the
            # display name. Deleting it would cascade into records a retention
            # obligation keeps (a harvest in it: CanG, NFR-011 R-16), so the
            # tenant is kept and stops naming anyone: owner replaced, name and
            # slug rewritten to ``anonymized_rename_value(tombstone, key)`` —
            # unique per row (``slug`` has a unique index) and derived from the
            # salted tombstone, so nobody can register it first. Until the
            # #1700 review it was ``anonymized-<key>``: Arango keys are
            # guessable, a display name "Anonymized <key>" took the slug, and
            # the erasure transaction aborted on the unique index on every
            # retry. An organisation tenant the subject founded keeps
            # its name — it is the group's, not the subject's — and loses only
            # the owner reference. ``owner_user_key`` confers no permission
            # (authority is the membership role, REQ-049), so there is nothing
            # to transfer.
            collection="tenants",
            user_field="owner_user_key",
            anonymized_value=ANONYMIZED_MARKER,
            rename_fields=["name", "slug"],
            rename_when={"tenant_type": "personal"},
            reason=(
                "REQ-024 / NFR-011 R-16: a tenant may hold records under a retention obligation, "
                "so it is retained; the owner reference is removed and a personal tenant's "
                "display-name-derived name and slug are replaced."
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
    # There is now one list, and every entry says who removes it. Every
    # ArangoDB entry — whatever its attribution — is executed by
    # ``ArangoErasureExecutor`` whenever ``PrivacyService.erase_account`` runs,
    # and both account-deletion paths run it: the platform-admin delete (#1664)
    # and the scheduled self-service Art. 17 erasure,
    # ``PrivacyService._finalize_erasure`` (#1645). The attribution says which
    # *further* reader a step has: ``account_cascade`` is also run by
    # ``ArangoUserRepository.delete`` (unverified-account cleanup),
    # ``pest_image_cleanup`` by the REQ-010 pest-image cleanup; ``account_erasure``
    # has no reader but ``erase_account``. See ``ErasureExecutor`` for the set.
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
        ErasureStep(collection="requested_export", kind="edge", executor="account_erasure", user_field="_from"),
        ErasureStep(collection="has_consent", kind="edge", executor="account_erasure", user_field="_from"),
        ErasureStep(collection="has_restriction", kind="edge", executor="account_erasure", user_field="_from"),
        ErasureStep(collection="requested_erasure", kind="edge", executor="account_erasure", user_field="_from"),
        ErasureStep(
            collection="requested_email_change",
            kind="edge",
            executor="account_erasure",
            user_field="_from",
        ),
        ErasureStep(
            # #1663 — written by ``FavoritesService`` (``_from`` = the user,
            # ``_to`` = species / nutrient plan / fertilizer) and named in no
            # erasure enumeration until now.
            collection="user_favorites",
            kind="edge",
            executor="account_erasure",
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
        # #1700 — the membership block is ``account_cascade``: registration
        # creates a membership (in the personal tenant) before the address is
        # verified, and the unverified-account cleanup left it, and every
        # location assignment hanging off it, behind a deleted user.
        ErasureStep(
            # #1663 — ``users -> memberships``; ``delete_all_for_user`` has always
            # removed it, the inventory never named it.
            collection="has_membership",
            kind="edge",
            executor="account_cascade",
            user_field="_from",
        ),
        # #1700 — REQ-024 assignment-based write control. An assignment carries
        # no account key, only ``membership_key`` (``models/location_assignment.py``),
        # so it is reached ``via`` the subject's memberships; its three edges
        # start at the assignment (``location_assignment_repository.create``).
        # Removing a membership one by one always removed its assignments
        # (``membership_repository.delete``); the bulk erasure did not.
        ErasureStep(
            collection="assigned_to_location",
            kind="edge",
            executor="account_cascade",
            user_field="_from",
            via="location_assignments",
        ),
        ErasureStep(
            collection="assignment_for",
            kind="edge",
            executor="account_cascade",
            user_field="_from",
            via="location_assignments",
        ),
        ErasureStep(
            collection="assignment_in_tenant",
            kind="edge",
            executor="account_cascade",
            user_field="_from",
            via="location_assignments",
        ),
        ErasureStep(
            collection="location_assignments",
            kind="document",
            executor="account_cascade",
            user_field="membership_key",
            via="memberships",
            note="No account key on the model; matched on the _key of the subject's memberships.",
        ),
        ErasureStep(
            collection="membership_in",
            kind="edge",
            executor="account_cascade",
            user_field="_from",
            via="memberships",
            note="memberships -> tenants; never touches users (membership_repository.create).",
        ),
        ErasureStep(collection="memberships", kind="document", executor="account_cascade", user_field="user_key"),
        ErasureStep(
            collection="data_export_requests",
            kind="document",
            executor="account_erasure",
            user_field="user_key",
        ),
        ErasureStep(collection="consent_records", kind="document", executor="account_erasure", user_field="user_key"),
        ErasureStep(
            collection="processing_restrictions",
            kind="document",
            executor="account_erasure",
            user_field="user_key",
        ),
        ErasureStep(
            collection="email_change_requests",
            kind="document",
            executor="account_erasure",
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
            executor="account_erasure",
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
            executor="account_erasure",
            user_field="_from",
            via="pest_detections",
        ),
        ErasureStep(
            collection="pest_detection_flagged",
            kind="edge",
            executor="account_erasure",
            user_field="_from",
            via="pest_detections",
        ),
        ErasureStep(
            collection="pest_detection_suggested_inspection",
            kind="edge",
            executor="account_erasure",
            user_field="_from",
            via="pest_detections",
        ),
        ErasureStep(collection="pest_detections", kind="document", executor="account_erasure", user_field="user_key"),
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
        # ── #1700: personal rows that were in neither inventory ──────────────
        # None of these carries a retention obligation in NFR-011; each is the
        # subject's own (inbox, settings, feeds, AI chats, CV requests).
        ErasureStep(
            # REQ-031 section 7.5: the erasure "cascades to all ai_conversations".
            collection="ai_conversations",
            kind="document",
            executor="account_erasure",
            user_field="user_key",
        ),
        ErasureStep(
            collection="notification_for_run",
            kind="edge",
            executor="account_erasure",
            user_field="_from",
            via="notifications",
        ),
        ErasureStep(collection="notifications", kind="document", executor="account_erasure", user_field="user_key"),
        ErasureStep(
            collection="notification_preferences",
            kind="document",
            executor="account_erasure",
            user_field="user_key",
        ),
        ErasureStep(
            # REQ-015: the feed row holds the token the iCal endpoint serves
            # (``calendar_feed_repository.get_by_token``); removing the row is
            # what makes the token stop serving.
            collection="calendar_feeds",
            kind="document",
            executor="account_erasure",
            user_field="user_key",
        ),
        # REQ-038 CV diagnosis requests: the subject's own analysis requests, the
        # same category as ``identification_requests``. The inspection a request
        # may be attached to is retained and anonymised by its own rule.
        ErasureStep(
            collection="cv_diagnosed_for",
            kind="edge",
            executor="account_erasure",
            user_field="_from",
            via="plant_diagnosis_requests",
        ),
        ErasureStep(
            collection="cv_diagnosis_found",
            kind="edge",
            executor="account_erasure",
            user_field="_from",
            via="plant_diagnosis_requests",
        ),
        ErasureStep(
            collection="cv_attached_to_inspection",
            kind="edge",
            executor="account_erasure",
            user_field="_from",
            via="plant_diagnosis_requests",
        ),
        ErasureStep(
            collection="cv_phenotype_of",
            kind="edge",
            executor="account_erasure",
            user_field="_from",
            via="plant_diagnosis_requests",
        ),
        ErasureStep(
            collection="plant_diagnosis_requests",
            kind="document",
            executor="account_erasure",
            user_field="user_key",
        ),
        # An invitation the subject *accepted* has served its purpose and names
        # the subject twice (``accepted_by_user_key`` and the ``email`` it was
        # sent to). The tenant -> invitation edge goes with it.
        ErasureStep(
            collection="has_invitation",
            kind="edge",
            executor="account_erasure",
            user_field="_to",
            via="invitations",
        ),
        ErasureStep(
            collection="invitations",
            kind="document",
            executor="account_erasure",
            user_field="accepted_by_user_key",
        ),
        ErasureStep(
            # The attachment documents whose bytes the storage phase hard-deleted
            # (``user_pest_reference_images``). Before #1700 the document stayed,
            # pointing at nothing and still naming the uploader.
            collection="attachments",
            kind="document",
            executor="account_erasure",
            user_field="created_by",
            where={"category": "pest_reference"},
        ),
        ErasureStep(
            # REQ-033 replay cache (TTL); keyed by the service account that called.
            collection="mcp_idempotency_record",
            kind="document",
            executor="account_erasure",
            user_field="service_account_key",
        ),
        ErasureStep(
            collection="_anonymize_collections",
            kind="phase",
            executor="account_erasure",
        ),
        ErasureStep(
            collection="_pseudonymize_audit_collections",
            kind="phase",
            executor="account_erasure",
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
        PseudonymizationRule(
            # #1700 — REQ-033: the MCP audit log is an audit record with its own
            # retention (``MCP_AUDIT_RETENTION_DAYS``); the calling service
            # account's key becomes the tombstone hash, like the erasure audit.
            collection="mcp_audit_log",
            user_field="service_account_key",
            replacement_strategy="tombstone_hash",
            reason=(
                "REQ-033 / NFR-011: MCP tool-call audit entries are retained for their audit "
                "window; the service-account key is pseudonymised so the entries stay linkable."
            ),
        ),
    ]

    # ── Stored user-reference fields the erasure deliberately leaves (#1700) ──
    #
    # ``scripts/check_privacy_inventory.py`` R6 requires every persisted model
    # field shaped like an account key to be reached above or named here with
    # the reason. Each reason below was measured against the write path.
    EXCLUDED_USER_REFERENCES: list[ErasureExclusion] = [
        ErasureExclusion(
            collection="watering_events",
            user_field="performed_by",
            reason=(
                "Free text typed by the caller (watering_events/schemas.py), never an account key; "
                "matching on it erases whatever was typed (the class #1663 measured)."
            ),
        ),
        ErasureExclusion(
            collection="watering_logs",
            user_field="performed_by",
            reason="Free text typed by the caller (watering_logs/schemas.py, e.g. 'Lisa'), never an account key.",
        ),
        ErasureExclusion(
            collection="maintenance_logs",
            user_field="performed_by",
            reason="Free text typed by the caller (tanks/schemas.py), never an account key.",
        ),
        ErasureExclusion(
            collection="tank_fill_events",
            user_field="performed_by",
            reason="Free text typed by the caller (tanks/schemas.py), never an account key.",
        ),
        ErasureExclusion(
            collection="workflow_templates",
            user_field="created_by",
            reason=(
                "Free text from the request body (tasks/schemas.py WorkflowTemplateCreate.created_by), "
                "never stamped from the caller's account."
            ),
        ),
        ErasureExclusion(
            collection="task_audit_entries",
            user_field="changed_by",
            reason=(
                "Written only by TaskService._record_audit, which no code path calls with an account "
                "key; every stored value is its default 'system'."
            ),
        ),
        ErasureExclusion(
            collection="sync_runs",
            user_field="triggered_by",
            reason="A SyncTrigger enum value (manual / scheduled), not a person.",
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

    def deleted_collection_names(self) -> list[str]:
        """Collections whose rows of the subject are removed outright, in declared order.

        The other half of the REQ-025 AK-08a confirmation beside
        :meth:`anonymized_collection_names`: the *document* and *user* steps of
        :attr:`DELETE_STEPS`. Edges are the graph's plumbing between those
        documents, not a category of data a user would recognise, and phases are
        not collections.
        """
        return [step.collection for step in self.DELETE_STEPS if step.kind in ("document", "user")]

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
    def is_tombstone(value: str) -> bool:
        """True when *value* has the exact shape of a :meth:`compute_tombstone_hash` result.

        The audit pseudonymisation writes this hash into ``erasure_requests.user_key``
        inside the same ArangoDB transaction that removes the user document, so an
        erasure request carrying one has had its ArangoDB plan committed. Running
        the plan again with the hash as the "user key" would match nothing but the
        audit rows themselves and rewrite them to a hash of the hash, breaking the
        linkability NFR-011 R-06 keeps the hash for.
        """
        return _TOMBSTONE_PATTERN.fullmatch(value) is not None

    @staticmethod
    def anonymized_rename_value(tombstone: str, row_key: str) -> str:
        """The value a ``rename_fields`` rule writes into row *row_key* (#1700).

        ``anonymized-`` + the first 16 hex chars of ``sha256(tombstone + ":" + row_key)``.
        ``ArangoErasureExecutor`` computes the same expression in AQL for every
        matched row; this is its specification and the tests' oracle.

        Why the erased **user's** tombstone and not ``compute_tombstone_hash`` of
        the tenant key: the tombstone is the only salted value the executor is
        handed — the salt itself never leaves ``PrivacyService`` — and it is
        already non-guessable without the salt, so a squatter cannot predict the
        slug. The row key is mixed in so two renamed rows of one subject never
        share a value under a unique index.

        Raises:
            ValueError: *tombstone* is not a tombstone hash — a rename keyed on
                anything guessable reopens the squatting hole.
        """
        if not ErasureEngine.is_tombstone(tombstone):
            msg = "a rename value must be derived from a tombstone hash"
            raise ValueError(msg)
        digest = hashlib.sha256(f"{tombstone}:{row_key}".encode()).hexdigest()
        return f"{ANONYMIZED_KEY_PREFIX}{digest[:16]}"

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
