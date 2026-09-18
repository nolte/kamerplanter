"""Integration test for migration v0051 — the CEC key rename (#1468).

The unit suite runs the migration against a double. Three things in this migration
are properties of ArangoDB itself and a double can only restate my belief about
them:

* **the removal.** The rename is a ``PATCH`` with ``cec_meq_per_100g: null`` and
  ``keep_none=False``; that the server *deletes* the attribute rather than storing
  a null is the entire mechanism, and ``HAS(d, "cec_meq_per_100g")`` afterwards is
  the only honest way to measure it;
* **the scan query.** It reads an attribute through a bind parameter
  (``d.@old``) and asks ``HAS(d, @old)`` with the same parameter — legal AQL, and
  not something a hand-written double can certify;
* **the defect itself.** ``Substrate.model_validate`` over a document as stored
  reads ``cec_meq_per_100cm3 is None`` before the migration and the stored number
  after. That is the round-trip #1468 asks for, and it is measured on documents
  that went through a real insert and a real update.

Run with::

    docker run -d --rm --name kp-it-1468 -p 8529:8529 \
      -e ARANGO_ROOT_PASSWORD=rootpassword arangodb:3.12
    pytest tests/integration/test_v0051_rename_cec_key.py -v
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.domain.models.substrate import Substrate
from app.migrations.versions.v0051_rename_cec_key import (
    _CATEGORIES,
    NEW_KEY,
    OLD_KEY,
    RenameCecKeyMigration,
)

# The server probe lives in tests/integration/conftest.py (``arango_db``).
pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("ArangoDB's own keepNull semantics and attribute-name bind parameters are the SUT"),
]

_DB_NAME = "kamerplanter_v0051_migration_test"

#: One document per category the migration reports, by ``_key``.
_SEEDED_OLD = "seeded_old"
_TENANT_MIX_OLD = "tenant_mix_old"
_BOTH_KEYS = "both_keys"
_ALREADY_NEW = "already_new"
_NO_CEC = "no_cec"
_OLD_NULL = "old_null"


def _connect():
    from app.config.settings import Settings
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(Settings(arangodb_database=_DB_NAME))
    return conn, conn.connect()


def _close(connection) -> None:
    """Close the client ``ArangoConnection`` opened — it owns one of its own."""
    connection.close()


def _substrate(key: str, **extra: Any) -> dict[str, Any]:
    """A substrate document as the repository writes one, plus the case's CEC."""
    return {
        "_key": key,
        "type": "soil",
        "name_de": f"Testsubstrat {key}",
        "name_en": f"Test substrate {key}",
        "tenant_key": "",
        "ph_base": 6.5,
        "ec_base_ms": 0.5,
        "water_retention": "medium",
        "buffer_capacity": "medium",
        **extra,
    }


@pytest.fixture
def db():
    """A freshly bootstrapped database — every collection and index production has."""
    from arango import ArangoClient

    from app.data_access.arango.collections import ensure_collections
    from tests.support.arango_integration import (
        ARANGO_PASSWORD,
        ARANGO_URL,
        ARANGO_USERNAME,
        SYSTEM_DATABASE,
    )

    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db(SYSTEM_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)

    connection, handle = _connect()
    ensure_collections(handle)
    yield handle

    # Two clients are open here: the probe client above and the one
    # ``ArangoConnection`` created. Both are closed, in that order — a leaked
    # session per test module is the sort of thing that only shows up as an
    # exhausted connection pool in a long run.
    _close(connection)
    system.delete_database(_DB_NAME)
    client.close()


@pytest.fixture
def population(db):
    """Insert one document per category and return the handle."""
    substrates = db.collection(col.SUBSTRATES)
    substrates.insert(_substrate(_SEEDED_OLD, **{OLD_KEY: 15.0}))
    substrates.insert(_substrate(_TENANT_MIX_OLD, tenant_key="mein-garten", is_mix=True, **{OLD_KEY: 6.0}))
    substrates.insert(_substrate(_BOTH_KEYS, **{OLD_KEY: 99.0, NEW_KEY: 12.0}))
    substrates.insert(_substrate(_ALREADY_NEW, **{NEW_KEY: 8.5}))
    substrates.insert(_substrate(_NO_CEC))
    substrates.insert(_substrate(_OLD_NULL, **{OLD_KEY: None}))
    return db


def _stored(db, key: str) -> dict[str, Any]:
    doc = db.collection(col.SUBSTRATES).get(key)
    assert doc is not None, f"{key} vanished"
    return doc


def _has_attribute(db, key: str, attribute: str) -> bool:
    """Ask the server, not the driver: an absent attribute and a stored ``null``
    are different documents, and only ``HAS`` tells them apart."""
    query = f"FOR d IN {col.SUBSTRATES} FILTER d._key == @key RETURN HAS(d, @attribute)"
    return list(db.aql.execute(query, bind_vars={"key": key, "attribute": attribute}))[0]


class TestTheDefectThisMigrationFixes:
    def test_a_document_with_the_old_key_reads_as_no_cec_at_all(self, population):
        """The failure #1468 reports, measured on a stored document.

        Red before the migration by construction — this is the state every
        database seeded before #1174 is in.
        """
        before = Substrate.model_validate(_stored(population, _SEEDED_OLD))

        assert before.cec_meq_per_100cm3 is None

    def test_the_same_document_carries_its_cec_after_the_migration(self, population):
        RenameCecKeyMigration().up(population)

        after = Substrate.model_validate(_stored(population, _SEEDED_OLD))

        assert after.cec_meq_per_100cm3 == 15.0


class TestTheRename:
    def test_the_value_moves_and_the_old_attribute_is_removed(self, population):
        """``keep_none=False`` must *delete* the attribute, not store a null."""
        RenameCecKeyMigration().up(population)

        assert _stored(population, _SEEDED_OLD)[NEW_KEY] == 15.0
        assert not _has_attribute(population, _SEEDED_OLD, OLD_KEY)

    def test_a_tenant_owned_mix_is_renamed_too(self, population):
        """The scope decision, asserted: this migration has no tenant filter.

        v0047/v0049 write catalogue *values* and stop at ``tenant_key == ""``. A
        key that moved moved for everyone, and a tenant mix stored before #1174
        reads as ``None`` for its owner exactly like a seed record.
        """
        RenameCecKeyMigration().up(population)

        doc = _stored(population, _TENANT_MIX_OLD)
        assert doc[NEW_KEY] == 6.0
        assert not _has_attribute(population, _TENANT_MIX_OLD, OLD_KEY)

    def test_a_stored_null_loses_the_old_name_without_gaining_a_new_one(self, population):
        """``cec_meq_per_100g: null`` says "no CEC" and keeps saying it.

        The model reads an absent ``cec_meq_per_100cm3`` as ``None``, so the
        document's meaning is unchanged; what must not survive is the abandoned
        attribute name.
        """
        RenameCecKeyMigration().up(population)

        assert not _has_attribute(population, _OLD_NULL, OLD_KEY)
        assert Substrate.model_validate(_stored(population, _OLD_NULL)).cec_meq_per_100cm3 is None

    def test_nothing_else_about_the_document_changes(self, population):
        before = _stored(population, _SEEDED_OLD)
        untouched = {k: v for k, v in before.items() if k not in {OLD_KEY, "_rev"}}

        RenameCecKeyMigration().up(population)

        after = _stored(population, _SEEDED_OLD)
        assert {k: v for k, v in after.items() if k not in {NEW_KEY, "_rev"}} == untouched


class TestTheConflictCase:
    def test_a_document_with_both_keys_is_left_exactly_as_it_was(self, population):
        before = _stored(population, _BOTH_KEYS)

        RenameCecKeyMigration().up(population)

        after = _stored(population, _BOTH_KEYS)
        assert after[NEW_KEY] == 12.0
        assert after[OLD_KEY] == 99.0
        assert after["_rev"] == before["_rev"], "the conflict case must not be written at all"

    def test_it_is_named_in_the_report(self, population):
        """Named with both numbers: the operator is the only one who can decide
        which is right, and they cannot decide about a row they cannot see."""
        stored = _stored(population, _BOTH_KEYS)

        report = RenameCecKeyMigration().up(population)

        assert report.details["both_keys_present_total"] == 1
        row = report.details["both_keys_present"][0]
        assert _BOTH_KEYS in row
        assert repr(stored[OLD_KEY]) in row
        assert repr(stored[NEW_KEY]) in row


class TestTheReport:
    def test_every_scanned_document_lands_in_exactly_one_category(self, population):
        report = RenameCecKeyMigration().up(population)

        totals = {category: report.details[f"{category}_total"] for category in _CATEGORIES}
        assert totals == {
            "renamed": 2,
            "old_key_dropped_without_value": 1,
            "both_keys_present": 1,
            "already_correct": 1,
            "no_cec_stored": 1,
        }
        assert sum(totals.values()) == report.scanned == 6
        assert report.changed == 3
        assert report.details["write_failed_total"] == 0

    def test_a_dry_run_reports_the_same_plan_and_writes_nothing(self, population):
        revisions = {key: _stored(population, key)["_rev"] for key in (_SEEDED_OLD, _TENANT_MIX_OLD, _OLD_NULL)}

        report = RenameCecKeyMigration().up(population, dry_run=True)

        assert report.dry_run is True
        assert report.changed == 0
        assert report.details["renamed_total"] == 2
        assert report.details["old_key_dropped_without_value_total"] == 1
        assert {key: _stored(population, key)["_rev"] for key in revisions} == revisions
        assert _has_attribute(population, _SEEDED_OLD, OLD_KEY)


class TestIdempotence:
    def test_a_second_run_writes_nothing_and_reports_the_records_as_correct(self, population):
        migration = RenameCecKeyMigration()
        migration.up(population)

        second = migration.up(population)

        assert second.changed == 0
        assert second.noop is True
        assert second.details["renamed_total"] == 0
        assert second.details["old_key_dropped_without_value_total"] == 0
        # The two documents that carried a number, plus the one that already had
        # the new key. The third write was a stored ``null``: it lost the old
        # attribute and gained no new one, so it re-reads as ``no_cec_stored`` —
        # the same thing the model reads as ``None`` either way.
        assert second.details["already_correct_total"] == 3
        assert second.details["no_cec_stored_total"] == 2
        assert second.details["both_keys_present_total"] == 1


class TestAnEmptyInstallation:
    def test_an_empty_collection_is_a_no_op(self, db):
        report = RenameCecKeyMigration().up(db)

        assert report.scanned == 0
        assert report.changed == 0
