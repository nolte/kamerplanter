#!/usr/bin/env python3
"""Refuse a bare ``date.today()`` in the backend application code.

Runs as a repo-local pre-commit hook in the required ``static`` lane, and can be
invoked directly::

    python3 scripts/check_utc_calendar_day.py
    python3 scripts/check_utc_calendar_day.py --list   # name every call site
    python3 scripts/check_utc_calendar_day.py --json   # machine-readable

**What it enforces.** ``spec/style-guides/BACKEND.md`` §12a: a calendar day that
is compared against a stored timestamp comes from
:func:`app.common.datetimes.today_utc`, never from the local server date. The
rule already existed, in prose; nothing measured it, so the sweep it demanded had
to be repeated three times (#772, #812, #858) and 18 call sites survived the
second one.

The defect this closes is invisible by construction. On a UTC container
``date.today()`` and ``datetime.now(UTC).date()` return the same value, so the
mistake looks correct in review, in local development on a UTC box, and in CI —
which runs on UTC. It surfaces only in production on a host whose zone sits on
the far side of midnight, and only for part of the day.

**Why zero, and not a numeric ratchet.** ``check_schema_examples.py`` carries a
recorded ceiling because its debt is real and cannot be paid off in one change.
(``check_bdd_traceability.py`` carried two until #839 paid its debt off and
dropped them — a baseline is a holding position, not an answer.) This one has no
debt left: #858 converted
every site, so the honest baseline is zero, and a ratchet constant pinned at zero
is dead machinery pretending to be a policy. The escape hatch is per-site instead
of numeric, which is strictly more informative than a number: a site that
genuinely wants the local clock says so, in place, with a reason a reviewer can
argue with.

**The escape hatch.** A call site may keep the local date by carrying a
justification marker on the same line or on the line directly above::

    # local-clock: the log file name follows the operator's wall clock
    stamp = date.today()

    stamp = date.today()  # local-clock: operator wall clock, never persisted

The reason text is mandatory and must be more than a word — ``# local-clock:``
alone does not satisfy the check, so the hatch cannot be used as a silencer. §12a
is the standard the reason is measured against: the local date is admissible only
where the result is compared with **neither** a persisted timestamp **nor**
another calendar value.

**What it detects.** ``date.today()`` under every spelling this codebase can
produce, resolved through the module's own imports rather than by bare name:

* ``from datetime import date`` → ``date.today()``
* ``from datetime import date as _date`` → ``_date.today()`` (the calendar
  router used exactly this alias, inside a function body)
* ``import datetime`` / ``import datetime as dt`` → ``datetime.date.today()``
* the same imports written inside a function, which is this codebase's habit for
  breaking import cycles.

A name that is not bound to ``datetime.date`` in the module is not flagged, so an
unrelated ``self.clock.today()`` or a domain object's ``today()`` stays quiet.
The trade is one-directional and deliberate: an exotic spelling
(``getattr(date, "today")()``, a re-export through a third module) slips through,
but nothing that is *not* ``datetime.date.today()`` is ever reported. A checker
that cried wolf would be switched off within a week, and then it would guard
nothing at all.

Scope is the application/package source of the backend and the three Python side
services — ``src/backend/app/``, ``src/knowledge-service/app/``,
``src/inference-service/app/`` and ``src/libs/kp_vectordb/kp_vectordb/`` (see
``DEFAULT_SCAN_ROOTS``). The side services were added in #1058, once their pytest
suites ran in CI (``side-services.yml``); before that a gate over them would have
guarded code no test exercised. Every ``tests/`` tree is excluded on purpose:
tests must be able to read the local clock — ``tests/support/timezones.py``
compares it against UTC, which is the entire mechanism that makes the divergence
testable — which is why the scan roots are the app/package dirs, never their
parents.

Standard library only, no application import, no running stack: the ``static`` CI
job is Python-only, and importing the application to answer a question that is
answerable from its source text would drag in settings and database clients.

Traces to issue #858 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Where the application code that persists timestamps lives, relative to the
#: repository root. Each entry is an app/package directory, NOT its parent: the
#: parent also holds a ``tests/`` tree, and tests are excluded on purpose (they
#: read the local clock to make the divergence testable — see the module
#: docstring). The backend was the original and only scope; the three Python
#: side services joined in #1058, once their pytest suites began running in CI
#: (``side-services.yml``), so a calendar-day regression in them is now caught by
#: a running test rather than only asserted by this gate. The order does matter —
#: the gate was extended *after* the suites run, not before.
DEFAULT_SCAN_ROOTS = (
    "src/backend/app",
    "src/knowledge-service/app",
    "src/inference-service/app",
    "src/libs/kp_vectordb/kp_vectordb",
)

#: The marker that exempts a call site, plus the minimum length of the reason
#: that must follow it. A bare marker is not an exemption: the point of the
#: hatch is the reason, not the token.
JUSTIFICATION_MARKER = "# local-clock:"
MIN_JUSTIFICATION_CHARS = 12

#: The replacement the failure message names, so the fix does not need a lookup.
REPLACEMENT = "app.common.datetimes.today_utc()"

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2


class CalendarDayCheckError(Exception):
    """A usage or environment problem — not a finding about the code."""


@dataclass(frozen=True)
class CallSite:
    """One ``date.today()`` call found in the scanned tree."""

    path: Path
    line: int
    expression: str
    justification: str | None

    @property
    def justified(self) -> bool:
        return self.justification is not None

    def relative_to(self, root: Path) -> str:
        try:
            return str(self.path.relative_to(root))
        except ValueError:
            return str(self.path)


class _DateTodayVisitor(ast.NodeVisitor):
    """Collect ``date.today()`` calls, resolving the local ``datetime`` imports.

    Two binding sets are tracked because both spellings occur in this codebase:

    * ``date_names`` — names bound directly to ``datetime.date``
      (``from datetime import date``, ``... import date as _date``);
    * ``module_names`` — names bound to the ``datetime`` *module*
      (``import datetime``, ``import datetime as dt``), which reach the class as
      ``<module>.date``.

    Imports are collected wherever they appear, including inside a function body:
    the calendar router bound ``_date`` in two function bodies, and a visitor
    that only looked at module level would have missed both. Because the visit
    order is source order, an import written below its use would not register in
    time — that shape does not occur, and could not run anyway.
    """

    def __init__(self) -> None:
        self.date_names: set[str] = set()
        self.module_names: set[str] = set()
        self.hits: list[tuple[int, str]] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "datetime":
                self.module_names.add(alias.asname or "datetime")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "datetime":
            for alias in node.names:
                if alias.name == "date":
                    self.date_names.add(alias.asname or "date")
                elif alias.name == "datetime":
                    # ``from datetime import datetime`` binds the *class*, whose
                    # ``.today()`` is a different (also naive) call. Out of scope
                    # here: §12a and #858 are about the calendar day.
                    continue
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "today" and self._is_date_class(func.value):
            self.hits.append((func.lineno, f"{_render(func.value)}.today()"))
        self.generic_visit(node)

    def _is_date_class(self, node: ast.expr) -> bool:
        # ``date.today()`` / ``_date.today()``
        if isinstance(node, ast.Name):
            return node.id in self.date_names
        # ``datetime.date.today()`` / ``dt.date.today()``
        if isinstance(node, ast.Attribute) and node.attr == "date":
            return isinstance(node.value, ast.Name) and node.value.id in self.module_names
        return False


def _render(node: ast.expr) -> str:
    """A readable rendering of the receiver, for the report."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_render(node.value)}.{node.attr}"
    return "<expr>"


def justification_for(lines: list[str], line: int) -> str | None:
    """Return the reason exempting the call on *line*, or ``None``.

    Accepted on the call's own line (trailing comment) or on the line directly
    above it (own-line comment), because a long call does not always leave room
    for a trailing comment within the line limit.
    """
    candidates = [lines[line - 1]]
    if line >= 2:
        candidates.append(lines[line - 2].strip())
    for candidate in candidates:
        marker = candidate.find(JUSTIFICATION_MARKER)
        if marker == -1:
            continue
        reason = candidate[marker + len(JUSTIFICATION_MARKER) :].strip()
        if len(reason) >= MIN_JUSTIFICATION_CHARS:
            return reason
    return None


def scan_file(path: Path) -> list[CallSite]:
    """Find every ``date.today()`` call in one source file."""
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CalendarDayCheckError(f"cannot read {path}: {exc}") from exc
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise CalendarDayCheckError(f"cannot parse {path}: {exc}") from exc

    visitor = _DateTodayVisitor()
    visitor.visit(tree)
    if not visitor.hits:
        return []

    lines = source.splitlines()
    return [
        CallSite(path=path, line=line, expression=expression, justification=justification_for(lines, line))
        for line, expression in sorted(visitor.hits)
    ]


def iter_sources(roots: list[Path]) -> list[Path]:
    """Every ``.py`` file below *roots*, sorted for a stable report."""
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(sorted(root.rglob("*.py")))
        else:
            raise CalendarDayCheckError(f"scan root does not exist: {root}")
    return files


def collect(roots: list[Path]) -> list[CallSite]:
    """Every ``date.today()`` call site below *roots*, justified or not."""
    sites: list[CallSite] = []
    for path in iter_sources(roots):
        sites.extend(scan_file(path))
    return sites


def _resolve(raw: list[str]) -> list[Path]:
    return [(REPO_ROOT / entry) if not Path(entry).is_absolute() else Path(entry) for entry in raw]


def report(sites: list[CallSite], *, list_all: bool, as_json: bool) -> int:
    """Print the outcome and return the process exit code."""
    unjustified = [site for site in sites if not site.justified]
    justified = [site for site in sites if site.justified]

    if as_json:
        print(
            json.dumps(
                {
                    "call_sites": len(sites),
                    "justified": [
                        {
                            "file": site.relative_to(REPO_ROOT),
                            "line": site.line,
                            "expression": site.expression,
                            "reason": site.justification,
                        }
                        for site in justified
                    ],
                    "unjustified": [
                        {
                            "file": site.relative_to(REPO_ROOT),
                            "line": site.line,
                            "expression": site.expression,
                        }
                        for site in unjustified
                    ],
                },
                indent=2,
            )
        )
        return EXIT_DEFECTS if unjustified else EXIT_OK

    if unjustified:
        print(f"check_utc_calendar_day: {len(unjustified)} local-clock call site(s) in the scanned app code\n")
        for site in unjustified:
            print(f"  {site.relative_to(REPO_ROOT)}:{site.line}: {site.expression}")
        print(
            f"\n{REPLACEMENT} returns the calendar day in UTC, which is the clock every\n"
            "timestamp this application persists is written on (BACKEND.md §12a).\n"
            "\n"
            "If the local server date really is correct at one of these sites — the result is\n"
            "compared with neither a stored timestamp nor another calendar value — say so where\n"
            f"it stands, on the same line or the one above:\n"
            f"\n"
            f"    {JUSTIFICATION_MARKER} <why the local clock is right here>\n"
            "\n"
            f"The reason is mandatory and must be at least {MIN_JUSTIFICATION_CHARS} characters."
        )
        return EXIT_DEFECTS

    if justified:
        print(f"check_utc_calendar_day: OK — {len(justified)} justified local-clock call site(s):")
        for site in justified:
            print(f"  {site.relative_to(REPO_ROOT)}:{site.line}: {site.justification}")
        return EXIT_OK

    if list_all:
        print("check_utc_calendar_day: OK — no date.today() call site at all.")
    else:
        print("check_utc_calendar_day: OK — every calendar day in the scanned app code comes from UTC.")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Run the check.

    Returns:
        0 when every call site is UTC or carries a justification, 1 when at least
        one bare ``date.today()`` remains, 2 on a usage or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_utc_calendar_day.py",
        description=(
            "Refuse a bare date.today() in the backend application code (BACKEND.md §12a). "
            f"A call site may keep the local clock by carrying a '{JUSTIFICATION_MARKER} <reason>' "
            "comment on its own line or the line above."
        ),
    )
    parser.add_argument(
        "--scan-root",
        action="append",
        metavar="PATH",
        help=f"directory or .py file to scan (repeatable; default: {', '.join(DEFAULT_SCAN_ROOTS)})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_all",
        help="report even when nothing was found at all",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the findings as JSON instead of the human report",
    )
    args = parser.parse_args(argv)

    try:
        sites = collect(_resolve(args.scan_root or list(DEFAULT_SCAN_ROOTS)))
    except CalendarDayCheckError as exc:
        print(f"check_utc_calendar_day: {exc}", file=sys.stderr)
        return EXIT_USAGE

    return report(sites, list_all=args.list_all, as_json=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
