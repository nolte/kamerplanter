"""v0041 swaps the species dedup index from global to per-tenant (#1162).

The assertion that decides whether this migration did anything is **not** that the
compound index exists — it is that the **legacy global one is gone**. Leaving it in
place keeps the stricter constraint in force, so the compound index would be
decorative and the whole change would look applied while behaving exactly as
before. `test_the_legacy_global_index_is_dropped` is that test; without it this
file would pass against a migration that only adds.

Order is asserted too: the compound index is created *before* the legacy one is
dropped, because the reverse leaves a window with no uniqueness constraint at all,
and a concurrent create in that window inserts the duplicate both indexes exist to
prevent.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.versions.v0041_tenant_scoped_species_dedup_index import (
    TenantScopedSpeciesDedupIndexMigration,
)

_COMPOUND = ["tenant_key", "scientific_name_normalized"]
_LEGACY = ["scientific_name_normalized"]


class _Collection:
    def __init__(self, indexes: list[dict[str, Any]]) -> None:
        self._indexes = indexes
        #: Every mutation in order, so the *sequence* can be asserted and not only
        #: the end state — the window between the two steps is the risk.
        self.operations: list[str] = []

    def indexes(self) -> list[dict[str, Any]]:
        return list(self._indexes)

    def add_persistent_index(self, *, fields: list[str], unique: bool = False) -> None:
        self.operations.append(f"add:{','.join(fields)}:{unique}")
        self._indexes.append({"id": f"i{len(self._indexes)}", "type": "persistent", "fields": fields, "unique": unique})

    def delete_index(self, index_id: str, ignore_missing: bool = False) -> None:
        self.operations.append(f"drop:{index_id}")
        self._indexes = [idx for idx in self._indexes if idx.get("id") != index_id]


class _Db:
    def __init__(self, collection: _Collection | None) -> None:
        self._collection = collection

    def has_collection(self, name: str) -> bool:
        return self._collection is not None and name == col.SPECIES

    def collection(self, name: str) -> _Collection:
        assert self._collection is not None
        return self._collection


def _db(*, legacy: bool = True, compound: bool = False) -> tuple[_Db, _Collection]:
    indexes: list[dict[str, Any]] = [{"id": "primary", "type": "primary", "fields": ["_key"]}]
    if legacy:
        indexes.append({"id": "legacy1", "type": "persistent", "fields": _LEGACY, "unique": True})
    if compound:
        indexes.append({"id": "compound1", "type": "persistent", "fields": _COMPOUND, "unique": True})
    collection = _Collection(indexes)
    return _Db(collection), collection


@pytest.fixture
def migration() -> TenantScopedSpeciesDedupIndexMigration:
    return TenantScopedSpeciesDedupIndexMigration()


def _fields(collection: _Collection) -> list[list[str]]:
    return [idx["fields"] for idx in collection.indexes() if idx.get("type") == "persistent"]


def test_the_compound_index_is_created(migration) -> None:
    db, collection = _db()

    migration.up(db)  # type: ignore[arg-type]

    assert _COMPOUND in _fields(collection)


def test_the_legacy_global_index_is_dropped(migration) -> None:
    """The assertion that decides whether this migration did anything at all.

    A global unique index left in place is *stricter* than the compound one, so it
    keeps deciding — and the change looks applied while behaving as before.
    """
    db, collection = _db()

    migration.up(db)  # type: ignore[arg-type]

    assert _LEGACY not in _fields(collection)


def test_the_compound_index_exists_before_the_legacy_one_is_dropped(migration) -> None:
    """No window without a uniqueness constraint.

    Dropping first would let a concurrent create insert exactly the duplicate both
    indexes exist to prevent — a race that would be invisible afterwards, because
    the end state looks identical either way. Only the order distinguishes them.
    """
    db, collection = _db()

    migration.up(db)  # type: ignore[arg-type]

    add_index = next(i for i, op in enumerate(collection.operations) if op.startswith("add:"))
    drop_index = next(i for i, op in enumerate(collection.operations) if op.startswith("drop:"))
    assert add_index < drop_index


def test_the_new_index_is_unique(migration) -> None:
    """A non-unique compound index would enforce nothing and pass every other test."""
    db, collection = _db()

    migration.up(db)  # type: ignore[arg-type]

    compound = next(idx for idx in collection.indexes() if idx.get("fields") == _COMPOUND)
    assert compound["unique"] is True


def test_a_dry_run_changes_no_index(migration) -> None:
    db, collection = _db()

    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

    assert report.changed == 0
    assert collection.operations == []
    assert _LEGACY in _fields(collection)


def test_a_second_run_is_a_no_op(migration) -> None:
    """M-3: the compound index is present and the legacy one gone."""
    db, collection = _db()
    migration.up(db)  # type: ignore[arg-type]
    collection.operations.clear()

    second = migration.up(db)  # type: ignore[arg-type]

    assert second.changed == 0
    assert collection.operations == []


def test_an_install_that_already_has_only_the_compound_index_is_untouched(migration) -> None:
    db, collection = _db(legacy=False, compound=True)

    report = migration.up(db)  # type: ignore[arg-type]

    assert report.changed == 0


def test_a_missing_species_collection_is_a_clean_no_op(migration) -> None:
    """A fresh install must boot rather than fail on an absent collection."""
    report = migration.up(_Db(None))  # type: ignore[arg-type]

    assert report.changed == 0
