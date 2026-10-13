"""#2027 follow-up — a tenant's row flagged ``is_system`` is still the tenant's, and the erasure removes it.

Until this change the inventory kept every ``activities`` and ``workflow_templates``
row of the erased tenant that carried ``is_system: true`` (``keep_when``), on the
theory that such a row was a system seed the ``v0004`` backfill had stamped with
the tenant. A seed is global (``tenant_key == ""``) and the erasure only selects
rows carrying the tenant's key, so the exception reached nothing but tenant rows
with the flag — written, until #2027, by ``POST /t/{slug}/tasks/workflows`` with
``is_system: true``. Those rows, and the tenant's names and descriptions in them,
outlived the tenant's erasure (REQ-025, Art. 17).

Runs against a real ArangoDB (see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango.tenant_erasure_executor import ArangoTenantErasureExecutor
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

TEST_DATABASE = run_database_name("tenant_erasure_system_flag")
TENANT = "t-erased"
OTHER = "t-other"

pytestmark = pytest.mark.usefixtures("arango_db")


@pytest.fixture
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    from app.data_access.arango.collections import ensure_collections

    ensure_collections(database)
    for tenant in (TENANT, OTHER):
        database.collection("tenants").insert({"_key": tenant, "slug": tenant, "name": tenant})
    yield database
    system.delete_database(TEST_DATABASE)


def _rows(database, collection: str) -> None:
    """A global seed, the erased tenant's own row with and without the flag, and another tenant's flagged row."""
    rows = [
        {"_key": "seed", "tenant_key": "", "name": "Topping", "is_system": True},
        {"_key": "own-flagged", "tenant_key": TENANT, "name": "My secret routine", "is_system": True},
        {"_key": "own-plain", "tenant_key": TENANT, "name": "My routine", "is_system": False},
        {"_key": "other-flagged", "tenant_key": OTHER, "name": "Their routine", "is_system": True},
    ]
    database.collection(collection).insert_many(rows)


@pytest.mark.parametrize("collection", ["activities", "workflow_templates"])
def test_a_flagged_tenant_row_goes_with_its_tenant_and_the_global_seed_stays(database, collection):
    _rows(database, collection)

    report = ArangoTenantErasureExecutor(database).run_tenant_erasure(
        TenantErasureEngine().build_plan(TENANT), pseudonymize=lambda key: "anon_" + "0" * 16
    )

    remaining = {doc["_key"] for doc in database.collection(collection).all()}
    assert remaining == {"seed", "other-flagged"}
    assert report.unreached == []
    assert report.tenant_document_removed is True
