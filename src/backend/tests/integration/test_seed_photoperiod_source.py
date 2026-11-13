"""The seed loaders stamp the provenance of a phase's light hours (#2857, REQ-003, REQ-053 §9.2a W-016.6).

No migration may add ``photoperiod_source`` (the privacy reservations hold the next migration numbers), so an existing
installation receives it through the loaders that run on every start. Measured against a real server, through the
production entry points:

* a fresh seed: Steckbrief phases (``plant_info*.yaml``, ``adventskalender.yaml``) carry ``sourced``; the generic
  phases of ``species.yaml`` (``default_phases``, one table for every species) carry ``generated`` - except the
  phases ``steckbrief_phase_photoperiods`` lists for a species (hemp): those carry the Steckbrief's hours as
  ``sourced``, and only their requirement profiles differ (same phases, names, durations, nutrient profiles);
* a re-seed over profiles stored before the field existed stamps ``sourced`` where the Steckbrief states the hours -
  also when the value is unchanged - and leaves every other profile's origin alone (no relabelling of a generator
  value, no migration);
* both ways, a hemp plant in the vegetative phase and one in flowering in one tent give ``tent.photoperiod_conflict``.
"""

from __future__ import annotations

from typing import Any

import pytest
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.garden_object_repository import ArangoGardenObjectRepository
from app.data_access.arango.garden_plan_repository import ArangoGardenPlanRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from app.domain.models.tent_hint import HINT_PHOTOPERIOD_CONFLICT
from app.domain.services.garden_plan_service import GardenPlanService
from app.domain.services.garden_resource_service import GardenResourceService
from app.migrations.seed_adventskalender import run_seed_adventskalender
from app.migrations.seed_data import run_seed
from app.migrations.seed_phase_ownership import species_with_seeded_phases
from app.migrations.seed_plant_info import run_seed_plant_info
from app.migrations.seed_plant_info_extended import run_seed_plant_info_extended
from app.migrations.yaml_loader import load_yaml
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the seed provenance is measured against a real server"),
]

_DB_NAME = run_database_name("seed_photoperiod_source")


@pytest.fixture(scope="module")
def seeded():
    """One seeded database for the module: the loaders in their registry order (``seeds/registry.py``)."""
    monkeypatch = pytest.MonkeyPatch()
    system, database = create_database(_DB_NAME)
    bind_database(monkeypatch, database)
    _seed()
    yield database
    monkeypatch.undo()
    system.delete_database(_DB_NAME)


def _seed() -> None:
    run_seed()
    run_seed_adventskalender()
    run_seed_plant_info()
    run_seed_plant_info_extended()


def _profiles(db: StandardDatabase, scientific_name: str) -> dict[str, dict[str, Any]]:
    """Phase name -> its requirement profile, for the global species ``scientific_name``."""
    rows = db.aql.execute(
        """
        FOR sp IN @@species
            FILTER sp.scientific_name == @name AND (sp.tenant_key == null OR sp.tenant_key == "")
            FOR lc IN 1..1 OUTBOUND sp @@has_lifecycle
                FOR phase IN 1..1 OUTBOUND lc @@consists_of
                    FOR profile IN 1..1 OUTBOUND phase @@requires_profile
                        RETURN {phase: phase.name, profile: profile}
        """,
        bind_vars={
            "@species": col.SPECIES,
            "@has_lifecycle": col.HAS_LIFECYCLE,
            "@consists_of": col.CONSISTS_OF,
            "@requires_profile": col.REQUIRES_PROFILE,
            "name": scientific_name,
        },
    )
    return {row["phase"]: row["profile"] for row in rows}


def _steckbrief_phases(filename: str, *, hours_key: str, requirement_key: str) -> tuple[str, dict[str, float]]:
    """The first species of ``filename`` whose phases all state their hours: its name and phase -> hours."""
    for name, phases in (load_yaml(filename).get("growth_phases") or {}).items():
        stated = {
            (p["phase"]["name"] if "phase" in p else p["name"]): p[requirement_key].get(hours_key)
            for p in (phases or [])
        }
        if stated and all(hours is not None for hours in stated.values()):
            return name, {phase: float(hours) for phase, hours in stated.items()}
    raise AssertionError(f"{filename} has no species whose phases all state their light hours")


def _generic_species() -> str:
    """A species of species.yaml seeded only with the generic default phases and no Steckbrief light hours."""
    data = load_yaml("species.yaml")
    listed = set(data["steckbrief_phase_photoperiods"])
    owned = species_with_seeded_phases()
    return next(
        entry["scientific_name"]
        for entry in data["species"]
        if entry["scientific_name"] not in owned and entry["scientific_name"] not in listed
    )


_TENANT = "ten_hemp"
_RECT = {"kind": "rect", "origin": [0, 0], "width_m": 4, "length_m": 4, "rotation_deg": 0}


def _hemp_tent_hints(db: StandardDatabase) -> list[str]:
    """A tent with one hemp plant in the vegetative and one in the flowering phase: the codes of its hints."""
    hemp = {name: profile["phase_key"] for name, profile in _profiles(db, "Cannabis sativa").items()}
    species_key = next(
        db.aql.execute(
            "FOR s IN @@c FILTER s.scientific_name == 'Cannabis sativa' AND s.tenant_key == '' RETURN s._key",
            bind_vars={"@c": col.SPECIES},
        )
    )
    for collection in (col.SITES, col.LOCATIONS, col.PLANT_INSTANCES):
        db.aql.execute("FOR d IN @@c FILTER d._key LIKE 'hemp_%' REMOVE d IN @@c", bind_vars={"@c": collection})
    db.collection(col.SITES).insert(
        {
            "_key": "hemp_site",
            "tenant_key": _TENANT,
            "name": "Grow room",
            "type": "indoor",
            "total_area_m2": 0.0,
            "timezone": "UTC",
            "plan": {"boundary": _RECT, "plan_revision": 1, "north_angle_deg": 0.0},
        }
    )
    db.collection(col.LOCATIONS).insert(
        {
            "_key": "hemp_tent",
            "site_key": "hemp_site",
            "name": "Tent",
            "location_type_key": "tent",
            "area_m2": 1.44,
            "depth": 0,
            "path": "hemp_tent",
            "geometry": {"kind": "rect", "origin": [1, 1], "width_m": 1.2, "length_m": 1.2, "rotation_deg": 0},
        }
    )
    for key, phase in (("hemp_veg", "vegetative"), ("hemp_flower", "flowering")):
        db.collection(col.PLANT_INSTANCES).insert(
            {
                "_key": key,
                "tenant_key": _TENANT,
                "instance_id": key.upper(),
                "species_key": species_key,
                "location_key": "hemp_tent",
                "current_phase_key": hemp[phase],
                "removed_on": None,
            }
        )
    sites = ArangoSiteRepository(db)
    plan = ArangoGardenPlanRepository(db)
    service = GardenResourceService(sites, plan, ArangoGardenObjectRepository(db), GardenPlanService(sites, plan))
    return [hint.code for hint in service.get_summary("hemp_tent", tenant_key=_TENANT).tent_hints]


def _forget_the_origins(db: StandardDatabase) -> None:
    """Give every stored profile the shape it had before #2857: no ``photoperiod_source``."""
    db.aql.execute(
        "FOR p IN @@c UPDATE p WITH {photoperiod_source: null} IN @@c OPTIONS {keepNull: false}",
        bind_vars={"@c": col.REQUIREMENT_PROFILES},
    )


def test_steckbrief_phases_are_sourced_and_generic_ones_generated(seeded: StandardDatabase) -> None:
    plant_info, stated = _steckbrief_phases(
        "plant_info.yaml", hours_key="photoperiod_hours", requirement_key="requirement_profile"
    )
    profiles = _profiles(seeded, plant_info)
    assert {name: (p["photoperiod_hours"], p["photoperiod_source"]) for name, p in profiles.items()} == {
        name: (hours, "sourced") for name, hours in stated.items()
    }

    advent, advent_stated = _steckbrief_phases(
        "adventskalender.yaml", hours_key="photoperiod", requirement_key="requirements"
    )
    advent_profiles = _profiles(seeded, advent)
    assert {name: p["photoperiod_source"] for name, p in advent_profiles.items()} == dict.fromkeys(
        advent_stated, "sourced"
    )

    # Hemp has no Steckbrief phases; its default phases get its Steckbrief's hours (steckbrief_phase_photoperiods).
    hemp = _profiles(seeded, "Cannabis sativa")
    assert {name: (p["photoperiod_hours"], p["photoperiod_source"]) for name, p in hemp.items()} == {
        "seedling": (18.0, "sourced"),
        "vegetative": (18.0, "sourced"),
        "flowering": (12.0, "sourced"),
        "flushing": (12.0, "generated"),  # the Steckbrief has no flushing phase (E-10)
        "ripening": (12.0, "sourced"),
    }
    # Any other generic species keeps the phase-name table's hours.
    generic = _profiles(seeded, _generic_species())
    assert generic and {p["photoperiod_source"] for p in generic.values()} <= {"generated", "default"}

    assert _hemp_tent_hints(seeded) == [HINT_PHOTOPERIOD_CONFLICT]


def test_a_reseed_stamps_stated_hours_and_relabels_nothing_else(seeded: StandardDatabase) -> None:
    plant_info, stated = _steckbrief_phases(
        "plant_info.yaml", hours_key="photoperiod_hours", requirement_key="requirement_profile"
    )
    advent, _ = _steckbrief_phases("adventskalender.yaml", hours_key="photoperiod", requirement_key="requirements")
    _forget_the_origins(seeded)
    assert {p.get("photoperiod_source") for p in _profiles(seeded, plant_info).values()} == {None}

    _seed()

    # Unchanged values, stamped on the patch path - no migration needed.
    assert {name: p.get("photoperiod_source") for name, p in _profiles(seeded, plant_info).items()} == dict.fromkeys(
        stated, "sourced"
    )
    # The adventskalender never patches existing phases; it vouches for values still equal to its own.
    assert {p.get("photoperiod_source") for p in _profiles(seeded, advent).values()} == {"sourced"}
    # Hemp: the Steckbrief's hours are stamped on the legacy profiles; flushing (no Steckbrief row) stays unknown.
    assert {name: p.get("photoperiod_source") for name, p in _profiles(seeded, "Cannabis sativa").items()} == {
        "seedling": "sourced",
        "vegetative": "sourced",
        "flowering": "sourced",
        "flushing": None,
        "ripening": "sourced",
    }
    # Other generic phases stay of unknown origin: nothing in a seed states their hours for that species.
    assert {p.get("photoperiod_source") for p in _profiles(seeded, _generic_species()).values()} == {None}
    assert _hemp_tent_hints(seeded) == [HINT_PHOTOPERIOD_CONFLICT]
