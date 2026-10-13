"""v0073 / v0074 drop the hash-typed legacy unique index their predecessor missed (#2034).

Both are the same call into ``app.migrations.support.legacy_indexes`` with a
different shape pair, so one parametrised double covers both. The real-server
counterparts are ``tests/integration/test_v0073_*`` and ``test_v0074_*``.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.support.legacy_indexes import IndexShape
from app.migrations.versions.v0073_retire_hash_typed_harvest_batch_id_index import (
    LEGACY_BATCH_ID_INDEX,
    SPARSE_BATCH_ID_INDEX,
)
from app.migrations.versions.v0073_retire_hash_typed_harvest_batch_id_index import (
    migration as v0073,
)
from app.migrations.versions.v0074_retire_hash_typed_provider_link_index import (
    LEGACY_PROVIDER_LINK_INDEX,
    PROVIDER_LINK_INDEX,
)
from app.migrations.versions.v0074_retire_hash_typed_provider_link_index import (
    migration as v0074,
)

_CASES = [
    pytest.param(v0073, col.HARVEST_BATCHES, LEGACY_BATCH_ID_INDEX, SPARSE_BATCH_ID_INDEX, id="v0073"),
    pytest.param(v0074, col.AUTH_PROVIDERS, LEGACY_PROVIDER_LINK_INDEX, PROVIDER_LINK_INDEX, id="v0074"),
]


def _row(index_id: str, index_type: str, shape: IndexShape) -> dict[str, Any]:
    return {
        "id": index_id,
        "type": index_type,
        "fields": list(shape.fields),
        "unique": shape.unique,
        "sparse": shape.sparse,
    }


class _Collection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def indexes(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.rows]

    def delete_index(self, index_id: str, ignore_missing: bool = False) -> bool:  # noqa: ARG002
        self.rows = [row for row in self.rows if row["id"] != index_id]
        return True


class _Db:
    def __init__(self, name: str, rows: list[dict[str, Any]] | None) -> None:
        self.name = name
        self.handle = _Collection(rows or [])
        self.present = rows is not None

    def has_collection(self, name: str) -> bool:
        return self.present and name == self.name

    def collection(self, name: str) -> _Collection:
        assert name == self.name, f"the migration touched {name}"
        return self.handle


@pytest.mark.parametrize(("migration", "collection", "legacy", "replacement"), _CASES)
def test_a_hash_typed_legacy_index_is_dropped(
    migration: Migration, collection: str, legacy: IndexShape, replacement: IndexShape
) -> None:
    db = _Db(collection, [_row("c/1", "hash", legacy), _row("c/2", "persistent", replacement)])

    report = migration.up(db)  # type: ignore[arg-type]

    assert [row["id"] for row in db.handle.rows] == ["c/2"]
    assert report.changed == 1
    assert report.precondition_unmet is False
    assert migration.up(db).changed == 0  # type: ignore[arg-type]


@pytest.mark.parametrize(("migration", "collection", "legacy", "replacement"), _CASES)
def test_without_the_replacement_it_refuses(
    migration: Migration, collection: str, legacy: IndexShape, replacement: IndexShape
) -> None:
    del replacement
    db = _Db(collection, [_row("c/1", "hash", legacy)])

    report = migration.up(db)  # type: ignore[arg-type]

    assert report.precondition_unmet is True
    assert report.changed == 0
    assert report.details["legacy_indexes"] == 1
    assert [row["id"] for row in db.handle.rows] == ["c/1"]


@pytest.mark.parametrize(("migration", "collection", "legacy", "replacement"), _CASES)
def test_a_dry_run_drops_nothing(
    migration: Migration, collection: str, legacy: IndexShape, replacement: IndexShape
) -> None:
    db = _Db(collection, [_row("c/1", "hash", legacy), _row("c/2", "persistent", replacement)])

    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

    assert report.changed == 0
    assert report.details["legacy_indexes"] == 1
    assert len(db.handle.rows) == 2


@pytest.mark.parametrize(("migration", "collection", "legacy", "replacement"), _CASES)
def test_a_missing_collection_is_a_no_op(
    migration: Migration, collection: str, legacy: IndexShape, replacement: IndexShape
) -> None:
    del legacy, replacement
    report = migration.up(_Db(collection, None))  # type: ignore[arg-type]

    assert report.changed == 0
    assert report.precondition_unmet is False
