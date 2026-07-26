"""Repository-level contract for the single care-task dedup helper (#509).

``ArangoTaskRepository.find_open_care_task`` is THE tenant-aware idempotency
predicate for care reminders. These tests pin the query contract without a live
ArangoDB — following the capturing-fake-db style of ``test_dashboard_counts_repo``:

* the lookup is **tenant-scoped** — the AQL filters ``doc.tenant_key ==
  @tenant_key`` and the caller's tenant is passed as a bind var (never inlined),
  so a care task in another tenant can never be returned (the closed gap);
* it matches the reminder type by the ``"— {value}"`` name suffix and guards
  against ``null`` names;
* the recency rule ("completed today counts as satisfied") is expressed in the
  query, gated by the ``include_completed_today`` bind var and evaluated against
  the **UTC** calendar day even when the server's local timezone says otherwise
  (#772); and
* the result document is wrapped into a ``Task`` (or ``None`` when empty).
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime
from typing import Any

import pytest

from app.common.enums import ReminderType, TaskCategory, TaskStatus
from app.data_access.arango.task_repository import ArangoTaskRepository


class _CapturingAql:
    def __init__(self, result: list[Any]) -> None:
        self.query: str | None = None
        self.bind_vars: dict[str, Any] | None = None
        self._result = result

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        self.query = query
        self.bind_vars = bind_vars or {}
        return iter(self._result)


class _CapturingDb:
    def __init__(self, result: list[Any]) -> None:
        self.aql = _CapturingAql(result)


def _repo(result: list[Any]) -> ArangoTaskRepository:
    return ArangoTaskRepository(_CapturingDb(result))  # type: ignore[arg-type]


# ── Local-timezone harness for the UTC recency rule (#772) ──────────────────
#
# freezegun (the project's usual clock tool) cannot express this scenario: its
# ``tz_offset`` shifts ``date.today()`` *and* ``datetime.now(UTC)`` by the same
# amount, so the local-vs-UTC divergence the bug lives in never appears. The
# divergence is a property of the *process* timezone, so we set it for real via
# ``TZ`` + ``time.tzset()`` and let the wall clock supply the instant.


@contextmanager
def _local_timezone(tz: str) -> Iterator[None]:
    """Run the block with ``TZ`` set to ``tz``, restoring the previous value."""
    previous = os.environ.get("TZ")
    os.environ["TZ"] = tz
    time.tzset()
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous
        time.tzset()


def _timezone_on_another_calendar_day() -> str:
    """A non-UTC ``TZ`` whose local calendar day differs from the UTC one *now*.

    POSIX ``TZ`` offsets are sign-inverted, so ``"XXX-14"`` is UTC+14 (shifts the
    day forward whenever the UTC hour is >= 10) and ``"XXX+12"`` is UTC-12
    (shifts it backward whenever the UTC hour is < 12). The two ranges overlap,
    so one of them always lands on the far side of midnight — the test is
    date-boundary-crossing at every hour of the day, with hours of margin, and
    never flaky. Plain offset strings are used instead of named zones so the
    harness does not depend on a tzdata database being installed.
    """
    for tz in ("XXX-14", "XXX+12"):
        with _local_timezone(tz):
            if date.today() != datetime.now(UTC).date():
                return tz
    raise AssertionError("no candidate TZ put the local calendar day off the UTC one")


def test_lookup_is_tenant_scoped() -> None:
    repo = _repo([])
    repo.find_open_care_task("plant-1", ReminderType.WATERING, "tenant-A")

    aql = repo._db.aql  # type: ignore[attr-defined]
    # The tenant is filtered in the DB and passed through as a bind var — never
    # inlined into the query string (cross-tenant leak guard).
    assert "doc.tenant_key == @tenant_key" in aql.query
    assert aql.bind_vars["tenant_key"] == "tenant-A"
    assert "tenant-A" not in aql.query
    # Collection is bound via @@col, not string-interpolated (injection guard).
    assert "@@col" in aql.query
    assert aql.bind_vars["@col"] == repo._collection_name


def test_lookup_binds_entity_and_reminder_type_suffix() -> None:
    repo = _repo([])
    repo.find_open_care_task("plant-1", ReminderType.FERTILIZING, "tenant-A")

    aql = repo._db.aql  # type: ignore[attr-defined]
    assert aql.bind_vars["entity_key"] == "plant-1"
    assert aql.bind_vars["care_category"] == TaskCategory.CARE_REMINDER.value
    # Reminder type is matched via the name suffix (audit P5 — not a first-class field).
    assert aql.bind_vars["name_suffix"] == f"— {ReminderType.FERTILIZING.value}"
    assert "RIGHT(doc.name, LENGTH(@name_suffix)) == @name_suffix" in aql.query
    # Null-name guard so a task without a name never raises / matches.
    assert "doc.name != null" in aql.query


def test_recency_rule_gated_by_include_completed_today() -> None:
    repo = _repo([])
    repo.find_open_care_task("plant-1", ReminderType.WATERING, "tenant-A")

    aql = repo._db.aql  # type: ignore[attr-defined]
    assert aql.bind_vars["include_completed_today"] is True
    assert aql.bind_vars["open_statuses"] == [
        TaskStatus.PENDING.value,
        TaskStatus.IN_PROGRESS.value,
    ]
    assert aql.bind_vars["completed_status"] == TaskStatus.COMPLETED.value
    # The "completed today counts as satisfied" recency rule is in the query and
    # gated by the include-flag bind var.
    assert "@include_completed_today" in aql.query
    assert "LEFT(doc.completed_at, 10) >= @today" in aql.query
    # Newest-first so ties keep the latest task.
    assert "SORT doc.due_date DESC, doc.created_at DESC" in aql.query
    assert "LIMIT 1" in aql.query


@pytest.mark.skipif(not hasattr(time, "tzset"), reason="TZ switching needs a POSIX time.tzset()")
def test_recency_rule_uses_utc_not_local_date() -> None:
    """The ``@today`` bind var is the UTC day, not the local server day (#772).

    ``completed_at`` is stamped in UTC, so ``LEFT(doc.completed_at, 10)`` is a UTC
    calendar date. Deriving ``@today`` from ``date.today()`` compared it against
    the *local* date: identical on a UTC host — which is why the bug survived —
    but a day off elsewhere for part of every day, silently applying the #509
    idempotency guard to the wrong day.

    The local timezone is forced onto the other side of the date boundary here,
    so this test fails against the unfixed code on any host.
    """
    tz = _timezone_on_another_calendar_day()

    with _local_timezone(tz):
        local_today = date.today()
        utc_today = datetime.now(UTC).date()
        # Premise of the test: the two clocks really are on different days.
        assert local_today != utc_today

        repo = _repo([])
        repo.find_open_care_task("plant-1", ReminderType.WATERING, "tenant-A")
        bound_today = repo._db.aql.bind_vars["today"]  # type: ignore[attr-defined]

    assert bound_today == utc_today.isoformat()
    assert bound_today != local_today.isoformat()


@pytest.mark.skipif(not hasattr(time, "tzset"), reason="TZ switching needs a POSIX time.tzset()")
def test_recency_rule_utc_day_matches_the_completed_at_clock() -> None:
    """The bound day is the one a just-completed task would carry (#772).

    Ties the read side to the write side: ``TaskService`` stamps
    ``completed_at = datetime.now(UTC)``, so a task completed right now must fall
    inside ``LEFT(completed_at, 10) >= @today`` — including when the server's
    local timezone sits on a different calendar day.
    """
    tz = _timezone_on_another_calendar_day()

    with _local_timezone(tz):
        # Exactly how TaskService.complete_task stamps a completion.
        completed_at = datetime.now(UTC).isoformat()

        repo = _repo([])
        repo.find_open_care_task("plant-1", ReminderType.WATERING, "tenant-A")
        bound_today = repo._db.aql.bind_vars["today"]  # type: ignore[attr-defined]

        # The AQL predicate, evaluated in Python over the same string prefixes.
        assert completed_at[:10] >= bound_today
        assert date.today().isoformat() != bound_today


def test_complete_flag_false_is_forwarded() -> None:
    repo = _repo([])
    repo.find_open_care_task(
        "plant-1",
        ReminderType.WATERING,
        "tenant-A",
        include_completed_today=False,
    )

    aql = repo._db.aql  # type: ignore[attr-defined]
    assert aql.bind_vars["include_completed_today"] is False


def test_returns_wrapped_task_when_document_found() -> None:
    doc = {
        "_key": "task-1",
        "name": "Monstera — watering",
        "instruction": "Water Monstera.",
        "category": TaskCategory.CARE_REMINDER.value,
        "entity_key": "plant-1",
        "entity_type": "plant_instance",
        "tenant_key": "tenant-A",
        "status": TaskStatus.PENDING.value,
    }
    repo = _repo([doc])

    task = repo.find_open_care_task("plant-1", ReminderType.WATERING, "tenant-A")

    assert task is not None
    assert task.key == "task-1"
    assert task.tenant_key == "tenant-A"
    assert task.name == "Monstera — watering"


def test_returns_none_when_no_document() -> None:
    repo = _repo([])

    assert repo.find_open_care_task("plant-1", ReminderType.WATERING, "tenant-A") is None
