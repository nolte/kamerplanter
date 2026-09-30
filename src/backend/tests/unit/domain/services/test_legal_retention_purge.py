"""#1789 / #1793 — the NFR-011 R-16..R-18 and R-06a purges, service and settings side.

The AQL is measured against a real ArangoDB in
``tests/integration/test_legal_retention_purge.py``; here the double records what
the service asks for, and refuses what the real repository cannot take (a
cutoff that is not an ISO instant, a rule that is not a declared one).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.config.settings import Settings
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.interfaces.legal_retention_repository import ILegalRetentionRepository
from app.domain.models.legal_retention import LegalRetentionPurgeCount, LegalRetentionRule
from app.domain.models.tenant_erasure import TenantErasureEntry
from app.domain.services.privacy_service import PrivacyService
from app.domain.services.retention_service import RetentionService

NOW = datetime(2026, 9, 30, 4, 45, tzinfo=UTC)


class RecordingLegalRetentionRepo(ILegalRetentionRepository):
    def __init__(self, fail_on: str | None = None) -> None:
        self.row_calls: list[tuple[str, str, datetime]] = []
        self.record_calls: list[tuple[datetime, list[str]]] = []
        self._fail_on = fail_on

    def delete_expired_rows_of_deleted_tenants(
        self, rule: LegalRetentionRule, *, cutoff_iso: str
    ) -> LegalRetentionPurgeCount:
        if rule not in TenantErasureEngine.LEGAL_RETENTION_RULES:
            raise ValueError("not a declared rule")
        cutoff = datetime.fromisoformat(cutoff_iso)  # the real query reads it with DATE_TIMESTAMP
        self.row_calls.append((rule.rule, rule.collection, cutoff))
        if rule.rule == self._fail_on:
            raise ConnectionError("database gone")
        return LegalRetentionPurgeCount(rows=1)

    def delete_expired_tenant_erasure_records(self, *, cap_before_iso: str, retained_collections: Sequence[str]) -> int:
        self.record_calls.append((datetime.fromisoformat(cap_before_iso), list(retained_collections)))
        return 4


def _service(repo: ILegalRetentionRepository | None, retention: RetentionService | None = None) -> PrivacyService:
    return PrivacyService(
        export_repo=MagicMock(),
        consent_repo=MagicMock(),
        restriction_repo=MagicMock(),
        erasure_repo=MagicMock(),
        email_change_repo=MagicMock(),
        user_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        data_export_engine=MagicMock(),
        erasure_engine=ErasureEngine(),
        consent_engine=MagicMock(),
        password_engine=MagicMock(),
        token_engine=MagicMock(),
        email_service=MagicMock(),
        frontend_url="http://frontend.invalid",
        retention=retention or RetentionService(),
        legal_retention_repo=repo,
    )


class TestTheRowPurge:
    async def test_each_rule_counts_its_own_period_back_in_calendar_years(self):
        repo = RecordingLegalRetentionRepo()

        counts = await _service(repo).purge_expired_legal_retention_rows(NOW)

        assert repo.row_calls == [
            ("R-16", "harvest_batches", datetime(2021, 9, 30, 4, 45, tzinfo=UTC)),
            ("R-17", "treatment_applications", datetime(2023, 9, 30, 4, 45, tzinfo=UTC)),
            ("R-18", "inspections", datetime(2023, 9, 30, 4, 45, tzinfo=UTC)),
        ]
        assert counts == {rule: {"rows": 1, "children": 0, "edges": 0} for rule in ("R-16", "R-17", "R-18")}

    async def test_the_period_is_read_from_its_setting(self):
        repo = RecordingLegalRetentionRepo()
        retention = RetentionService(harvest_data_retention_years=7)

        await _service(repo, retention).purge_expired_legal_retention_rows(NOW)

        assert repo.row_calls[0][2] == datetime(2019, 9, 30, 4, 45, tzinfo=UTC)

    async def test_one_failing_rule_does_not_stop_the_others_and_the_run_still_fails(self):
        repo = RecordingLegalRetentionRepo(fail_on="R-16")

        with pytest.raises(ConnectionError):
            await _service(repo).purge_expired_legal_retention_rows(NOW)

        assert [call[0] for call in repo.row_calls] == ["R-16", "R-17", "R-18"]

    async def test_it_refuses_without_a_repository(self):
        with pytest.raises(RuntimeError, match="legal-retention repository"):
            await _service(None).purge_expired_legal_retention_rows(NOW)


class TestTheRecordPurge:
    async def test_the_cap_and_the_anchor_collections_reach_the_repository(self):
        repo = RecordingLegalRetentionRepo()

        assert await _service(repo).purge_expired_tenant_erasure_records(NOW) == 4

        assert repo.record_calls == [
            (datetime(2021, 9, 30, 4, 45, tzinfo=UTC), ["harvest_batches", "treatment_applications", "inspections"])
        ]


class TestThePeriods:
    @pytest.mark.parametrize(
        ("argument", "value"),
        [
            ("harvest_data_retention_years", 4),
            ("treatment_retention_years", 2),
            ("inspection_retention_years", 2),
            ("tenant_erasure_record_retention_years", 6),
            ("tenant_erasure_record_retention_years", 0),
        ],
    )
    def test_the_service_refuses_a_period_outside_the_legal_bounds(self, argument, value):
        with pytest.raises(ValueError, match="NFR-011"):
            RetentionService(**{argument: value})

    @pytest.mark.parametrize(
        ("variable", "value"),
        [
            ("RETENTION_HARVEST_DATA_MIN_RETENTION_YEARS", "4"),
            ("RETENTION_TREATMENT_MIN_RETENTION_YEARS", "2"),
            ("RETENTION_INSPECTION_MIN_RETENTION_YEARS", "2"),
            ("RETENTION_TENANT_ERASURE_RECORD_RETENTION_YEARS", "6"),
        ],
    )
    def test_the_setting_refuses_it_at_start(self, monkeypatch, variable, value):
        monkeypatch.setenv(variable, value)

        with pytest.raises(ValidationError):
            Settings()

    def test_a_29_february_cutoff_lands_on_28_february(self):
        leap = datetime(2028, 2, 29, 4, 45, tzinfo=UTC)

        assert RetentionService().legal_retention_cutoff("R-17", leap) == datetime(2025, 2, 28, 4, 45, tzinfo=UTC)


class TestTheRulesFollowTheInventory:
    """#1789 — a row kept for R-16..R-18 cannot lack a purge rule (``TenantErasureEngine.validate``)."""

    def test_the_declared_rules_validate(self):
        TenantErasureEngine.validate()

    def test_a_kept_collection_without_a_rule_is_refused(self, monkeypatch):
        rules = tuple(r for r in TenantErasureEngine.LEGAL_RETENTION_RULES if r.rule != "R-18")
        monkeypatch.setattr(TenantErasureEngine, "LEGAL_RETENTION_RULES", rules)

        with pytest.raises(ValueError, match="inspections"):
            TenantErasureEngine.validate()

    def test_a_rule_on_a_deleted_collection_is_refused(self, monkeypatch):
        inventory = [
            TenantErasureEntry(collection="inspections", action="delete") if e.collection == "inspections" else e
            for e in TenantErasureEngine.INVENTORY
        ]
        monkeypatch.setattr(TenantErasureEngine, "INVENTORY", inventory)

        with pytest.raises(ValueError, match="R-18"):
            TenantErasureEngine.validate()

    def test_the_tombstone_fields_are_the_pseudonymised_ones(self):
        assert TenantErasureEngine.pseudonymized_account_fields() == {
            ("harvest_batches", "harvested_by_key"),
            ("quality_assessments", "assessed_by_key"),
            ("treatment_applications", "applied_by_key"),
            ("inspections", "inspected_by_key"),
        }
