"""Integration test for migration v0054 — the credential left on soft-deleted accounts.

Everything this migration turns on is a property of ArangoDB itself, so a double
could only restate my belief about it:

* **the removal.** The strip is an ``UPDATE`` with ``password_hash: null`` and
  ``keep_none=False``; that the server *deletes* the attribute rather than storing a
  null is the whole mechanism, and ``field not in stored`` afterwards is the only
  honest way to measure it — the same claim #1525's repository change rests on.
* **the scoping query.** It joins ``users`` to ``erasure_requests`` and escapes AQL's
  single-character wildcard in ``LIKE(u.email, "deleted\\_%@…")``. A hand-written
  double would answer whatever I believed that escape does, which is exactly the
  failure class the escape was introduced for.
* **what must NOT be touched.** ``is_active == false`` is not the population:
  a platform admin can deactivate an account through ``PATCH
  /admin/platform/users/{key}`` and that is **reversible**. Stripping such an
  account's password would lock its owner out permanently and silently — a data-loss
  bug wearing a security fix's clothes. That negative is the most important assertion
  in this file and it has to be measured against the real filter.

Run with::

    docker run -d --rm --name kp-it-1525 -p 8529:8529 \\
      -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0054_strip_soft_deleted_credentials.py -v
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.migrations.versions.v0054_strip_credentials_from_soft_deleted_accounts import (
    StripCredentialsFromSoftDeletedAccountsMigration,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("keepNull removal and the LIKE-escaped join are the SUT"),
]

_DB_NAME = run_database_name("v0054_migration")
_HASH = "$2b$12$abcdefghijklmnopqrstuv0123456789ABCDEFGHIJKLMNOPQRSTU"
_AVATAR = "https://cdn.example.org/avatars/erika.png"

#: One user per case, by ``_key``.
_ERASURE_REQUESTED = "u_erasure_requested"
_TOMBSTONED_NEW = "u_tombstoned_new_domain"
_TOMBSTONED_LEGACY = "u_tombstoned_legacy_domain"
_ADMIN_DEACTIVATED = "u_admin_deactivated"
_ACTIVE = "u_active"
_ALREADY_STRIPPED = "u_already_stripped"

#: The accounts the migration must strip, and the ones it must leave alone.
_MUST_STRIP = [_ERASURE_REQUESTED, _TOMBSTONED_NEW, _TOMBSTONED_LEGACY]
_MUST_KEEP = [_ADMIN_DEACTIVATED, _ACTIVE]


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
    """Six accounts spanning every branch of the scoping filter."""
    users = db.collection(col.USERS)
    users.insert(
        {
            "_key": _ERASURE_REQUESTED,
            # Deliberately the user's *real* address: `request_erasure` never
            # rewrote the email, which is why the account stayed reachable.
            "email": "erika@example.org",
            "display_name": "Erika",
            "is_active": False,
            "password_hash": _HASH,
            "avatar_url": _AVATAR,
        }
    )
    users.insert(
        {
            "_key": _TOMBSTONED_NEW,
            "email": f"deleted_{_TOMBSTONED_NEW}@deleted.example.com",
            "display_name": "Deleted User",
            "is_active": False,
            "password_hash": _HASH,
        }
    )
    users.insert(
        {
            "_key": _TOMBSTONED_LEGACY,
            "email": f"deleted_{_TOMBSTONED_LEGACY}@deleted.local",
            "display_name": "Deleted User",
            "is_active": False,
            "password_hash": _HASH,
        }
    )
    users.insert(
        {
            "_key": _ADMIN_DEACTIVATED,
            # A suspension, not a deletion: no erasure request, ordinary address.
            "email": "suspended@example.org",
            "display_name": "Suspended",
            "is_active": False,
            "password_hash": _HASH,
            "avatar_url": _AVATAR,
        }
    )
    users.insert(
        {
            "_key": _ACTIVE,
            "email": "active@example.org",
            "display_name": "Active",
            "is_active": True,
            "password_hash": _HASH,
            "avatar_url": _AVATAR,
        }
    )
    users.insert(
        {
            "_key": _ALREADY_STRIPPED,
            "email": f"deleted_{_ALREADY_STRIPPED}@deleted.example.com",
            "display_name": "Deleted User",
            "is_active": False,
        }
    )
    db.collection(col.ERASURE_REQUESTS).insert(
        {"user_key": _ERASURE_REQUESTED, "status": "scheduled", "requested_at": "2026-08-01T00:00:00+00:00"}
    )
    return db


def _stored(db, key: str) -> dict:
    doc = db.collection(col.USERS).get(key)
    assert doc is not None, f"user {key} disappeared"
    return doc


class TestTheStrip:
    @pytest.mark.parametrize("key", _MUST_STRIP)
    def test_the_credential_attributes_are_removed_not_nulled(self, seeded, key):
        """``field not in stored`` — a stored ``null`` would be a different outcome.

        It is the outcome #1525's repository produces for a freshly deleted account,
        so a repaired legacy row has to be indistinguishable from a new one; anything
        else leaves two shapes in the collection and the scan able to rediscover its
        own output.
        """
        StripCredentialsFromSoftDeletedAccountsMigration().up(seeded)

        stored = _stored(seeded, key)
        assert "password_hash" not in stored, "the soft-deleted account kept its credential"
        assert "avatar_url" not in stored

    def test_it_reports_exactly_the_accounts_it_stripped(self, seeded):
        report = StripCredentialsFromSoftDeletedAccountsMigration().up(seeded)

        assert sorted(report.details["keys"]) == sorted(_MUST_STRIP)
        assert report.changed == len(_MUST_STRIP)
        assert report.scanned == 6

    def test_the_report_never_carries_the_credential(self, seeded):
        """A migration report is logged and stored; the hash may not travel in it."""
        report = StripCredentialsFromSoftDeletedAccountsMigration().up(seeded)

        assert _HASH not in repr(report.details)


class TestWhatItMustNotTouch:
    @pytest.mark.parametrize("key", _MUST_KEEP)
    def test_an_account_that_was_not_deleted_keeps_its_password(self, seeded, key):
        """The dangerous case: admin deactivation is reversible.

        Red against a migration scoped on ``is_active == false`` alone — the obvious
        filter, and the one that silently locks out every suspended user.
        """
        StripCredentialsFromSoftDeletedAccountsMigration().up(seeded)

        stored = _stored(seeded, key)
        assert stored["password_hash"] == _HASH
        assert stored["avatar_url"] == _AVATAR

    def test_the_other_fields_of_a_stripped_account_survive(self, seeded):
        """A strip, not a wipe: the row must still read as the account it was."""
        StripCredentialsFromSoftDeletedAccountsMigration().up(seeded)

        stored = _stored(seeded, _ERASURE_REQUESTED)
        assert stored["email"] == "erika@example.org"
        assert stored["display_name"] == "Erika"
        assert stored["is_active"] is False


class TestTheRunItself:
    def test_a_dry_run_writes_nothing_and_reports_the_same_plan(self, seeded):
        migration = StripCredentialsFromSoftDeletedAccountsMigration()

        dry = migration.up(seeded, dry_run=True)

        assert sorted(dry.details["keys"]) == sorted(_MUST_STRIP)
        assert dry.changed == 0
        assert _stored(seeded, _ERASURE_REQUESTED)["password_hash"] == _HASH

    def test_it_is_idempotent(self, seeded):
        migration = StripCredentialsFromSoftDeletedAccountsMigration()
        migration.up(seeded)

        second = migration.up(seeded)

        assert second.changed == 0, "the migration rediscovered its own output"
        assert second.details["keys"] == []

    def test_an_already_stripped_account_is_not_in_the_plan(self, seeded):
        """The filter matches documents that still *have* the attribute."""
        plan = StripCredentialsFromSoftDeletedAccountsMigration().up(seeded, dry_run=True)

        assert _ALREADY_STRIPPED not in plan.details["keys"]
