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


def gate_gaps(document: dict[str, Any]) -> dict[str, str]:
    """``job id -> why its gate can never be true``, empty when every build job can run."""
    changes = jobs_of(document).get("changes", {})
    declared = set(changes.get("outputs", {}) or {})
    filters = _declared_filters(changes)
    trigger_paths = _pull_request_paths(document)

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
        for output in sorted(referenced):
            uncovered = [pattern for pattern in filters.get(output, []) if not _covered_by(pattern, trigger_paths)]
            if uncovered:
                findings[job_id] = (
                    f"filter {output!r} watches {uncovered}, which `on.pull_request.paths` does not "
                    "carry — the workflow never starts on those changes"
                )
    return findings


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
