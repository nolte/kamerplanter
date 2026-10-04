"""#2028 — a location type another writer inserted between ``has`` and ``insert`` is not fatal.

``location_types`` is the registry's only fatal job. Before the seed lock, the replica
that lost the insert race died with ``ERR 1210 ... conflicting key: home``. The lock
removes the race; the loader still reads a primary-key conflict as "exists", so a
lock takeover or a manual run cannot abort a startup either. Any other insert error
still propagates.
"""

from __future__ import annotations

import pytest
from arango.exceptions import DocumentInsertError

from app.migrations.seed_location_types import seed_location_types


def _insert_error(code: int) -> DocumentInsertError:
    exc = DocumentInsertError.__new__(DocumentInsertError)
    exc.error_code = code
    return exc


class _RacedCollection:
    """``has`` says absent (the read happened before the other writer), ``insert`` refuses."""

    def __init__(self, code: int) -> None:
        self.code = code
        self.inserts = 0

    def has(self, _key: str) -> bool:
        return False

    def insert(self, _doc: dict) -> None:
        self.inserts += 1
        raise _insert_error(self.code)


class _Db:
    def __init__(self, collection: _RacedCollection) -> None:
        self._collection = collection

    def collection(self, _name: str) -> _RacedCollection:
        return self._collection


def test_a_key_another_writer_inserted_counts_as_existing() -> None:
    collection = _RacedCollection(1210)

    seed_location_types(_Db(collection))

    assert collection.inserts == 12, "every type was attempted, none aborted the job"


def test_any_other_insert_error_still_fails_the_fatal_job() -> None:
    with pytest.raises(DocumentInsertError):
        seed_location_types(_Db(_RacedCollection(1203)))
