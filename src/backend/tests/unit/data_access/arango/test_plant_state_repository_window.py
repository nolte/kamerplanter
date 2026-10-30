"""#2489 S-2: the plant-state read bounds its window and its bed list (defence in depth below the API).

* ``limit`` above the API's pagination ceiling (200) is refused, not clamped — a clamped window comes back short
  and a pager reads a short page as the end.
* More than :data:`BED_KEYS_PER_STATEMENT` bed keys are bound in chunks; the window stays the one a single
  statement would give (ordered by plant key across chunks). Against a real store:
  ``tests/integration/test_plant_state_repository.py::TestManyBeds``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from app.data_access.arango.plant_state_repository import (
    BED_KEYS_PER_STATEMENT,
    MAX_STATE_WINDOW,
    ArangoPlantStateRepository,
)

NOW = datetime(2026, 6, 10, 12, 0, tzinfo=UTC)


def _row(plant_key: str, bed: str) -> dict[str, Any]:
    return {
        "plant_key": plant_key,
        "location_key": bed,
        "instance_id": plant_key.upper(),
        "species_key": "sp",
        "cultivar_key": None,
        "planted_on": "2026-04-01",
        "slot_key": None,
        "slot_id": None,
        "species_name": None,
        "scientific_name": None,
        "cultivar_name": None,
        "phase_key": None,
        "phase_name": None,
        "phase_started_at": None,
        "phase_typical_days": None,
        "phase_allows_harvest": False,
        "phase_is_terminal": False,
        "cover_photo_ref": None,
        "run_key": None,
    }


class _PlantsAql:
    """Answers the plant statement from ``plants`` (bed → plant keys) like the server would — filtered by the bound
    beds, sorted by key, windowed — and every other statement with nothing."""

    def __init__(self, plants: dict[str, list[str]]) -> None:
        self.plants = plants
        self.plant_statements: list[dict[str, Any]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind = bind_vars or {}
        if "@plants" not in bind:
            return iter([])
        self.plant_statements.append(bind)
        rows = sorted(
            (_row(key, bed) for bed in bind["beds"] for key in self.plants.get(bed, [])),
            key=lambda row: row["plant_key"],
        )
        return iter(rows[bind["offset"] : bind["offset"] + bind["limit"]])


class _Db:
    def __init__(self, plants: dict[str, list[str]]) -> None:
        self.aql = _PlantsAql(plants)


@pytest.mark.parametrize(("offset", "limit"), [(0, MAX_STATE_WINDOW + 1), (0, 0), (-1, 50)])
def test_a_window_outside_the_api_bounds_is_refused_before_any_statement(offset, limit) -> None:
    db = _Db({})
    repo = ArangoPlantStateRepository(db)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="limit"):
        repo.list_plants_in_beds(["b1"], tenant_key="t", now=NOW, offset=offset, limit=limit)
    with pytest.raises(ValueError, match="limit"):
        repo.list_bed_plants("b1", tenant_key="t", now=NOW, offset=offset, limit=limit)
    assert db.aql.plant_statements == []


def test_the_api_ceiling_itself_is_accepted() -> None:
    db = _Db({"b1": ["p1"]})

    rows = ArangoPlantStateRepository(db).list_plants_in_beds(  # type: ignore[arg-type]
        ["b1"], tenant_key="t", now=NOW, offset=0, limit=MAX_STATE_WINDOW
    )

    assert [row.plant_key for row in rows] == ["p1"]
    assert len(db.aql.plant_statements) == 1


def test_up_to_the_chunk_size_the_beds_are_one_statement() -> None:
    beds = [f"b{index:04d}" for index in range(BED_KEYS_PER_STATEMENT)]
    db = _Db({"b0000": ["p1"]})

    ArangoPlantStateRepository(db).list_plants_in_beds(beds, tenant_key="t", now=NOW, offset=0, limit=50)  # type: ignore[arg-type]

    (statement,) = db.aql.plant_statements
    assert len(statement["beds"]) == BED_KEYS_PER_STATEMENT
    assert (statement["offset"], statement["limit"]) == (0, 50)


def test_beyond_the_chunk_size_the_beds_are_chunked_and_the_window_is_ordered_across_chunks() -> None:
    beds = [f"b{index:04d}" for index in range(1200)]
    plants = {"b1100": ["p1", "p4"], "b0000": ["p2"], "b0600": ["p3"], "b0001": ["p5"]}
    db = _Db(plants)
    repo = ArangoPlantStateRepository(db)  # type: ignore[arg-type]

    pages = [
        [row.plant_key for row in repo.list_plants_in_beds(beds, tenant_key="t", now=NOW, offset=o, limit=2)]
        for o in (0, 2, 4)
    ]

    assert pages == [["p1", "p2"], ["p3", "p4"], ["p5"]]
    first_page = db.aql.plant_statements[:3]
    assert [len(statement["beds"]) for statement in first_page] == [500, 500, 200]
    assert all(len(statement["beds"]) <= BED_KEYS_PER_STATEMENT for statement in db.aql.plant_statements)
    # each chunk reads the head of its plants up to the end of the window, never an unbounded list
    assert {(statement["offset"], statement["limit"]) for statement in first_page} == {(0, 2)}
    assert {(statement["offset"], statement["limit"]) for statement in db.aql.plant_statements[3:6]} == {(0, 4)}
