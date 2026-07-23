"""Tests for v0029_repair_fragaria_runner_binding (#541/#680).

Verifies against a fake ArangoDB that strawberry's blanket edge is re-pointed onto
``perennial_runner`` (or created when absent), that a precise binding is never clobbered,
that a non-scoped species is untouched, that the allelopathy score is corrected only from
the pinned error value, and that the migration is idempotent and dry-run-safe.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0029_repair_fragaria_runner_binding import migration


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
                    if "to_id" in bind_vars:
                        doc["_to"] = bind_vars["to_id"]
                    if "score" in bind_vars:
                        doc["allelopathy_score"] = bind_vars["score"]
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

    def species(self, key: str) -> dict[str, Any]:
        return next(s for s in self._collections[col.SPECIES] if s["_key"] == key)


def _seq_id(key: str) -> str:
    return f"{col.PHASE_SEQUENCES}/{key}"


def _sp_id(key: str) -> str:
    return f"{col.SPECIES}/{key}"


def _collections() -> dict[str, list[dict[str, Any]]]:
    return {
        col.PHASE_SEQUENCES: [
            {"_key": "indoor", "name": "indoor_default"},
            {"_key": "evergreen", "name": "evergreen_foliage_perennial"},
            {"_key": "runner", "name": "perennial_runner"},
        ],
        col.SPECIES: [
            {"_key": "sp-frag", "scientific_name": "Fragaria x ananassa", "allelopathy_score": 0.1},
            # non-scoped species that must not be touched.
            {"_key": "sp-ficus", "scientific_name": "Ficus benjamina", "allelopathy_score": 0.0},
        ],
        col.HAS_PHASE_SEQUENCE: [
            # strawberry stuck on the annual blanket (the #541 symptom).
            {"_key": "e-frag", "_from": _sp_id("sp-frag"), "_to": _seq_id("indoor")},
            # non-scoped Ficus on evergreen — must stay.
            {"_key": "e-ficus", "_from": _sp_id("sp-ficus"), "_to": _seq_id("evergreen")},
        ],
    }


class TestMigration:
    def test_rebinds_and_fixes_allelopathy(self) -> None:
        collections = _collections()
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details == {"rebound": 1, "created": 0, "allelopathy_fixed": 1}
        assert report.changed == 2
        assert db.edges_from(_sp_id("sp-frag"))[0]["_to"] == _seq_id("runner")
        assert db.species("sp-frag")["allelopathy_score"] == -0.4
        # non-scoped Ficus untouched.
        assert db.edges_from(_sp_id("sp-ficus"))[0]["_to"] == _seq_id("evergreen")
        assert db.species("sp-ficus")["allelopathy_score"] == 0.0

    def test_creates_edge_when_absent(self) -> None:
        collections = _collections()
        collections[col.HAS_PHASE_SEQUENCE] = [e for e in collections[col.HAS_PHASE_SEQUENCE] if e["_key"] != "e-frag"]
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]
        assert report.details["created"] == 1
        frag_edges = db.edges_from(_sp_id("sp-frag"))
        assert len(frag_edges) == 1 and frag_edges[0]["_to"] == _seq_id("runner")

    def test_precise_binding_not_clobbered(self) -> None:
        collections = _collections()
        for edge in collections[col.HAS_PHASE_SEQUENCE]:
            if edge["_key"] == "e-frag":
                edge["_to"] = _seq_id("runner")
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]
        assert report.details["rebound"] == 0
        assert db.edges_from(_sp_id("sp-frag"))[0]["_to"] == _seq_id("runner")

    def test_allelopathy_untouched_when_not_error_value(self) -> None:
        """A score that is not the pinned error value is left alone."""
        collections = _collections()
        collections[col.SPECIES][0]["allelopathy_score"] = -0.4  # already corrected
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]
        assert report.details["allelopathy_fixed"] == 0
        assert db.species("sp-frag")["allelopathy_score"] == -0.4

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
        assert db.edges_from(_sp_id("sp-frag"))[0]["_to"] == _seq_id("indoor")
        assert db.species("sp-frag")["allelopathy_score"] == 0.1

    def test_missing_sequence_is_skipped(self) -> None:
        collections = _collections()
        collections[col.PHASE_SEQUENCES] = [
            s for s in collections[col.PHASE_SEQUENCES] if s["name"] != "perennial_runner"
        ]
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]
        # edge not rebound (no target), but allelopathy is an independent fix → still applies.
        assert report.details["rebound"] == 0
        assert db.edges_from(_sp_id("sp-frag"))[0]["_to"] == _seq_id("indoor")
        assert db.species("sp-frag")["allelopathy_score"] == -0.4
