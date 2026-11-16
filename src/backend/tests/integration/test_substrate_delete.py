"""#2560 (D2) — ``delete_substrate`` refuses with 422 while a plant or a run uses it, and cuts ``uses_type``.

Measured against ArangoDB: the refusal and the removal read one snapshot inside one stream transaction, and the
derived edge set (``edges_touching(SUBSTRATES)``) is what the old bare ``super().delete`` left behind.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.common.exceptions import ValidationError
from app.data_access.arango import collections as col
from app.data_access.arango.graph_edges import edges_touching
from app.data_access.arango.substrate_repository import ArangoSubstrateRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = pytest.mark.usefixtures("arango_db")

TEST_DATABASE = run_database_name("substrate_delete")
SUBSTRATE = "coco"
_DOCUMENTS = (col.SUBSTRATES, col.SUBSTRATE_BATCHES, col.PLANT_INSTANCES, col.PLANTING_RUNS)
_EDGES = tuple(dict.fromkeys((col.RUN_USES_SUBSTRATE, *(edge for edge, _ in edges_touching(col.SUBSTRATES)))))


@pytest.fixture(scope="module")
def database():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(TEST_DATABASE):
        system.delete_database(TEST_DATABASE)
    system.create_database(TEST_DATABASE)
    db = client.db(TEST_DATABASE, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    col.ensure_collections(db)
    yield db
    system.delete_database(TEST_DATABASE)
    client.close()


@pytest.fixture
def db(database):
    for name in (*_DOCUMENTS, *_EDGES):
        database.collection(name).truncate()
    database.collection(col.SUBSTRATES).insert({"_key": SUBSTRATE, "tenant_key": "ten_a", "name": "Coco"})
    database.collection(col.SUBSTRATE_BATCHES).insert(
        {"_key": "batch1", "tenant_key": "ten_a", "batch_id": "B1", "substrate_key": SUBSTRATE}
    )
    database.collection(col.USES_TYPE).insert(
        {"_from": f"{col.SUBSTRATE_BATCHES}/batch1", "_to": f"{col.SUBSTRATES}/{SUBSTRATE}"}
    )
    return database


@pytest.fixture
def repo(db) -> ArangoSubstrateRepository:
    return ArangoSubstrateRepository(db)


def test_an_unused_substrate_goes_with_every_edge_on_it(db, repo) -> None:
    assert edges_touching(col.SUBSTRATES), "the graph lets no edge end at a substrate — the test proves nothing"

    assert repo.delete_substrate(SUBSTRATE) is True

    assert db.collection(col.SUBSTRATES).get(SUBSTRATE) is None
    for edge, end in edges_touching(col.SUBSTRATES):
        assert list(db.collection(edge).find({end: f"{col.SUBSTRATES}/{SUBSTRATE}"})) == [], edge


def test_a_plant_on_the_substrate_refuses_the_delete(db, repo) -> None:
    db.collection(col.PLANT_INSTANCES).insert({"_key": "p1", "tenant_key": "ten_a", "substrate_key": SUBSTRATE})

    with pytest.raises(ValidationError) as refused:
        repo.delete_substrate(SUBSTRATE)

    assert refused.value.status_code == 422
    assert refused.value.details[0]["code"] == "SUBSTRATE_IN_USE"
    assert db.collection(col.SUBSTRATES).get(SUBSTRATE) is not None
    assert db.collection(col.USES_TYPE).count() == 1


@pytest.mark.parametrize("by", ["field", "edge"])
def test_a_run_on_a_batch_of_the_substrate_refuses_the_delete(db, repo, by: str) -> None:
    run = {"_key": "r1", "tenant_key": "ten_a"}
    if by == "field":
        run["substrate_batch_key"] = "batch1"
    db.collection(col.PLANTING_RUNS).insert(run)
    if by == "edge":
        db.collection(col.RUN_USES_SUBSTRATE).insert(
            {"_from": f"{col.PLANTING_RUNS}/r1", "_to": f"{col.SUBSTRATE_BATCHES}/batch1"}
        )

    with pytest.raises(ValidationError):
        repo.delete_substrate(SUBSTRATE)

    assert db.collection(col.SUBSTRATES).get(SUBSTRATE) is not None


def test_a_plant_on_another_substrate_does_not_block(db, repo) -> None:
    db.collection(col.PLANT_INSTANCES).insert({"_key": "p1", "tenant_key": "ten_a", "substrate_key": "peat"})

    assert repo.delete_substrate(SUBSTRATE) is True


def test_a_missing_substrate_writes_nothing(db, repo) -> None:
    assert repo.delete_substrate("no-such") is False

    assert db.collection(col.USES_TYPE).count() == 1
