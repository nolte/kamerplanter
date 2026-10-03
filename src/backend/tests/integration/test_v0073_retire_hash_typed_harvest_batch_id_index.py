"""#2034 — v0073 drops the hash-typed ``batch_id`` index v0030 left on pre-June volumes.

The legacy index is created exactly as ``ensure_collections`` created it until
2026-06-07 (``{"type": "hash", ...}``); the database itself comes from today's
``ensure_collections``, so the unique+sparse replacement is present as on a
migrated volume.
"""

from __future__ import annotations

import pytest
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.migrations.versions.v0030_sparse_unique_harvest_batch_id import migration as v0030
from app.migrations.versions.v0073_retire_hash_typed_harvest_batch_id_index import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration drops an index on a real server"),
]

_DB_NAME = run_database_name("v0073_hash_batch_id_index")


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    yield database
    system.delete_database(_DB_NAME)


def _batch_id_indexes(db) -> list[tuple[str, bool, bool]]:
    return sorted(
        (idx["type"], bool(idx["unique"]), bool(idx["sparse"]))
        for idx in db.collection(col.HARVEST_BATCHES).indexes()
        if idx["fields"] == ["batch_id"]
    )


def _with_pre_june_index(db) -> None:
    db.collection(col.HARVEST_BATCHES).add_index({"type": "hash", "fields": ["batch_id"], "unique": True})


def test_the_hash_index_survives_v0030_and_is_dropped_here(db) -> None:
    batches = db.collection(col.HARVEST_BATCHES)
    _with_pre_june_index(db)
    batches.insert({"batch_id": None})
    v0030.up(db)
    assert ("hash", True, False) in _batch_id_indexes(db), "the gap v0030 left"
    with pytest.raises(DocumentInsertError):
        batches.insert({"batch_id": None})  # #740, still in force

    report = migration.up(db)

    assert _batch_id_indexes(db) == [("persistent", True, True)]
    assert report.changed == 1
    assert report.details["legacy_index_types"] == ["hash"]
    batches.insert({"batch_id": None})  # a second unlabelled batch is accepted now
    batches.insert({"batch_id": "LOT-1"})
    with pytest.raises(DocumentInsertError):
        batches.insert({"batch_id": "LOT-1"})  # the replacement still holds real labels unique


def test_a_second_run_is_a_no_op(db) -> None:
    _with_pre_june_index(db)
    migration.up(db)

    again = migration.up(db)

    assert again.changed == 0
    assert again.details["legacy_indexes"] == 0
    assert _batch_id_indexes(db) == [("persistent", True, True)]


def test_a_dry_run_counts_and_drops_nothing(db) -> None:
    _with_pre_june_index(db)

    report = migration.up(db, dry_run=True)

    assert report.changed == 0
    assert report.details["legacy_indexes"] == 1
    assert ("hash", True, False) in _batch_id_indexes(db)


def test_without_the_sparse_replacement_nothing_is_dropped(db) -> None:
    batches = db.collection(col.HARVEST_BATCHES)
    for idx in batches.indexes():
        if idx["fields"] == ["batch_id"]:
            batches.delete_index(idx["id"])
    _with_pre_june_index(db)

    report = migration.up(db)

    assert report.precondition_unmet is True
    assert report.details["replacement_indexes"] == 0
    assert _batch_id_indexes(db) == [("hash", True, False)]
