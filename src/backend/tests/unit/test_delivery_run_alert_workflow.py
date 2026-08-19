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
    DELIVERY_WORKFLOW,
    RUN_DEVELOP_GREEN_CHART_RAN,
    RUN_DEVELOP_GREEN_CHART_RAN_JOBS,
    RUN_DEVELOP_GREEN_CHART_SKIPPED,
    RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS,
    RUN_DEVELOP_RED_FIRST,
    RUN_DEVELOP_RED_FIRST_JOBS,
    RUN_DEVELOP_RED_SECOND,
    RUN_DEVELOP_RED_SECOND_JOBS,
    RUN_NUCLEI_CANCELLED,
    RUN_NUCLEI_CANCELLED_JOBS,
    RUN_V0_2_0_RED,
    RUN_V0_2_0_RED_JOBS,
    RUN_V0_2_1_GREEN,
    RUN_V0_2_1_GREEN_JOBS,
    jobs_page,
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


def entry(job: str, lane_ref: str, since: str) -> dict[str, str]:
    """One outstanding failure, exactly as the marker records it.

    ``job`` is the FULL job name (matrix suffix included) or ``"*"`` for a run
    that failed without any job reporting a failing conclusion; ``lane_ref`` is
    the half of the lane the failure happened on; ``since`` is the failing run's
    ``run_started_at`` as the report normalises it.
    """
    return {"job": job, "lane_ref": lane_ref, "since": since}


def marker(*entries: dict[str, str]) -> str:
    """The machine-readable marker (v2) the alert body carries.

    Three things about an entry are load-bearing, and each has its own test
    below: the FULL job name (``test_one_matrix_leg_cannot_prove_another``), the
    lane half (``test_a_green_develop_run_cannot_prove_a_tag_failure``) and the
    ``since`` anchor
    (``test_a_green_run_that_started_before_the_failure_proves_nothing``).

    Rendered exactly as the shipped script renders it: compact separators, key
    order ``job, lane_ref, since``, entries sorted by ``"<lane_ref> <job>"``. A
    Python default of ``", "`` here, or a different key order, would build a
    string the script never writes — and every assertion comparing a whole
    marker would then be checking a shape that cannot occur.
    """
    ordered = sorted(entries, key=lambda item: f"{item['lane_ref']} {item['job']}")
    payload = json.dumps({"entries": ordered}, separators=(",", ":"))
    return f"<!-- kp:delivery-run-alert:v2={payload} -->"


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


#: A run that concluded `startup_failure` having started NO job — the shape of a
#: `docker-publish.yml` whose YAML or job-level expression did not parse.
#: Measured on runs 32202729898 (nolte/gh-plumbing) and 26304512675
#: (nolte/claude-shared): `total_count: 0` with the run itself red. The
#: conclusion and the empty job page are placed on the recorded develop payload;
#: no field of it is invented, and the delivery lane has never produced one (a
#: fact this check exists to be ready for, not to wait for).
STARTUP_FAILURE_REPORT = judge(
    replacing(RUN_DEVELOP_GREEN_CHART_SKIPPED, conclusion="startup_failure"),
    jobs_page(RUN_DEVELOP_GREEN_CHART_SKIPPED["id"]),
)

#: A red run in which an IMAGE BUILD failed and the chart job passed — eight of
#: the lane's eleven jobs are image builds, so this is the ordinary alert, not
#: the exotic one. The two conclusions are swapped on the recorded v0.2.0
#: payload (the same technique as INCONCLUSIVE_REPORT above): everything else,
#: including every job name and timestamp, is the measured run.
RED_BACKEND_BUILD_JOBS = jobs_page(
    RUN_V0_2_0_RED["id"],
    *[
        {**item, "conclusion": "success" if item["name"] == CHART_JOB_RAN else item["conclusion"]}
        if item["name"] == CHART_JOB_RAN
        else {**item, "conclusion": "failure" if item["name"] == "build-backend" else item["conclusion"]}
        for item in RUN_V0_2_0_RED_JOBS["jobs"]
    ],
)
RED_BACKEND_BUILD_REPORT = judge(RUN_V0_2_0_RED, RED_BACKEND_BUILD_JOBS)

#: Green, chart job ran, dispatched on a `v*` TAG. `docker-publish.yml` gates
#: every release step on `startsWith(github.ref, 'refs/tags/v')` and runs the
#: whole release path on exactly such a run, so it is a legitimate repair of the
#: tag half — `gh workflow run docker-publish.yml --ref v0.2.1` is a path GitHub
#: offers next to `gh run rerun`.
GREEN_DISPATCH_TAG_REPORT = judge(
    replacing(RUN_V0_2_1_GREEN, event="workflow_dispatch"),
    RUN_V0_2_1_GREEN_JOBS,
)

#: Green on `develop`, chart job RAN — 32188774721, 2026-08-18T21:38. The run
#: that can prove a `develop` entry, as opposed to its skipped sibling.
GREEN_DEVELOP_CHART_RAN_REPORT = judge(RUN_DEVELOP_GREEN_CHART_RAN, RUN_DEVELOP_GREEN_CHART_RAN_JOBS)

#: The `run_started_at` of each recorded run, as the report normalises it. The
#: markers below anchor on these rather than on retyped literals, so a fixture
#: whose timestamp changes cannot leave a test asserting an impossible ordering.
TAG_RED_AT = RED_TAG_REPORT["run_started_at"]
TAG_GREEN_AT = GREEN_CHART_RAN_REPORT["run_started_at"]
DEVELOP_RED_FIRST_AT = judge(RUN_DEVELOP_RED_FIRST, RUN_DEVELOP_RED_FIRST_JOBS)["run_started_at"]
DEVELOP_RED_SECOND_AT = judge(RUN_DEVELOP_RED_SECOND, RUN_DEVELOP_RED_SECOND_JOBS)["run_started_at"]
DEVELOP_GREEN_CHART_RAN_AT = GREEN_DEVELOP_CHART_RAN_REPORT["run_started_at"]
RED_WITHOUT_A_FAILING_JOB_AT = RED_WITHOUT_A_FAILING_JOB_REPORT["run_started_at"]

#: `job: "*"` — how the marker records a run that failed with no failing job.
RUN_ITSELF = "*"


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

        assert marker(entry(CHART_JOB_RAN, "tag", TAG_RED_AT)) in only(calls, "create")["body"]
        assert marker(entry(CHART_BASE, "tag", TAG_RED_AT)) not in only(calls, "create")["body"]

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

    def test_a_red_run_without_a_failing_job_records_the_run_itself(self, tmp_path: Path) -> None:
        """An alert whose `failed_jobs` is empty is still a closable alert.

        There are two ways to reach it: a `startup_failure` run that never
        started a job (measured: runs 32202729898 and 26304512675 return
        `total_count: 0`), and a run GitHub failed while every job it reports
        concluded otherwise. Both are recorded as `*` — "the run itself" — so a
        later green run of the same half can strike it off. Recording nothing
        would leave the lane's most systematic breakage in an issue that can
        never close on its own.
        """
        calls = run_alert_script(tmp_path, RED_WITHOUT_A_FAILING_JOB_REPORT)

        body = only(calls, "create")["body"]
        assert "none reports a failing conclusion" in body
        assert marker(entry(RUN_ITSELF, "develop", RED_WITHOUT_A_FAILING_JOB_AT)) in body
        assert "the run itself on the develop half" in body

    def test_a_startup_failure_says_no_job_ran_and_where_to_look(self, tmp_path: Path) -> None:
        """The zero-job shape reads differently from "no job failed", and must.

        A run that started no job at all has nothing to open and read inside it;
        the triage step therefore points at `docker-publish.yml` itself. Pinning
        both halves keeps the branch from collapsing into one generic sentence.
        """
        body = only(run_alert_script(tmp_path, STARTUP_FAILURE_REPORT), "create")["body"]

        assert "the run started no job at all" in body
        assert "unparseable workflow file" in body
        assert marker(entry(RUN_ITSELF, "develop", RED_WITHOUT_A_FAILING_JOB_AT)) in body

    def test_the_outstanding_list_names_what_has_to_be_proven(self, tmp_path: Path) -> None:
        """The closing rule works off the marker; the body says the same in prose.

        A reader who cannot see the HTML comment must still be able to tell why
        the issue is open and what would close it — otherwise the only honest
        answer is "wait and see", which is what this observer replaces.
        """
        body = only(run_alert_script(tmp_path, RED_TAG_REPORT), "create")["body"]

        assert "## Outstanding" in body
        assert f"`{CHART_JOB_RAN}` on the tag half (failing since {TAG_RED_AT})" in body
        assert "proven independently" in body

    def test_the_chart_incident_is_not_baked_into_an_unrelated_alert(self, tmp_path: Path) -> None:
        """F8: eight of the lane's eleven jobs are image builds.

        The `publish-helm-charts` story (#1218/#1224) is one incident, not every
        alert. Emitted unconditionally it would hand a reader diagnosing a
        `build-backend` failure a Helm-attestation diagnosis — the misdirected
        triage this observer exists to prevent.
        """
        chart = only(run_alert_script(tmp_path, RED_TAG_REPORT), "create")["body"]
        other = only(run_alert_script(tmp_path, RED_BACKEND_BUILD_REPORT), "create")["body"]

        assert "Attest chart provenance" in chart
        assert "runs only when `helm/**` changed" in chart
        assert "Attest chart provenance" not in other
        assert "runs only when `helm/**` changed" not in other
        # Falsification in the same expression: the generic half survives.
        assert "A job that is **skipped** takes nothing down with it" in other

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
        open_issue = issue(77, body=f"old body\n{marker(entry(CHART_JOB_RAN, 'tag', TAG_RED_AT))}")

        calls = run_alert_script(tmp_path, RED_TAG_REPORT, open_issues=[open_issue])

        assert "create" not in names(calls)
        assert only(calls, "update")["issue_number"] == 77
        assert "Red again as of" in only(calls, "createComment")["body"]

    def test_the_marker_is_unioned_so_an_earlier_failure_is_not_forgotten(self, tmp_path: Path) -> None:
        """Two jobs breaking in two consecutive runs must both stay recorded.

        Replacing the set instead of unioning it would let a green run that only
        repaired the newer failure close an alert whose older one is still broken.
        """
        older = entry("update-release-assets", "tag", "2026-08-01T00:00:00+00:00")
        open_issue = issue(77, body=f"old body\n{marker(older)}")

        calls = run_alert_script(tmp_path, RED_TAG_REPORT, open_issues=[open_issue])

        assert marker(older, entry(CHART_JOB_RAN, "tag", TAG_RED_AT)) in only(calls, "update")["body"]

    def test_the_same_job_failing_again_moves_its_anchor_forward(self, tmp_path: Path) -> None:
        """Otherwise a green run BETWEEN the two failures would prove the second.

        The union keeps one entry per (half, job); which of the two `since`
        values it keeps decides whether an already-elapsed green run counts. It
        keeps the later one, so proof must postdate the most recent failure.
        """
        stale = entry(CHART_JOB_RAN, "tag", "2026-08-01T00:00:00+00:00")
        open_issue = issue(77, body=marker(stale))

        calls = run_alert_script(tmp_path, RED_TAG_REPORT, open_issues=[open_issue])

        assert marker(entry(CHART_JOB_RAN, "tag", TAG_RED_AT)) in only(calls, "update")["body"]

    def test_an_unreadable_marker_is_rebuilt_and_the_loss_is_stated(self, tmp_path: Path) -> None:
        """F6: `recorded || []` would drop the old names silently.

        The new marker can only carry this run's entries — that is unavoidable —
        but a silently shortened list closes the issue too early, so the comment
        says what happened and points at the history.
        """
        open_issue = issue(77, body="somebody edited this and the marker is gone")

        calls = run_alert_script(tmp_path, RED_TAG_REPORT, open_issues=[open_issue])

        assert marker(entry(CHART_JOB_RAN, "tag", TAG_RED_AT)) in only(calls, "update")["body"]
        assert "could not be read" in only(calls, "createComment")["body"]

    def test_a_pull_request_carrying_the_label_is_not_mistaken_for_the_alert(self, tmp_path: Path) -> None:
        """`listForRepo` returns pull requests too; the script filters them out."""
        recorded = marker(entry(CHART_JOB_RAN, "tag", TAG_RED_AT))
        pull = {"number": 9, "body": recorded, "pull_request": {"url": "…"}}
        real = issue(77, body=recorded)

        calls = run_alert_script(tmp_path, RED_TAG_REPORT, open_issues=[pull, real])

        assert only(calls, "update")["issue_number"] == 77

    def test_the_dedup_query_asks_for_open_issues_with_the_label(self, tmp_path: Path) -> None:
        query = only(run_alert_script(tmp_path, RED_TAG_REPORT), "listForRepo")

        assert query["state"] == "open"
        assert query["labels"] == LABEL


class TestClosingCannotFlap:
    """R6: an entry is struck off only by a run that actually proves it.

    Three independent conditions, each with its own failure mode and its own
    test: the same half of the lane, started after the failure, and the job
    itself ran and passed. Dropping any one of them closes an alert on evidence
    that does not exist.
    """

    def test_the_green_run_that_ran_the_chart_job_closes_the_alert(self, tmp_path: Path) -> None:
        """32259216513, the v0.2.1 tag run: same half, later, job ran and passed."""
        open_issue = issue(77, body=f"…\n{marker(entry(CHART_JOB_RAN, 'tag', TAG_RED_AT))}")

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
        open_issue = issue(77, body=f"…\n{marker(entry(CHART_JOB_RAN, 'develop', DEVELOP_RED_FIRST_AT))}")

        calls = run_alert_script(tmp_path, GREEN_CHART_SKIPPED_REPORT, open_issues=[open_issue])

        assert names(calls) == ["listForRepo", "notice"]
        notice = messages(calls, "notice")
        assert "stays OPEN" in notice
        # Named with the reason: the job still exists, this run just never
        # reached it. "Absent" would mean something else entirely (S-6).
        assert f"`{CHART_JOB_RAN}` on the develop half" in notice
        assert "[skipped in this run]" in notice

    def test_a_green_develop_run_cannot_prove_a_tag_failure(self, tmp_path: Path) -> None:
        """The two halves are not interchangeable, and the job NAME hides it.

        `publish-helm-charts`'s `Upload chart as release asset` step runs only on
        a tag (`if: startsWith(github.ref, 'refs/tags/v')`), so a green `develop`
        run executes the same job name with that step skipped. Accepting it as
        proof would re-introduce the skipped-proves-nothing blindness one level
        down, where no job-level bucket can see it.
        """
        open_issue = issue(77, body=marker(entry(CHART_JOB_RAN, "tag", TAG_RED_AT)))

        calls = run_alert_script(tmp_path, GREEN_DEVELOP_CHART_RAN_REPORT, open_issues=[open_issue])

        assert "update" not in names(calls)
        assert "[this run is on the develop half]" in messages(calls, "notice")

    def test_a_green_tag_run_cannot_prove_a_develop_failure(self, tmp_path: Path) -> None:
        """The same rule in the other direction — falsification, not one-sided."""
        open_issue = issue(77, body=marker(entry(CHART_JOB_RAN, "develop", DEVELOP_RED_FIRST_AT)))

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        assert "update" not in names(calls)
        assert "[this run is on the tag half]" in messages(calls, "notice")

    def test_a_green_run_that_started_before_the_failure_proves_nothing(self, tmp_path: Path) -> None:
        """F4: two delivery runs overlap routinely, and a replay is arbitrary.

        `docker-publish.yml`'s concurrency is per `github.ref`, so a `develop`
        push and a tag run run side by side; the older one finishing green says
        nothing about a failure that began after it started. The same anchor
        stops `workflow_dispatch -f run_id=<old green run>` from closing a
        current alert.
        """
        failed_after_the_green_run = entry(CHART_JOB_RAN, "tag", "2026-08-19T20:00:00+00:00")
        open_issue = issue(77, body=marker(failed_after_the_green_run))

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        assert "update" not in names(calls)
        assert "started before that failure" in messages(calls, "notice")

    def test_two_failures_on_one_half_clear_one_at_a_time(self, tmp_path: Path) -> None:
        """F6: all-or-nothing would leave an alert `develop` can never close.

        On `develop` most jobs are path-skipped on any given push, so two jobs
        breaking in two runs are almost never repaired by one run. Proving them
        together would hold the alert open until an unrelated `v*` tag; entries
        are therefore struck off independently, and only the last one closes it.
        """
        chart = entry(CHART_JOB_RAN, "develop", DEVELOP_RED_FIRST_AT)
        other = entry("build-backend", "develop", DEVELOP_RED_SECOND_AT)
        open_issue = issue(77, body=marker(chart, other))

        first = run_alert_script(tmp_path, GREEN_DEVELOP_CHART_RAN_REPORT, open_issues=[open_issue])

        # The chart job ran and passed in 32188774721; `build-backend` did too,
        # so this run proves both — the interesting half is that the body is
        # rewritten with the remaining entries rather than all-or-nothing.
        assert only(first, "update")["state"] == "closed"

        # Now the same alert with one entry this run cannot prove.
        unprovable = entry("a-job-that-did-not-run", "develop", DEVELOP_RED_SECOND_AT)
        partial = issue(78, body=marker(chart, unprovable))

        second = run_alert_script(tmp_path, GREEN_DEVELOP_CHART_RAN_REPORT, open_issues=[partial])

        updated = only(second, "update")
        assert "state" not in updated
        assert marker(unprovable) in updated["body"]
        assert marker(chart, unprovable) not in updated["body"]
        assert "Proven in run" in only(second, "createComment")["body"]

    def test_the_skipped_case_is_reported_to_the_run_log_and_not_as_a_comment(self, tmp_path: Path) -> None:
        """Deliberate: this branch is reached on nearly every push to `develop`.

        A comment per green run would bury the issue it is meant to protect
        under dozens of identical notes a day; the observer's run log is where a
        maintainer looking at this looks.
        """
        open_issue = issue(77, body=f"…\n{marker(entry(CHART_JOB_RAN, 'develop', DEVELOP_RED_FIRST_AT))}")

        calls = run_alert_script(tmp_path, GREEN_CHART_SKIPPED_REPORT, open_issues=[open_issue])

        assert "createComment" not in names(calls)
        assert "update" not in names(calls)

    def test_an_empty_entry_list_never_closes_the_alert(self, tmp_path: Path) -> None:
        """`every()` over an empty array is TRUE — the vacuous close.

        A hand-emptied marker names nothing that has to be proven. Treating it
        as satisfied would close the issue having verified nothing, which is the
        failure class this repository pays for repeatedly.
        """
        open_issue = issue(77, body=f"…\n{marker()}")

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        assert names(calls) == ["listForRepo", "notice"]
        assert "marker missing, unparseable or empty" in messages(calls, "notice")

    def test_an_alert_about_the_run_itself_closes_on_a_later_green_run_of_that_half(self, tmp_path: Path) -> None:
        """End to end over two runs, using the body the script itself wrote.

        The `*` entry is what makes a `startup_failure` observable AND closable:
        no job can prove it, so the proof is a later green run of the same half.
        """
        opened = only(run_alert_script(tmp_path, RED_WITHOUT_A_FAILING_JOB_REPORT), "create")

        calls = run_alert_script(
            tmp_path,
            GREEN_DEVELOP_CHART_RAN_REPORT,
            open_issues=[issue(77, body=opened["body"])],
        )

        assert only(calls, "update")["state"] == "closed"
        assert "the run itself" in only(calls, "createComment")["body"]

    def test_an_alert_about_the_run_itself_is_not_closed_by_the_other_half(self, tmp_path: Path) -> None:
        """The negative twin: a green TAG run says nothing about a broken `develop`."""
        opened = only(run_alert_script(tmp_path, RED_WITHOUT_A_FAILING_JOB_REPORT), "create")

        calls = run_alert_script(
            tmp_path,
            GREEN_CHART_RAN_REPORT,
            open_issues=[issue(77, body=opened["body"])],
        )

        assert "update" not in names(calls)
        assert "the run itself" in messages(calls, "notice")

    @pytest.mark.parametrize(
        "body",
        [
            "no marker at all",
            "<!-- kp:delivery-run-alert:v2=not json -->",
            '<!-- kp:delivery-run-alert:v2={"entries":"nope"} -->',
            '<!-- kp:delivery-run-alert:v2={"entries":[{"job":"x"}]} -->',
            (
                '<!-- kp:delivery-run-alert:v2={"entries":[{"job":"x","lane_ref":"moon",'
                '"since":"2026-08-13T18:09:50+00:00"}]} -->'
            ),
            '<!-- kp:delivery-run-alert:v2={"entries":[{"job":"x","lane_ref":"tag","since":"whenever"}]} -->',
            '<!-- kp:delivery-run-alert:failed-jobs=["publish-helm-charts (kamerplanter)"] -->',
        ],
        ids=["absent", "unparseable", "not-a-list", "incomplete", "unknown-half", "unparseable-since", "v1-marker"],
    )
    def test_a_marker_that_cannot_be_read_leaves_the_alert_open(self, tmp_path: Path, body: str) -> None:
        """A hand-edited — or outdated — body must not be read as "nothing to prove".

        The v1 case is deliberate: an alert opened before this rule landed
        carries the old marker, and the safe reading of it is "I cannot tell",
        not "nothing outstanding".
        """
        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[issue(77, body=body)])

        assert names(calls) == ["listForRepo", "notice"]
        assert "marker missing, unparseable or empty" in messages(calls, "notice")

    def test_a_green_run_with_no_open_alert_touches_nothing(self, tmp_path: Path) -> None:
        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT)

        assert names(calls) == ["listForRepo", "notice"]
        assert "no alert issue is open" in messages(calls, "notice").lower()

    def test_one_matrix_leg_cannot_prove_another(self, tmp_path: Path) -> None:
        """S-4: the reason the marker records full names.

        `publish-helm-charts` has exactly ONE leg today (docker-publish.yml,
        `matrix.chart: [kamerplanter]`), so a base-name key would work — right up
        to the second chart. Two legs failing and one leg re-running would then
        read as "proven", because both collapse to `publish-helm-charts`. The
        full name keeps them apart, and this test is what stops a future refactor
        from quietly re-introducing the collapse.
        """
        open_issue = issue(
            77,
            body=marker(
                entry(CHART_JOB_RAN, "tag", TAG_RED_AT),
                entry("publish-helm-charts (other-chart)", "tag", TAG_RED_AT),
            ),
        )

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        assert "state" not in only(calls, "update")
        assert "publish-helm-charts (other-chart)" in messages(calls, "notice")

    def test_a_job_that_vanished_reads_differently_from_one_that_was_skipped(self, tmp_path: Path) -> None:
        """S-6: "skipped in this run" and "absent from the lane" want different acts.

        A skipped job will come back on the right trigger; a renamed or deleted
        one never will, and that alert can only be closed by a human.
        """
        open_issue = issue(77, body=marker(entry("a-job-that-no-longer-exists", "tag", TAG_RED_AT)))

        calls = run_alert_script(tmp_path, GREEN_CHART_RAN_REPORT, open_issues=[open_issue])

        assert "update" not in names(calls)
        notice = messages(calls, "notice")
        assert "`a-job-that-no-longer-exists` on the tag half" in notice
        assert "[absent from this run — renamed or removed?]" in notice
        # The two readings must not collapse: a skipped job comes back, an
        # absent one does not, and only the second needs a human.
        assert "[skipped in this run]" not in notice


class TestOnlyTheLaneCanProveARepair:
    """W-1/F2: `docker-publish.yml` can be dispatched on ANY branch.

    Its `workflow_dispatch` is unrestricted and `publish-helm-charts` runs
    unconditionally there, so a collaborator dispatching on `fix/xyz` produces a
    green run in which the failing job "ran and succeeded" — about a branch the
    alert was never about. Closing on that would report the lane repaired while
    `develop` and the release tags are still broken.

    The predicate reads `lane_ref`, which the check derives from `event` and
    `head_branch` against docker-publish.yml's own trigger list — deliberately
    not `ref_kind`, which is a heuristic kept for prose.
    """

    def test_a_green_dispatch_on_a_feature_branch_does_not_close_the_alert(self, tmp_path: Path) -> None:
        open_issue = issue(77, body=marker(entry(CHART_JOB_RAN, "tag", TAG_RED_AT)))

        calls = run_alert_script(tmp_path, GREEN_DISPATCH_FEATURE_REPORT, open_issues=[open_issue])

        assert names(calls) == ["listForRepo", "warning"]
        warning = messages(calls, "warning")
        assert "fix/xyz" in warning
        assert "not the delivery lane" in warning
        assert "untouched" in warning

    def test_a_green_dispatch_on_develop_does_close_the_alert(self, tmp_path: Path) -> None:
        """The manual repair path stays usable — the gate is the ref, not the event."""
        open_issue = issue(77, body=marker(entry(CHART_JOB_RAN, "develop", DEVELOP_RED_FIRST_AT)))

        calls = run_alert_script(tmp_path, GREEN_DISPATCH_DEVELOP_REPORT, open_issues=[open_issue])

        assert only(calls, "update")["state"] == "closed"

    def test_a_green_dispatch_on_a_tag_does_close_the_alert(self, tmp_path: Path) -> None:
        """F2: `gh workflow run docker-publish.yml --ref v0.2.1` is a repair path.

        Every release step in that workflow is gated on
        `startsWith(github.ref, 'refs/tags/v')` and runs on exactly such a
        dispatch, so refusing it would leave an alert open until an unrelated
        `helm/**` push — while the release it is about had already been repaired.
        """
        open_issue = issue(77, body=marker(entry(CHART_JOB_RAN, "tag", TAG_RED_AT)))

        calls = run_alert_script(tmp_path, GREEN_DISPATCH_TAG_REPORT, open_issues=[open_issue])

        assert only(calls, "update")["state"] == "closed"

    def test_a_red_dispatch_on_a_feature_branch_opens_nothing(self, tmp_path: Path) -> None:
        """Opening would be a claim the run does not support.

        The title says "the delivery lane went red", but a dispatch on `fix/xyz`
        is somebody's branch, not `develop` and not a release tag. Worse, the
        entry would be recorded against no half of the lane and could therefore
        never be proven — an alert that can only be closed by hand. The
        dispatcher sees their own red run; the warning records that the observer
        looked and stayed out.
        """
        calls = run_alert_script(tmp_path, RED_DISPATCH_FEATURE_REPORT)

        assert "create" not in names(calls)
        warning = messages(calls, "warning")
        assert "`fix/xyz`" in warning
        assert "neither `develop` nor a `v*` tag" in warning

    def test_a_red_dispatch_on_a_feature_branch_leaves_an_open_alert_alone(self, tmp_path: Path) -> None:
        """And it must not touch an existing one either — in either direction."""
        open_issue = issue(77, body=marker(entry(CHART_JOB_RAN, "tag", TAG_RED_AT)))

        calls = run_alert_script(tmp_path, RED_DISPATCH_FEATURE_REPORT, open_issues=[open_issue])

        assert names(calls) == ["listForRepo", "warning"]
        assert "#77 is untouched" in messages(calls, "warning")

    def test_the_lane_check_does_not_run_when_no_alert_is_open(self, tmp_path: Path) -> None:
        """Nothing to protect, so the notice says only that nothing is open."""
        calls = run_alert_script(tmp_path, GREEN_DISPATCH_FEATURE_REPORT)

        assert names(calls) == ["listForRepo", "warning"]
        assert "no alert issue is open" in messages(calls, "warning").lower()


class TestVerdictsThatMustTouchNothing:
    """Inconclusive and foreign runs leave the tracker exactly as they found it."""

    def test_an_inconclusive_run_leaves_an_open_alert_alone(self, tmp_path: Path) -> None:
        open_issue = issue(77, body=marker(entry(CHART_JOB_RAN, "tag", TAG_RED_AT)))

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
        open_issue = issue(77, body=marker(entry(CHART_JOB_RAN, "tag", TAG_RED_AT)))

        calls = run_alert_script(tmp_path, FOREIGN_REPORT, open_issues=[open_issue])

        assert names(calls) == ["warning"]
        assert "Security — Nuclei Post-Merge Scan" in messages(calls, "warning")


class TestTheCouplingToTheObservedWorkflow:
    """F7: three literal copies of `docker-publish.yml`'s identity, plus a
    hard-coded reading of its triggers — and nothing that notices when they rot.

    The `workflow_run` trigger matches on the observed workflow's `name:`, the
    script defaults to the same string, and the fixtures repeat it. A rename in
    an unrelated refactor makes the observer silently stop firing — no red run,
    no alert, exactly the "nothing observed it" class #1225 was opened for.

    The trigger list is load-bearing a second time: `lane_ref` derives "a push
    run is on `develop` exactly when `head_branch` says so, and is a tag run
    otherwise" FROM the fact that `on.push` accepts nothing else. Adding
    `branches: [develop, release/*]` — or a `pull_request:` trigger — would make
    a feature-branch run classify as on-lane and let it close a genuine alert.
    That is the W-1 hole the closing rule exists to shut.

    These assertions read the observed workflow itself, so they fail on the
    change rather than on its consequence.
    """

    @staticmethod
    def observed() -> dict[str, Any]:
        root = find_repo_root(Path(__file__).resolve())
        assert root is not None, "checkout root not found"
        return yaml.safe_load((root / ".github/workflows/docker-publish.yml").read_text(encoding="utf-8"))

    def test_all_three_copies_of_the_workflow_name_agree(self) -> None:
        root = find_repo_root(Path(__file__).resolve())
        assert root is not None
        observer = yaml.safe_load((root / ALERT_WORKFLOW).read_text(encoding="utf-8"))
        script = (root / "scripts/ci/check_delivery_run.py").read_text(encoding="utf-8")

        observed_name = self.observed()["name"]

        # `on` is parsed by PyYAML as the boolean True (YAML 1.1), hence the key.
        assert observer[True]["workflow_run"]["workflows"] == [observed_name]
        assert f'DEFAULT_WORKFLOW_NAME = "{observed_name}"' in script
        assert observed_name == DELIVERY_WORKFLOW

    def test_the_observed_push_trigger_is_still_develop_and_v_tags_only(self) -> None:
        """The premise `lane_ref` is derived from, asserted against its source."""
        push = self.observed()[True]["push"]

        assert push["branches"] == ["develop"]
        assert push["tags"] == ["v*"]

    def test_the_observed_workflow_has_no_pull_request_trigger(self) -> None:
        """A fork PR run would carry attacker-influenced fields into the report,
        and `event == 'push'` is only a safe lane test while no other event can
        reach the workflow from an arbitrary ref."""
        assert "pull_request" not in self.observed()[True]

    def test_the_chart_job_is_still_the_single_matrix_leg_the_fixtures_record(self) -> None:
        """The recorded job name `publish-helm-charts (kamerplanter)` is a matrix
        expansion. A second leg is legitimate — but the fixtures would then no
        longer cover the lane, and `test_one_matrix_leg_cannot_prove_another`
        would be guarding a case the recorded payloads never exercise."""
        chart = self.observed()["jobs"]["publish-helm-charts"]

        assert chart["strategy"]["matrix"]["chart"] == ["kamerplanter"]
        assert f"{CHART_BASE} ({chart['strategy']['matrix']['chart'][0]})" == CHART_JOB_RAN


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
