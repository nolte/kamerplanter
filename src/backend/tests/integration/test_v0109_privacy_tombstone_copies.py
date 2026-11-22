"""spec/privacy/09 §3 / §12 (TA-700, TA-701, TA-716) — v0109 against a real ArangoDB.

The AQL is what this module measures: the tenant filter, both tombstone generations, the ``deleted`` gate, the
per-tenant stream transaction, the shared census on a nested field, and the persisted report. The phases
(partial run, residual, runner) are pinned in ``tests/unit/migrations/versions/test_v0109_privacy_tombstone_copies.py``.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0109_privacy_tombstone_copies.py -v
"""

from __future__ import annotations

import json

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.tombstone_census import count_tombstones_by_field
from app.domain.models.privacy import ANONYMIZED_MARKER, TOMBSTONE_REGEX
from app.migrations.framework.report_store import persist_report
from app.migrations.versions.v0109_privacy_tombstone_copies import (
    BUCKET_CARE_EVENTS,
    BUCKET_FILENAMES,
    BUCKET_PLAN_AUDIT,
    BUCKET_UNDECLARED,
    migration,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the correction is per-tenant AQL in a stream transaction on a real server"),
]

_DB_NAME = run_database_name("v0109_privacy_tombstone_copies")
T1 = "anon_0123456789abcdef"
T2 = "anon2_fedcba9876543210"


def _insert(database, collection: str, documents: list[dict]) -> None:  # type: ignore[no-untyped-def]
    """``insert_many`` reports a refused document inline instead of raising; a fixture must not lose one silently."""
    results = database.collection(collection).insert_many(documents)
    refused = [result for result in results if isinstance(result, Exception)]
    assert refused == [], refused


@pytest.fixture
def db():  # type: ignore[no-untyped-def]
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    _insert(
        database,
        col.TENANTS,
        [
            {"_key": key, "slug": key, "status": key.removeprefix("t_")}
            for key in ("t_active", "t_suspended", "t_deleted")
        ],
    )
    events = []
    audits = []
    files = []
    for tenant in ("t_active", "t_suspended", "t_deleted"):
        events += [
            {"_key": f"{tenant}_e_perf", "tenant_key": tenant, "performed_by_user_key": T1, "created_by": "u1"},
            {"_key": f"{tenant}_e_created", "tenant_key": tenant, "performed_by_user_key": "u1", "created_by": T2},
            {"_key": f"{tenant}_e_live", "tenant_key": tenant, "performed_by_user_key": "u1", "created_by": "u1"},
            {"_key": f"{tenant}_e_near", "tenant_key": tenant, "performed_by_user_key": "anon_0123"},
            # Undeclared: a tombstone in a cell no step corrects — counted, never changed.
            {"_key": f"{tenant}_e_voided", "tenant_key": tenant, "voided_by": T1},
        ]
        audits += [
            {"_key": f"{tenant}_a_tomb", "tenant_key": tenant, "user_key": T2, "summary": "Omas Hochbeet"},
            {"_key": f"{tenant}_a_live", "tenant_key": tenant, "user_key": "u1"},
        ]
        files += [
            {
                "_key": f"{tenant}_f_anon",
                "tenant_key": tenant,
                "created_by": ANONYMIZED_MARKER,
                "original_filename": "IMG_Anna.jpg",
            },
            {"_key": f"{tenant}_f_live", "tenant_key": tenant, "created_by": "u1", "original_filename": "keep.jpg"},
        ]
    _insert(database, col.CARE_EVENTS, events)
    _insert(database, col.GARDEN_PLAN_AUDIT, audits)
    _insert(database, col.ATTACHMENTS, files)
    database.collection(col.SITES).insert({"_key": "s1", "tenant_key": "t_active", "plan": {"plan_updated_by": T1}})
    yield database
    system.delete_database(_DB_NAME)


def _doc(db, collection: str, key: str) -> dict:  # type: ignore[no-untyped-def]
    return db.collection(collection).get(key)


def test_the_dry_run_counts_every_bucket_and_writes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db, dry_run=True)

    assert report.details["status"] == "dry_run"
    assert report.details["buckets"][BUCKET_CARE_EVENTS] == {"t_active": 2, "t_suspended": 2}
    assert report.details["buckets"][BUCKET_PLAN_AUDIT] == {"t_active": 1, "t_suspended": 1}
    assert report.details["buckets"][BUCKET_FILENAMES] == {"t_active": 1, "t_suspended": 1}
    assert report.details["buckets"][BUCKET_UNDECLARED] == {"care_events.voided_by": 3, "sites.plan.plan_updated_by": 1}
    assert _doc(db, col.CARE_EVENTS, "t_active_e_perf")["performed_by_user_key"] == T1
    assert _doc(db, col.GARDEN_PLAN_AUDIT, "t_active_a_tomb")["user_key"] == T2
    assert _doc(db, col.ATTACHMENTS, "t_active_f_anon")["original_filename"] == "IMG_Anna.jpg"


def test_the_real_run_corrects_active_and_suspended_tenants_and_leaves_a_deleted_one(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db)

    assert report.details["status"] == "applied"
    assert report.incomplete is False
    assert report.changed == 8
    for tenant in ("t_active", "t_suspended"):
        assert _doc(db, col.CARE_EVENTS, f"{tenant}_e_perf")["performed_by_user_key"] == ANONYMIZED_MARKER
        assert _doc(db, col.CARE_EVENTS, f"{tenant}_e_perf")["created_by"] == "u1"
        assert _doc(db, col.CARE_EVENTS, f"{tenant}_e_created")["created_by"] == ANONYMIZED_MARKER
        assert _doc(db, col.CARE_EVENTS, f"{tenant}_e_created")["performed_by_user_key"] == "u1"
        assert _doc(db, col.GARDEN_PLAN_AUDIT, f"{tenant}_a_tomb")["user_key"] == ANONYMIZED_MARKER
        assert _doc(db, col.ATTACHMENTS, f"{tenant}_f_anon")["original_filename"] == ""
    # Never touched: live keys, a near miss, the undeclared cell, a deleted tenant.
    assert _doc(db, col.CARE_EVENTS, "t_active_e_live")["created_by"] == "u1"
    assert _doc(db, col.CARE_EVENTS, "t_active_e_near")["performed_by_user_key"] == "anon_0123"
    assert "created_by" not in _doc(db, col.CARE_EVENTS, "t_active_e_near")
    assert _doc(db, col.CARE_EVENTS, "t_active_e_voided")["voided_by"] == T1
    assert _doc(db, col.GARDEN_PLAN_AUDIT, "t_active_a_live")["user_key"] == "u1"
    assert _doc(db, col.ATTACHMENTS, "t_active_f_live")["original_filename"] == "keep.jpg"
    assert _doc(db, col.CARE_EVENTS, "t_deleted_e_perf")["performed_by_user_key"] == T1
    assert _doc(db, col.GARDEN_PLAN_AUDIT, "t_deleted_a_tomb")["user_key"] == T2
    assert report.details["phases"]["apply"]["tenants_done"] == ["t_active", "t_suspended"]
    assert report.details["phases"]["verify"]["residual"] == {
        BUCKET_CARE_EVENTS: 0,
        BUCKET_PLAN_AUDIT: 0,
        BUCKET_FILENAMES: 0,
    }
    assert report.details["buckets"][BUCKET_UNDECLARED] == {"care_events.voided_by": 3, "sites.plan.plan_updated_by": 1}


def test_a_second_run_changes_nothing(db) -> None:  # type: ignore[no-untyped-def]
    migration.up(db)

    again = migration.up(db)

    assert again.changed == 0
    assert again.details["status"] == "applied"


def test_the_persisted_report_carries_no_tombstone_name_or_user_key(db) -> None:  # type: ignore[no-untyped-def]
    report = migration.up(db, dry_run=True)

    persist_report(db, migration, report)

    (stored,) = list(db.collection(col.MIGRATION_REPORTS).all())
    text = json.dumps(stored)
    assert stored["redacted_entries"] == 0
    assert stored["status"] == "dry_run"
    for forbidden in (T1, T2, "u1", "Omas Hochbeet", "IMG_Anna.jpg"):
        assert forbidden not in text


def test_the_census_reads_a_nested_field_with_the_live_pattern(db) -> None:  # type: ignore[no-untyped-def]
    counts = count_tombstones_by_field(
        db, [("sites", "plan.plan_updated_by"), ("care_events", "voided_by"), ("no_such", "x")], TOMBSTONE_REGEX
    )

    assert counts == {"sites.plan.plan_updated_by": 1, "care_events.voided_by": 3, "no_such.x": 0}
