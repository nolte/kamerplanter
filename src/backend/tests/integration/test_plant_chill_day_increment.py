"""#1970 — the vernalization chill-day increment is one server-side AQL statement.

``ArangoPlantInstanceRepository.increment_chill_days`` replaces a read-modify-write
of a whole plant snapshot. The contract is the AQL one (increment commutes, a removed
plant is left alone, other fields untouched), so it is measured here and not against a double.
"""

from __future__ import annotations

import pytest
from arango import ArangoClient

from app.data_access.arango import collections as col
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from tests.support.arango_integration import ARANGO_PASSWORD, ARANGO_URL, ARANGO_USERNAME, run_database_name

pytestmark = [
    pytest.mark.usefixtures("arango_db"),
    pytest.mark.allow_db_connection("#1970 the increment is an AQL contract; no double may answer it"),
]

_DB_NAME = run_database_name("plant_chill_day_increment")


@pytest.fixture
def repo():
    client = ArangoClient(hosts=ARANGO_URL)
    system = client.db("_system", username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    if system.has_database(_DB_NAME):
        system.delete_database(_DB_NAME)
    system.create_database(_DB_NAME)
    db = client.db(_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    db.create_collection(col.PLANT_INSTANCES)
    plants = db.collection(col.PLANT_INSTANCES)
    plants.insert({"_key": "live", "removed_on": None, "chill_days_accumulated": 4, "current_phase_key": "veg"})
    plants.insert({"_key": "legacy", "removed_on": None, "current_phase_key": "veg"})
    plants.insert({"_key": "gone", "removed_on": "2026-10-01", "chill_days_accumulated": 4})
    try:
        yield ArangoPlantInstanceRepository(db)
    finally:
        system.delete_database(_DB_NAME)


def test_the_counter_is_incremented_and_other_fields_are_untouched(repo: ArangoPlantInstanceRepository) -> None:
    assert repo.increment_chill_days("live") == 5
    assert repo.increment_chill_days("live") == 6
    doc = repo.collection.get("live")
    assert doc["chill_days_accumulated"] == 6
    assert doc["current_phase_key"] == "veg"


def test_a_document_without_the_counter_starts_from_zero(repo: ArangoPlantInstanceRepository) -> None:
    assert repo.increment_chill_days("legacy") == 1


def test_a_removed_or_missing_plant_is_left_alone(repo: ArangoPlantInstanceRepository) -> None:
    assert repo.increment_chill_days("gone") is None
    assert repo.increment_chill_days("nope") is None
    assert repo.collection.get("gone")["chill_days_accumulated"] == 4
