"""#1535 / #1573 / #2560 — ``delete_slot`` cuts every edge the graph lets end at a slot, on the end it names.

History of this file: #1535 found the ``has_slot`` removal anchored on a ``locations/%`` wildcard that ``==`` never
matched; #1573 found ``adjacent_to`` cut on the outbound half only. Both were hand-listed edges. Since #2560 the
delete cuts the derived set (``graph_edges.edges_touching(SLOTS)``) — the same derivation the location delete uses —
so ``placed_in``, ``log_slot``, ``run_planned_at`` and ``system_has_growbed`` go too, and a relation registered later
is cut without touching the repository.

The assertion is on the *same expression* the rule is about: every ``(edge collection, endpoint)`` pair of the
derivation is removed with the slot's id bound, and every one of those collections is declared to the transaction.
The real-server counterpart is ``tests/integration/test_slot_edge_cleanup.py``.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango import site_repository
from app.data_access.arango.graph_edges import edges_touching
from app.data_access.arango.site_repository import ArangoSiteRepository

SLOT_ID = f"{col.SLOTS}/slot-1"


class _Aql:
    def __init__(self, *, exists: bool) -> None:
        self.exists = exists
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Iterator[Any]:
        self.calls.append((query, dict(bind_vars or {})))
        if "DOCUMENT(@id)" in query:
            return iter([1] if self.exists else [])
        return iter([])


class _Txn:
    def __init__(self, *, exists: bool) -> None:
        self.aql = _Aql(exists=exists)


def _open(monkeypatch: pytest.MonkeyPatch, *, exists: bool) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    @contextmanager
    def fake(_db: Any, *, write: Sequence[str], entity: str, **_: Any) -> Iterator[_Txn]:
        txn = _Txn(exists=exists)
        seen.update(write=tuple(write), entity=entity, txn=txn)
        yield txn

    monkeypatch.setattr(site_repository, "stream_transaction", fake)
    return seen


def _removed_pairs(txn: _Txn) -> set[tuple[str, str]]:
    pairs = set()
    for query, bind_vars in txn.aql.calls:
        if "REMOVE e IN @@edges" in query:
            assert bind_vars["ids"] == [SLOT_ID]
            pairs.add((bind_vars["@edges"], "_from" if "e._from IN @ids" in query else "_to"))
    return pairs


def test_delete_slot_cuts_every_derived_edge_pair(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _open(monkeypatch, exists=True)

    assert ArangoSiteRepository(object()).delete_slot("slot-1") is True  # type: ignore[arg-type]

    derived = set(edges_touching(col.SLOTS))
    assert _removed_pairs(seen["txn"]) == derived
    # The self-referencing adjacency on both ends (#1573 SCR-001), ``has_slot`` on the end it points at (#1535), and
    # the edges the hand list never had (#2560).
    assert {
        (col.ADJACENT_TO, "_from"),
        (col.ADJACENT_TO, "_to"),
        (col.HAS_SLOT, "_to"),
        (col.PLACED_IN, "_to"),
        (col.RUN_PLANNED_AT, "_to"),
    } <= derived
    assert {edge for edge, _ in derived} | {col.SLOTS} == set(seen["write"])


def test_delete_slot_removes_the_slot_row(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _open(monkeypatch, exists=True)

    ArangoSiteRepository(object()).delete_slot("slot-1")  # type: ignore[arg-type]

    removals = [bind_vars for query, bind_vars in seen["txn"].aql.calls if "REMOVE d IN @@col" in query]
    assert removals == [{"@col": col.SLOTS, "ids": [SLOT_ID]}]


def test_a_missing_slot_writes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _open(monkeypatch, exists=False)

    assert ArangoSiteRepository(object()).delete_slot("slot-1") is False  # type: ignore[arg-type]

    assert [query for query, _ in seen["txn"].aql.calls if "REMOVE" in query] == []
