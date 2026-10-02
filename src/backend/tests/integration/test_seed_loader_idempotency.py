"""#1956 — the seed registry run on every boot must not multiply catalogue rows.

``run_seed`` wrapped ``create_indicator`` in a ``try/except`` that logged
``harvest_indicator_exists``. The collection has no unique index, so the insert
never failed and the ``except`` never fired: 173 rows more on every start. The IPM
treatment edges (``targets_pest``, ``targets_disease``, ``contraindicated_with``)
had the same shape through ``create_edge``.

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

#: The collections the two defects multiplied. Counted per boot, never as a total.
_MEASURED = ("harvest_indicators", "has_harvest_indicator", "targets_pest", "targets_disease", "contraindicated_with")


@pytest.fixture(scope="module")
def booted_twice():
    """``{boot: {collection: rows}}`` after the registry ran twice over one database."""
    monkeypatch = pytest.MonkeyPatch()
    system, db = create_database(_DB_NAME)
    bind_database(monkeypatch, db)
    try:
        counts: dict[int, dict[str, int]] = {}
        for boot in (1, 2):
            run_seeds(db)
            counts[boot] = {name: db.collection(name).count() for name in _MEASURED}
        yield db, counts
    finally:
        monkeypatch.undo()
        system.delete_database(_DB_NAME)


@pytest.mark.parametrize("collection", _MEASURED)
def test_a_second_boot_leaves_the_row_count_unchanged(booted_twice, collection: str) -> None:
    _, counts = booted_twice

    assert counts[1][collection] > 0, "the first boot seeded nothing — the measurement would be vacuous"
    assert counts[2][collection] == counts[1][collection]


def test_every_harvest_indicator_has_a_species_and_a_unique_identity(booted_twice) -> None:
    db, _ = booted_twice

    rows = list(db.collection("harvest_indicators").all())
    identities = Counter((r["species_key"], r["indicator_type"], r["measurement_unit"]) for r in rows)

    assert all(r["species_key"] for r in rows), "an indicator was created reachable through no species"
    assert [k for k, n in identities.items() if n > 1] == []


def test_every_seed_entry_whose_species_exists_is_in_the_catalogue(booted_twice) -> None:
    db, _ = booted_twice
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
    db, _ = booted_twice
    row = next(iter(db.collection("harvest_indicators").all()))
    db.collection("harvest_indicators").update({"_key": row["_key"], "reliability_score": 0.01})
    before = db.collection("harvest_indicators").get(row["_key"])

    run_seeds(db)

    assert db.collection("harvest_indicators").get(row["_key"]) == before
