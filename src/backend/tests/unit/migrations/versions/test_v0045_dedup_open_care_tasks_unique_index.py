"""Unit tests for v0045_dedup_open_care_tasks_unique_index — the *pure* half.

The migration's two load-bearing properties are properties of a real ArangoDB:
that creating a unique index over a key space with collisions fails, and that a
newly configured computed value is not applied retroactively to stored documents.
A fake database cannot exhibit either, and a fake that pretended to would be the
"positive test certifies nothing" trap — so those live in
``tests/integration/test_v0045_care_task_dedup_migration.py``, against a real
server on the pre-#1301 collection shape.

What is genuinely testable in isolation is the survivor rule: *which* of a
duplicate group stays open. It has to be the task the application has been acting
on, i.e. the one ``find_open_care_task`` returns (``SORT due_date DESC,
created_at DESC LIMIT 1``); picking any other would close the task a user can see
in their queue and leave a different one behind. That is a pure ordering decision
over document dicts, and it is what this file pins.
"""

from __future__ import annotations

from app.migrations.versions.v0045_dedup_open_care_tasks_unique_index import (
    _LOSER_STATUS,
    _pick_survivor,
    migration,
)


def _doc(key: str, *, due: str | None = None, created: str | None = None) -> dict:
    doc: dict = {"_key": key}
    if due is not None:
        doc["due_date"] = due
    if created is not None:
        doc["created_at"] = created
    return doc


def test_newest_due_date_wins():
    docs = [
        _doc("a", due="2026-06-10T00:00:00+00:00", created="2026-06-09T10:00:00+00:00"),
        _doc("b", due="2026-06-14T00:00:00+00:00", created="2026-06-09T09:00:00+00:00"),
        _doc("c", due="2026-06-12T00:00:00+00:00", created="2026-06-09T11:00:00+00:00"),
    ]
    assert _pick_survivor(docs)["_key"] == "b"


def test_created_at_breaks_a_due_date_tie():
    """Exactly the racing-producers case: same computed due date, different insert times."""
    docs = [
        _doc("a", due="2026-06-14T00:00:00+00:00", created="2026-06-09T09:00:00.100+00:00"),
        _doc("b", due="2026-06-14T00:00:00+00:00", created="2026-06-09T09:00:00.300+00:00"),
        _doc("c", due="2026-06-14T00:00:00+00:00", created="2026-06-09T09:00:00.200+00:00"),
    ]
    assert _pick_survivor(docs)["_key"] == "b"


def test_a_missing_due_date_ranks_oldest_and_never_beats_a_dated_task():
    """``find_open_care_task`` sorts a null ``due_date`` last; the survivor rule agrees."""
    docs = [
        _doc("undated", created="2026-06-09T12:00:00+00:00"),
        _doc("dated", due="2026-06-14T00:00:00+00:00", created="2026-06-09T09:00:00+00:00"),
    ]
    assert _pick_survivor(docs)["_key"] == "dated"


def test_survivor_is_deterministic_when_every_timestamp_matches():
    """A re-run over an unchanged volume must close the same tasks (M-3)."""
    docs = [
        _doc("k2", due="2026-06-14T00:00:00+00:00", created="2026-06-09T09:00:00+00:00"),
        _doc("k1", due="2026-06-14T00:00:00+00:00", created="2026-06-09T09:00:00+00:00"),
        _doc("k3", due="2026-06-14T00:00:00+00:00", created="2026-06-09T09:00:00+00:00"),
    ]
    first = _pick_survivor(docs)["_key"]
    assert first == _pick_survivor(list(reversed(docs)))["_key"]


def test_losers_are_closed_not_completed():
    """``completed`` would additionally suppress the next reminder for the UTC day (#509)."""
    assert _LOSER_STATUS == "skipped"


def test_migration_metadata():
    assert migration.version == "0045"
    assert migration.reversible is False
