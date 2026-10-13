"""#2065 — v0079 moves instance_id, batch_id and slot_id from collection-wide to their owner.

The database comes from today's ``ensure_collections``; the legacy indexes are then
added as shipped code created them: ``add_persistent_index(fields=["instance_id"] /
["slot_id"], unique=True)`` and, since v0030, ``["batch_id"]`` unique **sparse** — and,
for a pre-June volume, ``instance_id`` / ``slot_id`` typed ``hash`` (measured on 3.12.8:
the pre-June image's ``add_hash_index`` calls left exactly these beside today's).

Each variant first proves the legacy constraint is in force (a second owner refused),
so a green run after the migration is not the absence of the setup.
"""

from __future__ import annotations

import pytest
from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.migrations.versions import v0079_tenant_scoped_identifier_indexes as module
from app.migrations.versions.v0079_tenant_scoped_identifier_indexes import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration replaces indexes on a real server"),
]

_DB_NAME = run_database_name("v0079_identifier_indexes")

#: ``collection -> (the same label under owner 1, under owner 2)``.
_ROWS = {
    col.PLANT_INSTANCES: ({"tenant_key": "ta", "instance_id": "P-1"}, {"tenant_key": "tb", "instance_id": "P-1"}),
    col.HARVEST_BATCHES: ({"tenant_key": "ta", "batch_id": "LOT-1"}, {"tenant_key": "tb", "batch_id": "LOT-1"}),
    col.SLOTS: ({"location_key": "loc-a", "slot_id": "T_A1"}, {"location_key": "loc-b", "slot_id": "T_A1"}),
}


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    yield database
    system.delete_database(_DB_NAME)


def _drop_compounds(db: StandardDatabase) -> None:
    """The shape of a volume before #2065: no compound index."""
    for name, fields in _SCOPED.items():
        handle = db.collection(name)
        for idx in handle.indexes():
            if tuple(idx.get("fields") or ()) == fields:
                handle.delete_index(idx["id"])


#: The legacy indexes as the shipped ``ensure_collections`` created them — spelled out,
#: not read from the migration under test: ``collection -> (fields, sparse)``.
_LEGACY = {
    col.PLANT_INSTANCES: (["instance_id"], False),
    col.HARVEST_BATCHES: (["batch_id"], True),  # sparse since v0030 (#740)
    col.SLOTS: (["slot_id"], False),
}

#: Today's scoped indexes, as ``ensure_collections`` creates them.
_SCOPED = {
    col.PLANT_INSTANCES: ("tenant_key", "instance_id"),
    col.HARVEST_BATCHES: ("tenant_key", "batch_id"),
    col.SLOTS: ("location_key", "slot_id"),
}


def _add_legacy(db: StandardDatabase, index_type: str) -> None:
    for name, (fields, sparse) in _LEGACY.items():
        # v0030 made the label index sparse after June: there is no hash-typed sparse one.
        kind = "persistent" if sparse else index_type
        db.collection(name).add_index({"type": kind, "fields": fields, "unique": True, "sparse": sparse})


def _shapes(db: StandardDatabase, name: str) -> list[tuple[str, ...]]:
    field = _LEGACY[name][0][-1]
    return sorted(tuple(i["fields"]) for i in db.collection(name).indexes() if field in i.get("fields", []))


@pytest.mark.parametrize("index_type", ["persistent", "hash"])
def test_after_the_migration_two_owners_share_a_label_and_one_owner_does_not(db, index_type: str) -> None:
    _drop_compounds(db)
    _add_legacy(db, index_type)
    for name, (first, second) in _ROWS.items():
        db.collection(name).insert(dict(first))
        with pytest.raises(DocumentInsertError):
            db.collection(name).insert(dict(second))  # the defect, in force before the migration

    report = migration.up(db)

    assert report.precondition_unmet is False
    assert report.changed == 6  # three compounds created, three legacy indexes dropped
    for name, (first, second) in _ROWS.items():
        assert _shapes(db, name) == [_SCOPED[name]], name
        db.collection(name).insert(dict(second))
        with pytest.raises(DocumentInsertError):
            db.collection(name).insert(dict(first))  # the same owner is still refused


def test_on_a_booted_volume_only_the_legacy_indexes_go(db) -> None:
    _add_legacy(db, "persistent")  # today's ensure_collections already created the compounds

    report = migration.up(db)

    assert report.changed == 3
    assert all(not d["compound_created"] for d in report.details["collections"].values())


def test_unlabelled_batches_stay_outside_the_constraint(db) -> None:
    _add_legacy(db, "persistent")
    migration.up(db)
    batches = db.collection(col.HARVEST_BATCHES)

    batches.insert({"tenant_key": "ta", "batch_id": None})
    batches.insert({"tenant_key": "ta", "batch_id": None})

    assert batches.count() == 2


def test_a_second_run_is_a_no_op(db) -> None:
    _drop_compounds(db)
    _add_legacy(db, "hash")
    migration.up(db)

    again = migration.up(db)

    assert again.changed == 0
    assert again.precondition_unmet is False


def test_a_dry_run_touches_no_index(db) -> None:
    _drop_compounds(db)
    _add_legacy(db, "persistent")
    before = {name: _shapes(db, name) for name in _LEGACY}

    report = migration.up(db, dry_run=True)

    assert report.changed == 0
    assert report.precondition_unmet is False
    assert {name: _shapes(db, name) for name in _LEGACY} == before


def test_without_a_replacement_nothing_is_dropped_and_the_version_stays_pending(db, monkeypatch) -> None:
    _drop_compounds(db)
    _add_legacy(db, "persistent")
    monkeypatch.setattr(module, "_create_replacement", lambda collection, target: None)

    report = migration.up(db)

    assert report.precondition_unmet is True
    for name, (fields, _sparse) in _LEGACY.items():
        assert _shapes(db, name) == [tuple(fields)]
