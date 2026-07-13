"""Tests for v0023_document_instance_cultivation_cycle (ADR-006 E1 / E7, #565 Phase 2).

The migration is a pure, no-op documentation step for the additive, schemaless
PlantInstance.cultivation_cycle_type field: it counts live instances and the subset
that inherit the species default (no override), and writes nothing.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.migrations.versions.v0023_document_instance_cultivation_cycle import migration


class _FakeAql:
    """Interprets the migration's single ``FOR d IN <col> RETURN d.cultivation_cycle_type`` scan."""

    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections
        self.executed: list[str] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.executed.append(query)
        tokens = query.split()
        collection = tokens[tokens.index("IN") + 1]
        docs = self._collections.get(collection, [])
        return iter([d.get("cultivation_cycle_type") for d in docs])


class _FakeDb:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self.aql = _FakeAql(collections)


def _collections(*overrides: str | None) -> dict[str, list[dict[str, Any]]]:
    return {
        col.PLANT_INSTANCES: [
            {"_key": f"plant-{i}", "cultivation_cycle_type": value} for i, value in enumerate(overrides)
        ],
    }


class TestMigration:
    def test_counts_total_and_inheriting_without_writing(self) -> None:
        db = _FakeDb(_collections(None, "annual", None, "perennial"))
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.scanned == 4
        assert report.changed == 0  # additive/schemaless — nothing transformed
        assert report.details["inheriting_species_default"] == 2
        # Pure read: only the scan query ran, no UPDATE/INSERT.
        assert all("UPDATE" not in q and "INSERT" not in q for q in db.aql.executed)

    def test_empty_database_is_a_noop(self) -> None:
        db = _FakeDb(_collections())
        report = migration.up(db)  # type: ignore[arg-type]

        assert report.scanned == 0
        assert report.changed == 0
        assert report.noop

    def test_dry_run_matches_normal_run(self) -> None:
        db = _FakeDb(_collections(None, "annual"))
        dry = migration.up(db, dry_run=True)  # type: ignore[arg-type]
        wet = migration.up(db, dry_run=False)  # type: ignore[arg-type]

        assert dry.scanned == wet.scanned == 2
        assert dry.changed == wet.changed == 0
        assert migration.reversible is False
