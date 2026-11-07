"""The one read of a document by key - an unreadable key is an absent document, not a 500 (#2709).

``StandardCollection.get(key)`` answers ``None`` for a key that names no document, but not for every key
a client can put into a path segment. Measured against ArangoDB 3.12 (2026-11-07):

* ``"a b"``, ``"x!%"``, ``"%zz"``, ``"ä"``, a 300-character key: ``None`` - the server answers 1202 and the
  driver reads it as "not there".
* ``""``, ``"."`` and ``".."``: ``DocumentGetError`` [HTTP 404][ERR 1203] - the empty or dot segment is
  normalised out of ``/_api/document/<collection>/<key>``, so the server sees a malformed URL. ``"."`` and
  ``".."`` reach a route as ``%2E`` / ``%2E%2E`` (Starlette decodes them into the path parameter), and every
  keyed route of the garden plan answered them with a 500.
* a key with a ``/`` naming another collection (``"other/x"``): ``DocumentParseError`` raised by the driver
  before any request is sent.

**Why here and not ``Path(pattern=ARANGO_KEY_PATTERN)``.** The pattern
(:data:`app.common.pagination.ARANGO_KEY_PATTERN`) admits ``"."`` and ``".."`` - both are made of allowed
characters, and ArangoDB even stores them on insert - so it would not have closed the 500, and a tightened
pattern would have to be repeated on every ``{key}`` of every router. A key that cannot be read is answered
"absent" at the single place every repository reads through, so the routes inherit it.

**Why not catch 1203.** ``1203`` is also what a missing collection answers. Mapping it to ``None`` would turn
a broken deployment into a quiet 404; the dot keys are refused *before* the request instead, and a real 1203
still raises.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

import structlog
from arango.collection import StandardCollection
from arango.exceptions import DocumentParseError
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from app.common.exceptions import StoredDocumentInvalidError

logger = structlog.get_logger(__name__)

#: Keys the document endpoint cannot address: the URL normalisation removes them before the server sees them.
UNADDRESSABLE_KEYS: frozenset[str] = frozenset({"", ".", ".."})


def get_document(collection: StandardCollection, key: str) -> dict[str, Any] | None:
    """The document ``key`` of ``collection``, or ``None`` when it does not exist or cannot be addressed."""
    if key in UNADDRESSABLE_KEYS:
        return None
    try:
        return cast("dict[str, Any] | None", collection.get(key))
    except DocumentParseError:
        # A "/" naming another collection: no document of *this* collection has that key.
        return None


def invalid_fields(exc: PydanticValidationError) -> list[str]:
    """The dotted paths of the fields ``exc`` rejects - never their values (NFR-006), for the log and the 409."""
    return sorted({".".join(str(part) for part in error["loc"]) for error in exc.errors()})


def model_or_conflict[T: BaseModel](model: type[T], doc: dict[str, Any], *, entity: str) -> T:
    """``doc`` as ``model``; a stored document that fails validation raises the 409 (#2709).

    For a read whose caller acts on the answer - a read by key, a write path's sibling read, an export: leaving
    the row out would answer 404 for a document that exists, or let a write miss it (a duplicate slot id, an
    undercounted quota, a backup without the row). The raw document rides on the error as ``stored`` so an
    ownership walk can answer a foreign tenant's row as absent first.
    """
    try:
        return model(**doc)
    except PydanticValidationError as exc:
        key = str(doc.get("_key") or doc.get("key") or "")
        fields = invalid_fields(exc)
        logger.warning("stored_document.unreadable", entity=entity, key=key, fields=fields)
        raise StoredDocumentInvalidError(entity, key, fields, stored=doc) from None


def readable_rows[T: BaseModel](model: type[T], rows: Iterable[dict[str, Any]], *, read: str) -> list[T]:
    """``rows`` as ``model``, a row that fails validation logged and left out (#2709).

    Only for a read that is displayed and acted on by nobody: one legacy document (a retired enum value, a bound
    a later model tightened) must not turn the whole plan into an error. Every other read uses
    :func:`model_or_conflict`. The log names the document and the failing fields, never their values.
    """
    readable: list[T] = []
    for row in rows:
        try:
            readable.append(model(**row))
        except PydanticValidationError as exc:
            logger.warning(
                "stored_document.unreadable_row_skipped",
                read=read,
                model=model.__name__,
                key=row.get("_key") or row.get("slot_key"),
                fields=invalid_fields(exc),
            )
    return readable
