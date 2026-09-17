"""Integration test for migration v0046 — reconcile photo_refs with the catalogue (#1438).

The unit tests run the migration against a fake whose stem reduction is parsed out of
the query text. That proves the migration keeps *using* the repository's expression;
it cannot prove what ArangoDB's ``SPLIT`` / ``FIRST`` / ``LAST`` actually do to a
storage key — and the whole defect class here is a Python-side belief about an AQL
string that turned out to be false.

Two further properties only a real server can supply:

* the attachment ``_key`` is **assigned by ArangoDB**, not chosen here, so the "two
  identities" premise (a short numeric key beside an unrelated ULID) is measured
  rather than staged;
* ``FOR ref IN @refs`` really reduces a bound list of reference strings.

Run with::

    docker run -d --rm -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0046_reconcile_photo_refs.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, SYSTEM_DATABASE

_DB_NAME = "kamerplanter_v0046_migration_test"

# The server probe lives in tests/integration/conftest.py (``arango_db``): one
# probe for the tier, a loud failure under CI, a skip with the address locally.
# A private ``ARANGO_AVAILABLE`` copy here would be the self-skip #1432 retired.
pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the AQL stem reduction and ArangoDB's own key assignment are the SUT"),
]

ULID = "01J0ABCDEFGHJKMNPQRSTVWXYZ"
STRANGER_ULID = "01J0ZYXWVUTSRQPNMKJHGFEDCB"
TENANT = "mein-garten"
OTHER_TENANT = "volkspark"


@pytest.fixture
def db():
    from app.data_access.arango import collections as col

    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db(SYSTEM_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    handle = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in (col.ATTACHMENTS, col.TASKS, col.PLANT_INSTANCES):
        handle.create_collection(name)
    yield handle
    system.delete_database(_DB_NAME)
    client.close()


def _insert_attachment(db, *, tenant: str, ulid: str) -> str:
    """Insert an attachment **without** a ``_key`` — ArangoDB assigns it, as in production."""
    from app.data_access.arango import collections as col

    meta = db.collection(col.ATTACHMENTS).insert(
        {
            "tenant_key": tenant,
            "category": "task",
            "storage_key": f"t/{tenant}/task/2026/01/{ulid}.jpg",
        }
    )
    return str(meta["_key"])


def test_the_two_identities_are_really_two(db) -> None:
    """The control: without this, every assertion below could be a tautology."""
    key = _insert_attachment(db, tenant=TENANT, ulid=ULID)

    assert key != ULID
    assert key.isdigit(), f"expected ArangoDB's numeric key, got {key!r}"


def test_the_ulid_stem_v0003_wrote_is_rewritten_onto_the_document_key(db) -> None:
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0046_reconcile_photo_refs import migration

    key = _insert_attachment(db, tenant=TENANT, ulid=ULID)
    db.collection(col.TASKS).insert({"_key": "task-1", "tenant_key": TENANT, "photo_refs": [ULID]})

    report = migration.up(db)

    assert db.collection(col.TASKS).get("task-1")["photo_refs"] == [key]
    assert report.details["repaired_total"] == 1
    assert report.changed == 1


def test_a_full_storage_key_reduces_through_the_same_expression(db) -> None:
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0046_reconcile_photo_refs import migration

    key = _insert_attachment(db, tenant=TENANT, ulid=ULID)
    storage_key = f"t/{TENANT}/task/2026/01/{ULID}.jpg"
    db.collection(col.TASKS).insert({"_key": "task-1", "tenant_key": TENANT, "photo_refs": [storage_key]})

    migration.up(db)

    assert db.collection(col.TASKS).get("task-1")["photo_refs"] == [key]


def test_a_thumbnail_uri_is_not_repaired_onto_the_attachment_its_size_names(db) -> None:
    """B-1 against a real server, where the numeric keys are ArangoDB's own.

    ``_photo_response`` hands clients
    ``/api/v1/t/{slug}/attachments/{id}/thumbnails/320``. Reduced by
    ``aql_storage_key_stem`` that is ``"320"`` — and a document key of exactly that
    shape is what ArangoDB assigns. The one here is set explicitly because the test
    has to *have* the collision, not wait for it; ``test_the_two_identities_are_really_two``
    is the control that real keys look like this.
    """
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0046_reconcile_photo_refs import migration

    key = _insert_attachment(db, tenant=TENANT, ulid=ULID)
    db.collection(col.ATTACHMENTS).insert(
        {
            "_key": "320",
            "tenant_key": TENANT,
            "category": "task",
            "storage_key": f"t/{TENANT}/task/2026/01/{STRANGER_ULID}.jpg",
        }
    )
    uri = f"/api/v1/t/{TENANT}/attachments/{key}/thumbnails/320"
    db.collection(col.TASKS).insert({"_key": "task-1", "tenant_key": TENANT, "photo_refs": [uri]})

    report = migration.up(db)

    assert db.collection(col.TASKS).get("task-1")["photo_refs"] == [key]
    assert report.details["repaired"] == [
        {
            "collection": col.TASKS,
            "document": "task-1",
            "field": "photo_refs",
            "tenant_key": TENANT,
            "before": uri,
            "after": key,
        }
    ]


def test_a_thumbnail_uri_naming_no_live_key_is_reported_not_guessed(db) -> None:
    """The same URI without its attachment: report it, never fall back to the size."""
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0046_reconcile_photo_refs import migration

    db.collection(col.ATTACHMENTS).insert(
        {
            "_key": "320",
            "tenant_key": TENANT,
            "category": "task",
            "storage_key": f"t/{TENANT}/task/2026/01/{ULID}.jpg",
        }
    )
    uri = f"/api/v1/t/{TENANT}/attachments/9999999/thumbnails/320"
    db.collection(col.TASKS).insert({"_key": "task-1", "tenant_key": TENANT, "photo_refs": [uri]})

    report = migration.up(db)

    assert db.collection(col.TASKS).get("task-1")["photo_refs"] == [uri]
    assert report.changed == 0
    assert report.details["unresolved_total"] == 1


def test_an_unresolvable_entry_stays_verbatim(db) -> None:
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0046_reconcile_photo_refs import migration

    _insert_attachment(db, tenant=TENANT, ulid=ULID)
    db.collection(col.TASKS).insert({"_key": "task-1", "tenant_key": TENANT, "photo_refs": [STRANGER_ULID]})

    report = migration.up(db)

    assert db.collection(col.TASKS).get("task-1")["photo_refs"] == [STRANGER_ULID]
    assert report.changed == 0
    assert report.details["unresolved_total"] == 1
    assert report.details["unresolved"][0]["reference"] == STRANGER_ULID


def test_a_foreign_tenants_attachment_does_not_repair(db) -> None:
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0046_reconcile_photo_refs import migration

    _insert_attachment(db, tenant=OTHER_TENANT, ulid=ULID)
    db.collection(col.TASKS).insert({"_key": "task-1", "tenant_key": TENANT, "photo_refs": [ULID]})

    report = migration.up(db)

    assert db.collection(col.TASKS).get("task-1")["photo_refs"] == [ULID]
    assert report.details["repaired_total"] == 0


def test_dry_run_then_apply_then_re_run(db) -> None:
    """Dry-run writes nothing, the apply repairs, the re-run is a no-op (M-3/M-5)."""
    from app.data_access.arango import collections as col
    from app.migrations.versions.v0046_reconcile_photo_refs import migration

    key = _insert_attachment(db, tenant=TENANT, ulid=ULID)
    db.collection(col.PLANT_INSTANCES).insert(
        {"_key": "plant-1", "tenant_key": TENANT, "photo_refs": [ULID], "cover_photo_ref": ULID}
    )

    dry = migration.up(db, dry_run=True)
    assert dry.details["repaired_total"] == 2
    assert db.collection(col.PLANT_INSTANCES).get("plant-1")["photo_refs"] == [ULID]
    assert db.collection(col.PLANT_INSTANCES).get("plant-1")["cover_photo_ref"] == ULID

    applied = migration.up(db)
    assert applied.details["repaired_total"] == 2
    assert db.collection(col.PLANT_INSTANCES).get("plant-1")["photo_refs"] == [key]
    assert db.collection(col.PLANT_INSTANCES).get("plant-1")["cover_photo_ref"] == key

    again = migration.up(db)
    assert again.changed == 0
    assert again.details["repaired_total"] == 0
    assert again.details["unresolved"] == []
