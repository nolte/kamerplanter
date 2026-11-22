"""Cron (5-field) → RFC 5545 RRULE for migration M5 (REQ-053 GP-ACC-038, ADR-008, #2325).

Pure functions, no I/O. Only the subset a cron string can express *without loss* as
an RRULE is converted; everything else returns ``None`` and the migration lists the
row instead of guessing (E-10 spirit: no invented cadence). Converted today:

* ``m h * * *``      → ``FREQ=DAILY;BYHOUR=h;BYMINUTE=m``
* ``m h * * dow``    → ``FREQ=WEEKLY;BYDAY=…;BYHOUR=h;BYMINUTE=m`` (GP-ACC-038:
  ``0 8 * * 1`` → ``FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0``)
* ``m h dom * *``    → ``FREQ=MONTHLY;BYMONTHDAY=…;BYHOUR=h;BYMINUTE=m``
* ``m h dom mon *``  → ``FREQ=YEARLY;BYMONTH=…;BYMONTHDAY=…;BYHOUR=h;BYMINUTE=m``
* ``m h * mon *``    → ``FREQ=DAILY;BYMONTH=…;BYHOUR=h;BYMINUTE=m`` (every day of those months)
* ``m h * mon dow``  → ``FREQ=WEEKLY;BYMONTH=…;BYDAY=…;BYHOUR=h;BYMINUTE=m``

Lists (``1,15``), ranges (``1-5``) and weekday names (``MON``) are accepted in the
day/month fields; ``minute`` and ``hour`` must be single integers. Refused: steps
(``*/15`` — sub-daily or every-n-days cadences), a ``*`` minute or hour, and a cron
line that sets **both** day-of-month and day-of-week (cron ORs them, RRULE ANDs
them — no faithful rendering).
"""

from __future__ import annotations

import re

_WEEKDAYS = ("SU", "MO", "TU", "WE", "TH", "FR", "SA")
_WEEKDAY_NAMES = dict(zip(("SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"), _WEEKDAYS, strict=True))
_MONTHS = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
_MONTH_NAMES = {name: i + 1 for i, name in enumerate(_MONTHS)}
_FIVE_FIELDS = re.compile(r"^\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$")


def looks_like_cron(rule: str) -> bool:
    """Five whitespace-separated fields and no ``FREQ=`` — the shape of a legacy cron string."""
    return bool(_FIVE_FIELDS.match(rule)) and "FREQ=" not in rule.upper()


def _single_int(field: str, low: int, high: int) -> int | None:
    if not (field.isascii() and field.isdigit()):
        return None
    value = int(field)
    return value if low <= value <= high else None


def _int_list(field: str, low: int, high: int, names: dict[str, int] | None = None) -> list[int] | None:
    """``*`` → ``[]``; lists and ranges → sorted ints; steps or out-of-range → ``None``."""
    if field == "*":
        return []
    values: set[int] = set()
    part: str
    for part in field.upper().split(","):
        if "/" in part or not part:
            return None
        lo: str
        hi: str
        lo, _, hi = part.partition("-")
        lo_i = names.get(lo) if names and lo in names else (int(lo) if lo.isascii() and lo.isdigit() else None)
        if lo_i is None:
            return None
        if hi:
            hi_i = names.get(hi) if names and hi in names else (int(hi) if hi.isascii() and hi.isdigit() else None)
            if hi_i is None or hi_i < lo_i:
                return None
        else:
            hi_i = lo_i
        for value in range(lo_i, hi_i + 1):
            if not low <= value <= high:
                return None
            values.add(value)
    return sorted(values)


def _weekdays(field: str) -> list[str] | None:
    numbers = _int_list(field, 0, 7, names={name: _WEEKDAYS.index(code) for name, code in _WEEKDAY_NAMES.items()})
    if numbers is None:
        return None
    codes = [_WEEKDAYS[n % 7] for n in numbers]  # cron: 0 and 7 are both Sunday
    return sorted(set(codes), key=_WEEKDAYS.index)


def cron_to_rrule(expr: str) -> str | None:
    """The lossless RRULE for a 5-field cron expression, or ``None`` when there is none."""
    match = _FIVE_FIELDS.match(expr or "")
    if not match:
        return None
    minute_f, hour_f, dom_f, month_f, dow_f = match.groups()
    minute = _single_int(minute_f, 0, 59)
    hour = _single_int(hour_f, 0, 23)
    days = _int_list(dom_f, 1, 31)
    months = _int_list(month_f, 1, 12, names=_MONTH_NAMES)
    weekdays = _weekdays(dow_f)
    if minute is None or hour is None or days is None or months is None or weekdays is None:
        return None
    if days and weekdays:
        return None  # cron ORs the two; an RRULE would AND them

    # A month list without a day list is a *filter* on a daily/weekly cadence — never
    # FREQ=YEARLY, whose missing BYMONTHDAY would default to dtstart's day and lose
    # "every day in March" (measured in the support test).
    if weekdays:
        freq = "WEEKLY"
    elif days:
        freq = "YEARLY" if months else "MONTHLY"
    else:
        freq = "DAILY"
    parts: list[str] = [f"FREQ={freq}"]
    if months:
        parts.append(f"BYMONTH={_csv(months)}")
    if days:
        parts.append(f"BYMONTHDAY={_csv(days)}")
    if weekdays:
        parts.append(f"BYDAY={','.join(weekdays)}")
    parts.extend((f"BYHOUR={hour}", f"BYMINUTE={minute}"))
    return ";".join(parts)


def _csv(values: list[int]) -> str:
    return ",".join(str(v) for v in values)
