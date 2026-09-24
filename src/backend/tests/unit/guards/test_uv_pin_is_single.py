"""#1383 — the uv version is named in one place, and the workflows read it.

**What this guards.** Until #1383 the uv version lived in eight literal
``pip install 'uv==<version>'`` strings spread over four workflow files, plus
``[tool.uv].required-version`` in five ``pyproject.toml`` and five Dockerfile
image tags. Nothing kept them equal. The ``uv toolchain`` group in
``renovate.json5`` moved them together *in practice* — PR #1447 bumped all eight
in one pull request — but a group is a promise about the sites it knows, not a
mechanism: a ninth site added by someone who did not know about the group ages
on its own, and the first symptom is a lock relocked by a different resolver
than the one that installs it (#1296).

``astral-sh/setup-uv`` with ``version-file:`` removed the literals. This file is
the absence check that keeps them removed, because the acceptance criterion
"``grep -rn 'uv==' .github/workflows/`` returns nothing" is otherwise a fact
about one afternoon.

**Why an absence check and not just the Renovate group.** NFR-018 §1: a rule
nothing can violate visibly is not a rule. A reintroduced literal would be
perfectly valid YAML, would run, and would be wrong only later.

**Deliberately narrow.** This says nothing about *which* uv version is right —
that is ``[tool.uv].required-version`` and the ``uv toolchain`` group's job. It
says only that no workflow names one itself, and that every ``setup-uv`` step
points at a file that really carries the pin. Traces to #1383 (no TC-ID: CI
configuration is not a user-facing case).
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_WORKFLOW_DIR = _REPO_ROOT / ".github" / "workflows"

# The exact shape the acceptance criterion greps for, plus the quoted and
# double-quoted spellings of the same thing, so a literal cannot slip back in by
# changing its quoting. `uv>=`/`uv~=` are matched too: a floor is the same defect
# with a wider blast radius, not a lesser one.
_LITERAL_UV_PIN = re.compile(r"""["']?\buv["']?\s*(==|>=|~=|<=)\s*["']?\d""")

# `uses: astral-sh/setup-uv@<40 hex> # vX.Y.Z` — the repository's action-pinning
# convention (helpers:pinGitHubActionDigests + a version comment).
_SETUP_UV_USES = re.compile(r"^astral-sh/setup-uv@(?P<sha>[0-9a-f]{40})$")


def _workflow_files() -> list[Path]:
    files = sorted(p for p in _WORKFLOW_DIR.glob("*.y*ml") if p.is_file())
    assert files, f"no workflow files under {_WORKFLOW_DIR} — the sweep would be vacuously green"
    return files


def _steps(document: object) -> list[dict[str, object]]:
    """Every mapping under any job's ``steps:``, across the whole document."""
    steps: list[dict[str, object]] = []
    jobs = document.get("jobs", {}) if isinstance(document, dict) else {}
    if not isinstance(jobs, dict):
        return steps
    for job in jobs.values():
        if not isinstance(job, dict):
            continue
        for step in job.get("steps", []) or []:
            if isinstance(step, dict):
                steps.append(step)
    return steps


class TestNoWorkflowNamesAUvVersion:
    """The acceptance criterion of #1383, made permanent."""

    def test_no_workflow_file_carries_a_literal_uv_version(self) -> None:
        offenders: list[str] = []
        for path in _workflow_files():
            for lineno, line in enumerate(path.read_text().splitlines(), start=1):
                # Comments may DESCRIBE the old shape (several do, at length);
                # only executable YAML is under this rule.
                code = line.split("#", 1)[0]
                if _LITERAL_UV_PIN.search(code):
                    offenders.append(f"{path.relative_to(_REPO_ROOT)}:{lineno}: {line.strip()}")

        assert not offenders, (
            "A workflow names a uv version itself. The version belongs in "
            "[tool.uv].required-version and nowhere else; workflows read it through "
            "`astral-sh/setup-uv` with `version-file:` (#1383). Offending lines:\n  " + "\n  ".join(offenders)
        )

    def test_the_sweep_sees_the_workflows_that_install_uv(self) -> None:
        """Absence checks fail open. Name the files this one must have read.

        If `backend.yml` were ever renamed or moved out of `.github/workflows/`,
        the sweep above would go green having inspected a set that no longer
        contains the interesting file — the failure class this repository keeps
        hitting (a measuring tool with a gap that looks complete).
        """
        names = {p.name for p in _workflow_files()}
        # side-services.yml is in this list since #1374/#1383: it carries two
        # `setup-uv` steps of its own (knowledge-service, inference-service), so
        # a sweep that never opened it would miss a third of the uv installs
        # while looking complete.
        for expected in (
            "backend.yml",
            "backend-guards.yml",
            "api-docs.yml",
            "release-publish.yml",
            "side-services.yml",
        ):
            assert expected in names, f"{expected} is not under {_WORKFLOW_DIR} — the uv sweep lost its subject"


class TestEverySetupUvStepReadsThePin:
    """`setup-uv` without `version-file:` installs *latest* — silently."""

    def test_setup_uv_steps_exist(self) -> None:
        found = [
            step
            for path in _workflow_files()
            for step in _steps(yaml.safe_load(path.read_text()))
            if isinstance(step.get("uses"), str) and step["uses"].startswith("astral-sh/setup-uv@")
        ]
        assert found, (
            "No workflow uses astral-sh/setup-uv. Either the action was removed — in which case "
            "something is installing uv another way and the checks below measure nothing — or the "
            "pin convention changed and this file must follow it (#1383)."
        )

    def test_every_setup_uv_step_is_digest_pinned_and_reads_a_real_version_file(self) -> None:
        problems: list[str] = []
        for path in _workflow_files():
            document = yaml.safe_load(path.read_text())
            for step in _steps(document):
                uses = step.get("uses")
                if not isinstance(uses, str) or not uses.startswith("astral-sh/setup-uv@"):
                    continue
                where = f"{path.relative_to(_REPO_ROOT)} step {step.get('name', uses)!r}"

                if not _SETUP_UV_USES.match(uses):
                    problems.append(f"{where}: not pinned to a 40-character commit SHA ({uses})")

                inputs = step.get("with")
                version_file = inputs.get("version-file") if isinstance(inputs, dict) else None
                if not version_file:
                    problems.append(
                        f"{where}: no `version-file:` — the action would install the LATEST uv, "
                        "not [tool.uv].required-version"
                    )
                    continue

                target = _REPO_ROOT / str(version_file)
                if not target.is_file():
                    problems.append(f"{where}: version-file {version_file} does not exist")
                    continue
                pin = tomllib.loads(target.read_text()).get("tool", {}).get("uv", {}).get("required-version")
                if not pin:
                    problems.append(f"{where}: {version_file} carries no [tool.uv].required-version to read")
                elif not str(pin).startswith("=="):
                    problems.append(
                        f"{where}: {version_file} pins [tool.uv].required-version to {pin!r}, which is not an "
                        "exact `==` specifier. TWO readers degrade silently on anything else, and neither "
                        "goes red: (1) the `uv toolchain` customManager in renovate.json5 matches "
                        '`required-version = "==(?<currentValue>...)"` and simply stops tracking the pin; '
                        "(2) tests/unit/guards/test_lock_hash_verification.py's _required_uv_version() returns "
                        "None and the hash falsifier stops checking that the uv on PATH is the pinned one. "
                        "Loosen this only together with both."
                    )

        assert not problems, "setup-uv steps that do not resolve the pin (#1383):\n  " + "\n  ".join(problems)
