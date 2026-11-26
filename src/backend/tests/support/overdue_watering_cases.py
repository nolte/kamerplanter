"""One case table for the overdue-watering selection, run against ArangoDB AND the unit fake (#3135).

``ArangoNotificationRepository.find_overdue_watering`` is an AQL filter; the unit
tests of the escalation chain run over
:class:`~tests.unit.domain.services.notification_fakes.EscalationNotificationRepo`,
whose ``find_overdue_watering`` is a Python reading of that filter. A fake that
selects a row the real statement would not (or the reverse) lets the whole chain
look right while production does something else — the project has been bitten by
exactly that (fixtures inventing data no query returns).

So the predicate is not described twice, it is **measured** twice against the
same expectations:

* ``tests/integration/test_overdue_watering_candidates.py`` seeds every case as a
  stored document and asks the real statement;
* ``tests/unit/domain/services/test_overdue_watering_fake_matches_the_case_table.py``
  builds the same documents as models and asks the fake.

A change to either side that the other does not follow turns one of them red.

Each case is a stored document (the shape ArangoDB holds) plus whether it is
selected for :data:`CUTOFF` at :data:`LEVEL`. No personal data: every value is
synthetic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

TENANT = "tenant-overdue"
OTHER_TENANT = "tenant-overdue-other"
USER = "user-overdue"
LEVEL = 0

#: The escalation's cutoff (``now - escalation_days[level]``), spelled like ``isoformat()``.
CUTOFF_ISO = "2026-11-20T12:00:00+00:00"
CUTOFF = datetime.fromisoformat(CUTOFF_ISO)

LONG_AGO = "2026-10-01T00:00:00+00:00"
RECENT = "2026-11-25T08:00:00+00:00"
FUTURE = "2026-12-28T00:00:00+00:00"


@dataclass(frozen=True)
class Case:
    """One stored notification and whether the overdue query selects it."""

    name: str
    selected: bool
    #: Overrides on top of :func:`base_document`; ``data`` replaces the whole ``data``.
    doc: dict = field(default_factory=dict)
    why: str = ""


def base_document(key: str) -> dict:
    """An unacted level-0 watering reminder of :data:`TENANT`, due long before the cutoff."""
    return {
        "_key": key,
        "tenant_key": TENANT,
        "user_key": USER,
        "notification_type": "care.watering",
        "title": "Monstera",
        "body": "watering due: Monstera",
        "group_key": f"care.watering:{key}",
        "escalation_level": LEVEL,
        "read_at": None,
        "acted_at": None,
        "created_at": LONG_AGO,
        "data": {"plant_key": key, "due_date": LONG_AGO},
    }


CASES: tuple[Case, ...] = (
    Case("due_long_before_the_cutoff", True, why="the plain overdue reminder"),
    Case(
        "reused_row_old_created_at_future_due",
        False,
        {"created_at": LONG_AGO, "data": {"due_date": FUTURE}},
        "#3135: a row reused for the next occurrence keeps its created_at; its due date decides",
    ),
    Case(
        "retimed_into_the_future",
        False,
        {"data": {"due_date": FUTURE}},
        "#3135: a task retimed by dormancy 'minimal' is not overdue",
    ),
    Case(
        "fresh_row_old_due",
        True,
        {"created_at": RECENT, "data": {"due_date": LONG_AGO}},
        "the age of the row says nothing; an occurrence due long ago is overdue",
    ),
    Case(
        "due_half_a_second_after_the_cutoff_with_a_fraction",
        False,
        {"data": {"due_date": "2026-11-20T12:00:00.500000Z"}},
        "instants, not ICU string order ('.' sorts before '+')",
    ),
    Case(
        "due_half_a_second_before_the_cutoff",
        True,
        {"data": {"due_date": "2026-11-20T11:59:59.5Z"}},
        "instants, not ICU string order",
    ),
    Case(
        "due_with_an_offset_before_the_cutoff",
        True,
        {"data": {"due_date": "2026-11-20T13:30:00+02:00"}},
        "11:30 UTC — later as text, earlier as an instant",
    ),
    Case(
        "due_without_an_offset_is_utc",
        False,
        {"data": {"due_date": "2026-11-20T12:30:00"}},
        "no offset reads as UTC on both sides: 12:30 UTC is after the cutoff",
    ),
    Case("no_due_date", False, {"data": {"plant_key": "p"}}, "no announced due date: not proven overdue"),
    Case("due_date_null", False, {"data": {"due_date": None}}, "no announced due date: not proven overdue"),
    Case("due_date_empty", False, {"data": {"due_date": ""}}, "no announced due date: not proven overdue"),
    Case("due_date_unreadable", False, {"data": {"due_date": "not-a-date"}}, "unreadable: not proven overdue"),
    Case(
        "due_date_a_number",
        False,
        {"data": {"due_date": 1700000000000}},
        "only an ISO string is a due date (DATE_TIMESTAMP would read a number as epoch ms)",
    ),
    Case(
        "escalation_row",
        False,
        {"notification_type": "care.watering.escalation", "parent_notification_key": "x"},
        "#3135: an escalation is never escalated itself",
    ),
    Case(
        "another_type_sharing_the_prefix",
        False,
        {"notification_type": "care.watering.due"},
        "the type is matched exactly, not as a prefix",
    ),
    Case("acted", False, {"acted_at": RECENT}, "the user dealt with it"),
    Case("read_but_not_acted", True, {"read_at": RECENT}, "reading is not watering"),
    Case("another_tenant", False, {"tenant_key": OTHER_TENANT}, "tenant-scoped"),
    Case("another_level", False, {"escalation_level": LEVEL + 1}, "exactly the queried level"),
)


def document(case: Case) -> dict:
    """The stored document of *case*."""
    doc = base_document(case.name)
    doc.update(case.doc)
    return doc
