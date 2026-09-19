"""#1535 — ``delete_slot`` must detach the ``has_slot`` edge that points at the slot.

``_delete_slot_internal`` asked for the edge with a wildcard on the *other* end::

    self.delete_edges(col.HAS_SLOT, from_id=f"{col.LOCATIONS}/%", to_id=slot_id)

``delete_edges`` binds the vertex as a parameter and compares it with ``==``
(``base_repository.py``: ``clause = "e._from == @vertex"``). There is no ``LIKE``,
so ``%`` is a literal character and ``locations/%`` is not a document id any edge
carries: the call matched nothing, every time. The slot document was deleted and
its incoming edge stayed behind, so a traversal from the location still walked it.

The edge points *at* the slot, so the end to detach is the inbound one — the same
repair #1525 made for ``phase_history_edge``.

The assertion below is on the *same expression* the rule is about: the AQL clause
and the bound vertex of the ``has_slot`` removal. Asserting only "one has_slot call
was issued" would have been green against the broken code too.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.data_access.arango.site_repository import ArangoSiteRepository


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

    def get(self, key: str) -> None:  # pragma: no cover - not reached by this test
        return None


class _CapturingDb:
    def __init__(self) -> None:
        self.aql = _CapturingAql()
        self._collection = _FakeCollection()

    def collection(self, _name: str) -> _FakeCollection:
        return self._collection


def _edge_calls(db: _CapturingDb, edge_collection: str) -> list[dict[str, Any]]:
    return [c for c in db.aql.calls if c["bind_vars"].get("@edge") == edge_collection]


def test_delete_slot_removes_the_incoming_has_slot_edge() -> None:
    db = _CapturingDb()
    repo = ArangoSiteRepository(db)  # type: ignore[arg-type]

    assert repo.delete_slot("slot-1") is True

    slot_id = f"{col.SLOTS}/slot-1"
    has_slot = _edge_calls(db, col.HAS_SLOT)
    assert len(has_slot) == 1
    call = has_slot[0]

    # Anchored on the slot, on the end the edge actually points at …
    assert call["bind_vars"]["vertex"] == slot_id
    assert "e._to == @vertex" in call["query"]

    # … and with no pattern character anywhere in the bound values: the query
    # compares with `==`, so a `%` is a literal that matches nothing.
    assert not any("%" in v for v in call["bind_vars"].values() if isinstance(v, str))


def test_delete_slot_still_detaches_its_outbound_edges() -> None:
    """The two edges that start *at* the slot keep their outbound anchor."""
    db = _CapturingDb()
    repo = ArangoSiteRepository(db)  # type: ignore[arg-type]

    repo.delete_slot("slot-1")
    slot_id = f"{col.SLOTS}/slot-1"

    for edge in (col.ADJACENT_TO, col.FILLED_WITH):
        calls = _edge_calls(db, edge)
        assert len(calls) == 1, edge
        assert calls[0]["bind_vars"]["vertex"] == slot_id
        assert "e._from == @vertex" in calls[0]["query"]
