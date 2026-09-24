"""The onboarding plan match filters on the species↔plan relation (#1618).

Before #1618 ``FavoritesService.get_matching_nutrient_plans`` returned every
template plan visible to the tenant: the ``species_keys`` the wizard sends were
accepted and ignored, because the data model carried no relation between a
species and a nutrient plan. The operator decision (2026-09-23) is a real
relation — ``NutrientPlan.species_keys`` — and a match on it, with one rule
stated up front: **a plan without the relation matches no species**. An empty
relation that silently matched everything would be the old behaviour under a
new name.

Measured against a real ArangoDB because the rule lives in the AQL. Every
assertion is taken through the production read path — the service over the
real repository — so a test cannot reach the rule by a route production does
not take. The rows, one per arm:

* ``plan-tomato`` (global) — linked to tomato,
* ``plan-basil`` (global) — linked to basil,
* ``plan-both`` (global) — linked to tomato *and* basil,
* ``plan-unlinked`` (global) — template with an **empty** relation,
* ``plan-legacy`` (global) — template that predates the field (attribute absent),
* ``plan-foreign-tomato`` — another tenant's tomato plan,
* ``plan-own-tomato`` — the caller's own tomato plan,
* ``plan-private-tomato`` — the caller's tomato plan that is not a template.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.domain.services.favorites_service import FavoritesService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name
from tests.support.onboarding_wiring import build_favorites_service

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("the species filter is AQL; the store is the SUT"),
]

TEST_DATABASE = run_database_name("plan_species_matching")
CALLER_TENANT = "tenant-alice"
FOREIGN_TENANT = "tenant-bob"

TOMATO = "solanum-lycopersicum"
BASIL = "ocimum-basilicum"
CARROT = "daucus-carota"


def _plan(key: str, tenant_key: str, species_keys: list[str] | None, *, is_template: bool = True) -> dict:
    doc: dict = {
        "_key": key,
        "tenant_key": tenant_key,
        "name": f"Plan {key}",
        "description": f"description of {key}",
        "is_template": is_template,
    }
    if species_keys is not None:
        doc["species_keys"] = species_keys
    return doc


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)

    for name in (col.NUTRIENT_PLANS, col.NUTRIENT_PLAN_PHASE_ENTRIES, col.FERTILIZERS):
        database.create_collection(name)
    database.create_collection(col.PLAN_USES_FERTILIZER, edge=True)

    database.collection(col.NUTRIENT_PLANS).insert_many(
        [
            _plan("plan-tomato", "", [TOMATO]),
            _plan("plan-basil", "", [BASIL]),
            _plan("plan-both", "", [BASIL, TOMATO]),
            _plan("plan-unlinked", "", []),
            _plan("plan-legacy", "", None),
            _plan("plan-foreign-tomato", FOREIGN_TENANT, [TOMATO]),
            _plan("plan-own-tomato", CALLER_TENANT, [TOMATO]),
            _plan("plan-private-tomato", CALLER_TENANT, [TOMATO], is_template=False),
        ]
    )

    yield database

    system.delete_database(TEST_DATABASE)


@pytest.fixture
def service(db) -> FavoritesService:
    return build_favorites_service(db)


def _keys(rows: list[dict]) -> set[str]:
    return {row["plan_key"] for row in rows}


def test_a_species_request_returns_only_plans_linked_to_that_species(service: FavoritesService) -> None:
    rows = service.get_matching_nutrient_plans([TOMATO], tenant_key=CALLER_TENANT)

    assert _keys(rows) == {"plan-tomato", "plan-both", "plan-own-tomato"}


def test_a_plan_with_an_empty_relation_is_never_returned(service: FavoritesService) -> None:
    # The operator's rule: no relation means no match — for every species,
    # including one no plan is linked to.
    for species in ([TOMATO], [BASIL], [CARROT], [TOMATO, BASIL, CARROT]):
        keys = _keys(service.get_matching_nutrient_plans(species, tenant_key=CALLER_TENANT))
        assert "plan-unlinked" not in keys, species
        assert "plan-legacy" not in keys, species


def test_a_species_no_plan_is_linked_to_matches_nothing(service: FavoritesService) -> None:
    assert service.get_matching_nutrient_plans([CARROT], tenant_key=CALLER_TENANT) == []


def test_several_species_match_the_union_and_report_which_species_matched(service: FavoritesService) -> None:
    rows = service.get_matching_nutrient_plans([TOMATO, BASIL], tenant_key=CALLER_TENANT)

    matched = {row["plan_key"]: sorted(row["matched_species"]) for row in rows}
    assert matched == {
        "plan-both": sorted([BASIL, TOMATO]),
        "plan-tomato": [TOMATO],
        "plan-basil": [BASIL],
        "plan-own-tomato": [TOMATO],
    }
    # REQ-020 §3: sorted by relevance — the plan that fits both selected species first.
    assert rows[0]["plan_key"] == "plan-both"


def test_another_tenants_linked_plan_is_not_served(service: FavoritesService) -> None:
    rows = service.get_matching_nutrient_plans([TOMATO], tenant_key=CALLER_TENANT)

    assert "plan-foreign-tomato" not in _keys(rows)


def test_the_other_tenant_sees_its_own_plan_and_not_the_callers(service: FavoritesService) -> None:
    keys = _keys(service.get_matching_nutrient_plans([TOMATO], tenant_key=FOREIGN_TENANT))

    assert "plan-foreign-tomato" in keys
    assert "plan-own-tomato" not in keys


def test_the_anonymous_context_sees_only_global_linked_plans(service: FavoritesService) -> None:
    keys = _keys(service.get_matching_nutrient_plans([TOMATO], tenant_key=""))

    assert keys == {"plan-tomato", "plan-both"}


def test_a_linked_plan_that_is_not_a_template_is_not_served(service: FavoritesService) -> None:
    rows = service.get_matching_nutrient_plans([TOMATO], tenant_key=CALLER_TENANT)

    assert "plan-private-tomato" not in _keys(rows)


def test_the_repository_answers_an_empty_selection_with_nothing(db) -> None:
    repo = ArangoNutrientPlanRepository(db)

    assert repo.list_template_plan_summaries(tenant_key=CALLER_TENANT, species_keys=[]) == []
