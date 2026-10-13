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
  A download stage may hold more than one fetch (#1774: MiniLM's window comes
  from the model authors' repository). ``repo_id``/``revision`` are then the
  MODEL's fetch — the one whose ``allow_patterns`` name ``onnx/model.onnx`` —
  and every other pinned fetch of the stage must appear, with its revision,
  in ``extra_sources`` (omitted when there is none).
- The ``model`` it names is the one the stage declares in ``EMBEDDING_MODEL`` /
  ``RERANKER_MODEL``: that is how the probe picks the file for a running image.
- No golden file is left over for a stage that no longer exists.
- Its inputs still cover the three kinds the issue asks for — among them a text
  past the model's token window, re-checked through the token count recorded
  for that model's tokenizer — and its one-time cross-check against the PyTorch
  weights (``reference_check``) is present and within the probe's tolerance,
  naming the pinned commit wherever the weights come from the pinned repository
  or one of its extra sources.
- **The window is bound too (#1774).** Until #1774 the service truncated every
  embedding model at a hard-coded 512 and the golden computation and its
  cross-check forced the same 512 on both sides, so nothing could notice that
  MiniLM's authors publish 128. An embedding golden file now records the
  ``max_seq_length`` the image's ``sentence_bert_config.json`` declares; that
  file must be among the verified ``files_sha256`` (the window's source is a
  pinned, hashed file), ``reference_check.max_seq_length`` —
  sentence-transformers' own value for the source repository — must equal it,
  and the long case must exceed it. The rerankers keep the fixed 512 of the
  reranker service.

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
    FetchSite,
    _call_arguments,
    _call_pattern,
    _dockerfiles,
    _fold_continuations,
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
    #: ``(repo, revision)`` of every other pinned fetch of the download stage, sorted (#1774).
    extra_sources: tuple[tuple[str, str], ...] = ()
    #: Why the model's fetch could not be told apart from the others; None when it could.
    binding_problem: str | None = None

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


#: ``allow_patterns=[... 'onnx/model.onnx' ...]`` — the fetch that brings the graph.
_FETCHES_GRAPH = re.compile(r"\ballow_patterns\s*=\s*\[[^\]]*\\?['\"]onnx/model\.onnx\\?['\"]")


def _call_arguments_by_line(text: str) -> dict[int, list[str]]:
    """The argument text of every fetch call in the Dockerfile *text*, by the line the call starts on.

    The same comment stripping, continuation folding and call reader as
    ``fetch_sites``, so the line numbers are the ones ``FetchSite.line`` carries.
    """
    code = _fold_continuations(_strip_dockerfile_comments(text))
    found: dict[int, list[str]] = {}
    for match in _call_pattern(code).finditer(code):
        found.setdefault(code.count("\n", 0, match.start()) + 1, []).append(_call_arguments(code, match.end() - 1))
    return found


def _model_fetch(sites: list[FetchSite], arguments: dict[int, list[str]]) -> tuple[FetchSite | None, str | None]:
    """``(the model's fetch, None)`` among a download stage's pinned *sites*, or ``(None, why not)``.

    One pinned fetch is the model's, whatever its spelling. With several, the
    model's is the one whose ``allow_patterns`` name ``onnx/model.onnx`` — and
    there must be exactly one such fetch, or the golden file's ``repo_id``
    could be bound to the wrong repository.
    """
    if len(sites) == 1:
        return sites[0], None
    graph = [
        site
        for site in sites
        if any(_FETCHES_GRAPH.search(args) and site.repo and site.repo in args for args in arguments.get(site.line, []))
    ]
    if len(graph) != 1:
        repos = sorted(site.repo or "?" for site in sites)
        return None, f"{len(graph)} of the stage's pinned fetches {repos} name 'onnx/model.onnx'; exactly one must"
    return graph[0], None


def governed_targets(text: str, *, path: str) -> list[GovernedTarget]:
    """Every final stage in the Dockerfile *text* that ``COPY --from``s a stage with a pinned HF fetch."""
    stages = _stages(_strip_dockerfile_comments(text))
    pinned: dict[str, list[FetchSite]] = {}
    for site in fetch_sites(text, path=path):
        if site.pinned:
            pinned.setdefault(site.stage, []).append(site)
    arguments = _call_arguments_by_line(text)
    found = []
    for name, body in stages.items():
        for source in {match.group("stage") for match in _COPY_FROM.finditer(body)} & pinned.keys():
            model, problem = _model_fetch(pinned[source], arguments)
            extras = tuple(
                sorted((site.repo or "", site.revision or "") for site in pinned[source] if site is not model)
            )
            hashes = {
                Path(match.group("path")).name: match.group("digest") for match in _HASH_LINE.finditer(stages[source])
            }
            env = dict(re.findall(r"^ENV\s+(\w+)=(\S+)\s*$", body, re.MULTILINE))
            found.append(
                GovernedTarget(
                    path,
                    name,
                    source,
                    model.repo or "" if model else "",
                    model.revision or "" if model else "",
                    hashes,
                    env,
                    extras if model else (),
                    problem,
                )
            )
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
    if target.binding_problem is not None:
        problems.append(f"{target.label}: {target.binding_problem}")
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
    extra_sources = [{"repo_id": repo, "revision": revision} for repo, revision in target.extra_sources]
    if golden.get("extra_sources", []) != extra_sources:
        problems.append(
            f"{target.label}: golden extra_sources is {golden.get('extra_sources', [])!r}, the Dockerfile pins "
            f"{extra_sources!r} — a re-pin must regenerate the golden outputs "
            "(scripts/ci/compute_model_golden_outputs.py)"
        )
    problems.extend(f"{target.label}: {problem}" for problem in content_problems(golden))
    return problems


#: The reranker service's fixed truncation window (docker/reranker-service/main.py ``MAX_LENGTH``).
_RERANKER_WINDOW = 512

#: The file an embedding model's window is read from (docker/embedding-service/tokenization.py, #1774).
_WINDOW_FILE = "sentence_bert_config.json"


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def window_problems(golden: dict[str, Any]) -> tuple[int | None, list[str]]:
    """``(the golden file's truncation window, why it is not bound)`` — #1774.

    Rerankers: the fixed 512. Embedding models: the recorded ``max_seq_length``,
    which must be a positive int, sourced from a verified
    ``sentence_bert_config.json`` and equal to the value sentence-transformers
    itself loaded for the source repository in ``reference_check``.
    """
    if golden.get("service") != "embedding":
        return _RERANKER_WINDOW, []
    problems = []
    window = golden.get("max_seq_length")
    if not _positive_int(window):
        problems.append(
            f"max_seq_length is {window!r}, not a positive int — the embedding window must be recorded (#1774)"
        )
        window = None
    if _WINDOW_FILE not in (golden.get("files_sha256") or {}):
        problems.append(f"files_sha256 has no {_WINDOW_FILE}: the window's source is not a pinned, verified file")
    check = golden.get("reference_check")
    if isinstance(check, dict) and check.get("max_seq_length") != golden.get("max_seq_length"):
        problems.append(
            f"reference_check max_seq_length {check.get('max_seq_length')!r} differs from the golden "
            f"max_seq_length {golden.get('max_seq_length')!r} — the image does not truncate where the model's "
            "authors do"
        )
    return window, problems


def content_problems(golden: dict[str, Any]) -> list[str]:
    """What the golden cases lack: the input kinds, the reduction shape, the PyTorch cross-check."""
    problems = []
    cases = golden.get("cases") or []
    if len(cases) < 3:
        problems.append(f"{len(cases)} golden cases; at least 3 (normal, multilingual, past the token window)")
    window, unbound = window_problems(golden)
    problems.extend(unbound)
    if window is not None and not any(case.get("untruncated_tokens", 0) > window for case in cases):
        problems.append(f"no golden case exceeds the {window}-token window for this model's tokenizer")
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
            low, high = probe.GOLDEN_LOGIT_RANGE
            if not all(low <= logit <= high for logit in logits):
                problems.append(
                    f"case {case.get('name')!r}: a logit leaves {probe.GOLDEN_LOGIT_RANGE}, where the served "
                    "float32 score no longer carries it to within the tolerance"
                )
    check = golden.get("reference_check")
    if not isinstance(check, dict):
        problems.append("no reference_check — run compute_model_golden_outputs.py reference-check")
    else:
        if not check.get("max_abs_delta", math.inf) <= tolerance:
            problems.append(f"reference_check max |Δ| {check.get('max_abs_delta')} exceeds the tolerance {tolerance}")
        source, _, revision = str(check.get("against", "")).partition("@")
        if source == golden.get("repo_id") and revision != golden.get("revision"):
            problems.append(f"reference_check ran against {revision!r}, not the pinned {golden.get('revision')!r}")
        for extra in golden.get("extra_sources") or []:
            if source == extra.get("repo_id") and revision != extra.get("revision"):
                problems.append(
                    f"reference_check ran against {revision!r}, not the pinned extra source {extra.get('revision')!r}"
                )
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


def _embedding_dockerfile() -> str:
    return (_REPO_ROOT / "docker" / "embedding-service" / "Dockerfile").read_text(encoding="utf-8")


def _target(text: str, name: str) -> GovernedTarget:
    path = "docker/embedding-service/Dockerfile"
    return next(target for target in governed_targets(text, path=path) if target.target == name)


def _minilm(text: str) -> GovernedTarget:
    return _target(text, "minilm")


def _synthetic_golden(target: GovernedTarget, window: int, long_tokens: int | None = None) -> dict[str, Any]:
    """A golden file that describes *target* exactly, with *window* as its ``max_seq_length``.

    Built from the Dockerfile's binding rather than read from the checked-in
    golden files, so the falsifying tests below each start from a green input
    and flip ONE property — independent of whether the files in the tree have
    been regenerated yet. The cross-check names the extra source when there is
    one (MiniLM's PyTorch weights live in the authors' repository), else the
    pinned repository.
    """
    source = target.extra_sources[0] if target.extra_sources else (target.repo, target.revision)
    reduced = {"sample": [0.0] * probe.GOLDEN_SAMPLE_SIZE, "projection": [0.0] * probe.GOLDEN_PROJECTIONS}
    golden: dict[str, Any] = {
        "schema": probe.GOLDEN_SCHEMA,
        "service": target.kind,
        "target": target.target,
        "model": target.env.get(probe.MODEL_ENV[target.kind]),
        "download_stage": target.download_stage,
        "repo_id": target.repo,
        "revision": target.revision,
        "files_sha256": dict(target.files_sha256),
        "max_seq_length": window,
        "cases": [
            {"name": "normal-en", "untruncated_tokens": 18, **reduced},
            {"name": "german", "untruncated_tokens": 21, **reduced},
            {"name": "long", "untruncated_tokens": window + 1 if long_tokens is None else long_tokens, **reduced},
        ],
        "reference_check": {"against": f"{source[0]}@{source[1]}", "max_abs_delta": 0.0, "max_seq_length": window},
    }
    if target.extra_sources:
        golden["extra_sources"] = [{"repo_id": repo, "revision": revision} for repo, revision in target.extra_sources]
    return golden


def _write(golden_dir: Path, golden: dict[str, Any]) -> Path:
    golden_dir.mkdir(parents=True, exist_ok=True)
    (golden_dir / f"{golden['target']}.json").write_text(json.dumps(golden), encoding="utf-8")
    return golden_dir


def test_the_unmodified_tree_is_green(tmp_path: Path) -> None:
    text, golden_dir = _embedding_fixture(tmp_path)
    assert golden_problems(_minilm(text), golden_dir) == []


@pytest.mark.parametrize(("name", "window"), [("e5-small", 512), ("e5-large", 512), ("minilm", 128)])
def test_a_golden_file_that_matches_the_pin_is_green(tmp_path: Path, name: str, window: int) -> None:
    """The baseline every falsifying test below flips one property of: without it they prove nothing."""
    target = _target(_embedding_dockerfile(), name)
    assert golden_problems(target, _write(tmp_path, _synthetic_golden(target, window))) == []


def test_a_revision_bump_without_new_golden_outputs_is_red(tmp_path: Path) -> None:
    text = _embedding_dockerfile()
    golden_dir = _write(tmp_path, _synthetic_golden(_minilm(text), 128))
    bumped = text.replace("2c4055b12046f11709e9df2c122e59ffbdc2f900", "0" * 40)
    assert bumped != text
    assert any("golden revision" in problem for problem in golden_problems(_minilm(bumped), golden_dir))


def test_a_rehashed_file_without_new_golden_outputs_is_red(tmp_path: Path) -> None:
    text = _embedding_dockerfile()
    golden_dir = _write(tmp_path, _synthetic_golden(_minilm(text), 128))
    digest = _minilm(text).files_sha256["model.onnx"]
    rehashed = text.replace(digest, "f" * 64)
    assert any("golden files_sha256" in problem for problem in golden_problems(_minilm(rehashed), golden_dir))


def test_a_missing_golden_file_is_red(tmp_path: Path) -> None:
    text, golden_dir = _embedding_fixture(tmp_path)
    (golden_dir / "minilm.json").unlink()
    assert any("no golden outputs" in problem for problem in golden_problems(_minilm(text), golden_dir))


def test_a_golden_file_without_a_long_case_is_red() -> None:
    golden = _synthetic_golden(_minilm(_embedding_dockerfile()), 128, long_tokens=128)
    assert any("128-token window" in problem for problem in content_problems(golden))


def test_the_long_case_is_measured_against_the_models_window_not_512() -> None:
    """#1774: 300 tokens exceed MiniLM's 128 but not e5's 512 — the check must know which model it holds."""
    text = _embedding_dockerfile()
    assert content_problems(_synthetic_golden(_minilm(text), 128, long_tokens=300)) == []
    assert any(
        "512-token window" in problem
        for problem in content_problems(_synthetic_golden(_target(text, "e5-small"), 512, long_tokens=300))
    )


def test_a_reranker_keeps_the_512_window() -> None:
    golden = json.loads(
        (_REPO_ROOT / "docker/reranker-service/golden/ms-marco-minilm.json").read_text(encoding="utf-8")
    )
    assert "max_seq_length" not in golden
    assert not any("max_seq_length" in problem for problem in content_problems(golden))
    golden["cases"] = [dict(case, untruncated_tokens=512) for case in golden["cases"]]
    assert any("512-token window" in problem for problem in content_problems(golden))


def test_a_reference_check_against_another_revision_is_red() -> None:
    golden = _synthetic_golden(_target(_embedding_dockerfile(), "e5-small"), 512)
    golden["reference_check"]["against"] = f"{golden['repo_id']}@{'1' * 40}"
    assert any("reference_check ran against" in problem for problem in content_problems(golden))


def test_a_reference_check_against_another_extra_source_revision_is_red() -> None:
    golden = _synthetic_golden(_minilm(_embedding_dockerfile()), 128)
    source = golden["extra_sources"][0]["repo_id"]
    golden["reference_check"]["against"] = f"{source}@{'1' * 40}"
    assert any("pinned extra source" in problem for problem in content_problems(golden))


# --------------------------------------------------------------------------
# #1774: the truncation window and the extra source, against falsifying edits
# --------------------------------------------------------------------------


def test_the_model_fetch_is_the_one_that_brings_the_graph() -> None:
    """MiniLM's stage fetches twice; the golden ``repo_id`` is the graph's repository, not the window's."""
    target = _minilm(_embedding_dockerfile())
    assert target.binding_problem is None
    assert target.repo == "Xenova/paraphrase-multilingual-MiniLM-L12-v2"
    assert target.extra_sources == (
        ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"),
    )
    assert "sentence_bert_config.json" in target.files_sha256


def test_a_second_fetch_of_the_graph_is_red(tmp_path: Path) -> None:
    """Two fetches naming ``onnx/model.onnx``: which repository the golden file binds is undecidable."""
    text = _embedding_dockerfile()
    golden_dir = _write(tmp_path, _synthetic_golden(_minilm(text), 128))
    doubled = text.replace("allow_patterns=['sentence_bert_config.json']", "allow_patterns=['onnx/model.onnx']")
    assert doubled != text
    assert any("exactly one must" in problem for problem in golden_problems(_minilm(doubled), golden_dir))


def test_an_extra_source_revision_the_golden_does_not_name_is_red(tmp_path: Path) -> None:
    text = _embedding_dockerfile()
    golden_dir = _write(tmp_path, _synthetic_golden(_minilm(text), 128))
    bumped = text.replace("e8f8c211226b894fcb81acc59f3b34ba3efd5f42", "0" * 40)
    assert bumped != text
    assert any("golden extra_sources" in problem for problem in golden_problems(_minilm(bumped), golden_dir))


def test_a_golden_file_without_the_extra_source_is_red(tmp_path: Path) -> None:
    target = _minilm(_embedding_dockerfile())
    golden = _synthetic_golden(target, 128)
    del golden["extra_sources"]
    assert any("golden extra_sources" in problem for problem in golden_problems(target, _write(tmp_path, golden)))


def test_an_extra_source_the_dockerfile_does_not_fetch_is_red(tmp_path: Path) -> None:
    target = _target(_embedding_dockerfile(), "e5-small")
    golden = _synthetic_golden(target, 512)
    golden["extra_sources"] = [{"repo_id": "someone/else", "revision": "1" * 40}]
    assert any("golden extra_sources" in problem for problem in golden_problems(target, _write(tmp_path, golden)))


def test_a_window_that_differs_from_the_reference_check_is_red() -> None:
    """The pre-#1774 state for MiniLM: the image truncated at 512, its authors publish 128."""
    golden = _synthetic_golden(_minilm(_embedding_dockerfile()), 512)
    golden["reference_check"]["max_seq_length"] = 128
    assert any("reference_check max_seq_length 128" in problem for problem in content_problems(golden))


def test_a_reference_check_without_a_window_is_red() -> None:
    golden = _synthetic_golden(_minilm(_embedding_dockerfile()), 128)
    del golden["reference_check"]["max_seq_length"]
    assert any("reference_check max_seq_length None" in problem for problem in content_problems(golden))


@pytest.mark.parametrize("window", [None, 0, -1, True, "128", 128.0])
def test_an_embedding_golden_without_a_usable_window_is_red(window: Any) -> None:
    golden = _synthetic_golden(_minilm(_embedding_dockerfile()), 128)
    if window is None:
        del golden["max_seq_length"]
    else:
        golden["max_seq_length"] = window
    assert any("not a positive int" in problem for problem in content_problems(golden))


def test_a_window_from_an_unverified_file_is_red() -> None:
    golden = _synthetic_golden(_target(_embedding_dockerfile(), "e5-base"), 512)
    del golden["files_sha256"]["sentence_bert_config.json"]
    assert any("no sentence_bert_config.json" in problem for problem in content_problems(golden))


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


def test_the_logit_range_is_recoverable_from_a_float32_score() -> None:
    """At either end of the band, a float32-rounded score still inverts to within a tenth of the tolerance."""
    import struct

    for logit in probe.GOLDEN_LOGIT_RANGE:
        exact = 1.0 / (1.0 + math.exp(-logit))
        served = struct.unpack("f", struct.pack("f", exact))[0]
        assert abs(probe.score_logit(served) - logit) < probe.GOLDEN_LOGIT_TOLERANCE / 10


def test_a_logit_past_the_band_is_red() -> None:
    golden = json.loads(
        (_REPO_ROOT / "docker/reranker-service/golden/ms-marco-minilm.json").read_text(encoding="utf-8")
    )
    golden["cases"][0]["logits"][1] = 13.0
    assert any("leaves" in problem for problem in content_problems(golden))


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
