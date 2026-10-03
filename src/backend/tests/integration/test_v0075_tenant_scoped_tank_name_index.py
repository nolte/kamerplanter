"""#2029 — v0075 moves the tank name index from collection-wide to per tenant.

The database comes from today's ``ensure_collections``; the legacy index is then
added exactly as the shipped code created it, in both spellings a volume can carry:

* ``hash`` — ``tanks_col.add_hash_index(fields=["name"], unique=True)`` until
  2026-06-07 (``516bcd832^:src/backend/app/data_access/arango/collections.py:1118``);
  ArangoDB 3.12 reports it as ``type: "hash"``;
* ``persistent`` — ``tanks_col.add_persistent_index(fields=["name"], unique=True)``
  from then until #2029.

Each variant first proves the legacy constraint is in force (tenant B refused A's
name), so a green run after the migration is not the absence of the setup.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.migrations.versions import v0075_tenant_scoped_tank_name_index as module
from app.migrations.versions.v0075_tenant_scoped_tank_name_index import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration replaces an index on a real server"),
]

_DB_NAME = run_database_name("v0075_tank_name_index")


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    yield database
    system.delete_database(_DB_NAME)


def _hash_legacy(db: StandardDatabase) -> None:
    db.collection(col.TANKS).add_index({"type": "hash", "fields": ["name"], "unique": True})


def _persistent_legacy(db: StandardDatabase) -> None:
    db.collection(col.TANKS).add_index({"type": "persistent", "fields": ["name"], "unique": True})


LEGACY_VARIANTS = [
    pytest.param(_hash_legacy, "hash", id="pre-june-hash"),
    pytest.param(_persistent_legacy, "persistent", id="persistent"),
]


def _drop_compound(db: StandardDatabase) -> None:
    """The shape of a volume before #2029: ``ensure_collections`` never created the compound."""
    tanks = db.collection(col.TANKS)
    for idx in tanks.indexes():
        if idx.get("fields") == col.TANK_NAME_INDEX_FIELDS:
            tanks.delete_index(idx["id"])


def _name_indexes(db: StandardDatabase) -> list[tuple[str, tuple[str, ...], bool]]:
    return sorted(
        (idx["type"], tuple(idx["fields"]), bool(idx["unique"]))
        for idx in db.collection(col.TANKS).indexes()
        if "name" in idx.get("fields", [])
    )


def _tank(tenant: str, name: str = "Tank 1") -> dict[str, str]:
    return {"tenant_key": tenant, "name": name, "tank_type": "nutrient"}


@pytest.mark.parametrize(("legacy", "legacy_type"), LEGACY_VARIANTS)
def test_after_the_migration_two_tenants_share_a_name_and_one_tenant_does_not(
    db: StandardDatabase, legacy: Callable[[StandardDatabase], None], legacy_type: str
) -> None:
    tanks = db.collection(col.TANKS)
    _drop_compound(db)
    legacy(db)
    tanks.insert(_tank("tenant-a"))
    with pytest.raises(DocumentInsertError):
        tanks.insert(_tank("tenant-b"))  # the defect, in force before the migration

    report = migration.up(db)

    assert report.precondition_unmet is False
    assert report.details["compound_created"] is True
    assert report.details["legacy_index_types"] == [legacy_type]
    assert report.changed == 2  # one index created, one dropped
    assert _name_indexes(db) == [("persistent", ("tenant_key", "name"), True)]
    tanks.insert(_tank("tenant-b"))
    with pytest.raises(DocumentInsertError):
        tanks.insert(_tank("tenant-a"))  # the same tenant is still refused


@pytest.mark.parametrize(("legacy", "legacy_type"), LEGACY_VARIANTS)
def test_on_a_booted_volume_the_compound_is_kept_and_only_the_legacy_index_goes(
    db: StandardDatabase, legacy: Callable[[StandardDatabase], None], legacy_type: str
) -> None:
    legacy(db)  # today's ensure_collections already created the compound

    report = migration.up(db)

    assert report.details["compound_created"] is False
    assert report.details["legacy_index_types"] == [legacy_type]
    assert report.changed == 1
    assert _name_indexes(db) == [("persistent", ("tenant_key", "name"), True)]


@pytest.mark.parametrize(("legacy", "legacy_type"), LEGACY_VARIANTS)
def test_a_second_run_is_a_no_op(
    db: StandardDatabase, legacy: Callable[[StandardDatabase], None], legacy_type: str
) -> None:
    del legacy_type
    _drop_compound(db)
    legacy(db)
    migration.up(db)
    before = _name_indexes(db)

    again = migration.up(db)

    assert again.changed == 0
    assert again.details["legacy_indexes"] == 0
    assert again.details["compound_created"] is False
    assert _name_indexes(db) == before


@pytest.mark.parametrize(("legacy", "legacy_type"), LEGACY_VARIANTS)
def test_a_dry_run_writes_nothing(
    db: StandardDatabase, legacy: Callable[[StandardDatabase], None], legacy_type: str
) -> None:
    _drop_compound(db)
    legacy(db)
    before = _name_indexes(db)

    report = migration.up(db, dry_run=True)

    assert report.dry_run is True
    assert report.changed == 0
    assert report.precondition_unmet is False  # the real run creates the replacement first
    assert report.details["compound_to_create"] is True
    assert report.details["legacy_indexes"] == 1
    assert report.details["legacy_index_types"] == [legacy_type]
    assert _name_indexes(db) == before == [(legacy_type, ("name",), True)]


@pytest.mark.parametrize(("legacy", "legacy_type"), LEGACY_VARIANTS)
def test_without_the_replacement_nothing_is_dropped(
    db: StandardDatabase,
    legacy: Callable[[StandardDatabase], None],
    legacy_type: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The drop is gated on the re-read index list, not on the creation call having run."""
    _drop_compound(db)
    legacy(db)
    monkeypatch.setattr(module, "_create_replacement", lambda _tanks: None)

    report = migration.up(db)

    assert report.precondition_unmet is True
    assert report.changed == 0
    assert report.details["replacement_indexes"] == 0
    assert report.details["legacy_indexes"] == 1
    assert _name_indexes(db) == [(legacy_type, ("name",), True)]
