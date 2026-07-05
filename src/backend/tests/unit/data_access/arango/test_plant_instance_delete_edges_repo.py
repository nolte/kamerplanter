"""Edge cleanup on plant-instance deletion (REQ-003 D10 / REQ-017, Fix #2).

Deleting a plant instance must not leave dangling graph edges. Besides the
placement / phase edges, the ``descended_from`` lineage edge must be removed in
**both** directions: a plant can be the child (outbound) or the mother (inbound)
of such an edge, and an orphaned inbound edge would otherwise keep
``has_descendants(mother)`` true and permanently block a re-spawn.
"""

from __future__ import annotations

from typing import Any

from app.data_access.arango import collections as col
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository


class _CapturingAql:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.calls.append({"query": query, "bind_vars": bind_vars or {}})
        return iter([])  # no edges to remove in this fake


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


def _edge_calls(db: _CapturingDb, edge_collection: str) -> list[dict[str, Any]]:
    return [c for c in db.aql.calls if c["bind_vars"].get("@edge") == edge_collection]


def test_delete_removes_descended_from_edges_in_both_directions() -> None:
    db = _CapturingDb()
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]

    assert repo.delete("pup-1") is True

    # The document itself is deleted.
    assert db._collection.deleted == ["pup-1"]

    # A descended_from cleanup is issued for this vertex …
    lineage = _edge_calls(db, col.DESCENDED_FROM)
    assert len(lineage) == 1
    call = lineage[0]
    # … in BOTH directions (child=outbound _from, mother=inbound _to).
    assert "(e._from == @vertex OR e._to == @vertex)" in call["query"]
    assert call["bind_vars"]["vertex"] == f"{col.PLANT_INSTANCES}/pup-1"

    # Regression guard: the pre-existing placement/phase cleanups still happen.
    assert _edge_calls(db, col.PLACED_IN)
    assert _edge_calls(db, col.PHASE_HISTORY_EDGE)
    assert _edge_calls(db, col.CURRENT_PHASE)


def test_get_by_instance_id_can_be_tenant_scoped() -> None:
    """Fix #1 support: the pup-existence lookup constrains to the mother's tenant."""
    db = _CapturingDb()
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]

    repo.get_by_instance_id("AGV-1-pup", tenant_key="tenant-a")

    assert db.aql.calls, "a lookup query should have been issued"
    joined = " ".join(c["query"] for c in db.aql.calls)
    bind_values = {k: v for c in db.aql.calls for k, v in c["bind_vars"].items()}
    # Both the instance_id and the tenant_key are bound (never interpolated).
    assert "AGV-1-pup" in bind_values.values()
    assert "tenant-a" in bind_values.values()
    assert "tenant_key" in joined
