"""MT-032 (#2128): ``get_active_phase_histories`` — one query for a page, the per-plant pick per plant.

The auto-transition scan reads the open phase-history entry of a whole page of plants
at once. Which entry counts as open must not change with the batching: the per-plant
path (``PhaseService.get_current_phase``) sorts a plant's history by ``entered_at`` and
takes the first entry without ``exited_at``. The query keeps the open entries; the
repository keeps the earliest per plant. The AQL itself is measured on the server in
``tests/integration/test_active_phase_histories_query.py``.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository


class _AnsweringAql:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.calls: list[dict[str, Any]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.calls.append({"query": query, "bind_vars": bind_vars or {}})
        return iter([dict(row, history=dict(row["history"])) for row in self.rows])


class _Db:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.aql = _AnsweringAql(rows)

    def collection(self, _name: str) -> object:
        return object()


def _open(plant: str, key: str, entered: str, phase: str = "veg") -> dict[str, Any]:
    return {
        "plant_id": f"{col.PLANT_INSTANCES}/{plant}",
        "history": {"_key": key, "plant_instance_key": plant, "phase_key": phase, "entered_at": entered},
    }


def test_one_query_for_the_page_bound_to_the_edge_collection_and_the_plant_ids() -> None:
    db = _Db([])
    repo = ArangoLifecycleRepository(db)  # type: ignore[arg-type]

    repo.get_active_phase_histories(["p2", "p1", "p1", ""])

    assert len(db.aql.calls) == 1
    call = db.aql.calls[0]
    assert call["bind_vars"] == {
        "@edge": col.PHASE_HISTORY_EDGE,
        "ids": [f"{col.PLANT_INSTANCES}/p1", f"{col.PLANT_INSTANCES}/p2"],
    }
    assert "edge._from IN @ids" in call["query"]
    assert "history.exited_at == null" in call["query"]


def test_no_plant_no_query() -> None:
    db = _Db([])

    assert ArangoLifecycleRepository(db).get_active_phase_histories([]) == {}  # type: ignore[arg-type]
    assert db.aql.calls == []


def test_the_earliest_open_entry_wins_per_plant() -> None:
    db = _Db(
        [
            _open("p1", "h-late", "2026-05-01T00:00:00+00:00", phase="flower"),
            _open("p1", "h-early", "2026-04-01T00:00:00+00:00", phase="veg"),
            _open("p2", "h-only", "2026-03-01T00:00:00+00:00", phase="seedling"),
        ]
    )

    active = ArangoLifecycleRepository(db).get_active_phase_histories(["p1", "p2", "p3"])  # type: ignore[arg-type]

    assert {key: h.key for key, h in active.items()} == {"p1": "h-early", "p2": "h-only"}
    assert active["p1"].phase_key == "veg"
