"""``utc_range`` / ``as_utc``: one reading of a ``from`` / ``to`` query for the care log and the bed history.

A naive bound next to an aware one used to raise ``TypeError`` inside the route (a 500, REQ-053 WP 4.5 review).
"""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.common.datetimes import as_utc, utc_range
from app.common.exceptions import ValidationError


def test_a_naive_instant_is_read_as_utc_and_an_aware_one_is_kept() -> None:
    assert as_utc(datetime(2026, 6, 1, 8)) == datetime(2026, 6, 1, 8, tzinfo=UTC)
    plus_two = datetime(2026, 6, 1, 8, tzinfo=timezone(timedelta(hours=2)))
    assert as_utc(plus_two) is plus_two
    assert as_utc(None) is None


def test_a_naive_and_an_aware_bound_compare_without_a_type_error() -> None:
    start, end = utc_range(datetime(2026, 6, 1), datetime(2026, 6, 2, tzinfo=UTC))
    assert start == datetime(2026, 6, 1, tzinfo=UTC) and end == datetime(2026, 6, 2, tzinfo=UTC)


def test_an_open_end_is_allowed() -> None:
    assert utc_range(None, None) == (None, None)
    assert utc_range(datetime(2026, 6, 1), None)[1] is None


def test_to_before_from_is_a_validation_error() -> None:
    with pytest.raises(ValidationError):
        utc_range(datetime(2026, 6, 2), datetime(2026, 6, 1, tzinfo=UTC))


def test_equal_bounds_are_one_instant_not_an_error() -> None:
    instant = datetime(2026, 6, 1, tzinfo=UTC)
    assert utc_range(instant, instant) == (instant, instant)
