"""#1764 — every pinned model target is built and probed before merge, not only the shipped ones.

**The defect this is written against, measured 2026-09-25.** Since #1763 the
contract probe (``scripts/ci/probe_model_service_contract.py``) compares a
running model image against ``docker/<service>/golden/<target>.json``, and a
golden file exists for all six pinned models. But ``docker-lint-build.yml``
built exactly one target per image — ``minilm`` (no ``target:``, so the last
stage) and ``bge-reranker-v2-m3`` — so ``e5-small``, ``e5-base``, ``e5-large``
and ``ms-marco-minilm`` were compared against their golden outputs nowhere. A
change to the shared runtime that broke only one of them passed CI.

**The property, over the class.** The governed set is derived, not listed: every
final stage of every Dockerfile that ships a pinned Hugging Face download — the
same enumeration ``test_model_golden_outputs_match_pins.py`` binds golden files
to. For each, ``docker-lint-build.yml`` has a job whose build step produces
that target (a literal ``target:``, a ``${{ matrix.target }}`` leg, or — with
no ``target:`` — the Dockerfile's last stage) and that job runs the contract
probe against the tag it built. A matrix build keeps one gha cache scope per
leg: concurrent legs sharing one scope overwrite each other's cache manifest.

Traces to #1764 (no TC-ID: CI configuration is not a user-facing case).
"""

from __future__ import annotations

import re
import shlex
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root
from tests.unit.guards.test_model_golden_outputs_match_pins import _TARGETS
from tests.unit.guards.test_model_images_prove_readiness import (
    _find_build,
    _runs,
    _strip_shell_comments,
)

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "docker-lint-build.yml"
_PROBE = "scripts/ci/probe_model_service_contract.py"
_MATRIX_TARGET = re.compile(r"^\$\{\{\s*matrix\.target\s*\}\}$")
_STAGE = re.compile(r"^\s*FROM\s+\S+\s+AS\s+(\S+)\s*$", re.IGNORECASE | re.MULTILINE)


def _matrix_targets(job: dict[str, Any]) -> set[str]:
    """The ``target`` values of the job's matrix: the axis list plus any ``include`` entries."""
    matrix = (job.get("strategy") or {}).get("matrix") or {}
    if not isinstance(matrix, dict):
        return set()
    values = matrix.get("target")
    found = {str(value) for value in values} if isinstance(values, list) else set()
    for entry in matrix.get("include") or []:
        if isinstance(entry, dict) and "target" in entry:
            found.add(str(entry["target"]))
    for entry in matrix.get("exclude") or []:
        if isinstance(entry, dict) and "target" in entry:
            found.discard(str(entry["target"]))
    return found


def probe_gaps(document: dict[str, Any], governed: dict[str, set[str]], stages: dict[str, list[str]]) -> list[str]:
    """Why a governed ``{dockerfile: {target, ...}}`` is not built and probed by *document* — empty when it is.

    *stages* maps each Dockerfile to its stage names in order, so a build
    without ``target:`` resolves to the last stage exactly as buildx does.
    """
    gaps = []
    for dockerfile, targets in sorted(governed.items()):
        job_id, step, job = _find_build(document, dockerfile)
        if step is None or job is None:
            gaps.append(f"{dockerfile}: no job builds it")
            continue
        with_ = step.get("with") if isinstance(step.get("with"), dict) else {}
        target = with_.get("target")
        if target is None:
            built = {stages[dockerfile][-1]} if stages.get(dockerfile) else set()
        elif _MATRIX_TARGET.match(str(target)):
            built = _matrix_targets(job)
            for key in ("cache-from", "cache-to"):
                cache = str(with_.get(key) or "")
                if cache and not re.search(r"scope=[^,\s]*\$\{\{\s*matrix\.target\s*\}\}", cache):
                    gaps.append(
                        f"{job_id}: `{key}: {cache}` has no per-leg scope — concurrent legs overwrite one "
                        "cache manifest and each restores whichever leg exported last"
                    )
        else:
            built = {str(target)}
        for missing in sorted(targets - built):
            gaps.append(f"{job_id}: never builds the pinned target {missing!r} of {dockerfile} (#1764)")
        tags = str(with_.get("tags") or "")
        probed = [
            words
            for run in _runs(job)
            for line in _strip_shell_comments(run).splitlines()
            if _PROBE in line
            for words in [shlex.split(line)]
        ]
        if not any(len(words) > 1 and words[1] in tags.split(",") for words in probed):
            gaps.append(f"{job_id}: no step runs {_PROBE} against the tag it built ({tags!r})")
    return gaps


def _governed() -> dict[str, set[str]]:
    governed: dict[str, set[str]] = {}
    for target in _TARGETS:
        governed.setdefault(target.dockerfile, set()).add(target.target)
    return governed


def _stages() -> dict[str, list[str]]:
    return {
        dockerfile: _STAGE.findall((_REPO_ROOT / dockerfile).read_text(encoding="utf-8")) for dockerfile in _governed()
    }


def test_the_governed_set_is_not_empty() -> None:
    """A blind enumeration would pass the check below on nothing (#1545)."""
    assert sum(len(targets) for targets in _governed().values()) >= 6, _governed()


def test_every_pinned_target_is_built_and_probed() -> None:
    document = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    assert probe_gaps(document, _governed(), _stages()) == []


# --------------------------------------------------------------------------
# the check, against falsifying documents
# --------------------------------------------------------------------------

_DOCKERFILE = "docker/x-service/Dockerfile"
_GOVERNED = {_DOCKERFILE: {"a", "b"}}
_STAGES = {_DOCKERFILE: ["dl-a", "dl-b", "runtime", "a", "b"]}


def _document(*, target: str | None, matrix: Any = None, scope: bool = True, probe: bool = True) -> dict[str, Any]:
    with_: dict[str, Any] = {"context": "docker/x-service", "file": _DOCKERFILE, "load": True, "tags": "kp-x:pr"}
    if target is not None:
        with_["target"] = target
    suffix = ",scope=x-${{ matrix.target }}" if scope else ""
    with_["cache-from"] = f"type=gha{suffix}"
    with_["cache-to"] = f"type=gha,mode=max{suffix}"
    steps: list[dict[str, Any]] = [
        {"uses": "docker/build-push-action@0000000000000000000000000000000000000000", "with": with_}
    ]
    if probe:
        steps.append({"run": f"{_PROBE} kp-x:pr x"})
    job: dict[str, Any] = {"runs-on": "ubuntu-latest", "steps": steps}
    if matrix is not None:
        job["strategy"] = {"fail-fast": False, "matrix": matrix}
    return {"jobs": {"build-x": job}}


def test_a_full_matrix_is_not_a_finding() -> None:
    document = _document(target="${{ matrix.target }}", matrix={"target": ["a", "b"]})
    assert probe_gaps(document, _GOVERNED, _STAGES) == []


def test_a_matrix_include_counts() -> None:
    document = _document(target="${{ matrix.target }}", matrix={"target": ["a"], "include": [{"target": "b"}]})
    assert probe_gaps(document, _GOVERNED, _STAGES) == []


def test_a_missing_leg_is_a_finding() -> None:
    document = _document(target="${{ matrix.target }}", matrix={"target": ["a"]})
    assert any("'b'" in gap for gap in probe_gaps(document, _GOVERNED, _STAGES))


def test_an_excluded_leg_is_a_finding() -> None:
    document = _document(target="${{ matrix.target }}", matrix={"target": ["a", "b"], "exclude": [{"target": "a"}]})
    assert any("'a'" in gap for gap in probe_gaps(document, _GOVERNED, _STAGES))


def test_the_pre_1764_shape_is_a_finding() -> None:
    """One literal target — the shipped one — leaves the others unprobed."""
    assert any("'a'" in gap for gap in probe_gaps(_document(target="b", scope=False), _GOVERNED, _STAGES))


def test_no_target_builds_only_the_last_stage() -> None:
    gaps = probe_gaps(_document(target=None, scope=False), _GOVERNED, _STAGES)
    assert [gap for gap in gaps if "never builds" in gap] == [
        f"build-x: never builds the pinned target 'a' of {_DOCKERFILE} (#1764)"
    ]


def test_a_shared_cache_scope_across_legs_is_a_finding() -> None:
    document = _document(target="${{ matrix.target }}", matrix={"target": ["a", "b"]}, scope=False)
    assert any("per-leg scope" in gap for gap in probe_gaps(document, _GOVERNED, _STAGES))


def test_a_job_without_the_probe_is_a_finding() -> None:
    document = _document(target="${{ matrix.target }}", matrix={"target": ["a", "b"]}, probe=False)
    assert any(_PROBE in gap for gap in probe_gaps(document, _GOVERNED, _STAGES))


def test_a_commented_out_probe_is_a_finding() -> None:
    document = _document(target="${{ matrix.target }}", matrix={"target": ["a", "b"]}, probe=False)
    document["jobs"]["build-x"]["steps"].append({"run": f"# {_PROBE} kp-x:pr x"})
    assert any(_PROBE in gap for gap in probe_gaps(document, _GOVERNED, _STAGES))


def test_an_unbuilt_dockerfile_is_a_finding() -> None:
    assert probe_gaps({"jobs": {}}, _GOVERNED, _STAGES) == [f"{_DOCKERFILE}: no job builds it"]


@pytest.mark.parametrize("tag", ["kp-other:pr", "kp-x:pr-typo"])
def test_probing_another_tag_is_a_finding(tag: str) -> None:
    document = _document(target="${{ matrix.target }}", matrix={"target": ["a", "b"]}, probe=False)
    document["jobs"]["build-x"]["steps"].append({"run": f"{_PROBE} {tag} x"})
    assert any(_PROBE in gap for gap in probe_gaps(document, _GOVERNED, _STAGES))
