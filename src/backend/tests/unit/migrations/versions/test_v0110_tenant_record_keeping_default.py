"""spec/privacy/09 §4, §9, §11, §12 — v0110 classifies the existing tenants (TA-700, TA-716; DEC-30).

The phases are decided here against an in-memory store with the shape of :class:`RecordKeepingStore`;
the AQL itself (the stamp rule, the ``deleted`` gate, the tenant filter, ``down``) is measured against a
real ArangoDB in ``tests/integration/test_v0110_tenant_record_keeping_default.py``. What this module
pins and the integration test cannot cheaply: a tenant whose write fails while the others finish, a
residual the after-check finds, and the runner's handling of both.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from app.common.enums import OrganizationKind, RecordKeeping, TenantType
from app.domain.models.tenant import Tenant, TenantSettings
from app.migrations.framework import tracking
from app.migrations.framework.report_store import DETAILS_SHAPE, redact_details
from app.migrations.framework.runner import MigrationRunner
from app.migrations.versions import v0110_tenant_record_keeping_default as v0110
from app.migrations.versions.v0110_tenant_record_keeping_default import (
    BUCKET_LEGACY,
    BUCKET_LEGACY_REMOVED,
    BUCKET_NONE,
    BUCKET_UNKNOWN_KIND,
    BUCKET_UNKNOWN_KIND_REMOVED,
    Stamp,
    TenantRecordKeepingDefaultMigration,
)
from tests.unit.migrations.framework.conftest import FakeDatabase

#: What ``down`` removes: the values only v0110 writes.
_REMOVED_VALUES = (("record_keeping", "legacy"), ("organization_kind", "unknown_legacy"))


def _rule(tenant: dict[str, Any]) -> Stamp | None:
    """The stamp rule of the AQL, restated: what the tenant is missing (``None`` = nothing)."""
    if tenant.get("status") == "deleted":
        return None
    settings = tenant.get("settings")
    if settings is not None and not isinstance(settings, dict):
        return None
    settings = settings or {}
    personal = tenant.get("tenant_type") in (None, "personal")
    record_keeping = None
    if settings.get("record_keeping") is None:
        record_keeping = "none" if personal else "legacy"
    kind = "unknown_legacy" if settings.get("organization_kind") is None and not personal else None
    if record_keeping is None and kind is None:
        return None
    return Stamp(tenant["_key"], record_keeping, kind)


@dataclass
class FakeStore:
    tenants: list[dict[str, Any]]
    missing: list[str] = field(default_factory=list)
    failing_tenants: set[str] = field(default_factory=set)
    #: Fields that reappear unset after the stamp (a writer racing the migration) — drives ``verify_failed``.
    unset_after: list[tuple[str, str]] = field(default_factory=list)
    stamped: list[str] = field(default_factory=list)

    def missing_collections(self) -> list[str]:
        return list(self.missing)

    def pending(self) -> list[Stamp]:
        return [s for t in sorted(self.tenants, key=lambda t: t["_key"]) if (s := _rule(t)) is not None]

    def stamp(self, tenant_key: str) -> Stamp | None:
        if tenant_key in self.failing_tenants:
            raise RuntimeError("write refused")
        tenant = next(t for t in self.tenants if t["_key"] == tenant_key)
        stamp = _rule(tenant)
        if stamp is None:
            return None
        self.stamped.append(tenant_key)
        settings = dict(tenant.get("settings") or {})
        if stamp.record_keeping is not None:
            settings["record_keeping"] = stamp.record_keeping
        if stamp.organization_kind is not None:
            settings["organization_kind"] = stamp.organization_kind
        tenant["settings"] = settings
        for key, name in self.unset_after:
            if key == tenant_key:
                settings.pop(name, None)
        self.unset_after = [(k, n) for k, n in self.unset_after if k != tenant_key]
        return stamp

    def _drops(self) -> list[tuple[dict[str, Any], list[str]]]:
        out = []
        for tenant in sorted(self.tenants, key=lambda t: t["_key"]):
            settings = tenant.get("settings")
            if tenant.get("status") == "deleted" or not isinstance(settings, dict):
                continue
            drop = [name for name, value in _REMOVED_VALUES if settings.get(name) == value]
            if drop:
                out.append((tenant, drop))
        return out

    def removable(self) -> list[tuple[str, list[str]]]:
        return [(t["_key"], drop) for t, drop in self._drops()]

    def remove(self) -> list[tuple[str, list[str]]]:
        rows = self._drops()
        for tenant, drop in rows:
            for name in drop:
                tenant["settings"].pop(name)
        return [(t["_key"], drop) for t, drop in rows]


def _tenant(key: str, tenant_type: str | None, status: str = "active", **settings: Any) -> dict[str, Any]:
    doc: dict[str, Any] = {"_key": key, "status": status, "settings": {"ai_features_enabled": True, **settings}}
    if tenant_type is not None:
        doc["tenant_type"] = tenant_type
    return doc


def _seeded() -> FakeStore:
    return FakeStore(
        tenants=[
            _tenant("org", "organization"),
            _tenant("org_suspended", "organization", status="suspended"),
            _tenant("org_deleted", "organization", status="deleted"),
            _tenant("pers", "personal"),
            _tenant("pers_untyped", None),
            _tenant("org_declared", "organization", record_keeping="both", organization_kind="association"),
            _tenant("org_half", "organization", record_keeping="pflschg_professional"),
        ]
    )


def _settings(store: FakeStore, key: str) -> dict[str, Any]:
    return next(t for t in store.tenants if t["_key"] == key)["settings"]


@pytest.fixture
def use_store(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    def _install(store: FakeStore) -> TenantRecordKeepingDefaultMigration:
        monkeypatch.setattr(TenantRecordKeepingDefaultMigration, "store_factory", lambda db: store)
        return TenantRecordKeepingDefaultMigration()

    return _install


class TestTheModel:
    """DEC-30: no model default; the values of ``08`` §3.2; a stored stamp reads back."""

    def test_a_new_tenant_is_undeclared(self) -> None:
        settings = TenantSettings()

        assert settings.record_keeping is None
        assert settings.organization_kind is None
        assert Tenant(name="n", slug="n", owner_user_key="u").settings.record_keeping is None

    def test_the_enum_values_are_the_spec_values(self) -> None:
        assert {v.value for v in RecordKeeping} == {
            "legacy",
            "none",
            "pflschg_professional",
            "kcang_association",
            "both",
        }
        assert {v.value for v in OrganizationKind} == {
            "association",
            "commercial",
            "community",
            "other",
            "unknown_legacy",
        }

    def test_a_stamped_document_round_trips_through_the_model(self) -> None:
        """What the repository writes (``model_dump(mode="json", exclude_none=True)``) is what it reads back."""
        stored = {
            "name": "n",
            "slug": "n",
            "owner_user_key": "u",
            "tenant_type": "organization",
            "settings": {"record_keeping": "legacy", "organization_kind": "unknown_legacy", "custom": 1},
        }

        tenant = Tenant.model_validate(stored)
        dumped = tenant.model_dump(by_alias=True, exclude_none=True, mode="json")

        assert tenant.settings.record_keeping is RecordKeeping.LEGACY
        assert tenant.settings.organization_kind is OrganizationKind.UNKNOWN_LEGACY
        assert dumped["settings"]["record_keeping"] == "legacy"
        assert dumped["settings"]["organization_kind"] == "unknown_legacy"
        assert dumped["settings"]["custom"] == 1

    def test_an_undeclared_tenant_writes_no_classification(self) -> None:
        dumped = Tenant(name="n", slug="n", owner_user_key="u").model_dump(exclude_none=True, mode="json")

        assert "record_keeping" not in dumped["settings"]
        assert "organization_kind" not in dumped["settings"]

    def test_no_tenant_api_schema_carries_or_accepts_the_classification(self) -> None:
        """Out of this lane: the declaration at creation (PRIV-409) and the read in GET /tenants (``08`` §5)."""
        from app.api.v1.admin.platform import schemas as admin_schemas
        from app.api.v1.tenants import schemas as tenant_schemas

        classes = [
            tenant_schemas.TenantCreateRequest,
            tenant_schemas.TenantUpdateRequest,
            tenant_schemas.TenantResponse,
            tenant_schemas.TenantWithRoleResponse,
            admin_schemas.AdminTenantResponse,
            admin_schemas.AdminTenantDetailResponse,
            admin_schemas.AdminTenantUpdate,
        ]
        for schema in classes:
            assert not {"settings", "record_keeping", "organization_kind"} & set(schema.model_fields), schema


class TestTheFrozenValues:
    def test_the_frozen_literals_are_the_enum_values_at_the_time_of_writing(self) -> None:
        assert RecordKeeping.LEGACY.value == v0110._LEGACY
        assert RecordKeeping.NONE.value == v0110._NONE
        assert OrganizationKind.UNKNOWN_LEGACY.value == v0110._UNKNOWN_LEGACY
        assert TenantType.PERSONAL.value == v0110._PERSONAL

    def test_it_is_a_reversible_privacy_correction(self) -> None:
        assert v0110.migration.kind == "privacy_correction"
        assert v0110.migration.reversible is True
        assert v0110.migration.version == "0110"


class TestThePrecheck:
    def test_a_missing_collection_leaves_the_migration_pending_and_writes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.missing = ["tenants"]

        report = use_store(store).up(None)

        assert report.precondition_unmet is True
        assert report.details["phases"]["precheck"] == {"ok": False, "unmet": ["tenants"], "candidates": {}}
        assert store.stamped == []

    def test_a_model_with_a_default_is_an_unmet_precondition(self, use_store, monkeypatch: pytest.MonkeyPatch) -> None:  # type: ignore[no-untyped-def]
        from app.domain.models import tenant as tenant_module

        class _Defaulted(TenantSettings):
            record_keeping: RecordKeeping | None = RecordKeeping.LEGACY

        monkeypatch.setattr(tenant_module, "TenantSettings", _Defaulted)
        store = _seeded()

        report = use_store(store).up(None)

        assert report.precondition_unmet is True
        assert "model.tenant_settings.record_keeping.no_default" in report.details["phases"]["precheck"]["unmet"]
        assert store.stamped == []

    def test_the_model_of_this_build_meets_it(self) -> None:
        assert v0110._unmet_model() == []


class TestTheDryRun:
    def test_it_counts_every_bucket_and_writes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()

        report = use_store(store).up(None, dry_run=True)

        assert store.stamped == []
        assert report.changed == 0
        assert report.details["status"] == "dry_run"
        assert report.details["buckets"][BUCKET_LEGACY] == {"org": 1, "org_suspended": 1}
        assert report.details["buckets"][BUCKET_NONE] == {"pers": 1, "pers_untyped": 1}
        assert report.details["buckets"][BUCKET_UNKNOWN_KIND] == {"org": 1, "org_half": 1, "org_suspended": 1}
        assert report.details["phases"]["dry_run"]["would_change"] == {
            BUCKET_LEGACY: 2,
            BUCKET_NONE: 2,
            BUCKET_UNKNOWN_KIND: 3,
        }
        assert set(report.details["phases"]) == {"precheck", "dry_run"}
        assert "record_keeping" not in _settings(store, "org")


class TestTheRealRun:
    def test_it_stamps_active_and_suspended_and_leaves_deleted_and_declared(self, use_store) -> None:  # type: ignore[no-untyped-def]
        """TA-716: a privacy correction processes ``suspended``; ``deleted`` is skipped."""
        store = _seeded()

        report = use_store(store).up(None)

        for key in ("org", "org_suspended"):
            assert _settings(store, key)["record_keeping"] == "legacy"
            assert _settings(store, key)["organization_kind"] == "unknown_legacy"
            assert _settings(store, key)["ai_features_enabled"] is True
        for key in ("pers", "pers_untyped"):
            assert _settings(store, key)["record_keeping"] == "none"
            assert "organization_kind" not in _settings(store, key)
        assert "record_keeping" not in _settings(store, "org_deleted")
        assert _settings(store, "org_declared")["record_keeping"] == "both"
        assert _settings(store, "org_declared")["organization_kind"] == "association"
        # A present value is never overwritten — each field on its own.
        assert _settings(store, "org_half")["record_keeping"] == "pflschg_professional"
        assert _settings(store, "org_half")["organization_kind"] == "unknown_legacy"
        assert report.changed == 5
        assert report.details["status"] == "applied"
        assert report.incomplete is False
        assert report.details["phases"]["verify"] == {
            "residual": {BUCKET_LEGACY: 0, BUCKET_NONE: 0, BUCKET_UNKNOWN_KIND: 0}
        }
        assert {"precheck", "dry_run", "apply", "verify"} <= set(report.details["phases"])

    def test_a_second_run_changes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        migration = use_store(store)
        migration.up(None)

        again = migration.up(None)

        assert again.changed == 0
        assert again.scanned == 0
        assert again.details["status"] == "applied"

    def test_a_failing_tenant_is_left_alone_and_the_run_is_partial(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.failing_tenants = {"org_suspended"}

        report = use_store(store).up(None)

        assert "org_suspended" not in store.stamped
        assert report.details["phases"]["apply"]["tenants_failed"] == ["org_suspended"]
        assert "org" in report.details["phases"]["apply"]["tenants_done"]
        assert report.details["status"] == "partial"
        assert report.incomplete is True
        assert report.changed == 4
        assert report.details["phases"]["verify"]["residual"][BUCKET_LEGACY] == 1

    def test_a_residual_after_apply_is_verify_failed(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.unset_after = [("org", "organization_kind")]

        report = use_store(store).up(None)

        assert report.details["status"] == "verify_failed"
        assert report.incomplete is True
        assert report.details["phases"]["verify"]["residual"][BUCKET_UNKNOWN_KIND] == 1


class TestDown:
    def test_it_removes_only_the_legacy_stamps(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        migration = use_store(store)
        migration.up(None)

        report = migration.down(None)

        for key in ("org", "org_suspended"):
            assert "record_keeping" not in _settings(store, key)
            assert "organization_kind" not in _settings(store, key)
            assert _settings(store, key)["ai_features_enabled"] is True
        # ``none`` on a personal tenant is not unambiguously v0110's and is right either way — it stays.
        assert _settings(store, "pers")["record_keeping"] == "none"
        assert _settings(store, "org_declared") == {
            "ai_features_enabled": True,
            "record_keeping": "both",
            "organization_kind": "association",
        }
        assert _settings(store, "org_half") == {"ai_features_enabled": True, "record_keeping": "pflschg_professional"}
        assert report.details["buckets"][BUCKET_LEGACY_REMOVED] == {"org": 1, "org_suspended": 1}
        assert report.details["buckets"][BUCKET_UNKNOWN_KIND_REMOVED] == {"org": 1, "org_half": 1, "org_suspended": 1}
        assert report.changed == 3

    def test_a_dry_run_down_writes_nothing(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        migration = use_store(store)
        migration.up(None)

        report = migration.down(None, dry_run=True)

        assert _settings(store, "org")["record_keeping"] == "legacy"
        assert report.changed == 0
        assert report.scanned == 3
        assert report.details["status"] == "dry_run"


def _alone(migration: TenantRecordKeepingDefaultMigration) -> MigrationRunner:
    """A runner over this migration only; the runner wants a gapless history from 0001 (M-1)."""
    migration.version = "0001"
    return MigrationRunner([migration])


class TestTheRunnerAndTheReport:
    def test_a_partial_run_is_not_recorded_and_its_report_is_persisted(self, use_store) -> None:  # type: ignore[no-untyped-def]
        store = _seeded()
        store.failing_tenants = {"org"}
        db = FakeDatabase()

        reports = _alone(use_store(store)).upgrade(db)

        assert reports[-1].incomplete is True
        assert tracking.applied_versions(db) == set()
        (stored,) = db.collection("migration_reports").all()
        assert stored["status"] == "partial"
        assert stored["kind"] == "privacy_correction"
        assert stored["redacted_entries"] == 0

    def test_a_clean_run_is_recorded(self, use_store) -> None:  # type: ignore[no-untyped-def]
        db = FakeDatabase()

        _alone(use_store(_seeded())).upgrade(db)

        assert tracking.applied_versions(db) == {"0001"}

    def test_the_reports_pass_the_redaction_filter_whole(self, use_store) -> None:  # type: ignore[no-untyped-def]
        """TA-700: everything up and down report fits the allowed shape — nothing is dropped."""
        migration = use_store(_seeded())
        up = migration.up(None)
        down = migration.down(None)

        for report in (up, down):
            redacted, dropped = redact_details(report.details)
            assert dropped == 0
            assert redacted == report.details
            assert set(report.details) <= set(DETAILS_SHAPE)
