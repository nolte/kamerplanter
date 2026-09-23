"""``get_matching_nutrient_plans`` must answer the hybrid-catalogue union (#1561).

``FavoritesService.get_matching_nutrient_plans`` backs the onboarding wizard's
nutrient-plan step. It took a ``tenant_key`` and ran its AQL **without**
``bind_vars``: the only filter was ``is_template == true OR origin == "system"``,
so every row any tenant flagged as a template was served to any authenticated
caller of any tenant, with its name, description, substrate type and the
product name and brand of every fertilizer it uses. A cross-tenant read, not
merely an existence oracle.

This module measures the query against a **real** ArangoDB, because the defect
is in the AQL, not in the Python around it — a fake ``aql.execute`` that returns
a canned list would certify the call signature and nothing else. Three rows,
one per arm of the decision:

* a **foreign** tenant's template plan — must never appear,
* a **global** seed plan (``tenant_key == ""``) — must still appear, because a
  strict owner predicate that blanks the seeded catalogue is the #324
  regression this repository already shipped once,
* the caller's **own** template plan — must appear.

The fertilizer projection is measured on the foreign row on purpose: the leak
was never only the plan name.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.domain.services.favorites_service import FavoritesService
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("favorites_matching_plans")
CALLER_TENANT = "tenant-alice"
FOREIGN_TENANT = "tenant-bob"

SPECIES_KEYS = ["tomato"]


def _plan(key: str, tenant_key: str) -> dict:
    return {
        "_key": key,
        "tenant_key": tenant_key,
        "name": f"Plan {key}",
        "description": f"description of {key}",
        "substrate_type": "soil",
        "is_template": True,
    }


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

    plans = database.collection(col.NUTRIENT_PLANS)
    plans.insert(_plan("plan-foreign", FOREIGN_TENANT))
    plans.insert(_plan("plan-global", ""))
    plans.insert(_plan("plan-own", CALLER_TENANT))
    # A row that carries no ownership field at all: global by absence, the same
    # way the `== null` arm of the shared predicate reads it.
    plans.insert({"_key": "plan-null-tenant", "name": "Plan null", "is_template": True})
    # Not a template and not a system row: outside the answer for every caller.
    plans.insert({"_key": "plan-private", "tenant_key": CALLER_TENANT, "name": "Private", "is_template": False})

    # The foreign plan's fertilizer, reachable through an embedded dosage — the
    # projection that leaked product name and brand.
    database.collection(col.FERTILIZERS).insert(
        {"_key": "fert-secret", "product_name": "Bobs Secret Bloom", "brand": "BobCorp"}
    )
    database.collection(col.NUTRIENT_PLAN_PHASE_ENTRIES).insert(
        {
            "_key": "pe-foreign",
            "plan_key": "plan-foreign",
            "delivery_channels": [{"fertilizer_dosages": [{"fertilizer_key": "fert-secret"}]}],
        }
    )

    yield database

    system.delete_database(TEST_DATABASE)


@pytest.fixture
def service(db) -> FavoritesService:
    return FavoritesService(db)


def _plan_keys(rows: list[dict]) -> set[str]:
    return {row["plan_key"] for row in rows}


def test_foreign_tenants_template_plan_is_not_served(service: FavoritesService) -> None:
    rows = service.get_matching_nutrient_plans(SPECIES_KEYS, tenant_key=CALLER_TENANT)

    assert "plan-foreign" not in _plan_keys(rows)


def test_foreign_tenants_fertilizer_list_is_not_served(service: FavoritesService) -> None:
    rows = service.get_matching_nutrient_plans(SPECIES_KEYS, tenant_key=CALLER_TENANT)

    brands = {f.get("brand") for row in rows for f in row["fertilizers"]}
    assert "BobCorp" not in brands


def test_global_seed_plan_is_still_served(service: FavoritesService) -> None:
    # #324 counter-example: the strict owner predicate that hides the seeded
    # catalogue trades a leak for an empty onboarding step.
    rows = service.get_matching_nutrient_plans(SPECIES_KEYS, tenant_key=CALLER_TENANT)

    assert "plan-global" in _plan_keys(rows)
    assert "plan-null-tenant" in _plan_keys(rows)


def test_own_template_plan_is_served(service: FavoritesService) -> None:
    rows = service.get_matching_nutrient_plans(SPECIES_KEYS, tenant_key=CALLER_TENANT)

    assert "plan-own" in _plan_keys(rows)


def test_non_template_row_is_served_to_nobody(service: FavoritesService) -> None:
    rows = service.get_matching_nutrient_plans(SPECIES_KEYS, tenant_key=CALLER_TENANT)

    assert "plan-private" not in _plan_keys(rows)


def test_empty_species_selection_returns_nothing(service: FavoritesService) -> None:
    assert service.get_matching_nutrient_plans([], tenant_key=CALLER_TENANT) == []
