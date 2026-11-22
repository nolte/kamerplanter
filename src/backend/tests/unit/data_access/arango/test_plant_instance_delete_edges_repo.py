"""Edge cleanup on plant-instance deletion (REQ-003 D10 / REQ-017, Fix #2).

Deleting a plant instance must not leave dangling graph edges — since #2560 the whole derived edge set
(``edges_touching(PLANT_INSTANCES)``) goes with the plant. Besides the
placement / phase edges, the ``descended_from`` lineage edge must be removed in
**both** directions: a plant can be the child (outbound) or the mother (inbound)
of such an edge, and an orphaned inbound edge would otherwise keep
``has_descendants(mother)`` true and permanently block a re-spawn.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango import plant_instance_repository
from app.data_access.arango.graph_edges import edges_touching
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


class _TxnAql(_CapturingAql):
    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any):
        super().execute(query, bind_vars)
        return iter([1] if "DOCUMENT(@id)" in query else [])


class _Txn:
    def __init__(self) -> None:
        self.aql = _TxnAql()
        self.removed: list[str] = []

    def collection(self, _name: str) -> Any:
        txn = self

        class _Handle:
            def delete(self, key: str) -> None:
                txn.removed.append(key)

        return _Handle()


def test_delete_removes_every_derived_edge_including_lineage_both_ways(monkeypatch: pytest.MonkeyPatch) -> None:
    """#2560: the derived set (``edges_touching(PLANT_INSTANCES)``), not the old four-edge hand list."""
    seen: dict[str, Any] = {}

    @contextmanager
    def fake(_db: Any, *, write: Sequence[str], **_: Any) -> Iterator[_Txn]:
        txn = _Txn()
        seen.update(write=tuple(write), txn=txn)
        yield txn

    monkeypatch.setattr(plant_instance_repository, "stream_transaction", fake)

    assert ArangoPlantInstanceRepository(_CapturingDb()).delete("pup-1") is True  # type: ignore[arg-type]

    txn = seen["txn"]
    assert txn.removed == ["pup-1"]
    cut = {
        (call["bind_vars"]["@edges"], "_from" if "e._from IN @ids" in call["query"] else "_to")
        for call in txn.aql.calls
        if "REMOVE e IN @@edges" in call["query"]
    }
    assert cut == set(edges_touching(col.PLANT_INSTANCES))
    # The lineage edge on both ends (child = ``_from``, mother = ``_to``), and the four the hand list had.
    assert {
        (col.DESCENDED_FROM, "_from"),
        (col.DESCENDED_FROM, "_to"),
        (col.PLACED_IN, "_from"),
        (col.PHASE_HISTORY_EDGE, "_from"),
        (col.CURRENT_PHASE, "_from"),
    } <= cut
    assert set(seen["write"]) == {col.PLANT_INSTANCES, *(edge for edge, _ in cut)}


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


def test_get_by_instance_id_with_empty_tenant_still_filters_on_the_tenant() -> None:
    """An empty tenant key matches only rows with an empty tenant, never every tenant's."""
    db = _CapturingDb()
    repo = ArangoPlantInstanceRepository(db)  # type: ignore[arg-type]

    repo.get_by_instance_id("AGV-1-pup", tenant_key="")

    joined = " ".join(c["query"] for c in db.aql.calls)
    assert "tenant_key" in joined
