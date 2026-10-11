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

from collections.abc import Collection, Iterable, Iterator
from typing import Any

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
        selected = [
            row
            for row in self.rows
            if field_of(row, "tenant_key") in keys
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
