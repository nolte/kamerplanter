"""Tests for v0030_sparse_unique_harvest_batch_id (#740).

The migration (1) nulls out blank ``harvest_batches.batch_id`` sentinels that the
pre-fix optional-with-default-"" model persisted, and (2) promotes the persistent
index on ``batch_id`` from the non-sparse unique bootstrap shape to unique+sparse so
multiple unlabelled batches no longer collide on the empty key.

Covered:
  * a volume with ``""``/whitespace batch_ids has them nulled AND the index is
    promoted (sparse+unique created, non-sparse dropped);
  * idempotency — a re-run finds no blank ids and the sparse+unique index already
    present (``changed == 0``);
  * dry-run writes nothing — neither the blank ids nor the index are touched;
  * a fresh volume that already carries the sparse+unique index is a no-op;
  * ``down`` refuses (irreversible).
"""

from __future__ import annotations

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0030_sparse_unique_harvest_batch_id import (
    _INDEX_FIELDS,
    migration,
)

# ── Fake database: AQL for the blank-scan + null-out UPDATE, collection API for
#    index introspection (persistent handles so index state survives calls). ──


class _FakeCollection:
    def __init__(self, store: dict[str, dict], indexes: list[dict]) -> None:
        self._store = store
        self._indexes = indexes
        self._seq = [0]

    # -- index API (used by v0030's promotion) --
    def indexes(self) -> list[dict]:
        return [dict(i) for i in self._indexes]

    def add_persistent_index(self, *, fields, unique: bool = False, sparse: bool = False, **_):
        self._seq[0] += 1
        record = {
            "id": f"{col.HARVEST_BATCHES}/{self._seq[0]}",
            "type": "persistent",
            "fields": list(fields),
            "unique": unique,
            "sparse": sparse,
        }
        self._indexes.append(record)
        return record

    def delete_index(self, index_id: str, ignore_missing: bool = False) -> bool:
        for i, idx in enumerate(self._indexes):
            if idx.get("id") == index_id:
                del self._indexes[i]
                return True
        if not ignore_missing:
            raise KeyError(index_id)
        return False


class _FakeAql:
    def __init__(self, db: _FakeDb) -> None:
        self._db = db

    def execute(self, query: str, bind_vars: dict | None = None):
        bind_vars = bind_vars or {}
        store = self._db.cols.get(col.HARVEST_BATCHES, {})

        if "TRIM(doc.batch_id) == ''" in query:
            return iter(
                [
                    doc["_key"]
                    for doc in store.values()
                    if doc.get("batch_id") is not None and str(doc["batch_id"]).strip() == ""
                ]
            )

        if "UPDATE {_key: key, batch_id: null}" in query:
            for key in bind_vars["keys"]:
                store[key]["batch_id"] = None
            return iter([])

        raise AssertionError(f"unhandled query: {query!r}")


class _FakeDb:
    def __init__(self, cols: dict[str, dict[str, dict]], indexes: dict[str, list[dict]] | None = None) -> None:
        self.cols = cols
        self.index_store = indexes or {}
        self._handles: dict[str, _FakeCollection] = {}
        self.aql = _FakeAql(self)

    def has_collection(self, name: str) -> bool:
        return name in self.cols

    def collection(self, name: str) -> _FakeCollection:
        if name not in self._handles:
            store = self.cols.setdefault(name, {})
            idx = self.index_store.setdefault(name, [])
            self._handles[name] = _FakeCollection(store, idx)
        return self._handles[name]


_PRIMARY_INDEX = {"id": f"{col.HARVEST_BATCHES}/0", "type": "primary", "fields": ["_key"], "unique": True}
_NON_SPARSE_UNIQUE = {
    "id": f"{col.HARVEST_BATCHES}/bid",
    "type": "persistent",
    "fields": list(_INDEX_FIELDS),
    "unique": True,
    "sparse": False,
}
_SPARSE_UNIQUE = {
    "id": f"{col.HARVEST_BATCHES}/bid_sparse",
    "type": "persistent",
    "fields": list(_INDEX_FIELDS),
    "unique": True,
    "sparse": True,
}


def _blank_batch_db() -> _FakeDb:
    """A volume carrying two unlabelled batches (pre-#740 ``""`` sentinel).

    The non-sparse unique bootstrap index is still in place.
    """
    return _FakeDb(
        cols={
            col.HARVEST_BATCHES: {
                "hb_1": {"_key": "hb_1", "batch_id": "", "plant_key": "pi_1"},
                "hb_2": {"_key": "hb_2", "batch_id": "  ", "plant_key": "pi_2"},
                "hb_3": {"_key": "hb_3", "batch_id": "LOT-42", "plant_key": "pi_3"},
            },
        },
        indexes={col.HARVEST_BATCHES: [dict(_PRIMARY_INDEX), dict(_NON_SPARSE_UNIQUE)]},
    )


def _clean_sparse_db() -> _FakeDb:
    """A fresh/already-migrated volume that already carries the sparse+unique index."""
    return _FakeDb(
        cols={
            col.HARVEST_BATCHES: {
                "hb_a": {"_key": "hb_a", "batch_id": None, "plant_key": "pi_a"},
                "hb_b": {"_key": "hb_b", "batch_id": "LOT-1", "plant_key": "pi_b"},
            },
        },
        indexes={col.HARVEST_BATCHES: [dict(_PRIMARY_INDEX), dict(_SPARSE_UNIQUE)]},
    )


def _batch_id_indexes(db: _FakeDb) -> list[dict]:
    return [
        idx
        for idx in db.collection(col.HARVEST_BATCHES).indexes()
        if idx.get("type") == "persistent" and idx.get("fields") == list(_INDEX_FIELDS)
    ]


class TestNullOutAndPromote:
    def test_blank_ids_nulled_and_index_promoted(self):
        db = _blank_batch_db()
        report = migration.up(db)

        batches = db.cols[col.HARVEST_BATCHES]
        # Both blank sentinels became null; the real label is untouched.
        assert batches["hb_1"]["batch_id"] is None
        assert batches["hb_2"]["batch_id"] is None
        assert batches["hb_3"]["batch_id"] == "LOT-42"

        # Exactly one persistent batch_id index remains — unique and sparse.
        indexes = _batch_id_indexes(db)
        assert len(indexes) == 1
        assert indexes[0]["unique"] is True
        assert indexes[0]["sparse"] is True

        assert report.scanned == 2
        assert report.details["nulled_batch_ids"] == 2
        assert report.details["sparse_unique_index_enforced"] is True
        assert report.changed > 0

    def test_index_promotion_only_when_no_blanks(self):
        db = _clean_sparse_db()
        report = migration.up(db)

        indexes = _batch_id_indexes(db)
        assert len(indexes) == 1
        assert indexes[0]["unique"] is True
        assert indexes[0]["sparse"] is True
        # Nothing changed: no blanks, sparse+unique index already present.
        assert report.changed == 0
        assert report.noop is True


class TestIdempotency:
    def test_rerun_is_a_noop(self):
        db = _blank_batch_db()
        migration.up(db)
        report = migration.up(db)

        assert report.changed == 0
        assert report.noop is True
        indexes = _batch_id_indexes(db)
        assert len(indexes) == 1
        assert indexes[0]["unique"] is True
        assert indexes[0]["sparse"] is True


class TestDryRun:
    def test_dry_run_touches_neither_data_nor_index(self):
        db = _blank_batch_db()
        report = migration.up(db, dry_run=True)

        assert report.dry_run is True
        assert report.changed == 0
        # The blank sentinels are still present and the index is still non-sparse.
        assert db.cols[col.HARVEST_BATCHES]["hb_1"]["batch_id"] == ""
        indexes = _batch_id_indexes(db)
        assert len(indexes) == 1
        assert indexes[0]["sparse"] is False
        assert report.details["will_create_sparse_unique_index"] is True
        assert report.details["will_drop_redundant_indexes"] == 1


class TestMetadataAndReversibility:
    def test_migration_metadata(self):
        assert migration.version == "0030"
        assert migration.name == "sparse_unique_harvest_batch_id"
        assert migration.reversible is False

    def test_down_refuses(self):
        db = _clean_sparse_db()
        try:
            migration.down(db)
        except IrreversibleMigrationError:
            return
        raise AssertionError("down() must raise IrreversibleMigrationError")
