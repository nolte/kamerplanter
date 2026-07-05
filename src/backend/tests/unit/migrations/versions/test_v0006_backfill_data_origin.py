"""Tests for v0006_backfill_data_origin.

The migration stamps the ``origin`` provenance marker on master data that predates
the field: ``system`` for records whose natural key is part of the seed set,
``tenant`` for everything else (user-created data that must stay editable).
Records that already carry an ``origin`` are never touched (idempotency).
"""

from __future__ import annotations

from app.common.enums import DataOrigin
from app.migrations.versions.v0006_backfill_data_origin import (
    _seed_cultivar_identities,
    _seed_disease_names,
    _seed_species_names,
    _seed_treatment_names,
    migration,
)

# Natural keys that are known to exist in the seed YAMLs (species.yaml / ipm.yaml).
SEED_SPECIES = "Solanum lycopersicum"
SEED_CULTIVAR = ("Solanum lycopersicum", "San Marzano")
SEED_DISEASE = "Botrytis cinerea"
SEED_TREATMENT = "Crop Rotation"


class _FakeAql:
    def __init__(self, data: dict[str, dict[str, dict]]) -> None:
        self._data = data

    def execute(self, query: str, bind_vars: dict | None = None):
        bind_vars = bind_vars or {}
        if "UPDATE" in query:
            collection = bind_vars["@collection"]
            origin = bind_vars["origin"]
            for key in bind_vars["keys"]:
                self._data[collection][key]["origin"] = origin
            return iter([])
        if "cultivars" in query:
            return iter(
                {"key": k, "name": d.get("name"), "species_key": d.get("species_key")}
                for k, d in self._data["cultivars"].items()
                if d.get("origin") is None
            )
        if "diseases" in query:
            return iter(
                {"key": k, "scientific_name": d.get("scientific_name")}
                for k, d in self._data["diseases"].items()
                if d.get("origin") is None
            )
        if "treatments" in query:
            return iter(
                {"key": k, "name": d.get("name")}
                for k, d in self._data["treatments"].items()
                if d.get("origin") is None
            )
        if "species" in query:
            items = self._data["species"].items()
            if "d.origin == null" in query:
                items = [(k, d) for k, d in items if d.get("origin") is None]
            return iter({"key": k, "scientific_name": d.get("scientific_name")} for k, d in items)
        return iter([])


class _FakeDb:
    def __init__(self, data: dict[str, dict[str, dict]]) -> None:
        self.data = data
        self.aql = _FakeAql(data)


def _sample_data() -> dict[str, dict[str, dict]]:
    return {
        "species": {
            "sp_seed": {"scientific_name": SEED_SPECIES},
            "sp_user": {"scientific_name": "Userplant customica"},
            # Already stamped — must be left untouched.
            "sp_done": {"scientific_name": SEED_SPECIES, "origin": DataOrigin.TENANT.value},
        },
        "cultivars": {
            "cv_seed": {"name": SEED_CULTIVAR[1], "species_key": "sp_seed"},
            "cv_user": {"name": "My Backyard Special", "species_key": "sp_seed"},
        },
        "diseases": {
            "d_seed": {"scientific_name": SEED_DISEASE},
            "d_user": {"scientific_name": "Madeupensis fictiva"},
        },
        "treatments": {
            "t_seed": {"name": SEED_TREATMENT},
            "t_user": {"name": "My Homebrew Spray"},
        },
    }


class TestSeedSets:
    def test_seed_species_names_include_known_seed(self):
        assert SEED_SPECIES in _seed_species_names()

    def test_seed_cultivar_identities_include_known_seed(self):
        assert SEED_CULTIVAR in _seed_cultivar_identities()

    def test_seed_disease_names_include_known_seed(self):
        assert SEED_DISEASE in _seed_disease_names()

    def test_seed_treatment_names_include_known_seed(self):
        assert SEED_TREATMENT in _seed_treatment_names()


class TestBackfill:
    def test_seed_records_become_system_user_records_become_tenant(self):
        data = _sample_data()
        db = _FakeDb(data)

        report = migration.up(db)

        assert data["species"]["sp_seed"]["origin"] == DataOrigin.SYSTEM.value
        assert data["species"]["sp_user"]["origin"] == DataOrigin.TENANT.value
        assert data["cultivars"]["cv_seed"]["origin"] == DataOrigin.SYSTEM.value
        assert data["cultivars"]["cv_user"]["origin"] == DataOrigin.TENANT.value
        assert data["diseases"]["d_seed"]["origin"] == DataOrigin.SYSTEM.value
        assert data["diseases"]["d_user"]["origin"] == DataOrigin.TENANT.value
        assert data["treatments"]["t_seed"]["origin"] == DataOrigin.SYSTEM.value
        assert data["treatments"]["t_user"]["origin"] == DataOrigin.TENANT.value
        # 8 origin-less docs were stamped; sp_done was already stamped and skipped.
        assert report.changed == 8
        assert report.scanned == 8

    def test_existing_origin_is_never_overwritten(self):
        data = _sample_data()
        migration.up(_FakeDb(data))
        # sp_done kept its pre-existing 'tenant' origin despite being a seed name.
        assert data["species"]["sp_done"]["origin"] == DataOrigin.TENANT.value

    def test_rerun_is_a_noop(self):
        data = _sample_data()
        migration.up(_FakeDb(data))
        report = migration.up(_FakeDb(data))
        assert report.changed == 0
        assert report.noop is True

    def test_dry_run_writes_nothing(self):
        data = _sample_data()
        report = migration.up(_FakeDb(data), dry_run=True)
        assert report.dry_run is True
        assert report.changed == 0
        assert "origin" not in data["species"]["sp_seed"]
        assert "origin" not in data["diseases"]["d_user"]

    def test_report_counts_breakdown(self):
        data = _sample_data()
        report = migration.up(_FakeDb(data))
        counts = report.details["counts"]
        assert counts["species"] == {"system": 1, "tenant": 1}
        assert counts["treatments"] == {"system": 1, "tenant": 1}

    def test_migration_metadata(self):
        assert migration.version == "0006"
        assert migration.reversible is False
