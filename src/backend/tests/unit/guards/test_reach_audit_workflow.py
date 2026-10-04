"""``reach-audit.yml`` stays what it was written to be: periodic, read-only, pinned.

The capability reach audit is "not a merge gate" by its own spec, and the runner is
fetched from a second repository. Three properties are mechanical and cheap to hold:

* the runner is checked out at a FULL commit SHA, never a branch or tag (a floating
  ref would let the audit change under the repository without a diff here);
* the workflow runs on ``schedule`` and ``workflow_dispatch`` only (no ``push`` or
  ``pull_request``: it is heavy and advisory, and a required context cannot live in
  a workflow that does not report on every change);
* no job holds a write permission and no step is ``continue-on-error`` (a measurement
  that cannot fail is not one).

What it does not hold, stated rather than implied: that the invocation's flags match
the runner's CLI. The runner lives in nolte/claude-shared, so a repository test would
have to read a second checkout; the first real run is that test.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_ROOT = find_repo_root(Path(__file__).resolve())
_PATH = (_ROOT / ".github" / "workflows" / "reach-audit.yml") if _ROOT else None


@pytest.fixture(scope="module")
def workflow() -> dict[str, Any]:
    assert _PATH is not None and _PATH.is_file(), "reach-audit.yml must exist"
    return yaml.safe_load(_PATH.read_text(encoding="utf-8"))


def _triggers(workflow: dict[str, Any]) -> set[str]:
    return set(workflow.get(True) or workflow.get("on") or {})  # YAML 1.1 reads `on:` as True


def _steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    return [step for job in workflow["jobs"].values() for step in job["steps"]]


def test_runs_only_periodically_or_on_demand(workflow: dict[str, Any]) -> None:
    assert _triggers(workflow) == {"schedule", "workflow_dispatch"}


def test_runner_checkout_is_pinned_to_a_full_commit(workflow: dict[str, Any]) -> None:
    other = [s for s in _steps(workflow) if (s.get("with") or {}).get("repository") == "nolte/claude-shared"]
    assert len(other) == 1
    assert re.fullmatch(r"[0-9a-f]{40}", str(other[0]["with"]["ref"]))


def test_no_write_permission_and_no_masked_failure(workflow: dict[str, Any]) -> None:
    scopes = dict(workflow.get("permissions") or {})
    for job in workflow["jobs"].values():
        scopes.update(job.get("permissions") or {})
    assert "write" not in set(scopes.values())
    assert not [s for s in _steps(workflow) if s.get("continue-on-error")]
    assert not [j for j in workflow["jobs"].values() if j.get("continue-on-error")]


def test_the_verdict_step_runs_over_the_runner_output(workflow: dict[str, Any]) -> None:
    runs = " ".join(str(s.get("run", "")) for s in _steps(workflow))
    assert "scripts/ci/reach_report_verdict.py" in runs
    assert "--include-t2" in runs
