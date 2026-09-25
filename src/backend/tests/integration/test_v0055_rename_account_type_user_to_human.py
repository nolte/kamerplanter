"""Integration test for migration v0055 — ``account_type`` ``"user"`` → ``"human"`` (#1620).

The one thing the unit tier cannot decide is what the scan's ``!HAS(u,
"account_type")`` clause matches on a real server: a document inserted without the
attribute is the shape every account written before April 2026 has, and a double
would only restate my belief about ``HAS``. The rest is repeated here so the file
reads on its own.

Run with::

    docker run -d --rm --name kp-it-1620 -p 127.0.0.1:8529:8529 \\
      -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0055_rename_account_type_user_to_human.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.migrations.versions.v0055_rename_account_type_user_to_human import (
    NEW_VALUE,
    OLD_VALUE,
    RenameAccountTypeUserToHumanMigration,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the HAS() clause of the scan is the SUT"),
]

_DB_NAME = run_database_name("v0055_migration")

_OLD_DEFAULT = "u_stored_as_user"
_PRE_FIELD = "u_without_attribute"
_SERVICE = "u_service"
_ALREADY_HUMAN = "u_already_human"

_MUST_REWRITE = [_OLD_DEFAULT, _PRE_FIELD]
_MUST_KEEP = [_SERVICE, _ALREADY_HUMAN]


def _connect():
    from app.config.settings import Settings
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(Settings(arangodb_database=_DB_NAME))
    return conn, conn.connect()


@pytest.fixture
def db():
    from app.data_access.arango.collections import ensure_collections

    conn, database = _connect()
    ensure_collections(database)
    yield database
    conn.close()
    system = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)


@pytest.fixture
def seeded(db):
    """Four accounts: the two shapes to rewrite, and the two to leave alone."""
    users = db.collection(col.USERS)
    users.insert({"_key": _OLD_DEFAULT, "email": "erika@example.org", "account_type": OLD_VALUE})
    # Deliberately no ``account_type`` at all — a row from before the field existed.
    users.insert({"_key": _PRE_FIELD, "email": "april@example.org"})
    users.insert({"_key": _SERVICE, "email": "bot@example.org", "account_type": "service"})
    users.insert({"_key": _ALREADY_HUMAN, "email": "done@example.org", "account_type": NEW_VALUE})
    return db


def _stored(db, key: str) -> dict:
    doc = db.collection(col.USERS).get(key)
    assert doc is not None, f"user {key} disappeared"
    return doc


class TestTheRewrite:
    @pytest.mark.parametrize("key", _MUST_REWRITE)
    def test_both_shapes_are_rewritten_to_human(self, seeded, key):
        """The pre-field row is the reason this tier exists: ``HAS`` on a real document."""
        RenameAccountTypeUserToHumanMigration().up(seeded)

        assert _stored(seeded, key)["account_type"] == NEW_VALUE

    @pytest.mark.parametrize("key", _MUST_KEEP)
    def test_a_service_account_keeps_its_type(self, seeded, key):
        before = _stored(seeded, key)

        RenameAccountTypeUserToHumanMigration().up(seeded)

        after = _stored(seeded, key)
        assert after["account_type"] == before["account_type"]
        assert after["_rev"] == before["_rev"], "the row was written although nothing changed"

    def test_it_reports_exactly_the_rows_it_rewrote(self, seeded):
        report = RenameAccountTypeUserToHumanMigration().up(seeded)

        assert sorted(report.details["keys"]) == sorted(_MUST_REWRITE)
        assert report.changed == len(_MUST_REWRITE)
        assert report.scanned == 4


class TestTheRunItself:
    def test_a_dry_run_writes_nothing_and_reports_the_same_plan(self, seeded):
        dry = RenameAccountTypeUserToHumanMigration().up(seeded, dry_run=True)

        assert sorted(dry.details["keys"]) == sorted(_MUST_REWRITE)
        assert dry.changed == 0
        assert _stored(seeded, _OLD_DEFAULT)["account_type"] == OLD_VALUE
        assert "account_type" not in _stored(seeded, _PRE_FIELD)

    def test_it_is_idempotent(self, seeded):
        migration = RenameAccountTypeUserToHumanMigration()
        migration.up(seeded)

        second = migration.up(seeded)

        assert second.changed == 0, "the migration rediscovered its own output"
        assert second.details["keys"] == []
