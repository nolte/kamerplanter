"""Repository-level contract for the crop-rotation successor counts aggregate (#550).

``ArangoGraphRepository.get_rotation_successor_counts`` feeds the per-family
successor-count chips in the "Von Familie" dropdown. It MUST:

* run a **single** batch AQL over the ``ROTATION_AFTER`` edge collection — never a
  per-family query (no N+1);
* bind the edge collection via ``@@…`` (never interpolate — injection guard);
* return, per family ``_key``, the outbound edge count of ``ROTATION_AFTER``;
* return an empty map when no rotation edges exist.

Uses a capturing fake db (no live ArangoDB), matching
``test_graph_repository_counts.py`` / ``test_dashboard_counts_repo.py``.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango.graph_repository import ArangoGraphRepository


class _CapturingAql:
    def __init__(self, result: list[Any]) -> None:
        self.query: str | None = None
        self.bind_vars: dict[str, Any] | None = None
        self.execute_calls = 0
        self._result = result

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.query = query
        self.bind_vars = bind_vars or {}
        self.execute_calls += 1
        return iter(self._result)


class _CapturingDb:
    def __init__(self, result: list[Any]) -> None:
        self.aql = _CapturingAql(result)

    def collection(self, _name: str):  # pragma: no cover - must not be reached
        raise AssertionError("rotation counts must run through a single batch AQL")


# The rows the batch COLLECT query returns: Solanaceae has three curated
# rotation successors, Fabaceae has one, and Brassicaceae has two.
_ROWS = [
    {"family_key": "solanaceae", "count": 3},
    {"family_key": "fabaceae", "count": 1},
    {"family_key": "brassicaceae", "count": 2},
]


def _repo(result: list[Any]) -> tuple[ArangoGraphRepository, _CapturingDb]:
    db = _CapturingDb(result)
    return ArangoGraphRepository(db), db  # type: ignore[arg-type]


def test_counts_map_per_family() -> None:
    repo, _db = _repo(_ROWS)

    counts = repo.get_rotation_successor_counts()

    assert counts == {"solanaceae": 3, "fabaceae": 1, "brassicaceae": 2}


def test_counts_run_single_batch_query_no_n_plus_1() -> None:
    repo, db = _repo(_ROWS)

    repo.get_rotation_successor_counts()

    # Exactly one AQL round trip regardless of how many families have edges.
    assert db.aql.execute_calls == 1


def test_counts_bind_edge_collection_and_never_interpolate() -> None:
    repo, db = _repo(_ROWS)

    repo.get_rotation_successor_counts()

    query = db.aql.query or ""
    assert "@@rotation_col" in query
    assert db.aql.bind_vars is not None
    assert db.aql.bind_vars["@rotation_col"] == "rotation_after"
    # Collection name is bound, never interpolated into the query string.
    assert "rotation_after" not in query
    assert "COLLECT" in query


def test_counts_empty_when_no_edges() -> None:
    repo, _db = _repo([])

    assert repo.get_rotation_successor_counts() == {}
