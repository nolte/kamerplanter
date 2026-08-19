"""Tests for the observer workflow's decision (``.github/workflows/delivery-run-alert.yml``).

**What is under test.** Not the check script — that is
``test_delivery_run_check.py`` — but the ``actions/github-script`` body that acts
on its report: when an issue is opened, updated, closed, or deliberately left
alone. The rule this file exists for is R6 of
``project/requirements/delivery-run-alert.md``: a green delivery run closes the
alert only if every job the alert names actually RAN and succeeded. A green run
that merely skipped them proves nothing, and closing on it would make the alert
flap open and shut with every unrelated push to ``develop``.

**The shipped script is executed, not transcribed.** The body is read out of the
YAML with PyYAML and run verbatim under node — ``actions/github-script`` is a
node action, and node is present on every ``ubuntu-latest`` runner, which is
where this suite runs. A transcribed copy would keep passing while the shipped
script drifted away from it, which is this repository's "the test reaches the
rule by a different path than production" failure class. Asserting on the text
of the script would pin its spelling rather than its behaviour.

**The reports are produced by the shipped check, from recorded payloads.** The
fixtures are imported from ``test_delivery_run_check.py`` and run through
``scripts/ci/check_delivery_run.py`` itself, so what the JS sees here is
byte-identical to what the workflow's first step writes in production. Nothing
in this file hand-writes a report — a hand-written one could carry a field
combination the script cannot produce, and every assertion on it would then
certify nothing.

The three ``github`` methods, the ``context`` and the ``core`` calls are stubs
that record their arguments; the assertions are on the calls the shipped script
made, in order.

Traces to issue #1225 (no TC-ID: a CI alarm is not a user-facing case).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root
from tests.unit.test_delivery_run_check import (
    RUN_DEVELOP_GREEN_CHART_SKIPPED,
    RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS,
    RUN_NUCLEI_CANCELLED,
    RUN_NUCLEI_CANCELLED_JOBS,
    RUN_V0_2_0_RED,
    RUN_V0_2_0_RED_JOBS,
    RUN_V0_2_1_GREEN,
    RUN_V0_2_1_GREEN_JOBS,
    judge,
    replacing,
)

#: The workflow whose `actions/github-script` step acts on the report.
ALERT_WORKFLOW = ".github/workflows/delivery-run-alert.yml"

#: The job key inside it, and the report file name both halves agree on.
ALERT_JOB = "check-delivery-run"
REPORT_FILE = "delivery-run-report.json"

LABEL = "delivery-run-failed"

#: The chart job under both of the names GitHub reports it with, plus the base
#: name the marker carries. See test_delivery_run_check.py for the measurement.
CHART_JOB_RAN = "publish-helm-charts (kamerplanter)"
CHART_BASE = "publish-helm-charts"


def alert_script() -> str:
    """The ``actions/github-script`` body of the observer workflow, as shipped."""
    root = find_repo_root(Path(__file__).resolve())
    assert root is not None, "checkout root not found"
    document = yaml.safe_load((root / ALERT_WORKFLOW).read_text(encoding="utf-8"))
    scripts = [
        step["with"]["script"]
        for step in document["jobs"][ALERT_JOB]["steps"]
        if str(step.get("uses", "")).startswith("actions/github-script@")
    ]
    assert len(scripts) == 1, f"expected exactly one github-script step, found {len(scripts)}"
    return scripts[0]


#: Harness around the shipped script: the three objects `actions/github-script`
#: injects, faked, recording every call. The script body runs verbatim inside
#: the async wrapper — nothing about it is re-implemented here.
NODE_HARNESS = """
const fs = require('fs');
const calls = [];
const openIssues = JSON.parse(process.env.OPEN_ISSUES);
const github = {
  rest: {
    issues: {
      listForRepo: async (args) => { calls.push(['listForRepo', args]); return { data: openIssues }; },
      createComment: async (args) => { calls.push(['createComment', args]); },
      update: async (args) => { calls.push(['update', args]); },
      create: async (args) => { calls.push(['create', args]); return { data: { number: 4242 } }; },
    },
  },
};
const context = { repo: { owner: 'nolte', repo: 'kamerplanter' } };
const core = {
  notice: (message) => { calls.push(['notice', message]); },
  warning: (message) => { calls.push(['warning', message]); },
};

(async () => {
__BODY__
})().then(
  () => fs.writeFileSync('calls.json', JSON.stringify(calls)),
  (error) => { fs.writeFileSync('calls.json', JSON.stringify([['threw', String(error)]])); process.exit(3); },
);
"""


def run_alert_script(
    tmp_path: Path,
    report: dict[str, Any],
    *,
    open_issues: list[dict[str, Any]] | None = None,
) -> list[list[Any]]:
    """Execute the shipped script against *report* and return the calls it made."""
    node = shutil.which("node")
    if node is None:  # pragma: no cover — only on a runner without Node
        pytest.skip("node is not on PATH; the shipped github-script body cannot be executed")

    body = "\n".join(f"  {line}" if line.strip() else line for line in alert_script().splitlines())
    (tmp_path / "harness.js").write_text(NODE_HARNESS.replace("__BODY__", body), encoding="utf-8")
    (tmp_path / REPORT_FILE).write_text(json.dumps(report), encoding="utf-8")

    completed = subprocess.run(  # noqa: S603 — fixed argv, no shell, test-only
        [node, "harness.js"],
        cwd=tmp_path,
        # Inherited rather than replaced: a version-managed `node` shim needs
        # both HOME and its own PATH entries to resolve an interpreter at all.
        env={
            **os.environ,
            "RUN_URL": "https://github.com/nolte/kamerplanter/actions/runs/1",
            "OPEN_ISSUES": json.dumps(open_issues or []),
        },
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, f"node exited {completed.returncode}: {completed.stderr}"
    return json.loads((tmp_path / "calls.json").read_text(encoding="utf-8"))


def names(calls: list[list[Any]]) -> list[str]:
    """The call names in order, e.g. ``['listForRepo', 'create', 'notice']``."""
    return [call[0] for call in calls]


def only(calls: list[list[Any]], name: str) -> dict[str, Any]:
    """The single call named *name*, or a failure naming what was called instead."""
    matches = [call[1] for call in calls if call[0] == name]
    assert len(matches) == 1, f"expected exactly one {name}, got {names(calls)}"
    return matches[0]


def messages(calls: list[list[Any]], name: str) -> str:
    """Every `core.<name>` message, joined."""
    return "\n".join(str(call[1]) for call in calls if call[0] == name)


def issue(number: int, *, body: str, pull_request: Any = None) -> dict[str, Any]:
    """An open issue as `listForRepo` returns it."""
    return {"number": number, "body": body, "pull_request": pull_request}


def marker(*job_names: str) -> str:
    """The machine-readable marker the alert body carries.

    FULL job names, matrix suffix included — see
    ``TestClosingCannotFlap::test_one_matrix_leg_cannot_prove_another`` for why
    base names would be the wrong key.

    Rendered exactly as `JSON.stringify` does it — compact separators, no space
    after the comma. A Python default of `", "` here would build a string the
    shipped script never writes, and the union assertion would then be checking
    a marker that cannot occur.
    """
    payload = json.dumps(sorted(job_names), separators=(",", ":"))
    return f"<!-- kp:delivery-run-alert:failed-jobs={payload} -->"


# --------------------------------------------------------------------------- #
# The reports, produced by the shipped check from the recorded payloads.
# --------------------------------------------------------------------------- #

RED_TAG_REPORT = judge(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS)
GREEN_CHART_RAN_REPORT = judge(RUN_V0_2_1_GREEN, RUN_V0_2_1_GREEN_JOBS)
GREEN_CHART_SKIPPED_REPORT = judge(RUN_DEVELOP_GREEN_CHART_SKIPPED, RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS)

#: A delivery-lane run that concluded `cancelled`. The recorded cancelled run
#: belongs to another workflow (no delivery run has ever been cancelled), and
#: that one exercises a different branch — so the conclusion is swapped onto the
#: recorded green develop payload, and nothing else about it is invented.
INCONCLUSIVE_REPORT = judge(
    replacing(RUN_DEVELOP_GREEN_CHART_SKIPPED, conclusion="cancelled"),
    RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS,
)

#: A run GitHub concluded `failure` although no job carries a failing conclusion.
#: The report's `failed_jobs` is then honestly empty — see the script docstring.
RED_WITHOUT_A_FAILING_JOB_REPORT = judge(
    replacing(RUN_DEVELOP_GREEN_CHART_SKIPPED, conclusion="failure"),
    RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS,
)

#: A cancelled run of a DIFFERENT workflow — what a `workflow_dispatch` with a
#: foreign run id produces.
FOREIGN_REPORT = judge(RUN_NUCLEI_CANCELLED, RUN_NUCLEI_CANCELLED_JOBS)

# --------------------------------------------------------------------------- #
# The dispatch reports (W-1) are DERIVED, and here is why they have to be.
#
# `docker-publish.yml` carries a bare, unrestricted `workflow_dispatch:` — any
# collaborator can run the delivery lane on any branch, and `publish-helm-charts`
# runs unconditionally there (its `if:` accepts `github.event_name ==
# 'workflow_dispatch'`). But nobody ever has:
#
#     gh api "repos/nolte/kamerplanter/actions/workflows/246887462/runs\
#             ?event=workflow_dispatch" --jq .total_count   ->  0
#
# So there is no payload to record, and exactly two fields are replaced on a
# recorded one — `event` and `head_branch`. Everything else, including the job
# list that makes the chart job "ran and succeeded", is the measured v0.2.1 run.
# --------------------------------------------------------------------------- #

#: Green, chart job ran — but dispatched on a feature branch. The shape that
#: would let somebody close a `develop`/tag alert from their own branch.
GREEN_DISPATCH_FEATURE_REPORT = judge(
    replacing(RUN_V0_2_1_GREEN, event="workflow_dispatch", head_branch="fix/xyz"),
    RUN_V0_2_1_GREEN_JOBS,
)

#: Green, chart job ran, dispatched on `develop` — a legitimate manual repair of
#: the lane, and therefore a legitimate resolution.
GREEN_DISPATCH_DEVELOP_REPORT = judge(
    replacing(RUN_V0_2_1_GREEN, event="workflow_dispatch", head_branch="develop"),
    RUN_V0_2_1_GREEN_JOBS,
)

#: Red, dispatched on a feature branch. Still worth an alert — a red delivery run
#: is worth seeing wherever it ran — but the body has to say where.
RED_DISPATCH_FEATURE_REPORT = judge(
    replacing(RUN_V0_2_0_RED, event="workflow_dispatch", head_branch="fix/xyz"),
    RUN_V0_2_0_RED_JOBS,
)


class TestTheReportsUnderTestAreWhatTheScriptProduces:
    """Guards against this module's own fixtures drifting from the check."""

    def test_the_red_tag_report_is_an_alert_naming_the_chart_job(self) -> None:
        assert RED_TAG_REPORT["alert"] is True
        assert RED_TAG_REPORT["failed_jobs"] == [CHART_JOB_RAN]

    def test_the_two_green_reports_differ_only_in_whether_the_chart_job_ran(self) -> None:
        assert GREEN_CHART_RAN_REPORT["resolved"] is True
        assert GREEN_CHART_SKIPPED_REPORT["resolved"] is True
        assert CHART_JOB_RAN in GREEN_CHART_RAN_REPORT["succeeded_jobs"]
        assert CHART_BASE in GREEN_CHART_SKIPPED_REPORT["skipped_jobs"]

    def test_the_report_of_a_run_without_a_failing_job_names_none(self) -> None:
        assert RED_WITHOUT_A_FAILING_JOB_REPORT["alert"] is True
        assert RED_WITHOUT_A_FAILING_JOB_REPORT["failed_jobs"] == []


class TestOpeningTheAlert:
    """A red run with no open issue opens exactly one, labelled and marked."""

    def test_the_v0_2_0_run_opens_a_labelled_issue(self, tmp_path: Path) -> None:
        calls = run_alert_script(tmp_path, RED_TAG_REPORT)

        created = only(calls, "create")
        assert created["labels"] == [LABEL, "deployment"]
        assert created["title"] == ("The delivery lane went red: Build & Publish Container Images failed (#1225)")
        assert "update" not in names(calls)
        assert "createComment" not in names(calls)

    def test_the_body_carries_the_failed_job_set_as_full_names(self, tmp_path: Path) -> None:
        """The marker is the alert's memory: it is what a later green run is judged against.

        FULL names, matrix suffix included. The base name would join the
        executed and the skipped form of a job — convenient, and wrong: it would
        also join two DIFFERENT matrix legs, so one green leg could prove a leg
        that never re-ran.
        """
        calls = run_alert_script(tmp_path, RED_TAG_REPORT)

        assert marker(CHART_JOB_RAN) in only(calls, "create")["body"]
        assert marker(CHART_BASE) not in only(calls, "create")["body"]

    def test_the_body_names_the_measurement_a_human_needs(self, tmp_path: Path) -> None:
        body = only(run_alert_script(tmp_path, RED_TAG_REPORT), "create")["body"]

        assert "https://github.com/nolte/kamerplanter/actions/runs/31729355999" in body
        assert f"`{CHART_JOB_RAN}`" in body
        assert "`update-release-assets`" in body
        assert "tag `v0.2.0`" in body
        assert "8 of 11 job(s)" in body
        # The blindness this observer exists for, restated where it is read.
        assert "skipped" in body

    def test_the_commit_subject_is_never_rendered_into_the_issue(self, tmp_path: Path) -> None:
        """`display_title` is the most attacker-influenced string in the payload.

        It is carried in the report (a measurement) and deliberately not written
        into an issue body, where it would be rendered as Markdown.
        """
        body = only(run_alert_script(tmp_path, RED_TAG_REPORT), "create")["body"]

        assert RED_TAG_REPORT["display_title"] not in body

    def test_a_red_run_without_a_failing_job_says_so_and_marks_an_empty_set(self, tmp_path: Path) -> None:
        calls = run_alert_script(tmp_path, RED_WITHOUT_A_FAILING_JOB_REPORT)

        body = only(calls, "create")["body"]
        assert "none reports a failing conclusion" in body
        assert marker() in body

    def test_an_empty_job_set_promises_a_manual_close_not_an_automatic_one(self, tmp_path: Path) -> None:
        """S-6: the body must not promise what the marker cannot deliver.

        With no job named, no green run can ever satisfy the closing rule, so
        telling the reader "it closes when the job(s) named above succeed" —
        while naming none — would leave an issue open forever with a false
        explanation attached to it.
        """
        body = only(run_alert_script(tmp_path, RED_WITHOUT_A_FAILING_JOB_REPORT), "create")["body"]

        assert "cannot close automatically" in body
        assert "close this issue yourself" in body
        assert "It closes only when a run on the lane itself" not in body

    def test_a_normal_alert_still_promises_the_automatic_close(self, tmp_path: Path) -> None:
        """The other direction of the same branch — falsification, not one-sided."""
        body = only(run_alert_script(tmp_path, RED_TAG_REPORT), "create")["body"]

        assert "It closes only when a run on the lane itself" in body
        assert "cannot close automatically" not in body

    def test_the_body_warns_that_it_is_regenerated_and_points_edits_at_comments(self, tmp_path: Path) -> None:
        """S-5: the body is rewritten on every red run.

        An edit to it is lost, and an edit that strips the marker would stop the
        issue from ever closing automatically — so the body says so, and the
        triage step that used to invite "say so here" now asks for a comment.
        """
        body = only(run_alert_script(tmp_path, RED_TAG_REPORT), "create")["body"]

        assert "regenerated on every red run" in body
        assert "as a **comment** instead" in body
        assert "in a comment on this issue" in body


class TestUpdatingTheAlert:
    """A second red run updates the one issue and unions the marker."""

    def test_an_existing_issue_is_updated_not_duplicated(self, tmp_path: Path) -> None:
        open_issue = issue(77, body=f"old body\n{marker(CHART_JOB_RAN)}")

        calls = run_alert_script(tmp_path, RED_TAG_REPORT, open_issues=[open_issue])

        assert "create" not in names(calls)
        assert only(calls, "update")["issue_number"] == 77
        assert "Red again as of" in only(calls, "createComment")["body"]

    def test_the_marker_is_unioned_so_an_earlier_failure_is_not_forgotten(self, tmp_path: Path) -> None:
        """Two jobs breaking in two consecutive runs must both stay recorded.

        Replacing the set instead of unioning it would let a green run that only
        repaired the newer failure close an alert whose older one is still broken.
        """
        open_issue = issue(77, body=f"old body\n{marker('update-release-assets')}")

        calls = run_alert_script(tmp_path, RED_TAG_REPORT, open_issues=[open_issue])

        assert marker(CHART_JOB_RAN, "update-release-assets") in only(calls, "update")["body"]

    def test_a_pull_request_carrying_the_label_is_not_mistaken_for_the_alert(self, tmp_path: Path) -> None:
        """`listForRepo` returns pull requests too; the script filters them out."""
        pull = {"number": 9, "body": marker(CHART_JOB_RAN), "pull_request": {"url": "…"}}
        real = issue(77, body=marker(CHART_JOB_RAN))

        calls = run_alert_script(tmp_path, RED_TAG_REPORT, open_issues=[pull, real])

        assert only(calls, "update")["issue_number"] == 77

    def test_the_dedup_query_asks_for_open_issues_with_the_label(self, tmp_path: Path) -> None:
        query = only(run_alert_script(tmp_path, RED_TAG_REPORT), "listForRepo")

        assert query["state"] == "open"
        assert query["labels"] == LABEL


class TestClosingCannotFlap:
    """R6: only a run that actually re-ran the failing job may close the alert."""

    def test_the_green_run_that_ran_the_chart_job_closes_the_alert(self, tmp_path: Path) -> None:
        """32259216513, the v0.2.1 tag run: the chart job ran and passed."""
        open_issue = issue(77, body=f"…\n{marker(CHART_JOB_RAN)}")

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        comment = only(calls, "createComment")["body"]
        assert "Resolved" in comment
        assert f"`{CHART_JOB_RAN}`" in comment
        assert only(calls, "update") == {
            "owner": "nolte",
            "repo": "kamerplanter",
            "issue_number": 77,
            "state": "closed",
        }

    def test_the_green_run_that_skipped_the_chart_job_does_not_close_it(self, tmp_path: Path) -> None:
        """32157445903: green, and the job the alert is about never ran.

        This is the flap the whole rule exists to prevent — on `develop` the
        chart job is skipped on nearly every push, so closing here would reopen
        and reclose the alert indefinitely while the lane stayed broken.
        """
        open_issue = issue(77, body=f"…\n{marker(CHART_JOB_RAN)}")

        calls = run_alert_script(tmp_path, GREEN_CHART_SKIPPED_REPORT, open_issues=[open_issue])

        assert names(calls) == ["listForRepo", "notice"]
        notice = messages(calls, "notice")
        assert "stays OPEN" in notice
        # Named with the reason: the job still exists, this run just never
        # reached it. "Absent" would mean something else entirely (S-6).
        assert f"{CHART_JOB_RAN} [skipped in this run]" in notice

    def test_the_skipped_case_is_reported_to_the_run_log_and_not_as_a_comment(self, tmp_path: Path) -> None:
        """Deliberate: this branch is reached on nearly every push to `develop`.

        A comment per green run would bury the issue it is meant to protect
        under dozens of identical notes a day; the observer's run log is where a
        maintainer looking at this looks.
        """
        open_issue = issue(77, body=f"…\n{marker(CHART_JOB_RAN)}")

        calls = run_alert_script(tmp_path, GREEN_CHART_SKIPPED_REPORT, open_issues=[open_issue])

        assert "createComment" not in names(calls)
        assert "update" not in names(calls)

    def test_an_empty_marker_set_never_closes_the_alert(self, tmp_path: Path) -> None:
        """`every()` over an empty array is TRUE — the vacuous close.

        An alert opened by a red run with no failing job carries an empty marker.
        Treating it as satisfied would close the issue having verified nothing,
        which is the failure class this repository pays for repeatedly.
        """
        open_issue = issue(77, body=f"…\n{marker()}")

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        assert names(calls) == ["listForRepo", "notice"]
        assert "names no job set" in messages(calls, "notice")

    def test_an_alert_opened_without_a_failing_job_is_not_closed_by_the_next_green_run(self, tmp_path: Path) -> None:
        """End to end over the two runs, using the body the script itself wrote."""
        opened = only(run_alert_script(tmp_path, RED_WITHOUT_A_FAILING_JOB_REPORT), "create")

        calls = run_alert_script(
            tmp_path,
            GREEN_CHART_RAN_REPORT,
            open_issues=[issue(77, body=opened["body"])],
        )

        assert "update" not in names(calls)

    @pytest.mark.parametrize(
        "body",
        [
            "no marker at all",
            "<!-- kp:delivery-run-alert:failed-jobs=not json -->",
            '<!-- kp:delivery-run-alert:failed-jobs={"a": 1} -->',
            "<!-- kp:delivery-run-alert:failed-jobs=[1, 2] -->",
        ],
        ids=["absent", "unparseable", "not-an-array", "not-strings"],
    )
    def test_a_marker_that_cannot_be_read_leaves_the_alert_open(self, tmp_path: Path, body: str) -> None:
        """A hand-edited body must not be read as "nothing to prove"."""
        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[issue(77, body=body)])

        assert names(calls) == ["listForRepo", "notice"]
        assert "marker missing, unparseable or empty" in messages(calls, "notice")

    def test_a_green_run_with_no_open_alert_touches_nothing(self, tmp_path: Path) -> None:
        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT)

        assert names(calls) == ["listForRepo", "notice"]
        assert "no alert issue is open" in messages(calls, "notice").lower()

    def test_one_matrix_leg_cannot_prove_another(self, tmp_path: Path) -> None:
        """S-4: the reason the marker records full names.

        `publish-helm-charts` has exactly ONE leg today
        (docker-publish.yml, `matrix.chart: [kamerplanter]`), so a base-name key
        would work — right up to the second chart. Two legs failing and one leg
        re-running would then read as "proven", because both collapse to
        `publish-helm-charts`. The full name keeps them apart, and this test is
        what stops a future refactor from quietly re-introducing the collapse.
        """
        open_issue = issue(77, body=marker(CHART_JOB_RAN, "publish-helm-charts (other-chart)"))

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        assert "update" not in names(calls)
        assert "publish-helm-charts (other-chart)" in messages(calls, "notice")

    def test_a_job_that_vanished_reads_differently_from_one_that_was_skipped(self, tmp_path: Path) -> None:
        """S-6: "skipped in this run" and "absent from the lane" want different acts.

        A skipped job will come back on the right trigger; a renamed or deleted
        one never will, and that alert can only be closed by a human.
        """
        open_issue = issue(77, body=marker("a-job-that-no-longer-exists"))

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        assert "update" not in names(calls)
        assert "a-job-that-no-longer-exists [absent from this run" in messages(calls, "notice")

    def test_a_partially_repaired_alert_stays_open(self, tmp_path: Path) -> None:
        """Two recorded failures, one repaired: not resolved.

        The green tag run re-ran and passed `publish-helm-charts`, but the alert
        also remembers `some-other-job`, which is in no bucket of that run.
        """
        open_issue = issue(77, body=marker(CHART_JOB_RAN, "some-other-job"))

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        assert "update" not in names(calls)
        assert "some-other-job" in messages(calls, "notice")


class TestOnlyTheLaneCanProveARepair:
    """W-1: `docker-publish.yml` can be dispatched on ANY branch.

    Its `workflow_dispatch` is unrestricted and `publish-helm-charts` runs
    unconditionally there, so a collaborator dispatching on `fix/xyz` produces a
    green run in which the failing job "ran and succeeded" — about a branch the
    alert was never about. Closing on that would report the lane repaired while
    `develop` and the release tags are still broken.

    The predicate reads `event` and `head_branch`, both verbatim API fields, and
    deliberately not `ref_kind`, which is a heuristic on the branch name.
    """

    def test_a_green_dispatch_on_a_feature_branch_does_not_close_the_alert(self, tmp_path: Path) -> None:
        open_issue = issue(77, body=marker(CHART_JOB_RAN))

        calls = run_alert_script(tmp_path, GREEN_DISPATCH_FEATURE_REPORT, open_issues=[open_issue])

        assert names(calls) == ["listForRepo", "notice"]
        notice = messages(calls, "notice")
        assert "non-lane ref" in notice
        assert "fix/xyz" in notice
        assert "stays OPEN" in notice

    def test_a_green_dispatch_on_develop_does_close_the_alert(self, tmp_path: Path) -> None:
        """The manual repair path stays usable — the gate is the ref, not the event."""
        open_issue = issue(77, body=marker(CHART_JOB_RAN))

        calls = run_alert_script(tmp_path, GREEN_DISPATCH_DEVELOP_REPORT, open_issues=[open_issue])

        assert only(calls, "update")["state"] == "closed"

    def test_a_green_tag_push_closes_the_alert(self, tmp_path: Path) -> None:
        """`event == 'push'` needs no branch check: docker-publish.yml's `on.push`
        accepts only `branches: [develop]` and `tags: ['v*']`, so a push can
        reach it from nowhere else."""
        open_issue = issue(77, body=marker(CHART_JOB_RAN))

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        assert only(calls, "update")["state"] == "closed"

    def test_a_red_dispatch_on_a_feature_branch_still_opens_but_says_where(self, tmp_path: Path) -> None:
        """Opening is the right call — a red delivery run is worth seeing.

        The title says "the delivery lane went red", which on a dispatched
        feature-branch run is not yet established, so the body has to carry the
        ref the reader would otherwise assume.
        """
        body = only(run_alert_script(tmp_path, RED_DISPATCH_FEATURE_REPORT), "create")["body"]

        assert "not on the delivery lane's own refs" in body
        assert "`workflow_dispatch` on" in body
        assert "`fix/xyz`" in body

    def test_the_lane_check_does_not_run_when_no_alert_is_open(self, tmp_path: Path) -> None:
        """Nothing to protect, so the ordinary "nothing is open" notice wins."""
        calls = run_alert_script(tmp_path, GREEN_DISPATCH_FEATURE_REPORT)

        assert names(calls) == ["listForRepo", "notice"]
        assert "no alert issue is open" in messages(calls, "notice").lower()


class TestVerdictsThatMustTouchNothing:
    """Inconclusive and foreign runs leave the tracker exactly as they found it."""

    def test_an_inconclusive_run_leaves_an_open_alert_alone(self, tmp_path: Path) -> None:
        open_issue = issue(77, body=marker(CHART_JOB_RAN))

        calls = run_alert_script(tmp_path, INCONCLUSIVE_REPORT, open_issues=[open_issue])

        assert names(calls) == ["listForRepo", "notice"]
        assert "left OPEN" in messages(calls, "notice")
        assert "cancelled" in messages(calls, "notice")

    def test_an_inconclusive_run_opens_nothing_either(self, tmp_path: Path) -> None:
        calls = run_alert_script(tmp_path, INCONCLUSIVE_REPORT)

        assert names(calls) == ["listForRepo", "notice"]
        assert "No alert issue is open" in messages(calls, "notice")

    def test_a_run_of_another_workflow_is_warned_about_and_ignored(self, tmp_path: Path) -> None:
        """A dispatch may point anywhere; acting on it would be wrong twice over.

        A foreign RED run would open an issue blaming the delivery lane, and a
        foreign GREEN one would close a genuine, still-unrepaired alert. The
        script returns before the dedup query is even issued.
        """
        open_issue = issue(77, body=marker(CHART_JOB_RAN))

        calls = run_alert_script(tmp_path, FOREIGN_REPORT, open_issues=[open_issue])

        assert names(calls) == ["warning"]
        assert "Security — Nuclei Post-Merge Scan" in messages(calls, "warning")


class TestTheWorkflowContract:
    """Static properties of the shipped YAML the script half depends on."""

    def workflow(self) -> dict[str, Any]:
        root = find_repo_root(Path(__file__).resolve())
        assert root is not None
        return yaml.safe_load((root / ALERT_WORKFLOW).read_text(encoding="utf-8"))

    def test_it_observes_the_delivery_lane_on_completion(self) -> None:
        # PyYAML parses the unquoted `on:` key as the boolean True (YAML 1.1).
        triggers = self.workflow()[True]

        assert triggers["workflow_run"]["workflows"] == ["Build & Publish Container Images"]
        assert triggers["workflow_run"]["types"] == ["completed"]
        assert "run_id" in triggers["workflow_dispatch"]["inputs"]

    def test_permissions_are_least_privilege(self) -> None:
        assert self.workflow()["permissions"] == {
            "contents": "read",
            "actions": "read",
            "issues": "write",
        }

    def test_the_alerting_job_serialises_and_never_cancels(self) -> None:
        concurrency = self.workflow()["concurrency"]

        assert concurrency["group"] == "delivery-run-alert"
        assert concurrency["cancel-in-progress"] is False

    def test_both_actions_are_digest_pinned_to_the_siblings_shas(self) -> None:
        """Same SHAs as release-assets-complete.yml — read from it, not restated."""
        root = find_repo_root(Path(__file__).resolve())
        assert root is not None
        sibling = (root / ".github/workflows/release-assets-complete.yml").read_text(encoding="utf-8")
        mine = (root / ALERT_WORKFLOW).read_text(encoding="utf-8")

        for action in ("actions/checkout@", "actions/github-script@"):
            pinned = {line.split(action)[1].split()[0] for line in sibling.splitlines() if action in line}
            assert len(pinned) == 1, f"{action} is not pinned uniformly in the sibling"
            assert f"{action}{pinned.pop()}" in mine

    def test_the_untrusted_event_field_reaches_the_script_only_through_env(self) -> None:
        """`github.event.workflow_run.*` must never be interpolated into `run:`."""
        steps = self.workflow()["jobs"][ALERT_JOB]["steps"]
        check = next(step for step in steps if "run" in step)

        assert check["env"]["DELIVERY_RUN_ID"] == "${{ inputs.run_id || github.event.workflow_run.id }}"
        assert "github.event" not in check["run"]

        # No workflow expression of any kind inside the script body — that is
        # the rule, and it is stronger than "no github.event": an interpolated
        # expression is evaluated into the JS source before node ever sees it.
        # Comment lines are stripped first, because the body EXPLAINS the rule
        # and would otherwise fail an assertion about its own subject.
        code = "\n".join(line for line in alert_script().splitlines() if not line.strip().startswith("//"))
        assert "${{" not in code
        assert "github.event" not in code

    def test_the_issue_step_is_gated_on_the_report_file(self) -> None:
        """No report means undetermined, which must open nothing (NFR-018 §2)."""
        steps = self.workflow()["jobs"][ALERT_JOB]["steps"]
        issue_step = next(step for step in steps if str(step.get("uses", "")).startswith("actions/github-script@"))

        assert issue_step["if"] == f"always() && hashFiles('{REPORT_FILE}') != ''"

    def test_both_halves_agree_on_the_report_file_name(self) -> None:
        """The `run:` writes it, the `if:` guards on it, the script reads it."""
        steps = self.workflow()["jobs"][ALERT_JOB]["steps"]
        check = next(step for step in steps if "run" in step)

        assert check["run"].endswith(f"scripts/ci/check_delivery_run.py {REPORT_FILE}")
        assert f"readFileSync('{REPORT_FILE}'" in alert_script()

    def test_the_siblings_cross_reference_now_resolves(self) -> None:
        """`release-assets-complete.yml` and the check script named this file first."""
        root = find_repo_root(Path(__file__).resolve())
        assert root is not None
        assert (root / ALERT_WORKFLOW).is_file()

        for path in (
            ".github/workflows/release-assets-complete.yml",
            "scripts/ci/check_release_assets.py",
        ):
            assert "delivery-run-alert.yml" in (root / path).read_text(encoding="utf-8")
