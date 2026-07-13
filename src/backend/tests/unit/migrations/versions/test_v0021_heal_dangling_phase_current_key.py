"""Tests for v0021_heal_dangling_phase_current_key (#579 error #2).

Verifies the name-anchored heal decision (pure), plus the full migration against a
fake ArangoDB: a plant pointing at a dangling PhaseSequenceEntry key is repointed
onto the live entry (and its open phase-history entry), a plant already pointing at
a live key is untouched (idempotency), and dry-run writes nothing.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0021_heal_dangling_phase_current_key import (
    migration,
    open_phase_name,
    plan_healed_key,
)

# ── pure decision ─────────────────────────────────────────────────────────────


def _defs() -> dict[str, dict[str, Any]]:
    return {
        "pd-germ": {"_key": "pd-germ", "name": "germination"},
        "pd-veg": {"_key": "pd-veg", "name": "vegetative"},
        "pd-flower": {"_key": "pd-flower", "name": "flowering"},
    }


def _entries() -> list[dict[str, Any]]:
    return [
        {"_key": "e-germ", "phase_definition_key": "pd-germ", "sequence_order": 0, "phase_sequence_key": "seq-1"},
        {"_key": "e-veg", "phase_definition_key": "pd-veg", "sequence_order": 1, "phase_sequence_key": "seq-1"},
        {"_key": "e-flower", "phase_definition_key": "pd-flower", "sequence_order": 2, "phase_sequence_key": "seq-1"},
    ]


class TestPlanHealedKey:
    def test_matches_entry_by_definition_name(self) -> None:
        assert plan_healed_key("vegetative", _entries(), _defs()) == "e-veg"

    def test_no_anchor_returns_none(self) -> None:
        assert plan_healed_key("", _entries(), _defs()) is None

    def test_unmatched_name_returns_none(self) -> None:
        assert plan_healed_key("dormancy", _entries(), _defs()) is None


class TestOpenPhaseName:
    def test_prefers_open_entry(self) -> None:
        histories = [
            {"phase_name": "germination", "exited_at": "2025-01-10"},
            {"phase_name": "vegetative", "exited_at": None},
        ]
        assert open_phase_name(histories) == "vegetative"

    def test_falls_back_to_latest_closed(self) -> None:
        histories = [
            {"phase_name": "germination", "exited_at": "2025-01-10"},
            {"phase_name": "vegetative", "exited_at": "2025-02-10"},
        ]
        assert open_phase_name(histories) == "vegetative"

    def test_empty(self) -> None:
        assert open_phase_name([]) == ""


# ── full migration against a fake ArangoDB ────────────────────────────────────


class _FakeAql:
    """Interprets the migration's ``FOR d IN <col> RETURN d`` scans and
    ``UPDATE {_key: @key, …} IN <col>`` writes against in-memory collections."""

    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        tokens = query.split()
        collection = tokens[tokens.index("IN") + 1]
        docs = self._collections.setdefault(collection, [])
        if query.lstrip().startswith("UPDATE"):
            for doc in docs:
                if doc["_key"] != bind_vars["key"]:
                    continue
                if "current_phase_key: @new_key" in query:
                    doc["current_phase_key"] = bind_vars["new_key"]
                elif "phase_key: @new_key" in query:
                    doc["phase_key"] = bind_vars["new_key"]
            return iter([])
        return iter(list(docs))


class _FakeDb:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections
        self.aql = _FakeAql(collections)

    def doc(self, name: str, key: str) -> dict[str, Any]:
        return next(d for d in self._collections.get(name, []) if d["_key"] == key)


def _seeded_collections(*, current_phase_key: str) -> dict[str, list[dict[str, Any]]]:
    """A plant on species sp-1 (sequence seq-1) plus the live entries/defs/edge."""
    return {
        col.PLANT_INSTANCES: [
            {"_key": "plant-1", "species_key": "sp-1", "current_phase_key": current_phase_key},
        ],
        col.PHASE_HISTORIES: [
            {
                "_key": "h-1",
                "plant_instance_key": "plant-1",
                "phase_key": current_phase_key,
                "phase_name": "vegetative",
                "exited_at": None,
            },
        ],
        col.PHASE_SEQUENCE_ENTRIES: _entries(),
        col.PHASE_DEFINITIONS: list(_defs().values()),
        col.GROWTH_PHASES: [],
        col.HAS_PHASE_SEQUENCE: [
            {"_from": f"{col.SPECIES}/sp-1", "_to": f"{col.PHASE_SEQUENCES}/seq-1"},
        ],
    }


class TestMigration:
    def test_heals_dangling_key(self) -> None:
        db = _FakeDb(_seeded_collections(current_phase_key="e-stale"))
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.scanned == 1
        assert report.changed == 1
        plant = db.doc(col.PLANT_INSTANCES, "plant-1")
        history = db.doc(col.PHASE_HISTORIES, "h-1")
        assert plant["current_phase_key"] == "e-veg"
        # The open phase-history entry is repointed too (no dangling reference left).
        assert history["phase_key"] == "e-veg"

    def test_idempotent_on_live_key(self) -> None:
        db = _FakeDb(_seeded_collections(current_phase_key="e-veg"))
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.scanned == 0
        assert report.changed == 0
        assert db.doc(col.PLANT_INSTANCES, "plant-1")["current_phase_key"] == "e-veg"

    def test_dry_run_writes_nothing(self) -> None:
        db = _FakeDb(_seeded_collections(current_phase_key="e-stale"))
        report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

        assert report.dry_run is True
        assert report.changed == 1
        # No mutation happened.
        assert db.doc(col.PLANT_INSTANCES, "plant-1")["current_phase_key"] == "e-stale"
        assert db.doc(col.PHASE_HISTORIES, "h-1")["phase_key"] == "e-stale"

    def test_unhealable_without_anchor_reported(self) -> None:
        collections = _seeded_collections(current_phase_key="e-stale")
        # Strip the phase name anchor → cannot heal, must not guess.
        collections[col.PHASE_HISTORIES][0]["phase_name"] = ""
        db = _FakeDb(collections)
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.scanned == 1
        assert report.changed == 0
        assert report.details["unhealable"] == ["plant-1"]
        assert db.doc(col.PLANT_INSTANCES, "plant-1")["current_phase_key"] == "e-stale"
