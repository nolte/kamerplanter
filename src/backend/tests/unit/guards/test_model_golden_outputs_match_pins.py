"""#1763 — every pinned model has golden outputs, and they belong to the pin.

**Why this exists.** The MiniLM embedding image on ``develop`` before #1758
returned vectors of the right width and unit norm whose content was garbage —
transformers 5 tokenized almost every word to ``<unk>`` — and every CI check
passed, because ``scripts/ci/probe_model_service_contract.py`` asserted shape
only. Since #1763 the probe also compares the running image against golden
outputs: fixed inputs, embedded (or scored) once from the pinned model files
by ``scripts/ci/compute_model_golden_outputs.py`` and stored in
``docker/<service>/golden/<target>.json``.

Golden outputs are only as good as their binding to the model they describe. A
``revision=`` bump that leaves the old golden file in place either fails the
probe on every build (a legitimate model change the reviewer then "fixes" by
loosening the tolerance) or — worse — passes against values of a model that no
longer ships. So this guard binds each golden file to its pin, over the class:

- **Every final stage that ships a Hugging Face download** (found with the same
  scanner as ``test_hf_model_fetches_pin_a_revision.py``, over every Dockerfile
  in the checkout) has exactly one golden file, named after the stage.
- The golden file names that stage's download stage, repository, 40-hex
  ``revision`` and the sha256 of every file the stage verifies — so a re-pin,
  or a re-hash of one file, without regenerating the golden outputs fails here.
- The ``model`` it names is the one the stage declares in ``EMBEDDING_MODEL`` /
  ``RERANKER_MODEL``: that is how the probe picks the file for a running image.
- No golden file is left over for a stage that no longer exists.
- Its inputs still cover the three kinds the issue asks for — among them a text
  past the 512-token window, re-checked through the token count recorded for
  that model's tokenizer — and its one-time cross-check against the PyTorch
  weights (``reference_check``) is present and within the probe's tolerance,
  naming the pinned commit wherever the weights come from the pinned repository.

The second half of the file holds the probe's comparison against falsifying
inputs: without them, a comparison that always returned 0 would pass here and
in CI alike.
"""

from __future__ import annotations

import json
import math
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from tests.support.repo_scripts import load_repo_script
from tests.unit.guards.test_hf_model_fetches_pin_a_revision import (
    _REPO_ROOT,
    _dockerfiles,
    _strip_dockerfile_comments,
    fetch_sites,
)

probe = load_repo_script("ci/probe_model_service_contract")

#: The six targets #1763 was written for. A floor, not the definition: the
#: enumeration below derives the governed set from the Dockerfiles; this only
#: keeps a scanner that went blind from passing on an empty set (#1545).
_KNOWN_TARGETS = {
    "docker/embedding-service/Dockerfile:e5-small",
    "docker/embedding-service/Dockerfile:e5-base",
    "docker/embedding-service/Dockerfile:e5-large",
    "docker/embedding-service/Dockerfile:minilm",
    "docker/reranker-service/Dockerfile:bge-reranker-v2-m3",
    "docker/reranker-service/Dockerfile:ms-marco-minilm",
}

_STAGE = re.compile(r"^FROM\s+\S+\s+AS\s+(?P<stage>\S+)\s*$", re.IGNORECASE | re.MULTILINE)
_COPY_FROM = re.compile(r"^COPY\s+(?:--\S+\s+)*--from=(?P<stage>\S+)", re.IGNORECASE | re.MULTILINE)
_HASH_LINE = re.compile(r"(?P<digest>[0-9a-f]{64})\s+\*?(?P<path>/[^\s'\"]+)")


@dataclass(frozen=True)
class GovernedTarget:
    """One final image stage that ships a pinned Hugging Face download."""

    dockerfile: str
    target: str
    download_stage: str
    repo: str
    revision: str
    #: ``{file name: sha256}`` from the download stage's ``sha256sum -c`` lines.
    files_sha256: dict[str, str]
    #: ``{env var: value}`` the target stage declares.
    env: dict[str, str]

    @property
    def label(self) -> str:
        return f"{self.dockerfile}:{self.target}"

    @property
    def kind(self) -> str:
        """``embedding`` for ``docker/embedding-service/Dockerfile`` — the probe's service argument."""
        return Path(self.dockerfile).parent.name.removesuffix("-service")


def _stages(text: str) -> dict[str, str]:
    matches = list(_STAGE.finditer(text))
    return {
        match.group("stage"): text[match.end() : matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        for i, match in enumerate(matches)
    }


def governed_targets(text: str, *, path: str) -> list[GovernedTarget]:
    """Every final stage in the Dockerfile *text* that ``COPY --from``s a stage with a pinned HF fetch."""
    stages = _stages(_strip_dockerfile_comments(text))
    pinned = {site.stage: site for site in fetch_sites(text, path=path) if site.pinned}
    found = []
    for name, body in stages.items():
        for source in {match.group("stage") for match in _COPY_FROM.finditer(body)} & pinned.keys():
            site = pinned[source]
            hashes = {
                Path(match.group("path")).name: match.group("digest") for match in _HASH_LINE.finditer(stages[source])
            }
            env = dict(re.findall(r"^ENV\s+(\w+)=(\S+)\s*$", body, re.MULTILINE))
            found.append(GovernedTarget(path, name, source, site.repo or "", site.revision or "", hashes, env))
    return found


def golden_problems(target: GovernedTarget, golden_dir: Path) -> list[str]:
    """Why ``<golden_dir>/<target>.json`` does not describe *target*'s pin — empty when it does."""
    path = golden_dir / f"{target.target}.json"
    if not path.is_file():
        return [
            f"{target.label}: no golden outputs at {path.name} — run "
            f"scripts/ci/compute_model_golden_outputs.py {target.kind} {target.target} <image> (#1763)"
        ]
    golden = json.loads(path.read_text(encoding="utf-8"))
    problems = []
    if target.kind not in probe.MODEL_ENV:
        return [f"{target.label}: the contract probe compares golden outputs for {sorted(probe.MODEL_ENV)} only"]
    expected = {
        "schema": probe.GOLDEN_SCHEMA,
        "service": target.kind,
        "target": target.target,
        "download_stage": target.download_stage,
        "repo_id": target.repo,
        "revision": target.revision,
        "files_sha256": target.files_sha256,
        "model": target.env.get(probe.MODEL_ENV[target.kind]),
    }
    for field, value in expected.items():
        if golden.get(field) != value:
            problems.append(
                f"{target.label}: golden {field} is {golden.get(field)!r}, the Dockerfile pins {value!r} — "
                "a re-pin must regenerate the golden outputs (scripts/ci/compute_model_golden_outputs.py)"
            )
    problems.extend(f"{target.label}: {problem}" for problem in content_problems(golden))
    return problems


def content_problems(golden: dict[str, Any]) -> list[str]:
    """What the golden cases lack: the input kinds, the reduction shape, the PyTorch cross-check."""
    problems = []
    cases = golden.get("cases") or []
    if len(cases) < 3:
        problems.append(f"{len(cases)} golden cases; at least 3 (normal, multilingual, >512 tokens)")
    if not any(case.get("untruncated_tokens", 0) > 512 for case in cases):
        problems.append("no golden case exceeds the 512-token window for this model's tokenizer")
    if golden.get("service") == "embedding":
        tolerance = probe.GOLDEN_TOLERANCE
        for case in cases:
            if len(case.get("sample", [])) != probe.GOLDEN_SAMPLE_SIZE:
                problems.append(f"case {case.get('name')!r}: sample is not {probe.GOLDEN_SAMPLE_SIZE} values")
            if len(case.get("projection", [])) != probe.GOLDEN_PROJECTIONS:
                problems.append(f"case {case.get('name')!r}: projection is not {probe.GOLDEN_PROJECTIONS} values")
    else:
        tolerance = probe.GOLDEN_LOGIT_TOLERANCE
        for case in cases:
            logits = case.get("logits", [])
            if len(logits) != len(case.get("documents", [])) or not logits:
                problems.append(f"case {case.get('name')!r}: not one logit per document")
            if any(abs(logit) >= probe.GOLDEN_MAX_ABS_LOGIT for logit in logits):
                problems.append(f"case {case.get('name')!r}: a logit saturates the served sigmoid")
    check = golden.get("reference_check")
    if not isinstance(check, dict):
        problems.append("no reference_check — run compute_model_golden_outputs.py reference-check")
    else:
        if not check.get("max_abs_delta", math.inf) <= tolerance:
            problems.append(f"reference_check max |Δ| {check.get('max_abs_delta')} exceeds the tolerance {tolerance}")
        source, _, revision = str(check.get("against", "")).partition("@")
        if source == golden.get("repo_id") and revision != golden.get("revision"):
            problems.append(f"reference_check ran against {revision!r}, not the pinned {golden.get('revision')!r}")
    return problems


def _tree_targets() -> list[GovernedTarget]:
    targets = []
    for dockerfile in _dockerfiles():
        relative = str(dockerfile.relative_to(_REPO_ROOT))
        targets.extend(governed_targets(dockerfile.read_text(encoding="utf-8"), path=relative))
    return targets


_TARGETS = _tree_targets()


class TestGoldenOutputsAreBoundToThePins:
    """Every shipped pinned model has golden outputs that name exactly its pin."""

    def test_the_enumeration_reaches_the_tree(self) -> None:
        labels = {target.label for target in _TARGETS}
        assert labels >= _KNOWN_TARGETS, (
            f"the enumeration lost {sorted(_KNOWN_TARGETS - labels)} — a blind scanner would pass every case below"
        )

    @pytest.mark.parametrize("target", _TARGETS, ids=lambda target: target.label)
    def test_golden_outputs_match_the_pin(self, target: GovernedTarget) -> None:
        golden_dir = _REPO_ROOT / Path(target.dockerfile).parent / "golden"
        assert golden_problems(target, golden_dir) == []

    def test_no_golden_file_outlives_its_stage(self) -> None:
        expected = {_REPO_ROOT / Path(t.dockerfile).parent / "golden" / f"{t.target}.json" for t in _TARGETS}
        present = {path for dockerfile in _dockerfiles() for path in (dockerfile.parent / "golden").glob("*.json")}
        assert present - expected == set(), "golden files for stages that no longer ship a pinned model"

    def test_the_probe_reads_the_golden_directories_this_guard_checks(self) -> None:
        for target in _TARGETS:
            assert probe.GOLDEN_DIRS[target.kind] == _REPO_ROOT / Path(target.dockerfile).parent / "golden"


# --------------------------------------------------------------------------
# the binding, against falsifying edits (each must turn the guard red)
# --------------------------------------------------------------------------


def _embedding_fixture(tmp_path: Path) -> tuple[str, Path]:
    dockerfile = _REPO_ROOT / "docker" / "embedding-service" / "Dockerfile"
    golden_dir = tmp_path / "golden"
    shutil.copytree(dockerfile.parent / "golden", golden_dir)
    return dockerfile.read_text(encoding="utf-8"), golden_dir


def _minilm(text: str) -> GovernedTarget:
    path = "docker/embedding-service/Dockerfile"
    return next(target for target in governed_targets(text, path=path) if target.target == "minilm")


def test_the_unmodified_tree_is_green(tmp_path: Path) -> None:
    text, golden_dir = _embedding_fixture(tmp_path)
    assert golden_problems(_minilm(text), golden_dir) == []


def test_a_revision_bump_without_new_golden_outputs_is_red(tmp_path: Path) -> None:
    text, golden_dir = _embedding_fixture(tmp_path)
    bumped = text.replace("2c4055b12046f11709e9df2c122e59ffbdc2f900", "0" * 40)
    assert bumped != text
    assert any("golden revision" in problem for problem in golden_problems(_minilm(bumped), golden_dir))


def test_a_rehashed_file_without_new_golden_outputs_is_red(tmp_path: Path) -> None:
    text, golden_dir = _embedding_fixture(tmp_path)
    digest = _minilm(text).files_sha256["model.onnx"]
    rehashed = text.replace(digest, "f" * 64)
    assert any("golden files_sha256" in problem for problem in golden_problems(_minilm(rehashed), golden_dir))


def test_a_missing_golden_file_is_red(tmp_path: Path) -> None:
    text, golden_dir = _embedding_fixture(tmp_path)
    (golden_dir / "minilm.json").unlink()
    assert any("no golden outputs" in problem for problem in golden_problems(_minilm(text), golden_dir))


def test_a_golden_file_without_a_long_case_is_red(tmp_path: Path) -> None:
    text, golden_dir = _embedding_fixture(tmp_path)
    path = golden_dir / "minilm.json"
    golden = json.loads(path.read_text(encoding="utf-8"))
    golden["cases"] = [case for case in golden["cases"] if case["untruncated_tokens"] <= 512]
    path.write_text(json.dumps(golden), encoding="utf-8")
    assert any("512-token window" in problem for problem in golden_problems(_minilm(text), golden_dir))


def test_a_reference_check_against_another_revision_is_red(tmp_path: Path) -> None:
    golden = json.loads((_REPO_ROOT / "docker/embedding-service/golden/e5-small.json").read_text(encoding="utf-8"))
    golden["reference_check"]["against"] = f"{golden['repo_id']}@{'1' * 40}"
    assert any("reference_check ran against" in problem for problem in content_problems(golden))


# --------------------------------------------------------------------------
# the probe's comparison, against falsifying inputs
# --------------------------------------------------------------------------


def test_a_deviation_within_tolerance_passes() -> None:
    expected = [0.1, -0.2, 0.3]
    actual = [value + probe.GOLDEN_TOLERANCE / 2 for value in expected]
    assert probe.compare_golden("x", expected, actual, probe.GOLDEN_TOLERANCE) == pytest.approx(
        probe.GOLDEN_TOLERANCE / 2
    )


@pytest.mark.parametrize(
    "actual",
    [
        [0.1, -0.2, 0.3 + 2e-3],  # one component past the tolerance
        [0.1, -0.2, math.nan],  # a NaN never compares <= anything
        [0.1, -0.2],  # a short list is not a truncated zip
    ],
)
def test_a_deviation_past_tolerance_is_red(actual: list[float]) -> None:
    with pytest.raises(probe.ProbeError):
        probe.compare_golden("x", [0.1, -0.2, 0.3], actual, probe.GOLDEN_TOLERANCE)


def test_the_reduction_covers_every_component() -> None:
    """A change in a component the sample does not pick still moves a projection."""
    dimension = 384
    vector = [math.sin(index) / math.sqrt(dimension) for index in range(dimension)]
    sampled = set(probe.golden_sample_indices(dimension))
    unsampled = next(index for index in range(dimension) if index not in sampled)
    changed = list(vector)
    changed[unsampled] += 0.05
    before, after = probe.reduce_embedding(vector), probe.reduce_embedding(changed)
    assert before["sample"] == after["sample"]
    assert probe.max_deviation(before["projection"], after["projection"]) > probe.GOLDEN_TOLERANCE


def test_the_projection_signs_are_fixed() -> None:
    """The stored projections are only comparable while the directions never change."""
    signs = probe.golden_projection_signs(0, 8)
    assert signs == probe.golden_projection_signs(0, 8)
    assert set(signs) <= {-1, 1}
    assert signs != probe.golden_projection_signs(1, 8)


@pytest.mark.parametrize("logit", [-11.03, -1.4, 0.0, 3.13, 5.15])
def test_score_logit_inverts_the_served_sigmoid(logit: float) -> None:
    score = 1.0 / (1.0 + math.exp(-logit))
    assert probe.score_logit(score) == pytest.approx(logit, abs=1e-9)


@pytest.mark.parametrize("score", [0.0, 1.0])
def test_a_saturated_score_is_red(score: float) -> None:
    with pytest.raises(probe.ProbeError):
        probe.score_logit(score)


def test_load_golden_needs_exactly_one_file(tmp_path: Path) -> None:
    document = {"schema": probe.GOLDEN_SCHEMA, "model": "m", "reduction": None}
    with pytest.raises(probe.ProbeError, match="exactly one"):
        probe.load_golden("reranker", "m", tmp_path)
    (tmp_path / "a.json").write_text(json.dumps(document), encoding="utf-8")
    assert probe.load_golden("reranker", "m", tmp_path)[1] == document
    (tmp_path / "b.json").write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(probe.ProbeError, match="exactly one"):
        probe.load_golden("reranker", "m", tmp_path)
