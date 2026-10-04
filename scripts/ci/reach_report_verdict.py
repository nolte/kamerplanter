#!/usr/bin/env python3
"""Turn a capability-reach report into an honest job verdict for ``reach-audit.yml``.

The runner (``reach_audit.py`` of the ``capability-reach-audit`` skill in
nolte/claude-shared) answers with an exit code that covers only the *change
detection* half of its report: ``4`` for a weakened probe, an invalid probe or
manifest, an approval mismatch or a contradiction, ``3`` for an empty probe set.
It exits ``0`` for a report in which a probe measured ``not reached`` and for a
report in which an environment target failed to come up, because both are
*classes in the report*, not findings (``references/runner-exit-codes.md``,
measured 2026-10-04: a T0/T1 run with 24 of 26 entries not probed exits 0).

A scheduled job that only looked at that exit code would stay green over exactly
the defect the audit exists to find. This script reads the report the runner
wrote and fails the job for the cases the exit code does not carry:

* a probe classed ``not reached`` — the capability measured zero or less than
  its declared scope;
* a probe classed ``not probed`` whose reason is NOT one of the documented
  coverage facts below — an environment target that failed, an observation step
  that failed, hung or printed nothing, an unapproved or uncommitted probe.
  That is infrastructure or a defect, never a measurement, and silence about it
  is the failure mode this job is written against. It FAILS CLOSED: a reason this
  script does not know fails the job, so a new runner reason cannot hide.

It does NOT fail for coverage facts, which it surfaces as warnings instead,
because the skill states them as such (SKILL.md, "Stale is not an error"):

* ``declaration changed since derivation`` — a stale probe, withheld until the
  operator re-confirms or re-derives it;
* ``tier T2 not requested`` — only when the run did not ask for T2;
* ``not constructible: <code>`` — a manifest entry no probe could be built for.

``partially reached`` is a warning, not a failure: it is a measured ratio below
the declared scope, shown with its numbers, and a transient (one run still in
flight, one cancelled) must not turn a weekly job red on its own.

Usage::

    python3 scripts/ci/reach_report_verdict.py --runner-output FILE [--summary FILE]

``--runner-output`` is the captured stdout of the runner, from which the report
path is read (``reach_audit: report written: <path>``). Exit 0: no failing probe.
Exit 1: a failing probe, or no report to read.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REPORT_LINE = re.compile(r"^reach_audit: report written[^:]*: (?P<path>.+)$", re.MULTILINE)
_UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")

NOT_REACHED = "not reached"
PARTIAL = "partially reached"
NOT_PROBED = "not probed"

#: Not-probed reasons the skill documents as coverage facts (a stale declaration,
#: a tier that was not requested, a manifest entry). Anything else is a failure.
_COVERAGE_REASONS = (
    "declaration changed since derivation",
    "not constructible:",
)
_T2_NOT_REQUESTED = "tier T2 not requested"


@dataclass(frozen=True)
class ProbeRow:
    """One row of the report's Probes table."""

    probe: str
    cls: str
    reach: str
    reason: str


def report_path_from_output(runner_output: str) -> Path | None:
    """The report path the runner printed, or ``None`` when it wrote none."""
    match = _REPORT_LINE.search(runner_output)
    return Path(match.group("path").strip()) if match else None


def _cells(line: str) -> list[str]:
    parts = _UNESCAPED_PIPE.split(line.strip())
    return [cell.strip() for cell in parts[1:-1]]


def parse_probe_rows(report: str) -> list[ProbeRow]:
    """The rows of the report's Probes table, columns located by their header."""
    rows: list[ProbeRow] = []
    columns: dict[str, int] | None = None
    in_probes = False
    for line in report.splitlines():
        if line.startswith("## "):
            in_probes = line.strip() == "## Probes"
            columns = None
            continue
        if not in_probes or not line.startswith("|"):
            continue
        cells = _cells(line)
        if columns is None:
            if "Probe" in cells and "Class" in cells and "Reason" in cells:
                columns = {name: cells.index(name) for name in ("Probe", "Class", "Reach", "Reason")}
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(
            ProbeRow(
                probe=cells[columns["Probe"]],
                cls=cells[columns["Class"]],
                reach=cells[columns["Reach"]],
                reason=cells[columns["Reason"]],
            )
        )
    return rows


def t2_requested(report: str) -> bool:
    return "- Tier T2: requested" in report


def classify(rows: list[ProbeRow], *, t2: bool) -> tuple[list[str], list[str]]:
    """Return ``(failures, warnings)``, one line each, for the report's rows."""
    failures: list[str] = []
    warnings: list[str] = []
    for row in rows:
        if row.cls == NOT_REACHED:
            failures.append(f"{row.probe}: not reached ({row.reach})")
        elif row.cls == PARTIAL:
            warnings.append(f"{row.probe}: partially reached ({row.reach})")
        elif row.cls == NOT_PROBED:
            reason = row.reason
            if reason.startswith(_T2_NOT_REQUESTED):
                if t2:
                    failures.append(f"{row.probe}: reported 'tier T2 not requested' although T2 was requested")
                else:
                    warnings.append(f"{row.probe}: {reason}")
            elif reason.startswith(_COVERAGE_REASONS):
                warnings.append(f"{row.probe}: {reason}")
            else:
                failures.append(f"{row.probe}: not probed for a reason that is not a coverage fact: {reason}")
    return failures, warnings


def render_summary(failures: list[str], warnings: list[str], headline: str) -> str:
    lines = ["## Capability reach audit — verdict", "", headline, ""]
    if failures:
        lines += ["### Failing", ""] + [f"- {item}" for item in failures] + [""]
    if warnings:
        lines += ["### Coverage facts and partial reach (not failing)", ""] + [f"- {item}" for item in warnings] + [""]
    if not failures and not warnings:
        lines += ["Every entry is reached.", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--runner-output", required=True, type=Path, help="Captured stdout of reach_audit.py.")
    parser.add_argument("--summary", type=Path, help="Append a Markdown summary to this file (GITHUB_STEP_SUMMARY).")
    args = parser.parse_args(argv)

    try:
        output = args.runner_output.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"reach verdict: cannot read the runner output: {exc}", file=sys.stderr)
        return 1
    report_path = report_path_from_output(output)
    if report_path is None or not report_path.is_file():
        print("reach verdict: the runner wrote no report; there is nothing to judge.", file=sys.stderr)
        return 1

    report = report_path.read_text(encoding="utf-8")
    rows = parse_probe_rows(report)
    if not rows:
        print("reach verdict: the report has no probe rows; an empty probe set is not a pass.", file=sys.stderr)
        return 1
    failures, warnings = classify(rows, t2=t2_requested(report))
    headline = next((ln for ln in report.splitlines() if ln.startswith("**Not probed")), "")
    summary = render_summary(failures, warnings, headline)
    print(summary)
    if args.summary is not None:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(summary + "\n")
    for item in warnings:
        print(f"::warning title=reach::{item}")
    for item in failures:
        print(f"::error title=reach::{item}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
