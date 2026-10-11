"""MT-032 (#2128) — the tenant walk the beats read through: tenant-filtered in AQL, one keyset page at a time.

``BaseArangoRepository.iter_for_tenants`` replaces ``get_all_pages(repo, all_tenants=True)``
in the actuator, tank and plant beats. Four properties make the swap sound, each asserted
here against a database double that answers the generated AQL from in-memory rows:

* the tenant is a query predicate (``doc.tenant_key IN @…``), never a Python filter, and an
  empty key set issues no query at all — a tenantless row cannot be selected;
* pages are read lazily: the worker holds one page, so its memory does not grow with the
  installation;
* the cursor is the last ``_key`` seen, not an offset, so a row deleted by the caller
  mid-walk cannot shift the next window and skip a row;
* no count query is paid.

``ArangoTenantRepository.keys_in_status`` names the tenants. The real-server half (the AQL
as ArangoDB evaluates it, the legacy ``is_active`` reading) is
``tests/integration/test_tenant_walk_query.py``.
"""

from __future__ import annotations

import re
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.common.enums import TenantStatus
from app.data_access.arango.base_repository import PagingCeilingError
from app.data_access.arango.tank_repository import ArangoTankRepository
from app.data_access.arango.tenant_repository import ArangoTenantRepository

_AFTER = re.compile(r"doc\._key > @(v\d+)")
_TANK = {"tank_type": "nutrient", "volume_liters": 50.0}


class _RowsDb:
    """Answers the walk's page queries from ``rows`` the way ArangoDB would."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = {row["_key"]: row for row in rows}
        self.executed: list[tuple[str, dict[str, Any]]] = []
        self.aql = MagicMock()
        self.aql.execute.side_effect = self._execute

    def collection(self, name: str) -> MagicMock:
        return MagicMock(name=name)

    def _execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any) -> Any:
        bind_vars = dict(bind_vars or {})
        self.executed.append((query, bind_vars))
        assert "doc.tenant_key IN @v0" in query
        tenants = bind_vars["v0"]
        after_match = _AFTER.search(query)
        after = bind_vars[after_match.group(1)] if after_match else None
        selected = [
            dict(row)
            for key, row in sorted(self.rows.items())
            if row.get("tenant_key") in tenants and (after is None or key > after)
        ]
        offset, limit = bind_vars["__offset"], bind_vars["__limit"]
        return iter(selected[offset : offset + limit])


def _tanks(n: int, tenant: str = "t1") -> list[dict[str, Any]]:
    return [{"_key": f"tank{i:05d}", "tenant_key": tenant, "name": f"Tank {i}", **_TANK} for i in range(n)]


def test_an_empty_tenant_set_reads_nothing_and_asks_nothing() -> None:
    db = _RowsDb(_tanks(3))

    assert list(ArangoTankRepository(db).iter_for_tenants([])) == []
    assert list(ArangoTankRepository(db).iter_for_tenants(["", ""])) == []
    assert db.executed == []


def test_the_tenant_is_a_query_predicate_and_no_count_is_paid() -> None:
    db = _RowsDb([*_tanks(2, "t1"), *_tanks(0, "t2"), {"_key": "x", "tenant_key": "t3", "name": "X", **_TANK}])

    rows = list(ArangoTankRepository(db).iter_for_tenants({"t2", "t1", ""}))

    assert [r.key for r in rows] == ["tank00000", "tank00001"]
    query, bind_vars = db.executed[0]
    assert bind_vars["v0"] == ["t1", "t2"]  # sorted, the empty key dropped
    assert "SORT doc._key ASC" in query
    assert all("COLLECT WITH COUNT" not in q for q, _ in db.executed)


def test_every_row_is_read_once_in_key_order_across_pages() -> None:
    db = _RowsDb(_tanks(2501))

    rows = list(ArangoTankRepository(db).iter_for_tenants(["t1"]))

    assert [r.key for r in rows] == [f"tank{i:05d}" for i in range(2501)]
    assert len(db.executed) == 3
    second_query, second_vars = db.executed[1]
    after_var = _AFTER.search(second_query)
    assert after_var is not None
    assert second_vars[after_var.group(1)] == "tank00999"
    assert {v["__offset"] for _, v in db.executed} == {0}


def test_the_walk_reads_one_page_before_the_caller_sees_a_row() -> None:
    """The worker holds a page, not the collection: the second page is read only when the first is used up."""
    db = _RowsDb(_tanks(1500))
    walk = ArangoTankRepository(db).iter_for_tenants(["t1"])

    first = next(walk)

    assert first.key == "tank00000"
    assert len(db.executed) == 1


def test_a_row_deleted_mid_walk_does_not_skip_the_next_one() -> None:
    """An offset window would shift by the deleted row and skip ``tank01000``; the keyset cursor cannot."""
    db = _RowsDb(_tanks(2000))
    seen: list[str] = []

    for row in ArangoTankRepository(db).iter_for_tenants(["t1"]):
        seen.append(row.key)
        if row.key == "tank00010":
            del db.rows["tank00000"]  # the caller removes a row it already handled

    assert seen == [f"tank{i:05d}" for i in range(2000)]


def test_extra_filters_are_query_predicates_too() -> None:
    db = _RowsDb(_tanks(1))

    list(ArangoTankRepository(db).iter_for_tenants(["t1"], filters=[("removed_on", "==", None)]))

    query, bind_vars = db.executed[0]
    assert "doc.removed_on == @v1" in query
    assert bind_vars["v1"] is None


def test_the_page_ceiling_raises_instead_of_looping() -> None:
    db = _RowsDb(_tanks(5))

    with pytest.raises(PagingCeilingError):
        list(ArangoTankRepository(db).iter_for_tenants(["t1"], page_size=2, max_pages=2))


def test_a_page_size_below_one_is_refused() -> None:
    with pytest.raises(ValueError, match="page_size"):
        list(ArangoTankRepository(_RowsDb([])).iter_for_tenants(["t1"], page_size=0))


class _TenantDb:
    def __init__(self, answer: list[dict[str, str]]) -> None:
        self.answer = answer
        self.executed: list[tuple[str, dict[str, Any]]] = []
        self.aql = MagicMock()
        self.aql.execute.side_effect = lambda query, bind_vars=None, **_: (
            self.executed.append((query, dict(bind_vars or {}))) or iter(self.answer)
        )

    def collection(self, name: str) -> MagicMock:
        return MagicMock(name=name)


def test_keys_in_status_filters_the_state_in_the_query() -> None:
    db = _TenantDb([{"key": "t1", "status": "active"}, {"key": "t2", "status": "suspended"}])

    states = ArangoTenantRepository(db).keys_in_status({TenantStatus.SUSPENDED, TenantStatus.ACTIVE})

    assert states == {"t1": TenantStatus.ACTIVE, "t2": TenantStatus.SUSPENDED}
    query, bind_vars = db.executed[0]
    assert "FILTER state IN @statuses" in query
    assert bind_vars["statuses"] == ["active", "suspended"]


def test_keys_in_status_without_a_status_asks_nothing() -> None:
    db = _TenantDb([])

    assert ArangoTenantRepository(db).keys_in_status(set()) == {}
    assert db.executed == []
