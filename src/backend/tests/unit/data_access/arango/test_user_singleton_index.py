"""Tests for ``ensure_user_singleton_index`` (REQ-020/REQ-021, SEC-005).

The per-user singleton index on ``user_key`` is bootstrapped **unique and
sparse**: unique so the auto-create race can no longer mint two preferences /
onboarding documents for one user, sparse so legacy documents that carry no
``user_key`` at all — the ones v0031 deliberately refuses to collapse, because
AQL groups them as one ``null`` group across different users — cannot block the
constraint that protects every real user.

``ensure_collections`` runs at startup *before* the migration runner, so the
helper must also degrade gracefully on a volume that still carries duplicate
singletons instead of taking startup down before v0031 can repair it. Covered:

  * a fresh volume gets the unique+sparse index;
  * an already-migrated volume is a no-op;
  * a pre-fix unique but non-sparse index is not accepted as the target;
  * duplicates blocking the unique index fall back to the non-unique index.
"""

from __future__ import annotations

from arango.exceptions import IndexCreateError

from app.data_access.arango.collections import (
    USER_SINGLETON_INDEX_FIELDS,
    ensure_user_singleton_index,
)


class _FakeCollection:
    def __init__(self, indexes: list[dict], *, unique_create_fails: bool = False) -> None:
        self._indexes = list(indexes)
        self._unique_create_fails = unique_create_fails
        self.created: list[dict] = []

    def indexes(self) -> list[dict]:
        return [dict(i) for i in self._indexes]

    def add_persistent_index(self, *, fields, unique: bool = False, sparse: bool = False, **_):
        if unique and self._unique_create_fails:
            # Emulate ArangoDB rejecting a unique index while duplicates exist.
            raise IndexCreateError.__new__(IndexCreateError)
        record = {"type": "persistent", "fields": list(fields), "unique": unique, "sparse": sparse}
        self.created.append(record)
        self._indexes.append(record)
        return record


_PRIMARY = {"type": "primary", "fields": ["_key"], "unique": True}
_TARGET = {
    "type": "persistent",
    "fields": list(USER_SINGLETON_INDEX_FIELDS),
    "unique": True,
    "sparse": True,
}
_UNIQUE_NON_SPARSE = {
    "type": "persistent",
    "fields": list(USER_SINGLETON_INDEX_FIELDS),
    "unique": True,
    "sparse": False,
}


def test_creates_unique_sparse_on_fresh_volume():
    collection = _FakeCollection([_PRIMARY])
    ensure_user_singleton_index(collection)

    assert collection.created == [
        {"type": "persistent", "fields": USER_SINGLETON_INDEX_FIELDS, "unique": True, "sparse": True}
    ]


def test_noop_when_target_index_already_present():
    collection = _FakeCollection([_PRIMARY, _TARGET])
    ensure_user_singleton_index(collection)

    assert collection.created == []


def test_non_sparse_unique_index_is_not_accepted_as_target():
    """A pre-fix non-sparse index would still block attribute-less legacy docs."""
    collection = _FakeCollection([_PRIMARY, _UNIQUE_NON_SPARSE])
    ensure_user_singleton_index(collection)

    assert collection.created == [
        {"type": "persistent", "fields": USER_SINGLETON_INDEX_FIELDS, "unique": True, "sparse": True}
    ]


def test_falls_back_to_non_unique_when_duplicates_block_unique():
    """Startup must survive a pre-v0031 volume so the migration can repair it."""
    collection = _FakeCollection([_PRIMARY], unique_create_fails=True)
    ensure_user_singleton_index(collection)

    assert collection.created == [
        {"type": "persistent", "fields": USER_SINGLETON_INDEX_FIELDS, "unique": False, "sparse": False}
    ]
