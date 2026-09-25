"""The manifest-against-live-workflow rules run in ``lane-inputs.yml`` and nowhere a pull request runs (#1794).

WHY. ``test_lane_filters_cover_measured_inputs.py`` holds the committed
``.github/lane-inputs/`` manifests against the live workflows: every filtered job
has a manifest, no manifest is older than its job, every read is selected by its
filter, every held ``run:`` line is the one recorded. A pull request that changes
a job can only turn those rules green with a CI recording, and recording on pull
requests cost 74 runs in two days, 33 of them red (operator decision 2026-09-25).
So those rules carry the ``lane_inputs_drift`` marker, ``tests/conftest.py``
deselects them unless ``--lane-inputs-drift`` is given, and only the ``guard``
job of ``lane-inputs.yml`` — weekly and on dispatch, never on a pull request —
gives it.

WHAT THIS FILE HOLDS. Each half of that sentence, over the real files:

1. **The deselection is real and exact.** Collecting the guard file without the
   option leaves out the marked rules and keeps the rest (the synthetic trees,
   the matcher, the decision-shape rule, which needs no recording); with the
   option and ``-m lane_inputs_drift`` it collects exactly the marked rules. A
   marker nobody deselects, or an option that selects nothing, is red here.
2. **Only the lane passes the option, and the lane runs no pull-request code.**
   No workflow or Taskfile besides ``lane-inputs.yml`` names ``--lane-inputs-drift``;
   ``lane-inputs.yml`` has no ``pull_request``/``pull_request_target``/``push``
   trigger; its ``guard`` job runs the guard file with the option; every job's
   ``GITHUB_TOKEN`` is ``contents: read``; the App token is minted only under a
   ``refs/heads/develop`` condition (#1614).

Traces to #1794 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from tests.support.repo_scripts import find_repo_root

_BACKEND = Path(__file__).resolve().parents[3]
_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — unreachable inside a checkout
    raise RuntimeError("checkout root not found")

_GUARD = "tests/unit/guards/test_lane_filters_cover_measured_inputs.py"
_OPTION = "--lane-inputs-drift"
_LANE = _REPO_ROOT / ".github" / "workflows" / "lane-inputs.yml"

#: The rules that need a recording. Named, so a marker moved onto another test — or
#: dropped from one of these — is a visible change of this file, not a silent one.
_NEEDS_A_RECORDING = {
    "TestTheRealTree::test_every_filtered_job_and_every_filter_name_is_measured",
    "TestTheRealTree::test_every_manifest_is_well_formed_and_names_a_live_job",
    "TestTheRealTree::test_no_manifest_is_older_than_its_job",
    "TestTheRealTree::test_every_read_is_selected_by_every_filter_that_gates_its_job",
    "TestTheRealTree::test_every_held_invocation_of_a_job_is_the_one_its_manifest_recorded",
}


def _collected(*extra: str) -> set[str]:
    """Node ids (relative to the guard file) a fresh pytest collects from the guard file."""
    env = {key: value for key, value in os.environ.items() if key != "PYTEST_ADDOPTS"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", _GUARD, *extra],
        cwd=_BACKEND,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    prefix = f"{_GUARD}::"
    return {line.removeprefix(prefix) for line in result.stdout.splitlines() if line.startswith(prefix)}


class TestTheDeselectionIsRealAndExact:
    def test_without_the_option_the_recording_rules_are_left_out_and_the_rest_is_kept(self) -> None:
        collected = _collected()
        assert not collected & _NEEDS_A_RECORDING, sorted(collected & _NEEDS_A_RECORDING)
        # The rest of the file still runs where it ran: synthetic trees and the decision-shape rule.
        assert "TestTheRealTree::test_required_in_job_decisions_keep_their_fail_safe_shape" in collected
        assert any(node.startswith("TestTheSweepCanGoRed::") for node in collected)

    def test_with_the_option_exactly_the_recording_rules_are_selected(self) -> None:
        assert _collected(_OPTION, "-m", "lane_inputs_drift") == _NEEDS_A_RECORDING


def _load(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text())
    assert isinstance(document, dict), path
    return document


def _strings(node: Any) -> list[str]:
    """Every string value of a parsed YAML document — commands, never comments."""
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [text for value in node.values() for text in _strings(value)]
    if isinstance(node, list):
        return [text for value in node for text in _strings(value)]
    return []


def _triggers(document: dict[str, Any]) -> dict[str, Any]:
    # PyYAML reads a bare `on:` key as the boolean True.
    raw = document.get("on", document.get(True))
    if isinstance(raw, str):
        return {raw: None}
    if isinstance(raw, list):
        return dict.fromkeys(raw)
    return dict(raw or {})


class TestOnlyTheLaneRunsTheRulesAndItRunsNoPullRequestCode:
    def test_no_other_workflow_or_taskfile_passes_the_option(self) -> None:
        sources = [
            *sorted((_REPO_ROOT / ".github" / "workflows").glob("*.y*ml")),
            _REPO_ROOT / "Taskfile.yaml",
            *sorted((_REPO_ROOT / ".taskfiles").glob("*.y*ml")),
        ]
        # Parsed, not grepped: a comment that explains the option is not a run of it.
        offenders = [path.name for path in sources if path != _LANE and _OPTION in " ".join(_strings(_load(path)))]
        assert not offenders, offenders

    def test_the_lane_has_no_diff_driven_trigger(self) -> None:
        triggers = _triggers(_load(_LANE))
        assert set(triggers) == {"schedule", "workflow_dispatch"}, sorted(triggers)

    def test_the_guard_job_runs_the_guard_file_with_the_option(self) -> None:
        steps = _load(_LANE)["jobs"]["guard"]["steps"]
        runs = [str(step.get("run", "")) for step in steps if isinstance(step, dict)]
        with_option = [run for run in runs if _GUARD in run and f"{_OPTION} -m lane_inputs_drift" in run]
        # Once over the committed manifests, once with the recording copied in.
        assert len(with_option) == 2, runs

    def test_every_job_token_is_read_only_and_the_app_token_is_minted_only_on_develop(self) -> None:
        document = _load(_LANE)
        assert document.get("permissions") == {}, document.get("permissions")
        for job_id, job in document["jobs"].items():
            assert job.get("permissions") == {"contents": "read"}, (job_id, job.get("permissions"))
        minting = [
            step
            for job in document["jobs"].values()
            for step in job.get("steps") or []
            if isinstance(step, dict) and "create-github-app-token@" in str(step.get("uses", ""))
        ]
        assert minting, "the propose job mints no App token — a GITHUB_TOKEN pull request starts no checks"
        for step in minting:
            assert "github.ref == 'refs/heads/develop'" in str(step.get("if", "")), step
