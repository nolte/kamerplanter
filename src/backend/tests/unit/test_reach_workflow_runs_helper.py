"""The observation step of the post-merge ZAP reach probe (#1976).

``scripts/reach/observe_workflow_runs.py`` counts how many of a workflow's last N
completed runs executed. Two properties are pinned here, both found when the T0
probe it replaces reported 299/300 for a healthy lane:

* **A run still in flight is not a run that did not execute.** The earlier probe
  read every row's ``conclusion`` and counted an empty one (queued or in progress)
  as "not executed", so a lane whose newest push run was still scanning read as
  partially reached, and the value moved with the clock.
* **A short read is no measurement.** When the platform lists fewer rows than the
  total it reports, the helper stops with an error (the runner reads that as *not
  probed*) instead of printing a low count the lane never earned.

The ``gh`` call itself is not exercised: a fake cannot stand in for the platform's
paging, and the real run against the repository is the test of that half.
"""

from __future__ import annotations

from typing import Any

import pytest

from tests.support.repo_scripts import load_repo_script

runs = load_repo_script("reach/observe_workflow_runs")


def _run(conclusion: str | None, status: str = "completed") -> dict[str, Any]:
    return {"status": status, "conclusion": conclusion}


def _pager(rows: list[dict[str, Any]], *, total: int | None = None, per_page: int = 100):
    """A stand-in for one ``gh api`` page request over *rows* (newest first)."""
    reported = len(rows) if total is None else total

    def fetch(page: int) -> dict[str, Any]:
        start = (page - 1) * per_page
        return {"total_count": reported, "workflow_runs": rows[start : start + per_page]}

    return fetch


def test_executed_conclusions_count_and_the_four_that_never_ran_do_not():
    rows = [_run("success"), _run("failure"), _run("skipped"), _run("cancelled"), _run("startup_failure"), _run(None)]
    assert runs.observe(_pager(rows), limit=300) == 2


def test_only_the_newest_limit_rows_are_counted():
    rows = [_run("success")] * 3 + [_run("cancelled")] * 2
    assert runs.observe(_pager(rows), limit=3) == 3


def test_rows_beyond_the_first_page_are_read():
    rows = [_run("success")] * 250
    assert runs.observe(_pager(rows), limit=250) == 250


def test_a_listing_shorter_than_the_reported_total_is_no_measurement():
    # 300 runs exist, the platform handed back 53: a low count here would be a defect
    # of the lane the probe does not have.
    fetch = _pager([_run("success")] * 53, total=300)
    with pytest.raises(runs.ShortReadError):
        runs.observe(fetch, limit=300)


def test_fewer_runs_than_the_limit_are_counted_when_the_platform_lists_them_all():
    assert runs.observe(_pager([_run("success")] * 7), limit=300) == 7


def test_an_in_flight_run_takes_no_slot_of_the_sample():
    # The window is the newest `limit` *completed* runs. A run still in progress at the
    # head of the listing used to take one of the 300 slots and read as "did not
    # execute", so a healthy lane measured 299 until the scan finished.
    rows = [_run(None, status="in_progress"), _run("success"), _run("success"), _run("success")]
    assert runs.observe(_pager(rows), limit=3) == 3


def test_caller_supplied_values_cannot_add_parameters_to_the_request():
    path = runs.runs_path("w.yml", "push&per_page=1", "develop#x y", "completed", 2)
    assert "per_page=1&" not in path
    assert "&per_page=100&page=2" in path
    assert "develop%23x%20y" in path and "push%26per_page%3D1" in path
    assert path.startswith("repos/{owner}/{repo}/actions/workflows/w.yml/runs?")
