"""Pure logic for REQ-025 data exports (Art. 15 / 20)."""

from datetime import datetime
from typing import Any

from app.domain.models.privacy import DataExportRequest, DataSourceDefinition

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

        Outside the ``t/{tenant}/...`` attachment namespace on purpose: the
        bundle spans every tenant the user belongs to and belongs to the user,
        not to any one of them.
        """
        return f"privacy/exports/{user_key}/{export_key}.json"

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
