"""#2027 — v0076 moves the activity name index from collection-wide to per tenant.

The database comes from today's ``ensure_collections``; the legacy index is then
added exactly as the shipped code created it, in every spelling a volume can carry:

* ``hash`` — ``activities_col.add_hash_index(fields=["name"], unique=True)`` until 2026-06-07
  (``516bcd832^:src/backend/app/data_access/arango/collections.py:1246``);
  ArangoDB 3.12 reports it as ``type: "hash"``;
* ``persistent`` — ``add_persistent_index(fields=["name"], unique=True)`` from then
  until #2027;
* ``hash`` **plus** a ``persistent`` twin — the real state of a pre-June volume that
  booted the later code: the identical definition created a second index (#2034).

Each variant first proves the legacy constraint is in force (a tenant refused the
global row's name), so a green run after the migration is not the absence of the setup.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.migrations.versions import v0076_tenant_scoped_activity_name_index as module
from app.migrations.versions.v0076_tenant_scoped_activity_name_index import migration
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the migration replaces an index on a real server"),
]

_DB_NAME = run_database_name("v0076_activity_name_index")
_COLLECTION = col.ACTIVITIES
_COMPOUND = col.ACTIVITY_NAME_INDEX_FIELDS
GLOBAL = ""
TENANT = "t-grower"


@pytest.fixture
def db():
    system, database = create_database(_DB_NAME)
    yield database
    system.delete_database(_DB_NAME)


def _hash_legacy(db: StandardDatabase) -> None:
    db.collection(_COLLECTION).add_index({"type": "hash", "fields": ["name"], "unique": True})


def _persistent_legacy(db: StandardDatabase) -> None:
    db.collection(_COLLECTION).add_index({"type": "persistent", "fields": ["name"], "unique": True})


def _hash_with_persistent_twin(db: StandardDatabase) -> None:
    """The real pre-June volume after a later boot (#2034, measured on 3.12.8)."""
    _hash_legacy(db)
    _persistent_legacy(db)
    assert len([idx for idx in db.collection(_COLLECTION).indexes() if idx.get("fields") == ["name"]]) == 2, (
        "the server returned the hash index instead of creating a twin"
    )


#: ``(create the legacy state, the index types the server then reports)``.
LEGACY_VARIANTS = [
    pytest.param(_hash_legacy, ["hash"], id="pre-june-hash"),
    pytest.param(_persistent_legacy, ["persistent"], id="persistent"),
    pytest.param(_hash_with_persistent_twin, ["hash", "persistent"], id="hash+persistent"),
]


def _drop_compound(db: StandardDatabase) -> None:
    """The shape of a volume before #2027: ``ensure_collections`` never created the compound."""
    target = db.collection(_COLLECTION)
    for idx in target.indexes():
        if idx.get("fields") == _COMPOUND:
            target.delete_index(idx["id"])


def _name_indexes(db: StandardDatabase) -> list[tuple[str, tuple[str, ...], bool]]:
    return sorted(
        (idx["type"], tuple(idx["fields"]), bool(idx["unique"]))
        for idx in db.collection(_COLLECTION).indexes()
        if "name" in idx.get("fields", [])
    )


def _legacy_rows(legacy_types: list[str]) -> list[tuple[str, tuple[str, ...], bool]]:
    return sorted((t, ("name",), True) for t in legacy_types)


def _row(tenant: str, name: str = "Topping") -> dict[str, str]:
    return {"tenant_key": tenant, "name": name}


@pytest.mark.parametrize(("legacy", "legacy_types"), LEGACY_VARIANTS)
def test_after_the_migration_a_tenant_shares_the_global_name_and_one_scope_does_not(
    db: StandardDatabase, legacy: Callable[[StandardDatabase], None], legacy_types: list[str]
) -> None:
    target = db.collection(_COLLECTION)
    _drop_compound(db)
    legacy(db)
    target.insert(_row(GLOBAL))
    with pytest.raises(DocumentInsertError):
        target.insert(_row(TENANT))  # the defect, in force before the migration

    report = migration.up(db)

    assert report.precondition_unmet is False
    assert report.details["compound_created"] is True
    assert report.details["legacy_index_types"] == legacy_types
    assert report.details["legacy_indexes_dropped"] == len(legacy_types)
    assert report.changed == 1 + len(legacy_types)  # the compound created, every legacy index dropped
    assert _name_indexes(db) == [("persistent", ("tenant_key", "name"), True)]
    target.insert(_row(TENANT))
    target.insert(_row("t-other"))
    with pytest.raises(DocumentInsertError):
        target.insert(_row(TENANT))  # the same tenant is still refused
    with pytest.raises(DocumentInsertError):
        target.insert(_row(GLOBAL))  # and so is a second global row


@pytest.mark.parametrize(("legacy", "legacy_types"), LEGACY_VARIANTS)
def test_on_a_booted_volume_the_compound_is_kept_and_only_the_legacy_index_goes(
    db: StandardDatabase, legacy: Callable[[StandardDatabase], None], legacy_types: list[str]
) -> None:
    legacy(db)  # today's ensure_collections already created the compound

    report = migration.up(db)

    assert report.details["compound_created"] is False
    assert report.details["legacy_index_types"] == legacy_types
    assert report.changed == len(legacy_types)
    assert _name_indexes(db) == [("persistent", ("tenant_key", "name"), True)]


@pytest.mark.parametrize(("legacy", "legacy_types"), LEGACY_VARIANTS)
def test_a_second_run_is_a_no_op(
    db: StandardDatabase, legacy: Callable[[StandardDatabase], None], legacy_types: list[str]
) -> None:
    del legacy_types
    _drop_compound(db)
    legacy(db)
    migration.up(db)
    before = _name_indexes(db)

    again = migration.up(db)

    assert again.changed == 0
    assert again.details["legacy_indexes"] == 0
    assert again.details["compound_created"] is False
    assert _name_indexes(db) == before


@pytest.mark.parametrize(("legacy", "legacy_types"), LEGACY_VARIANTS)
def test_a_dry_run_writes_nothing(
    db: StandardDatabase, legacy: Callable[[StandardDatabase], None], legacy_types: list[str]
) -> None:
    _drop_compound(db)
    legacy(db)
    before = _name_indexes(db)

    report = migration.up(db, dry_run=True)

    assert report.dry_run is True
    assert report.changed == 0
    assert report.precondition_unmet is False  # the real run creates the replacement first
    assert report.details["compound_to_create"] is True
    assert report.details["legacy_indexes"] == len(legacy_types)
    assert report.details["legacy_index_types"] == legacy_types
    assert _name_indexes(db) == before == _legacy_rows(legacy_types)


@pytest.mark.parametrize(("legacy", "legacy_types"), LEGACY_VARIANTS)
def test_without_the_replacement_nothing_is_dropped(
    db: StandardDatabase,
    legacy: Callable[[StandardDatabase], None],
    legacy_types: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The drop is gated on the re-read index list, not on the creation call having run."""
    _drop_compound(db)
    legacy(db)
    monkeypatch.setattr(module, "_create_replacement", lambda _collection: None)

    report = migration.up(db)

    assert report.precondition_unmet is True
    assert report.changed == 0
    assert report.details["replacement_indexes"] == 0
    assert report.details["legacy_indexes"] == len(legacy_types)
    assert _name_indexes(db) == _legacy_rows(legacy_types)


def test_a_global_row_without_tenant_key_is_normalised_and_holds_its_name(db: StandardDatabase) -> None:
    """``null`` and ``""`` are two values for the compound index; the legacy global row gets ``""``."""
    target = db.collection(_COLLECTION)
    _drop_compound(db)
    _persistent_legacy(db)
    legacy_key = target.insert({"name": "Topping"})["_key"]  # written before the field existed

    dry = migration.up(db, dry_run=True)
    assert dry.details["null_tenant_keys"] == 1
    assert dry.details["null_tenant_keys_normalised"] == 0
    assert "tenant_key" not in target.get(legacy_key)

    report = migration.up(db)

    assert report.details["null_tenant_keys_normalised"] == 1
    assert report.changed == 1 + 1 + 1  # normalised, compound created, legacy dropped
    assert target.get(legacy_key)["tenant_key"] == ""
    with pytest.raises(DocumentInsertError):
        target.insert(_row(GLOBAL))  # global exactly once, whichever spelling came first
    target.insert(_row(TENANT))
    again = migration.up(db)
    assert again.changed == 0
    assert again.details["null_tenant_keys"] == 0


def test_a_null_row_whose_name_a_global_row_holds_is_counted_not_rewritten(db: StandardDatabase) -> None:
    """The compound index alone admits both; rewriting the null row would abort the boot."""
    target = db.collection(_COLLECTION)
    null_key = target.insert({"name": "Topping"})["_key"]
    target.insert(_row(GLOBAL))

    report = migration.up(db)

    assert report.precondition_unmet is False
    assert report.details["null_tenant_key_name_conflicts"] == 1
    assert report.details["null_tenant_keys_normalised"] == 0
    assert "tenant_key" not in target.get(null_key)
