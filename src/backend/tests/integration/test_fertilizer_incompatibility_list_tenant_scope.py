"""A fertilizer's incompatibility list shows only partners the caller may see — bundle A security review (K1).

``get_incompatibilities`` returned every edge of a product. For a **global**
product that included the edges other tenants declared from their private
products, with the partner's ``product_name`` and the edge's ``reason``. The
partner is now filtered with the hybrid-catalogue rule: global or the caller's.
Against a real server, because the predicate is AQL.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.fertilizer_repository import ArangoFertilizerRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("fertilizer_incompatibility_list_scope")


@pytest.fixture(scope="module")
def db():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    database = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    database.create_collection(col.FERTILIZERS)
    database.create_collection(col.FERT_INCOMPATIBLE, edge=True)
    database.collection(col.FERTILIZERS).insert_many(
        [
            {"_key": "g1", "tenant_key": "", "product_name": "Global CalMag"},
            {"_key": "g2", "tenant_key": "", "product_name": "Global Base"},
            {"_key": "a1", "tenant_key": "t_a", "product_name": "A private"},
            {"_key": "b1", "tenant_key": "t_b", "product_name": "B secret product"},
        ]
    )
    edges = database.collection(col.FERT_INCOMPATIBLE)
    for other, reason in (("g2", "shared"), ("a1", "a note"), ("b1", "b secret reason")):
        edges.insert(
            {
                "_from": f"{col.FERTILIZERS}/g1",
                "_to": f"{col.FERTILIZERS}/{other}",
                "reason": reason,
                "severity": "high",
            }
        )
    yield database
    system.delete_database(TEST_DATABASE)


def test_a_global_products_list_hides_other_tenants_partners(db) -> None:
    rows = ArangoFertilizerRepository(db).get_incompatibilities("g1", tenant_key="t_a")

    assert sorted(r["fertilizer_key"] for r in rows) == ["a1", "g2"]
    assert "B secret" not in str(rows) and "b secret" not in str(rows)
