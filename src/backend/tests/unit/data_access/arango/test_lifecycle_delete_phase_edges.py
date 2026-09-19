"""#1573 review SCR-001, second instance — ``delete_phase`` and the ``next_phase`` chain.

``next_phase`` is written ``from_phase → to_phase`` by
``ArangoLifecycleRepository.create_transition_rule``. ``delete_phase`` detached only
the **outbound** half, so deleting a phase in the middle of a chain left the
predecessor's ``prev → deleted phase`` edge pointing at a document that no longer
exists — the #1535 defect in a different repository, found by the R5 rule of
``tests/unit/guards/test_arango_call_surface_scoping.py`` rather than by reading.

The assertion is on the clause and the bound vertex, i.e. the same expression the
rule is about; "one ``next_phase`` call was issued" was true of the broken code too.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.data_access.arango.lifecycle_repository import ArangoLifecycleRepository


class _CapturingAql:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.calls.append({"query": query, "bind_vars": bind_vars or {}})
        return iter([])


class _FakeCollection:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    def delete(self, key: str) -> None:
        self.deleted.append(key)


class _CapturingDb:
    def __init__(self) -> None:
        self.aql = _CapturingAql()
        self._collection = _FakeCollection()

    def collection(self, _name: str) -> _FakeCollection:
        return self._collection


def _edge_call(db: _CapturingDb, edge_collection: str) -> dict[str, Any]:
    calls = [c for c in db.aql.calls if c["bind_vars"].get("@edge") == edge_collection]
    assert len(calls) == 1, f"{edge_collection}: {len(calls)} calls"
    return calls[0]


def test_delete_phase_detaches_the_chain_on_both_ends() -> None:
    db = _CapturingDb()
    repo = ArangoLifecycleRepository(db)  # type: ignore[arg-type]

    assert repo.delete_phase("phase-2") is True

    call = _edge_call(db, col.NEXT_PHASE)
    assert call["bind_vars"]["vertex"] == f"{col.GROWTH_PHASES}/phase-2"
    # Both ends: the successor edge this phase owns *and* the predecessor edge that
    # points at it. Outbound alone left the latter dangling.
    assert "(e._from == @vertex OR e._to == @vertex)" in call["query"]


def test_delete_phase_leaves_its_directed_edges_outbound() -> None:
    """The other three edges really do start at the phase — not everything is `any`."""
    db = _CapturingDb()
    repo = ArangoLifecycleRepository(db)  # type: ignore[arg-type]

    repo.delete_phase("phase-2")
    phase_id = f"{col.GROWTH_PHASES}/phase-2"

    for edge in (col.REQUIRES_PROFILE, col.USES_NUTRIENTS, col.GOVERNED_BY):
        call = _edge_call(db, edge)
        assert call["bind_vars"]["vertex"] == phase_id
        assert "e._from == @vertex" in call["query"]

    # …and the lifecycle's `consists_of` edge points *at* the phase.
    consists_of = _edge_call(db, col.CONSISTS_OF)
    assert "e._to == @vertex" in consists_of["query"]
