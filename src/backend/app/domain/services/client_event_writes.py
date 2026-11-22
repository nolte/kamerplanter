"""The insert of a replayable client write and its lost race (REQ-053 WP 9.3, shared by WP 9.13).

A write that carries a ``client_event_id`` stores the id under a unique index per tenant (v0106). Two attempts with
the same id race on that index; the loser must read the winner instead of answering an error:

* ``DuplicateError`` naming a client-event index (``1210``): the winner committed - read it;
* ``WriteConflictError`` (``1200``): the winner may still be writing - read it, else try again, a bounded number
  of times, then give up loudly;
* a ``DuplicateError`` of any other unique index is not a replay and is raised as it is.

One helper for the single care event (``POST /care-events``) and the zone round of "rain - skipped" (one event per
bed, ``insert_many``): the caller passes the insert and the read-back of what its stamps stored, so the race rule
cannot drift between them.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.common.exceptions import DuplicateError, WriteConflictError
from app.domain.models.client_event import is_client_event_conflict

#: How often a replayable write tries its insert while a concurrent one holds the same id.
CLIENT_WRITE_ATTEMPTS = 3


@dataclass(frozen=True)
class ReplayableOutcome[W, R]:
    """Exactly one of the two is set: what this attempt wrote, or what the winner of the race had stored."""

    written: W | None = None
    replayed: R | None = None


def insert_or_read_winner[W, R](
    insert: Callable[[], W],
    read_stored: Callable[[], R | None],
    *,
    attempts: int = CLIENT_WRITE_ATTEMPTS,
) -> ReplayableOutcome[W, R]:
    """Run ``insert``; when the client-event index refuses it, answer ``read_stored()`` - the winner's object.

    ``read_stored`` reads what the caller's stamps stored and raises itself when that is another request (409
    ``client_event.payload_mismatch``). A refusal whose winner cannot be read is raised as it came.
    """
    for attempt in range(attempts):
        try:
            return ReplayableOutcome(written=insert())
        except DuplicateError as exc:
            if not is_client_event_conflict(exc.details):
                raise  # another unique index refused the write: not a replay
            stored = read_stored()
            if stored is None:
                raise
            return ReplayableOutcome(replayed=stored)
        except WriteConflictError:
            stored = read_stored()
            if stored is not None:
                return ReplayableOutcome(replayed=stored)
            if attempt == attempts - 1:  # the winner rolled back, or is still writing
                raise
    raise AssertionError("unreachable: the loop returns or raises")  # pragma: no cover
