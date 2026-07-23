"""Tests for v0028_rebind_dendrobium_nobile_cam_succulent_rest (#680).

Verifies against a fake ArangoDB that Dendrobium nobile is re-pointed off the generic
``evergreen_foliage_perennial`` blanket (its pre-fix binding) onto ``cam_succulent_rest``,
that the older ``indoor_default`` blanket is also caught, that a species with no edge gets
one created, that an edge already on a *precise* sequence is left untouched, that a
non-scoped species is never touched, and that the migration is idempotent and dry-run-safe.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0028_rebind_dendrobium_nobile_cam_succulent_rest import migration


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
        ],
        col.SPECIES: [
            # Dendrobium on its pre-fix generic evergreen blanket.
            {"_key": "sp-dendrobium", "scientific_name": "Dendrobium nobile"},
            # non-scoped species that must not be touched.
            {"_key": "sp-ficus", "scientific_name": "Ficus benjamina"},
        ],
        col.HAS_PHASE_SEQUENCE: [
            {"_key": "e-dendrobium", "_from": _sp_id("sp-dendrobium"), "_to": _seq_id("evergreen")},
            # non-scoped Ficus on evergreen — must stay.
            {"_key": "e-ficus", "_from": _sp_id("sp-ficus"), "_to": _seq_id("evergreen")},
        ],
    }


class TestMigration:
    def test_rebinds_dendrobium_off_evergreen_blanket(self) -> None:
        collections = _collections()
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details == {"rebound": 1, "created": 0}
        assert report.changed == 1
        assert db.edges_from(_sp_id("sp-dendrobium"))[0]["_to"] == _seq_id("cam")
        # non-scoped Ficus untouched.
        assert db.edges_from(_sp_id("sp-ficus"))[0]["_to"] == _seq_id("evergreen")

    def test_rebinds_off_indoor_default_blanket(self) -> None:
        """An even older install bound to indoor_default is also caught."""
        collections = _collections()
        for edge in collections[col.HAS_PHASE_SEQUENCE]:
            if edge["_key"] == "e-dendrobium":
                edge["_to"] = _seq_id("indoor")
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details == {"rebound": 1, "created": 0}
        assert db.edges_from(_sp_id("sp-dendrobium"))[0]["_to"] == _seq_id("cam")

    def test_creates_edge_when_absent(self) -> None:
        """A Dendrobium with no has_phase_sequence edge gets one created."""
        collections = _collections()
        collections[col.HAS_PHASE_SEQUENCE] = [
            e for e in collections[col.HAS_PHASE_SEQUENCE] if e["_key"] != "e-dendrobium"
        ]
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details == {"rebound": 0, "created": 1}
        edges = db.edges_from(_sp_id("sp-dendrobium"))
        assert len(edges) == 1 and edges[0]["_to"] == _seq_id("cam")

    def test_precise_binding_not_clobbered(self) -> None:
        """An edge already on cam_succulent_rest is never re-pointed and not counted."""
        collections = _collections()
        for edge in collections[col.HAS_PHASE_SEQUENCE]:
            if edge["_key"] == "e-dendrobium":
                edge["_to"] = _seq_id("cam")
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.details == {"rebound": 0, "created": 0}
        assert report.noop is True
        assert db.edges_from(_sp_id("sp-dendrobium"))[0]["_to"] == _seq_id("cam")

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
        assert db.edges_from(_sp_id("sp-dendrobium"))[0]["_to"] == _seq_id("evergreen")

    def test_missing_target_sequence_is_skipped(self) -> None:
        """When cam_succulent_rest is not seeded, the species is skipped cleanly."""
        collections = _collections()
        collections[col.PHASE_SEQUENCES] = [
            s for s in collections[col.PHASE_SEQUENCES] if s["name"] != "cam_succulent_rest"
        ]
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]
        assert report.changed == 0
        assert db.edges_from(_sp_id("sp-dendrobium"))[0]["_to"] == _seq_id("evergreen")
