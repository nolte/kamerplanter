"""The clock contract: a calendar day compared against a stored timestamp is UTC.

Every timestamp this application persists is UTC, so resolving "today" from the
*local* server date silently disagrees with them for part of every day on any
host that is not itself on UTC. On a UTC container the two are identical — which
is why the mistake keeps passing review (#772, #812).

These tests force a real non-UTC process timezone, because that is the only way
the divergence appears at all: freezegun's ``tz_offset`` moves ``date.today()``
and ``datetime.now(UTC)`` together, so the gap it is supposed to expose closes.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from app.common.datetimes import today_utc
from tests.support.timezones import local_timezone, timezone_on_another_calendar_day


def test_today_utc_ignores_the_local_server_date() -> None:
    """The helper answers in UTC even when the process sits on another day."""
    tz = timezone_on_another_calendar_day()

    with local_timezone(tz):
        # Precondition of the test itself: this TZ really is across the boundary,
        # otherwise the assertion below would pass for the wrong reason.
        assert date.today() != datetime.now(UTC).date()  # noqa: DTZ011 - deliberate

        assert today_utc() == datetime.now(UTC).date()
        assert today_utc() != date.today()  # noqa: DTZ011 - deliberate


def test_today_utc_matches_the_now_utc_helper() -> None:
    """`today_utc()` and `now_utc()` cannot disagree about the day.

    The dashboard defect (#812) was exactly this disagreement: counters resolved
    from `datetime.now(UTC)` sat next to a per-plant flag resolved from
    `date.today()`, so the alert dot could mean a different day than the number
    above it.
    """
    from app.common.datetimes import now_utc

    tz = timezone_on_another_calendar_day()
    with local_timezone(tz):
        assert today_utc() == now_utc().date()


def test_the_harness_restores_the_previous_timezone() -> None:
    """A leaked `TZ` would silently re-date every later test in the process."""
    import os

    before = os.environ.get("TZ")
    with local_timezone("XXX-14"):
        pass
    assert os.environ.get("TZ") == before
