"""ArangoDB's conflict codes, translated into the domain's typed errors — in one place (#1458).

``1210`` (*unique constraint violated*) and ``1200`` (*conflict*) are the two
answers the server may give the loser of one race, and which one arrives is the
server's decision about how far the winner's transaction had got — not a property
of the calling code. Every write path therefore needs the same two-branch
translation, and until REQ-053 WP 1.2 it was written out per path: ``_insert_doc``
got the ``1200`` branch in #1436, ``create_edge`` months later in #1292, and every
caller in between was a 500. This module is the single spelling; the repository
base class and the stream-transaction helper both call :func:`conflict_error_for`
and carry no parser of their own.

The two codes are deliberately **different answers**, not variants of one:

* ``1210`` is a statement **about the data** — a committed, visible document
  already occupies the unique key. :class:`~app.common.exceptions.DuplicateError`,
  named after the real conflicting field, published as ``conflict.duplicate``.
* ``1200`` is a statement **about timing** — a concurrent transaction held the
  same key or index entry and this write could not be serialized against it. It
  says nothing about whether that transaction committed, so it may never be read
  as "the record exists" without a re-read.
  :class:`~app.common.exceptions.WriteConflictError`, published as
  ``conflict.write``. The driver message is not forwarded: it names an index and
  a document key, and these errors' ``details`` are client-visible.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from arango.exceptions import ArangoServerError

from app.common.exceptions import DuplicateError, KamerplanterError, WriteConflictError

#: ``arango.errno.UNIQUE_CONSTRAINT_VIOLATED`` — a statement about the data.
UNIQUE_CONSTRAINT_VIOLATED = 1210
#: ``arango.errno.CONFLICT`` — a statement about timing.
WRITE_WRITE_CONFLICT = 1200
#: ``arango.errno.LOCK_TIMEOUT`` — a collection lock could not be taken in time;
#: raised by ``begin_transaction`` once its ``lock_timeout`` has passed.
LOCK_TIMEOUT = 18
#: ``arango.errno.QUERY_KILLED`` — what an AQL query reports when ``maxRuntime`` ends it.
QUERY_KILLED = 1500

#: Matches the indexed field list in an ArangoDB unique-constraint message:
#: ``... over '["batch_id"]' ...``, the older ``... over 'batch_id' ...``, a
#: compound ``... over 'tenant_key, name'; ...`` (3.12) or a bare ``over [...]``.
_UNIQUE_INDEX_FIELDS_RE = re.compile(
    r"over\s+(?:'(?P<quoted>[^']*)'|(?P<bracketed>\[[^\]]*\])|(?P<bare>[A-Za-z_][A-Za-z0-9_.]*))"
)
_FIELD_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")

#: The scope of a compound unique index: the tenant, or the owning location of a
#: slot (``(location_key, slot_id)``, #2065). It bounds the constraint and is
#: never what the caller collided on; naming it would tell the caller an internal
#: key and point the client at no form field (#2029).
UNIQUE_SCOPE_FIELDS = frozenset({"tenant_key", "location_key"})


def extract_unique_field(error_message: str | None) -> str | None:
    """Extract the conflicting field name from an ArangoDB 1210 error message.

    ArangoDB names the violated unique index in its error message, e.g.::

        unique constraint violated - in index 42 of type persistent
        over '["batch_id"]'; conflicting key: '...'

    Returns the first indexed field that is not a scope (:data:`UNIQUE_SCOPE_FIELDS`)
    — for ``(tenant_key, name)`` that is ``name`` — or the first field when every
    field is a scope. ``None`` when the message does not follow the recognised
    shape, so callers can fall back gracefully.
    """
    if not error_message:
        return None
    match = _UNIQUE_INDEX_FIELDS_RE.search(error_message)
    if match is None:
        return None
    listed = match.group("quoted") or match.group("bracketed") or match.group("bare") or ""
    names: list[str] = _FIELD_NAME_RE.findall(listed)
    if not names:
        return None
    return next((name for name in names if name not in UNIQUE_SCOPE_FIELDS), names[0])


def describe_unique_conflict(error: ArangoServerError, data: Mapping[str, Any]) -> tuple[str, str]:
    """Turn a unique-constraint violation into a ``(field, value)`` pair.

    Reached from inserts **and** updates: an update can violate a unique index
    just as an insert can (reopening a completed care task while an equivalent
    one is already open, #1301), and ``1210`` means the same thing on both.

    Pairs the real conflicting field from the server message with the value taken
    from the document being written, so the resulting :class:`DuplicateError`
    names the actual culprit instead of a ``key='duplicate'`` placeholder. Falls
    back to a non-misleading ``field=''`` when the message cannot be parsed or
    the document is not in hand.
    """
    field = extract_unique_field(getattr(error, "error_message", None))
    if field and field in data:
        return field, str(data[field])
    if field:
        return field, ""
    return "field", ""


def conflict_error_for(
    error: ArangoServerError,
    *,
    entity: str,
    data: Mapping[str, Any] | None = None,
) -> KamerplanterError | None:
    """The domain conflict a refused write stands for, or ``None`` when it is not a conflict.

    Args:
        error: What the driver raised — an insert, update, delete, commit or AQL
            error; only ``error_code`` and ``error_message`` are read.
        entity: What the error is *about* for the caller — usually the collection
            that was written, which is what the existing errors carry.
        data: The document being written, when known; lets the duplicate carry
            the colliding value instead of an empty string.

    Returns:
        The typed error to raise **instead of** *error*, or ``None`` for every
        other code. Returned rather than raised so every ``raise`` is visible at
        the site that performs it, and so an unknown driver failure is re-raised
        as itself and never swallowed into a 409.
    """
    code = getattr(error, "error_code", None)
    if code == UNIQUE_CONSTRAINT_VIOLATED:
        field, value = describe_unique_conflict(error, data or {})
        return DuplicateError(entity, field, value)
    if code == WRITE_WRITE_CONFLICT:
        return WriteConflictError(entity)
    return None
