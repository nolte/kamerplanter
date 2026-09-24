"""Integration test for migration v0058 — the explicit empty species relation (#1618).

What the migration turns on is ArangoDB's own behaviour: ``!IS_ARRAY(doc.@field)``
must select a plan whose attribute is absent **and** one that stores ``null``,
and must leave both a linked list and a deliberately empty list alone. A fake
cannot tell those apart from the Python side, so they are measured here, together
with idempotency on the real store.

Run with::

    docker run -d --rm -p 8529:8529 -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0058_stamp_nutrient_plan_species_relation.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.migrations.versions.v0058_stamp_nutrient_plan_species_relation import migration
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("IS_ARRAY and bind-attribute semantics are the SUT"),
]

_DB_NAME = run_database_name("v0058_migration")

TOMATO = "solanum-lycopersicum"


@pytest.fixture
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    database = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    database.create_collection(col.NUTRIENT_PLANS)
    database.collection(col.NUTRIENT_PLANS).insert_many(
        [
            {"_key": "plan-legacy", "name": "Tomate — Plagron Terra", "tags": ["tomate"]},
            {"_key": "plan-null", "name": "Null", "species_keys": None},
            {"_key": "plan-linked", "name": "Linked", "species_keys": [TOMATO]},
            {"_key": "plan-empty", "name": "Empty", "species_keys": []},
        ]
    )
    yield database
    system.delete_database(_DB_NAME)


def _relation(db, key: str):
    return db.collection(col.NUTRIENT_PLANS).get(key).get("species_keys", "<absent>")


def test_absent_and_null_relations_become_empty_and_lists_are_untouched(db) -> None:
    report = migration.up(db)

    assert report.changed == 2
    assert _relation(db, "plan-legacy") == []
    assert _relation(db, "plan-null") == []
    assert _relation(db, "plan-linked") == [TOMATO]
    assert _relation(db, "plan-empty") == []


def test_no_species_is_derived_from_the_plan_name(db) -> None:
    migration.up(db)

    assert _relation(db, "plan-legacy") == []


def test_the_second_run_changes_nothing(db) -> None:
    migration.up(db)

    report = migration.up(db)

    assert report.changed == 0
    assert report.scanned == 4


def test_dry_run_writes_nothing(db) -> None:
    report = migration.up(db, dry_run=True)

    assert report.details == {"stamped": 2}
    assert _relation(db, "plan-legacy") == "<absent>"
    assert _relation(db, "plan-null") is None
