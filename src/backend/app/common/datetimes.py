"""Datetime helpers ensuring timezone-aware UTC comparisons.

These helpers exist so safety-critical gates (Karenz, resistance, HST) never
mix timezone-aware and naive datetimes, which would raise a ``TypeError`` and
surface as an HTTP 500 instead of the intended business-level HTTP 422.
"""

from datetime import UTC, date, datetime


def now_utc() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def today_utc() -> date:
    """Return today's calendar date **in UTC**, never the local server date.

    Use this anywhere a calendar day is compared against a stored timestamp.
    Every timestamp this application persists is UTC, so ``date.today()`` — the
    *local* server date — silently disagrees with them for part of every day on
    any host that is not itself on UTC. On a UTC container the two are
    identical, which is exactly why the mistake survives review (#812, #772).

    The failure is not theoretical and not confined to one layer:

    * a dashboard response mixed two clocks — its counters came from
      ``datetime.now(UTC)`` while the per-plant "has an open task" flag came
      from a ``date.today()`` query, so the alert dot could mean a different day
      than the number above it;
    * the care-reminder producer stamped a *local* calendar date wearing a UTC
      label, while the dedup rule that reads it back had already moved to UTC —
      so producer and deduplicator ran on different days.

    Testing note: ``freezegun`` cannot express this divergence. Its ``tz_offset``
    shifts ``date.today()`` and ``datetime.now(UTC)`` by the same amount, so the
    gap never appears. The divergence is a property of the *process* timezone;
    tests must set ``TZ`` + ``time.tzset()`` for real. The shared harness in
    ``tests/support/timezones.py`` does that and picks a zone guaranteed to sit
    on the far side of midnight at any hour.
    """
    return datetime.now(UTC).date()


def ensure_aware_utc(value: datetime | str | None) -> datetime | None:
    """Normalize a datetime or ISO string to timezone-aware UTC.

    - ``None`` -> ``None``
    - ISO string -> parsed; naive values are interpreted as UTC
    - naive datetime -> interpreted as UTC (legacy data written before the
      persistence layer enforced offsets)
    - aware datetime -> converted to UTC

    Args:
        value: A datetime, an ISO-8601 string, or ``None``.

    Returns:
        A timezone-aware UTC datetime, or ``None`` if the input was ``None``.
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def replace_year[T: (date, datetime)](value: T, year: int) -> T:
    """Return ``value`` moved to ``year``; 29 February lands on 28 February.

    ``value.replace(year=year)`` raises ``ValueError`` when ``value`` is
    29 February and ``year`` is not a leap year — once every four years, on
    exactly one day, which is why the crash survives every test run that does
    not pin the clock to that day (#1799). The earlier day is chosen, never
    1 March: a cutoff "N years back" that lands a day *earlier* keeps one more
    day of history, never one fewer, and a seasonal date (a frost date) stays in
    the month it was entered for.

    Every year shift in ``app/`` goes through here; the guard
    ``tests/unit/guards/test_aql_timestamp_comparisons_are_instants.py`` refuses
    a bare ``.replace(year=...)`` anywhere else.
    """
    try:
        return value.replace(year=year)
    except ValueError:
        if value.month == 2 and value.day == 29:
            return value.replace(year=year, day=28)
        raise
