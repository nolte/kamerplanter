"""Tests for v0026_promote_scientific_name_normalized_unique (Issue #624, SEC-003).

The migration (1) reconciles any residual ``scientific_name_normalized`` duplicate
that a pre-#624 bypassing create path minted after v0010 ran, delegating to v0010's
battle-tested reconcile, and (2) promotes the persistent index from the non-unique
bootstrap shape to unique so the DB enforces the dedup key going forward.

Covered:
  * a residual ``Fragaria × ananassa`` / ``Fragaria x ananassa`` pair is merged onto
    one survivor AND the index is promoted (unique created, non-unique dropped);
  * idempotency — a re-run finds no duplicates and the unique index already present
    (``changed == 0``);
  * dry-run writes nothing — neither the duplicate nor the index is touched;
  * a fresh volume that already carries the unique index is a no-op;
  * ``down`` refuses (irreversible).
"""

from __future__ import annotations

from app.data_access.arango import collections as col
from app.migrations.framework.report import IrreversibleMigrationError
from app.migrations.versions.v0026_promote_scientific_name_normalized_unique import (
    _INDEX_FIELDS,
    migration,
)

# ── Fake database: AQL for v0010's scans/backfill, collection API for reconcile
#    and index management (persistent handles so index state survives calls). ──


class _FakeCollection:
    def __init__(self, store: dict[str, dict], indexes: list[dict]) -> None:
        self._store = store
        self._indexes = indexes
        self._seq = [0]

    # -- document API (used by v0010's reconcile) --
    def all(self):
        return [dict(d) for d in self._store.values()]

    def get(self, key: str):
        doc = self._store.get(key)
        return dict(doc) if doc else None

    def update(self, doc: dict) -> None:
        self._store[doc["_key"]].update(doc)

    def insert(self, doc: dict) -> None:
        key = doc.get("_key") or f"gen_{len(self._store) + 1}_{id(doc)}"
        stored = dict(doc)
        stored["_key"] = key
        self._store[key] = stored

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    # -- index API (used by v0026's promotion) --
    def indexes(self) -> list[dict]:
        return [dict(i) for i in self._indexes]

    def add_persistent_index(self, *, fields, unique: bool = False, **_):
        self._seq[0] += 1
        record = {"id": f"{col.SPECIES}/{self._seq[0]}", "type": "persistent", "fields": list(fields), "unique": unique}
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
        cols = self._db.cols

        if "COLLECT sk = p.species_key" in query:
            counts: dict[str, int] = {}
            for p in cols.get(col.PLANT_INSTANCES, {}).values():
                if p.get("removed_on") is None and p.get("species_key"):
                    counts[p["species_key"]] = counts.get(p["species_key"], 0) + 1
            return iter([{"species_key": k, "count": v} for k, v in counts.items()])

        if query.strip() == f"FOR d IN {col.SPECIES} RETURN d":
            return iter([dict(d) for d in cols[col.SPECIES].values()])

        if "FOR pair IN @pairs" in query:
            for pair in bind_vars["pairs"]:
                cols[col.SPECIES][pair["key"]]["scientific_name_normalized"] = pair["norm"]
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


_PRIMARY_INDEX = {"id": f"{col.SPECIES}/0", "type": "primary", "fields": ["_key"], "unique": True}
_NON_UNIQUE_NORMALIZED = {
    "id": f"{col.SPECIES}/norm",
    "type": "persistent",
    "fields": list(_INDEX_FIELDS),
    "unique": False,
}
_UNIQUE_NORMALIZED = {
    "id": f"{col.SPECIES}/norm_u",
    "type": "persistent",
    "fields": list(_INDEX_FIELDS),
    "unique": True,
}


def _residual_duplicate_db() -> _FakeDb:
    """A volume where a bypassing create path minted a normalized-duplicate after v0010.

    The non-unique bootstrap index is still in place (pre-#624 shape).
    """
    return _FakeDb(
        cols={
            col.SPECIES: {
                "sp_sign": {
                    "_key": "sp_sign",
                    "scientific_name": "Fragaria × ananassa",
                    "scientific_name_normalized": "fragaria x ananassa",
                    "family_key": None,
                },
                "sp_ascii": {
                    "_key": "sp_ascii",
                    "scientific_name": "Fragaria x ananassa",
                    "scientific_name_normalized": "fragaria x ananassa",
                    "family_key": "fam_rosaceae",
                },
            },
            col.PLANT_INSTANCES: {
                "pi_1": {"_key": "pi_1", "species_key": "sp_sign", "removed_on": None},
            },
        },
        indexes={col.SPECIES: [dict(_PRIMARY_INDEX), dict(_NON_UNIQUE_NORMALIZED)]},
    )


def _clean_unique_db() -> _FakeDb:
    """A fresh/already-reconciled volume that already carries the unique index."""
    return _FakeDb(
        cols={
            col.SPECIES: {
                "sp_tomato": {
                    "_key": "sp_tomato",
                    "scientific_name": "Solanum lycopersicum",
                    "scientific_name_normalized": "solanum lycopersicum",
                },
            },
            col.PLANT_INSTANCES: {},
        },
        indexes={col.SPECIES: [dict(_PRIMARY_INDEX), dict(_UNIQUE_NORMALIZED)]},
    )


def _normalized_indexes(db: _FakeDb) -> list[dict]:
    return [
        idx
        for idx in db.collection(col.SPECIES).indexes()
        if idx.get("type") == "persistent" and idx.get("fields") == list(_INDEX_FIELDS)
    ]


class TestReconcileAndPromote:
    def test_residual_duplicate_merged_and_index_promoted(self):
        db = _residual_duplicate_db()
        report = migration.up(db)

        species = db.cols[col.SPECIES]
        # The duplicate group collapsed onto the survivor carrying the live plant.
        assert "sp_ascii" not in species
        assert "sp_sign" in species
        assert db.cols[col.PLANT_INSTANCES]["pi_1"]["species_key"] == "sp_sign"
        # Survivor adopted the loser's richer metadata (Rosaceae family).
        assert species["sp_sign"]["family_key"] == "fam_rosaceae"

        # Exactly one persistent normalized index remains — and it is unique.
        normalized = _normalized_indexes(db)
        assert len(normalized) == 1
        assert normalized[0]["unique"] is True
        assert report.details["unique_index_enforced"] is True
        assert report.changed > 0

    def test_index_promotion_only_when_no_duplicates(self):
        db = _clean_unique_db()
        report = migration.up(db)

        normalized = _normalized_indexes(db)
        assert len(normalized) == 1
        assert normalized[0]["unique"] is True
        # Nothing changed: no duplicates, unique index already present.
        assert report.changed == 0
        assert report.noop is True


class TestIdempotency:
    def test_rerun_is_a_noop(self):
        db = _residual_duplicate_db()
        migration.up(db)
        report = migration.up(db)

        assert report.changed == 0
        assert report.noop is True
        normalized = _normalized_indexes(db)
        assert len(normalized) == 1
        assert normalized[0]["unique"] is True


class TestDryRun:
    def test_dry_run_touches_neither_data_nor_index(self):
        db = _residual_duplicate_db()
        report = migration.up(db, dry_run=True)

        assert report.dry_run is True
        assert report.changed == 0
        # The duplicate is still present and the index is still non-unique.
        assert "sp_ascii" in db.cols[col.SPECIES]
        normalized = _normalized_indexes(db)
        assert len(normalized) == 1
        assert normalized[0]["unique"] is False
        assert report.details["will_create_unique_index"] is True
        assert report.details["will_drop_non_unique_indexes"] == 1


class TestMetadataAndReversibility:
    def test_migration_metadata(self):
        assert migration.version == "0026"
        assert migration.name == "promote_scientific_name_normalized_unique"
        assert migration.reversible is False

    def test_down_refuses(self):
        db = _clean_unique_db()
        try:
            migration.down(db)
        except IrreversibleMigrationError:
            return
        raise AssertionError("down() must raise IrreversibleMigrationError")
