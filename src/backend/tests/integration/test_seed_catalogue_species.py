"""#2857 SEC-001 - the seed loaders resolve a YAML species name among the global catalogue rows only.

A tenant created a species under a catalogue name (hemp) before the catalogue seeded it. ``scientific_name`` is unique
across catalogue and tenants, so no catalogue row of that name can exist beside it. Measured against a real server
through the production loaders (core seed, Adventskalender, plant info, plant info extended, outdoor lifecycles,
starter kits):

* the tenant's species, its lifecycle and the requirement profile of its phase stay exactly as the tenant stored them
  - no catalogue photoperiod type, no Steckbrief light hours, no phase replacement, no synced names;
* no second row of the name is created and the seed run does not fail on the unique index;
* the global catalogue species get their values (Guzmania lingulata: the ``day_neutral`` its lifecycle_config
  states; a species.yaml species without a source: ``unspecified``);
* ``get_global_by_scientific_name`` answers ``None`` for the tenant's name and the row for a global one.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.species_repository import ArangoSpeciesRepository
from app.migrations.seed_adventskalender import run_seed_adventskalender
from app.migrations.seed_data import run_seed
from app.migrations.seed_lifecycles_outdoor import run_seed_lifecycles_outdoor
from app.migrations.seed_plant_info import run_seed_plant_info
from app.migrations.seed_plant_info_extended import run_seed_plant_info_extended
from app.migrations.seed_starter_kits import run_seed_starter_kits
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the seed loaders' name resolution is measured against a real server"),
]

_DB_NAME = run_database_name("seed_catalogue_species")
_NAME = "Cannabis sativa"
_TENANT = "t_grower"


def _plant_tenant_hemp(db: StandardDatabase) -> None:
    db.collection(col.SPECIES).insert(
        {
            "_key": "sp_tenant_hemp",
            "scientific_name": _NAME,
            "scientific_name_normalized": "cannabis sativa",
            "tenant_key": _TENANT,
            "common_names": ["Mein Hanf"],
            "origin": "tenant",
        }
    )
    db.collection(col.LIFECYCLE_CONFIGS).insert(
        {
            "_key": "lc_tenant_hemp",
            "species_key": "sp_tenant_hemp",
            "cycle_type": "annual",
            "photoperiod_type": "long_day",
        }
    )
    db.collection(col.HAS_LIFECYCLE).insert(
        {"_from": f"{col.SPECIES}/sp_tenant_hemp", "_to": f"{col.LIFECYCLE_CONFIGS}/lc_tenant_hemp"}
    )
    db.collection(col.GROWTH_PHASES).insert(
        {
            "_key": "gp_tenant_veg",
            "name": "vegetative",
            "display_name": "Wachstum",
            "lifecycle_key": "lc_tenant_hemp",
            "typical_duration_days": 40,
            "sequence_order": 1,
        }
    )
    db.collection(col.CONSISTS_OF).insert(
        {"_from": f"{col.LIFECYCLE_CONFIGS}/lc_tenant_hemp", "_to": f"{col.GROWTH_PHASES}/gp_tenant_veg"}
    )
    db.collection(col.REQUIREMENT_PROFILES).insert(
        {"_key": "rp_tenant_veg", "phase_key": "gp_tenant_veg", "photoperiod_hours": 20.0}
    )
    db.collection(col.REQUIRES_PROFILE).insert(
        {"_from": f"{col.GROWTH_PHASES}/gp_tenant_veg", "_to": f"{col.REQUIREMENT_PROFILES}/rp_tenant_veg"}
    )


def _snapshot(db: StandardDatabase) -> dict[str, Any]:
    strip = ("_rev", "updated_at")

    def doc(collection: str, key: str) -> dict[str, Any]:
        return {k: v for k, v in db.collection(collection).get(key).items() if k not in strip}

    return {
        "species": doc(col.SPECIES, "sp_tenant_hemp"),
        "lifecycle": doc(col.LIFECYCLE_CONFIGS, "lc_tenant_hemp"),
        "phase": doc(col.GROWTH_PHASES, "gp_tenant_veg"),
        "profile": doc(col.REQUIREMENT_PROFILES, "rp_tenant_veg"),
        "phases": sorted(
            db.aql.execute(
                "FOR p IN 1..1 OUTBOUND @lc @@consists_of RETURN p._key",
                bind_vars={"lc": f"{col.LIFECYCLE_CONFIGS}/lc_tenant_hemp", "@consists_of": col.CONSISTS_OF},
            )
        ),
    }


@pytest.fixture(scope="module")
def seeded():
    monkeypatch = pytest.MonkeyPatch()
    system, database = create_database(_DB_NAME)
    bind_database(monkeypatch, database)
    _plant_tenant_hemp(database)
    before = _snapshot(database)
    run_seed()
    run_seed_starter_kits()
    run_seed_adventskalender()
    run_seed_plant_info()
    run_seed_plant_info_extended()
    run_seed_lifecycles_outdoor()
    yield database, before
    monkeypatch.undo()
    system.delete_database(_DB_NAME)


def _global_lifecycle_type(db: StandardDatabase, name: str) -> str | None:
    rows = list(
        db.aql.execute(
            """
            FOR sp IN @@species
                FILTER sp.scientific_name == @name AND (sp.tenant_key == null OR sp.tenant_key == "")
                FOR lc IN 1..1 OUTBOUND sp @@has_lifecycle
                    RETURN lc.photoperiod_type
            """,
            bind_vars={"@species": col.SPECIES, "@has_lifecycle": col.HAS_LIFECYCLE, "name": name},
        )
    )
    return rows[0] if rows else None


def test_the_tenants_species_lifecycle_and_profiles_are_untouched(seeded) -> None:
    db, before = seeded

    assert _snapshot(db) == before


def test_no_catalogue_row_of_the_tenants_name_is_created(seeded) -> None:
    db, _ = seeded

    rows = list(
        db.aql.execute(
            "FOR s IN @@species FILTER s.scientific_name == @name RETURN s._key",
            bind_vars={"@species": col.SPECIES, "name": _NAME},
        )
    )

    assert rows == ["sp_tenant_hemp"]


def test_the_global_species_get_their_values(seeded) -> None:
    db, _ = seeded

    assert _global_lifecycle_type(db, "Guzmania lingulata") == "day_neutral"
    assert _global_lifecycle_type(db, "Ocimum basilicum") == "day_neutral"


def test_no_global_seed_row_points_at_the_tenants_species(seeded) -> None:
    db, _ = seeded

    referencing = list(
        db.aql.execute(
            """
            FOR kit IN @@kits
                FILTER POSITION(kit.species_keys || [], "sp_tenant_hemp")
                RETURN kit._key
            """,
            bind_vars={"@kits": col.STARTER_KITS},
        )
    )

    assert referencing == []


def test_the_repository_resolves_global_rows_only(seeded) -> None:
    db, _ = seeded
    repo = ArangoSpeciesRepository(db)

    assert repo.get_global_by_scientific_name(_NAME) is None
    basil = repo.get_global_by_scientific_name("Ocimum basilicum")
    assert basil is not None and not basil.tenant_key
