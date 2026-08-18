"""Tests for the release-side develop-channel reservation.

**What is under test.** ``scripts/ci/determine_chart_version.sh`` — the step that
resolves the Helm chart version inside ``docker-publish.yml``'s
``publish-helm-charts`` job, and refuses a release tag whose first dot-separated
pre-release identifier is ``dev``.

**Why the reservation exists.** ``scripts/check_chart_develop_version.py`` keeps
``helm/*/Chart.yaml`` on a ``-dev`` version so that a ``helm/**`` merge can never
republish a released version reference (#1222). That static rule is *sufficient*
only while no release tag carries a ``-dev`` pre-release — tag ``v0.3.0-dev`` and
the release path would resolve the chart version to ``0.3.0-dev`` and publish
``charts/kamerplanter:0.3.0-dev``, the very OCI tag every develop merge
overwrites. This script turns that premise from an assumption into a rule, at the
one moment it is decidable: the tag ref itself.

**Why ``subprocess`` and not** ``tests.support.repo_scripts.load_repo_script``.
That loader executes a ``scripts/**.py`` module; the artifact under test is bash,
because it replaces bash that ran inline in the workflow and must keep running on
a bare runner. So it is invoked exactly as the workflow invokes it — as a
process, with ``REF``/``REF_NAME`` in the environment and ``GITHUB_OUTPUT``
pointing at a file — and the *checkout discovery* still goes through
``repo_scripts.find_repo_root`` rather than a hard-coded ``parents[N]``, which
breaks silently the moment a file moves. There is no other test for a
``scripts/ci/*.sh`` in this repository; this is the first, and it is deliberately
minimal: environment in, exit code and ``GITHUB_OUTPUT`` out. No network, no
live git, no live registry.

**The falsification carrier** is :class:`TestItCanFail`: revert the rejection in
the script and ``test_a_dev_release_tag_is_refused`` goes red. :class:`TestTheWiring`
is the second half of it — a rejection that the workflow no longer calls would
still pass every process test while being entirely inert in CI, so the step is
asserted to invoke the script *and* to sit ahead of ``helm package`` and
``helm push``. A rejection after the push would be theatre.

:class:`TestTheBlastRadiusIsDisclosed` is the third half of it. The rejection
fires *after* the GitHub release for the tag exists, and ``update-release-assets``
is gated on this job not failing — so refusing a ``-dev`` tag costs that release
its chart, its compose file, its env example and its Packages block. That is a
property of the workflow, measured here, and the script header is required to
say so: an undisclosed cost is one the person tagging pays without being asked.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package, so it is reached by path. It is not a
backend test in subject; it is one in placement, because this is the tier that
runs.

Traces to issue #1222 (no TC-ID: a release-path gate is not a user-facing case).
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found; the CI scripts are unreachable", allow_module_level=True)
if os.name != "posix":  # pragma: no cover — CI and every dev box here is POSIX
    pytest.skip("the script under test is a bash program", allow_module_level=True)

SCRIPT = _REPO_ROOT / "scripts" / "ci" / "determine_chart_version.sh"
WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "docker-publish.yml"

if not SCRIPT.is_file():  # pragma: no cover — only on a partial checkout
    pytest.skip(f"{SCRIPT} does not exist", allow_module_level=True)

#: The job and step the reservation lives in, and the two steps it must precede.
CHART_JOB = "publish-helm-charts"
VERSION_STEP = "Determine chart version"
PUBLISHING_STEPS = ("Package chart", "Push chart to GHCR")

#: The job that carries every non-chart release asset and is chained to
#: :data:`CHART_JOB`'s result. A rejection here skips it — see
#: :class:`TestTheBlastRadiusIsDisclosed`.
ASSET_JOB = "update-release-assets"


@dataclass(frozen=True)
class Resolution:
    """One invocation of the script, as GitHub Actions would see it."""

    returncode: int
    stdout: str
    stderr: str
    step_outputs: dict[str, str]

    @property
    def version(self) -> str | None:
        """The value the ``version`` step output carries, or None if unset.

        None and ``""`` are different outcomes: the empty string is what the two
        release-only steps downstream test against, while an absent output means
        nothing downstream can run at all.
        """
        return self.step_outputs.get("version")


def resolve(ref: str, ref_name: str | None, tmp_path: Path) -> Resolution:
    """Run the script with *ref* / *ref_name* in the environment.

    Args:
        ref: The value of ``github.ref``.
        ref_name: The value of ``github.ref_name``; None leaves it unset.
        tmp_path: Directory receiving the throwaway ``GITHUB_OUTPUT`` file.

    Returns:
        Exit code, both streams, and the parsed step outputs.
    """
    output_file = tmp_path / "github_output"
    output_file.touch()

    env = {"PATH": os.environ.get("PATH", ""), "REF": ref, "GITHUB_OUTPUT": str(output_file)}
    if ref_name is not None:
        env["REF_NAME"] = ref_name

    # Fixed argv, no shell, and an explicit timeout: the script is a repository
    # artifact, and nothing in it reaches the network.
    completed = subprocess.run(
        [str(SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    outputs: dict[str, str] = {}
    for line in output_file.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            outputs[key] = value

    return Resolution(completed.returncode, completed.stdout, completed.stderr, outputs)


class TestTheResolutionIsUnchanged:
    """The behaviour the workflow step had before the reservation was added.

    Moving logic out of a workflow into a script is only safe if the move is
    provably verbatim, so both branches of the original ``if`` are pinned.
    """

    def test_a_branch_ref_resolves_to_the_empty_version(self, tmp_path: Path) -> None:
        """The empty string is what keeps the release-only steps from running."""
        result = resolve("refs/heads/develop", "develop", tmp_path)

        assert result.returncode == 0, result.stderr
        assert result.version == ""

    def test_a_release_tag_resolves_to_the_tag_without_its_v(self, tmp_path: Path) -> None:
        """``${REF_NAME#v}`` — the value that is written into Chart.yaml."""
        result = resolve("refs/tags/v0.3.0", "v0.3.0", tmp_path)

        assert result.returncode == 0, result.stderr
        assert result.version == "0.3.0"
        assert result.stdout.strip() == "0.3.0"

    def test_the_next_published_release_still_resolves(self, tmp_path: Path) -> None:
        """``v0.2.1`` is the draft release that exists today; it must pass."""
        result = resolve("refs/tags/v0.2.1", "v0.2.1", tmp_path)

        assert result.returncode == 0, result.stderr
        assert result.version == "0.2.1"

    def test_a_pull_request_ref_is_treated_as_a_non_tag(self, tmp_path: Path) -> None:
        """Anything that is not ``refs/tags/v*`` takes the develop branch path."""
        result = resolve("refs/pull/42/merge", "42/merge", tmp_path)

        assert result.returncode == 0, result.stderr
        assert result.version == ""


class TestItCanFail:
    """The reserved tag, and the step going red on it.

    Delete the rejection from the script and every test in this class goes red;
    that is the whole point of the package. A gate nobody has watched fail is a
    gate nobody knows works (NFR-018 §2).
    """

    def test_a_dev_release_tag_is_refused(self, tmp_path: Path) -> None:
        """``v0.3.0-dev`` is the back door #1222 would come back through."""
        result = resolve("refs/tags/v0.3.0-dev", "v0.3.0-dev", tmp_path)

        assert result.returncode != 0

    def test_the_refusal_names_the_tag_and_the_reason(self, tmp_path: Path) -> None:
        """A red run that does not say which tag or why costs an investigation."""
        result = resolve("refs/tags/v0.3.0-dev", "v0.3.0-dev", tmp_path)

        assert "v0.3.0-dev" in result.stderr
        assert "develop channel" in result.stderr
        assert "#1222" in result.stderr

    def test_the_refusal_is_annotated_for_the_actions_log(self, tmp_path: Path) -> None:
        """``::error::`` is how the message surfaces on the run summary."""
        result = resolve("refs/tags/v0.3.0-dev", "v0.3.0-dev", tmp_path)

        assert result.stderr.startswith("::error::")

    def test_nothing_is_handed_downstream_when_the_tag_is_refused(self, tmp_path: Path) -> None:
        """No ``version`` output means no chart is packaged under the reserved tag.

        The rejection has to happen before anything is published; leaving a
        resolved version behind would let a re-run or a follow-on step use it.
        """
        result = resolve("refs/tags/v0.3.0-dev", "v0.3.0-dev", tmp_path)

        assert result.version is None

    def test_a_dotted_dev_identifier_is_refused_too(self, tmp_path: Path) -> None:
        """``dev.4`` has ``dev`` as its first identifier and collides just as well."""
        result = resolve("refs/tags/v0.3.0-dev.4", "v0.3.0-dev.4", tmp_path)

        assert result.returncode != 0

    def test_a_missing_ref_name_on_a_tag_ref_is_refused(self, tmp_path: Path) -> None:
        """Resolving to the bare empty version on a tag would skip the rewrite silently."""
        result = resolve("refs/tags/v0.3.0", None, tmp_path)

        assert result.returncode != 0
        assert result.version is None


class TestTheReservationIsNarrow:
    """Only ``dev`` is reserved — every other pre-release stays releasable.

    A guard that rejected *any* pre-release would forbid release candidates,
    which this repository has no reason to give up, and it would make the rule
    something other than the one the static checker's sufficiency rests on.
    """

    @pytest.mark.parametrize(
        ("tag", "expected"),
        [
            ("v0.3.0-rc1", "0.3.0-rc1"),
            ("v0.3.0-rc.1", "0.3.0-rc.1"),
            ("v0.3.0-beta.1", "0.3.0-beta.1"),
            # `development` is a different identifier from `dev`, so it cannot
            # collide with the value the develop tree carries.
            ("v0.3.0-development", "0.3.0-development"),
            # Build metadata is not a pre-release: `0.3.0+dev` and `0.3.0-dev`
            # are different versions and different OCI tags.
            ("v0.3.0+dev", "0.3.0+dev"),
            # SemVer pre-release identifiers are case-sensitive, and the develop
            # tree carries lowercase `dev`.
            ("v0.3.0-DEV", "0.3.0-DEV"),
        ],
    )
    def test_a_non_dev_pre_release_tag_is_released_normally(self, tag: str, expected: str, tmp_path: Path) -> None:
        """Each of these must reach `helm package` untouched."""
        result = resolve(f"refs/tags/{tag}", tag, tmp_path)

        assert result.returncode == 0, result.stderr
        assert result.version == expected


class TestTheWiring:
    """The workflow calls the script, and calls it before it publishes anything.

    Without these two assertions the reservation could be perfectly correct and
    completely inert — the failure class this repository has paid for most often.
    """

    @staticmethod
    def _chart_job_steps() -> list[dict[str, object]]:
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        steps = workflow["jobs"][CHART_JOB]["steps"]
        assert isinstance(steps, list)
        return steps

    @staticmethod
    def _index_of(steps: list[dict[str, object]], name: str) -> int:
        for index, step in enumerate(steps):
            if step.get("name") == name:
                return index
        raise AssertionError(f"no step named {name!r} in {CHART_JOB}: {[s.get('name') for s in steps]}")

    def test_the_version_step_invokes_the_script(self) -> None:
        """Inline logic here would be a second copy of the rule, untested."""
        steps = self._chart_job_steps()
        step = steps[self._index_of(steps, VERSION_STEP)]

        assert "scripts/ci/determine_chart_version.sh" in str(step["run"])

    def test_the_script_is_executable(self) -> None:
        """The workflow calls it as a program; a lost mode bit fails the release."""
        assert os.access(SCRIPT, os.X_OK)

    @pytest.mark.parametrize("publishing_step", PUBLISHING_STEPS)
    def test_the_rejection_precedes_publication(self, publishing_step: str) -> None:
        """Rejecting after `helm push` would leave the artifact published."""
        steps = self._chart_job_steps()

        assert self._index_of(steps, VERSION_STEP) < self._index_of(steps, publishing_step)


class TestTheBlastRadiusIsDisclosed:
    """Finding F-3: what this rejection costs, measured and written down.

    The workflow is triggered *by* the tag, so the GitHub release for a
    ``v0.3.0-dev`` tag is already published when this script fires — and
    ``update-release-assets`` is gated on this job not failing. The rejection
    therefore leaves a published release with no chart, no compose file, no env
    example and no Packages block: the #1218 damage, caused by our own check.

    Two assertions, and they are only worth something together. The first
    *measures* the coupling in the workflow, so it goes red if the chaining is
    ever changed — at which point the header would be stating something false.
    The second requires the header to disclose it, so a reader deciding whether
    to tag ``-dev`` learns the cost from the file that imposes it rather than
    from a release that came out half-built.
    """

    @staticmethod
    def _header() -> str:
        """The script's leading comment block, up to the first executable line."""
        text = SCRIPT.read_text(encoding="utf-8")
        head, marker, _ = text.partition("set -euo pipefail")
        assert marker, "the script no longer starts with a comment header followed by `set -euo pipefail`"
        return head

    def test_the_asset_job_is_chained_to_this_jobs_result(self) -> None:
        """The coupling itself — the reason a chart rejection costs the assets."""
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        job = workflow["jobs"][ASSET_JOB]

        assert CHART_JOB in job["needs"]
        assert "!contains(needs.*.result, 'failure')" in " ".join(str(job["if"]).split())

    def test_the_asset_job_carries_the_artifacts_the_header_names(self) -> None:
        """Named concretely, so the disclosure cannot outlive what it describes."""
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        run_bodies = " ".join(str(step.get("run", "")) for step in workflow["jobs"][ASSET_JOB]["steps"])

        assert "docker-compose" in run_bodies
        assert ".env.example" in run_bodies

    def test_the_header_discloses_the_skipped_asset_job(self) -> None:
        """Disclosing only the eight images understates the cost by three artifacts."""
        header = self._header()

        assert ASSET_JOB in header
        assert "docker-compose" in header
        assert ".env.example" in header

    def test_the_header_says_the_release_is_already_published_when_this_runs(self) -> None:
        """The decisive fact: this check cannot prevent the release, only the chart."""
        header = self._header()

        assert "#1218" in header
        assert "already" in header
