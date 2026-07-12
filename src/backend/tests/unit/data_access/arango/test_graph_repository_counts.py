"""Repository-level contract for the companion-planting counts aggregate (#549).

``ArangoGraphRepository.get_companion_counts`` feeds the per-species
compatible/incompatible badges in the "Art auswaehlen" dropdown. It MUST:

* run a **single** batch AQL over both edge collections — never a per-species
  query (no N+1);
* bind both edge collections via ``@@…`` (never interpolate — injection guard);
* return, per species ``_key``, the outbound edge counts of ``COMPATIBLE_WITH``
  and ``INCOMPATIBLE_WITH`` respectively — each bidirectional relationship
  counted once from the species' own outbound perspective;
* default the missing category to ``0`` (a species present only in the
  incompatible aggregate reports ``compatible: 0``).

Uses a capturing fake db (no live ArangoDB), matching
``test_dashboard_counts_repo.py``.
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
        raise AssertionError("companion counts must run through a single batch AQL")


# The single aggregate document the batch query returns: tomato has two
# compatible companions and one incompatible; basil has one compatible and none
# incompatible; nettle has only an incompatible edge (0 compatible).
_AGGREGATE = {
    "compatible": [
        {"species_key": "tomato", "count": 2},
        {"species_key": "basil", "count": 1},
    ],
    "incompatible": [
        {"species_key": "tomato", "count": 1},
        {"species_key": "nettle", "count": 1},
    ],
}


def _repo(result: list[Any]) -> tuple[ArangoGraphRepository, _CapturingDb]:
    db = _CapturingDb(result)
    return ArangoGraphRepository(db), db  # type: ignore[arg-type]


def test_counts_map_both_categories_per_species() -> None:
    repo, _db = _repo([_AGGREGATE])

    counts = repo.get_companion_counts()

    assert counts["tomato"] == {"compatible": 2, "incompatible": 1}
    assert counts["basil"] == {"compatible": 1, "incompatible": 0}
    # nettle appears only in the incompatible aggregate → compatible defaults to 0.
    assert counts["nettle"] == {"compatible": 0, "incompatible": 1}


def test_counts_run_single_batch_query_no_n_plus_1() -> None:
    repo, db = _repo([_AGGREGATE])

    repo.get_companion_counts()

    # Exactly one AQL round trip regardless of how many species have edges.
    assert db.aql.execute_calls == 1


def test_counts_bind_edge_collections_and_never_interpolate() -> None:
    repo, db = _repo([_AGGREGATE])

    repo.get_companion_counts()

    query = db.aql.query or ""
    assert "@@compatible_col" in query
    assert "@@incompatible_col" in query
    assert db.aql.bind_vars is not None
    assert db.aql.bind_vars["@compatible_col"] == "compatible_with"
    assert db.aql.bind_vars["@incompatible_col"] == "incompatible_with"
    # Collection names are bound, never interpolated into the query string.
    assert "compatible_with" not in query
    assert "COLLECT" in query


def test_counts_empty_when_no_edges() -> None:
    repo, _db = _repo([{"compatible": [], "incompatible": []}])

    assert repo.get_companion_counts() == {}
