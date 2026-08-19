#!/usr/bin/env python3
"""Alert when a run of the DELIVERY LANE goes red.

Issue #1225, work package P1. This watches the **process** — "did the run that
builds and publishes this project actually pass?" — and it is the third member
of a family whose division of labour is deliberate:

    release-lag.yml            has a release been PUBLISHED at all?
    release-assets-complete.yml does the published release CARRY its artefacts?
    delivery-run-alert.yml     did the delivery RUN go red?      <- this one

The two siblings watch outcomes on the release page. Neither of them can see a
red run, and a red run is exactly what nobody saw here.

THE INCIDENT THIS EXISTS FOR
----------------------------
`publish-helm-charts` in `.github/workflows/docker-publish.yml` failed on
2026-08-13 (run 31729355999, tag `v0.2.0`), on 2026-08-16 (31955164085,
`develop`) and again 8 minutes later (31955579431, `develop`). Every one of
those runs is RED in the Actions tab. Every one of them alerted nobody, and the
cause was re-diagnosed from scratch five days later.

Nothing in this repository observed it, because nothing could:
`grep -rl "workflow_run" .github/workflows/` returned NOTHING on `origin/develop`
(re-measured 2026-08-19). A red run is a notification GitHub sends to the actor
and nowhere else; on a Renovate-authored push the actor is a bot.

WHY THE LANE STILL LOOKED HEALTHY
---------------------------------
`publish-helm-charts` only runs when `helm/**` changed, when the ref is a `v*`
tag, or on `workflow_dispatch` (its `if:` in docker-publish.yml). On every other
push to `develop` it is SKIPPED — and a skipped job takes nothing down with it,
so the run is green. The lane therefore reads green most of the time and the red
runs look intermittent rather than systematic. They were not: every run that
actually reached the chart job failed.

That is why this check reports jobs that RAN AND SUCCEEDED separately from jobs
that were SKIPPED. The observer workflow (P2) closes an alert only when every
job recorded as failing has actually run and succeeded again — a green run that
merely skipped them proves nothing and must not close anything. Without the
distinction the alert would flap: open on a `helm/**` push, close on the next
unrelated push, open again on the next release.

TWO MEASURED FACTS ABOUT THE JOBS ENDPOINT, BOTH LOAD-BEARING
-------------------------------------------------------------
Measured with `gh api repos/nolte/kamerplanter/actions/runs/<id>/jobs?per_page=100`
on 2026-08-19:

1. **A skipped job is `"conclusion": "skipped"` here, NOT `"success"`.** The
   phrase "a skipped job reports success" — true, and this repository's most
   expensive failure class — is about `needs.<job>.result` inside workflow
   expressions and about the run-level conclusion. The jobs API is explicit, so
   this check can tell the two apart at all. It reads `conclusion` verbatim and
   never infers "it must have passed" from the absence of a failure.

2. **A matrix job changes NAME depending on whether it ran.** Executed, it is
   `publish-helm-charts (kamerplanter)` (runs 31729355999, 32259216513);
   skipped, GitHub reports the unexpanded `publish-helm-charts` (run
   32157445903). Same job, two strings. A consumer that records the failing name
   and later looks for it among the skipped ones will not find it. Every job
   entry in the report therefore carries `base_name` — the name with the matrix
   suffix stripped — so the observer can compare across that boundary instead of
   silently concluding "the job is gone".

THE CONCLUSION TAXONOMY, AND WHY THREE VERDICTS
-----------------------------------------------
    failure, timed_out, startup_failure   -> alert       (the lane is broken)
    success                               -> resolved    (the lane is healthy)
    cancelled, neutral, skipped,
    action_required, stale                -> inconclusive

`alert` and `resolved` are never both true; on `inconclusive` neither is. A
cancelled run is an operator act (or a `concurrency` eviction), not a broken
lane, and "the run did not fail" is not "the lane works" — closing an alert on
it would certify something nobody measured. So `inconclusive` is written to the
report, exits 0, and the workflow leaves the issue exactly as it found it. This
is the same shape as `check_release_assets.py`'s "judged nothing" state, and it
exists for the same reason: an undetermined state must not present itself as
measured-clean.

An UNRECOGNISED conclusion string is a different thing entirely and raises. A
value this taxonomy has never seen means the check does not know what happened;
folding it into `inconclusive` would turn "we do not know" into the determined
fact "the run neither failed nor succeeded", which is precisely the substitution
NFR-018 §2 forbids.

FAIL LOUD (NFR-018 section 2)
-----------------------------
A run that is not `completed`, an unreachable API, an undecodable payload, a run
object without `status`/`conclusion`, a jobs page that does not carry the jobs it
claims, a job whose conclusion is absent, a run id that is not an integer — none
of these is "the delivery run is fine". Each raises :class:`DeliveryRunError`;
``main()`` prints ``::error::`` and exits non-zero WITHOUT writing the report, so
the observer run goes red and opens NO issue. A transient API blip must not spam
the tracker, and an undetermined check must never read as a clean one.

WHAT THE OBSERVER WORKFLOW (P2) MUST KNOW
------------------------------------------
* The report exists **iff** the verdict is determined. Gate the issue step on
  the file, exactly as `release-assets-complete.yml` does.
* Open/update on ``alert``; close on ``resolved`` AND on the per-job evidence —
  never on ``!alert``, which is also true for every inconclusive run.
* ``alert: true`` with an EMPTY ``failed_jobs`` is possible: GitHub can fail a
  run without any job carrying a failing conclusion (a workflow-level error, or
  a failure on an earlier attempt while this endpoint reports the latest one).
  The list is reported honestly rather than back-filled. Treat an empty set as
  "unknown job set" and do NOT let the closing rule pass vacuously over it —
  "every job in an empty set succeeded" is true and proves nothing.
* ``is_expected_workflow`` says whether the run belongs to the workflow this
  observer is for. On the `workflow_run` trigger it is always true by
  construction; on a `workflow_dispatch` a human can hand over any run id at
  all, including one from an unrelated workflow. The check does NOT hard-fail on
  it — pointing the observer at another lane is a legitimate thing to do — it
  reports the fact and lets the workflow decide.
* Environment inputs: ``GITHUB_REPOSITORY`` (default `nolte/kamerplanter`),
  ``GITHUB_TOKEN`` (optional; public reads work without it, the token lifts the
  rate limit and is required for `actions: read` on a private repo),
  ``DELIVERY_RUN_ID`` (the run to judge, overridden by ``--run-id``),
  ``DELIVERY_WORKFLOW_NAME`` (default "Build & Publish Container Images").

Traces to issue #1225 (no TC-ID: a CI alarm is not a user-facing case).
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

API_ROOT = "https://api.github.com"

#: Written only on a DETERMINED verdict; the workflow's issue step keys off its
#: existence, so an undetermined run leaves it absent and opens nothing.
REPORT_PATH = "delivery-run-report.json"

DEFAULT_REPOSITORY = "nolte/kamerplanter"

#: The `name:` of `.github/workflows/docker-publish.yml`. Only ever compared and
#: reported, never enforced — see "WHAT THE OBSERVER WORKFLOW MUST KNOW".
DEFAULT_WORKFLOW_NAME = "Build & Publish Container Images"

#: The delivery lane has 11 jobs, so one page covers it; the pagination below
#: exists because a matrix that grows past 100 would otherwise be truncated
#: silently, and a truncated job list is how a check starts certifying nothing.
JOB_PAGE_SIZE = 100

#: 2000 jobs is far past anything this lane could legitimately produce; hitting
#: it means the endpoint is not converging, which is undetermined, not clean.
MAX_JOB_PAGES = 20

HTTP_TIMEOUT_SECONDS = 30

SECONDS_PER_MINUTE = 60.0

#: Run conclusions that mean the delivery lane is broken.
ALERTING_CONCLUSIONS = frozenset({"failure", "timed_out", "startup_failure"})

#: Run conclusions that mean the delivery lane worked.
RESOLVING_CONCLUSIONS = frozenset({"success"})

#: Run conclusions that are determined facts about the run but say nothing about
#: the lane's health — reported, acted on by nobody.
INCONCLUSIVE_CONCLUSIONS = frozenset({"cancelled", "neutral", "skipped", "action_required", "stale"})

KNOWN_CONCLUSIONS = ALERTING_CONCLUSIONS | RESOLVING_CONCLUSIONS | INCONCLUSIVE_CONCLUSIONS

#: Job conclusions that count as "this job broke". Mirrors the run-level set:
#: the jobs endpoint reports `failure` and `timed_out`, and `startup_failure` is
#: included so a run-level shape can never appear here unclassified.
FAILING_JOB_CONCLUSIONS = frozenset({"failure", "timed_out", "startup_failure"})

VERDICT_ALERT = "alert"
VERDICT_RESOLVED = "resolved"
VERDICT_INCONCLUSIVE = "inconclusive"

#: `GET /actions/runs/{id}` carries no ref type: on a tag run `head_branch` is
#: the TAG NAME (measured — run 31729355999 reports `head_branch: "v0.2.0"`).
#: This repository tags releases `v<major>.<minor>.<patch>` and docker-publish.yml
#: gates its release steps on `refs/tags/v*`, so the shape is derivable — but it
#: IS a heuristic: a branch literally named `v1.2.3` would be read as a tag.
#: `ref_kind` is therefore for the alert's prose only; nothing decides on it.
TAG_REF_PATTERN = re.compile(r"^v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")

#: A matrix job is reported as `<job> (<value>, <value>)` when it runs and as
#: the bare `<job>` when it is skipped. See "TWO MEASURED FACTS" above.
MATRIX_SUFFIX_PATTERN = re.compile(r"\s+\(.*\)$")


class DeliveryRunError(RuntimeError):
    """A condition under which the verdict could not be determined — fail loud."""


@dataclass(frozen=True)
class Job:
    """One job of a workflow run, reduced to what the verdict turns on."""

    name: str
    status: str
    conclusion: str
    url: str
    started_at: str
    completed_at: str

    @property
    def base_name(self) -> str:
        """The job name with a matrix suffix stripped.

        `publish-helm-charts (kamerplanter)` and `publish-helm-charts` are the
        same job seen in its executed and its skipped form; this is the key that
        joins them.
        """
        return MATRIX_SUFFIX_PATTERN.sub("", self.name)

    @property
    def failed(self) -> bool:
        return self.conclusion in FAILING_JOB_CONCLUSIONS

    @property
    def succeeded(self) -> bool:
        """Whether this job RAN and passed. A skipped job is not a success here."""
        return self.conclusion == "success"

    @property
    def skipped(self) -> bool:
        return self.conclusion == "skipped"


@dataclass(frozen=True)
class Run:
    """One workflow run, reduced to what the verdict and the alert body need."""

    run_id: int
    workflow_name: str
    workflow_path: str
    event: str
    head_branch: str
    head_sha: str
    display_title: str
    status: str
    conclusion: str
    run_attempt: int
    run_number: int
    run_started_at: datetime
    updated_at: datetime
    html_url: str

    @property
    def ref_kind(self) -> str:
        """``tag`` or ``branch`` — a heuristic, see :data:`TAG_REF_PATTERN`."""
        return "tag" if TAG_REF_PATTERN.match(self.head_branch) else "branch"

    @property
    def duration_seconds(self) -> float:
        return (self.updated_at - self.run_started_at).total_seconds()


def parse_timestamp(value: Any, *, context: str) -> datetime:
    """Parse an ISO-8601 GitHub timestamp into an aware UTC datetime.

    Args:
        value: The raw field value.
        context: What is being parsed, for the error message.

    Returns:
        A timezone-aware datetime.

    Raises:
        DeliveryRunError: The value is absent or unparseable. Never a fallback to
            "now" — a guessed timestamp would put an invented duration into an
            alert a human reads as measured.
    """
    if not isinstance(value, str) or not value:
        raise DeliveryRunError(f"{context}: missing timestamp (got {value!r})")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DeliveryRunError(f"{context}: unparseable timestamp {value!r}: {exc}") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_run_id(value: Any) -> int:
    """Turn a run id from the CLI or the environment into an int.

    Args:
        value: The raw ``--run-id`` argument or ``DELIVERY_RUN_ID`` value.

    Returns:
        The run id.

    Raises:
        DeliveryRunError: The value is absent, not an integer, or not positive.
            `${{ github.event.workflow_run.id }}` renders empty when the event
            payload is not what the workflow assumed, and an empty id must go
            red rather than fetch `/actions/runs/`.
    """
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise DeliveryRunError(f"run id must be an integer, got {value!r}")
    text = str(value).strip()
    if not text:
        raise DeliveryRunError("no run id given — pass --run-id or set DELIVERY_RUN_ID")
    if not text.isdigit():
        raise DeliveryRunError(f"run id must be an integer, got {text!r}")
    run_id = int(text)
    if run_id <= 0:
        raise DeliveryRunError(f"run id must be positive, got {run_id}")
    return run_id


def parse_run(payload: Any) -> Run:
    """Turn a ``GET /actions/runs/{id}`` payload into a :class:`Run`.

    Args:
        payload: The decoded JSON body.

    Returns:
        The run.

    Raises:
        DeliveryRunError: The payload is not a run object, or lacks a field the
            verdict depends on. ``status`` and ``conclusion`` are required KEYS:
            reading an absent ``conclusion`` as "no failure reported" would turn
            an API shape change into a permanent, silent all-clear.
    """
    if not isinstance(payload, dict):
        raise DeliveryRunError(f"run payload is not a JSON object (got {type(payload).__name__})")

    raw_id = payload.get("id")
    if not isinstance(raw_id, int) or isinstance(raw_id, bool):
        raise DeliveryRunError(f"run payload has no integer id (got {raw_id!r})")

    if "status" not in payload:
        raise DeliveryRunError(f"run {raw_id}: payload carries no status field")
    status = payload["status"]
    if not isinstance(status, str) or not status:
        raise DeliveryRunError(f"run {raw_id}: status is not a non-empty string (got {status!r})")

    if "conclusion" not in payload:
        raise DeliveryRunError(f"run {raw_id}: payload carries no conclusion field")
    conclusion = payload["conclusion"]

    if status != "completed":
        raise DeliveryRunError(
            f"run {raw_id} is {status!r}, not 'completed' — its outcome is not decided yet, "
            "so there is nothing to alert on or resolve"
        )
    if not isinstance(conclusion, str) or not conclusion:
        raise DeliveryRunError(
            f"run {raw_id} is completed but carries conclusion {conclusion!r} — "
            "a completed run without a conclusion leaves the verdict undetermined"
        )

    attempt = payload.get("run_attempt")
    number = payload.get("run_number")
    return Run(
        run_id=raw_id,
        workflow_name=str(payload.get("name") or ""),
        workflow_path=str(payload.get("path") or ""),
        event=str(payload.get("event") or ""),
        head_branch=str(payload.get("head_branch") or ""),
        head_sha=str(payload.get("head_sha") or ""),
        display_title=str(payload.get("display_title") or ""),
        status=status,
        conclusion=conclusion,
        run_attempt=attempt if isinstance(attempt, int) and not isinstance(attempt, bool) else 1,
        run_number=number if isinstance(number, int) and not isinstance(number, bool) else 0,
        run_started_at=parse_timestamp(payload.get("run_started_at"), context=f"run {raw_id} run_started_at"),
        updated_at=parse_timestamp(payload.get("updated_at"), context=f"run {raw_id} updated_at"),
        html_url=str(payload.get("html_url") or ""),
    )


def parse_jobs_page(payload: Any, *, run_id: int, page: int) -> tuple[int, list[Job]]:
    """Turn one ``GET /actions/runs/{id}/jobs`` page into (total_count, jobs).

    Args:
        payload: The decoded JSON body of one page.
        run_id: The owning run, for error messages.
        page: The 1-based page number, for error messages.

    Returns:
        The endpoint's own ``total_count`` and the jobs on this page.

    Raises:
        DeliveryRunError: The page is not a jobs object, or a job lacks a name,
            a status or a conclusion. A job whose conclusion is absent cannot be
            classified, and dropping it would quietly shrink the very sets the
            observer's closing rule reads.
    """
    if not isinstance(payload, dict):
        raise DeliveryRunError(f"run {run_id}: jobs page {page} is not a JSON object (got {type(payload).__name__})")

    total = payload.get("total_count")
    if not isinstance(total, int) or isinstance(total, bool):
        raise DeliveryRunError(f"run {run_id}: jobs page {page} has no integer total_count (got {total!r})")

    raw_jobs = payload.get("jobs")
    if not isinstance(raw_jobs, list):
        raise DeliveryRunError(f"run {run_id}: jobs page {page} carries no jobs array")

    jobs: list[Job] = []
    for index, entry in enumerate(raw_jobs):
        if not isinstance(entry, dict):
            raise DeliveryRunError(f"run {run_id}: job[{index}] on page {page} is not an object")
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise DeliveryRunError(f"run {run_id}: job[{index}] on page {page} has no name")
        status = entry.get("status")
        if not isinstance(status, str) or not status:
            raise DeliveryRunError(f"run {run_id}: job {name!r} has no status")
        conclusion = entry.get("conclusion")
        if not isinstance(conclusion, str) or not conclusion:
            raise DeliveryRunError(
                f"run {run_id}: job {name!r} is {status!r} and carries conclusion {conclusion!r} — "
                "it cannot be classified as failed, succeeded or skipped"
            )
        jobs.append(
            Job(
                name=name,
                status=status,
                conclusion=conclusion,
                url=str(entry.get("html_url") or ""),
                started_at=str(entry.get("started_at") or ""),
                completed_at=str(entry.get("completed_at") or ""),
            )
        )
    return total, jobs


def fetch_jobs(fetch: Callable[[str], Any], *, repository: str, run_id: int) -> list[Job]:
    """Read every job of *run_id*, following pagination.

    The endpoint defaults to ``filter=latest``, i.e. the jobs of the run's most
    recent attempt — which is the right window: a re-run that passed is the
    state the lane is in now.

    Args:
        fetch: The injected HTTP layer.
        repository: ``owner/name``.
        run_id: The run to read.

    Returns:
        Every job of the latest attempt.

    Raises:
        DeliveryRunError: The pages do not add up to the ``total_count`` the
            endpoint reports, no job comes back at all, or the pagination does
            not converge. A partially-read job list would let the observer close
            an alert because the job it was watching happened to be on a page
            nobody fetched.
    """
    collected: list[Job] = []
    total = 0
    for page in range(1, MAX_JOB_PAGES + 1):
        url = f"{API_ROOT}/repos/{repository}/actions/runs/{run_id}/jobs?per_page={JOB_PAGE_SIZE}&page={page}"
        total, jobs = parse_jobs_page(fetch(url), run_id=run_id, page=page)
        collected.extend(jobs)
        if len(collected) >= total:
            break
        if not jobs:
            raise DeliveryRunError(
                f"run {run_id}: the jobs endpoint reports {total} job(s) but page {page} is empty — "
                f"only {len(collected)} could be read"
            )
    else:
        raise DeliveryRunError(
            f"run {run_id}: the jobs endpoint did not converge within {MAX_JOB_PAGES} pages "
            f"({len(collected)} of {total} job(s) read)"
        )

    if len(collected) != total:
        raise DeliveryRunError(
            f"run {run_id}: read {len(collected)} job(s) but the endpoint reports {total} — "
            "the job list is inconsistent and any verdict on it would be partial"
        )
    if not collected:
        raise DeliveryRunError(
            f"run {run_id}: the run is completed but carries no jobs — "
            "refusing to judge the delivery lane against nothing"
        )
    return collected


def classify(conclusion: str, *, run_id: int) -> str:
    """Map a run conclusion onto one of the three verdicts.

    Raises:
        DeliveryRunError: The conclusion is not one this taxonomy knows. See
            "THE CONCLUSION TAXONOMY" in the module docstring: an unrecognised
            value means the check does not know what happened, which is not the
            same determined fact as "the run neither failed nor succeeded".
    """
    if conclusion in ALERTING_CONCLUSIONS:
        return VERDICT_ALERT
    if conclusion in RESOLVING_CONCLUSIONS:
        return VERDICT_RESOLVED
    if conclusion in INCONCLUSIVE_CONCLUSIONS:
        return VERDICT_INCONCLUSIVE
    raise DeliveryRunError(
        f"run {run_id}: unknown conclusion {conclusion!r} — known values are "
        f"{', '.join(sorted(KNOWN_CONCLUSIONS))}; refusing to guess what it means"
    )


def build_report(
    fetch: Callable[[str], Any],
    *,
    repository: str,
    run_id: int,
    workflow_name: str = DEFAULT_WORKFLOW_NAME,
    now: datetime,
) -> dict[str, Any]:
    """Judge one delivery-lane run and return the report the workflow acts on.

    Args:
        fetch: Returns the decoded JSON body for a URL, or raises
            :class:`DeliveryRunError`. Injected so the tests need no network.
        repository: ``owner/name``.
        run_id: The workflow run to judge.
        workflow_name: The workflow this observer is for; only compared and
            reported (``is_expected_workflow``), never enforced.
        now: Evaluation instant, timezone-aware.

    Returns:
        A JSON-serialisable report carrying one ``verdict`` plus the two
        booleans the workflow branches on. ``alert`` and ``resolved`` are
        derived from the verdict, so they cannot both be true and cannot drift
        apart from it.

    Raises:
        DeliveryRunError: Anything that leaves the verdict undetermined.
    """
    run = parse_run(fetch(f"{API_ROOT}/repos/{repository}/actions/runs/{run_id}"))
    if run.run_id != run_id:
        raise DeliveryRunError(f"asked for run {run_id} but the API answered with run {run.run_id}")

    jobs = fetch_jobs(fetch, repository=repository, run_id=run_id)
    verdict = classify(run.conclusion, run_id=run_id)

    failed = [job for job in jobs if job.failed]
    succeeded = [job for job in jobs if job.succeeded]
    skipped = [job for job in jobs if job.skipped]
    cancelled = [job for job in jobs if job.conclusion == "cancelled"]
    classified = {id(job) for group in (failed, succeeded, skipped, cancelled) for job in group}
    other = [job for job in jobs if id(job) not in classified]

    return {
        "repository": repository,
        "evaluated_at": now.isoformat(),
        "run_id": run.run_id,
        "html_url": run.html_url,
        "workflow_name": run.workflow_name,
        "workflow_path": run.workflow_path,
        "expected_workflow": workflow_name,
        # Reported, never enforced — a dispatch may legitimately point at another
        # lane, and the workflow is the layer that decides what to do about it.
        "is_expected_workflow": run.workflow_name == workflow_name,
        "event": run.event,
        "head_branch": run.head_branch,
        "head_sha": run.head_sha,
        # A heuristic on head_branch, which carries the TAG NAME on a tag run.
        "ref_kind": run.ref_kind,
        "display_title": run.display_title,
        "status": run.status,
        "conclusion": run.conclusion,
        "run_attempt": run.run_attempt,
        "run_number": run.run_number,
        "run_started_at": run.run_started_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
        "duration_seconds": round(run.duration_seconds, 1),
        "age_minutes": round((now - run.updated_at).total_seconds() / SECONDS_PER_MINUTE, 1),
        "verdict": verdict,
        "alert": verdict == VERDICT_ALERT,
        # NOT `not alert`. On an inconclusive run both are false, and the
        # workflow must then leave the alert issue exactly as it found it.
        "resolved": verdict == VERDICT_RESOLVED,
        "job_count": len(jobs),
        "jobs": [
            {
                "name": job.name,
                # The join key across the executed/skipped name asymmetry.
                "base_name": job.base_name,
                "status": job.status,
                "conclusion": job.conclusion,
                "url": job.url,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
            }
            for job in jobs
        ],
        "failed_jobs": [job.name for job in failed],
        # Jobs that RAN and passed. A skipped job is never in here — that
        # distinction is what keeps the alert from flapping (R6).
        "succeeded_jobs": [job.name for job in succeeded],
        "skipped_jobs": [job.name for job in skipped],
        "cancelled_jobs": [job.name for job in cancelled],
        "other_jobs": [{"name": job.name, "conclusion": job.conclusion} for job in other],
    }


def api_json(url: str) -> Any:
    """GET *url* from the GitHub API and decode it.

    Raises:
        DeliveryRunError: Any transport, status or decode failure. Every branch
            raises; none returns a placeholder.
    """
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise DeliveryRunError(f"GET {url} failed: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise DeliveryRunError(f"GET {url} failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DeliveryRunError(f"GET {url} returned undecodable JSON: {exc}") from exc


@dataclass(frozen=True)
class Arguments:
    """The parsed command line."""

    run_id: str | None
    report_path: str


def parse_arguments(argv: list[str]) -> Arguments:
    """Parse ``[--run-id N] [report.json]``.

    Hand-rolled rather than argparse, so a usage error is a return value the
    tests can assert on instead of a :class:`SystemExit`, like the siblings.

    Raises:
        DeliveryRunError: The command line is malformed.
    """
    run_id: str | None = None
    positional: list[str] = []
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument == "--run-id":
            if index + 1 >= len(argv):
                raise DeliveryRunError("--run-id needs a value")
            run_id = argv[index + 1]
            index += 2
            continue
        if argument.startswith("--run-id="):
            run_id = argument.split("=", 1)[1]
            index += 1
            continue
        if argument.startswith("-"):
            raise DeliveryRunError(f"unknown option {argument!r}")
        positional.append(argument)
        index += 1

    if len(positional) > 1:
        raise DeliveryRunError(f"expected at most one report path, got {len(positional)}: {', '.join(positional)}")
    return Arguments(run_id=run_id, report_path=positional[0] if positional else REPORT_PATH)


def _render(report: dict[str, Any]) -> str:
    """The human summary printed to the job log.

    Readable without opening the JSON, and deliberately explicit about the
    skipped jobs: "the lane is green" and "the lane did not run the job that
    broke it" look identical in the Actions tab and must not look identical
    here.
    """
    lines = [
        f"Run {report['run_id']} of {report['workflow_name']!r} ({report['event']} on "
        f"{report['ref_kind']} {report['head_branch']}, attempt {report['run_attempt']}): "
        f"{report['status']}/{report['conclusion']}.",
        f"{report['html_url']} — {report['duration_seconds']}s, finished {report['age_minutes']} minute(s) ago.",
    ]
    if not report["is_expected_workflow"]:
        lines.append(
            f"NOTE: this run belongs to {report['workflow_name']!r}, not to the observed "
            f"{report['expected_workflow']!r}."
        )

    if report["failed_jobs"]:
        lines.append(f"Failed job(s): {', '.join(report['failed_jobs'])}.")
    if report["cancelled_jobs"]:
        lines.append(f"Cancelled job(s): {', '.join(report['cancelled_jobs'])}.")
    if report["skipped_jobs"]:
        lines.append(f"Skipped, therefore NOT proven by this run: {', '.join(report['skipped_jobs'])}.")
    lines.append(f"Ran and succeeded: {', '.join(report['succeeded_jobs']) if report['succeeded_jobs'] else 'none'}.")
    for entry in report["other_jobs"]:
        lines.append(f"Job {entry['name']} concluded {entry['conclusion']}.")

    if report["alert"]:
        named = ", ".join(report["failed_jobs"]) if report["failed_jobs"] else "no job reports a failing conclusion"
        lines.append(f"DELIVERY RUN RED: {report['conclusion']} ({named}).")
    elif report["resolved"]:
        lines.append(f"Delivery run green: {len(report['succeeded_jobs'])} job(s) ran and succeeded.")
    else:
        lines.append(
            f"INCONCLUSIVE: the run concluded {report['conclusion']}, which is neither a lane failure "
            "nor proof that the lane works — no alert is opened and no alert is closed."
        )
    return "\n".join(lines)


def main(
    argv: list[str] | None = None,
    *,
    fetch: Callable[[str], Any] | None = None,
    now: datetime | None = None,
) -> int:
    """Run the check and write the report.

    Args:
        argv: Optional ``[--run-id N] [report_path]``; the run id falls back to
            ``DELIVERY_RUN_ID`` and the path to :data:`REPORT_PATH`.
        fetch: Injection point for the HTTP layer (tests pass a fake).
        now: Injection point for the clock (tests pass a fixed instant).

    Returns:
        0 on a determined verdict — alert, resolved AND inconclusive alike, all
        three of which are facts about the run. Undetermined raises
        :class:`DeliveryRunError`, which the module entry point turns into a red
        run with no report.
    """
    arguments = parse_arguments(list(sys.argv[1:] if argv is None else argv))
    run_id = parse_run_id(arguments.run_id if arguments.run_id is not None else os.environ.get("DELIVERY_RUN_ID", ""))

    report = build_report(
        fetch or api_json,
        repository=os.environ.get("GITHUB_REPOSITORY") or DEFAULT_REPOSITORY,
        run_id=run_id,
        workflow_name=os.environ.get("DELIVERY_WORKFLOW_NAME") or DEFAULT_WORKFLOW_NAME,
        now=now or datetime.now(timezone.utc),
    )

    with open(arguments.report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(_render(report))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DeliveryRunError as exc:
        # Loud, and no report written: an undetermined check is not a clean check.
        print(f"::error::delivery run check could not be determined: {exc}", file=sys.stderr)
        sys.exit(1)
