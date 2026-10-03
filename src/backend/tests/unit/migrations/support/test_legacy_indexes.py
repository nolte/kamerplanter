"""The shared legacy-index selector sees hash-typed indexes too (#2034).

The index rows below are the shapes ArangoDB 3.12.8 returned from ``indexes()``
for an index created with ``{"type": "hash", ...}`` and one created with
``add_persistent_index`` (measured in a throwaway container; the real-server
counterpart is ``tests/integration/test_v0073_*`` and ``test_v0074_*``).
"""

from __future__ import annotations

from typing import Any

import pytest

from app.migrations.support.legacy_indexes import (
    PERSISTENT_INDEX_TYPES,
    IndexShape,
    indexes_on,
    is_index_on,
    retire_legacy_index,
)

_HASH = {"id": "c/1", "type": "hash", "fields": ["batch_id"], "unique": True, "sparse": False}
_PERSISTENT = {"id": "c/2", "type": "persistent", "fields": ["batch_id"], "unique": True, "sparse": True}
_PRIMARY = {"id": "c/0", "type": "primary", "fields": ["_key"], "unique": True, "sparse": False}

_LEGACY = IndexShape(fields=("batch_id",), unique=True, sparse=False)
_REPLACEMENT = IndexShape(fields=("batch_id",), unique=True, sparse=True)


class _Collection:
    """Answers ``indexes()`` and ``delete_index`` like the server, nothing else."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = [dict(row) for row in rows]
        self.deleted: list[str] = []

    def indexes(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.rows]

    def delete_index(self, index_id: str, ignore_missing: bool = False) -> bool:
        before = len(self.rows)
        self.rows = [row for row in self.rows if row["id"] != index_id]
        if len(self.rows) == before and not ignore_missing:
            raise AssertionError(f"no index {index_id}")
        self.deleted.append(index_id)
        return True


class TestSelector:
    def test_a_hash_typed_index_is_selected(self) -> None:
        assert is_index_on(_HASH, ["batch_id"])

    def test_a_persistent_index_is_selected(self) -> None:
        assert is_index_on(_PERSISTENT, ("batch_id",))

    def test_other_fields_or_types_are_not_selected(self) -> None:
        assert not is_index_on(_HASH, ["batch_id", "tenant_key"])
        assert not is_index_on(_PRIMARY, ["_key"])
        assert not is_index_on({**_HASH, "type": "skiplist"}, ["batch_id"])

    def test_the_types_are_exactly_persistent_and_hash(self) -> None:
        assert PERSISTENT_INDEX_TYPES == ("persistent", "hash")

    def test_indexes_on_returns_both_types(self) -> None:
        assert [idx["type"] for idx in indexes_on(_Collection([_PRIMARY, _HASH, _PERSISTENT]), ["batch_id"])] == [
            "hash",
            "persistent",
        ]


class TestRetireLegacyIndex:
    def test_a_hash_typed_legacy_index_is_dropped_beside_its_replacement(self) -> None:
        collection = _Collection([_PRIMARY, _HASH, _PERSISTENT])

        outcome = retire_legacy_index(collection, legacy=_LEGACY, replacement=_REPLACEMENT, dry_run=False)

        assert collection.deleted == ["c/1"]
        assert outcome.dropped == 1
        assert outcome.details()["legacy_index_types"] == ["hash"]

    def test_without_a_replacement_nothing_is_dropped(self) -> None:
        collection = _Collection([_PRIMARY, _HASH])

        outcome = retire_legacy_index(collection, legacy=_LEGACY, replacement=_REPLACEMENT, dry_run=False)

        assert outcome.refused
        assert collection.deleted == []
        assert outcome.details() == {
            "legacy_indexes": 1,
            "legacy_index_types": ["hash"],
            "replacement_indexes": 0,
            "legacy_indexes_dropped": 0,
            "refused_without_replacement": True,
        }

    def test_a_dry_run_drops_nothing(self) -> None:
        collection = _Collection([_HASH, _PERSISTENT])

        outcome = retire_legacy_index(collection, legacy=_LEGACY, replacement=_REPLACEMENT, dry_run=True)

        assert collection.deleted == []
        assert outcome.legacy_ids == ("c/1",)
        assert outcome.dropped == 0

    def test_a_second_run_finds_nothing(self) -> None:
        collection = _Collection([_HASH, _PERSISTENT])
        retire_legacy_index(collection, legacy=_LEGACY, replacement=_REPLACEMENT, dry_run=False)

        again = retire_legacy_index(collection, legacy=_LEGACY, replacement=_REPLACEMENT, dry_run=False)

        assert again.legacy_ids == ()
        assert not again.refused

    def test_a_non_unique_replacement_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="unique"):
            retire_legacy_index(
                _Collection([]),
                legacy=_LEGACY,
                replacement=IndexShape(fields=("batch_id",), unique=False),
                dry_run=False,
            )

    def test_a_replacement_equal_to_the_legacy_shape_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="same index"):
            retire_legacy_index(_Collection([]), legacy=_LEGACY, replacement=_LEGACY, dry_run=False)
