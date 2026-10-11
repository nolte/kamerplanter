"""In-memory doubles for the per-tenant beat walk (MT-032, #2128).

The beats that read actuators, tanks and plants used to load every tenant's rows
(``get_all_pages(repo, all_tenants=True)``) and drop a closed tenant's rows in Python.
They now ask the tenant repository for the tenants they may touch
(:meth:`ITenantRepository.keys_in_status`) and the row repository for exactly those
tenants' rows (:meth:`BaseArangoRepository.iter_for_tenants`).

``TenantRows`` answers ``iter_for_tenants`` with the semantics of the AQL — tenant
``IN`` the given keys (an empty key never matches), every ``(field, op, value)``
filter applied, ``_key`` order, one ``page_size`` window at a time — and
``tests/integration/test_tenant_walk_query.py`` measures that claim against the real
server. Its ``get_all`` refuses: a beat that falls back to loading the collection
fails the test instead of passing on a double that would have answered it.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Iterable, Iterator
from typing import Any
from unittest.mock import MagicMock

from app.common.enums import TenantStatus


def field_of(row: Any, name: str) -> Any:
    if isinstance(row, dict):
        return row.get(name)
    return getattr(row, name, None)


def row_key(row: Any) -> str:
    key = field_of(row, "_key") if isinstance(row, dict) else getattr(row, "key", None)
    return "" if key is None else str(key)


_OPS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">": lambda a, b: a is not None and a > b,
    "IN": lambda a, b: a in b,
}


class TenantRows:
    """``iter_for_tenants`` over in-memory rows (dicts or models); ``get_all`` refuses."""

    def __init__(self, rows: Iterable[Any] = (), **extra: Any) -> None:
        self.rows = sorted(rows, key=row_key)
        #: Every call: (sorted tenant keys, filters).
        self.walks: list[tuple[list[str], list[tuple[str, str, Any]]]] = []
        #: Every ``iter_without_tenant`` call: its filters.
        self.tenantless_walks: list[list[tuple[str, str, Any]]] = []
        #: Rows handed out per page, in order.
        self.pages: list[int] = []
        for name, value in extra.items():
            setattr(self, name, value)

    def get_all(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("a beat must not load every tenant's rows (MT-032, #2128)")

    def iter_for_tenants(
        self,
        tenant_keys: Collection[str],
        *,
        filters: list[tuple[str, str, Any]] | None = None,
        page_size: int = 1000,
        max_pages: int = 1000,  # noqa: ARG002 - the signature of the real method
    ) -> Iterator[Any]:
        keys = sorted({key for key in tenant_keys if key})
        self.walks.append((keys, list(filters or [])))
        if not keys:
            return
        yield from self._walk(keys, filters, page_size)

    def iter_without_tenant(
        self,
        *,
        filters: list[tuple[str, str, Any]] | None = None,
        page_size: int = 1000,
        max_pages: int = 1000,  # noqa: ARG002 - the signature of the real method
    ) -> Iterator[Any]:
        """The rows whose ``tenant_key`` is empty or missing (``IN [null, ""]``)."""
        self.tenantless_walks.append(list(filters or []))
        yield from self._walk([None, ""], filters, page_size)

    def _walk(self, scope: list[Any], filters: list[tuple[str, str, Any]] | None, page_size: int) -> Iterator[Any]:
        selected = [
            row
            for row in self.rows
            if field_of(row, "tenant_key") in scope
            and all(_OPS[op](field_of(row, name), value) for name, op, value in filters or [])
        ]
        for start in range(0, len(selected), page_size):
            page = selected[start : start + page_size]
            self.pages.append(len(page))
            yield from page


class TenantStates:
    """``keys_in_status`` over stored ``{tenant_key: status}``; records what was asked."""

    def __init__(self, states: dict[str, TenantStatus] | None = None, **extra: Any) -> None:
        self.states = dict(states or {})
        self.asked: list[set[TenantStatus]] = []
        for name, value in extra.items():
            setattr(self, name, value)

    def keys_in_status(self, statuses: Collection[TenantStatus]) -> dict[str, TenantStatus]:
        wanted = set(statuses)
        self.asked.append(wanted)
        return {key: status for key, status in sorted(self.states.items()) if status in wanted}

    def get_by_key(self, key: str) -> Any:
        raise AssertionError(f"a walking beat must not look tenants up one by one (asked for {key!r})")


def active(*keys: str) -> TenantStates:
    """Tenant repository double whose tenants are all ``active``."""
    return TenantStates(dict.fromkeys(keys, TenantStatus.ACTIVE))


AFTER_CURSOR = re.compile(r"doc\._key > @(v\d+)")


class AqlRowsDb:
    """A ``StandardDatabase`` stand-in that answers the walk's page queries the way ArangoDB would.

    For driving a **real** repository's ``iter_for_tenants`` / ``iter_without_tenant``: the
    scope is the ``doc.tenant_key IN @v0`` bind (a missing field reads as ``null``), the
    keyset cursor the ``doc._key > @vN`` bind, the window ``LIMIT @__offset, @__limit``.
    Other filters are not evaluated — the tests that use it pass none.
    """

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
        scope = bind_vars["v0"]
        after_match = AFTER_CURSOR.search(query)
        after = bind_vars[after_match.group(1)] if after_match else None
        selected = [
            dict(row)
            for key, row in sorted(self.rows.items())
            if row.get("tenant_key") in scope and (after is None or key > after)
        ]
        offset, limit = bind_vars["__offset"], bind_vars["__limit"]
        return iter(selected[offset : offset + limit])
