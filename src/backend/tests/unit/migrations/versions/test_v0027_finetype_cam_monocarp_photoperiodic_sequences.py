"""Tests for v0027_finetype_cam_monocarp_photoperiodic_sequences (#616).

Verifies against a fake ArangoDB that the CAM/monocarp/photoperiodic/palm-fern-geophyte
cohorts are re-pointed onto their fine-typed sequence: an edge on a generic blanket
(``indoor_default`` / ``evergreen_foliage_perennial``) is re-bound, a cohort species with
no edge gets one created, an edge already on a *precise* sequence is left untouched, a
non-cohort species is never touched, and the migration is idempotent and dry-run-safe.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0027_finetype_cam_monocarp_photoperiodic_sequences import migration


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
            {"_key": "cam", "name": "cam_succulent_rest"},
            {"_key": "cam2", "name": "cam_double_rest"},
            {"_key": "clonal", "name": "clonal_monocarp"},
            {"_key": "photo", "name": "photoperiodic_ornamental"},
            {"_key": "palm", "name": "palm_evergreen"},
            {"_key": "fern", "name": "fern_spore"},
            {"_key": "geo", "name": "geophyte_fine"},
            {"_key": "standard", "name": "perennial_standard"},
        ],
        col.SPECIES: [
            {"_key": "sp-aloe", "scientific_name": "Aloe vera"},
            {"_key": "sp-lithops", "scientific_name": "Lithops spp."},
            {"_key": "sp-aechmea", "scientific_name": "Aechmea fasciata"},
            {"_key": "sp-euphorbia", "scientific_name": "Euphorbia pulcherrima"},
            {"_key": "sp-palm", "scientific_name": "Chamaedorea elegans"},
            {"_key": "sp-fern", "scientific_name": "Adiantum raddianum"},
            {"_key": "sp-clivia", "scientific_name": "Clivia miniata"},
            # non-cohort species that must not be touched.
            {"_key": "sp-ficus", "scientific_name": "Ficus benjamina"},
            # a cohort species already on a precise (WP-8-style) sequence — untouched.
            {"_key": "sp-anemone", "scientific_name": "Anemone hupehensis"},
        ],
        col.HAS_PHASE_SEQUENCE: [
            # CAM succulent left on the annual blanket.
            {"_key": "e-aloe", "_from": _sp_id("sp-aloe"), "_to": _seq_id("indoor")},
            # Lithops on the generic evergreen (Phase-1).
            {"_key": "e-lithops", "_from": _sp_id("sp-lithops"), "_to": _seq_id("evergreen")},
            # bromeliad on the annual blanket.
            {"_key": "e-aechmea", "_from": _sp_id("sp-aechmea"), "_to": _seq_id("indoor")},
            # poinsettia on the generic evergreen.
            {"_key": "e-euphorbia", "_from": _sp_id("sp-euphorbia"), "_to": _seq_id("evergreen")},
            # palm on the annual blanket.
            {"_key": "e-palm", "_from": _sp_id("sp-palm"), "_to": _seq_id("indoor")},
            # fern & clivia have NO edge yet → insert.
            # non-cohort Ficus on evergreen — must stay.
            {"_key": "e-ficus", "_from": _sp_id("sp-ficus"), "_to": _seq_id("evergreen")},
            # Anemone is in _TARGET? No — it is not; but even if edged precisely it stays.
            {"_key": "e-anemone", "_from": _sp_id("sp-anemone"), "_to": _seq_id("standard")},
        ],
    }


class TestMigration:
    def test_rebinds_and_inserts_for_cohorts_only(self) -> None:
        collections = _collections()
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]

        # 5 rebinds (aloe, lithops, aechmea, euphorbia, palm) + 2 inserts (fern, clivia).
        assert report.details == {"rebound": 5, "created": 2}
        assert report.changed == 7

        assert db.edges_from(_sp_id("sp-aloe"))[0]["_to"] == _seq_id("cam")
        assert db.edges_from(_sp_id("sp-lithops"))[0]["_to"] == _seq_id("cam2")
        assert db.edges_from(_sp_id("sp-aechmea"))[0]["_to"] == _seq_id("clonal")
        assert db.edges_from(_sp_id("sp-euphorbia"))[0]["_to"] == _seq_id("photo")
        assert db.edges_from(_sp_id("sp-palm"))[0]["_to"] == _seq_id("palm")
        # fern & clivia got brand-new edges.
        fern_edges = db.edges_from(_sp_id("sp-fern"))
        assert len(fern_edges) == 1 and fern_edges[0]["_to"] == _seq_id("fern")
        clivia_edges = db.edges_from(_sp_id("sp-clivia"))
        assert len(clivia_edges) == 1 and clivia_edges[0]["_to"] == _seq_id("geo")
        # non-cohort Ficus untouched.
        assert db.edges_from(_sp_id("sp-ficus"))[0]["_to"] == _seq_id("evergreen")

    def test_precise_binding_not_clobbered(self) -> None:
        """An edge already on a non-blanket sequence is never re-pointed."""
        collections = _collections()
        # Put Aloe on a precise sequence already — the scope guard must skip it.
        for edge in collections[col.HAS_PHASE_SEQUENCE]:
            if edge["_key"] == "e-aloe":
                edge["_to"] = _seq_id("cam")
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]
        # Aloe is already correct → not counted; rebinds drop to 4.
        assert report.details["rebound"] == 4
        assert db.edges_from(_sp_id("sp-aloe"))[0]["_to"] == _seq_id("cam")

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
        assert db.edges_from(_sp_id("sp-aloe"))[0]["_to"] == _seq_id("indoor")
        assert db.edges_from(_sp_id("sp-fern")) == []

    def test_missing_sequence_is_skipped(self) -> None:
        collections = _collections()
        # Simulate a database where the fern sequence has not been seeded.
        collections[col.PHASE_SEQUENCES] = [s for s in collections[col.PHASE_SEQUENCES] if s["name"] != "fern_spore"]
        db = _FakeDb(collections)
        migration.up(db)  # type: ignore[arg-type]
        # fern is skipped (no target); the other cohorts still resolve.
        assert db.edges_from(_sp_id("sp-fern")) == []
        assert db.edges_from(_sp_id("sp-aloe"))[0]["_to"] == _seq_id("cam")
