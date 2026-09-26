"""Pure logic for REQ-025 data exports (Art. 15 / 20)."""

from datetime import datetime
from typing import Any

from app.domain.engines.storage.export_bundle_key import export_bundle_key
from app.domain.models.privacy import DataExportRequest, DataSourceDefinition, DisclosureExclusion

#: Why the three legally-retained categories are only *partly* disclosable.
#: Since #1669 every create path stores the caller's account in
#: ``harvest_batches.harvested_by_key``, ``inspections.inspected_by_key`` and
#: ``treatment_applications.applied_by_key``, and the walk keys on those. Rows
#: written before that field existed carry ``null`` there (stamped by v0056):
#: their only attribution is the free text (``harvester`` etc. — a typed-in
#: name, or ``mcp:<account>``), which is deliberately **not** used to guess an
#: owner. Those rows can never be matched to a subject, so the bundle says so
#: beside the rows it does deliver rather than presenting the section as
#: complete. (Before #1669 the whole category carried a ``disclosure_gap``.)
_LEGACY_ATTRIBUTION_GAP = (
    "Records of this kind created before the system started storing the acting "
    "account (migration v0056) carry only a free-text name and are not attributed "
    "to any account. Such records cannot be matched to you and are not "
    "included here, even if the free text names you. They are retained under CanG / "
    "PflSchG; the free-text reference is cleared on erasure only for records that "
    "carry your account."
)


#: The same statement for ``quality_assessments``, whose account key arrived
#: one migration later (#1663, v0057).
_LEGACY_QUALITY_ATTRIBUTION_GAP = _LEGACY_ATTRIBUTION_GAP.replace("migration v0056", "migration v0057")


class DataExportEngine:
    """Defines the manifest of all user-related data sources for export.

    Pure-logic engine. No I/O. The actual data collection runs in a Celery task
    that walks this manifest and queries ArangoDB.
    """

    USER_DATA_MANIFEST: list[DataSourceDefinition] = [
        DataSourceDefinition(
            collection="users",
            filter_field="_key",
            label="Profile",
            fields=[
                "email",
                "display_name",
                "avatar_url",
                "locale",
                "timezone",
                "email_verified",
                "is_active",
                "created_at",
                "last_login_at",
            ],
        ),
        DataSourceDefinition(
            collection="auth_providers",
            edge_collection="has_auth_provider",
            label="Linked authentication providers",
            fields=["provider", "provider_email", "linked_at", "last_used_at"],
        ),
        DataSourceDefinition(
            collection="refresh_tokens",
            edge_collection="has_session",
            label="Active sessions",
            fields=["user_agent", "ip_address", "created_at", "expires_at"],
        ),
        DataSourceDefinition(
            collection="memberships",
            # #1645 - this declared ``edge_collection="membership_in"``, an edge
            # the named graph runs ``memberships -> tenants``: it never touches
            # ``users``, so the declared route reached no document and the
            # Art. 15 disclosure of a user's tenant memberships was empty
            # without anything saying so. A membership carries ``user_key``
            # directly (``ArangoMembershipRepository.list_by_user``), which is
            # the route that exists.
            filter_field="user_key",
            label="Tenant memberships",
            fields=["tenant_key", "role", "joined_at", "is_active"],
        ),
        DataSourceDefinition(
            collection="consent_records",
            edge_collection="has_consent",
            label="Consents",
            fields=["purpose", "granted", "granted_at", "revoked_at"],
        ),
        DataSourceDefinition(
            collection="processing_restrictions",
            edge_collection="has_restriction",
            label="Processing restrictions",
            fields=["scope", "reason", "created_at", "lifted_at", "notes"],
        ),
        DataSourceDefinition(
            collection="erasure_requests",
            edge_collection="requested_erasure",
            label="Erasure requests",
            fields=[
                "status",
                "requested_at",
                "soft_deleted_at",
                "hard_delete_scheduled_at",
                "completed_at",
            ],
        ),
        DataSourceDefinition(
            collection="email_change_requests",
            edge_collection="requested_email_change",
            label="Email-change requests",
            fields=[
                "new_email",
                "status",
                "requested_at",
                "expires_at",
                "confirmed_at",
                "previous_email",
                "revert_expires_at",
                "reverted_at",
            ],
        ),
        DataSourceDefinition(
            collection="data_export_requests",
            edge_collection="requested_export",
            label="Data-export requests",
            fields=[
                "status",
                "requested_at",
                "completed_at",
                "expires_at",
                "file_size_bytes",
                "download_count",
            ],
        ),
        # Tenant-scoped user-attributable resources (filter by user_key fields).
        #
        # **Every name below must exist on the corresponding domain model.** A
        # field name that does not is invisible in operation: the export simply
        # carries an empty value, which reads exactly like "the user has no data
        # here". ``tests/unit/domain/engines/test_privacy_engines.py``
        # (``test_every_manifest_field_exists_on_its_model``) checks the whole
        # manifest against the models for that reason.
        DataSourceDefinition(
            collection="tasks",
            tenant_scoped=True,
            # ``assigned_to_user_key`` — the model has never had ``assigned_to``,
            # so this source used to match no document at all.
            filter_field="assigned_to_user_key",
            label="Assigned tasks",
            # ``name`` — the Task model has no ``title``.
            fields=["name", "status", "due_date", "completed_at", "completion_notes"],
        ),
        DataSourceDefinition(
            collection="harvest_batches",
            tenant_scoped=True,
            # #1669 — server-set on every create path (REST + MCP); ``harvester``
            # is the display name and never a key. Pre-#1669 rows carry ``null``.
            filter_field="harvested_by_key",
            attribution_gap=_LEGACY_ATTRIBUTION_GAP,
            label="Harvest records",
            # Previously ["name", "status", "started_at", "completed_at"] — not
            # one of those four exists on HarvestBatch.
            fields=[
                "batch_id",
                "plant_key",
                "harvest_type",
                "harvest_date",
                "quality_grade",
                "notes",
                "created_at",
            ],
        ),
        DataSourceDefinition(
            collection="quality_assessments",
            # #1663 — server-set on the one create path (REST); ``assessed_by``
            # is the display name. Pre-#1663 rows carry ``null`` (v0057).
            #
            # Not ``tenant_scoped``: the model carries no ``tenant_key`` (the
            # assessment hangs off its harvest batch), so a tenant clause would
            # match nothing. The clause exists against *planting* a foreign key
            # into a user-editable field (#1662 SCR-001); ``assessed_by_key`` is
            # never read from a body and no route updates an assessment, so
            # the value is always the account that created the row.
            filter_field="assessed_by_key",
            attribution_gap=_LEGACY_QUALITY_ATTRIBUTION_GAP,
            label="Harvest quality assessments",
            fields=[
                "batch_key",
                "assessed_at",
                "appearance_score",
                "aroma_score",
                "color_score",
                "defects",
                "overall_score",
                "grade",
                "notes",
            ],
        ),
        DataSourceDefinition(
            collection="inspections",
            tenant_scoped=True,
            # #1669 — server-set on every create path (REST, MCP, the
            # pest-detection and CV-diagnosis bridges); ``inspector`` is the
            # display name. Pre-#1669 rows carry ``null``.
            filter_field="inspected_by_key",
            attribution_gap=_LEGACY_ATTRIBUTION_GAP,
            label="Inspection records",
            # ``inspected_at`` (not ``performed_at``); the "findings" of an
            # inspection are ``symptoms_observed`` + the detected keys.
            fields=[
                "plant_key",
                "inspected_at",
                "symptoms_observed",
                "detected_pest_keys",
                "detected_disease_keys",
                "notes",
            ],
        ),
        DataSourceDefinition(
            collection="treatment_applications",
            tenant_scoped=True,
            # #1669 — server-set on the one create path (REST); ``applied_by``
            # is the display name (the model never had ``applicator``).
            # Pre-#1669 rows carry ``null``.
            filter_field="applied_by_key",
            attribution_gap=_LEGACY_ATTRIBUTION_GAP,
            label="Treatment applications",
            # ``dosage`` (not ``dose``).
            fields=["treatment_key", "plant_key", "applied_at", "dosage", "notes"],
        ),
        DataSourceDefinition(
            collection="plant_diary_entries",
            tenant_scoped=True,
            filter_field="created_by",
            label="Plant diary entries",
            # ``text``/``created_at`` (not ``body``/``logged_at``): the export
            # used to deliver a diary entry with an empty text and no date.
            # ``analysis`` carries the REQ-050 AI result, which is part of the
            # entry and therefore part of the Art. 15 disclosure (AK-24).
            fields=[
                "plant_key",
                "entry_type",
                "title",
                "text",
                "tags",
                "measurements",
                "photo_refs",
                "created_at",
                "analysis_state",
                "analysis",
            ],
        ),
        DataSourceDefinition(
            collection="identification_requests",
            tenant_scoped=True,
            filter_field="user_key",
            label="Plant identification requests",
            # image_hash is an internal dedup/audit value, not user-facing data.
            fields=[
                "adapter_key",
                "image_organ",
                "status",
                "results",
                "selected_result_rank",
                "created_at",
            ],
        ),
        # ── #1700: categories the erasure inventory now reaches ──────────────
        # Every collection #1700 added to the erasure inventory is disclosed
        # here too. Each ``filter_field`` below is stamped server-side from the
        # caller's account, never read from a request body, so the sources are
        # not ``tenant_scoped`` (the argument ``quality_assessments`` makes):
        # nobody can plant a row into another subject's disclosure through them,
        # and a tenant the subject has left still discloses what they wrote there.
        DataSourceDefinition(
            collection="ai_conversations",
            filter_field="user_key",
            label="AI assistant conversations",
            fields=["tenant_key", "title", "context_type", "language", "messages", "created_at", "expires_at"],
        ),
        DataSourceDefinition(
            collection="ai_tip_cache",
            filter_field="dismissed_by",
            label="AI tips you dismissed",
            fields=["tenant_key", "title", "dismissed_at", "acted_on_at"],
        ),
        DataSourceDefinition(
            # REQ-031 section 7.6: hashed, without question/answer plain text.
            collection="ai_audit_log",
            filter_field="user_key",
            label="AI assistant audit entries",
            fields=["tenant_key", "endpoint", "question_hash", "model_name", "provider_type", "status"],
        ),
        DataSourceDefinition(
            collection="notifications",
            filter_field="user_key",
            label="Notifications",
            fields=["tenant_key", "notification_type", "title", "body", "status", "read_at", "created_at"],
        ),
        DataSourceDefinition(
            collection="notification_preferences",
            filter_field="user_key",
            label="Notification preferences",
            fields=["channels", "quiet_hours", "batching", "escalation", "type_overrides", "daily_summary"],
        ),
        DataSourceDefinition(
            # ``token`` is deliberately not exported: it is a live credential.
            collection="calendar_feeds",
            filter_field="user_key",
            label="Calendar feeds",
            fields=["tenant_key", "name", "filters", "is_active", "expires_at", "created_at"],
        ),
        DataSourceDefinition(
            collection="plant_diagnosis_requests",
            filter_field="user_key",
            label="Plant diagnosis requests",
            # #1719 — ``inspection_key``, ``harvest_observation_key`` and
            # ``confirmed_labels`` are what the three ``cv_*`` edges below
            # mirror; they are disclosed here so the edges need not be.
            fields=[
                "tenant_key",
                "plant_instance_key",
                "planting_run_key",
                "inspection_key",
                "harvest_observation_key",
                "classifications",
                "phenotype",
                "confirmed_labels",
                "adapter_key",
                "created_at",
            ],
        ),
        DataSourceDefinition(
            collection="task_comments",
            filter_field="created_by",
            label="Task comments",
            fields=["task_key", "comment_text", "created_at"],
        ),
        DataSourceDefinition(
            collection="invitations",
            filter_field="invited_by_user_key",
            label="Invitations you sent",
            fields=["tenant_key", "invitation_type", "email", "role", "status", "expires_at", "created_at"],
        ),
        DataSourceDefinition(
            collection="invitations",
            filter_field="accepted_by_user_key",
            label="Invitations you accepted",
            fields=["tenant_key", "email", "role", "accepted_at"],
        ),
        DataSourceDefinition(
            collection="location_assignments",
            label="Location assignments",
            fields=["tenant_key", "location_key", "can_edit", "notes"],
            # The one #1700 category the walk cannot reach: an assignment carries
            # the membership key, not the account key, and the walk follows a
            # field or a single edge from ``users`` (two hops would be needed).
            disclosure_gap=(
                "Location assignments reference your tenant membership, not your account, and are "
                "not collected per person. Your memberships are listed above; a tenant lead can show "
                "you the locations assigned to them."
            ),
        ),
        DataSourceDefinition(
            collection="attachments",
            filter_field="created_by",
            label="Uploaded files (metadata)",
            fields=["tenant_key", "category", "original_filename", "mime_type", "byte_size", "caption", "taken_on"],
        ),
        DataSourceDefinition(
            collection="pest_image_contributions",
            filter_field="contributed_by",
            label="Pest reference images you contributed",
            fields=["tenant_key", "pest_key", "caption", "status", "created_at"],
        ),
        DataSourceDefinition(
            collection="pest_image_contributions",
            filter_field="promoted_by",
            label="Pest reference images you promoted",
            fields=["pest_key", "status", "promoted_at"],
        ),
        DataSourceDefinition(
            collection="import_jobs",
            filter_field="uploaded_by",
            label="Imports",
            fields=["tenant_key", "entity_type", "status", "filename", "row_count", "created_at"],
        ),
        DataSourceDefinition(
            collection="weather_source_configs",
            filter_field="updated_by",
            label="Weather-source settings you changed",
            fields=["tenant_key", "site_key", "enabled", "updated_at"],
        ),
        DataSourceDefinition(
            collection="manual_overrides",
            filter_field="created_by",
            label="Manual actuator overrides",
            fields=["tenant_key", "actuator_key", "started_at", "expires_at", "reason", "created_at"],
        ),
        DataSourceDefinition(
            collection="tenants",
            filter_field="owner_user_key",
            label="Tenants you own",
            fields=["name", "slug", "tenant_type", "created_at"],
        ),
        DataSourceDefinition(
            collection="mcp_audit_log",
            filter_field="service_account_key",
            label="MCP tool calls (service accounts)",
            fields=["tenant_key", "tool_name", "status", "created_at"],
        ),
        DataSourceDefinition(
            collection="mcp_idempotency_record",
            filter_field="service_account_key",
            label="MCP idempotency records (service accounts)",
            fields=["tenant_key", "tool_name", "created_at", "expires_at"],
        ),
        # ── #1719: erased as the subject's data, and until now not disclosed ──
        # Found by the reverse direction of R2 in
        # ``scripts/check_privacy_inventory.py``: each collection below is
        # deleted by ``ErasureEngine.DELETE_STEPS`` because it is the subject's,
        # which is the proof that Art. 15 has to show it. Every ``filter_field``
        # is stamped from the caller's account, never read from a body, so none
        # is ``tenant_scoped``.
        DataSourceDefinition(
            # REQ-020: the edge row is the data (``_from`` = the subject,
            # ``_to`` = the catalogue entry, when and how it was marked), not the
            # catalogue entry at its other end — that is global or tenant data.
            collection="user_favorites",
            filter_field="_from",
            label="Favourites",
            fields=["_to", "target_type", "source", "cascade_from_key", "favorited_at"],
        ),
        DataSourceDefinition(
            # ``key_hash`` is deliberately not exported: it is the stored form of
            # a live credential (the ``calendar_feeds.token`` argument).
            collection="api_keys",
            filter_field="user_key",
            label="API keys (without the secret)",
            fields=[
                "label",
                "key_prefix",
                "tenant_scope",
                "ip_allowlist",
                "rate_limit_per_minute",
                "revoked",
                "last_used_at",
                "expires_at",
                "created_at",
            ],
        ),
        DataSourceDefinition(
            collection="user_preferences",
            filter_field="user_key",
            label="Personal settings",
            fields=[
                "experience_level",
                "onboarding_completed",
                "locale",
                "theme",
                "temperature_unit",
                "watering_can_liters",
                "smart_home_enabled",
                "kiosk_enabled",
                "high_contrast",
                "module_visibility",
                "dashboard_layout",
                "created_at",
                "updated_at",
            ],
        ),
        DataSourceDefinition(
            collection="onboarding_states",
            filter_field="user_key",
            label="Onboarding wizard progress",
            fields=[
                "completed",
                "skipped",
                "completed_at",
                "selected_kit_id",
                "selected_experience_level",
                "wizard_step",
                "created_entities",
                "site_name",
                "site_type",
                "selected_site_key",
                "plant_count",
                "plant_configs",
                "favorite_species_keys",
                "favorite_nutrient_plan_keys",
                "created_at",
            ],
        ),
        DataSourceDefinition(
            # REQ-044 section 8: the subject's own detection requests (no image
            # is stored). ``image_hash`` is an internal dedup value, as for
            # ``identification_requests``, and not exported.
            collection="pest_detections",
            filter_field="user_key",
            label="Pest detection requests",
            fields=[
                "tenant_key",
                "plant_instance_key",
                "planting_run_key",
                "source",
                "adapter_key",
                "trigger",
                "capture_device",
                "findings",
                "suggested_next_step",
                "llm_explanation",
                "feedback",
                "created_at",
            ],
        ),
    ]

    #: Collections the erasure inventory removes that the bundle deliberately
    #: does not carry as sections of their own (#1719). The rule is R2's reverse
    #: direction in ``scripts/check_privacy_inventory.py``: an erasure target is
    #: disclosed unless it is named here, with the reason, measured against its
    #: write path. Every entry is a graph edge whose endpoints are disclosed
    #: documents and whose attributes, where it has any, are a copy of a field a
    #: disclosed source already delivers — the edge adds nothing the subject
    #: does not already receive. An edge that carries information of its own
    #: (``user_favorites``) is a manifest source instead.
    EXCLUDED_FROM_DISCLOSURE: list[DisclosureExclusion] = [
        DisclosureExclusion(
            collection="has_api_key",
            reason=(
                "users -> api_keys, no attributes (api_key_repository.create); the api_keys rows are "
                "disclosed by user_key."
            ),
        ),
        DisclosureExclusion(
            collection="has_membership",
            reason=(
                "users -> memberships, no attributes (membership_repository.create); the memberships are "
                "disclosed by user_key."
            ),
        ),
        DisclosureExclusion(
            collection="membership_in",
            reason=(
                "memberships -> tenants, no attributes; the tenant of each disclosed membership is its tenant_key."
            ),
        ),
        DisclosureExclusion(
            collection="assigned_to_location",
            reason=(
                "location_assignments -> locations, no attributes (location_assignment_repository.create); "
                "the assignment's location_key is its own field, and the category is named in the bundle "
                "with its disclosure_gap."
            ),
        ),
        DisclosureExclusion(
            collection="assignment_for",
            reason=(
                "location_assignments -> memberships, no attributes; the membership is disclosed, the "
                "assignment category is named with its disclosure_gap."
            ),
        ),
        DisclosureExclusion(
            collection="assignment_in_tenant",
            reason=(
                "location_assignments -> tenants, no attributes; the assignment's tenant_key is its own "
                "field, the category is named with its disclosure_gap."
            ),
        ),
        DisclosureExclusion(
            collection="pest_detection_of",
            reason=(
                "pest_detections -> plant_instances / planting_runs, no attributes; mirrors the disclosed "
                "plant_instance_key / planting_run_key of the detection."
            ),
        ),
        DisclosureExclusion(
            collection="pest_detection_flagged",
            reason=(
                "pest_detections -> pests; confidence / mode / confirmed copy the disclosed findings and "
                "feedback of the detection (pest_detection_repository.create / add_feedback)."
            ),
        ),
        DisclosureExclusion(
            collection="pest_detection_suggested_inspection",
            reason=(
                "pest_detections -> inspections, no attributes (link_suggested_inspection); the inspection "
                "is disclosed by inspected_by_key, which the detection bridge stamps from the caller."
            ),
        ),
        DisclosureExclusion(
            collection="notification_for_run",
            reason=(
                "notifications -> planting_runs; declared in the graph, but no code path under app/ writes "
                "it (measured 2026-09-24). The notifications themselves are disclosed by user_key."
            ),
        ),
        DisclosureExclusion(
            collection="cv_diagnosed_for",
            reason=(
                "plant_diagnosis_requests -> plant_instances / planting_runs, no attributes; mirrors the "
                "disclosed plant_instance_key / planting_run_key of the request."
            ),
        ),
        DisclosureExclusion(
            collection="cv_diagnosis_found",
            reason=(
                "plant_diagnosis_requests -> diseases / pests; confidence / rank / category / confirmed copy "
                "the disclosed classifications and confirmed_labels (plant_diagnosis_repository.create)."
            ),
        ),
        DisclosureExclusion(
            collection="cv_attached_to_inspection",
            reason=(
                "plant_diagnosis_requests -> inspections, no attributes; mirrors the disclosed inspection_key "
                "of the request (plant_diagnosis_repository.mark_confirmed)."
            ),
        ),
        DisclosureExclusion(
            collection="cv_phenotype_of",
            reason=(
                "plant_diagnosis_requests -> harvest_observations, no attributes; mirrors the disclosed "
                "harvest_observation_key of the request."
            ),
        ),
        DisclosureExclusion(
            collection="has_invitation",
            reason=(
                "tenants -> invitations, no attributes (invitation_repository.create); the invitations are "
                "disclosed by invited_by_user_key and accepted_by_user_key."
            ),
        ),
    ]

    #: Bumped when the bundle's shape changes, so a downloaded file stays
    #: interpretable without guessing which version produced it (Art. 20
    #: portability: the recipient is not necessarily this system).
    BUNDLE_FORMAT_VERSION = "1.1"

    def build_export_manifest(self, user_key: str) -> list[DataSourceDefinition]:
        """Return the full export manifest for the given user."""
        return list(self.USER_DATA_MANIFEST)

    def build_bundle(
        self,
        user_key: str,
        generated_at: datetime,
        sections: list[tuple[DataSourceDefinition, list[dict[str, Any]]]],
        *,
        controller_name: str,
        controller_email: str,
    ) -> dict[str, Any]:
        """Assemble the Art. 15 disclosure document from collected rows.

        A section is kept even when it is empty: Art. 15(1) is a right to know
        *which* categories are processed, and a silently omitted category is
        indistinguishable from one the walk never reached. ``record_count``
        makes that explicit for a reader who is not counting array entries. A
        source with a ``disclosure_gap`` appears with ``disclosed: false`` and
        the reason, so the reader learns *why* rather than seeing an empty list.
        A source with an ``attribution_gap`` is disclosed, and the section says
        which of its rows can never be in it (#1669: pre-attribution rows).
        """
        return {
            "format_version": self.BUNDLE_FORMAT_VERSION,
            "generated_at": generated_at.isoformat(),
            "user_key": user_key,
            "data_controller": {"name": controller_name, "contact_email": controller_email},
            "legal_basis": "GDPR Art. 15 (right of access) and Art. 20 (data portability).",
            "sections": [
                {
                    "collection": source.collection,
                    "label": source.label,
                    "fields": list(source.fields),
                    "disclosed": source.disclosure_gap is None,
                    "not_disclosed_reason": source.disclosure_gap,
                    "attribution_gap": source.attribution_gap,
                    "record_count": len(records),
                    "records": records,
                }
                for source, records in sections
            ],
        }

    @staticmethod
    def bundle_object_key(user_key: str, export_key: str) -> str:
        """Storage key of one export bundle.

        The shape lives in :mod:`app.domain.engines.storage.export_bundle_key`,
        next to the redaction the storage adapters log it through (#1773), so
        the builder and the redaction cannot drift apart.
        """
        return export_bundle_key(user_key, export_key)

    def validate_export_request(
        self,
        user_key: str,
        existing_exports: list[DataExportRequest],
    ) -> list[str]:
        """Return a list of validation errors. Empty list means OK."""
        errors: list[str] = []
        active = [export for export in existing_exports if export.status in ("pending", "processing")]
        if active:
            errors.append("An export job is already active for this user.")
        return errors
