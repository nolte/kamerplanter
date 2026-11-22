"""#2513 review round 2: what one ``delete_site`` reads and derives, on a fake stream transaction.

The fake answers each statement from canned ids and records it; what the AQL does on a real server is measured by
``tests/integration/test_site_delete_cascade.py``. Pinned here:

* R2 — the irrigation zones are a site dependent like the others: one ``_DEPENDENTS_OF_SITE`` scan per dependent,
  zones included, no zone-only statement;
* R3 — the slots of the removed locations are looked up once per delete (the scope already holds them);
* R4 — the dependents' edge sets are derived once at import time, never per delete.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango import site_repository
from app.data_access.arango.graph_edges import edges_touching
from app.data_access.arango.irrigation_zone_repository import ZONE_EDGES
from app.data_access.arango.site_repository import ArangoSiteRepository


class _FakeCollection:
    def insert(self, document: dict[str, Any], **_: Any) -> None:
        del document

    def delete(self, document: str, **_: Any) -> None:
        del document


class _FakeAql:
    def __init__(self, txn: _FakeTxn) -> None:
        self.txn = txn

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Iterator[Any]:
        bind = bind_vars or {}
        self.txn.statements.append((query, bind))
        if query == site_repository._SITE_FOR_DELETE:
            return iter([{"tenant_key": "t1", "name": "Garden", "revision": 3}])
        if bind.get("@has_slot") == col.HAS_SLOT:
            self.txn.slot_lookups += 1
            return iter([["slots/s1"]])
        if bind.get("@has_object") == col.HAS_GARDEN_OBJECT:
            return iter([[]])
        if bind.get("@plants") == col.PLANT_INSTANCES:
            return iter([0])
        if bind.get("@locations") == col.LOCATIONS and "site_key" in bind and "@contains" not in bind:
            return iter(["locations/bed"])
        if query == site_repository._DEPENDENTS_OF_SITE and bind["@col"] == col.IRRIGATION_ZONES:
            return iter(["irrigation_zones/z1"])
        return iter(())


class _FakeTxn:
    def __init__(self) -> None:
        self.statements: list[tuple[str, dict[str, Any]]] = []
        self.slot_lookups = 0
        self.aql = _FakeAql(self)

    def collection(self, name: str) -> _FakeCollection:
        del name
        return _FakeCollection()

    def check_budget(self) -> None:
        return None


@pytest.fixture
def txn(monkeypatch: pytest.MonkeyPatch) -> _FakeTxn:
    fake = _FakeTxn()

    @contextmanager
    def _stream(*_: Any, **__: Any) -> Iterator[_FakeTxn]:
        yield fake

    monkeypatch.setattr(site_repository, "stream_transaction", _stream)
    return fake


def _removed_ids(txn: _FakeTxn, collection: str) -> list[str]:
    return [
        doc_id
        for query, bind in txn.statements
        if "REMOVE d IN @@col" in query and bind.get("@col") == collection
        for doc_id in bind["ids"]
    ]


def test_delete_site_looks_up_the_slots_of_its_locations_once(txn: _FakeTxn) -> None:
    ArangoSiteRepository(MagicMock()).delete_site("site1", tenant_key="t1", user_key="u1")

    assert txn.slot_lookups == 1
    assert _removed_ids(txn, col.SLOTS) == ["slots/s1"]
    assert _removed_ids(txn, col.LOCATIONS) == ["locations/bed"]


def test_delete_location_still_looks_up_its_slots(txn: _FakeTxn) -> None:
    txn.aql.execute = _location_answers(txn)  # type: ignore[method-assign]

    assert ArangoSiteRepository(MagicMock()).delete_location("bed") is True

    assert txn.slot_lookups == 1
    assert _removed_ids(txn, col.SLOTS) == ["slots/s1"]


def _location_answers(txn: _FakeTxn) -> Any:
    def execute(query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Iterator[Any]:
        bind = bind_vars or {}
        txn.statements.append((query, bind))
        if bind.get("id") == "locations/bed":
            return iter([""])
        if bind.get("@has_slot") == col.HAS_SLOT:
            txn.slot_lookups += 1
            return iter([["slots/s1"]])
        return iter(())

    return execute


def test_zones_are_scanned_and_removed_as_a_site_dependent(txn: _FakeTxn) -> None:
    ArangoSiteRepository(MagicMock()).delete_site("site1", tenant_key="t1", user_key="u1")

    scanned = [bind["@col"] for query, bind in txn.statements if query == site_repository._DEPENDENTS_OF_SITE]
    assert scanned == list(site_repository._SITE_DEPENDENTS)
    assert col.IRRIGATION_ZONES in scanned
    assert not hasattr(site_repository, "_ZONES_OF_SITE")
    assert _removed_ids(txn, col.IRRIGATION_ZONES) == ["irrigation_zones/z1"]
    cut = {
        (bind["@edges"], query.split("FILTER e.", 1)[1].split(" ", 1)[0])
        for query, bind in txn.statements
        if bind.get("ids") == ["irrigation_zones/z1"] and "@edges" in bind
    }
    assert cut == set(ZONE_EDGES)


def test_the_dependent_edges_are_derived_once_not_per_delete(txn: _FakeTxn, monkeypatch: pytest.MonkeyPatch) -> None:
    def _refuse(name: str) -> Any:
        raise AssertionError(f"edges_touching({name!r}) re-derived during a delete")

    monkeypatch.setattr(site_repository, "edges_touching", _refuse)

    ArangoSiteRepository(MagicMock()).delete_site("site1", tenant_key="t1", user_key="u1")

    assert txn.slot_lookups == 1


def test_the_write_set_and_the_runtime_cut_share_one_derivation() -> None:
    pairs = site_repository._DEPENDENT_EDGE_PAIRS
    assert list(pairs) == list(site_repository._SITE_DEPENDENTS)
    assert all(pairs[name] == edges_touching(name) for name in pairs)
    assert tuple(pair for edges in pairs.values() for pair in edges) == site_repository._DEPENDENT_EDGES
    assert {edge for edge, _ in ZONE_EDGES} <= set(site_repository._SITE_DELETE_WRITE)
