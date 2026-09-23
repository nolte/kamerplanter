"""Integration test for migration v0056 — the explicit ``null`` on pre-#1669 rows.

What this migration turns on is ArangoDB's own behaviour, which a double could only
restate:

* ``FILTER !HAS(doc, @field)`` selects a document that *lacks* the attribute and
  not one that carries ``null`` — the whole idempotency argument.
* ``update(..., keep_none=True)`` makes the ``null`` land instead of dropping the
  attribute (``keepNull``); ``field in stored and stored[field] is None`` afterwards
  is the only honest measurement.

And the one negative that matters is measured here too: a legacy row whose free-text
name is **literally an existing user key** still gets ``null``. Guessing an owner
from the free text is the backfill #1669 forbids.

Run with::

    docker run -d --rm -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0056_stamp_attribution_user_keys.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.migrations.versions.v0056_stamp_attribution_user_keys import ATTRIBUTION_KEY_FIELDS, migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("!HAS and keepNull semantics are the SUT"),
]

_DB_NAME = "kamerplanter_v0056_migration_test"

#: A user that exists — and whose key somebody typed into the free-text field.
USER = "user-42"


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for collection, _field in ATTRIBUTION_KEY_FIELDS:
        database.create_collection(collection)
    yield database
    system.delete_database(_DB_NAME)


@pytest.fixture
def seeded(db):
    db.collection(col.HARVEST_BATCHES).insert_many(
        [
            {"_key": "hb-legacy", "tenant_key": "t-a", "harvester": "Maren"},
            {"_key": "hb-name-is-a-key", "tenant_key": "t-a", "harvester": USER},
            {"_key": "hb-keyed", "tenant_key": "t-a", "harvester": "Maren", "harvested_by_key": USER},
        ]
    )
    db.collection(col.INSPECTIONS).insert_many(
        [
            {"_key": "in-legacy", "tenant_key": "t-a", "inspector": f"mcp:{USER}"},
            {"_key": "in-keyed", "tenant_key": "t-a", "inspector": f"mcp:{USER}", "inspected_by_key": USER},
        ]
    )
    db.collection(col.TREATMENT_APPLICATIONS).insert_many(
        [
            {"_key": "ta-legacy", "tenant_key": "t-a", "applied_by": ""},
        ]
    )
    return db


def _stored(db, collection: str, key: str) -> dict:
    return dict(db.collection(collection).get(key))


def test_legacy_rows_carry_an_explicit_null_and_keyed_rows_are_untouched(seeded):
    report = migration.up(seeded)

    assert report.changed == 4
    for collection, key, field in [
        (col.HARVEST_BATCHES, "hb-legacy", "harvested_by_key"),
        (col.HARVEST_BATCHES, "hb-name-is-a-key", "harvested_by_key"),
        (col.INSPECTIONS, "in-legacy", "inspected_by_key"),
        (col.TREATMENT_APPLICATIONS, "ta-legacy", "applied_by_key"),
    ]:
        stored = _stored(seeded, collection, key)
        assert field in stored, f"{collection}/{key}: the attribute was dropped instead of stamped null"
        assert stored[field] is None
    # The rows a #1669 path had already written keep their key.
    assert _stored(seeded, col.HARVEST_BATCHES, "hb-keyed")["harvested_by_key"] == USER
    assert _stored(seeded, col.INSPECTIONS, "in-keyed")["inspected_by_key"] == USER


def test_a_free_text_that_equals_a_user_key_is_not_promoted_to_the_key(seeded):
    """The forbidden backfill, against the real store."""
    migration.up(seeded)

    stored = _stored(seeded, col.HARVEST_BATCHES, "hb-name-is-a-key")
    assert stored["harvested_by_key"] is None
    assert stored["harvester"] == USER, "the free text itself is not touched either"
    legacy = _stored(seeded, col.INSPECTIONS, "in-legacy")
    assert legacy["inspected_by_key"] is None
    assert legacy["inspector"] == f"mcp:{USER}"


def test_a_second_run_finds_nothing(seeded):
    """M-3 against ``!HAS``: a stamped ``null`` is *present*, so it is not rediscovered."""
    first = migration.up(seeded)
    second = migration.up(seeded)

    assert first.changed == 4
    assert second.changed == 0
    assert second.noop is True


def test_dry_run_writes_nothing(seeded):
    report = migration.up(seeded, dry_run=True)

    assert report.changed == 0
    assert report.details["stamped"]["harvest_batches.harvested_by_key"] == 2
    assert "harvested_by_key" not in _stored(seeded, col.HARVEST_BATCHES, "hb-legacy")
