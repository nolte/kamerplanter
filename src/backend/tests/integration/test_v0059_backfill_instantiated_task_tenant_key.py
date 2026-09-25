"""Integration test for migration v0059 — the tenant of instantiated tasks (#1708).

The scan turns on ArangoDB's own semantics — ``doc.tenant_key == null`` must
select an **absent** attribute as well as a stored ``null``, and ``""`` must be
selected too — and the owner is read off real entity documents, so the
resolution is measured here against a server rather than a fake.

Run with::

    docker run -d --rm -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0059_backfill_instantiated_task_tenant_key.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.migrations.versions.v0059_backfill_instantiated_task_tenant_key import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("null/absent attribute semantics and entity resolution are the SUT"),
]

_DB_NAME = run_database_name("v0059_migration")

TENANT_A = "tenant-alice"
TENANT_B = "tenant-bob"

_COLLECTIONS = (
    col.TASKS,
    col.WORKFLOW_EXECUTIONS,
    col.PLANT_INSTANCES,
    col.PLANTING_RUNS,
    col.TANKS,
    col.LOCATIONS,
    col.SITES,
)


def _execution(key: str, entity_type: str, entity_key: str) -> dict:
    return {"_key": key, "workflow_template_key": "wf", "entity_type": entity_type, "entity_key": entity_key}


def _task(key: str, execution_key: str | None, entity_type: str, entity_key: str, **extra) -> dict:
    doc = {"_key": key, "name": key, "entity_type": entity_type, "entity_key": entity_key, "tenant_key": ""}
    if execution_key is not None:
        doc["workflow_execution_key"] = execution_key
    doc.update(extra)
    return doc


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _COLLECTIONS:
        database.create_collection(name)

    database.collection(col.SITES).insert_many(
        [{"_key": "site-a", "tenant_key": TENANT_A}, {"_key": "site-b", "tenant_key": TENANT_B}]
    )
    # Locations carry no tenant of their own (#1397); the site does.
    database.collection(col.LOCATIONS).insert({"_key": "loc-b", "tenant_key": "", "site_key": "site-b"})
    database.collection(col.PLANT_INSTANCES).insert_many(
        [{"_key": "plant-a", "tenant_key": TENANT_A}, {"_key": "plant-b", "tenant_key": TENANT_B}]
    )
    database.collection(col.TANKS).insert({"_key": "tank-a", "tenant_key": TENANT_A})
    database.collection(col.PLANTING_RUNS).insert({"_key": "run-b", "tenant_key": TENANT_B})
    database.collection(col.WORKFLOW_EXECUTIONS).insert_many(
        [
            _execution("we-plant-a", "plant_instance", "plant-a"),
            _execution("we-loc-b", "location", "loc-b"),
            _execution("we-tank-a", "tank", "tank-a"),
            _execution("we-gone", "plant_instance", "plant-deleted"),
            _execution("we-generic", "generic", "thing"),
            _execution("we-plant-b", "plant_instance", "plant-b"),
        ]
    )
    absent = _task("t-absent", "we-plant-b", "plant_instance", "plant-b")
    del absent["tenant_key"]
    database.collection(col.TASKS).insert_many(
        [
            _task("t-plant", "we-plant-a", "plant_instance", "plant-a"),
            _task("t-loc", "we-loc-b", "location", "loc-b"),
            _task("t-tank", "we-tank-a", "tank", "tank-a"),
            # The execution record is gone; the task's own binding is the source.
            _task("t-run", "we-deleted", "planting_run", "run-b"),
            _task("t-null", "we-plant-a", "plant_instance", "plant-a", tenant_key=None),
            absent,
            # Unresolvable: entity deleted, and an owner-less entity type.
            _task("t-gone", "we-gone", "plant_instance", "plant-deleted"),
            _task("t-generic", "we-generic", "generic", "thing"),
            # Out of scope: already stamped, and not from an execution.
            _task("t-stamped", "we-plant-b", "plant_instance", "plant-b", tenant_key=TENANT_A),
            _task("t-manual", None, "plant_instance", "plant-b"),
        ]
    )
    yield database
    system.delete_database(_DB_NAME)


def _tenant(db, key: str):
    return db.collection(col.TASKS).get(key).get("tenant_key", "<absent>")


def test_instantiated_tasks_get_their_entitys_tenant(db) -> None:
    report = migration.up(db)

    assert report.scanned == 10
    assert report.changed == 6
    assert report.details == {"candidates": 8, "stamped": 6, "unresolved": 2}
    assert _tenant(db, "t-plant") == TENANT_A
    assert _tenant(db, "t-loc") == TENANT_B
    assert _tenant(db, "t-tank") == TENANT_A
    assert _tenant(db, "t-run") == TENANT_B
    assert _tenant(db, "t-null") == TENANT_A
    assert _tenant(db, "t-absent") == TENANT_B


def test_unresolvable_and_out_of_scope_rows_are_untouched(db) -> None:
    migration.up(db)

    assert _tenant(db, "t-gone") == ""
    assert _tenant(db, "t-generic") == ""
    assert _tenant(db, "t-stamped") == TENANT_A
    assert _tenant(db, "t-manual") == ""


def test_the_second_run_changes_nothing(db) -> None:
    migration.up(db)

    report = migration.up(db)

    assert report.changed == 0
    assert report.details == {"candidates": 2, "stamped": 0, "unresolved": 2}


def test_dry_run_writes_nothing(db) -> None:
    report = migration.up(db, dry_run=True)

    assert report.changed == 0
    assert report.details == {"candidates": 8, "stamped": 6, "unresolved": 2}
    assert _tenant(db, "t-plant") == ""
    assert _tenant(db, "t-absent") == "<absent>"
