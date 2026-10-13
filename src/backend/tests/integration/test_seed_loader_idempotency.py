"""#1956 — the seed registry run on every boot must not multiply catalogue rows.

``run_seed`` wrapped ``create_indicator`` in a ``try/except`` that logged
``harvest_indicator_exists``. The collection has no unique index, so the insert
never failed and the ``except`` never fired: 173 rows more on every start. The IPM
treatment edges (``targets_pest``, ``targets_disease``, ``contraindicated_with``)
had the same shape through ``create_edge``.

#2002 is a different shape on the same measurement: ``adventskalender`` created the
five growth phases of *Cichorium intybus* and ``plant_info_extended`` (which lists the
species' lifecycle but no phases) deleted them again on every start. Both happen within
one boot, so the end state of ``growth_phases`` looks unchanged; what shows it is the
phases' requirement and nutrient profiles, which the deletion left behind (five more
of each per boot), and the species left without the phases its seed file carries.

Only a real server shows it, and only the real entry point (``run_seeds``) shows
that the registry — not a re-implementation — is idempotent.
"""

from __future__ import annotations

from collections import Counter

import pytest

from app.migrations.seed_harvest_indicators import load_harvest_indicator_entries
from app.migrations.seeds.registry import run_seeds
from tests.support.arango_integration import run_database_name
from tests.support.seed_boot import bind_database, create_database

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the seed registry is measured against a real server"),
]

_DB_NAME = run_database_name("seed_loader_idempotency")

#: The collections the defects multiplied. Counted per boot, never as a total.
_MEASURED = (
    "harvest_indicators",
    "has_harvest_indicator",
    "targets_pest",
    "targets_disease",
    "contraindicated_with",
    # #2002
    "growth_phases",
    "requirement_profiles",
    "nutrient_profiles",
    "consists_of",
    "requires_profile",
    "uses_nutrients",
)

#: ``profile collection → the edge that reaches it from its phase`` (#2002).
_PROFILE_EDGES = {"requirement_profiles": "requires_profile", "nutrient_profiles": "uses_nutrients"}


def _orphaned_profiles(db, profiles: str) -> int:
    """Profiles no phase edge reaches — what ``delete_phase`` used to leave behind (#2002)."""
    cursor = db.aql.execute(
        "RETURN LENGTH(FOR p IN @@profiles FILTER LENGTH(FOR e IN @@edges FILTER e._to == p._id LIMIT 1 RETURN 1) == 0 "
        "RETURN 1)",
        bind_vars={"@profiles": profiles, "@edges": _PROFILE_EDGES[profiles]},
    )
    return int(next(cursor))


@pytest.fixture(scope="module")
def booted_twice():
    """``{boot: {collection: rows}}`` and ``{boot: growth phase keys}`` after the registry ran twice."""
    monkeypatch = pytest.MonkeyPatch()
    system, db = create_database(_DB_NAME)
    bind_database(monkeypatch, db)
    try:
        counts: dict[int, dict[str, int]] = {}
        phase_keys: dict[int, set[str]] = {}
        for boot in (1, 2):
            run_seeds(db)
            counts[boot] = {name: db.collection(name).count() for name in _MEASURED}
            phase_keys[boot] = set(db.aql.execute("FOR p IN growth_phases RETURN p._key"))
        yield db, counts, phase_keys
    finally:
        monkeypatch.undo()
        system.delete_database(_DB_NAME)


@pytest.mark.parametrize("collection", _MEASURED)
def test_a_second_boot_leaves_the_row_count_unchanged(booted_twice, collection: str) -> None:
    _, counts, _ = booted_twice

    assert counts[1][collection] > 0, "the first boot seeded nothing — the measurement would be vacuous"
    assert counts[2][collection] == counts[1][collection]


def test_every_harvest_indicator_has_a_species_and_a_unique_identity(booted_twice) -> None:
    db, _, _ = booted_twice

    rows = list(db.collection("harvest_indicators").all())
    identities = Counter((r["species_key"], r["indicator_type"], r["measurement_unit"]) for r in rows)

    assert all(r["species_key"] for r in rows), "an indicator was created reachable through no species"
    assert [k for k, n in identities.items() if n > 1] == []


def test_every_seed_entry_whose_species_exists_is_in_the_catalogue(booted_twice) -> None:
    db, _, _ = booted_twice
    species = {s["scientific_name"]: s["_key"] for s in db.collection("species").all()}
    stored = {
        (r["species_key"], r["indicator_type"], r["measurement_unit"])
        for r in db.collection("harvest_indicators").all()
    }

    expected = {
        (species[e["species_name"]], e["indicator_type"], e["measurement_unit"])
        for e in load_harvest_indicator_entries()
        if e["species_name"] in species
    }

    assert expected
    assert expected == stored


def test_a_hand_tuned_indicator_survives_a_boot(booted_twice) -> None:
    db, _, _ = booted_twice
    row = next(iter(db.collection("harvest_indicators").all()))
    db.collection("harvest_indicators").update({"_key": row["_key"], "reliability_score": 0.01})
    before = db.collection("harvest_indicators").get(row["_key"])

    run_seeds(db)

    assert db.collection("harvest_indicators").get(row["_key"]) == before


def test_a_second_boot_keeps_every_growth_phase_it_found(booted_twice) -> None:
    """A loader that deletes and re-creates phases on a boot keeps the count and changes the keys."""
    _, _, phase_keys = booted_twice

    assert phase_keys[1], "the first boot seeded no phase — the measurement would be vacuous"
    assert phase_keys[2] - phase_keys[1] == set()
    assert phase_keys[1] - phase_keys[2] == set()


@pytest.mark.parametrize("profiles", sorted(_PROFILE_EDGES))
def test_no_profile_is_left_without_its_phase(booted_twice, profiles: str) -> None:
    db, _, _ = booted_twice

    assert _orphaned_profiles(db, profiles) == 0


def test_the_species_whose_phases_one_file_owns_keeps_them(booted_twice) -> None:
    """*Cichorium intybus*: phases in ``adventskalender.yaml`` only, lifecycle in ``plant_info_outdoor_1.yaml`` too."""
    db, _, _ = booted_twice

    names = list(
        db.aql.execute(
            """
            FOR s IN species FILTER s.scientific_name == "Cichorium intybus"
                FOR lc IN lifecycle_configs FILTER lc.species_key == s._key
                    FOR p IN growth_phases FILTER p.lifecycle_key == lc._key
                        SORT p.sequence_order
                        RETURN p.name
            """
        )
    )
    assert names == ["germination", "seedling", "vegetative", "flowering", "dormancy"]
