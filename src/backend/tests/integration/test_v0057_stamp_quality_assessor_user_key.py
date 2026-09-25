"""Integration test for migration v0057 — the explicit ``null`` on pre-#1663 quality assessments.

As for v0056, what this migration turns on is ArangoDB's own behaviour:
``FILTER !HAS(doc, @field)`` selects a document that *lacks* the attribute and not
one carrying ``null``, and ``update(..., keep_none=True)`` makes the ``null`` land.
The one negative that matters is measured here too: a legacy row whose free-text
``assessed_by`` is **literally an existing user key** still gets ``null``.

Run with::

    docker run -d --rm -p 127.0.0.1:8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0057_stamp_quality_assessor_user_key.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.migrations.versions.v0057_stamp_quality_assessor_user_key import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("!HAS and keepNull semantics are the SUT"),
]

_DB_NAME = run_database_name("v0057_migration")

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
    database.create_collection(col.QUALITY_ASSESSMENTS)
    yield database
    system.delete_database(_DB_NAME)


@pytest.fixture
def seeded(db):
    db.collection(col.QUALITY_ASSESSMENTS).insert_many(
        [
            {"_key": "qa-legacy", "batch_key": "hb-1", "assessed_by": "Maren"},
            {"_key": "qa-name-is-a-key", "batch_key": "hb-1", "assessed_by": USER},
            {"_key": "qa-keyed", "batch_key": "hb-2", "assessed_by": "Maren", "assessed_by_key": USER},
        ]
    )
    return db


def _stored(db, key: str) -> dict:
    return dict(db.collection(col.QUALITY_ASSESSMENTS).get(key))


def test_legacy_rows_carry_an_explicit_null_and_keyed_rows_are_untouched(seeded):
    report = migration.up(seeded)

    assert report.changed == 2
    for key in ("qa-legacy", "qa-name-is-a-key"):
        stored = _stored(seeded, key)
        assert "assessed_by_key" in stored, f"{key}: the attribute was dropped instead of stamped null"
        assert stored["assessed_by_key"] is None
    assert _stored(seeded, "qa-keyed")["assessed_by_key"] == USER


def test_a_free_text_that_equals_a_user_key_is_not_promoted_to_the_key(seeded):
    """The forbidden backfill, against the real store."""
    migration.up(seeded)

    stored = _stored(seeded, "qa-name-is-a-key")
    assert stored["assessed_by_key"] is None
    assert stored["assessed_by"] == USER, "the free text itself is not touched either"


def test_a_second_run_finds_nothing(seeded):
    """M-3 against ``!HAS``: a stamped ``null`` is *present*, so it is not rediscovered."""
    first = migration.up(seeded)
    second = migration.up(seeded)

    assert first.changed == 2
    assert second.changed == 0
    assert second.noop is True


def test_dry_run_writes_nothing(seeded):
    report = migration.up(seeded, dry_run=True)

    assert report.changed == 0
    assert report.details["stamped"]["quality_assessments.assessed_by_key"] == 2
    assert "assessed_by_key" not in _stored(seeded, "qa-legacy")
