#!/usr/bin/env python3
"""Count how many of a workflow's newest completed runs executed, and print the number (#1976).

Observation step of the ``endpoint-zap-postmerge-push-runs-completed`` reach probe
(spec row "Scan lane never executes", T0). It asks the platform's run record, never
the workflow file, how many of the newest ``--limit`` *completed* runs the declared
trigger started actually executed; ``skipped``, ``cancelled`` and ``startup_failure``
runs do not count. A result says the lane ran, never that it works.

Two properties the replaced inline probe (``endpoint-zap-postmerge-push-runs``) lacked:

* Runs still in flight are not part of the sample. The request filters
  ``status=completed``, so a push run that is still scanning takes no slot and is not
  read as "did not execute" — a lane whose scans last twenty to thirty minutes
  measured 299 of 300 whenever the newest push was still running. How many runs are in
  flight is written to stderr, which the runner drops on success.
* A short read is no measurement. When the platform lists fewer rows than the
  ``total_count`` it reports for the same filter, the helper exits non-zero (the runner
  reports *not probed*, with the message) instead of printing a count the lane did not
  earn.

``gh`` resolves the repository from the working directory, as the replaced probe did.

Output: one integer. Exit 1: ``gh`` failed or the listing was short.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from typing import Any

PER_PAGE = 100
#: Conclusions of runs that completed without executing the workflow's work.
NOT_EXECUTED = {None, "", "skipped", "cancelled", "startup_failure"}
GH_TIMEOUT_SECONDS = 60


class ShortReadError(Exception):
    """The platform listed fewer runs than it reports to exist for the filter."""


def observe(fetch_page: Callable[[int], dict[str, Any]], limit: int) -> int:
    """How many of the newest *limit* completed runs executed.

    *fetch_page* returns one page (1-based) of ``{"total_count": int,
    "workflow_runs": [{"status", "conclusion"}, ...]}``, newest first, already
    filtered to completed runs; a row that is not completed is dropped regardless.

    Raises:
        ShortReadError: fewer completed rows came back than ``min(limit, total_count)``.
    """
    sample: list[dict[str, Any]] = []
    expected = limit
    page = 1
    while len(sample) < min(limit, expected):
        body = fetch_page(page)
        if page == 1:
            expected = min(limit, int(body.get("total_count", 0)))
        rows = body.get("workflow_runs") or []
        sample += [row for row in rows if row.get("status") == "completed"]
        if len(rows) < PER_PAGE:
            break
        page += 1
    sample = sample[:limit]
    if len(sample) < expected:
        raise ShortReadError(f"the platform listed {len(sample)} completed runs but reports {expected}")
    return sum(1 for row in sample if row.get("conclusion") not in NOT_EXECUTED)


def _gh_pager(workflow: str, event: str, branch: str, status: str) -> Callable[[int], dict[str, Any]]:
    def fetch(page: int) -> dict[str, Any]:
        path = (
            f"repos/{{owner}}/{{repo}}/actions/workflows/{workflow}/runs"
            f"?event={event}&branch={branch}&status={status}&per_page={PER_PAGE}&page={page}"
            "&exclude_pull_requests=true"
        )
        res = subprocess.run(  # noqa: S603, S607 - fixed argv, no shell
            ["gh", "api", path], capture_output=True, text=True, timeout=GH_TIMEOUT_SECONDS, check=False
        )
        if res.returncode != 0:
            sys.exit(f"gh api exited {res.returncode}: {res.stderr.strip()}")
        return json.loads(res.stdout)

    return fetch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workflow", required=True, help="workflow file name, e.g. security-zap-postmerge.yml")
    parser.add_argument("--event", default="push")
    parser.add_argument("--branch", default="develop")
    parser.add_argument("--limit", type=int, default=300)
    args = parser.parse_args()
    try:
        count = observe(_gh_pager(args.workflow, args.event, args.branch, "completed"), args.limit)
    except ShortReadError as exc:
        sys.exit(f"short read: {exc}")
    in_flight = sum(
        int(_gh_pager(args.workflow, args.event, args.branch, status)(1).get("total_count", 0))
        for status in ("queued", "in_progress")
    )
    print(f"in flight, not counted: {in_flight}", file=sys.stderr)
    print(count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
