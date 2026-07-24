from __future__ import annotations

import re
from typing import Any, ClassVar


def escape_aql_like(value: str) -> str:
    """Escape AQL ``LIKE`` wildcards in a user-supplied search term.

    AQL ``LIKE`` treats ``%`` (any sequence) and ``_`` (single character) as
    wildcards and ``\\`` as the escape character. A raw user term wrapped in
    ``%...%`` would otherwise let a caller inject wildcards (or an escape) into
    the pattern. The backslash is escaped first so it does not double-escape the
    wildcard escapes added afterwards; the result matches the term literally.

    This is the single source of truth for ``LIKE``-pattern escaping — every
    repository that wraps user input in a ``LIKE`` pattern must route through it.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class AQLBuilder:
    """Builds parameterized AQL queries to prevent injection."""

    #: Comparison operators allowed in :meth:`filter`. ``op`` is interpolated
    #: into the query text, so it is whitelisted to keep the builder injection
    #: safe even though callers pass code-level constants today.
    _ALLOWED_OPS: ClassVar[frozenset[str]] = frozenset({"==", "!=", ">", ">=", "<", "<=", "IN", "NOT IN", "LIKE"})

    #: Sort directions allowed in :meth:`sort`.
    _ALLOWED_DIRECTIONS: ClassVar[frozenset[str]] = frozenset({"ASC", "DESC"})

    #: Field names are interpolated (``doc.<field>``); restrict to identifiers
    #: and dotted paths so a hostile field name cannot break out of the clause.
    _FIELD_RE: ClassVar[re.Pattern[str]] = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")

    def __init__(self, collection: str) -> None:
        self._collection = collection
        self._filters: list[str] = []
        self._bind_vars: dict[str, Any] = {}
        self._sort: str | None = None
        self._limit: int | None = None
        self._offset: int | None = None
        self._var_counter = 0

    def filter(self, field: str, op: str, value: Any) -> AQLBuilder:
        if op not in self._ALLOWED_OPS:
            raise ValueError(f"Unsupported AQL operator: {op!r}")
        if not self._FIELD_RE.match(field):
            raise ValueError(f"Invalid AQL field name: {field!r}")
        var_name = f"v{self._var_counter}"
        self._var_counter += 1
        self._filters.append(f"doc.{field} {op} @{var_name}")
        self._bind_vars[var_name] = value
        return self

    def sort(self, field: str, direction: str = "ASC") -> AQLBuilder:
        if direction not in self._ALLOWED_DIRECTIONS:
            raise ValueError(f"Invalid sort direction: {direction!r}")
        if not self._FIELD_RE.match(field):
            raise ValueError(f"Invalid AQL sort field: {field!r}")
        self._sort = f"doc.{field} {direction}"
        return self

    def paginate(self, offset: int, limit: int) -> AQLBuilder:
        self._offset = offset
        self._limit = limit
        return self

    def build_list(self) -> tuple[str, dict[str, Any]]:
        parts = [f"FOR doc IN {self._collection}"]
        for f in self._filters:
            parts.append(f"  FILTER {f}")
        if self._sort:
            parts.append(f"  SORT {self._sort}")
        bind_vars = dict(self._bind_vars)
        if self._offset is not None and self._limit is not None:
            # SEC-B5: never interpolate offset/limit into the query text; bind
            # them instead. Reserved ``__``-prefixed names cannot collide with
            # the ``v0..vN`` filter placeholders.
            parts.append("  LIMIT @__offset, @__limit")
            bind_vars["__offset"] = self._offset
            bind_vars["__limit"] = self._limit
        parts.append("  RETURN doc")
        return "\n".join(parts), bind_vars

    def build_count(self) -> tuple[str, dict[str, Any]]:
        parts = [f"FOR doc IN {self._collection}"]
        for f in self._filters:
            parts.append(f"  FILTER {f}")
        parts.append("  COLLECT WITH COUNT INTO total")
        parts.append("  RETURN total")
        return "\n".join(parts), self._bind_vars
