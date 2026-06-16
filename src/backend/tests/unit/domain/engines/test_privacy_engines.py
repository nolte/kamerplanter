"""Tests for REQ-025 privacy engines: DataExport / Erasure / Consent."""

import pytest

from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import DataExportRequest


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


class TestErasureEngine:
    def test_build_plan_contains_all_phases(self):
        engine = ErasureEngine()
        plan = engine.build_erasure_plan("u1")

        assert plan.user_key == "u1"
        assert plan.soft_delete_immediate is True
        assert plan.hard_delete_after_days == 90
        assert plan.storage_cleanup
        assert plan.anonymize
        assert plan.pseudonymize_audit
        assert "users" in plan.delete

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
