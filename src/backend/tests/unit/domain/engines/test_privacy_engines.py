"""Tests for REQ-025 privacy engines: DataExport / Erasure / Consent."""

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel

from app.domain.engines.consent_engine import DIARY_AI_ANALYSIS, ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ANONYMIZED_MARKER, ErasureEngine
from app.domain.models.auth import AuthProvider, RefreshToken
from app.domain.models.harvest import HarvestBatch
from app.domain.models.identification import IdentificationRequest
from app.domain.models.ipm import Inspection, TreatmentApplication
from app.domain.models.membership import Membership
from app.domain.models.plant_diary_entry import PlantDiaryEntry
from app.domain.models.privacy import (
    ConsentRecord,
    DataExportRequest,
    EmailChangeRequest,
    ErasureRequest,
    ProcessingRestriction,
)
from app.domain.models.task import Task
from app.domain.models.user import User

#: Which domain model backs each collection of the export manifest / the
#: anonymisation rules. Used to check declared field names against reality —
#: see :func:`_model_field_names`.
COLLECTION_MODELS: dict[str, type[BaseModel]] = {
    "users": User,
    "auth_providers": AuthProvider,
    "refresh_tokens": RefreshToken,
    "memberships": Membership,
    "consent_records": ConsentRecord,
    "processing_restrictions": ProcessingRestriction,
    "erasure_requests": ErasureRequest,
    "email_change_requests": EmailChangeRequest,
    "data_export_requests": DataExportRequest,
    "tasks": Task,
    "harvest_batches": HarvestBatch,
    "inspections": Inspection,
    "treatment_applications": TreatmentApplication,
    "plant_diary_entries": PlantDiaryEntry,
    "identification_requests": IdentificationRequest,
}


def _model_field_names(model: type[BaseModel]) -> set[str]:
    """Field names of a model, including their aliases (``_key``)."""
    names = set(model.model_fields)
    names |= {field.alias for field in model.model_fields.values() if field.alias}
    return names


class TestDataExportEngine:
    def test_manifest_contains_user_collection(self):
        engine = DataExportEngine()
        manifest = engine.build_export_manifest("u1")
        collections = {entry.collection for entry in manifest}
        assert "users" in collections
        assert "consent_records" in collections
        assert "memberships" in collections

    def test_validate_blocks_when_active_pending(self):
        engine = DataExportEngine()
        existing = [
            DataExportRequest(_key="x", user_key="u1", status="pending"),
        ]
        errors = engine.validate_export_request("u1", existing)
        assert errors

    def test_validate_passes_when_no_active(self):
        engine = DataExportEngine()
        errors = engine.validate_export_request("u1", [])
        assert errors == []

    def test_manifest_includes_identification_requests(self):
        """GDPR-002: Art. 15/20 export must cover plant identification requests."""
        engine = DataExportEngine()
        manifest = engine.build_export_manifest("u1")
        entry = next((e for e in manifest if e.collection == "identification_requests"), None)
        assert entry is not None
        assert entry.filter_field == "user_key"
        assert {"adapter_key", "image_organ", "status", "results", "selected_result_rank", "created_at"} <= set(
            entry.fields
        )
        # image_hash is an internal dedup/audit value and must NOT be exported.
        assert "image_hash" not in entry.fields

    def test_diary_entries_are_exported_with_real_text_and_date(self):
        """REQ-050 AK-24 — Art. 15 disclosure of a diary entry incl. AI result.

        This is the test the old manifest failed: it projected ``body`` and
        ``logged_at``, neither of which exists on ``PlantDiaryEntry``. A wrong
        field name is invisible in an export — an entry with an empty text reads
        exactly like an entry the user never wrote.
        """
        engine = DataExportEngine()
        entry = next(e for e in engine.build_export_manifest("u1") if e.collection == "plant_diary_entries")

        assert entry.filter_field == "created_by"
        # The free text and the date, under the names the model actually uses.
        assert "text" in entry.fields
        assert "created_at" in entry.fields
        assert "body" not in entry.fields
        assert "logged_at" not in entry.fields
        # AK-24: the AI analysis is part of the entry and part of the disclosure.
        assert "analysis" in entry.fields

        # And the projection really produces values on a populated entry.
        diary = PlantDiaryEntry(
            _key="d1",
            plant_key="p1",
            entry_type="observation",
            title="Braune Flecken",
            text="Untere Blätter zeigen braune Flecken.",
            created_by="u1",
            created_at=datetime(2026, 8, 4, 9, 0, tzinfo=UTC),
        )
        projected = {field: getattr(diary, field) for field in entry.fields}
        assert projected["text"] == "Untere Blätter zeigen braune Flecken."
        assert projected["created_at"] == datetime(2026, 8, 4, 9, 0, tzinfo=UTC)

    def test_every_manifest_field_exists_on_its_model(self):
        """Guard for the whole manifest, not just the entry REQ-050 touched.

        Four sources carried names that no model has (``tasks.title``,
        ``harvest_batches.name/status/started_at/completed_at``,
        ``inspections.performed_at/findings``,
        ``treatment_applications.dose``) plus two filter fields that matched
        nothing at all (``assigned_to``, ``applicator``). None of that shows up
        at runtime, so it needs a test rather than a reviewer.
        """
        engine = DataExportEngine()
        manifest = engine.build_export_manifest("u1")

        # A new source must extend the mapping — otherwise it escapes the check.
        assert {entry.collection for entry in manifest} == set(COLLECTION_MODELS)

        unknown: list[str] = []
        for entry in manifest:
            allowed = _model_field_names(COLLECTION_MODELS[entry.collection])
            unknown += [f"{entry.collection}.{field}" for field in entry.fields if field not in allowed]
            if entry.filter_field and entry.filter_field not in allowed:
                unknown.append(f"{entry.collection}.[filter]{entry.filter_field}")
        assert unknown == []


class TestErasureEngine:
    def test_build_plan_contains_all_phases(self):
        engine = ErasureEngine()
        plan = engine.build_erasure_plan("u1")

        assert plan.user_key == "u1"
        assert plan.soft_delete_immediate is True
        assert plan.hard_delete_after_days == 90
        assert plan.storage_cleanup
        assert plan.reference_index_cleanup
        assert plan.anonymize
        assert plan.pseudonymize_audit
        assert "users" in plan.delete

    def test_reference_index_cleanup_runs_before_arango_delete(self):
        """REQ-034 SR-003: Phase 0.5 must precede edge/document/user deletion."""
        engine = ErasureEngine()
        plan = engine.build_erasure_plan("u1")

        order = plan.delete
        assert "_reference_index_cleanup" in order
        # Phase 0.5 sits right after Phase 0 storage cleanup and before users.
        assert order.index("_storage_cleanup") < order.index("_reference_index_cleanup")
        assert order.index("_reference_index_cleanup") < order.index("users")

        rule = plan.reference_index_cleanup[0]
        assert rule.store == "pgvector"
        assert rule.collection == "species_embeddings"
        assert "user_contributed" in rule.filter

    def test_tombstone_hash_deterministic(self):
        salt = "x" * 32
        h1 = ErasureEngine.compute_tombstone_hash("u1", salt)
        h2 = ErasureEngine.compute_tombstone_hash("u1", salt)
        assert h1 == h2
        assert h1.startswith("anon_")

    def test_tombstone_hash_rejects_short_salt(self):
        with pytest.raises(ValueError):
            ErasureEngine.compute_tombstone_hash("u1", "short")

    def test_tombstone_hash_distinct_users(self):
        salt = "x" * 32
        assert ErasureEngine.compute_tombstone_hash("u1", salt) != ErasureEngine.compute_tombstone_hash("u2", salt)

    def test_delete_order_includes_identification_requests(self):
        """GDPR-001: Art. 17 erasure must hard-delete plant identification requests.

        identification_requests carries user_key/tenant_key but has no legal
        retention basis, so it must be hard-deleted (in DELETE_ORDER), not
        anonymised.
        """
        engine = ErasureEngine()
        plan = engine.build_erasure_plan("u1")
        assert "identification_requests" in plan.delete
        # Must be deleted before the user document is removed (no orphan refs).
        assert plan.delete.index("identification_requests") < plan.delete.index("users")
        # Must NOT be anonymised — there is no retention obligation.
        anonymized = {rule.collection for rule in plan.anonymize}
        assert "identification_requests" not in anonymized

    def test_diary_entry_user_references_are_anonymised(self):
        """REQ-050 AK-23 / REQ-025 AK-DA-01 — the entry survives, the names do not.

        Before REQ-050 only the *attachments* of a diary entry were covered
        (storage scope ``user_diary_attachments``); the ``plant_diary_entries``
        document had no rule, so the free text of an erased user stayed
        attributable by name.
        """
        engine = ErasureEngine()
        plan = engine.build_erasure_plan("u1")

        diary_rules = [rule for rule in plan.anonymize if rule.collection == "plant_diary_entries"]
        assert {rule.user_field for rule in diary_rules} == {
            "created_by",
            "analysis_requested_by",
            "analysis_claimed_by",
        }
        # Same marker the attachment path writes (AK-OS-02), not "[deleted]".
        assert {rule.anonymized_value for rule in diary_rules} == {ANONYMIZED_MARKER}
        assert ANONYMIZED_MARKER == "_anonymized"

        # The document itself is kept — it belongs to the plant record of a
        # possibly shared tenant. Anonymised, therefore never deleted.
        assert "plant_diary_entries" not in plan.delete

    def test_anonymisation_rules_address_fields_that_exist(self):
        """A rule pointing at a missing field silently anonymises nothing.

        ``treatment_applications`` carried exactly that defect: the rule named
        ``applicator``, while the model has ``applied_by`` — so the applicator of
        a treatment would have kept their name through an erasure.
        """
        engine = ErasureEngine()
        unknown = [
            f"{rule.collection}.{rule.user_field}"
            for rule in engine.ANONYMIZE_COLLECTIONS
            if rule.user_field not in _model_field_names(COLLECTION_MODELS[rule.collection])
        ]
        assert unknown == []

    def test_anonymized_collection_names_are_reported_once(self):
        """AK-08a — the confirmation lists categories, not rules."""
        engine = ErasureEngine()
        names = engine.anonymized_collection_names()

        assert names.count("plant_diary_entries") == 1
        assert len(names) == len(set(names))
        assert set(names) == {rule.collection for rule in engine.ANONYMIZE_COLLECTIONS}


class TestConsentEngine:
    def test_required_purpose_always_allowed(self):
        engine = ConsentEngine()
        assert engine.is_processing_allowed("core_functionality", consent=None) is True

    def test_optional_purpose_blocked_without_consent(self):
        engine = ConsentEngine()
        assert engine.is_processing_allowed("error_tracking", consent=None) is False

    def test_revoking_required_returns_error(self):
        engine = ConsentEngine()
        errors = engine.validate_consent_change("core_functionality", grant=False)
        assert errors

    def test_unknown_purpose_returns_error(self):
        engine = ConsentEngine()
        errors = engine.validate_consent_change("does_not_exist", grant=True)
        assert errors

    def test_known_optional_purposes(self):
        engine = ConsentEngine()
        keys = {p.key for p in engine.get_all_purposes()}
        assert {"core_functionality", "error_tracking", "hibp_check", "external_enrichment"} <= keys

    def test_diary_ai_analysis_purpose_registered(self):
        """REQ-050 §7.1 — the purpose must be known, optional and revocable."""
        engine = ConsentEngine()
        purpose = engine.find_purpose(DIARY_AI_ANALYSIS)

        assert purpose is not None
        assert purpose.required is False
        assert purpose.legal_basis.startswith("Art. 6(1)(a)")
        # Revocable: a required purpose could not be withdrawn (AK-13 of REQ-025).
        assert engine.validate_consent_change(DIARY_AI_ANALYSIS, grant=False) == []
        # DE and EN label + description are both present (AK-28).
        assert purpose.label_de and purpose.label_en
        assert purpose.description_de and purpose.description_en

    def test_diary_ai_analysis_follows_grant_and_revocation(self):
        """AK-13 — no record and a revoked record both mean "not allowed"."""
        engine = ConsentEngine()
        granted = ConsentRecord(user_key="u1", purpose=DIARY_AI_ANALYSIS, granted=True)
        revoked = ConsentRecord(
            user_key="u1",
            purpose=DIARY_AI_ANALYSIS,
            granted=False,
            revoked_at=datetime.now(UTC),
        )

        assert engine.is_processing_allowed(DIARY_AI_ANALYSIS, consent=None) is False
        assert engine.is_processing_allowed(DIARY_AI_ANALYSIS, consent=granted) is True
        assert engine.is_processing_allowed(DIARY_AI_ANALYSIS, consent=revoked) is False

    def test_diary_ai_analysis_is_independent_of_the_ai_assistant_purposes(self):
        """§7.1 — neither consent implies the other, and cloud does not apply."""
        engine = ConsentEngine()
        diary_granted = ConsentRecord(user_key="u1", purpose=DIARY_AI_ANALYSIS, granted=True)

        # Granting the diary purpose says nothing about the server-side assistant.
        assert engine.is_processing_allowed("ai_tenant_data_access", consent=None) is False
        assert engine.is_processing_allowed("ai_cloud_processing", consent=None) is False
        assert engine.is_processing_allowed(DIARY_AI_ANALYSIS, consent=diary_granted) is True

    def test_plant_diagnosis_purpose_registered(self):
        engine = ConsentEngine()
        purpose = engine.find_purpose("plant_diagnosis")
        assert purpose is not None
        assert purpose.required is False
        # optional purpose: blocked without consent, allowed once granted
        assert engine.is_processing_allowed("plant_diagnosis", consent=None) is False
