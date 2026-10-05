"""#2123 (MT-027) — v0085 and the scheduled tenant deletion, measured on a real ArangoDB.

* v0085 turns every stored ``is_active`` into the ``status`` it meant — ``false``
  → ``suspended``, a tenant whose erasure is already open → ``deleted``, the rest
  → ``active`` — drops the bool, and changes nothing on a second run;
* ``list_due`` lists a ``scheduled`` record only once its grace has ended, and
  only when the caller names the instant;
* of a cancellation (``delete_scheduled``) and the beat's claim exactly one wins.

Locally it needs a database::

    docker run -d -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0085_tenant_status_model.py -v
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.tenant_erasure_repository import ArangoTenantErasureRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.models.tenant_erasure import TenantErasureRecord
from app.migrations.versions.v0085_tenant_status_model import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration and the conditional claim/remove are AQL over a real server"),
]

_DB_NAME = run_database_name("v0085_tenant_status_model")
NOW = datetime(2026, 10, 5, 9, 0, tzinfo=UTC)


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)
    yield database
    system.delete_database(_DB_NAME)


def _tenant(db, key: str, **fields) -> None:  # type: ignore[no-untyped-def]
    db.collection(col.TENANTS).insert(
        {"_key": key, "name": key, "slug": key, "tenant_type": "organization", "owner_user_key": "u", **fields}
    )


def _legacy_volume(db) -> None:  # type: ignore[no-untyped-def]
    _tenant(db, "on", is_active=True)
    _tenant(db, "off", is_active=False)
    _tenant(db, "unflagged")  # a missing flag always counted as active
    _tenant(db, "erasing", is_active=False)  # frozen by an immediate deletion (#1792)
    _tenant(db, "erased-partly", is_active=True)
    _tenant(db, "done-before", is_active=True)  # an old completed record of a re-used key
    records = db.collection(col.TENANT_ERASURE_RECORDS)
    records.insert({"_key": "ter_erasing", "tenant_key": "erasing", "status": "in_progress"})
    records.insert({"_key": "ter_erased-partly", "tenant_key": "erased-partly", "status": "partially_completed"})
    records.insert({"_key": "ter_done-before", "tenant_key": "done-before", "status": "completed"})


def test_every_flag_becomes_the_state_it_meant_and_the_bool_is_gone(db) -> None:  # type: ignore[no-untyped-def]
    _legacy_volume(db)

    report = migration.up(db)

    docs = {doc["_key"]: doc for doc in db.collection(col.TENANTS).all()}
    assert {key: doc["status"] for key, doc in docs.items()} == {
        "on": "active",
        "off": "suspended",
        "unflagged": "active",
        "erasing": "deleted",
        "erased-partly": "deleted",
        "done-before": "active",
    }
    assert not any("is_active" in doc for doc in docs.values())
    assert report.changed == 6
    assert report.details == {"tenants_active": 3, "tenants_deleted": 2, "tenants_suspended": 1}
    # the repository reads what the migration wrote
    repo = ArangoTenantRepository(db)
    assert repo.get_by_key("off").is_active is False  # type: ignore[union-attr]
    assert repo.count(active_only=True) == 3


def test_a_dry_run_counts_and_writes_nothing_and_a_second_run_is_a_no_op(db) -> None:  # type: ignore[no-untyped-def]
    _legacy_volume(db)

    dry = migration.up(db, dry_run=True)
    assert dry.details == {"tenants_active": 3, "tenants_deleted": 2, "tenants_suspended": 1}
    assert all("is_active" in doc for doc in db.collection(col.TENANTS).all() if doc["_key"] != "unflagged")

    migration.up(db)
    again = migration.up(db)

    assert (again.scanned, again.changed) == (0, 0)


def _scheduled(repo: ArangoTenantErasureRepository, tenant_key: str, *, due: datetime) -> str:
    key = TenantErasureEngine.record_key(tenant_key)
    repo.create_with_key(
        TenantErasureRecord(
            tenant_key=tenant_key,
            tenant_type="organization",
            origin="tenant_management",
            status="scheduled",
            requested_at=NOW,
            scheduled_for=due,
        ),
        key,
    )
    return key


def test_a_scheduled_record_is_due_only_after_its_grace_and_only_when_asked(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoTenantErasureRepository(db)
    key = _scheduled(repo, "t-1", due=NOW + timedelta(days=90))
    stale = (NOW - timedelta(hours=6)).isoformat()

    assert repo.list_due(stale_before_iso=stale) == []
    assert repo.list_due(stale_before_iso=stale, scheduled_due_before_iso=(NOW + timedelta(days=89)).isoformat()) == []
    due = repo.list_due(stale_before_iso=stale, scheduled_due_before_iso=(NOW + timedelta(days=90)).isoformat())
    assert [record.key for record in due] == [key]


def test_a_cancellation_removes_only_an_unclaimed_scheduled_record(db) -> None:  # type: ignore[no-untyped-def]
    repo = ArangoTenantErasureRepository(db)
    cancelled = _scheduled(repo, "t-cancel", due=NOW + timedelta(days=90))
    claimed = _scheduled(repo, "t-claimed", due=NOW)

    stale = (NOW - timedelta(hours=6)).isoformat()
    assert repo.claim_for_run(claimed, now_iso=NOW.isoformat(), stale_before_iso=stale) is not None

    assert repo.delete_scheduled(cancelled) is True
    assert repo.get(cancelled) is None
    assert repo.delete_scheduled(claimed) is False  # the run won: nothing is taken back
    assert repo.get(claimed).status == "in_progress"  # type: ignore[union-attr]
    assert repo.claim_for_run(cancelled, now_iso=NOW.isoformat(), stale_before_iso=stale) is None
