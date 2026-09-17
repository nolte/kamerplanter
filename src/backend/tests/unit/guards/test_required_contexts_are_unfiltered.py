"""A required status check may not live in a path-filtered workflow (#1432).

THE DEFECT THIS IS WRITTEN AGAINST, MEASURED 2026-09-17.

``Integration tests (ArangoDB)`` was promoted to a required context on
``develop`` while its job sat in ``.github/workflows/backend.yml``, which is
path-filtered to ``src/backend/**`` and a handful of scripts. A pull request that
touches none of those paths does not run the workflow, so the check run is never
created, so the context never reports — and GitHub does not read "absent" as
"passed": it holds the pull request on *Expected — waiting for status to be
reported*, forever. Three open pull requests were permanently blocked that way,
each listing every other required context and not this one (``gh pr view <n>
--json statusCheckRollup``): #1470 (frontend only), #1475 (workflow only), #1410
(documentation only).

This is the twin of the failure the same repository already knows from the other
side — a path-filtered check that reports *green* on a change it never looked at
(``build-static-tests.yaml`` and ``backend-guards.yml`` both argue it at length).
Same cause, opposite symptom, and neither is visible in the workflow file alone:
the filter is legible, the *requiredness* lives in branch protection, and nothing
in the repository joined the two.

WHAT "UNFILTERED" MEANS HERE, AND WHY IT IS NOT "``on:`` HAS NO ``paths:``".

Branch protection reads the check runs on a pull request's head commit, whichever
event produced them. ``frontend.yml`` is the worked example: its ``push`` trigger
IS path-filtered, and its required ``lint-test-build (22)`` reports anyway,
because its ``pull_request`` trigger carries no ``paths:`` — deliberately, per
the header there. So the property is per-workflow and not per-trigger: *at least
one* diff-driven trigger must fire for every pull request against ``develop``.

A ``push`` trigger qualifies only when it also has no ``branches:`` filter — a
feature branch is where a pull request's head lives, and ``branches: [develop]``
means the workflow first runs after the merge. A ``pull_request`` trigger
qualifies when its ``branches:`` filter is absent or names ``develop``.

Selection that has to happen anyway belongs in a job-level ``if:``, not in the
trigger: a job skipped by ``if:`` reports a conclusion branch protection accepts,
a workflow skipped by ``paths:`` reports nothing at all. ``frontend.yml``'s
``changes`` job and ``e2e-smoke.yml``'s ``smoke`` job are the pattern.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — unreachable inside a checkout
    raise RuntimeError("checkout root not found; this guard reads .github/ and cannot run without it")

_WORKFLOW_DIR = _REPO_ROOT / ".github" / "workflows"

#: The copy of branch protection, refreshed by hand — see the file's own header.
_FIXTURE = Path(__file__).parent / "fixtures" / "required_status_contexts_develop.yaml"

_SETTINGS = _REPO_ROOT / ".github" / "settings.yml"

#: The trigger events whose filters decide whether a *diff* runs the workflow.
#: ``schedule`` and ``workflow_dispatch`` are excluded on purpose: neither fires
#: for a pull request, so neither can make a required context report.
_DIFF_DRIVEN = ("push", "pull_request", "pull_request_target")

#: The branch a pull request in this repository targets.
_TARGET_BRANCH = "develop"


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def triggers_of(document: Any) -> dict[str, Any]:
    """The ``on:`` block, whichever way YAML decided to read the key.

    PyYAML follows YAML 1.1, where a bare ``on`` is the BOOLEAN ``True`` and not
    the string ``"on"``. A reader that only asks for ``document["on"]`` finds
    nothing in every workflow in this repository and reports every one of them as
    trigger-less — a sweep that is green because it sees nothing at all.
    """
    if not isinstance(document, dict):
        return {}
    block = document.get("on", document.get(True))
    if block is None:
        return {}
    if isinstance(block, str):
        return {block: None}
    if isinstance(block, list):
        return dict.fromkeys(block)
    return dict(block)


def unfiltered_triggers(document: Any) -> list[str]:
    """Diff-driven triggers of *document* that fire for every ``develop`` pull request."""
    qualifying = []
    for event, spec in triggers_of(document).items():
        if event not in _DIFF_DRIVEN:
            continue
        spec = spec or {}
        if not isinstance(spec, dict):
            continue
        if spec.get("paths") or spec.get("paths-ignore"):
            continue
        branches = spec.get("branches")
        if event == "push":
            # A required check has to report on the pull request's HEAD, which
            # lives on a feature branch. `branches: [develop]` runs it only after
            # the merge, which is exactly too late.
            if branches or spec.get("branches-ignore"):
                continue
        elif branches is not None and _TARGET_BRANCH not in branches:
            continue
        qualifying.append(event)
    return qualifying


def job_labels(document: Any) -> dict[str, str]:
    """``job id -> the label GitHub builds the check-run name from``."""
    jobs = document.get("jobs") if isinstance(document, dict) else None
    if not isinstance(jobs, dict):
        return {}
    labels = {}
    for job_id, job in jobs.items():
        name = job.get("name") if isinstance(job, dict) else None
        labels[str(job_id)] = str(name) if name else str(job_id)
    return labels


def job_reports(context: str, job_id: str, label: str) -> bool:
    """Whether the job could produce a check run named *context*.

    Three spellings, all of which occur among this repository's required
    contexts:

    * ``Write-route and tree guards`` — a plain job, reporting its own label;
    * ``lint-test-build (22)`` — a MATRIX job, whose check runs carry the matrix
      value in parentheses. Matched on the prefix rather than by expanding the
      matrix, because the expansion is not what branch protection was told;
    * ``static / Static CI Tests`` — a job that ``uses:`` a reusable workflow,
      reporting as ``<caller job id> / <reusable job name>``. Only the left half
      belongs to this repository, so only the left half is matched.
    """
    if context == label:
        return True
    if context.startswith(f"{label} (") and context.endswith(")"):
        return True
    return context.startswith(f"{job_id} / ")


def workflows_defining(context: str, workflow_dir: Path) -> list[Path]:
    """Every workflow file carrying a job that could report *context*."""
    found = []
    for path in sorted(workflow_dir.glob("*.y*ml")):
        document = _load(path)
        if any(job_reports(context, job_id, label) for job_id, label in job_labels(document).items()):
            found.append(path)
    return found


def offenders(contexts: list[str], workflow_dir: Path) -> dict[str, str]:
    """``context -> why it cannot be relied on``, empty when every context reports."""
    findings = {}
    for context in contexts:
        defining = workflows_defining(context, workflow_dir)
        if not defining:
            findings[context] = (
                "no job in .github/workflows/ can produce this check run, so branch "
                "protection waits for a context nothing will ever report"
            )
            continue
        filtered = [path.name for path in defining if not unfiltered_triggers(_load(path))]
        if filtered:
            findings[context] = (
                f"defined in {filtered}, whose diff-driven triggers all carry a paths:/branches: "
                "filter, so a pull request outside those paths never gets this check run"
            )
    return findings


def required_contexts() -> list[str]:
    """Every context that gates a merge to ``develop``, from both sources."""
    fixture = _load(_FIXTURE)
    return sorted(set(fixture["branch_protection"]) | set(fixture["rulesets"]))


class TestEveryRequiredContextCanReport:
    """The property, over the real tree."""

    def test_no_required_context_hides_behind_a_path_filter(self) -> None:
        findings = offenders(required_contexts(), _WORKFLOW_DIR)

        assert findings == {}, (
            "A required status check must live in a workflow that runs on EVERY pull request "
            "against develop:\n"
            + "\n".join(f"  - {context}: {reason}" for context, reason in findings.items())
            + "\n\nGitHub does not treat a missing context as satisfied — it blocks the pull "
            "request indefinitely (#1470, #1475, #1410 were blocked this way on 2026-09-17). "
            "Move the job into an unfiltered lane (.github/workflows/backend-guards.yml, "
            "build-static-tests.yaml) and put any selection in a job-level `if:`, which reports "
            "a conclusion branch protection accepts. Demoting the context in "
            ".github/settings.yml is the other legitimate answer; editing this fixture is not."
        )

    def test_the_integration_tier_reports_on_every_pull_request(self) -> None:
        """The named regression, asserted on its own so the failure names it (#1432)."""
        context = "Integration tests (ArangoDB)"
        defining = workflows_defining(context, _WORKFLOW_DIR)

        assert defining, f"no job produces {context!r} any more — was it renamed without branch protection?"
        for path in defining:
            assert unfiltered_triggers(_load(path)), (
                f"{context!r} is defined in {path.name}, which is path-filtered. "
                "It is a required context; it must live in a lane with no paths: filter."
            )


class TestTheFixtureIsHeldToTheVersionedHalf:
    """A hand-copied fixture goes stale silently; this is the tripwire."""

    def test_every_protected_context_is_declared_in_settings_yml(self) -> None:
        """`.github/settings.yml` is what the Settings App syncs FROM, so it must agree."""
        settings = _load(_SETTINGS)
        develop = next(entry for entry in settings["branches"] if entry["name"] == _TARGET_BRANCH)
        declared = set(develop["protection"]["required_status_checks"]["contexts"])
        fixture = set(_load(_FIXTURE)["branch_protection"])

        assert fixture == declared, (
            "The fixture copy of branch protection and .github/settings.yml disagree.\n"
            f"  only in the fixture : {sorted(fixture - declared)}\n"
            f"  only in settings.yml: {sorted(declared - fixture)}\n"
            "Both describe the same required checks; a promotion made in the GitHub UI without "
            "a commit is the gap this catches. Refresh the fixture from `gh api` (its header "
            "carries the commands) and reconcile settings.yml."
        )


class TestTheSweepCanGoRed:
    """Otherwise the green above certifies nothing (the 2026-08-15 class)."""

    @staticmethod
    def _plant(directory: Path, name: str, body: str) -> Path:
        path = directory / name
        path.write_text(body)
        return path

    _FILTERED = """
name: Filtered
on:
  push:
    branches: [develop]
    paths: ['src/backend/**']
  pull_request:
    branches: [develop]
    paths: ['src/backend/**']
jobs:
  integration:
    name: Integration tests (ArangoDB)
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

    _UNFILTERED = """
name: Unfiltered
on:
  push:
jobs:
  integration:
    name: Integration tests (ArangoDB)
    runs-on: ubuntu-latest
    steps:
      - run: 'true'
"""

    def test_a_filtered_workflow_is_a_finding(self, tmp_path: Path) -> None:
        self._plant(tmp_path, "filtered.yml", self._FILTERED)

        findings = offenders(["Integration tests (ArangoDB)"], tmp_path)

        assert list(findings) == ["Integration tests (ArangoDB)"]
        assert "filtered.yml" in findings["Integration tests (ArangoDB)"]

    def test_an_unfiltered_workflow_is_not_a_finding(self, tmp_path: Path) -> None:
        self._plant(tmp_path, "unfiltered.yml", self._UNFILTERED)

        assert offenders(["Integration tests (ArangoDB)"], tmp_path) == {}

    def test_a_context_no_job_produces_is_a_finding(self, tmp_path: Path) -> None:
        """A renamed job is the same block, reached from the other end."""
        self._plant(tmp_path, "unfiltered.yml", self._UNFILTERED)

        findings = offenders(["Integration tests (Arango)"], tmp_path)

        assert "will ever report" in findings["Integration tests (Arango)"]

    def test_the_real_tree_supplies_every_required_context(self) -> None:
        """Guards against the whole sweep passing because it resolved nothing."""
        for context in required_contexts():
            assert workflows_defining(context, _WORKFLOW_DIR), context


class TestWhatCountsAsUnfiltered:
    """The predicate itself, over the shapes this repository actually contains."""

    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            # `backend-guards.yml` / `build-static-tests.yaml`: a bare push.
            ("on:\n  push:\n", ["push"]),
            # `frontend.yml`: filtered push, unfiltered pull_request. Reports.
            (
                "on:\n  push:\n    branches: [develop]\n    paths: ['src/frontend/**']\n"
                "  pull_request:\n    branches: [develop]\n",
                ["pull_request"],
            ),
            # `backend.yml` before this change: both halves filtered.
            (
                "on:\n  push:\n    branches: [develop]\n    paths: ['src/backend/**']\n"
                "  pull_request:\n    branches: [develop]\n    paths: ['src/backend/**']\n",
                [],
            ),
            # A push restricted to develop runs only AFTER the merge.
            ("on:\n  push:\n    branches: [develop]\n", []),
            # `paths-ignore` filters just as effectively as `paths`.
            ("on:\n  pull_request:\n    paths-ignore: ['docs/**']\n", []),
            # A pull_request aimed elsewhere never reports on a develop one.
            ("on:\n  pull_request:\n    branches: [master]\n", []),
            # Neither of these fires for a pull request at all.
            ("on:\n  schedule:\n    - cron: '0 5 * * 1'\n  workflow_dispatch:\n", []),
            # The list form of `on:`, which carries no filters by construction.
            ("on: [push, pull_request]\n", ["push", "pull_request"]),
        ],
    )
    def test_trigger_shapes(self, source: str, expected: list[str]) -> None:
        assert unfiltered_triggers(yaml.safe_load(source)) == expected

    def test_the_yaml_one_one_on_key_is_read(self) -> None:
        """`on` parses as the boolean True; a reader that misses that sees no triggers."""
        document = yaml.safe_load("on:\n  push:\n")

        assert True in document and "on" not in document
        assert triggers_of(document) == {"push": None}

    @pytest.mark.parametrize(
        ("context", "job_id", "label", "expected"),
        [
            ("Write-route and tree guards", "guards", "Write-route and tree guards", True),
            ("lint-test-build (22)", "lint-test-build", "lint-test-build", True),
            ("static / Static CI Tests", "static", "static", True),
            ("chain-bench / Chain Bench", "chain-bench", "chain-bench", True),
            ("lint-test-build (22)", "lint-test", "lint-test", False),
            ("Integration tests (ArangoDB)", "coverage", "Coverage", False),
        ],
    )
    def test_context_to_job_matching(self, context: str, job_id: str, label: str, expected: bool) -> None:
        assert job_reports(context, job_id, label) is expected
