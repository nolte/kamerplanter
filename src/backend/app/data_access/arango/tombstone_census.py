"""Count tombstone-shaped values per ``(collection, field)`` (spec/privacy PRIV-206, DEC-28).

One query mechanism, two callers with their own policy:

* the ``privacy.consistency`` beat passes the live cells
  (:meth:`ErasureEngine.tombstone_watch_fields`) and the live pattern
  (:data:`app.domain.models.privacy.TOMBSTONE_REGEX`);
* migration v0109 passes the cells and the pattern it froze when it was written (NFR-016 M-7).

Nothing here decides *which* cells are watched or *what* a tombstone looks like, so the
migration's result cannot move when the inventory moves — only the AQL that counts is shared.
The count is read-only and returns numbers only: no row key, no value.

**Tenant binding.** The census is not bound to a tenant: a cell is reported as one number for the
installation, and several watched collections are account- or platform-scoped and carry no
``tenant_key`` at all (``refresh_tokens``, ``auth_providers``…). It writes nothing, so it cannot
write across a tenant boundary either.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.domain.interfaces.tombstone_census import ITombstoneCensus

#: One attribute, bound by name (``doc[@a]``); a dotted field is at most two segments deep, the same
#: limit the erasure executor applies to rule paths (``sites.plan.plan_updated_by``).
_COUNT_ONE_SEGMENT = """
FOR doc IN @@collection
  FILTER IS_STRING(doc[@a]) AND REGEX_TEST(doc[@a], @pattern)
  COLLECT WITH COUNT INTO n
  RETURN n
"""

_COUNT_TWO_SEGMENTS = """
FOR doc IN @@collection
  FILTER IS_STRING(doc[@a][@b]) AND REGEX_TEST(doc[@a][@b], @pattern)
  COLLECT WITH COUNT INTO n
  RETURN n
"""


def cell_name(collection: str, field: str) -> str:
    """The report and metric name of a cell: ``<collection>.<field>``."""
    return f"{collection}.{field}"


def _segments(field: str) -> list[str]:
    """The one or two attribute names of *field*; anything else is refused."""
    segments = field.split(".")
    if len(segments) in (1, 2) and all(segments):
        return segments
    msg = f"a census field is one or two attribute names, got {field!r}"
    raise ValueError(msg)


def _count_cell(db: StandardDatabase, collection: str, segments: list[str], pattern: str) -> int:
    # Each query constant is passed to ``execute`` by name, so the AQL guards can read it.
    binds: dict[str, Any] = {"@collection": collection, "pattern": pattern, "a": segments[0]}
    if len(segments) == 1:
        cursor = cast(Cursor, db.aql.execute(_COUNT_ONE_SEGMENT, bind_vars=binds))
    else:
        cursor = cast(Cursor, db.aql.execute(_COUNT_TWO_SEGMENTS, bind_vars=binds | {"b": segments[1]}))
    return int(sum(cursor))


def count_tombstones_by_field(db: StandardDatabase, fields: Sequence[tuple[str, str]], pattern: str) -> dict[str, int]:
    """``{"<collection>.<field>": count}`` of the rows whose *field* matches *pattern*.

    Every value is bound (``@@collection``, ``@a``/``@b``, ``@pattern``); nothing is interpolated.
    A collection the database does not have counts as ``0`` — an installation that never created it
    cannot hold a tombstone in it.

    Raises:
        ValueError: a field is empty or deeper than two segments.
    """
    counts: dict[str, int] = {}
    for collection, field in fields:
        segments = _segments(field)
        if not db.has_collection(collection):
            counts[cell_name(collection, field)] = 0
            continue
        counts[cell_name(collection, field)] = _count_cell(db, collection, segments, pattern)
    return counts


class ArangoTombstoneCensus(ITombstoneCensus):
    """:class:`ITombstoneCensus` over ArangoDB, through :func:`count_tombstones_by_field`."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def count_tombstones(self, fields: Sequence[tuple[str, str]], pattern: str) -> dict[str, int]:
        return count_tombstones_by_field(self._db, fields, pattern)
