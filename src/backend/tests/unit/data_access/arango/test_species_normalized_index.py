"""Tests for ``ensure_species_normalized_index`` (Issue #624, SEC-003).

``ensure_collections`` runs at startup *before* the migration runner, so the helper
must create the UNIQUE canonical dedup index when that is safe and otherwise degrade
gracefully to the non-unique bootstrap index (leaving the v0025 migration to dedup and
promote). Covered:

  * a fresh/reconciled volume gets the unique index;
  * an already-unique volume is a no-op;
  * a volume that still carries duplicates (unique-index creation raises
    ``IndexCreateError``) falls back to the non-unique index instead of crashing.
"""

from __future__ import annotations

from arango.exceptions import IndexCreateError

from app.data_access.arango.collections import (
    SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS,
    ensure_species_normalized_index,
)


class _FakeCollection:
    def __init__(self, indexes: list[dict], *, unique_create_fails: bool = False) -> None:
        self._indexes = list(indexes)
        self._unique_create_fails = unique_create_fails
        self.created: list[dict] = []

    def indexes(self) -> list[dict]:
        return [dict(i) for i in self._indexes]

    def add_persistent_index(self, *, fields, unique: bool = False, **_):
        if unique and self._unique_create_fails:
            # Emulate ArangoDB rejecting a unique index while duplicates exist.
            raise IndexCreateError.__new__(IndexCreateError)
        record = {"type": "persistent", "fields": list(fields), "unique": unique}
        self.created.append(record)
        self._indexes.append(record)
        return record


_PRIMARY = {"type": "primary", "fields": ["_key"], "unique": True}
_NON_UNIQUE = {"type": "persistent", "fields": list(SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS), "unique": False}
_UNIQUE = {"type": "persistent", "fields": list(SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS), "unique": True}


def test_creates_unique_on_fresh_volume():
    collection = _FakeCollection([_PRIMARY])
    ensure_species_normalized_index(collection)

    assert collection.created == [
        {"type": "persistent", "fields": SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS, "unique": True}
    ]


def test_noop_when_unique_already_present():
    collection = _FakeCollection([_PRIMARY, _UNIQUE])
    ensure_species_normalized_index(collection)

    assert collection.created == []


def test_falls_back_to_non_unique_when_duplicates_block_unique():
    collection = _FakeCollection([_PRIMARY], unique_create_fails=True)
    ensure_species_normalized_index(collection)

    # The unique attempt failed → the non-unique bootstrap index is created instead.
    assert collection.created == [
        {"type": "persistent", "fields": SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS, "unique": False}
    ]


def test_promotes_when_only_non_unique_present_and_no_duplicates():
    collection = _FakeCollection([_PRIMARY, _NON_UNIQUE])
    ensure_species_normalized_index(collection)

    # No unique index yet → it creates one (v0025 later drops the non-unique sibling).
    unique_index = {"type": "persistent", "fields": SCIENTIFIC_NAME_NORMALIZED_INDEX_FIELDS, "unique": True}
    assert unique_index in collection.created
