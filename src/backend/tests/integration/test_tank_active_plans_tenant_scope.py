"""``get_active_nutrient_plans`` reads only the tank's own tenant's runs — #1864 sweep (L3).

A tank's ``location_key`` used to be stored unverified. The read then matched
every active run at that location regardless of tenant, so a tank pointed at
another tenant's location returned that tenant's runs, plans and fertilizers.
The write is now verified (``TankService._require_owned_location``); this pins
the read's own tenant predicate against a real server, for rows written before.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.tank_repository import ArangoTankRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("tank_active_plans_tenant_scope")
_COLLECTIONS = (
    col.TANKS,
    col.PLANTING_RUNS,
    col.NUTRIENT_PLANS,
    col.PLANT_INSTANCES,
    col.FERTILIZERS,
    col.PLANTING_RUN_ENTRIES,
    col.NUTRIENT_PLAN_PHASE_ENTRIES,
)


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in _COLLECTIONS:
        database.create_collection(name)
    database.collection(col.NUTRIENT_PLANS).insert_many(
        [{"_key": "plan_a", "name": "Plan A"}, {"_key": "plan_b", "name": "Plan B"}]
    )
    database.collection(col.PLANTING_RUNS).insert_many(
        [
            {
                "_key": "run_a",
                "tenant_key": "t_a",
                "name": "A run",
                "status": "active",
                "location_key": "loc_b",
                "nutrient_plan_key": "plan_a",
            },
            {
                "_key": "run_b",
                "tenant_key": "t_b",
                "name": "B secret run",
                "status": "active",
                "location_key": "loc_b",
                "nutrient_plan_key": "plan_b",
            },
        ]
    )
    # A tank of tenant A written before the location was verified: it names B's location.
    database.collection(col.TANKS).insert({"_key": "tank_a", "tenant_key": "t_a", "location_key": "loc_b"})
    yield database
    system.delete_database(TEST_DATABASE)


def test_only_the_tanks_tenants_runs_are_returned(db) -> None:
    plans = ArangoTankRepository(db).get_active_nutrient_plans("tank_a")

    assert [p["run_key"] for p in plans] == ["run_a"]
    assert "B secret run" not in str(plans)
