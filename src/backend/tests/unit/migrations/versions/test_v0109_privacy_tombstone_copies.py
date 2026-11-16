"""spec/privacy/09 §3, §2a, §12 — v0109 corrects copied tombstones (TA-700, TA-701, TA-701a).

The phases are decided here against an in-memory store with the shape of :class:`TombstoneCopyStore`;
the AQL itself (tenant filter, both generations, the ``deleted`` gate, the transaction) is measured
against a real ArangoDB in ``tests/integration/test_v0109_privacy_tombstone_copies.py``. What this
module can pin and the integration test cannot cheaply: a tenant whose transaction fails while the
others finish, a residual the after-check finds, and the runner's handling of both.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import ANONYMIZED_MARKER, TOMBSTONE_REGEX, is_tombstone
from app.migrations.framework import tracking
from app.migrations.framework.report_store import DETAILS_SHAPE, redact_details
from app.migrations.framework.runner import MigrationRunner
from app.migrations.versions import v0109_privacy_tombstone_copies as v0109
from app.migrations.versions.v0109_privacy_tombstone_copies import (
    BUCKET_CARE_EVENTS,
    BUCKET_FILENAMES,
    BUCKET_PLAN_AUDIT,
    BUCKET_UNDECLARED,
    PrivacyTombstoneCopiesMigration,
)
from tests.unit.migrations.framework.conftest import FakeDatabase

T1 = "anon_0123456789abcdef"
T2 = "anon2_fedcba9876543210"


@dataclass
class _Row:
    collection: str
    tenant_key: str
    values: dict[str, Any]
    key: str


@dataclass
class FakeStore:
    """Holds rows per collection and applies the three steps the way the AQL does (one tenant at a time)."""

    tenants: list[str]
    rows: list[_Row] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    failing_tenants: set[str] = field(default_factory=set)
    #: Rows that reappear after apply (a writer racing the migration) — drives ``verify_failed``.
    resurrect: list[_Row] = field(default_factory=list)
    undeclared: dict[str, int] = field(default_factory=dict)
    applied_tenants: list[str] = field(default_factory=list)

    def missing_collections(self) -> list[str]:
        return list(self.missing)

    def tenant_keys(self) -> list[str]:
        return list(self.tenants)

    def _matches(self, bucket: str, row: _Row) -> bool:
        if bucket == BUCKET_CARE_EVENTS:
            return row.collection == "care_events" and (
                is_tombstone(row.values.get("performed_by_user_key")) or is_tombstone(row.values.get("created_by"))
            )
        if bucket == BUCKET_PLAN_AUDIT:
            return row.collection == "garden_plan_audit" and is_tombstone(row.values.get("user_key"))
        return (
            row.collection == "attachments"
            and row.values.get("created_by") == ANONYMIZED_MARKER
            and bool(row.values.get("original_filename"))
        )

    def hits(self, bucket: str, tenant_key: str) -> tuple[int, list[str]]:
        keys = [r.key for r in self.rows if r.tenant_key == tenant_key and self._matches(bucket, r)]
        return len(keys), keys[:25]

    def apply(self, tenant_key: str) -> dict[str, int]:
        if tenant_key in self.failing_tenants:
            raise RuntimeError("transaction aborted")
        self.applied_tenants.append(tenant_key)
        changed = dict.fromkeys(v0109.CORRECTED_BUCKETS, 0)
        for row in self.rows:
            if row.tenant_key != tenant_key:
                continue
            for bucket in v0109.CORRECTED_BUCKETS:
                if not self._matches(bucket, row):
                    continue
                changed[bucket] += 1
                if bucket == BUCKET_CARE_EVENTS:
                    for name in ("performed_by_user_key", "created_by"):
                        if is_tombstone(row.values.get(name)):
                            row.values[name] = ANONYMIZED_MARKER
                elif bucket == BUCKET_PLAN_AUDIT:
                    row.values["user_key"] = ANONYMIZED_MARKER
                else:
                    row.values["original_filename"] = ""
        self.rows.extend(self.resurrect)
        self.resurrect = []
        return changed

    def count_undeclared(self) -> dict[str, int]:
        return dict(self.undeclared)


def _seeded(tenants: list[str]) -> FakeStore:
    store = FakeStore(tenants=tenants, undeclared={"tasks.assigned_to_user_key": 1, "notifications.user_key": 0})
    for tenant in tenants:
        store.rows += [
            _Row("care_events", tenant, {"performed_by_user_key": T1, "created_by": "u1"}, f"{tenant}-e1"),
            _Row("care_events", tenant, {"performed_by_user_key": "u1", "created_by": T2}, f"{tenant}-e2"),
            _Row("care_events", tenant, {"performed_by_user_key": "u1", "created_by": "u1"}, f"{tenant}-e3"),
            _Row("garden_plan_audit", tenant, {"user_key": T1}, f"{tenant}-a1"),
            _Row("garden_plan_audit", tenant, {"user_key": "u1"}, f"{tenant}-a2"),
            _Row(
                "attachments",
                tenant,
                {"created_by": ANONYMIZED_MARKER, "original_filename": "IMG_Anna.jpg"},
                f"{tenant}-f1",
            ),
            _Row("attachments", tenant, {"created_by": "u1", "original_filename": "keep.jpg"}, f"{tenant}-f2"),
        ]
    return store


@pytest.fixture
def use_store(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    def _install(store: FakeStore) -> PrivacyTombstoneCopiesMigration:
        monkeypatch.setattr(PrivacyTombstoneCopiesMigration, "store_factory", lambda db: store)
        return PrivacyTombstoneCopiesMigration()

    return _install


class TestTheFrozenValues:
    def test_marker_and_pattern_match_the_one_definition_at_the_time_of_writing(self) -> None:
        assert v0109._MARKER == ANONYMIZED_MARKER
        assert v0109._TOMBSTONE_REGEX == TOMBSTONE_REGEX

    def test_the_frozen_cells_are_the_live_watch_list_without_the_corrected_ones(self) -> None:
        """Holds on the day of writing; when the inventory moves, this test is where the freeze shows (M-7)."""
        corrected = {("care_events", "performed_by_user_key"), ("care_events", "created_by")}
        corrected.add(("garden_plan_audit", "user_key"))
        #: Cells the inventory gained after the freeze: each came with its own correction (#2976 → v0114).
        added_later = {("rooting_protocols", "author_user_key")}
        assert set(v0109.UNDECLARED_CELLS) == set(ErasureEngine.tombstone_watch_fields()) - corrected - added_later
        assert not set(v0109.UNDECLARED_CELLS) & ErasureEngine.tombstone_allowlist()

    def test_it_is_a_privacy_correction_and_irreversible(self) -> None:
        assert v0109.migration.kind == "privacy_correction"
        assert v0109.migration.reversible is False


class TestThePrecheck:
    def test_a_missing_collection_leaves_the_migration_pending_and_writes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded(["t1"])
        store.missing = ["garden_plan_audit"]

        report = use_store(store).up(None)

        assert report.precondition_unmet is True
        assert report.details["status"] == "precondition_unmet"
        assert report.details["phases"]["precheck"] == {"ok": False, "unmet": ["garden_plan_audit"], "candidates": {}}
        assert store.applied_tenants == []

    def test_an_inventory_without_the_marker_rule_is_an_unmet_precondition(
        self, use_store, monkeypatch: pytest.MonkeyPatch
    ) -> None:  # type: ignore[no-untyped-def]
        without = [r for r in ErasureEngine.ANONYMIZE_COLLECTIONS if r.collection != "garden_plan_audit"]
        monkeypatch.setattr(ErasureEngine, "ANONYMIZE_COLLECTIONS", without)
        store = _seeded(["t1"])

        report = use_store(store).up(None)

        assert report.precondition_unmet is True
        assert "rule.garden_plan_audit.user_key.marker" in report.details["phases"]["precheck"]["unmet"]
        assert store.applied_tenants == []

    def test_the_live_inventory_of_this_build_meets_it(self) -> None:
        assert v0109._unmet_inventory() == []


class TestTheDryRun:
    def test_it_counts_every_bucket_and_writes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded(["t1", "t2"])

        report = use_store(store).up(None, dry_run=True)

        assert store.applied_tenants == []
        assert report.changed == 0
        assert report.details["status"] == "dry_run"
        assert report.details["buckets"][BUCKET_CARE_EVENTS] == {"t1": 2, "t2": 2}
        assert report.details["buckets"][BUCKET_PLAN_AUDIT] == {"t1": 1, "t2": 1}
        assert report.details["buckets"][BUCKET_FILENAMES] == {"t1": 1, "t2": 1}
        assert report.details["buckets"][BUCKET_UNDECLARED] == {"tasks.assigned_to_user_key": 1}
        assert report.details["phases"]["dry_run"]["would_change"] == {
            BUCKET_CARE_EVENTS: 4,
            BUCKET_PLAN_AUDIT: 2,
            BUCKET_FILENAMES: 2,
        }
        assert set(report.details["phases"]) == {"precheck", "dry_run", "monitor"}


class TestTheRealRun:
    def test_it_converts_counts_the_undeclared_one_and_verifies_zero(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded(["t1"])

        report = use_store(store).up(None)

        values = {r.key: r.values for r in store.rows}
        assert values["t1-e1"] == {"performed_by_user_key": ANONYMIZED_MARKER, "created_by": "u1"}
        assert values["t1-e2"] == {"performed_by_user_key": "u1", "created_by": ANONYMIZED_MARKER}
        assert values["t1-a1"]["user_key"] == ANONYMIZED_MARKER
        assert values["t1-a2"]["user_key"] == "u1"
        assert values["t1-f1"]["original_filename"] == ""
        assert values["t1-f2"]["original_filename"] == "keep.jpg"
        assert report.changed == 4
        assert report.details["status"] == "applied"
        assert report.incomplete is False
        assert report.details["buckets"][BUCKET_UNDECLARED] == {"tasks.assigned_to_user_key": 1}
        assert report.details["phases"]["verify"] == {
            "residual": {BUCKET_CARE_EVENTS: 0, BUCKET_PLAN_AUDIT: 0, BUCKET_FILENAMES: 0}
        }
        assert {"precheck", "dry_run", "apply", "verify"} <= set(report.details["phases"])

    def test_a_second_run_changes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded(["t1"])
        migration = use_store(store)
        migration.up(None)

        again = migration.up(None)

        assert again.changed == 0
        assert again.details["status"] == "applied"

    def test_a_failing_tenant_is_rolled_back_alone_and_the_run_is_partial(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded(["t1", "t2", "t3"])
        store.failing_tenants = {"t2"}

        report = use_store(store).up(None)

        assert store.applied_tenants == ["t1", "t3"]
        assert report.details["phases"]["apply"]["tenants_done"] == ["t1", "t3"]
        assert report.details["phases"]["apply"]["tenants_failed"] == ["t2"]
        assert report.details["status"] == "partial"
        assert report.incomplete is True
        assert report.changed == 8
        # t2 is untouched and still counted by the after-check.
        assert report.details["phases"]["verify"]["residual"][BUCKET_CARE_EVENTS] == 2

    def test_a_residual_after_apply_is_verify_failed(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded(["t1"])
        store.resurrect = [_Row("garden_plan_audit", "t1", {"user_key": T2}, "t1-late")]

        report = use_store(store).up(None)

        assert report.details["status"] == "verify_failed"
        assert report.incomplete is True
        assert report.details["phases"]["verify"]["residual"][BUCKET_PLAN_AUDIT] == 1

    def test_a_tenant_without_candidates_opens_no_transaction(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded(["t1"])
        store.tenants.append("empty")

        report = use_store(store).up(None)

        assert store.applied_tenants == ["t1"]
        assert report.details["phases"]["apply"]["tenants_done"] == ["t1", "empty"]


def _alone(migration: PrivacyTombstoneCopiesMigration) -> MigrationRunner:
    """A runner over this migration only; the runner wants a gapless history from 0001 (M-1)."""
    migration.version = "0001"
    return MigrationRunner([migration])


class TestTheRunnerAndTheReport:
    def test_a_partial_run_is_not_recorded_and_its_report_is_persisted(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded(["t1", "t2"])
        store.failing_tenants = {"t2"}
        migration = use_store(store)
        db = FakeDatabase()

        reports = _alone(migration).upgrade(db)

        assert reports[-1].incomplete is True
        assert tracking.applied_versions(db) == set()
        (stored,) = db.collection("migration_reports").all()
        assert stored["status"] == "partial"
        assert stored["kind"] == "privacy_correction"
        assert stored["redacted_entries"] == 0

    def test_a_dry_run_persists_its_report_and_records_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        db = FakeDatabase()

        _alone(use_store(_seeded(["t1"]))).upgrade(db, dry_run=True)

        assert tracking.applied_versions(db) == set()
        (stored,) = db.collection("migration_reports").all()
        assert stored["dry_run"] is True
        assert stored["status"] == "dry_run"

    def test_a_clean_run_is_recorded(self, use_store) -> None:  # type: ignore[no-untyped-def]
        db = FakeDatabase()

        _alone(use_store(_seeded(["t1"]))).upgrade(db)

        assert tracking.applied_versions(db) == {"0001"}

    def test_the_report_passes_the_redaction_filter_whole(self, use_store) -> None:  # type: ignore[no-untyped-def]
        """TA-700: everything the migration reports fits the allowed shape — nothing is dropped."""
        report = use_store(_seeded(["t1", "t2"])).up(None)

        redacted, dropped = redact_details(report.details)

        assert dropped == 0
        assert redacted == report.details
        assert set(report.details) <= set(DETAILS_SHAPE)
        assert not any(is_tombstone(key) for keys in report.details["samples"].values() for key in keys)
