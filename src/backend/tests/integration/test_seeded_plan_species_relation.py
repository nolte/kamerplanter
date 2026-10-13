"""The seed loaders maintain the species relation on the seeded template plans (#1618).

The five loaders that write ``nutrient_plans`` (``seed_fertilizers``,
``seed_plagron``, ``seed_gardol``, ``seed_nutrient_plans_outdoor``,
``seed_nutrient_plans_ro``) run here **unmodified** against a real ArangoDB, in
the registry's order, over a species catalogue holding exactly the species the
seed files name. Only the three connection factories are redirected to the test
database. That makes this the wiring proof for the relation: a loader that
forgot to resolve ``species_names`` would leave its plans unlinked and the
counts below would move.

What it pins:

* every plan whose seed entry carries ``species_names`` ends up linked, and every
  plan without it ends up with an **empty** relation (not absent, not guessed);
* the onboarding match returns the tomato plan for the tomato species and none
  of the unlinked plans for any species;
* a second seed run is idempotent for the relation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.collections import ensure_collections
from app.data_access.arango.fertilizer_repository import ArangoFertilizerRepository
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.domain.calculators.scientific_name import normalize_scientific_name
from app.migrations import (
    seed_fertilizers,
    seed_gardol,
    seed_nutrient_plans_outdoor,
    seed_nutrient_plans_ro,
    seed_plagron,
)
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.onboarding_wiring import build_favorites_service

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the seed loaders write through the real repositories"),
]

TEST_DATABASE = run_database_name("seeded_plan_species")
SEED_DIR = Path(seed_fertilizers.__file__).parent / "seed_data"
PLAN_FILES = (
    "fertilizers.yaml",
    "plagron.yaml",
    "gardol.yaml",
    "nutrient_plans_outdoor.yaml",
    "nutrient_plans_ro.yaml",
)
LOADERS = (seed_fertilizers, seed_plagron, seed_gardol, seed_nutrient_plans_outdoor, seed_nutrient_plans_ro)
RUNNERS = (
    seed_fertilizers.run_seed_fertilizers,
    seed_plagron.run_seed_plagron,
    seed_gardol.run_seed_gardol,
    seed_nutrient_plans_outdoor.run_seed_nutrient_plans_outdoor,
    seed_nutrient_plans_ro.run_seed_nutrient_plans_ro,
)


def _seed_plans() -> list[dict]:
    plans: list[dict] = []
    for name in PLAN_FILES:
        plans.extend(yaml.safe_load((SEED_DIR / name).read_text(encoding="utf-8"))["nutrient_plans"])
    return plans


def _species_key(scientific_name: str) -> str:
    return scientific_name.lower().replace(" ", "-").replace(".", "")


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    ensure_collections(database)

    names = sorted({n for plan in _seed_plans() for n in plan.get("species_names", [])})
    species = database.collection(col.SPECIES)
    for n in names:
        # ``insert`` rather than ``insert_many``: the latter reports a refused
        # document in its return value instead of raising, and a species the
        # catalogue silently refused would read as an unlinked plan.
        species.insert(
            {
                "_key": _species_key(n),
                "scientific_name": n,
                "scientific_name_normalized": normalize_scientific_name(n),
                "tenant_key": "",
            }
        )

    yield database

    system.delete_database(TEST_DATABASE)


@pytest.fixture(scope="module")
def seeded(db):
    patch = pytest.MonkeyPatch()
    for module in LOADERS:
        patch.setattr(module, "get_db", lambda: db)
        patch.setattr(module, "get_fertilizer_repo", lambda: ArangoFertilizerRepository(db))
        patch.setattr(module, "get_nutrient_plan_repo", lambda: ArangoNutrientPlanRepository(db))
    try:
        for run in RUNNERS:
            run()
        yield db
    finally:
        patch.undo()


def _relations(db) -> dict[str, list[str]]:
    cursor = db.aql.execute(
        "FOR p IN nutrient_plans FILTER p.tenant_key == '' RETURN { name: p.name, species: p.species_keys }"
    )
    return {row["name"]: row["species"] for row in cursor}


def test_every_plan_is_linked_exactly_as_its_seed_entry_says(seeded) -> None:
    relations = _relations(seeded)
    expected = {plan["name"]: [_species_key(n) for n in plan.get("species_names", [])] for plan in _seed_plans()}

    assert relations == expected


def test_the_seeded_catalogue_splits_into_linked_and_unlinked_plans(seeded) -> None:
    relations = _relations(seeded)
    linked = {name for name, species in relations.items() if species}
    unlinked = {name for name, species in relations.items() if species == []}

    # Every plan carries the attribute as a list — none is absent or null.
    assert linked | unlinked == set(relations)
    # The unlinked plans are exactly those whose source names no species (the
    # cannabis programmes name the crop, not a catalogued species).
    assert unlinked == {plan["name"] for plan in _seed_plans() if not plan.get("species_names")}
    assert all("Cannabis" in name for name in unlinked)


def test_the_onboarding_match_finds_the_tomato_plan_and_no_unlinked_plan(seeded) -> None:
    service = build_favorites_service(seeded)
    unlinked = {name for name, species in _relations(seeded).items() if not species}

    rows = service.get_matching_nutrient_plans([_species_key("Solanum lycopersicum")], tenant_key="tenant-a")

    assert [row["name"] for row in rows] == ["Tomate — Plagron Terra + PK 13-14"]
    all_species = [_species_key(n) for plan in _seed_plans() for n in plan.get("species_names", [])]
    every_match = {row["name"] for row in service.get_matching_nutrient_plans(all_species, tenant_key="tenant-a")}
    assert every_match.isdisjoint(unlinked)


def test_a_second_seed_run_leaves_the_relation_unchanged(seeded) -> None:
    before = _relations(seeded)
    patch = pytest.MonkeyPatch()
    for module in LOADERS:
        patch.setattr(module, "get_db", lambda: seeded)
        patch.setattr(module, "get_fertilizer_repo", lambda: ArangoFertilizerRepository(seeded))
        patch.setattr(module, "get_nutrient_plan_repo", lambda: ArangoNutrientPlanRepository(seeded))
    try:
        for run in RUNNERS:
            run()
    finally:
        patch.undo()

    assert _relations(seeded) == before
