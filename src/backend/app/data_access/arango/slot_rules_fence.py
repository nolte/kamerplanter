"""The per-bed fence of the slot rules V-04 and V-06 (#2773).

V-04 (a slot lies inside its bed) and V-06 (active zones of one bed do not overlap) are bed-level rules: a writer
checks its slot against the bed's frame and its sibling slots, read **before** its transaction opens (containment
and overlap are CPU work, GP-NFR-013). Touching the bed document first inside the transaction (``_lock_location``)
serialises two writers only while both transactions are open at once; a writer whose transaction begins after the
other one committed sees no conflict and stores a slot checked against siblings that are gone. Two ``PATCH
/slots`` redrawing two zones of one bed into the same area both passed that way.

The fence is a counter on the bed document, ``slot_rules_revision``. A writer reads it in the **same AQL
snapshot** as the frame and the siblings it validates against (``load_slot_rule_basis``) and, inside its
transaction, compares and raises it before it writes: a writer that committed in between has raised it, so the
comparison fails and the loser answers 409 ``conflict.write`` (:class:`~app.common.exceptions.WriteConflictError`,
retryable after a reload) instead of storing a layout no validation saw. A writer still in flight holds the bed
document; the second compare-and-raise is then the server's write-write conflict, the same 409.

Every write that can invalidate a sibling's check takes the fence: a slot's geometry or role (``PATCH /slots``),
the slot batch (``POST /locations/{key}/slots/batch``), the layout slots of a planting run, a mixed culture and a
quick planting, the bed frame a plan batch reshapes, and the slots a new season copies into a bed. A write that
only removes or archives slots cannot make a sibling's check wrong and does not take it.

A document without the attribute reads as ``0``; the location model ignores the attribute on read, and the
location writes merge, so no other write drops it.

:func:`lock_bed` is the one bed write a slot transaction makes: with a revision it is the fence (compare, raise,
touch ``updated_at``), without one the plain lock of the writes that only remove or archive slots. A write that
carries slots but no revision is a programming error and refused (:func:`require_fence`).
"""

from __future__ import annotations

from collections.abc import Mapping, Sized

from arango.exceptions import AQLQueryExecuteError

from app.common.exceptions import NotFoundError, WriteConflictError
from app.data_access.arango import collections as col
from app.data_access.arango.conflicts import WRITE_WRITE_CONFLICT
from app.data_access.arango.query_builder import aql_field
from app.data_access.arango.transactions import StreamTransaction

#: The attribute on the location document; not a model field, so no API reads or writes it.
SLOT_RULES_REVISION = "slot_rules_revision"

_TAKE = f"""
FOR l IN @@locations
    FILTER l._key IN @keys AND (l.{aql_field(SLOT_RULES_REVISION)} || 0) == @expected[l._key]
    UPDATE l WITH MERGE({{ {aql_field(SLOT_RULES_REVISION)}: @expected[l._key] + 1 }}, @touch) IN @@locations
    RETURN l._key
"""

_LOCK = "FOR l IN @@locations FILTER l._key == @key UPDATE l WITH {updated_at: @now} IN @@locations RETURN 1"

_EXISTING = "FOR l IN @@locations FILTER l._key IN @keys RETURN l._key"


class SlotRulesConflictError(WriteConflictError):
    """The fence missed: another write changed a bed's slots or frame since the check read them (409, retryable).

    A subclass, so the plan batch can answer it with its own revision conflict (``plan.revision_conflict``) while
    every other caller sees the plain ``WRITE_CONFLICT``.
    """

    def __init__(self) -> None:
        super().__init__(
            "Location", "the bed's slots or frame changed since they were checked against V-04/V-06; reload and retry"
        )


def take_slot_rules(txn: StreamTransaction, expected: Mapping[str, int], *, now: str | None = None) -> None:
    """Compare each bed's ``slot_rules_revision`` with the one its check read and raise it, inside ``txn``.

    Run it before the transaction's first slot write. ``txn`` is the stream-transaction handle; the collection
    ``locations`` must be declared for writing. ``now`` also stamps the bed's ``updated_at`` (the lock's write).

    Raises:
        NotFoundError: a bed of ``expected`` is gone.
        SlotRulesConflictError: another write changed a bed's slots or frame since the check read them, or holds
            the bed in a transaction still open (the server's write-write conflict) - 409 either way.
    """
    if not expected:
        return
    keys = sorted(expected)
    touch = {"updated_at": now} if now is not None else {}
    try:
        taken = set(
            txn.aql.execute(
                _TAKE,
                bind_vars={"@locations": col.LOCATIONS, "keys": keys, "expected": dict(expected), "touch": touch},
            )
        )
    except AQLQueryExecuteError as exc:
        if exc.error_code == WRITE_WRITE_CONFLICT:
            raise SlotRulesConflictError from exc
        raise
    if len(taken) == len(keys):
        return
    existing = set(txn.aql.execute(_EXISTING, bind_vars={"@locations": col.LOCATIONS, "keys": keys}))
    missing = [key for key in keys if key not in existing]
    if missing:
        raise NotFoundError("Location", missing[0])
    raise SlotRulesConflictError


def lock_bed(
    txn: StreamTransaction, location_key: str, now: str, *, revision: int | None, must_exist: bool = True
) -> None:
    """The bed write a slot transaction makes first: the fence with a ``revision``, the plain lock without one.

    Either way the bed document is written, so two transactions of one bed open at once conflict (409). Only the
    fence also refuses a writer whose transaction opens after another one committed.

    Raises:
        NotFoundError: the bed is gone (``must_exist``; always with a revision).
        SlotRulesConflictError: the fence missed.
    """
    if revision is not None:
        take_slot_rules(txn, {location_key: revision}, now=now)
        return
    touched = list(txn.aql.execute(_LOCK, bind_vars={"@locations": col.LOCATIONS, "key": location_key, "now": now}))
    if not touched and must_exist:
        raise NotFoundError("Location", location_key)


def require_fence(revision: int | None, slots: Sized, *, write: str) -> None:
    """A write that carries slots into a bed must carry the fence its check read; refusing is a programming error."""
    if revision is None and len(slots) > 0:
        raise ValueError(f"{write} carries slots but no slot_rules_revision: its V-04/V-06 check is unfenced (#2773).")
