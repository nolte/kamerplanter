"""Tombstones of deleted objects that a buffered write created (REQ-053 WP 9.3, #2743).

A late replay of a buffered write whose object the user deleted since must not re-create it. The repository that
deletes such an object (a task that carries a completion id, an attachment that carries an upload id) records the
id here; the replay path reads it and answers 404 ``client_event.deleted``.

A tombstone is ``{tenant_key, client_event_id, kind, deleted_at}`` - no personal data, the id is a random UUID the
client made. ``(tenant_key, client_event_id)`` is unique; a TTL index on ``deleted_at`` removes the row after
:data:`~app.domain.models.client_event.CLIENT_EVENT_TOMBSTONE_DAYS`. The tenant deletion removes a tenant's rows
(``TenantErasureEngine.INVENTORY``).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.data_access.arango.conflicts import UNIQUE_CONSTRAINT_VIOLATED

logger = structlog.get_logger(__name__)

_TOMBSTONED = """
FOR t IN @@tombstones
    FILTER t.tenant_key == @tenant_key AND t.client_event_id IN @ids
    LIMIT @limit
    RETURN t.client_event_id
"""


def record_tombstone(db: StandardDatabase, *, tenant_key: str, client_event_id: str, kind: str) -> None:
    """Record that the object of ``client_event_id`` was deleted; a second record of the same id is a no-op.

    Best effort after the delete: a failure is logged, never raised - the delete happened and is what the caller
    asked for; a missing tombstone only lets a very late replay re-create the object.
    """
    if not tenant_key or not client_event_id:
        return
    document = {
        "tenant_key": tenant_key,
        "client_event_id": client_event_id,
        "kind": kind,
        # ISO 8601 UTC: the TTL index reads a date string.
        "deleted_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        db.collection(col.CLIENT_EVENT_TOMBSTONES).insert(document)
    except DocumentInsertError as exc:
        if exc.error_code != UNIQUE_CONSTRAINT_VIOLATED:
            logger.error("client_event_tombstone_failed", kind=kind, error_code=exc.error_code)


def tombstoned_ids(db: StandardDatabase, ids: Sequence[str], *, tenant_key: str) -> set[str]:
    """The ids among ``ids`` whose object was deleted (bounded by ``len(ids)``)."""
    if not tenant_key or not ids:
        return set()
    cursor = cast(
        "Cursor",
        db.aql.execute(
            _TOMBSTONED,
            bind_vars=cast(
                "dict[str, Any]",
                {
                    "@tombstones": col.CLIENT_EVENT_TOMBSTONES,
                    "tenant_key": tenant_key,
                    "ids": list(ids),
                    "limit": len(ids),
                },
            ),
        ),
    )
    return {str(value) for value in cursor}
