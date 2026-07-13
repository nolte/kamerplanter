"""Tests for v0022_bind_perennials_to_cyclic_sequence (#565 WP-1).

Verifies against a fake ArangoDB that indoor_default edges of perennial species are
re-pointed onto the matching cyclic sequence (strawberry → perennial_runner, other
polycarpic perennials → evergreen_foliage_perennial), that annual and monocarpic
species are left untouched, and that the migration is idempotent and dry-run-safe.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0022_bind_perennials_to_cyclic_sequence import migration


class _FakeAql:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        tokens = query.split()
        collection = tokens[tokens.index("IN") + 1]
        docs = self._collections.setdefault(collection, [])
        if query.lstrip().startswith("UPDATE"):
            for doc in docs:
                if doc["_key"] == bind_vars["key"]:
                    doc["_to"] = bind_vars["to_id"]
            return iter([])
        return iter(list(docs))


class _FakeDb:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections
        self.aql = _FakeAql(collections)

    def has_collection(self, name: str) -> bool:
        return name in self._collections

    def edge(self, key: str) -> dict[str, Any]:
        return next(e for e in self._collections[col.HAS_PHASE_SEQUENCE] if e["_key"] == key)


def _seq_id(key: str) -> str:
    return f"{col.PHASE_SEQUENCES}/{key}"


def _collections() -> dict[str, list[dict[str, Any]]]:
    return {
        col.PHASE_SEQUENCES: [
            {"_key": "indoor", "name": "indoor_default"},
            {"_key": "runner", "name": "perennial_runner"},
            {"_key": "evergreen", "name": "evergreen_foliage_perennial"},
        ],
        col.SPECIES: [
            {"_key": "sp-straw", "scientific_name": "Fragaria x ananassa"},
            {"_key": "sp-ficus", "scientific_name": "Ficus benjamina"},
            {"_key": "sp-lettuce", "scientific_name": "Lactuca sativa"},
            {"_key": "sp-agave", "scientific_name": "Agave americana"},
        ],
        col.LIFECYCLE_CONFIGS: [
            {"_key": "lc-1", "species_key": "sp-straw", "cycle_type": "perennial", "flowering_strategy": "polycarpic"},
            {"_key": "lc-2", "species_key": "sp-ficus", "cycle_type": "perennial", "flowering_strategy": "polycarpic"},
            {"_key": "lc-3", "species_key": "sp-lettuce", "cycle_type": "annual", "flowering_strategy": None},
            {"_key": "lc-4", "species_key": "sp-agave", "cycle_type": "perennial", "flowering_strategy": "monocarpic"},
        ],
        col.HAS_PHASE_SEQUENCE: [
            {"_key": "edge-straw", "_from": f"{col.SPECIES}/sp-straw", "_to": _seq_id("indoor")},
            {"_key": "edge-ficus", "_from": f"{col.SPECIES}/sp-ficus", "_to": _seq_id("indoor")},
            {"_key": "edge-lettuce", "_from": f"{col.SPECIES}/sp-lettuce", "_to": _seq_id("indoor")},
            {"_key": "edge-agave", "_from": f"{col.SPECIES}/sp-agave", "_to": _seq_id("indoor")},
        ],
    }


class TestMigration:
    def test_rebinds_perennials_only(self) -> None:
        db = _FakeDb(_collections())
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.scanned == 2
        assert report.changed == 2
        assert db.edge("edge-straw")["_to"] == _seq_id("runner")
        assert db.edge("edge-ficus")["_to"] == _seq_id("evergreen")
        # Annual and monocarpic species stay on the annual blanket.
        assert db.edge("edge-lettuce")["_to"] == _seq_id("indoor")
        assert db.edge("edge-agave")["_to"] == _seq_id("indoor")

    def test_idempotent(self) -> None:
        db = _FakeDb(_collections())
        migration.up(db)  # type: ignore[arg-type]
        second = migration.up(db)  # type: ignore[arg-type]

        assert second.scanned == 0
        assert second.changed == 0

    def test_dry_run_writes_nothing(self) -> None:
        db = _FakeDb(_collections())
        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert report.dry_run is True
        assert report.changed == 0
        assert db.edge("edge-straw")["_to"] == _seq_id("indoor")

    def test_no_indoor_default_is_noop(self) -> None:
        collections = _collections()
        collections[col.PHASE_SEQUENCES] = [{"_key": "runner", "name": "perennial_runner"}]
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]
        assert report.scanned == 0
