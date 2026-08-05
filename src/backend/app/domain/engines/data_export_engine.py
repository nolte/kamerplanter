"""Pure logic for REQ-025 data exports (Art. 15 / 20)."""

from app.domain.models.privacy import DataExportRequest, DataSourceDefinition


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
            edge_collection="membership_in",
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
            fields=["new_email", "status", "requested_at", "expires_at", "confirmed_at"],
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
            # ``assigned_to_user_key`` — the model has never had ``assigned_to``,
            # so this source used to match no document at all.
            filter_field="assigned_to_user_key",
            label="Assigned tasks",
            # ``name`` — the Task model has no ``title``.
            fields=["name", "status", "due_date", "completed_at", "completion_notes"],
        ),
        DataSourceDefinition(
            collection="harvest_batches",
            filter_field="harvester",
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
            collection="inspections",
            filter_field="inspector",
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
            # ``applied_by`` — the model has never had ``applicator``.
            filter_field="applied_by",
            label="Treatment applications",
            # ``dosage`` (not ``dose``).
            fields=["treatment_key", "plant_key", "applied_at", "dosage", "notes"],
        ),
        DataSourceDefinition(
            collection="plant_diary_entries",
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
    ]

    def build_export_manifest(self, user_key: str) -> list[DataSourceDefinition]:
        """Return the full export manifest for the given user."""
        return list(self.USER_DATA_MANIFEST)

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
