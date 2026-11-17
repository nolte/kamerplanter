"""spec/privacy/09 §5a, §9, §11, §12 — v0114 moves the rooting-protocol author's key out of ``author`` (#2976).

The phases are decided here against an in-memory store with the shape of :class:`RootingAuthorStore`; the bucket
rule is restated in :meth:`FakeStore._classify` the way the AQL decides it. The AQL itself (tenant predicate,
``DOCUMENT`` lookup, ``UNSET``) runs against a real ArangoDB in
``tests/integration/test_v0114_rooting_protocol_author_key.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.tenant_export_engine import TenantExportEngine
from app.domain.models.privacy import ANONYMIZED_MARKER
from app.domain.models.propagation import RootingProtocol
from app.migrations.framework.report_store import redact_details
from app.migrations.versions import v0114_rooting_protocol_author_key as v0114
from app.migrations.versions.v0114_rooting_protocol_author_key import (
    BUCKET_DROPPED,
    BUCKET_KEYED,
    BUCKET_TO_MARKER,
    STEP_BUCKETS,
    RootingProtocolAuthorKeyMigration,
    TenantHits,
)


@dataclass
class _Row:
    tenant_key: str
    doc: dict[str, Any]
    key: str


@dataclass
class FakeStore:
    tenants: dict[str, str]
    users: set[str] = field(default_factory=set)
    rows: list[_Row] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    failing_tenants: set[str] = field(default_factory=set)
    #: Rows that reappear after apply (a writer racing the migration) — drives ``verify_failed``.
    resurrect: list[_Row] = field(default_factory=list)
    applied_tenants: list[str] = field(default_factory=list)

    def missing_collections(self) -> list[str]:
        return list(self.missing)

    def tenant_keys(self) -> list[str]:
        return sorted(k for k, status in self.tenants.items() if status != "deleted")

    def _classify(self, doc: dict[str, Any]) -> tuple[str, str | None]:
        author = doc["author"]
        named = isinstance(author, str) and author != ""
        kept = doc.get("author_user_key")
        live = named and author != ANONYMIZED_MARKER and author in self.users
        if kept is not None:
            return BUCKET_DROPPED, kept
        if live:
            return BUCKET_KEYED, author
        if named:
            return BUCKET_TO_MARKER, ANONYMIZED_MARKER
        return BUCKET_DROPPED, None

    def _pending(self, tenant_key: str) -> list[_Row]:
        return [r for r in self.rows if r.tenant_key == tenant_key and "author" in r.doc]

    def hits(self, tenant_key: str) -> TenantHits:
        counts = dict.fromkeys(STEP_BUCKETS, 0)
        rows = self._pending(tenant_key)
        for row in rows:
            counts[self._classify(row.doc)[0]] += 1
        return TenantHits(counts, [r.key for r in rows][:25])

    def apply(self, tenant_key: str) -> dict[str, int]:
        if tenant_key in self.failing_tenants:
            raise RuntimeError("transaction aborted")
        self.applied_tenants.append(tenant_key)
        changed = dict.fromkeys(STEP_BUCKETS, 0)
        for row in self._pending(tenant_key):
            bucket, new_key = self._classify(row.doc)
            changed[bucket] += 1
            row.doc.pop("author")
            row.doc["author_user_key"] = new_key
        self.rows.extend(self.resurrect)
        self.resurrect = []
        return changed


def _seeded() -> FakeStore:
    store = FakeStore(
        tenants={"t_active": "active", "t_suspended": "suspended", "t_deleted": "deleted"},
        users={"u_live"},
    )
    for tenant in ("t_active", "t_suspended", "t_deleted"):
        store.rows += [
            _Row(tenant, {"name": "a", "author": "u_live"}, f"{tenant}-p1"),
            _Row(tenant, {"name": "b", "author": "u_erased"}, f"{tenant}-p2"),
            _Row(tenant, {"name": "c", "author": None}, f"{tenant}-p3"),
            _Row(tenant, {"name": "d", "author": "u_erased", "author_user_key": "u_live"}, f"{tenant}-p4"),
            _Row(tenant, {"name": "e", "author_user_key": "u_live"}, f"{tenant}-p5"),
            _Row(tenant, {"name": "f", "author": ANONYMIZED_MARKER}, f"{tenant}-p6"),
        ]
    return store


def _doc(store: FakeStore, key: str) -> dict[str, Any]:
    return next(r for r in store.rows if r.key == key).doc


@pytest.fixture
def use_store(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    def _install(store: FakeStore) -> RootingProtocolAuthorKeyMigration:
        monkeypatch.setattr(RootingProtocolAuthorKeyMigration, "store_factory", lambda db: store)
        return RootingProtocolAuthorKeyMigration()

    return _install


class TestTheFrozenValues:
    def test_the_frozen_literals_are_the_definitions_at_the_time_of_writing(self) -> None:
        assert v0114._MARKER == ANONYMIZED_MARKER
        assert v0114._KEY_FIELD in RootingProtocol.model_fields
        assert v0114._OLD_FIELD not in RootingProtocol.model_fields

    def test_it_is_an_irreversible_privacy_correction(self) -> None:
        """PRIV-716: a correction walks every tenant but ``deleted``; M-6: no fake inverse."""
        assert v0114.migration.kind == "privacy_correction"
        assert v0114.migration.reversible is False
        assert v0114.migration.version == "0114"


class TestTheBuild:
    def test_the_build_meets_the_precheck(self) -> None:
        assert v0114._unmet_build() == []

    def test_the_erasure_writes_the_marker_and_the_export_knows_the_account(self) -> None:
        assert ("rooting_protocols", "author_user_key") in ErasureEngine.account_reference_fields()
        assert TenantExportEngine.references_of("rooting_protocols")["author_user_key"].kind == "account"

    def test_no_request_schema_accepts_the_key(self) -> None:
        """PRIV-705: the key is the server's; a body can neither set nor smuggle it."""
        from app.api.v1.propagation.schemas import RootingProtocolCreate

        assert "author_user_key" not in RootingProtocolCreate.model_fields
        assert "author" not in RootingProtocolCreate.model_fields

    def test_a_model_that_still_reads_author_is_an_unmet_precondition(
        self,
        use_store,  # type: ignore[no-untyped-def]
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(v0114, "_unmet_build", lambda: ["model.rooting_protocols.author.still_read"])
        store = _seeded()

        report = use_store(store).up(None)

        assert report.precondition_unmet is True
        assert store.applied_tenants == []
        assert _doc(store, "t_active-p1") == {"name": "a", "author": "u_live"}


class TestThePrecheck:
    def test_a_missing_collection_leaves_the_migration_pending_and_writes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.missing = ["rooting_protocols"]

        report = use_store(store).up(None)

        assert report.precondition_unmet is True
        assert report.details["phases"]["precheck"] == {"ok": False, "unmet": ["rooting_protocols"], "candidates": {}}
        assert store.applied_tenants == []


class TestTheDryRun:
    def test_it_counts_and_writes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()

        report = use_store(store).up(None, dry_run=True)

        assert store.applied_tenants == []
        assert report.changed == 0
        assert report.details["status"] == "dry_run"
        assert report.details["buckets"][BUCKET_KEYED] == {"t_active": 1, "t_suspended": 1}
        assert report.details["buckets"][BUCKET_TO_MARKER] == {"t_active": 2, "t_suspended": 2}
        assert report.details["buckets"][BUCKET_DROPPED] == {"t_active": 2, "t_suspended": 2}
        assert set(report.details["phases"]) == {"precheck", "dry_run"}
        assert _doc(store, "t_active-p1") == {"name": "a", "author": "u_live"}


class TestTheRealRun:
    def test_it_moves_the_key_in_every_tenant_but_deleted(self, use_store) -> None:  # type: ignore[no-untyped-def]
        """TA-716: a correction processes ``suspended`` too."""
        store = _seeded()

        report = use_store(store).up(None)

        assert store.applied_tenants == ["t_active", "t_suspended"]
        for tenant in ("t_active", "t_suspended"):
            assert _doc(store, f"{tenant}-p1") == {"name": "a", "author_user_key": "u_live"}
            assert _doc(store, f"{tenant}-p2") == {"name": "b", "author_user_key": ANONYMIZED_MARKER}
            assert _doc(store, f"{tenant}-p3") == {"name": "c", "author_user_key": None}
            # A key the new code stamped is never replaced by the old field.
            assert _doc(store, f"{tenant}-p4") == {"name": "d", "author_user_key": "u_live"}
            assert _doc(store, f"{tenant}-p5") == {"name": "e", "author_user_key": "u_live"}
            assert _doc(store, f"{tenant}-p6") == {"name": "f", "author_user_key": ANONYMIZED_MARKER}
        assert _doc(store, "t_deleted-p1") == {"name": "a", "author": "u_live"}
        assert report.details["status"] == "applied"
        assert report.changed == 10
        assert report.details["phases"]["verify"] == {"residual": {"rooting_protocols.author": 0}}
        assert {"precheck", "dry_run", "apply", "verify"} <= set(report.details["phases"])

    def test_no_raw_key_is_left_in_author(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()

        use_store(store).up(None)

        assert not [r.key for r in store.rows if r.tenant_key != "t_deleted" and "author" in r.doc]

    def test_a_second_run_changes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        migration = use_store(store)
        migration.up(None)

        again = migration.up(None)

        assert again.changed == 0
        assert again.details["status"] == "applied"

    def test_a_failing_tenant_rolls_back_alone_and_the_run_is_partial(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.failing_tenants = {"t_active"}

        report = use_store(store).up(None)

        assert report.details["status"] == "partial"
        assert report.incomplete is True
        assert report.details["phases"]["apply"]["tenants_failed"] == ["t_active"]
        assert report.details["phases"]["apply"]["tenants_done"] == ["t_suspended"]
        assert _doc(store, "t_suspended-p1") == {"name": "a", "author_user_key": "u_live"}

    def test_a_residual_is_verify_failed(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.resurrect = [_Row("t_active", {"name": "z", "author": "u_live"}, "t_active-late")]

        report = use_store(store).up(None)

        assert report.details["status"] == "verify_failed"
        assert report.incomplete is True

    def test_the_report_passes_the_redaction_filter_unchanged(self, use_store) -> None:  # type: ignore[no-untyped-def]
        """TA-701a: counts, bucket names, tenant and row keys only — no account key, no marker."""
        store = _seeded()

        report = use_store(store).up(None)

        _logged, dropped = redact_details(report.details)
        assert dropped == 0
