"""``get_runs_at_site`` returns one tenant's runs — #1870, against a real server.

The sowing calendar handed a caller-chosen site key to this query, which had no
tenant predicate; it now takes ``tenant_key`` keyword-only and filters on it.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.planting_run_repository import ArangoPlantingRunRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("runs_at_site_tenant_scope")


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    for name in (col.PLANTING_RUNS, col.LOCATIONS):
        database.create_collection(name)
    database.collection(col.LOCATIONS).insert({"_key": "loc_1", "name": "Beet", "site_key": "site_1"})
    database.collection(col.PLANTING_RUNS).insert_many(
        [
            {
                "_key": "run_a",
                "tenant_key": "t_a",
                "name": "A",
                "run_type": "monoculture",
                "status": "active",
                "location_key": "loc_1",
            },
            {
                "_key": "run_b",
                "tenant_key": "t_b",
                "name": "B",
                "run_type": "monoculture",
                "status": "active",
                "location_key": "loc_1",
            },
        ]
    )
    yield database
    system.delete_database(TEST_DATABASE)


def test_only_the_named_tenants_runs_come_back(db) -> None:
    runs = ArangoPlantingRunRepository(db).get_runs_at_site("site_1", tenant_key="t_a")

    assert [r.key for r in runs] == ["run_a"]
