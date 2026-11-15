"""spec/privacy/09 §4 / §11 / §12 (TA-700, TA-716) — v0110 against a real ArangoDB.

The AQL is what this module measures: the stamp rule (personal / organisation / untyped), the ``deleted``
gate, that a present value is never overwritten, that the rest of ``settings`` survives, ``down``, the
persisted report — and that the tenant repository reads the stamp and keeps it across a write.
The phases (partial run, residual, runner) are pinned in
``tests/unit/migrations/versions/test_v0110_tenant_record_keeping_default.py``.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0110_tenant_record_keeping_default.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.enums import OrganizationKind, RecordKeeping
from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.migrations.framework.report_store import persist_report
from app.migrations.versions.v0110_tenant_record_keeping_default import (
    BUCKET_LEGACY,
    BUCKET_LEGACY_REMOVED,
    BUCKET_NONE,
    BUCKET_UNKNOWN_KIND,
    migration,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the stamp rule is AQL over the tenants collection on a real server"),
]

_DB_NAME = run_database_name("v0110_tenant_record_keeping_default")


def _tenant(key: str, tenant_type: str | None, status: str = "active", **settings: object) -> dict:
    doc: dict = {"_key": key, "name": key, "slug": key, "owner_user_key": "u1", "status": status}
    if tenant_type is not None:
        doc["tenant_type"] = tenant_type
    if settings:
        doc["settings"] = settings
    return doc


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    documents = [
        _tenant("org", "organization", ai_features_enabled=True, custom="kept"),
        _tenant("org_suspended", "organization", status="suspended"),
        _tenant("org_deleted", "organization", status="deleted"),
        _tenant("pers", "personal", ai_daily_tip_enabled=False),
        _tenant("pers_untyped", None),
        _tenant("org_declared", "organization", record_keeping="both", organization_kind="association"),
        _tenant("org_half", "organization", record_keeping="pflschg_professional"),
    ]
    results = database.collection(col.TENANTS).insert_many(documents)
    assert [r for r in results if isinstance(r, Exception)] == []
    yield database
    system.delete_database(_DB_NAME)


def _settings(db, key: str) -> dict:  # type: ignore[no-untyped-def]
    return db.collection(col.TENANTS).get(key).get("settings") or {}


def test_the_dry_run_counts_and_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db, dry_run=True)

    assert report.details["status"] == "dry_run"
    assert report.details["buckets"][BUCKET_LEGACY] == {"org": 1, "org_suspended": 1}
    assert report.details["buckets"][BUCKET_NONE] == {"pers": 1, "pers_untyped": 1}
    assert report.details["buckets"][BUCKET_UNKNOWN_KIND] == {"org": 1, "org_half": 1, "org_suspended": 1}
    assert "record_keeping" not in _settings(db, "org")
    assert _settings(db, "pers_untyped") == {}


def test_the_real_run_stamps_every_status_but_deleted_and_overwrites_nothing(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db)

    assert report.details["status"] == "applied"
    assert report.changed == 5
    assert _settings(db, "org") == {
        "ai_features_enabled": True,
        "custom": "kept",
        "record_keeping": "legacy",
        "organization_kind": "unknown_legacy",
    }
    assert _settings(db, "org_suspended") == {"record_keeping": "legacy", "organization_kind": "unknown_legacy"}
    assert _settings(db, "pers") == {"ai_daily_tip_enabled": False, "record_keeping": "none"}
    assert _settings(db, "pers_untyped") == {"record_keeping": "none"}
    assert _settings(db, "org_deleted") == {}
    assert _settings(db, "org_declared") == {"record_keeping": "both", "organization_kind": "association"}
    assert _settings(db, "org_half") == {
        "record_keeping": "pflschg_professional",
        "organization_kind": "unknown_legacy",
    }
    assert report.details["phases"]["verify"]["residual"] == {BUCKET_LEGACY: 0, BUCKET_NONE: 0, BUCKET_UNKNOWN_KIND: 0}


def test_a_second_run_changes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)

    again = migration.up(db)

    assert again.changed == 0
    assert again.details["status"] == "applied"


def test_down_removes_the_legacy_stamps_and_keeps_none_and_declared_values(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)

    report = migration.down(db)

    assert _settings(db, "org") == {"ai_features_enabled": True, "custom": "kept"}
    assert _settings(db, "org_suspended") == {}
    assert _settings(db, "pers") == {"ai_daily_tip_enabled": False, "record_keeping": "none"}
    assert _settings(db, "org_declared") == {"record_keeping": "both", "organization_kind": "association"}
    assert _settings(db, "org_half") == {"record_keeping": "pflschg_professional"}
    assert report.details["buckets"][BUCKET_LEGACY_REMOVED] == {"org": 1, "org_suspended": 1}
    assert report.changed == 3
    assert migration.down(db).changed == 0


def test_the_repository_reads_the_stamp_and_keeps_it_across_a_write(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)
    repository = ArangoTenantRepository(db)

    tenant = repository.get_by_key("org")
    assert tenant is not None
    assert tenant.settings.record_keeping is RecordKeeping.LEGACY
    assert tenant.settings.organization_kind is OrganizationKind.UNKNOWN_LEGACY

    repository.update_fields("org", {"name": "Renamed"})
    repository.update("org", repository.get_by_key("org"))  # type: ignore[arg-type]

    assert _settings(db, "org")["record_keeping"] == "legacy"
    assert _settings(db, "org")["organization_kind"] == "unknown_legacy"
    assert _settings(db, "org")["custom"] == "kept"


def test_the_persisted_report_is_filtered_whole(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db, dry_run=True)

    stored = persist_report(db, migration, report)

    assert stored["redacted_entries"] == 0
    assert stored["kind"] == "privacy_correction"
    assert stored["status"] == "dry_run"
