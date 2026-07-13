"""Tests for v0024_rebind_masterdata_sweep_sequences (#565 WP-8).

Verifies against a fake ArangoDB that the WP-8 sweep species are re-pointed onto their
precise phase sequence (asparagus → perennial_early_harvest, boxwood/lavender →
evergreen_subshrub_rest, onion → biennial_vernalization), that a species without any
has_phase_sequence edge gets one created, that non-WP-8 species are left untouched, and
that the migration is idempotent and dry-run-safe.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0024_rebind_masterdata_sweep_sequences import migration


class _FakeAql:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        tokens = query.split()
        stripped = query.lstrip()
        if stripped.startswith("UPDATE"):
            collection = tokens[tokens.index("IN") + 1]
            for doc in self._collections.setdefault(collection, []):
                if doc["_key"] == bind_vars["key"]:
                    doc["_to"] = bind_vars["to_id"]
            return iter([])
        if stripped.startswith("INSERT"):
            collection = tokens[tokens.index("INTO") + 1]
            docs = self._collections.setdefault(collection, [])
            docs.append(
                {
                    "_key": f"edge-{len(docs)}",
                    "_from": bind_vars["from_id"],
                    "_to": bind_vars["to_id"],
                }
            )
            return iter([])
        collection = tokens[tokens.index("IN") + 1]
        return iter(list(self._collections.setdefault(collection, [])))


class _FakeDb:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections
        self.aql = _FakeAql(collections)

    def has_collection(self, name: str) -> bool:
        return name in self._collections

    def edges_from(self, from_id: str) -> list[dict[str, Any]]:
        return [e for e in self._collections[col.HAS_PHASE_SEQUENCE] if e["_from"] == from_id]


def _seq_id(key: str) -> str:
    return f"{col.PHASE_SEQUENCES}/{key}"


def _sp_id(key: str) -> str:
    return f"{col.SPECIES}/{key}"


def _collections() -> dict[str, list[dict[str, Any]]]:
    return {
        col.PHASE_SEQUENCES: [
            {"_key": "indoor", "name": "indoor_default"},
            {"_key": "evergreen", "name": "evergreen_foliage_perennial"},
            {"_key": "early", "name": "perennial_early_harvest"},
            {"_key": "subshrub", "name": "evergreen_subshrub_rest"},
            {"_key": "biennial", "name": "biennial_vernalization"},
            {"_key": "standard", "name": "perennial_standard"},
        ],
        col.SPECIES: [
            {"_key": "sp-asp", "scientific_name": "Asparagus officinalis"},
            {"_key": "sp-box", "scientific_name": "Buxus sempervirens"},
            {"_key": "sp-onion", "scientific_name": "Allium cepa"},
            {"_key": "sp-thyme", "scientific_name": "Thymus vulgaris"},
            {"_key": "sp-ficus", "scientific_name": "Ficus benjamina"},
        ],
        col.HAS_PHASE_SEQUENCE: [
            # asparagus & boxwood were left on the generic Phase-1 binding by v0022.
            {"_key": "e-asp", "_from": _sp_id("sp-asp"), "_to": _seq_id("evergreen")},
            {"_key": "e-box", "_from": _sp_id("sp-box"), "_to": _seq_id("evergreen")},
            # onion (biennial) stayed on the annual blanket.
            {"_key": "e-onion", "_from": _sp_id("sp-onion"), "_to": _seq_id("indoor")},
            # thyme has NO edge yet (herb had no lifecycle before WP-8).
            # a non-WP-8 species that must not be touched.
            {"_key": "e-ficus", "_from": _sp_id("sp-ficus"), "_to": _seq_id("evergreen")},
        ],
    }


class TestMigration:
    def test_rebinds_and_creates_for_wp8_species_only(self) -> None:
        collections = _collections()
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]

        # 3 rebinds (asp, box, onion) + 1 insert (thyme) = 4 changes.
        assert report.changed == 4
        assert report.details == {"rebound": 3, "created": 1}

        assert db.edges_from(_sp_id("sp-asp"))[0]["_to"] == _seq_id("early")
        assert db.edges_from(_sp_id("sp-box"))[0]["_to"] == _seq_id("subshrub")
        assert db.edges_from(_sp_id("sp-onion"))[0]["_to"] == _seq_id("biennial")
        # thyme got a brand-new edge onto the subshrub sequence.
        thyme_edges = db.edges_from(_sp_id("sp-thyme"))
        assert len(thyme_edges) == 1
        assert thyme_edges[0]["_to"] == _seq_id("subshrub")
        # non-WP-8 species is untouched.
        assert db.edges_from(_sp_id("sp-ficus"))[0]["_to"] == _seq_id("evergreen")

    def test_idempotent_on_second_run(self) -> None:
        db = _FakeDb(_collections())
        migration.up(db)  # type: ignore[arg-type]
        report = migration.up(db)  # type: ignore[arg-type]
        assert report.changed == 0
        assert report.noop is True

    def test_dry_run_writes_nothing(self) -> None:
        collections = _collections()
        db = _FakeDb(collections)
        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]
        assert report.dry_run is True
        assert report.changed == 0
        # Nothing moved.
        assert db.edges_from(_sp_id("sp-asp"))[0]["_to"] == _seq_id("evergreen")
        assert db.edges_from(_sp_id("sp-thyme")) == []

    def test_missing_sequence_is_skipped(self) -> None:
        collections = _collections()
        # Simulate a database where the new subshrub sequence has not been seeded.
        collections[col.PHASE_SEQUENCES] = [
            s for s in collections[col.PHASE_SEQUENCES] if s["name"] != "evergreen_subshrub_rest"
        ]
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]
        # boxwood + thyme (both subshrub) are skipped; asparagus + onion still handled.
        assert db.edges_from(_sp_id("sp-box"))[0]["_to"] == _seq_id("evergreen")
        assert db.edges_from(_sp_id("sp-thyme")) == []
        assert db.edges_from(_sp_id("sp-asp"))[0]["_to"] == _seq_id("early")
        assert report.details == {"rebound": 2, "created": 0}
