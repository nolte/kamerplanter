"""Tests for the delivery-lane run observer (``scripts/ci/check_delivery_run.py``).

**What is under test.** The verdict taxonomy, the ran-versus-skipped
distinction the no-flap rule turns on, the job pagination and the fail-loud
contract, driven against RECORDED GitHub API payloads. Both the HTTP layer and
the clock are injected, so nothing here touches the network, the GitHub API or a
live ``gh``. A test that asked the real API "is the delivery lane green?" would
answer something different after every push and assert nothing.

**The fixtures are recorded, not invented.** Captured on 2026-08-19 with::

    gh api repos/nolte/kamerplanter/actions/runs/<id>
    gh api repos/nolte/kamerplanter/actions/runs/<id>/jobs?per_page=100

and reduced to the fields the script reads; every id, job name, conclusion and
timestamp below is the measured value. The one derivation is each job's
``html_url``, rebuilt from ``runs/<run_id>/job/<job_id>`` — a pattern verified to
hold for all 67 recorded job objects, and a field the script only copies through.

    31729355999  v0.2.0 tag, RED     `publish-helm-charts (kamerplanter)` failed,
                                     `update-release-assets` skipped, `changes`
                                     skipped, 8 image builds succeeded
    31955164085  develop, RED        chart job failed, all 8 builds skipped
    31955579431  develop, RED        the same, 8 minutes later
    32259216513  v0.2.1 tag, GREEN   chart job RAN and succeeded
    32157445903  develop, GREEN      chart job SKIPPED
    32188774721  develop, GREEN      chart job RAN — see the refutation below
    32188774700  develop, CANCELLED  a run of another workflow entirely

**A refuted premise, recorded rather than quietly fixed.** The work package
named 32188774721 as "a green develop push where the chart job was skipped". It
is not: in that run ``publish-helm-charts (kamerplanter)`` ran and succeeded
(``gh api .../runs/32188774721/jobs`` — `build-backend` ran too, so the push
touched more than nothing). The genuine chart-skipped green develop push is
32157445903, found by scanning the workflow's run list; both are kept, because
the pair is exactly the distinction R6 depends on and having them side by side
is what proves the check tells them apart.

**Two measured shapes that no invented fixture would have had.**

1. A matrix job is named ``publish-helm-charts (kamerplanter)`` when it RUNS
   (31729355999, 32259216513, 32188774721) and plain ``publish-helm-charts``
   when it is SKIPPED (32157445903). Same job, two strings. A hand-written
   fixture would have used one name for both and certified a comparison that
   cannot work in production.
2. A skipped job carries ``"conclusion": "skipped"`` on this endpoint — not
   ``"success"``. The "a skipped job reports success" trap lives in
   ``needs.*.result``, not here, and the check is only able to separate ran from
   skipped because of it.

**The cancelled fixture comes from another workflow, deliberately.**
``gh api "repos/nolte/kamerplanter/actions/workflows/246887462/runs?status=cancelled"``
returns an EMPTY list: no run of the delivery lane has ever been cancelled. So
the cancelled shape is recorded from a real cancelled run of
``Security — Nuclei Post-Merge Scan`` (32188774700) rather than by editing a
delivery-lane payload — and it doubles as the ``is_expected_workflow: false``
case, which is what a `workflow_dispatch` pointed at the wrong run produces.
The three conclusions with no recorded instance anywhere (``neutral``,
``action_required``, ``stale``) are the only values swapped onto a recorded
payload, and the test that does it says so.

**Falsification in both directions.** Every red fixture is asserted to alert AND
to not resolve; every green fixture to resolve AND to not alert; the cancelled
one to do neither. A check that only ever says "red" is as worthless as one that
only ever says "green", and the mutual exclusivity is asserted across all
fixtures at once so no future verdict can set both.

**Placement.** The script lives outside the backend package (it runs in the
required ``static`` lane on a bare runner with none of this project's
dependencies installed), so it is loaded by path through
``tests.support.repo_scripts``. It is not a backend test in subject; it is one
in placement, because this is the tier that runs.

Traces to issue #1225 (no TC-ID: a CI alarm is not a user-facing case).
"""

from __future__ import annotations

import http.client
import json
import subprocess
import sys
import urllib.error
from collections.abc import Callable
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from tests.support.repo_scripts import find_repo_root, load_repo_script

checker = load_repo_script("ci/check_delivery_run")

REPOSITORY = "nolte/kamerplanter"

#: The workflow this observer is for — restated here so a change to the script's
#: default breaks a test rather than silently re-aiming the observer.
DELIVERY_WORKFLOW = "Build & Publish Container Images"

#: The chart job, in both of the names GitHub reports it under.
CHART_JOB_RAN = "publish-helm-charts (kamerplanter)"
CHART_JOB_SKIPPED = "publish-helm-charts"


def at(moment: str) -> datetime:
    """Parse a ``Z``-suffixed instant into an aware UTC datetime."""
    return datetime.fromisoformat(moment.replace("Z", "+00:00"))


def run_url(run_id: int) -> str:
    """The single run URL the check requests."""
    return f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{run_id}"


def jobs_url(run_id: int, page: int = 1) -> str:
    """One page of the jobs URL the check requests."""
    return f"https://api.github.com/repos/{REPOSITORY}/actions/runs/{run_id}/jobs?per_page=100&page={page}"


# --------------------------------------------------------------------------- #
# Payload builders — the recorded response shapes, field for field.
# --------------------------------------------------------------------------- #


def run_payload(**fields: Any) -> dict[str, Any]:
    """One ``GET /repos/{repo}/actions/runs/{id}`` object.

    A pass-through on purpose: the keyword names below ARE the recorded field
    names, so a fixture cannot acquire a field the API does not send.
    """
    return dict(fields)


def job(
    job_id: int,
    name: str,
    conclusion: str,
    started_at: str,
    completed_at: str,
    *,
    status: str = "completed",
) -> dict[str, Any]:
    """One entry of the ``jobs`` array, minus the URL its page fills in."""
    return {
        "id": job_id,
        "name": name,
        "status": status,
        "conclusion": conclusion,
        "started_at": started_at,
        "completed_at": completed_at,
    }


def jobs_page(run_id: int, *jobs: dict[str, Any], total_count: int | None = None) -> dict[str, Any]:
    """A ``GET /actions/runs/{id}/jobs`` page carrying *jobs*.

    ``total_count`` defaults to the number of jobs on the page, which is the
    single-page reality of this lane (11 jobs); the override exists for the
    pagination and truncation tests.
    """
    return {
        "total_count": len(jobs) if total_count is None else total_count,
        "jobs": [
            {
                **entry,
                "html_url": f"https://github.com/{REPOSITORY}/actions/runs/{run_id}/job/{entry['id']}",
            }
            for entry in jobs
        ],
    }


class RecordingFetch:
    """A routing fake for the injected HTTP layer, recording every URL."""

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = routes
        self.urls: list[str] = []

    def __call__(self, url: str) -> Any:
        self.urls.append(url)
        if url not in self.routes:
            raise checker.DeliveryRunError(f"GET {url} failed: HTTP 404")
        value = self.routes[url]
        if isinstance(value, Exception):
            raise value
        return value


def serving(run: dict[str, Any], jobs: dict[str, Any]) -> RecordingFetch:
    """A fake serving one recorded run and its one page of jobs."""
    return RecordingFetch({run_url(run["id"]): run, jobs_url(run["id"]): jobs})


def build(
    fetch: Callable[[str], Any],
    *,
    run_id: int,
    now: str = "2026-08-19T14:00:00Z",
) -> dict[str, Any]:
    """Call the script's report builder with the standard arguments."""
    return checker.build_report(
        fetch,
        repository=REPOSITORY,
        run_id=run_id,
        workflow_name=DELIVERY_WORKFLOW,
        now=at(now),
    )


def judge(run: dict[str, Any], jobs: dict[str, Any], *, now: str = "2026-08-19T14:00:00Z") -> dict[str, Any]:
    """Build the report for one recorded run/jobs pair."""
    return build(serving(run, jobs), run_id=run["id"], now=now)


def without(payload: dict[str, Any], key: str) -> dict[str, Any]:
    """A deep copy of *payload* with *key* removed."""
    copy = deepcopy(payload)
    copy.pop(key)
    return copy


def replacing(payload: dict[str, Any], **fields: Any) -> dict[str, Any]:
    """A deep copy of *payload* with *fields* overwritten."""
    copy = deepcopy(payload)
    copy.update(fields)
    return copy


# --------------------------------------------------------------------------- #
# The recorded runs, exactly as `gh api` returned them on 2026-08-19.
# --------------------------------------------------------------------------- #

#: v0.2.0, 2026-08-13 — the tag run that lost the release's chart. `changes` is
#: SKIPPED because its `if: github.ref_type == 'branch'` excludes tag runs; the
#: eight image builds ran and passed; the chart job failed; and
#: `update-release-assets` was skipped by the `!contains(needs.*.result,
#: 'failure')` guard on its own `needs`. That skip is the loss #1218 chased.
RUN_V0_2_0_RED = run_payload(
    id=31729355999,
    name="Build & Publish Container Images",
    path=".github/workflows/docker-publish.yml",
    event="push",
    head_branch="v0.2.0",
    head_sha="474e37ceb7da379b4379cee4529a97b200a134bb",
    display_title="chore(deps): update github/codeql-action action to v4.37.7 (#1136)",
    status="completed",
    conclusion="failure",
    run_attempt=1,
    run_number=504,
    run_started_at="2026-08-13T18:09:50Z",
    updated_at="2026-08-13T18:21:18Z",
    html_url="https://github.com/nolte/kamerplanter/actions/runs/31729355999",
)

RUN_V0_2_0_RED_JOBS = jobs_page(
    31729355999,
    job(94545584506, "changes", "skipped", "2026-08-13T18:09:51Z", "2026-08-13T18:09:51Z"),
    job(94545585229, "build-reranker-service", "success", "2026-08-13T18:09:53Z", "2026-08-13T18:20:38Z"),
    job(94545585245, "build-inference-service", "success", "2026-08-13T18:09:53Z", "2026-08-13T18:12:42Z"),
    job(94545585296, "build-embedding-service", "success", "2026-08-13T18:10:01Z", "2026-08-13T18:13:54Z"),
    job(94545585303, "build-vectordb", "success", "2026-08-13T18:09:55Z", "2026-08-13T18:11:32Z"),
    job(94545585325, "build-knowledge-service", "success", "2026-08-13T18:09:53Z", "2026-08-13T18:10:46Z"),
    job(94545585365, "build-knowledge", "success", "2026-08-13T18:09:53Z", "2026-08-13T18:10:32Z"),
    job(94545585371, "build-frontend", "success", "2026-08-13T18:09:53Z", "2026-08-13T18:12:01Z"),
    job(94545585383, "build-backend", "success", "2026-08-13T18:09:54Z", "2026-08-13T18:10:38Z"),
    job(94548618061, "publish-helm-charts (kamerplanter)", "failure", "2026-08-13T18:20:56Z", "2026-08-13T18:21:17Z"),
    job(94548802330, "update-release-assets", "skipped", "2026-08-13T18:21:18Z", "2026-08-13T18:21:17Z"),
)

#: develop, 2026-08-16T15:16 — a `helm/**`-only push: every image build is
#: skipped by the `changes` filter, the chart job runs anyway (its `always()`
#: condition) and fails.
RUN_DEVELOP_RED_FIRST = run_payload(
    id=31955164085,
    name="Build & Publish Container Images",
    path=".github/workflows/docker-publish.yml",
    event="push",
    head_branch="develop",
    head_sha="2531bb51bf9eb6a2d6d74cb0ca1c116e12d63ed9",
    display_title="chore(deps): update kamerplanter images (#1140)",
    status="completed",
    conclusion="failure",
    run_attempt=1,
    run_number=551,
    run_started_at="2026-08-16T15:16:38Z",
    updated_at="2026-08-16T15:17:11Z",
    html_url="https://github.com/nolte/kamerplanter/actions/runs/31955164085",
)

RUN_DEVELOP_RED_FIRST_JOBS = jobs_page(
    31955164085,
    job(95184588899, "changes", "success", "2026-08-16T15:16:40Z", "2026-08-16T15:16:47Z"),
    job(95184607483, "publish-helm-charts (kamerplanter)", "failure", "2026-08-16T15:16:50Z", "2026-08-16T15:17:10Z"),
    job(95184607570, "build-reranker-service", "skipped", "2026-08-16T15:16:48Z", "2026-08-16T15:16:48Z"),
    job(95184607626, "build-embedding-service", "skipped", "2026-08-16T15:16:48Z", "2026-08-16T15:16:48Z"),
    job(95184607688, "build-backend", "skipped", "2026-08-16T15:16:48Z", "2026-08-16T15:16:48Z"),
    job(95184607705, "build-knowledge-service", "skipped", "2026-08-16T15:16:48Z", "2026-08-16T15:16:48Z"),
    job(95184607756, "build-frontend", "skipped", "2026-08-16T15:16:48Z", "2026-08-16T15:16:48Z"),
    job(95184607772, "build-vectordb", "skipped", "2026-08-16T15:16:48Z", "2026-08-16T15:16:48Z"),
    job(95184607854, "build-knowledge", "skipped", "2026-08-16T15:16:48Z", "2026-08-16T15:16:48Z"),
    job(95184607904, "build-inference-service", "skipped", "2026-08-16T15:16:48Z", "2026-08-16T15:16:48Z"),
    job(95184655983, "update-release-assets", "skipped", "2026-08-16T15:17:11Z", "2026-08-16T15:17:10Z"),
)

#: develop, 2026-08-16T15:25 — the same failure eight minutes later, after an
#: attempted fix. Kept as its own fixture rather than assumed identical.
RUN_DEVELOP_RED_SECOND = run_payload(
    id=31955579431,
    name="Build & Publish Container Images",
    path=".github/workflows/docker-publish.yml",
    event="push",
    head_branch="develop",
    head_sha="d6fe6667c670f6c2c1047eb497d5632988f47f62",
    display_title="chore(deps): update the kamerplanter images to the digest published f…",
    status="completed",
    conclusion="failure",
    run_attempt=1,
    run_number=552,
    run_started_at="2026-08-16T15:24:59Z",
    updated_at="2026-08-16T15:25:27Z",
    html_url="https://github.com/nolte/kamerplanter/actions/runs/31955579431",
)

RUN_DEVELOP_RED_SECOND_JOBS = jobs_page(
    31955579431,
    job(95185603461, "changes", "success", "2026-08-16T15:25:01Z", "2026-08-16T15:25:11Z"),
    job(95185627312, "build-inference-service", "skipped", "2026-08-16T15:25:11Z", "2026-08-16T15:25:11Z"),
    job(95185627345, "build-reranker-service", "skipped", "2026-08-16T15:25:11Z", "2026-08-16T15:25:11Z"),
    job(95185627355, "build-knowledge-service", "skipped", "2026-08-16T15:25:11Z", "2026-08-16T15:25:11Z"),
    job(95185627379, "build-frontend", "skipped", "2026-08-16T15:25:11Z", "2026-08-16T15:25:11Z"),
    job(95185627384, "build-embedding-service", "skipped", "2026-08-16T15:25:11Z", "2026-08-16T15:25:11Z"),
    job(95185627389, "publish-helm-charts (kamerplanter)", "failure", "2026-08-16T15:25:13Z", "2026-08-16T15:25:26Z"),
    job(95185627406, "build-vectordb", "skipped", "2026-08-16T15:25:11Z", "2026-08-16T15:25:11Z"),
    job(95185627482, "build-backend", "skipped", "2026-08-16T15:25:11Z", "2026-08-16T15:25:11Z"),
    job(95185627570, "build-knowledge", "skipped", "2026-08-16T15:25:11Z", "2026-08-16T15:25:11Z"),
    job(95185657905, "update-release-assets", "skipped", "2026-08-16T15:25:26Z", "2026-08-16T15:25:26Z"),
)

#: v0.2.1, 2026-08-19 — the first tag run after PR #1224 repaired the chart
#: job's credentials. Everything ran; everything passed. This is the ONLY
#: recorded green run in which `publish-helm-charts (kamerplanter)` executed on
#: a tag, so it is the fixture that proves an alert can legitimately be closed.
RUN_V0_2_1_GREEN = run_payload(
    id=32259216513,
    name="Build & Publish Container Images",
    path=".github/workflows/docker-publish.yml",
    event="push",
    head_branch="v0.2.1",
    head_sha="07502fd7510dc32de2bbfdd6fd178ec2041e56a9",
    display_title="fix(helm): move the develop chart to a -dev channel so releases stop …",
    status="completed",
    conclusion="success",
    run_attempt=1,
    run_number=560,
    run_started_at="2026-08-19T13:38:11Z",
    updated_at="2026-08-19T13:53:41Z",
    html_url="https://github.com/nolte/kamerplanter/actions/runs/32259216513",
)

RUN_V0_2_1_GREEN_JOBS = jobs_page(
    32259216513,
    job(96088152790, "build-vectordb", "success", "2026-08-19T13:38:15Z", "2026-08-19T13:39:50Z"),
    job(96088153038, "build-inference-service", "success", "2026-08-19T13:38:15Z", "2026-08-19T13:41:36Z"),
    job(96088153061, "build-frontend", "success", "2026-08-19T13:38:14Z", "2026-08-19T13:40:20Z"),
    job(96088153074, "build-knowledge-service", "success", "2026-08-19T13:38:14Z", "2026-08-19T13:38:52Z"),
    job(96088153143, "build-backend", "success", "2026-08-19T13:38:15Z", "2026-08-19T13:38:58Z"),
    job(96088153148, "build-embedding-service", "success", "2026-08-19T13:38:15Z", "2026-08-19T13:42:13Z"),
    job(96088153159, "build-knowledge", "success", "2026-08-19T13:38:14Z", "2026-08-19T13:38:57Z"),
    job(96088153287, "build-reranker-service", "success", "2026-08-19T13:38:15Z", "2026-08-19T13:52:53Z"),
    job(96088153820, "changes", "skipped", "2026-08-19T13:38:12Z", "2026-08-19T13:38:12Z"),
    job(96092863479, "publish-helm-charts (kamerplanter)", "success", "2026-08-19T13:52:56Z", "2026-08-19T13:53:24Z"),
    job(96093032820, "update-release-assets", "success", "2026-08-19T13:53:27Z", "2026-08-19T13:53:40Z"),
)

#: develop, 2026-08-18T15:56 — green, and the chart job was SKIPPED. Note the
#: name: `publish-helm-charts`, WITHOUT the matrix suffix it carries when it
#: runs. This run must NOT close an alert about the chart job (R6).
RUN_DEVELOP_GREEN_CHART_SKIPPED = run_payload(
    id=32157445903,
    name="Build & Publish Container Images",
    path=".github/workflows/docker-publish.yml",
    event="push",
    head_branch="develop",
    head_sha="17aae5f58514e38771f8f2c4e4d07f3f1332c058",
    display_title="fix(ci): restore chart attestation and notice a release missing its a…",
    status="completed",
    conclusion="success",
    run_attempt=1,
    run_number=558,
    run_started_at="2026-08-18T15:56:09Z",
    updated_at="2026-08-18T15:58:15Z",
    html_url="https://github.com/nolte/kamerplanter/actions/runs/32157445903",
)

RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS = jobs_page(
    32157445903,
    job(95777961209, "changes", "success", "2026-08-18T15:56:11Z", "2026-08-18T15:56:23Z"),
    job(95778034662, "build-backend", "success", "2026-08-18T15:56:26Z", "2026-08-18T15:58:14Z"),
    job(95778035565, "build-knowledge", "skipped", "2026-08-18T15:56:23Z", "2026-08-18T15:56:23Z"),
    job(95778035789, "build-inference-service", "skipped", "2026-08-18T15:56:23Z", "2026-08-18T15:56:23Z"),
    job(95778035791, "build-knowledge-service", "skipped", "2026-08-18T15:56:23Z", "2026-08-18T15:56:23Z"),
    job(95778035802, "build-vectordb", "skipped", "2026-08-18T15:56:23Z", "2026-08-18T15:56:23Z"),
    job(95778035823, "build-frontend", "skipped", "2026-08-18T15:56:23Z", "2026-08-18T15:56:23Z"),
    job(95778035879, "build-embedding-service", "skipped", "2026-08-18T15:56:23Z", "2026-08-18T15:56:23Z"),
    job(95778036022, "build-reranker-service", "skipped", "2026-08-18T15:56:23Z", "2026-08-18T15:56:23Z"),
    job(95778626300, "publish-helm-charts", "skipped", "2026-08-18T15:58:15Z", "2026-08-18T15:58:15Z"),
    job(95778627009, "update-release-assets", "skipped", "2026-08-18T15:58:15Z", "2026-08-18T15:58:15Z"),
)

#: develop, 2026-08-18T21:38 — green, and the chart job RAN. The work package
#: named this run as the chart-skipped green develop push; the measurement says
#: otherwise (see the module docstring). Kept as the counter-fixture to
#: RUN_DEVELOP_GREEN_CHART_SKIPPED: two green develop pushes, opposite chart-job
#: outcomes, and the check has to separate them.
RUN_DEVELOP_GREEN_CHART_RAN = run_payload(
    id=32188774721,
    name="Build & Publish Container Images",
    path=".github/workflows/docker-publish.yml",
    event="push",
    head_branch="develop",
    head_sha="07502fd7510dc32de2bbfdd6fd178ec2041e56a9",
    display_title="fix(helm): move the develop chart to a -dev channel so releases stop …",
    status="completed",
    conclusion="success",
    run_attempt=1,
    run_number=559,
    run_started_at="2026-08-18T21:38:32Z",
    updated_at="2026-08-18T21:39:49Z",
    html_url="https://github.com/nolte/kamerplanter/actions/runs/32188774721",
)

RUN_DEVELOP_GREEN_CHART_RAN_JOBS = jobs_page(
    32188774721,
    job(95878342222, "changes", "success", "2026-08-18T21:38:34Z", "2026-08-18T21:38:42Z"),
    job(95878386020, "build-backend", "success", "2026-08-18T21:38:45Z", "2026-08-18T21:39:26Z"),
    job(95878386820, "build-embedding-service", "skipped", "2026-08-18T21:38:43Z", "2026-08-18T21:38:43Z"),
    job(95878386846, "build-inference-service", "skipped", "2026-08-18T21:38:43Z", "2026-08-18T21:38:43Z"),
    job(95878386934, "build-knowledge", "skipped", "2026-08-18T21:38:43Z", "2026-08-18T21:38:43Z"),
    job(95878386971, "build-knowledge-service", "skipped", "2026-08-18T21:38:43Z", "2026-08-18T21:38:43Z"),
    job(95878387013, "build-frontend", "skipped", "2026-08-18T21:38:43Z", "2026-08-18T21:38:43Z"),
    job(95878387144, "build-vectordb", "skipped", "2026-08-18T21:38:43Z", "2026-08-18T21:38:43Z"),
    job(95878387368, "build-reranker-service", "skipped", "2026-08-18T21:38:43Z", "2026-08-18T21:38:43Z"),
    job(95878577422, "publish-helm-charts (kamerplanter)", "success", "2026-08-18T21:39:29Z", "2026-08-18T21:39:48Z"),
    job(95878672756, "update-release-assets", "skipped", "2026-08-18T21:39:49Z", "2026-08-18T21:39:48Z"),
)

#: 2026-08-18 — a real CANCELLED run. It belongs to `Security — Nuclei
#: Post-Merge Scan`, not to the delivery lane, because no delivery-lane run has
#: ever been cancelled (`…/workflows/246887462/runs?status=cancelled` is empty).
#: It therefore carries the `is_expected_workflow: false` case for free.
RUN_NUCLEI_CANCELLED = run_payload(
    id=32188774700,
    name="Security — Nuclei Post-Merge Scan",
    path=".github/workflows/security-nuclei-postmerge.yml",
    event="push",
    head_branch="develop",
    head_sha="07502fd7510dc32de2bbfdd6fd178ec2041e56a9",
    display_title="fix(helm): move the develop chart to a -dev channel so releases stop …",
    status="completed",
    conclusion="cancelled",
    run_attempt=1,
    run_number=425,
    run_started_at="2026-08-18T21:38:32Z",
    updated_at="2026-08-18T22:13:35Z",
    html_url="https://github.com/nolte/kamerplanter/actions/runs/32188774700",
)

RUN_NUCLEI_CANCELLED_JOBS = jobs_page(
    32188774700,
    job(95878341880, "Nuclei Scan (fast profile)", "cancelled", "2026-08-18T21:38:34Z", "2026-08-18T22:13:34Z"),
)
#: Every recorded fixture, paired with the name its failure would carry in a
#: parametrised test id.
RED_FIXTURES = [
    ("v0.2.0-tag", RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS),
    ("develop-15:16", RUN_DEVELOP_RED_FIRST, RUN_DEVELOP_RED_FIRST_JOBS),
    ("develop-15:25", RUN_DEVELOP_RED_SECOND, RUN_DEVELOP_RED_SECOND_JOBS),
]

GREEN_FIXTURES = [
    ("v0.2.1-tag-chart-ran", RUN_V0_2_1_GREEN, RUN_V0_2_1_GREEN_JOBS),
    ("develop-chart-skipped", RUN_DEVELOP_GREEN_CHART_SKIPPED, RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS),
    ("develop-chart-ran", RUN_DEVELOP_GREEN_CHART_RAN, RUN_DEVELOP_GREEN_CHART_RAN_JOBS),
]

ALL_FIXTURES = [
    *RED_FIXTURES,
    *GREEN_FIXTURES,
    ("cancelled", RUN_NUCLEI_CANCELLED, RUN_NUCLEI_CANCELLED_JOBS),
]


# --------------------------------------------------------------------------- #
# The incident: three red runs that alerted nobody.
# --------------------------------------------------------------------------- #


class TestTheIncident:
    """The three measured red runs must each produce an alert that names the job."""

    def test_the_v0_2_0_tag_run_alerts_and_names_the_chart_job(self) -> None:
        """31729355999: the release that lost its chart, as measured."""
        report = judge(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS)

        assert report["verdict"] == "alert"
        assert report["alert"] is True
        assert report["resolved"] is False
        assert report["failed_jobs"] == [CHART_JOB_RAN]

    def test_the_v0_2_0_run_separates_the_skipped_victim_from_the_successes(self) -> None:
        """`update-release-assets` was SKIPPED, not failed — the whole point of #1218.

        A check that lumped skipped in with succeeded would report nine passing
        jobs and hide the artefact loss; one that lumped it in with failed would
        alert about a job that never ran.
        """
        report = judge(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS)

        assert "update-release-assets" in report["skipped_jobs"]
        assert "update-release-assets" not in report["succeeded_jobs"]
        assert "update-release-assets" not in report["failed_jobs"]
        # `changes` is skipped on a tag run by its own `if: github.ref_type == 'branch'`.
        assert sorted(report["skipped_jobs"]) == ["changes", "update-release-assets"]
        assert len(report["succeeded_jobs"]) == 8
        assert all(name.startswith("build-") for name in report["succeeded_jobs"])

    @pytest.mark.parametrize(
        ("run", "jobs"),
        [(run, jobs) for _, run, jobs in RED_FIXTURES],
        ids=[name for name, _, _ in RED_FIXTURES],
    )
    def test_every_measured_red_run_alerts_about_the_chart_job(self, run: dict[str, Any], jobs: dict[str, Any]) -> None:
        """All three, not just the newest: the failure was systematic, not intermittent."""
        report = judge(run, jobs)

        assert report["alert"] is True
        assert report["resolved"] is False
        assert report["failed_jobs"] == [CHART_JOB_RAN]

    def test_a_develop_red_run_shows_every_build_skipped(self) -> None:
        """31955164085: a `helm/**`-only push, so only `changes` and the chart job ran.

        This is the shape that makes the lane LOOK intermittent — eight skipped
        builds and one real failure — and the report has to say which is which.
        """
        report = judge(RUN_DEVELOP_RED_FIRST, RUN_DEVELOP_RED_FIRST_JOBS)

        assert report["succeeded_jobs"] == ["changes"]
        assert len(report["skipped_jobs"]) == 9
        assert CHART_JOB_RAN not in report["skipped_jobs"]

    def test_the_report_carries_the_run_facts_the_alert_body_needs(self) -> None:
        """Every field the observer workflow renders, pinned against the measurement."""
        report = judge(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS, now="2026-08-13T18:31:18Z")

        assert report["run_id"] == 31729355999
        assert report["html_url"] == "https://github.com/nolte/kamerplanter/actions/runs/31729355999"
        assert report["workflow_name"] == DELIVERY_WORKFLOW
        assert report["workflow_path"] == ".github/workflows/docker-publish.yml"
        assert report["is_expected_workflow"] is True
        assert report["event"] == "push"
        assert report["head_branch"] == "v0.2.0"
        assert report["head_sha"] == "474e37ceb7da379b4379cee4529a97b200a134bb"
        assert report["run_attempt"] == 1
        assert report["run_number"] == 504
        assert report["conclusion"] == "failure"
        assert report["run_started_at"] == "2026-08-13T18:09:50+00:00"
        assert report["updated_at"] == "2026-08-13T18:21:18+00:00"
        assert report["duration_seconds"] == 688.0
        assert report["age_minutes"] == 10.0
        assert report["job_count"] == 11
        assert report["repository"] == REPOSITORY

    def test_a_tag_run_is_recognised_as_a_tag_although_the_api_calls_it_a_branch(self) -> None:
        """`head_branch` carries the TAG NAME on a tag run — measured, not assumed."""
        assert RUN_V0_2_0_RED["head_branch"] == "v0.2.0"

        assert judge(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS)["ref_kind"] == "tag"
        assert judge(RUN_DEVELOP_RED_FIRST, RUN_DEVELOP_RED_FIRST_JOBS)["ref_kind"] == "branch"

    def test_the_check_requests_exactly_the_two_documented_endpoints(self) -> None:
        """No hidden third call, and the jobs page is requested with per_page=100."""
        fetch = serving(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS)

        build(fetch, run_id=31729355999)

        assert fetch.urls == [run_url(31729355999), jobs_url(31729355999)]


# --------------------------------------------------------------------------- #
# The green runs — and the distinction the no-flap rule turns on.
# --------------------------------------------------------------------------- #


class TestTheGreenRuns:
    """A green run resolves, and says whether the job that broke actually ran."""

    def test_the_v0_2_1_run_resolves_with_the_chart_job_among_the_successes(self) -> None:
        """32259216513: the chart job RAN and passed, so an alert may be closed."""
        report = judge(RUN_V0_2_1_GREEN, RUN_V0_2_1_GREEN_JOBS)

        assert report["verdict"] == "resolved"
        assert report["resolved"] is True
        assert report["alert"] is False
        assert report["failed_jobs"] == []
        assert CHART_JOB_RAN in report["succeeded_jobs"]
        assert CHART_JOB_RAN not in report["skipped_jobs"]
        assert CHART_JOB_SKIPPED not in report["skipped_jobs"]
        assert "update-release-assets" in report["succeeded_jobs"]

    def test_a_green_develop_push_that_skipped_the_chart_job_proves_nothing_about_it(self) -> None:
        """32157445903: green, and the chart job did NOT run.

        The run is a legitimate `resolved` — nothing failed — but the job the
        alert is about is in `skipped_jobs`, under its unexpanded matrix name.
        R6's closing rule reads exactly this difference.
        """
        report = judge(RUN_DEVELOP_GREEN_CHART_SKIPPED, RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS)

        assert report["resolved"] is True
        assert report["alert"] is False
        assert CHART_JOB_SKIPPED in report["skipped_jobs"]
        assert CHART_JOB_RAN not in report["succeeded_jobs"]
        assert CHART_JOB_SKIPPED not in report["succeeded_jobs"]
        assert report["succeeded_jobs"] == ["changes", "build-backend"]

    def test_the_run_the_work_package_believed_had_a_skipped_chart_job_actually_ran_it(self) -> None:
        """32188774721, REFUTED: P1's brief called this the chart-skipped green push.

        It is not. Recorded with `gh api .../runs/32188774721/jobs?per_page=100`,
        `publish-helm-charts (kamerplanter)` completed with conclusion `success`.
        The assertion is kept — and named — so the refutation stays measured
        rather than remembered, and so the pair with 32157445903 documents that
        two green develop pushes can differ on precisely this.
        """
        report = judge(RUN_DEVELOP_GREEN_CHART_RAN, RUN_DEVELOP_GREEN_CHART_RAN_JOBS)

        assert report["resolved"] is True
        assert CHART_JOB_RAN in report["succeeded_jobs"]
        assert CHART_JOB_SKIPPED not in report["skipped_jobs"]
        # …while `update-release-assets` still skipped: it is tag-only.
        assert "update-release-assets" in report["skipped_jobs"]

    def test_the_matrix_suffix_is_stripped_into_a_join_key(self) -> None:
        """The executed and the skipped name have to be joinable, or R6 cannot compare.

        Measured asymmetry: `publish-helm-charts (kamerplanter)` when it runs,
        `publish-helm-charts` when it is skipped. `base_name` is the only field
        that lets a consumer see they are the same job.
        """
        ran = judge(RUN_V0_2_1_GREEN, RUN_V0_2_1_GREEN_JOBS)
        skipped = judge(RUN_DEVELOP_GREEN_CHART_SKIPPED, RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS)

        ran_entry = next(entry for entry in ran["jobs"] if entry["name"] == CHART_JOB_RAN)
        skipped_entry = next(entry for entry in skipped["jobs"] if entry["name"] == CHART_JOB_SKIPPED)

        assert ran_entry["base_name"] == CHART_JOB_SKIPPED
        assert skipped_entry["base_name"] == CHART_JOB_SKIPPED
        assert ran_entry["base_name"] == skipped_entry["base_name"]

    def test_each_job_entry_carries_its_measured_url_and_timestamps(self) -> None:
        """The alert body links the failing job directly, not just the run."""
        report = judge(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS)

        entry = next(item for item in report["jobs"] if item["name"] == CHART_JOB_RAN)
        assert entry["conclusion"] == "failure"
        assert entry["status"] == "completed"
        assert entry["url"] == "https://github.com/nolte/kamerplanter/actions/runs/31729355999/job/94548618061"
        assert entry["started_at"] == "2026-08-13T18:20:56Z"
        assert entry["completed_at"] == "2026-08-13T18:21:17Z"


# --------------------------------------------------------------------------- #
# R6 — the closing rule the report has to make expressible.
# --------------------------------------------------------------------------- #


def would_close(report: dict[str, Any], recorded_failures: list[str]) -> bool:
    """The closing rule of requirement R6, expressed against the report schema.

    NOT a copy of shipped code, and it is not the observer workflow either. This
    is the *contract* the report schema has to make expressible — if the report
    cannot answer "did every job that failed run and succeed again?", R6 cannot
    be implemented on top of it. The observer workflow (P2,
    `.github/workflows/delivery-run-alert.yml`) exists and is its own subject:
    its `actions/github-script` body is executed verbatim under node in
    `test_delivery_run_alert_workflow.py`, the way `test_release_assets_check.py`
    does it. This helper does not stand in for that coverage, and predates it —
    the tests below must not be read as exercising the shipped closing logic.
    """
    return report["resolved"] and all(name in report["succeeded_jobs"] for name in recorded_failures)


class TestTheClosingRuleCannotFlap:
    """A green run closes the alert only if it actually re-ran the broken job."""

    def test_the_alert_from_the_red_tag_run_closes_on_the_green_tag_run(self) -> None:
        """The recorded failure set is satisfied by 32259216513 — close it."""
        recorded = judge(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS)["failed_jobs"]

        assert would_close(judge(RUN_V0_2_1_GREEN, RUN_V0_2_1_GREEN_JOBS), recorded) is True

    def test_the_same_alert_survives_a_green_run_that_skipped_the_chart_job(self) -> None:
        """32157445903 is green and proves nothing — the alert must stay open."""
        recorded = judge(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS)["failed_jobs"]
        report = judge(RUN_DEVELOP_GREEN_CHART_SKIPPED, RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS)

        assert report["resolved"] is True
        assert would_close(report, recorded) is False

    def test_the_report_lets_the_workflow_say_why_it_is_not_closing(self) -> None:
        """ "Skipped in the green run" and "gone from the run entirely" differ.

        Matching the recorded name against `skipped_jobs` finds nothing, because
        of the matrix-suffix asymmetry; matching on `base_name` finds it. Without
        that field the workflow could only report the weaker, and wrong, "the job
        no longer exists".
        """
        recorded = judge(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS)["failed_jobs"]
        report = judge(RUN_DEVELOP_GREEN_CHART_SKIPPED, RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS)

        assert [name for name in recorded if name in report["skipped_jobs"]] == []

        bases = {entry["base_name"] for entry in report["jobs"] if entry["conclusion"] == "skipped"}
        assert {checker.MATRIX_SUFFIX_PATTERN.sub("", name) for name in recorded} <= bases

    def test_an_alert_naming_no_job_would_close_vacuously_and_must_be_guarded(self) -> None:
        """A red run whose jobs all passed: `failed_jobs` is empty, honestly.

        GitHub can conclude a run `failure` with no job carrying a failing
        conclusion — a workflow-level error, or a failure on an earlier attempt
        while this endpoint reports the latest one. The payload here is the
        recorded 32157445903 with its run conclusion swapped to `failure`, which
        is that shape.

        The check reports the empty list rather than back-filling it, and this
        test pins the consequence: `all(... for name in [])` is TRUE, so the
        closing rule would close such an alert on the very next green run having
        verified nothing. P2 must treat an empty recorded set as "unknown job
        set" — which is why the script's docstring says so in as many words.
        """
        red_without_a_failing_job = replacing(RUN_DEVELOP_GREEN_CHART_SKIPPED, conclusion="failure")
        report = judge(red_without_a_failing_job, RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS)

        assert report["alert"] is True
        assert report["failed_jobs"] == []
        assert would_close(judge(RUN_V0_2_1_GREEN, RUN_V0_2_1_GREEN_JOBS), report["failed_jobs"]) is True


# --------------------------------------------------------------------------- #
# Inconclusive: determined about the run, silent about the lane.
# --------------------------------------------------------------------------- #


class TestInconclusive:
    """Neither alert nor resolution — the workflow leaves the issue alone."""

    def test_a_cancelled_run_is_neither(self) -> None:
        """32188774700, a real cancelled run: an operator act, not a broken lane."""
        report = judge(RUN_NUCLEI_CANCELLED, RUN_NUCLEI_CANCELLED_JOBS, now="2026-08-19T00:00:00Z")

        assert report["verdict"] == "inconclusive"
        assert report["alert"] is False
        assert report["resolved"] is False
        assert report["conclusion"] == "cancelled"
        assert report["cancelled_jobs"] == ["Nuclei Scan (fast profile)"]

    def test_a_run_of_another_workflow_is_reported_not_rejected(self) -> None:
        """A `workflow_dispatch` may hand over any run id; the workflow decides.

        The cancelled fixture belongs to `Security — Nuclei Post-Merge Scan`, so
        this case comes from a real payload rather than a doctored one.
        """
        report = judge(RUN_NUCLEI_CANCELLED, RUN_NUCLEI_CANCELLED_JOBS, now="2026-08-19T00:00:00Z")

        assert report["workflow_name"] == "Security — Nuclei Post-Merge Scan"
        assert report["expected_workflow"] == DELIVERY_WORKFLOW
        assert report["is_expected_workflow"] is False

    @pytest.mark.parametrize("conclusion", ["neutral", "skipped", "action_required", "stale"])
    def test_the_remaining_soft_conclusions_are_inconclusive(self, conclusion: str) -> None:
        """The only swapped values in this module, and the reason is measurable.

        No run in this repository has ever concluded `neutral`, `action_required`
        or `stale`, so there is nothing to record; the value is swapped onto the
        recorded green develop payload and nothing else about it is invented.
        """
        report = judge(
            replacing(RUN_DEVELOP_GREEN_CHART_SKIPPED, conclusion=conclusion),
            RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS,
        )

        assert report["verdict"] == "inconclusive"
        assert report["alert"] is False
        assert report["resolved"] is False

    def test_an_unknown_conclusion_raises_rather_than_reading_as_inconclusive(self) -> None:
        """ "We do not know" is not the determined fact "neither failed nor passed".

        Folding an unrecognised value into `inconclusive` would make a future
        GitHub conclusion silently unobservable — the exact substitution NFR-018
        §2 forbids.
        """
        payload = replacing(RUN_V0_2_1_GREEN, conclusion="mostly_fine")

        with pytest.raises(checker.DeliveryRunError, match="unknown conclusion"):
            judge(payload, RUN_V0_2_1_GREEN_JOBS)


# --------------------------------------------------------------------------- #
# Fail loud (NFR-018 §2).
# --------------------------------------------------------------------------- #


class TestFailLoud:
    """Everything undetermined raises; nothing degrades into a verdict."""

    @pytest.mark.parametrize("status", ["queued", "in_progress", "waiting", "requested", "pending"])
    def test_a_run_that_is_not_completed_raises(self, status: str) -> None:
        """The observer fires on `types: [completed]`, but a dispatch can be early."""
        payload = replacing(RUN_V0_2_1_GREEN, status=status, conclusion=None)

        with pytest.raises(checker.DeliveryRunError, match="not 'completed'"):
            judge(payload, RUN_V0_2_1_GREEN_JOBS)

    def test_a_completed_run_without_a_conclusion_raises(self) -> None:
        """An impossible-looking state that must not become "no failure reported"."""
        with pytest.raises(checker.DeliveryRunError, match="without a conclusion"):
            judge(replacing(RUN_V0_2_1_GREEN, conclusion=None), RUN_V0_2_1_GREEN_JOBS)

    @pytest.mark.parametrize("field", ["status", "conclusion"])
    def test_a_run_payload_missing_a_verdict_field_raises(self, field: str) -> None:
        """A missing KEY is an API shape change, not an all-clear."""
        with pytest.raises(checker.DeliveryRunError, match=f"carries no {field} field"):
            judge(without(RUN_V0_2_1_GREEN, field), RUN_V0_2_1_GREEN_JOBS)

    def test_a_run_payload_that_is_not_an_object_raises(self) -> None:
        fetch = RecordingFetch({run_url(1): ["not", "a", "run"]})

        with pytest.raises(checker.DeliveryRunError, match="not a JSON object"):
            build(fetch, run_id=1)

    def test_an_http_error_on_the_run_endpoint_raises(self) -> None:
        """Red run, no report, therefore no issue — and no tracker spam."""
        fetch = RecordingFetch({run_url(31729355999): checker.DeliveryRunError("GET … failed: HTTP 503")})

        with pytest.raises(checker.DeliveryRunError, match="HTTP 503"):
            build(fetch, run_id=31729355999)

    def test_an_http_error_on_the_jobs_endpoint_raises(self) -> None:
        """The run alone is not enough: an alert with no job list names nothing."""
        fetch = RecordingFetch(
            {
                run_url(31729355999): RUN_V0_2_0_RED,
                jobs_url(31729355999): checker.DeliveryRunError("GET … failed: HTTP 502"),
            }
        )

        with pytest.raises(checker.DeliveryRunError, match="HTTP 502"):
            build(fetch, run_id=31729355999)

    def test_a_jobs_payload_without_a_jobs_array_raises(self) -> None:
        """`{"total_count": 11}` with no array is not "no jobs failed"."""
        with pytest.raises(checker.DeliveryRunError, match="carries no jobs array"):
            judge(RUN_V0_2_0_RED, without(RUN_V0_2_0_RED_JOBS, "jobs"))

    def test_a_jobs_payload_without_a_total_count_raises(self) -> None:
        """Without it there is nothing to check the page against."""
        with pytest.raises(checker.DeliveryRunError, match="no integer total_count"):
            judge(RUN_V0_2_0_RED, without(RUN_V0_2_0_RED_JOBS, "total_count"))

    def test_a_green_run_with_no_jobs_at_all_raises(self) -> None:
        """Refusing to CERTIFY the lane against nothing.

        The asymmetry with the alerting case below is the point: "the run went
        red" survives an empty job list, "every job that had failed ran and
        succeeded" does not.
        """
        with pytest.raises(checker.DeliveryRunError, match="carries no jobs"):
            judge(RUN_V0_2_1_GREEN, jobs_page(32259216513))

    def test_a_job_without_a_conclusion_raises(self) -> None:
        """An unclassifiable job silently dropped would shrink `succeeded_jobs`."""
        broken = deepcopy(RUN_V0_2_0_RED_JOBS)
        broken["jobs"][9]["conclusion"] = None
        broken["jobs"][9]["status"] = "in_progress"

        with pytest.raises(checker.DeliveryRunError, match="cannot be classified"):
            judge(RUN_V0_2_0_RED, broken)

    def test_a_job_without_a_name_raises(self) -> None:
        broken = deepcopy(RUN_V0_2_0_RED_JOBS)
        broken["jobs"][0].pop("name")

        with pytest.raises(checker.DeliveryRunError, match="has no name"):
            judge(RUN_V0_2_0_RED, broken)

    def test_a_job_that_is_not_an_object_raises(self) -> None:
        broken = deepcopy(RUN_V0_2_0_RED_JOBS)
        broken["jobs"][0] = "publish-helm-charts"

        with pytest.raises(checker.DeliveryRunError, match="is not an object"):
            judge(RUN_V0_2_0_RED, broken)

    def test_a_page_carrying_fewer_jobs_than_it_claims_is_not_judged_on(self) -> None:
        """A truncated job list is how a check starts certifying nothing.

        The check does not judge the five jobs it got: it asks for the next page,
        and an empty one leaves it unable to account for the six the endpoint
        promised. Judging the partial list would let a green verdict rest on the
        jobs that happened to fit on page one.
        """
        truncated = deepcopy(RUN_V0_2_0_RED_JOBS)
        truncated["jobs"] = truncated["jobs"][:5]
        fetch = RecordingFetch(
            {
                run_url(31729355999): RUN_V0_2_0_RED,
                jobs_url(31729355999, 1): truncated,
                jobs_url(31729355999, 2): jobs_page(31729355999, total_count=11),
            }
        )

        with pytest.raises(checker.DeliveryRunError, match="page 2 is empty"):
            build(fetch, run_id=31729355999)

    def test_a_page_carrying_more_jobs_than_it_claims_raises(self) -> None:
        """The other direction of the same inconsistency, and just as undetermined."""
        inflated = deepcopy(RUN_V0_2_0_RED_JOBS)
        inflated["total_count"] = 9

        with pytest.raises(checker.DeliveryRunError, match="read 11 job\\(s\\) but the endpoint reports 9"):
            judge(RUN_V0_2_0_RED, inflated)

    def test_a_run_answering_with_a_different_id_raises(self) -> None:
        """A redirect or a copy-paste error must not judge somebody else's run."""
        fetch = RecordingFetch({run_url(4242): RUN_V0_2_0_RED, jobs_url(4242): RUN_V0_2_0_RED_JOBS})

        with pytest.raises(checker.DeliveryRunError, match="answered with run 31729355999"):
            build(fetch, run_id=4242)

    @pytest.mark.parametrize("field", ["run_started_at", "updated_at"])
    def test_a_missing_timestamp_raises(self, field: str) -> None:
        """No fallback to "now": the duration would be invented, and read as measured."""
        with pytest.raises(checker.DeliveryRunError, match=f"{field}: missing timestamp"):
            judge(replacing(RUN_V0_2_1_GREEN, **{field: None}), RUN_V0_2_1_GREEN_JOBS)

    def test_an_unparseable_timestamp_raises(self) -> None:
        with pytest.raises(checker.DeliveryRunError, match="unparseable timestamp"):
            judge(replacing(RUN_V0_2_1_GREEN, updated_at="yesterday"), RUN_V0_2_1_GREEN_JOBS)


class TestARunThatNeverStartedAJob:
    """`startup_failure` — the most systematic lane breakage, and it has no jobs.

    A run that dies before any job starts (an invalid `if:`, a YAML error) ends
    as `startup_failure` with `"total_count": 0` on its jobs endpoint. Measured
    by the reviewer on runs 32202729898 (nolte/gh-plumbing) and 26304512675
    (nolte/claude-shared). Refusing to judge that shape would leave the worst
    case unobserved, which is the hole this whole check exists to close.

    The payload here is the recorded develop failure with its conclusion set to
    `startup_failure` and an EMPTY jobs page — the two fields the measurement
    established, and nothing else invented.
    """

    def test_a_startup_failure_without_jobs_still_alerts(self) -> None:
        payload = replacing(RUN_DEVELOP_RED_FIRST, conclusion="startup_failure")

        report = judge(payload, jobs_page(RUN_DEVELOP_RED_FIRST["id"]))

        assert report["alert"] is True
        assert report["resolved"] is False
        assert report["failed_jobs"] == []
        assert report["job_count"] == 0
        assert report["jobs"] == []

    def test_the_lane_half_is_still_known_so_the_alert_can_be_closed_later(self) -> None:
        """Without `lane_ref` such an alert could never be resolved."""
        payload = replacing(RUN_DEVELOP_RED_FIRST, conclusion="startup_failure")

        assert judge(payload, jobs_page(RUN_DEVELOP_RED_FIRST["id"]))["lane_ref"] == "develop"

    @pytest.mark.parametrize("conclusion", ["failure", "timed_out", "startup_failure"])
    def test_every_alerting_conclusion_tolerates_an_empty_job_list(self, conclusion: str) -> None:
        payload = replacing(RUN_DEVELOP_RED_FIRST, conclusion=conclusion)

        assert judge(payload, jobs_page(RUN_DEVELOP_RED_FIRST["id"]))["alert"] is True

    def test_an_inconclusive_run_without_jobs_is_also_reported(self) -> None:
        """A run cancelled in its first seconds has no jobs either, and saying
        "cancelled" about it is still a determined fact."""
        payload = replacing(RUN_DEVELOP_RED_FIRST, conclusion="cancelled")

        report = judge(payload, jobs_page(RUN_DEVELOP_RED_FIRST["id"]))

        assert report["verdict"] == "inconclusive"
        assert report["job_count"] == 0


class TestWhichHalfOfTheLaneARunBelongsTo:
    """`lane_ref` — the field a closing decision may read, unlike `ref_kind`.

    `docker-publish.yml` carries an unrestricted `workflow_dispatch:` and its
    `publish-helm-charts` job runs unconditionally there, so a dispatch on a
    feature branch produces a green run in which the failing job "ran and
    succeeded". And the two halves are not interchangeable: that job's `Upload
    chart as release asset` step runs only on a tag, so a green `develop` run
    executes the same job NAME with fewer steps.

    The dispatch rows are derived — `…/workflows/246887462/runs?event=workflow_dispatch`
    returns `total_count: 0`, there has never been one — by replacing exactly
    `event` and `head_branch` on a recorded payload.
    """

    @pytest.mark.parametrize(
        ("event", "head_branch", "expected"),
        [
            ("push", "develop", "develop"),
            ("push", "v0.2.0", "tag"),
            ("push", "v0.2.1-rc1", "tag"),
            ("workflow_dispatch", "develop", "develop"),
            ("workflow_dispatch", "v0.2.1", "tag"),
            ("workflow_dispatch", "fix/xyz", None),
            ("workflow_dispatch", "v2", None),
            ("schedule", "develop", None),
        ],
        ids=[
            "push-develop",
            "push-tag",
            "push-prerelease-tag",
            "dispatch-develop",
            "dispatch-tag",
            "dispatch-feature-branch",
            "dispatch-tag-outside-the-convention",
            "another-event",
        ],
    )
    def test_the_lane_half_is_derived_from_the_trigger_list(
        self, event: str, head_branch: str, expected: str | None
    ) -> None:
        payload = replacing(RUN_V0_2_1_GREEN, event=event, head_branch=head_branch)

        assert judge(payload, RUN_V0_2_1_GREEN_JOBS)["lane_ref"] == expected

    def test_a_push_is_classified_by_branch_name_not_by_the_tag_heuristic(self) -> None:
        """`on.push` accepts `[develop]` and `v*` and nothing else.

        So a push that is not on `develop` is a tag push — including a tag whose
        name the `ref_kind` heuristic does not recognise. Deciding a push by the
        heuristic instead would file `v2` under `develop`.
        """
        payload = replacing(RUN_V0_2_1_GREEN, event="push", head_branch="v2")
        report = judge(payload, RUN_V0_2_1_GREEN_JOBS)

        assert report["lane_ref"] == "tag"
        assert report["ref_kind"] == "branch"

    def test_the_recorded_runs_land_on_the_half_they_came_from(self) -> None:
        assert judge(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS)["lane_ref"] == "tag"
        assert judge(RUN_DEVELOP_RED_FIRST, RUN_DEVELOP_RED_FIRST_JOBS)["lane_ref"] == "develop"
        assert judge(RUN_V0_2_1_GREEN, RUN_V0_2_1_GREEN_JOBS)["lane_ref"] == "tag"
        assert judge(RUN_DEVELOP_GREEN_CHART_SKIPPED, RUN_DEVELOP_GREEN_CHART_SKIPPED_JOBS)["lane_ref"] == "develop"


class TestTheRunIdIsValidatedBeforeAnyRequest:
    """`${{ github.event.workflow_run.id }}` renders empty when the event is not what the workflow assumed."""

    @pytest.mark.parametrize("value", ["", "   ", "not-a-number", "31729355999abc", "3.14", "-1", "0x10"])
    def test_a_non_integer_run_id_raises(self, value: str) -> None:
        with pytest.raises(checker.DeliveryRunError):
            checker.parse_run_id(value)

    @pytest.mark.parametrize(("value", "message"), [(0, "positive"), (-5, "integer"), ("-5", "integer")])
    def test_a_non_positive_run_id_raises(self, value: Any, message: str) -> None:
        """A negative id fails on the digit check first — both messages are refusals."""
        with pytest.raises(checker.DeliveryRunError, match=message):
            checker.parse_run_id(value)

    @pytest.mark.parametrize("value", [None, True, 3.5, ["31729355999"]])
    def test_a_run_id_of_the_wrong_type_raises(self, value: Any) -> None:
        with pytest.raises(checker.DeliveryRunError, match="integer|no run id"):
            checker.parse_run_id(value)

    @pytest.mark.parametrize("value", ["31729355999", " 31729355999 ", 31729355999])
    def test_a_well_formed_run_id_is_accepted(self, value: Any) -> None:
        assert checker.parse_run_id(value) == 31729355999


# --------------------------------------------------------------------------- #
# Pagination — the lane has 11 jobs, so this shape is constructed.
# --------------------------------------------------------------------------- #


def synthetic_jobs(run_id: int, count: int, *, page: int, total: int) -> dict[str, Any]:
    """One page of *count* jobs shaped like the recorded ones.

    Explicitly CONSTRUCTED, not recorded: the delivery lane has 11 jobs and no
    run in this repository has ever paginated. The field shape is copied from
    the recorded payloads; only the volume is invented, and volume is the single
    thing these two tests are about.
    """
    offset = (page - 1) * 100
    return jobs_page(
        run_id,
        *[
            job(
                900000 + offset + index,
                f"build-shard-{offset + index}",
                "success",
                "2026-08-19T13:38:15Z",
                "2026-08-19T13:39:50Z",
            )
            for index in range(count)
        ],
        total_count=total,
    )


class TestPagination:
    """A matrix larger than one page must not silently truncate the verdict."""

    def test_a_second_page_is_fetched_and_merged(self) -> None:
        run = replacing(RUN_V0_2_1_GREEN, id=999, html_url="https://github.com/nolte/kamerplanter/actions/runs/999")
        fetch = RecordingFetch(
            {
                run_url(999): run,
                jobs_url(999, 1): synthetic_jobs(999, 100, page=1, total=150),
                jobs_url(999, 2): synthetic_jobs(999, 50, page=2, total=150),
            }
        )

        report = build(fetch, run_id=999)

        assert report["job_count"] == 150
        assert len(report["succeeded_jobs"]) == 150
        assert fetch.urls == [run_url(999), jobs_url(999, 1), jobs_url(999, 2)]

    def test_a_second_page_that_comes_back_empty_raises(self) -> None:
        """The endpoint promised 150 and delivered 100 — that is not "150 passed"."""
        run = replacing(RUN_V0_2_1_GREEN, id=999, html_url="https://github.com/nolte/kamerplanter/actions/runs/999")
        fetch = RecordingFetch(
            {
                run_url(999): run,
                jobs_url(999, 1): synthetic_jobs(999, 100, page=1, total=150),
                jobs_url(999, 2): synthetic_jobs(999, 0, page=2, total=150),
            }
        )

        with pytest.raises(checker.DeliveryRunError, match="page 2 is empty"):
            build(fetch, run_id=999)


class TestTheHttpLayerTurnsEveryTransportFailureIntoADomainError:
    """`api_json` is the only place a raw exception could escape.

    `URLError` covers a DNS or connect failure, but a socket dying mid-response
    does not go through it: a read timeout arrives as `TimeoutError` and a
    truncated chunked body as `http.client.IncompleteRead`, which is an
    `HTTPException` and NOT an `OSError`. Either escaping raw would still fail
    the run — without the `::error::` annotation and without naming the URL.
    """

    @pytest.mark.parametrize(
        "error",
        [
            TimeoutError("timed out"),
            ConnectionResetError("connection reset by peer"),
            http.client.IncompleteRead(b"partial"),
            http.client.RemoteDisconnected("remote end closed connection"),
            OSError("network is unreachable"),
        ],
        ids=["read-timeout", "connection-reset", "incomplete-read", "remote-disconnected", "oserror"],
    )
    def test_a_transport_failure_becomes_a_delivery_run_error(
        self, error: Exception, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def explode(*args: Any, **kwargs: Any) -> Any:
            raise error

        monkeypatch.setattr(checker.urllib.request, "urlopen", explode)

        with pytest.raises(checker.DeliveryRunError, match="failed"):
            checker.api_json("https://api.github.com/repos/x/y/actions/runs/1")

    def test_an_http_status_keeps_its_more_specific_message(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HTTPError is an OSError subclass; the wider clause must not swallow it."""

        def explode(*args: Any, **kwargs: Any) -> Any:
            raise urllib.error.HTTPError("https://api.github.com/x", 403, "Forbidden", {}, None)  # type: ignore[arg-type]

        monkeypatch.setattr(checker.urllib.request, "urlopen", explode)

        with pytest.raises(checker.DeliveryRunError, match="HTTP 403"):
            checker.api_json("https://api.github.com/repos/x/y/actions/runs/1")

    def test_the_error_names_the_url_that_died(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A red observer run has to say WHICH read failed to be diagnosable."""

        def explode(*args: Any, **kwargs: Any) -> Any:
            raise TimeoutError("timed out")

        monkeypatch.setattr(checker.urllib.request, "urlopen", explode)

        with pytest.raises(checker.DeliveryRunError, match="actions/runs/31729355999"):
            checker.api_json("https://api.github.com/repos/nolte/kamerplanter/actions/runs/31729355999")


# --------------------------------------------------------------------------- #
# The entry point: the report file is the workflow's contract.
# --------------------------------------------------------------------------- #


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin every environment input main() reads, so the run is deterministic."""
    monkeypatch.setenv("GITHUB_REPOSITORY", REPOSITORY)
    monkeypatch.delenv("DELIVERY_RUN_ID", raising=False)
    monkeypatch.delenv("DELIVERY_WORKFLOW_NAME", raising=False)


@pytest.mark.usefixtures("clean_env")
class TestMain:
    """Present iff determined — inconclusive included, because that IS a fact."""

    def test_a_red_run_writes_the_report_and_exits_zero(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DELIVERY_RUN_ID", "31729355999")
        target = tmp_path / "delivery-run-report.json"

        exit_code = checker.main(
            [str(target)],
            fetch=serving(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS),
            now=at("2026-08-13T18:31:18Z"),
        )

        assert exit_code == 0
        report = json.loads(target.read_text(encoding="utf-8"))
        assert report["alert"] is True
        assert report["failed_jobs"] == [CHART_JOB_RAN]

    def test_the_command_line_run_id_wins_over_the_environment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A dispatch passes `--run-id`; the `workflow_run` trigger passes the env var."""
        monkeypatch.setenv("DELIVERY_RUN_ID", "31729355999")
        target = tmp_path / "report.json"

        checker.main(
            ["--run-id", "32259216513", str(target)],
            fetch=serving(RUN_V0_2_1_GREEN, RUN_V0_2_1_GREEN_JOBS),
            now=at("2026-08-19T14:00:00Z"),
        )

        assert json.loads(target.read_text(encoding="utf-8"))["run_id"] == 32259216513

    def test_the_run_id_may_be_glued_to_the_option(self, tmp_path: Path) -> None:
        target = tmp_path / "report.json"

        checker.main(
            [f"--run-id={RUN_V0_2_1_GREEN['id']}", str(target)],
            fetch=serving(RUN_V0_2_1_GREEN, RUN_V0_2_1_GREEN_JOBS),
            now=at("2026-08-19T14:00:00Z"),
        )

        assert json.loads(target.read_text(encoding="utf-8"))["resolved"] is True

    def test_the_report_path_defaults_to_the_documented_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The workflow's `hashFiles()` gate keys off this exact file name."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("DELIVERY_RUN_ID", "32259216513")

        checker.main([], fetch=serving(RUN_V0_2_1_GREEN, RUN_V0_2_1_GREEN_JOBS), now=at("2026-08-19T14:00:00Z"))

        assert (tmp_path / "delivery-run-report.json").is_file()
        assert checker.REPORT_PATH == "delivery-run-report.json"

    def test_an_inconclusive_run_still_writes_the_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """It is a determined fact about the run; the workflow just acts on neither flag."""
        monkeypatch.setenv("DELIVERY_RUN_ID", str(RUN_NUCLEI_CANCELLED["id"]))
        target = tmp_path / "report.json"

        assert (
            checker.main(
                [str(target)],
                fetch=serving(RUN_NUCLEI_CANCELLED, RUN_NUCLEI_CANCELLED_JOBS),
                now=at("2026-08-19T00:00:00Z"),
            )
            == 0
        )
        report = json.loads(target.read_text(encoding="utf-8"))
        assert report["verdict"] == "inconclusive"
        assert report["alert"] is False
        assert report["resolved"] is False

    def test_an_undetermined_run_writes_no_report(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Red run, no report, no issue."""
        monkeypatch.setenv("DELIVERY_RUN_ID", "31729355999")
        target = tmp_path / "report.json"
        fetch = RecordingFetch({run_url(31729355999): checker.DeliveryRunError("GET … failed: HTTP 503")})

        with pytest.raises(checker.DeliveryRunError):
            checker.main([str(target)], fetch=fetch, now=at("2026-08-19T14:00:00Z"))

        assert not target.exists()

    def test_a_missing_run_id_raises_before_anything_is_fetched(self, tmp_path: Path) -> None:
        """An empty `${{ github.event.workflow_run.id }}` must not GET `/runs/`."""
        fetch = RecordingFetch({})

        with pytest.raises(checker.DeliveryRunError, match="no run id given"):
            checker.main([str(tmp_path / "report.json")], fetch=fetch, now=at("2026-08-19T14:00:00Z"))

        assert fetch.urls == []

    @pytest.mark.parametrize(
        ("argv", "message"),
        [
            (["--run-id"], "--run-id needs a value"),
            (["--verbose"], "unknown option"),
            (["a.json", "b.json"], "at most one report path"),
        ],
    )
    def test_a_malformed_command_line_raises(self, argv: list[str], message: str) -> None:
        """Deliberately not the siblings' `return 2`: a malformed invocation is one
        more way the check could not be determined, and the workflow must treat
        it exactly like an unreachable API — red, and no report."""
        with pytest.raises(checker.DeliveryRunError, match=message):
            checker.main(argv, fetch=RecordingFetch({}), now=at("2026-08-19T14:00:00Z"))

    def test_the_repository_is_read_from_the_environment(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """`GITHUB_REPOSITORY` is what makes this usable from a fork or a rename."""
        monkeypatch.setenv("GITHUB_REPOSITORY", "nolte/elsewhere")
        fetch = RecordingFetch(
            {
                "https://api.github.com/repos/nolte/elsewhere/actions/runs/32259216513": RUN_V0_2_1_GREEN,
                "https://api.github.com/repos/nolte/elsewhere/actions/runs/32259216513/jobs?per_page=100&page=1": (
                    RUN_V0_2_1_GREEN_JOBS
                ),
            }
        )

        checker.main(
            ["--run-id", "32259216513", str(tmp_path / "report.json")],
            fetch=fetch,
            now=at("2026-08-19T14:00:00Z"),
        )

        assert fetch.urls[0].startswith("https://api.github.com/repos/nolte/elsewhere/")

    def test_the_observed_workflow_name_is_overridable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """So a second lane can be watched without editing the script."""
        monkeypatch.setenv("DELIVERY_WORKFLOW_NAME", "Security — Nuclei Post-Merge Scan")
        target = tmp_path / "report.json"

        checker.main(
            ["--run-id", str(RUN_NUCLEI_CANCELLED["id"]), str(target)],
            fetch=serving(RUN_NUCLEI_CANCELLED, RUN_NUCLEI_CANCELLED_JOBS),
            now=at("2026-08-19T00:00:00Z"),
        )

        assert json.loads(target.read_text(encoding="utf-8"))["is_expected_workflow"] is True

    def test_the_summary_names_the_failing_job_and_the_unproven_ones(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """An alerting run must be readable straight off the job log."""
        checker.main(
            ["--run-id", "31729355999", str(tmp_path / "report.json")],
            fetch=serving(RUN_V0_2_0_RED, RUN_V0_2_0_RED_JOBS),
            now=at("2026-08-13T18:31:18Z"),
        )
        out = capsys.readouterr().out

        assert "DELIVERY RUN RED" in out
        assert CHART_JOB_RAN in out
        assert "Skipped, therefore NOT proven by this run: changes, update-release-assets" in out
        assert "tag v0.2.0" in out

    def test_the_summary_of_an_inconclusive_run_says_it_decided_nothing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        checker.main(
            ["--run-id", str(RUN_NUCLEI_CANCELLED["id"]), str(tmp_path / "report.json")],
            fetch=serving(RUN_NUCLEI_CANCELLED, RUN_NUCLEI_CANCELLED_JOBS),
            now=at("2026-08-19T00:00:00Z"),
        )
        out = capsys.readouterr().out

        assert "INCONCLUSIVE" in out
        assert "no alert is opened and no alert is closed" in out
        assert "NOTE: this run belongs to" in out


class TestTheModuleEntryPoint:
    """`python3 scripts/ci/check_delivery_run.py` itself: exit 1, `::error::`, no report."""

    def script_path(self) -> Path:
        root = find_repo_root(Path(__file__).resolve())
        assert root is not None, "checkout root not found"
        return root / "scripts" / "ci" / "check_delivery_run.py"

    def run_script(self, tmp_path: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
        """Execute the script as the workflow does — no network is reachable from
        any of these invocations, because each fails before the first request."""
        return subprocess.run(  # noqa: S603 — fixed argv, no shell, test-only
            [sys.executable, str(self.script_path()), *argv],
            cwd=tmp_path,
            env={"PATH": "/usr/bin:/bin", "GITHUB_REPOSITORY": REPOSITORY},
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def test_a_malformed_run_id_exits_one_with_an_error_annotation(self, tmp_path: Path) -> None:
        completed = self.run_script(tmp_path, ["--run-id", "not-a-number", "report.json"])

        assert completed.returncode == 1
        assert "::error::delivery run check could not be determined" in completed.stderr
        assert not (tmp_path / "report.json").exists()

    def test_no_run_id_at_all_exits_one_with_an_error_annotation(self, tmp_path: Path) -> None:
        """The state an empty `${{ github.event.workflow_run.id }}` produces."""
        completed = self.run_script(tmp_path, [])

        assert completed.returncode == 1
        assert "::error::" in completed.stderr
        assert "no run id given" in completed.stderr
        assert not (tmp_path / "delivery-run-report.json").exists()

    def test_an_unknown_option_exits_one(self, tmp_path: Path) -> None:
        completed = self.run_script(tmp_path, ["--run-id", "31729355999", "--dry-run"])

        assert completed.returncode == 1
        assert "::error::" in completed.stderr
        assert not list(tmp_path.iterdir())


# --------------------------------------------------------------------------- #
# Invariants that must hold for every fixture at once.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("run", "jobs"),
    [(run, jobs) for _, run, jobs in ALL_FIXTURES],
    ids=[name for name, _, _ in ALL_FIXTURES],
)
class TestInvariants:
    """Properties no future verdict may break, checked against every recorded run."""

    def test_alert_and_resolved_are_mutually_exclusive(self, run: dict[str, Any], jobs: dict[str, Any]) -> None:
        report = judge(run, jobs, now="2026-08-19T14:00:00Z")

        assert not (report["alert"] and report["resolved"])
        assert report["verdict"] in {"alert", "resolved", "inconclusive"}
        assert report["alert"] is (report["verdict"] == "alert")
        assert report["resolved"] is (report["verdict"] == "resolved")

    def test_every_job_lands_in_exactly_one_bucket(self, run: dict[str, Any], jobs: dict[str, Any]) -> None:
        """No job may be counted twice or vanish — the buckets are the alert body."""
        report = judge(run, jobs, now="2026-08-19T14:00:00Z")

        bucketed = (
            len(report["failed_jobs"])
            + len(report["succeeded_jobs"])
            + len(report["skipped_jobs"])
            + len(report["cancelled_jobs"])
            + len(report["other_jobs"])
        )
        assert bucketed == report["job_count"] == len(report["jobs"])

    def test_the_report_is_json_serialisable(self, run: dict[str, Any], jobs: dict[str, Any]) -> None:
        """The workflow reads it with `JSON.parse`; a stray datetime would kill it."""
        report = judge(run, jobs, now="2026-08-19T14:00:00Z")

        assert json.loads(json.dumps(report)) == report
