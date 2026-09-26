"""#1799 class guard — every year shift in ``app/`` survives 29 February.

**The class.** ``value.replace(year=y)`` raises ``ValueError`` when ``value`` is
29 February and ``y`` is not a leap year. The crop-rotation history computed its
cutoff that way (``datetime.now(UTC).replace(year=now.year - years)``), so every
rotation check failed with a 500 on one day in four years — the one day no test
run pins the clock to. The retention service had already handled it locally
(``try … except ValueError``); a site-local repair per call is the drift this
guard closes: :func:`app.common.datetimes.replace_year` is the one place.

**The rule.** In ``app/`` outside ``common/datetimes.py``:

* a call ``<anything>.replace(...)`` with a ``year=`` keyword is a finding;
* a ``date(...)``/``datetime(...)`` construction whose month and day are
  ``v.month`` and ``v.day`` of one value ``v`` while its year is **not**
  ``v.year`` is a finding — the same shift, spelled as a constructor.

Spellings this does NOT match
-----------------------------

* ``date(y, m, d)`` from separately computed ``m``/``d`` variables (the month
  and day are not visibly taken from one value);
* ``value - timedelta(days=365 * n)`` — does not raise, but is a different
  defect (a year is not 365 days); not in this class;
* ``relativedelta(years=n)`` — handles 29 February itself (clips to the 28th).
"""

from __future__ import annotations

import ast
from datetime import date, datetime
from pathlib import Path

import pytest

from app.common.datetimes import replace_year
from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"
_HOME = "common/datetimes.py"


def _attr_of(node: ast.AST) -> tuple[str, str] | None:
    """``("v", "month")`` for ``v.month`` where ``v`` is a plain name or dotted path."""
    if isinstance(node, ast.Attribute):
        return ast.unparse(node.value), node.attr
    return None


def scan_source(source: str, rel_path: str) -> list[str]:
    findings: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "replace":
            if any(k.arg == "year" for k in node.keywords):
                findings.append(f"{rel_path}:{node.lineno}: .replace(year=...) — use replace_year()")
            continue
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if name not in {"date", "datetime"} or len(node.args) < 3:
            continue
        year, month, day = (_attr_of(a) for a in node.args[:3])
        same_value = month and day and month[1] == "month" and day[1] == "day" and month[0] == day[0]
        if same_value and year != (month[0], "year"):
            findings.append(f"{rel_path}:{node.lineno}: {name}(…, {month[0]}.month, …) — use replace_year()")
    return findings


def test_no_year_shift_in_app_bypasses_replace_year() -> None:
    findings = []
    for path in sorted(_APP.rglob("*.py")):
        rel = str(path.relative_to(_APP))
        if rel != _HOME:
            findings += scan_source(path.read_text(encoding="utf-8"), rel)

    assert findings == [], (
        "A year shift raises ValueError on 29 February in a non-leap target year (#1799). Route it through "
        "app.common.datetimes.replace_year.\n  " + "\n  ".join(findings)
    )


@pytest.mark.parametrize(
    ("value", "year", "expected"),
    [
        (date(2028, 2, 29), 2025, date(2025, 2, 28)),
        (date(2028, 2, 29), 2024, date(2024, 2, 29)),
        (date(2026, 9, 26), 2023, date(2023, 9, 26)),
        (datetime(2028, 2, 29, 13, 5, 7, 11), 2027, datetime(2027, 2, 28, 13, 5, 7, 11)),
    ],
)
def test_replace_year_lands_29_february_on_the_28th(value: date, year: int, expected: date) -> None:
    assert replace_year(value, year) == expected
    assert type(replace_year(value, year)) is type(value)


# ── falsification: the detector sees both spellings, and only them ────────────


def test_both_spellings_are_findings() -> None:
    source = """
def f(now, d, years):
    a = now.replace(year=now.year - years)
    b = date(d.year - 1, d.month, d.day)
    c = datetime(years, now.month, now.day, tzinfo=UTC)
"""
    assert len(scan_source(source, "probe.py")) == 3


def test_non_shifts_are_no_findings() -> None:
    source = """
def f(now, today, s):
    a = now.replace(microsecond=0)
    b = datetime(today.year, today.month, today.day, tzinfo=UTC)
    c = s.replace("a", "b")
    d = date(2025, 5, 1)
"""
    assert scan_source(source, "probe.py") == []
