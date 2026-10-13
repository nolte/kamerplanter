"""Integration test for MT-032 (#2128) — the batched open-history read, measured on the server.

``ArangoLifecycleRepository.get_active_phase_histories`` replaces one graph traversal
per plant (``get_phase_history``) in the auto-transition scan. It must pick, for every
plant, the entry the per-plant path picks: the earliest-entered one without
``exited_at`` — a missing ``exited_at`` field included, a closed entry never, another
plant's entry never. This file holds the batched answer to the per-plant one on the
same documents.

Run with: pytest tests/integration/test_active_phase_histories_query.py -v
(requires an ArangoDB; see ``tests/integration/conftest.py``).
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#2128 measures the batched phase-history read against the per-plant one"),
]

_DB_NAME = run_database_name("active_phase_histories")

#: (plant, history key, entered_at, exited_at or the string "missing" for an absent field)
HISTORIES = [
    ("p-open", "h1", "2026-03-01T00:00:00+00:00", "2026-04-01T00:00:00+00:00"),
    ("p-open", "h2", "2026-04-01T00:00:00+00:00", None),
    ("p-two-open", "h3", "2026-05-01T00:00:00+00:00", None),
    ("p-two-open", "h4", "2026-04-15T00:00:00+00:00", None),
    ("p-closed", "h5", "2026-03-01T00:00:00+00:00", "2026-03-20T00:00:00+00:00"),
    ("p-nofield", "h6", "2026-06-01T00:00:00+00:00", "missing"),
    ("p-other", "h7", "2026-06-01T00:00:00+00:00", None),
]

PLANTS = ["p-open", "p-two-open", "p-closed", "p-nofield", "p-none"]


@pytest.fixture(scope="module")
def db():
    from app.config.settings import Settings
    from app.data_access.arango import collections as col
    from app.data_access.arango.collections import ensure_collections
    from app.data_access.arango.connection import ArangoConnection

    conn = ArangoConnection(Settings(arangodb_database=_DB_NAME))
    database = conn.connect()
    ensure_collections(database)
    histories = []
    edges = []
    for plant, key, entered, exited in HISTORIES:
        doc = {"_key": key, "plant_instance_key": plant, "phase_key": f"phase-{key}", "entered_at": entered}
        if exited != "missing":
            doc["exited_at"] = exited
        histories.append(doc)
        edges.append({"_from": f"{col.PLANT_INSTANCES}/{plant}", "_to": f"{col.PHASE_HISTORIES}/{key}"})
    database.collection(col.PHASE_HISTORIES).insert_many(histories, overwrite=True)
    database.collection(col.PHASE_HISTORY_EDGE).insert_many(edges)
    yield database
    conn.close()
    system = ArangoClient(hosts=ARANGO_URL).db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)


def _repo(db):  # noqa: ANN001, ANN202
    from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository

    return ArangoLifecycleRepository(db)


def test_the_batched_read_picks_the_entry_the_per_plant_read_picks(db) -> None:
    repo = _repo(db)

    batched = repo.get_active_phase_histories(PLANTS)

    per_plant = {}
    for plant in PLANTS:
        active = next((h for h in repo.get_phase_history(plant) if h.exited_at is None), None)
        if active is not None:
            per_plant[plant] = active.key
    assert {plant: h.key for plant, h in batched.items()} == per_plant
    assert per_plant == {"p-open": "h2", "p-two-open": "h4", "p-nofield": "h6"}


def test_a_plant_outside_the_page_is_not_read(db) -> None:
    assert "p-other" not in _repo(db).get_active_phase_histories(PLANTS)
