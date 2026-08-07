"""A fake ArangoDB that replays whatever tenant predicate a query *actually* carries.

Issue #927 is a class of defect where the endpoint anchors on a foreign key and
the repository query behind it carries no ``tenant_key`` filter. Testing that
with an ordinary stub proves nothing: a stub returns whatever the test told it
to, so it agrees with the implementation whether or not the predicate is there.

These doubles work the other way round. Each holds the rows a query's
**non-tenant** predicates select and then applies the remaining predicates by
*reading them out of the query text*. Remove the ``tenant_key`` filter from the
repository and the fake hands the foreign rows straight back — exactly as real
ArangoDB would. That is what makes the negative tests in
``tests/api/test_cross_tenant_reads_router.py`` red on the unfixed code and
green on the fixed one.

The parser is deliberately small: it understands ``<var>.<field> ==|!= @<bind>``,
which is the shape both the hand-written repository AQL and
:class:`~app.data_access.arango.query_builder.AQLBuilder` emit. Anything it does
not understand is ignored rather than guessed at, so a fake can never be
*stricter* than the query — the failure mode is a false green on the fixed code,
never a false red, and the red-first observation rules that out.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from typing import Any

#: ``plant.tenant_key == @tenant_key``, ``doc.status == @val0``, … — the single
#: predicate shape both the hand-written AQL and ``AQLBuilder`` produce.
_PREDICATE_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_.]*)\s*(==|!=)\s*@([A-Za-z_][A-Za-z0-9_]*)")

#: Resolver: maps a row to the document an AQL variable stands for. ``doc`` is
#: the row itself; a joined variable (``plant``, ``task``, …) resolves to another
#: document, or to ``None`` for a dangling reference.
type Resolver = Callable[[dict[str, Any]], dict[str, Any] | None]


def apply_predicates(
    rows: list[dict[str, Any]],
    query: str,
    bind_vars: dict[str, Any],
    resolvers: dict[str, Resolver] | None = None,
) -> list[dict[str, Any]]:
    """Filter ``rows`` by every predicate the query text actually spells out.

    A predicate on an AQL variable with no resolver is skipped — the fake models
    what it was told about and nothing more.
    """
    resolvers = {"doc": lambda row: row, **(resolvers or {})}
    for var, field, op, bind_name in _PREDICATE_RE.findall(query):
        resolve = resolvers.get(var)
        if resolve is None or bind_name not in bind_vars:
            continue
        want = bind_vars[bind_name]

        def matches(row: dict[str, Any], _r=resolve, _f=field, _o=op, _w=want) -> bool:
            target = _r(row)
            value = None if target is None else target.get(_f)
            return value == _w if _o == "==" else value != _w

        rows = [row for row in rows if matches(row)]
    return rows


def paginate(rows: list[dict[str, Any]], query: str, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
    """Apply ``LIMIT @offset, @limit`` when the query carries one."""
    for offset_name, limit_name in (("offset", "limit"), ("__offset", "__limit")):
        if f"@{offset_name}" in query and offset_name in bind_vars:
            offset = int(bind_vars[offset_name])
            limit = int(bind_vars[limit_name])
            return rows[offset : offset + limit]
    return rows


class ReplayingAql:
    """``db.aql`` double dispatching on a marker substring of the query.

    Routes are matched in registration order, so a more specific marker must be
    registered before a broader one that also occurs in it.
    """

    def __init__(self) -> None:
        self._routes: list[tuple[str, Callable[[str, dict[str, Any]], Any]]] = []
        #: Every ``(query, bind_vars)`` pair seen, for assertions about *how* a
        #: query was issued rather than only about what it returned.
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def route(self, marker: str, handler: Callable[[str, dict[str, Any]], Any]) -> ReplayingAql:
        self._routes.append((marker, handler))
        return self

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None) -> Iterator[Any]:
        bind_vars = dict(bind_vars or {})
        self.calls.append((query, bind_vars))
        for marker, handler in self._routes:
            if marker in query:
                result = handler(query, bind_vars)
                return iter(result) if isinstance(result, list) else iter([result])
        raise AssertionError(f"No route matched this query — the fake is incomplete:\n{query}")


class ReplayingDatabase:
    """``StandardDatabase`` double exposing only ``aql`` and ``collection``."""

    def __init__(self, aql: ReplayingAql, collections: dict[str, Any] | None = None) -> None:
        self.aql = aql
        self._collections = collections or {}

    def collection(self, name: str) -> Any:
        return self._collections[name]


def rows_and_count(
    rows: list[dict[str, Any]],
    query: str,
    bind_vars: dict[str, Any],
    resolvers: dict[str, Resolver] | None = None,
) -> Any:
    """Serve either the page or the count of the same filtered row set.

    Filtering the page but not the count would still leak the *number* of another
    tenant's rows, so the fake answers both from one filtered list — a repository
    that filters only one of the two queries is caught by whichever assertion
    reads the other.
    """
    filtered = apply_predicates(rows, query, bind_vars, resolvers)
    if "COLLECT WITH COUNT" in query:
        return [len(filtered)]
    return paginate(filtered, query, bind_vars)
