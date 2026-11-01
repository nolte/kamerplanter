"""Tests for v0103_clear_spinach_light_requirement (#2516, E-10).

Verifies against a fake ArangoDB that the global seed row of *Spinacia oleracea*
loses its retired ``full_sun`` value, that a tenant-owned or user-created spinach row
and a value changed since are never touched, that another species is left alone,
that the frozen correction agrees with today's seed, and that the migration is
idempotent and dry-run-safe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.data_access.arango import collections as col
from app.migrations.versions.v0103_clear_spinach_light_requirement import migration

_SEED_DIR = Path(__file__).resolve().parents[4] / "app" / "migrations" / "seed_data"


class _FakeAql:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections
        self.writes = 0

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        tokens = query.split()
        if query.lstrip().startswith("UPDATE"):
            assert "light_requirement: null" in query
            collection = tokens[tokens.index("IN") + 1]
            for doc in self._collections.setdefault(collection, []):
                if doc["_key"] == bind_vars["key"]:
                    doc["light_requirement"] = None
                    self.writes += 1
            return iter([])
        collection = tokens[tokens.index("IN") + 1]
        return iter([dict(doc) for doc in self._collections.setdefault(collection, [])])


class _FakeDb:
    def __init__(self, collections: dict[str, list[dict[str, Any]]]) -> None:
        self._collections = collections
        self.aql = _FakeAql(collections)

    def has_collection(self, name: str) -> bool:
        return name in self._collections

    def species(self, key: str) -> dict[str, Any]:
        return next(d for d in self._collections[col.SPECIES] if d["_key"] == key)


def _spinach(key: str, **overrides: Any) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "_key": key,
        "scientific_name": "Spinacia oleracea",
        "origin": "system",
        "tenant_key": "",
        "light_requirement": "full_sun",
    }
    doc.update(overrides)
    return doc


def _db(*species: dict[str, Any]) -> _FakeDb:
    return _FakeDb({col.SPECIES: list(species)})


class TestMigration:
    def test_clears_the_retired_value_on_the_global_seed_row(self) -> None:
        db = _db(_spinach("sp-spinach"))

        report = migration.up(db)

        assert db.species("sp-spinach")["light_requirement"] is None
        assert report.changed == 1
        assert report.details == {"cleared": 1}

    def test_legacy_row_without_tenant_key_is_global(self) -> None:
        doc = _spinach("sp-spinach")
        del doc["tenant_key"]
        db = _db(doc)

        migration.up(db)

        assert db.species("sp-spinach")["light_requirement"] is None

    def test_tenant_owned_row_is_untouched(self) -> None:
        db = _db(_spinach("sp-tenant", tenant_key="tenant-a"))

        report = migration.up(db)

        assert db.species("sp-tenant")["light_requirement"] == "full_sun"
        assert report.changed == 0

    def test_user_created_row_is_untouched(self) -> None:
        db = _db(_spinach("sp-user", origin="tenant"))

        migration.up(db)

        assert db.species("sp-user")["light_requirement"] == "full_sun"

    def test_value_changed_since_is_untouched(self) -> None:
        db = _db(_spinach("sp-spinach", light_requirement="partial_shade"))

        report = migration.up(db)

        assert db.species("sp-spinach")["light_requirement"] == "partial_shade"
        assert report.changed == 0

    def test_other_species_is_untouched(self) -> None:
        other = {
            "_key": "sp-tomato",
            "scientific_name": "Solanum lycopersicum",
            "origin": "system",
            "tenant_key": "",
            "light_requirement": "full_sun",
        }
        db = _db(other)

        migration.up(db)

        assert db.species("sp-tomato")["light_requirement"] == "full_sun"

    def test_idempotent(self) -> None:
        db = _db(_spinach("sp-spinach"))

        migration.up(db)
        second = migration.up(db)

        assert second.changed == 0
        assert db.aql.writes == 1

    def test_dry_run_writes_nothing(self) -> None:
        db = _db(_spinach("sp-spinach"))

        report = migration.up(db, dry_run=True)

        assert db.species("sp-spinach")["light_requirement"] == "full_sun"
        assert report.dry_run is True
        assert report.scanned == 1
        assert report.changed == 0
        assert db.aql.writes == 0

    def test_missing_collection_is_a_noop(self) -> None:
        report = migration.up(_FakeDb({}))

        assert report.changed == 0


def test_seed_no_longer_carries_the_retired_value() -> None:
    """The frozen correction only makes sense while the seed itself says ``null``."""
    data = yaml.safe_load((_SEED_DIR / "plant_info_outdoor_2.yaml").read_text(encoding="utf-8"))
    spinach = next(e for e in data["new_species"] if e["scientific_name"] == "Spinacia oleracea")

    assert "light_requirement" in spinach
    assert spinach["light_requirement"] is None
