"""Datetime helpers ensuring timezone-aware UTC comparisons.

These helpers exist so safety-critical gates (Karenz, resistance, HST) never
mix timezone-aware and naive datetimes, which would raise a ``TypeError`` and
surface as an HTTP 500 instead of the intended business-level HTTP 422.
"""

from datetime import UTC, datetime


def now_utc() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


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
