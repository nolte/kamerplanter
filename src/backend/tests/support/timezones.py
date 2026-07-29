"""Force a real, non-UTC process timezone so local-vs-UTC drift becomes visible.

Extracted from ``tests/unit/data_access/arango/test_find_open_care_task_repo.py``
(#772) so the clock-contract tests of #812 reuse the harness instead of
re-deriving it — the reasoning below is subtle enough that a second copy would
drift.

**freezegun cannot express this scenario.** Its ``tz_offset`` shifts
``date.today()`` *and* ``datetime.now(UTC)`` by the same amount, so the
divergence the bug lives in never appears. The divergence is a property of the
*process* timezone, so it is set for real via ``TZ`` + ``time.tzset()`` and the
wall clock supplies the instant.
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime


@contextmanager
def local_timezone(tz: str) -> Iterator[None]:
    """Run the block with ``TZ`` set to *tz*, restoring the previous value."""
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


def timezone_on_another_calendar_day() -> str:
    """A non-UTC ``TZ`` whose local calendar day differs from the UTC one *now*.

    POSIX ``TZ`` offsets are sign-inverted, so ``"XXX-14"`` is UTC+14 (shifts the
    day forward whenever the UTC hour is >= 10) and ``"XXX+12"`` is UTC-12
    (shifts it backward whenever the UTC hour is < 12). The two ranges overlap,
    so one of them always lands on the far side of midnight — the test is
    date-boundary-crossing at every hour of the day, with hours of margin, and
    never flaky.

    Plain offset strings are used instead of named zones so the harness does not
    depend on a tzdata database being installed in the test image.
    """
    for tz in ("XXX-14", "XXX+12"):
        with local_timezone(tz):
            if date.today() != datetime.now(UTC).date():  # noqa: DTZ011 - the point of the check
                return tz
    raise AssertionError("no candidate TZ put the local calendar day off the UTC one")
