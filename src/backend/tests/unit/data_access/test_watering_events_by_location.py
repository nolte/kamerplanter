"""#2952: a location's watering events are the events of the plants standing in its slots now - list and stats alike.

Records the statements the two readers send. The behaviour on a real server (a moved plant, a plant moved before
#2948, an event watering two plants of the bed, the page window) is held by
``tests/integration/test_moved_plant_slot_readers.py::TestWateringEventsByLocation``.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.data_access.arango.watering_repository import _EVENTS_AT_LOCATION, ArangoWateringRepository


class _RecordingAql:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        self.calls.append((query, bind_vars or {}))
        return iter([])


class _Db:
    def __init__(self) -> None:
        self.aql = _RecordingAql()

    def collection(self, name: str) -> Any:
        return None


def _repo() -> tuple[ArangoWateringRepository, _RecordingAql]:
    db = _Db()
    return ArangoWateringRepository(db), db.aql  # type: ignore[arg-type]


def test_the_event_set_selects_the_plants_by_their_own_slot_key() -> None:
    assert "plant.slot_key IN slot_keys" in _EVENTS_AT_LOCATION
    assert "placed_in" not in _EVENTS_AT_LOCATION
    # one row per event, however many plants of the bed it watered
    assert "COLLECT event_id = water_edge._from" in _EVENTS_AT_LOCATION


def test_list_and_stats_read_the_same_event_set_inside_the_tenant() -> None:
    repo, aql = _repo()

    assert repo.get_by_location("bed", 10, 5, tenant_key="t_a") == []
    assert repo.get_stats_by_location("bed", tenant_key="t_a") == {
        "total_events": 0,
        "total_volume": 0.0,
        "by_method": [],
    }

    (list_query, list_vars), (stats_query, stats_vars) = aql.calls
    assert list_query.startswith(_EVENTS_AT_LOCATION)
    assert stats_query.startswith(_EVENTS_AT_LOCATION)
    shared = {
        "@has_slot": col.HAS_SLOT,
        "@plants": col.PLANT_INSTANCES,
        "@watered_plant": col.WATERED_PLANT,
        "location_id": f"{col.LOCATIONS}/bed",
        "tenant_key": "t_a",
    }
    assert list_vars == {**shared, "offset": 10, "limit": 5}
    assert stats_vars == shared


def test_the_page_window_follows_the_deduplicated_set() -> None:
    repo, aql = _repo()

    repo.get_by_location("bed", tenant_key="t_a")

    query = aql.calls[0][0]
    assert query.index("LIMIT @offset, @limit") > query.index("FOR doc IN events")
