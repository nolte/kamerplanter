"""Parameterised AQL building blocks.

Timestamp comparisons compare instants (#1784)
----------------------------------------------

ArangoDB orders strings by ICU collation, not by the time they spell, and this
system stores one instant in several spellings: Pydantic's JSON dump writes
``…:00Z`` for a whole second and ``…:00.500000Z`` otherwise,
``datetime.isoformat()`` writes ``…:00+00:00``, AQL's ``DATE_ISO8601`` writes
``…:00.000Z``. ``.`` collates before ``+`` and ``Z``, so compared as text
``'…04:30:00.5Z' < '…04:30:00+00:00'`` is **true** although the left instant is
half a second later (measured on ArangoDB 3.12.8). Every ordering comparison
(``<``, ``<=``, ``>``, ``>=``) on a stored timestamp therefore reduces **both**
sides to epoch milliseconds: ``DATE_TIMESTAMP(doc.x) < DATE_TIMESTAMP(@cutoff)``.
Normalising the writes instead would be an open class — every write path plus a
migration — while the comparison is one place per query.

Two consequences every such comparison has to handle:

* ``DATE_TIMESTAMP`` of ``null`` or of an unparsable string is ``null``, and AQL
  orders ``null`` below every number: ``null < n`` is true. A ``<``/``<=``
  selector must say what an undated record means — exclude it
  (``DATE_TIMESTAMP(doc.x) != null AND …``) or include it on purpose
  (``doc.x == null OR …``) — instead of letting the collation decide. ``>``/``>=``
  are null-safe (``null > n`` is false).
* ``DATE_TIMESTAMP`` truncates to milliseconds. For a strict ``doc < cutoff``
  that can only make a record look *younger*, never older: if
  ``doc_ms < cut_ms`` then ``doc_true < doc_ms + 1 <= cut_ms <= cut_true``, so a
  record selected as older than the cutoff really is. Only a record within the
  same millisecond as the cutoff can be kept one run longer — the safe direction
  for a deletion sweep.

Keeping a persistent index usable (#1809)
-----------------------------------------

``DATE_TIMESTAMP(doc.x)`` hides ``doc.x`` from the optimizer, so a sweep over an
indexed timestamp became a full collection scan. Where that index matters, the
instant comparison is preceded by a **raw pre-filter** on the bare field against
a bound one day past the cutoff (:func:`instant_prefilter_bound`)::

    FILTER doc.x < @cutoff_slack
      AND DATE_TIMESTAMP(doc.x) != null AND DATE_TIMESTAMP(doc.x) < DATE_TIMESTAMP(@cutoff)

The raw comparison only has to be a *superset* of the exact one. The collation
misorders spellings of the **same second** (fraction and offset notation) and a
stored local time differs from its UTC instant by at most 14 hours; a bound one
day later lies past both, so no record the instant comparison selects is dropped
by the pre-filter (measured on ArangoDB 3.12.8 with fractional, ``Z``,
``+00:00``, ``+14:00`` and ``-12:00`` spellings). The index narrows the scan;
the instant comparison decides. The guard accepts a bare ``<``/``<=`` on a
timestamp only when an instant comparison of the same direction on the same
field follows in the same ``FILTER``.

The guard ``tests/unit/guards/test_aql_timestamp_comparisons_are_instants.py``
holds every hand-written query in ``app/`` to this rule.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from typing import Any, ClassVar

#: How far past its cutoff the raw pre-filter of an instant comparison reaches.
INSTANT_PREFILTER_SLACK = timedelta(days=1)


def instant_prefilter_bound(cutoff: datetime | str) -> str:
    """The ``@<name>_slack`` value for a raw, index-usable pre-filter (module docstring).

    ``cutoff`` plus :data:`INSTANT_PREFILTER_SLACK`, as a UTC ISO string. A naive
    ``cutoff`` is read as UTC, like every timestamp this system stores.
    """
    moment = datetime.fromisoformat(cutoff) if isinstance(cutoff, str) else cutoff
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return (moment.astimezone(UTC) + INSTANT_PREFILTER_SLACK).isoformat()


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

    #: Operators that order their operands; on a timestamp these compare instants.
    _ORDERING_OPS: ClassVar[frozenset[str]] = frozenset({">", ">=", "<", "<="})

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
        """Add ``FILTER doc.<field> <op> @v<n>``.

        An ordering operator on a timestamp — a ``datetime`` value, or a string
        value on a ``*_at`` field — compares instants instead (see the module
        docstring): ``DATE_TIMESTAMP(doc.<field>) <op> DATE_TIMESTAMP(@v<n>)``,
        with the value bound as an ISO string. For ``<``/``<=`` a record whose
        timestamp is missing or unreadable is excluded rather than ordered below
        every instant.
        """
        if op not in self._ALLOWED_OPS:
            raise ValueError(f"Unsupported AQL operator: {op!r}")
        if not self._FIELD_RE.match(field):
            raise ValueError(f"Invalid AQL field name: {field!r}")
        var_name = f"v{self._var_counter}"
        self._var_counter += 1
        if op in self._ORDERING_OPS and self._is_timestamp(field, value):
            instant = f"DATE_TIMESTAMP(doc.{field})"
            clause = f"{instant} {op} DATE_TIMESTAMP(@{var_name})"
            if op in {"<", "<="}:
                clause = f"{instant} != null AND {clause}"
            self._filters.append(clause)
            self._bind_vars[var_name] = value.isoformat() if isinstance(value, datetime) else value
            return self
        self._filters.append(f"doc.{field} {op} @{var_name}")
        self._bind_vars[var_name] = value
        return self

    @staticmethod
    def _is_timestamp(field: str, value: Any) -> bool:
        """Whether ``doc.<field> <op> value`` orders two points in time.

        A ``date`` (not ``datetime``) value is excluded on purpose: a date-typed
        field is stored as fixed-width ``YYYY-MM-DD`` and compares correctly as
        text.
        """
        if isinstance(value, datetime):
            return True
        if isinstance(value, date):
            return False
        return isinstance(value, str) and field.rsplit(".", 1)[-1].endswith("_at")

    #: Name suffixes (and whole names) :meth:`sort` orders as instants.
    _INSTANT_SORT_SUFFIXES: ClassVar[tuple[str, ...]] = ("_at", "_date", "_until")
    _INSTANT_SORT_NAMES: ClassVar[frozenset[str]] = frozenset({"timestamp"})

    @classmethod
    def sorts_as_instant(cls, field: str) -> bool:
        """Whether :meth:`sort` orders ``field`` by its instant rather than its text (#1801).

        Decided by name, because a sort has no value whose type could tell: every
        ``*_at``, ``*_date`` and ``*_until`` field, and ``timestamp``. A date-typed
        field (``purchase_date``) is included harmlessly — ``DATE_TIMESTAMP`` of a
        fixed-width ``YYYY-MM-DD`` orders exactly like its text.
        """
        name = field.rsplit(".", 1)[-1]
        return name in cls._INSTANT_SORT_NAMES or name.endswith(cls._INSTANT_SORT_SUFFIXES)

    def sort(self, field: str, direction: str = "ASC") -> AQLBuilder:
        """Add ``SORT doc.<field> <direction>``; a timestamp field sorts by instant.

        The ICU collation that misplaces a record in a comparison (module
        docstring) misorders it in a sort too — within the same second, which is
        exactly the tie a "latest" pick or a page boundary decides (#1801). A
        timestamp field (:meth:`sorts_as_instant`) therefore sorts
        ``DATE_TIMESTAMP(doc.<field>)``. ``null`` and unreadable values sort first
        ascending, as a missing raw value already did.
        """
        if direction not in self._ALLOWED_DIRECTIONS:
            raise ValueError(f"Invalid sort direction: {direction!r}")
        if not self._FIELD_RE.match(field):
            raise ValueError(f"Invalid AQL sort field: {field!r}")
        key = f"DATE_TIMESTAMP(doc.{field})" if self.sorts_as_instant(field) else f"doc.{field}"
        self._sort = f"{key} {direction}"
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
