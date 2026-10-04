"""The job verdict of ``reach-audit.yml`` over a capability-reach report.

``reach_audit.py`` exits 0 for a report in which a probe measured ``not reached`` or
in which a T2 environment target failed (both are classes of the report, not
findings; measured 2026-10-04: a run with 24 of 26 entries not probed exits 0).
``scripts/ci/reach_report_verdict.py`` is the half of the verdict the exit code does
not carry. Pinned here:

* a ``not reached`` probe fails the job;
* a ``not probed`` probe fails it for every reason that is not a documented coverage
  fact (fail closed), including an environment target that failed;
* a stale probe, a not-constructible entry and a partial reach are warnings;
* ``tier T2 not requested`` is a warning only when T2 was not requested.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.repo_scripts import load_repo_script

verdict = load_repo_script("ci/reach_report_verdict")

_HEADER = (
    "| Probe | Class | Reach | Measured by | Tier | Executed (UTC) | derived_from "
    "| Change detection | Declaration | Reason |\n"
    "|---|---|---|---|---|---|---|---|---|---|\n"
)


def _report(*rows: tuple[str, str, str, str], t2: bool = True) -> str:
    tier = "- Tier T2: requested (--include-t2)." if t2 else "- Tier T2: not requested; every T2 probe is not probed."
    body = "".join(
        f"| {pid} | {cls} | {reach} | `cmd` | T2 | now | blob:abc | clean | endpoint: x (y) | {reason} |\n"
        for pid, cls, reach, reason in rows
    )
    head = "# Capability reach audit — x\n\n**Not probed: 1 of 2 entries, 0 of them not constructible.**\n\n"
    return f"{head}## Provenance\n\n{tier}\n\n## Probes\n\n{_HEADER}{body}"


def _judge(report: str) -> tuple[list[str], list[str]]:
    rows = verdict.parse_probe_rows(report)
    assert rows, "the fixture must parse into rows, or every assertion below is vacuous"
    return verdict.classify(rows, t2=verdict.t2_requested(report))


def test_all_reached_is_clean() -> None:
    failures, warnings = _judge(_report(("a", "reached", "3/3 things", "—")))
    assert (failures, warnings) == ([], [])


def test_not_reached_fails_although_the_runner_exits_zero() -> None:
    failures, _ = _judge(_report(("a", "not reached", "0/3 things", "—")))
    assert failures == ["a: not reached (0/3 things)"]


@pytest.mark.parametrize(
    "reason",
    [
        "environment target `reach:stack:up` failed (exit 1)",
        "observation step exited 1: boom",
        "observation step printed nothing",
        "probe file is not committed; commit project/reach-probes/",
        "not approved",
        "a reason the runner invents next year",
    ],
)
def test_not_probed_for_any_other_reason_fails_closed(reason: str) -> None:
    failures, _ = _judge(_report(("a", "not probed", "—", reason)))
    assert len(failures) == 1
    assert reason in failures[0]


@pytest.mark.parametrize(
    "reason",
    [
        "declaration changed since derivation: the content of x at HEAD is no longer blob:abc",
        "not constructible: scope_not_countable: why",
    ],
)
def test_coverage_facts_are_warnings_not_failures(reason: str) -> None:
    failures, warnings = _judge(_report(("a", "not probed", "—", reason)))
    assert failures == []
    assert len(warnings) == 1


def test_partial_reach_is_a_warning() -> None:
    failures, warnings = _judge(_report(("a", "partially reached", "299/300 runs", "—")))
    assert failures == []
    assert warnings == ["a: partially reached (299/300 runs)"]


def test_t2_not_requested_depends_on_the_request() -> None:
    row = ("a", "not probed", "—", "tier T2 not requested")
    assert _judge(_report(row, t2=False)) == ([], ["a: tier T2 not requested"])
    failures, _ = _judge(_report(row, t2=True))
    assert len(failures) == 1


def test_escaped_pipe_in_a_cell_does_not_shift_the_columns() -> None:
    report = _report(("a", "not reached", "0/1", "—")).replace("endpoint: x (y)", r"endpoint: x \| y")
    failures, _ = _judge(report)
    assert failures == ["a: not reached (0/1)"]


def test_report_path_is_read_from_the_runner_output() -> None:
    out = "noise\nreach_audit: report written: /w/.audits/capability-reach/2026-10-04.md\n"
    assert verdict.report_path_from_output(out) == Path("/w/.audits/capability-reach/2026-10-04.md")
    assert verdict.report_path_from_output("reach_audit: boom\n") is None


def test_main_fails_when_the_runner_wrote_no_report(tmp_path: Path) -> None:
    out = tmp_path / "runner.out"
    out.write_text("reach_audit: usage error\n", encoding="utf-8")
    assert verdict.main(["--runner-output", str(out)]) == 1


def test_main_exit_code_follows_the_failures(tmp_path: Path) -> None:
    report = tmp_path / "r.md"
    out = tmp_path / "runner.out"
    out.write_text(f"reach_audit: report written: {report}\n", encoding="utf-8")
    report.write_text(_report(("a", "reached", "1/1", "—")), encoding="utf-8")
    assert verdict.main(["--runner-output", str(out)]) == 0
    report.write_text(_report(("a", "not reached", "0/1", "—")), encoding="utf-8")
    assert verdict.main(["--runner-output", str(out)]) == 1
