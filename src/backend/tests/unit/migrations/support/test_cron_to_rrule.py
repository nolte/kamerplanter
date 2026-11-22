"""The lossless cron → RRULE subset of migration M5 (REQ-053 GP-ACC-038, #2325).

Every conversion is checked twice: the exact RRULE text (the migration writes it
verbatim) and that ``dateutil`` parses it and yields the same next occurrence the
cron line means — so a conversion the parser would reject or shift cannot pass.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from dateutil.rrule import rrulestr

from app.migrations.support.cron_to_rrule import cron_to_rrule, looks_like_cron

_AFTER = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)  # a Monday, noon


@pytest.mark.parametrize(
    ("cron", "rrule", "next_at"),
    [
        ("0 8 * * 1", "FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0", datetime(2026, 1, 12, 8, 0, tzinfo=UTC)),
        ("0 9 * * *", "FREQ=DAILY;BYHOUR=9;BYMINUTE=0", datetime(2026, 1, 6, 9, 0, tzinfo=UTC)),
        ("30 6 1 * *", "FREQ=MONTHLY;BYMONTHDAY=1;BYHOUR=6;BYMINUTE=30", datetime(2026, 2, 1, 6, 30, tzinfo=UTC)),
        ("0 7 1 6 *", "FREQ=YEARLY;BYMONTH=6;BYMONTHDAY=1;BYHOUR=7;BYMINUTE=0", datetime(2026, 6, 1, 7, 0, tzinfo=UTC)),
        ("0 8 * * MON,WED", "FREQ=WEEKLY;BYDAY=MO,WE;BYHOUR=8;BYMINUTE=0", datetime(2026, 1, 7, 8, 0, tzinfo=UTC)),
        ("0 8 * * 1-5", "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=8;BYMINUTE=0", datetime(2026, 1, 6, 8, 0, tzinfo=UTC)),
        ("5 4 * * 7", "FREQ=WEEKLY;BYDAY=SU;BYHOUR=4;BYMINUTE=5", datetime(2026, 1, 11, 4, 5, tzinfo=UTC)),
        ("0 8 * 3,4 *", "FREQ=DAILY;BYMONTH=3,4;BYHOUR=8;BYMINUTE=0", datetime(2026, 3, 1, 8, 0, tzinfo=UTC)),
        ("0 8 * 6 SAT", "FREQ=WEEKLY;BYMONTH=6;BYDAY=SA;BYHOUR=8;BYMINUTE=0", datetime(2026, 6, 6, 8, 0, tzinfo=UTC)),
        (
            "15 18 1,15 * *",
            "FREQ=MONTHLY;BYMONTHDAY=1,15;BYHOUR=18;BYMINUTE=15",
            datetime(2026, 1, 15, 18, 15, tzinfo=UTC),
        ),
    ],
)
def test_the_subset_converts_losslessly(cron: str, rrule: str, next_at: datetime) -> None:
    assert cron_to_rrule(cron) == rrule
    assert rrulestr(rrule, dtstart=_AFTER).after(_AFTER, inc=False) == next_at


def test_a_month_filter_keeps_every_day_of_the_month() -> None:
    """``0 8 * 3 *`` is every day of March — a YEARLY rule would have collapsed it to one day."""
    rule = rrulestr(cron_to_rrule("0 8 * 3 *"), dtstart=_AFTER)
    first = rule.after(_AFTER, inc=False)
    assert (first, rule.after(first, inc=False)) == (
        datetime(2026, 3, 1, 8, 0, tzinfo=UTC),
        datetime(2026, 3, 2, 8, 0, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    "cron",
    [
        "*/15 * * * *",  # step: sub-daily
        "0 */2 * * *",  # step in hours
        "* 8 * * *",  # every minute of an hour
        "0 8 1 * 1",  # day-of-month AND weekday: cron ORs, RRULE would AND
        "0 8 32 * *",  # out of range
        "0 25 * * *",
        "0 8 * 13 *",
        "0 8 * * 8",
        "0 8 * * MOO",
        "0 8 * *",  # four fields
        "FREQ=DAILY",  # already an RRULE, not cron
        "weekly",
        "",
    ],
)
def test_everything_else_is_refused_not_guessed(cron: str) -> None:
    assert cron_to_rrule(cron) is None


def test_looks_like_cron_is_the_five_field_shape() -> None:
    assert looks_like_cron("0 8 * * 1") is True
    assert looks_like_cron("FREQ=WEEKLY;BYDAY=MO") is False
    assert looks_like_cron("every monday") is False
