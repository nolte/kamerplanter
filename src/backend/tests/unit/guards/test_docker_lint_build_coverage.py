"""#1463 — every Dockerfile `docker-lint-build.yml` lints, it also builds.

**The defect this is written against, measured 2026-09-17.**
``src/inference-service/Dockerfile`` was linted by the ``hadolint`` job of
``.github/workflows/docker-lint-build.yml`` and built by no job in it. The only
build of that image in the repository was ``docker-publish.yml`` — a workflow
triggered by ``push`` to ``develop``, i.e. *after* the merge that broke it. A
pull request could therefore turn the inference image unbuildable and every
check would stay green; the failure surfaced on develop, on somebody else's
change. Seven of the eight images did not have that hole, which is the shape of
this repository's most expensive defect class: a rule honoured at all its
siblings and missed at one.

**The property.** Lint coverage and build coverage over that workflow enumerate
the SAME set of Dockerfiles. Lint without build is the #1463 hole. Build without
lint is the mirror hole (an image gated for buildability but never for
Dockerfile hygiene) and is a finding too — it is what made the
``src/knowledge-service`` gap of the workflow's own header visible.

**A second, quieter failure mode: a build job that can never run.** Each
``build-*`` job is gated on ``needs.changes.outputs.<name>``. An output that the
``changes`` job does not declare evaluates to the empty string, the ``if:`` is
false, and the job is skipped on every pull request forever — present in the
file, green in the checks, inert. ``inference-service`` would have been exactly
that had the output been forgotten, so the guard asserts the wiring too, right
through to ``on.paths``: a filter path outside the workflow's own trigger paths
means the workflow never starts on the change that matters.

**Deliberately scoped to this one workflow.** It is the repository's declared
place for pre-merge image builds; a Dockerfile built somewhere else entirely is
a different question (and ``docker-publish.yml`` is post-merge by construction).
Traces to #1463 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "docker-lint-build.yml"

#: ``hadolint [flags] <path>`` inside a ``run:`` block. The PATH is taken as the
#: last whitespace-separated token rather than the first one after the command,
#: so ``hadolint --failure-threshold error src/x/Dockerfile`` and
#: ``hadolint src/x/Dockerfile`` are read the same way. A future invocation that
#: puts a flag last would go UNREAD — the regex requires the token to look like a
#: Dockerfile path, and the "every linted file is a real file" assertion below
#: turns a misread into a red test rather than into a silently shrunken sweep.
_HADOLINT_CALL = re.compile(r"\bhadolint\b[^\n]*?(?P<path>[\w./-]*Dockerfile[\w.-]*)\s*$", re.MULTILINE)

#: The build action, matched WITHOUT its digest: the pin is Renovate's to move,
#: and a sweep anchored on today's sha would quietly stop finding build steps
#: after the next bump — the measuring-tool gap, not the gate's.
_BUILD_ACTION = "docker/build-push-action@"

#: ``if: needs.changes.outputs.<name> == 'true'`` — the gate every build job uses.
_GATE = re.compile(r"needs\.changes\.outputs\.(?P<output>[\w-]+)")

#: ``${{ steps.<id>.outputs.<name> }}`` — what a ``changes`` job output is wired to.
#: The NAME on the right has to be the filter's name; nothing in GitHub checks
#: that, and a mismatch resolves to the empty string rather than to an error.
_OUTPUT_SOURCE = re.compile(r"steps\.(?P<step>[\w-]+)\.outputs\.(?P<filter>[\w-]+)")

#: The comparison a gate must make. ``if: needs.changes.outputs.x`` without it is
#: TRUE for the string ``'false'`` — a non-empty string is truthy in a GitHub
#: expression — so the job would run on every pull request that starts the
#: workflow. The opposite failure of an undeclared output, and just as silent.
_TRUTH_TEST = "== 'true'"

#: The workflow file must be in every filter: a pull request that changes only
#: HOW a build runs (``context:``, ``file:``, ``target:``, an action pin) starts
#: the workflow through ``on.paths`` and then matches no filter, so every build
#: job skips and the change is merged having built nothing.
_SELF_PATH = ".github/workflows/docker-lint-build.yml"


def load(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text())
    return document if isinstance(document, dict) else {}


def jobs_of(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    jobs = document.get("jobs")
    return {str(k): v for k, v in jobs.items() if isinstance(v, dict)} if isinstance(jobs, dict) else {}


def steps_of(job: dict[str, Any]) -> list[dict[str, Any]]:
    steps = job.get("steps")
    return [step for step in steps if isinstance(step, dict)] if isinstance(steps, list) else []


def linted_dockerfiles(document: dict[str, Any]) -> set[str]:
    """Every Dockerfile path handed to hadolint anywhere in *document*."""
    found: set[str] = set()
    for job in jobs_of(document).values():
        for step in steps_of(job):
            run = step.get("run")
            if isinstance(run, str):
                found.update(match.group("path") for match in _HADOLINT_CALL.finditer(run))
    return found


def built_dockerfiles(document: dict[str, Any]) -> set[str]:
    """Every Dockerfile path a build step in *document* would build.

    ``file:`` wins; a step that gives only ``context:`` builds ``<context>/Dockerfile``,
    which is buildx's own default and a spelling this workflow could legitimately
    adopt tomorrow.
    """
    found: set[str] = set()
    for job in jobs_of(document).values():
        for step in steps_of(job):
            uses = step.get("uses")
            if not isinstance(uses, str) or not uses.startswith(_BUILD_ACTION):
                continue
            with_ = step.get("with") if isinstance(step.get("with"), dict) else {}
            file = with_.get("file")
            if isinstance(file, str) and file:
                found.add(file.strip())
                continue
            context = with_.get("context")
            if isinstance(context, str) and context:
                found.add(f"{context.rstrip('/')}/Dockerfile")
    return found


def coverage_gaps(document: dict[str, Any]) -> dict[str, set[str]]:
    """``"linted but never built" / "built but never linted"``, both empty when aligned."""
    linted = linted_dockerfiles(document)
    built = built_dockerfiles(document)
    return {"linted but never built": linted - built, "built but never linted": built - linted}


def output_wiring_gaps(document: dict[str, Any]) -> dict[str, str]:
    """``output name -> why it cannot carry a verdict``, over the ``changes`` job.

    Two silent mis-wirings, neither of which GitHub reports (#1491 review):

    * an output whose value reads ``steps.<id>.outputs.<OTHER name>`` — the
      declaration and the filter drift apart and the output is the empty string,
      so every job gated on it skips forever;
    * an output whose value reads a step id that is not the paths-filter step.
    """
    changes = jobs_of(document).get("changes", {})
    outputs = changes.get("outputs") or {}
    filter_step = next(
        (
            str(step.get("id"))
            for step in steps_of(changes)
            if isinstance(step.get("with"), dict) and "filters" in step["with"]
        ),
        None,
    )
    filters = _declared_filters(changes)

    findings: dict[str, str] = {}
    for name, value in outputs.items():
        source = _OUTPUT_SOURCE.search(str(value))
        if source is None:
            findings[str(name)] = f"value {value!r} does not read a step output at all"
            continue
        if filter_step is not None and source.group("step") != filter_step:
            findings[str(name)] = f"reads step {source.group('step')!r}, but the paths-filter step is {filter_step!r}"
            continue
        if source.group("filter") != str(name):
            findings[str(name)] = (
                f"reads the filter {source.group('filter')!r}. A `changes` output whose name and filter "
                "differ resolves to the EMPTY STRING, so every job gated on it skips on every pull "
                "request — present, green and inert"
            )
            continue
        if filters and str(name) not in filters:
            findings[str(name)] = f"no filter named {name!r} is declared in the paths-filter step"
    return findings


def gate_gaps(document: dict[str, Any]) -> dict[str, str]:
    """``job id -> why its gate can never be true``, empty when every build job can run."""
    changes = jobs_of(document).get("changes", {})
    declared = set(changes.get("outputs", {}) or {})
    filters = _declared_filters(changes)
    trigger_paths = _pull_request_paths(document)
    workflow_path = _workflow_path(document)

    findings: dict[str, str] = {}
    for job_id, job in jobs_of(document).items():
        if job_id == "changes" or not any(
            isinstance(step.get("uses"), str) and step["uses"].startswith(_BUILD_ACTION) for step in steps_of(job)
        ):
            continue
        condition = job.get("if")
        referenced = set(_GATE.findall(str(condition))) if condition is not None else set()
        if not referenced:
            continue
        missing = sorted(referenced - declared)
        if missing:
            findings[job_id] = f"gated on outputs the `changes` job does not declare: {missing}"
            continue
        if _TRUTH_TEST not in str(condition):
            findings[job_id] = (
                f"gate {str(condition)!r} does not compare {_TRUTH_TEST}. A bare "
                "`needs.changes.outputs.x` is TRUE for the string 'false' — a non-empty string is truthy "
                "in a GitHub expression — so the job runs whenever the workflow starts"
            )
            continue
        for output in sorted(referenced):
            patterns = filters.get(output, [])
            uncovered = [pattern for pattern in patterns if not _covered_by(pattern, trigger_paths)]
            if uncovered:
                findings[job_id] = (
                    f"filter {output!r} watches {uncovered}, which `on.pull_request.paths` does not "
                    "carry — the workflow never starts on those changes"
                )
                continue
            if workflow_path is not None and workflow_path not in patterns:
                findings[job_id] = (
                    f"filter {output!r} does not watch {workflow_path!r}. A pull request that changes only "
                    "HOW this job builds — `context:`, `file:`, `target:`, an action pin — starts the "
                    "workflow through `on.paths` and then matches no filter, so this job skips and the "
                    "change is merged having built nothing"
                )
    return findings


def _workflow_path(document: dict[str, Any]) -> str | None:
    """The workflow's own path, as its ``on.paths`` spells it.

    Read from the trigger rather than from ``__file__`` so the synthetic
    documents in the tests below carry their own answer, and so a renamed
    workflow is a finding here instead of a silently skipped check.
    """
    return next(
        (path for path in _pull_request_paths(document) if path.endswith(".yml") or path.endswith(".yaml")),
        None,
    )


def _declared_filters(changes_job: dict[str, Any]) -> dict[str, list[str]]:
    """``filter name -> its path patterns``, read out of the paths-filter step."""
    for step in steps_of(changes_job):
        filters = step.get("with", {}).get("filters") if isinstance(step.get("with"), dict) else None
        if isinstance(filters, str):
            parsed = yaml.safe_load(filters)
            if isinstance(parsed, dict):
                return {str(name): list(patterns or []) for name, patterns in parsed.items()}
    return {}


def _pull_request_paths(document: dict[str, Any]) -> list[str]:
    # `on` is the YAML 1.1 boolean True, not the string "on" (see
    # test_required_contexts_are_unfiltered.py, which pays for the same trap).
    triggers = document.get("on", document.get(True)) or {}
    spec = triggers.get("pull_request") if isinstance(triggers, dict) else None
    paths = spec.get("paths") if isinstance(spec, dict) else None
    return [str(pattern) for pattern in paths] if isinstance(paths, list) else []


def _covered_by(pattern: str, trigger_paths: list[str]) -> bool:
    """Whether a `changes` filter pattern is also watched by the workflow trigger."""
    if pattern in trigger_paths:
        return True
    prefix = pattern.split("*", 1)[0]
    return any(trigger.split("*", 1)[0] and prefix.startswith(trigger.split("*", 1)[0]) for trigger in trigger_paths)


class TestTheRealWorkflow:
    """The property, over the file that actually gates merges."""

    def test_lint_and_build_cover_the_same_dockerfiles(self) -> None:
        gaps = {label: sorted(paths) for label, paths in coverage_gaps(load(_WORKFLOW)).items() if paths}

        assert gaps == {}, (
            f"{_WORKFLOW.name} must lint and build the same set of Dockerfiles:\n"
            + "\n".join(f"  - {label}: {paths}" for label, paths in gaps.items())
            + "\n\nA Dockerfile linted but not built here is built only by docker-publish.yml, which "
            "runs on push to develop — after the merge that broke it (#1463). Add a `build-*` job "
            "beside its siblings, or stop linting the file here."
        )

    def test_every_build_job_can_actually_run(self) -> None:
        """A job gated on an undeclared output is present, green and inert."""
        assert gate_gaps(load(_WORKFLOW)) == {}, gate_gaps(load(_WORKFLOW))

    def test_every_changes_output_is_wired_to_its_own_filter(self) -> None:
        """Name and filter must agree; a mismatch is the empty string (#1491 review)."""
        assert output_wiring_gaps(load(_WORKFLOW)) == {}, output_wiring_gaps(load(_WORKFLOW))

    def test_every_filter_watches_the_workflow_file_itself(self) -> None:
        """A change to HOW a build runs must run the builds (#1491 review)."""
        document = load(_WORKFLOW)
        filters = _declared_filters(jobs_of(document)["changes"])

        assert filters, "no filters read out of the changes job — the assertion below would be vacuous"
        for name, patterns in filters.items():
            assert _SELF_PATH in patterns, (
                f"filter {name!r} does not watch {_SELF_PATH}. A pull request that only edits this "
                "workflow — a `context:`, a `file:`, a `target:`, an action pin — would start it and skip "
                f"build-{name}, merging a change to the build having built nothing."
            )

    def test_every_linted_dockerfile_exists(self) -> None:
        """If the path regex misread a line, the sweep shrank — this makes that red."""
        linted = linted_dockerfiles(load(_WORKFLOW))
        assert len(linted) >= 8, f"only {len(linted)} Dockerfiles read out of the lint job — regex drift?"
        for path in sorted(linted):
            assert (_REPO_ROOT / path).is_file(), f"lint job names {path}, which is not a file"

    def test_the_inference_image_is_built_before_merge(self) -> None:
        """The named regression, asserted on its own so the failure names it (#1463)."""
        document = load(_WORKFLOW)
        assert "src/inference-service/Dockerfile" in built_dockerfiles(document)
        assert "build-inference-service" in jobs_of(document)


class TestTheSweepCanGoRed:
    """Otherwise the green above certifies nothing (the 2026-08-15 class)."""

    _LINTED_NOT_BUILT = """
name: x
on:
  pull_request:
    paths: ['src/lonely/**']
jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      lonely: ${{ steps.filter.outputs.lonely }}
    steps:
      - uses: dorny/paths-filter@v4
        id: filter
        with:
          filters: |
            lonely:
              - 'src/lonely/**'
  hadolint:
    runs-on: ubuntu-latest
    steps:
      - name: Lint lonely Dockerfile
        run: |
          docker run --rm hadolint src/lonely/Dockerfile
"""

    _ALIGNED = (
        _LINTED_NOT_BUILT
        + """
  build-lonely:
    needs: [changes, hadolint]
    if: needs.changes.outputs.lonely == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: docker/build-push-action@deadbeef
        with:
          context: src/lonely
          file: src/lonely/Dockerfile
          push: false
"""
    )

    #: The same job, gated on an output nobody declares — present and inert.
    _INERT_GATE = _ALIGNED.replace("needs.changes.outputs.lonely", "needs.changes.outputs.lonley")

    #: The same job, watching a path the trigger never fires on.
    _UNWATCHED = _ALIGNED.replace("paths: ['src/lonely/**']", "paths: ['src/other/**']")

    def test_a_linted_but_unbuilt_dockerfile_is_a_finding(self) -> None:
        gaps = coverage_gaps(yaml.safe_load(self._LINTED_NOT_BUILT))

        assert gaps["linted but never built"] == {"src/lonely/Dockerfile"}
        assert gaps["built but never linted"] == set()

    def test_an_aligned_workflow_is_not_a_finding(self) -> None:
        assert all(not paths for paths in coverage_gaps(yaml.safe_load(self._ALIGNED)).values())

    def test_a_built_but_unlinted_dockerfile_is_a_finding(self) -> None:
        document = yaml.safe_load(self._ALIGNED)
        document["jobs"]["hadolint"]["steps"] = []

        assert coverage_gaps(document)["built but never linted"] == {"src/lonely/Dockerfile"}

    def test_a_context_only_build_step_counts_as_building(self) -> None:
        """buildx's own default spelling — a gap the `file:`-only reader would invent."""
        document = yaml.safe_load(self._ALIGNED)
        del document["jobs"]["build-lonely"]["steps"][0]["with"]["file"]

        assert coverage_gaps(document)["linted but never built"] == set()

    def test_hadolint_with_leading_flags_is_still_read(self) -> None:
        document = yaml.safe_load(
            self._LINTED_NOT_BUILT.replace(
                "hadolint src/lonely/Dockerfile", "hadolint --failure-threshold error src/lonely/Dockerfile"
            )
        )

        assert linted_dockerfiles(document) == {"src/lonely/Dockerfile"}

    def test_an_undeclared_output_is_a_gate_finding(self) -> None:
        findings = gate_gaps(yaml.safe_load(self._INERT_GATE))

        assert "build-lonely" in findings
        assert "lonley" in findings["build-lonely"]

    def test_a_filter_outside_the_trigger_paths_is_a_gate_finding(self) -> None:
        findings = gate_gaps(yaml.safe_load(self._UNWATCHED))

        assert "build-lonely" in findings
        assert "never starts" in findings["build-lonely"]

    def test_an_aligned_workflow_has_no_gate_finding(self) -> None:
        assert gate_gaps(yaml.safe_load(self._ALIGNED)) == {}

    #: The aligned document, plus the two properties the #1491 review added:
    #: the workflow file in the filter and an `== 'true'` comparison.
    _COMPLETE = _ALIGNED.replace(
        "    paths: ['src/lonely/**']",
        "    paths: ['src/lonely/**', '.github/workflows/x.yml']",
    ).replace(
        "            lonely:\n              - 'src/lonely/**'",
        "            lonely:\n              - 'src/lonely/**'\n              - '.github/workflows/x.yml'",
    )

    def test_the_complete_shape_has_no_gate_finding(self) -> None:
        """The positive control for the two properties below."""
        assert gate_gaps(yaml.safe_load(self._COMPLETE)) == {}

    def test_a_filter_not_watching_the_workflow_file_is_a_finding(self) -> None:
        """S2: the build would skip on a change to how it builds.

        The mutation keeps the workflow path in ``on.paths`` and removes it from
        the FILTER, which is the real defect exactly: the workflow starts and
        every build job skips.
        """
        half_wired = self._COMPLETE.replace("\n              - '.github/workflows/x.yml'", "")
        findings = gate_gaps(yaml.safe_load(half_wired))

        assert "build-lonely" in findings
        assert "built nothing" in findings["build-lonely"]

    def test_a_gate_without_the_true_comparison_is_a_finding(self) -> None:
        """S1: a bare output is truthy for the STRING 'false'."""
        truthy = self._COMPLETE.replace(
            "if: needs.changes.outputs.lonely == 'true'", "if: needs.changes.outputs.lonely"
        )
        findings = gate_gaps(yaml.safe_load(truthy))

        assert "build-lonely" in findings
        assert "== 'true'" in findings["build-lonely"]

    def test_an_output_wired_to_the_wrong_filter_is_a_finding(self) -> None:
        """S1: the mis-wiring GitHub resolves to the empty string."""
        crossed = self._COMPLETE.replace(
            "lonely: ${{ steps.filter.outputs.lonely }}", "lonely: ${{ steps.filter.outputs.lonley }}"
        )
        findings = output_wiring_gaps(yaml.safe_load(crossed))

        assert "lonely" in findings
        assert "EMPTY STRING" in findings["lonely"]

    def test_an_output_wired_to_the_wrong_step_is_a_finding(self) -> None:
        crossed = self._COMPLETE.replace("steps.filter.outputs.lonely", "steps.detect.outputs.lonely")
        findings = output_wiring_gaps(yaml.safe_load(crossed))

        assert "lonely" in findings
        assert "paths-filter step is 'filter'" in findings["lonely"]

    def test_a_correctly_wired_output_is_not_a_finding(self) -> None:
        assert output_wiring_gaps(yaml.safe_load(self._COMPLETE)) == {}
