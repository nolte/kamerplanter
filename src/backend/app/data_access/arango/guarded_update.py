"""An update that is written only while the columns the caller validated against still hold what it read (#2727).

A service that reads a document, validates a change against some of its stored columns and then writes only the
columns it changed leaves a window: another writer can change one of the columns the validation read, and the
two writes together store a document neither writer validated. ``PATCH /slots`` validates a change against the
stored role, capacity and geometry kind and writes only the changed columns; two PATCHes of one unplaced zone
(role to ``row`` here, the zone's polygon drawn there) stored a row with a polygon, which no read validates.

:func:`update_if_unchanged` closes the window in one AQL query: it reads the document, compares each expected
column (an attribute path in the stored JSON form, a missing attribute reading as the model default the caller
supplies), and writes only when all hold — fenced on the ``_rev`` it compared, so a write that lands between the
comparison and the update is a conflict too. A failed comparison is a
:class:`~app.common.exceptions.WriteConflictError` (409), a missing document a
:class:`~app.common.exceptions.NotFoundError`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.exceptions import ArangoServerError

from app.common.exceptions import NotFoundError, WriteConflictError
from app.data_access.arango.conflicts import conflict_error_for, is_document_not_found
from app.data_access.arango.transactions import StreamTransaction


@dataclass(frozen=True)
class StoredValue:
    """One precondition: the stored value at ``path`` is ``value``; a row without it reads as ``default``."""

    path: tuple[str, ...]
    value: Any
    default: Any = None


#: ``VALUE(doc, path)`` reads a nested attribute (``["geometry", "kind"]``) and answers ``null`` when absent; a
#: ``null`` reads as the default the model gives a row without the column, so a legacy row is not a conflict.
_GUARDED_UPDATE = """
LET doc = DOCUMENT(CONCAT(@prefix, @key))
LET held = doc != null AND (
    FOR c IN @expected
        LET stored = VALUE(doc, c.path)
        RETURN (stored == null ? c.default : stored) == c.value
) ALL == true
LET written = (
    FOR d IN (held ? [doc] : [])
        LET fenced = {_key: d._key, _rev: d._rev}
        UPDATE fenced WITH @data IN @@collection
        OPTIONS {ignoreRevs: false, keepNull: @keep_null, mergeObjects: @merge_objects}
        RETURN NEW
)
RETURN {found: doc != null, new: FIRST(written)}
"""


def update_if_unchanged(
    db: StandardDatabase | StreamTransaction,
    collection: str,
    key: str,
    data: Mapping[str, Any],
    *,
    expected: tuple[StoredValue, ...],
    entity: str,
    keep_null: bool,
    merge_objects: bool,
) -> dict[str, Any]:
    """Write ``data`` into ``collection/key`` only while every ``expected`` value is stored; return the new document.

    ``db`` may be a stream-transaction handle: the write then belongs to that transaction (``PATCH /slots`` takes
    the bed's slot-rule fence in the same one, #2773).

    Raises:
        NotFoundError: the document does not exist (any more).
        WriteConflictError: an expected column holds another value, or a concurrent write changed the document
            between the comparison and the update.
    """
    try:
        cursor = cast(
            "Cursor",
            db.aql.execute(
                _GUARDED_UPDATE,
                bind_vars={
                    "prefix": f"{collection}/",
                    "key": key,
                    "@collection": collection,
                    "expected": [{"path": list(c.path), "value": c.value, "default": c.default} for c in expected],
                    "data": dict(data),
                    "keep_null": keep_null,
                    "merge_objects": merge_objects,
                },
            ),
        )
        row = next(cursor, None)
    except ArangoServerError as exc:
        if is_document_not_found(exc):  # removed between the read and the update
            raise NotFoundError(entity, key) from exc
        conflict = conflict_error_for(exc, entity=entity, data=data)
        if conflict is not None:
            raise conflict from exc
        raise
    if row is None or not row["found"]:
        raise NotFoundError(entity, key)
    if row["new"] is None:
        raise WriteConflictError(entity, "the record changed since it was read; reload it and retry")
    return cast("dict[str, Any]", row["new"])
