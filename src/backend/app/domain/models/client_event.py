"""The client event id of a buffered write (REQ-053 §34 wave 9, E-06; WP 9.3).

A client that buffers a write while offline (UI-NFR-012, GP-UX-024) gives it a ``client_event_id`` - a UUID it
makes once, when the user acts, and sends with every attempt. The server stores the id **on the object the write
creates** (the care event, the task's completion, the attachment), under a unique index per tenant, so a replay
can never create a second object:

* the same id with the same request answers the stored object (200);
* two attempts at once: the unique index lets one insert win, the other reads the winner;
* the same id with a different request is refused, 409 ``client_event.payload_mismatch``
  (:class:`~app.common.exceptions.ClientEventMismatchError`).

"The same request" is decided by a digest of the request as the server read it (:func:`client_event_digest`),
stored beside the id. The digest includes the caller's account key: one member cannot claim another member's
write by replaying its id.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid5

#: The field a stored object carries the id in, and the field of its digest.
CLIENT_EVENT_ID_FIELD = "client_event_id"
CLIENT_EVENT_DIGEST_FIELD = "client_event_digest"


def client_event_digest(payload: Mapping[str, Any]) -> str:
    """SHA-256 over the canonical JSON of ``payload`` (sorted keys, no whitespace).

    ``payload`` is JSON-shaped already (``model_dump(mode="json")``); a value JSON cannot spell is written with
    ``str`` so a digest never fails on a stray ``datetime``.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def batch_item_client_event_id(batch_id: UUID, task_key: str) -> str:
    """The id one task of a batch completion stores: a name-based UUID of the batch id and the task key.

    A batch carries **one** ``client_event_id``; every task of it needs an id of its own, because the index is
    unique per tenant. ``uuid5`` derives it deterministically, so a replay of the batch finds each task's id again
    and decides per task.
    """
    return str(uuid5(batch_id, task_key))


@dataclass(frozen=True)
class ClientEventStamp:
    """The id and the digest a write stores on the object it creates."""

    client_event_id: str
    digest: str
