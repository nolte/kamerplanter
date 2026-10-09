"""MT-052 (#2144) — the v0004 stamp audit classifies author fields on a real ArangoDB and writes nothing.

The volume is stamped by the real ``backfill_tenant_key`` (the v0004 body): two
people's tasks existed before tenants did, one of them founded the tenant the
backfill then picked as default, so the other person's task now carries that
tenant's key — the case the audit is for.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.legacy_stamp_audit import ArangoLegacyStampAudit
from app.migrations import audit_legacy_stamps
from app.migrations.backfill_tenant_key import backfill_tenant_key
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("legacy_stamp_audit")

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    db.collection(col.TENANTS).insert(
        {"_key": "t-alice", "slug": "alice", "name": "Alice", "created_at": "2026-01-01T00:00:00+00:00"}
    )
    memberships = db.collection(col.MEMBERSHIPS)
    memberships.insert({"user_key": "alice", "tenant_key": "t-alice", "role": "admin", "is_active": True})
    memberships.insert({"user_key": "carol", "tenant_key": "t-alice", "role": "grower", "is_active": False})
    tasks = db.collection(col.TASKS)
    tasks.insert({"_key": "task-a", "name": "Water", "created_by": "alice"})
    tasks.insert({"_key": "task-b", "name": "Prune", "created_by": "bob"})
    tasks.insert({"_key": "task-c", "name": "Feed", "created_by": "carol", "completed_by_key": "alice"})
    tasks.insert({"_key": "anonymous", "name": "Check"})
    backfill_tenant_key(db)  # v0004: every task above now carries t-alice
    yield db
    system.delete_database(TEST_DATABASE)


def _by(report, collection: str, field: str, status: str):
    return next((f for f in report.findings if (f.collection, f.field, f.status) == (collection, field, status)), None)


def test_the_audit_classifies_each_author_against_the_stamped_tenant(database) -> None:
    before = sorted(database.collection(col.TASKS).all(), key=lambda d: d["_key"])

    report = ArangoLegacyStampAudit(database).measure()

    assert database.collection(col.TASKS).get("task-b")["tenant_key"] == "t-alice"  # the stamp this is about
    never = _by(report, col.TASKS, "created_by", "never")
    assert never is not None and (never.count, never.sample) == (1, ["task-b"])
    assert _by(report, col.TASKS, "created_by", "member").count == 1
    assert _by(report, col.TASKS, "created_by", "former").count == 1
    assert _by(report, col.TASKS, "completed_by_key", "member").count == 1
    assert report.count("never") == 1
    # Read-only: the rows are exactly as they were.
    assert sorted(database.collection(col.TASKS).all(), key=lambda d: d["_key"]) == before


def test_the_command_exits_3_when_never_rows_exist_and_prints_document_keys_only(database, capsys) -> None:
    code = audit_legacy_stamps.main(["--dry-run"], audit=ArangoLegacyStampAudit(database))

    out = capsys.readouterr().out
    assert code == audit_legacy_stamps.EXIT_FINDINGS
    assert "task-b" in out and "never=1" in out
    assert "alice" not in out.replace("t-alice", "")  # no account key is printed
