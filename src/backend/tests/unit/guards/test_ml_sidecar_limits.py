"""#1725 — the two ONNX sidecars bound their input and size their threads from the cgroup.

**The defects this is written against, measured 2026-09-24 on develop
288432867**, in both ``docker/reranker-service`` and
``docker/embedding-service`` (the embedding service is a template copy of the
reranker and carried every one of them):

* ``/rerank`` bounded only ``top_k``, ``/embed`` nothing. Under the chart's
  limits (``-m 4g --cpus 2``) with inputs of more than 512 tokens the reranker
  was OOMKilled at 100 documents and the e5-large embedding service at 64
  texts — all inputs of a request ran as ONE padded batch.
* ``intra_op_num_threads = os.cpu_count()`` — the HOST count: 8 under
  ``--cpus 2`` (``cpu.max`` ``200000 100000``).
* Every concurrent request ran its own ``session.run``.

**What is asserted, and against which file.** The request models, the bounds
and ``cpu_budget`` live in ``docker/<svc>/limits.py``, which imports only the
standard library and pydantic. This file loads THAT file by path — the one
``main.py`` imports — so the bound that is tested is the bound that runs; a
further AST check requires ``main.py`` to import its request model from
``limits`` and to define none of its own. ``main.py`` itself cannot be imported
here (onnxruntime, tokenizers and transformers are not backend dependencies),
so its wiring — ``cpu_budget()`` as the intra-op thread count, one inference
lock, one graph run per input — is read from its AST, never from its text, so a
comment naming ``cpu_budget`` satisfies nothing.

**Why parametrized over both services.** The group's structural finding: every
hardening of these two images so far was applied to one of them by whoever
touched it. A bound or a thread rule added to one and not the other is red
here.

**The bounds must never refuse the real caller.** src/knowledge-service is the
only client of both. Its limits are re-read from its source (the ask schema's
``max_length``, the ``reranker_initial_k`` default, the embed slice size, the
``prefix=`` literals) and the knowledge corpus is re-measured, so a caller that
grows past a bound goes red here instead of degrading silently in production
(the reranker client falls back to no reranking on any HTTP error).

**Serving under load (the security review of #1725).** A bound on the parsed
request does not bound what happens BEFORE parsing or WHILE serving, so the
same ``limits.py`` also carries — and this file drives directly, stdlib ASGI
messages in, messages out — the body-size middleware (413 on a declared or a
streamed body past ``MAX_BODY_BYTES``, a cap computed here to admit the largest
request the bounds accept), the 422 handler that never echoes ``input``, the
lock wait that ends in 503 busy and the per-request deadline that ends in 503
timeout. ``main.py``'s side — the middleware and both handlers registered,
``/health`` and ``/ready`` off the threadpool, the lock taken only through the
bounded wait, the deadline checked before every graph call — is read from its
AST.

**The rerank budget (#1751).** The reranker's server-side deadline only fits
so many scored characters per search. ``RERANK_SCORED_CHARS_BUDGET`` in the
caller's config.py records the measured envelope; the Settings defaults and
every deployment file that sets ``RERANKER_INITIAL_K`` or
``RERANKER_MAX_DOCUMENT_CHARS`` must keep ``initial_k x max_document_chars``
within it, so the budget cannot be raised without a reviewed re-measurement.
Every mention of the two names in a YAML/env file must be read as a value —
a spelling the reader does not know is red, never skipped.

Traces to #1725 and #1751 (no TC-ID: sidecar internals are not a user-facing case).
"""

from __future__ import annotations

import ast
import asyncio
import functools
import importlib.util
import json
import os
import re
import sys
import threading
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_KNOWLEDGE_SERVICE = _REPO_ROOT / "src" / "knowledge-service" / "app"
_CORPUS = _REPO_ROOT / "spec" / "knowledge" / "rag"


@functools.cache
def _load_limits(service: str) -> ModuleType:
    """Execute ``docker/<service>/limits.py`` — the file ``main.py`` imports — as a module.

    Registered in ``sys.modules`` before execution: pydantic resolves the
    postponed annotations of the request model through its module.
    """
    name = f"_ml_sidecar_limits_{service.replace('-', '_')}"
    path = _REPO_ROOT / "docker" / service / "limits.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"{path} is not loadable"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class Bound:
    """One bounded request field: a request at *limit* is accepted, one past it refused."""

    field: str
    constant: str
    expected: int
    build: Callable[[int], dict[str, Any]]


@dataclass(frozen=True)
class Sidecar:
    service: str
    model: str
    minimal: dict[str, Any]
    empty_field: str
    bounds: tuple[Bound, ...]
    #: The knowledge-service client module whose ``httpx.post(timeout=...)`` calls this service.
    client: str
    #: The largest request the bounds accept, every string filled with *char*.
    largest: Callable[[ModuleType, str], dict[str, Any]]

    @property
    def dir(self) -> Path:
        return _REPO_ROOT / "docker" / self.service

    def limits(self) -> ModuleType:
        return _load_limits(self.service)


_RERANKER = Sidecar(
    service="reranker-service",
    model="RerankRequest",
    minimal={"query": "q", "documents": ["d"]},
    empty_field="documents",
    bounds=(
        Bound("query", "MAX_QUERY_CHARS", 4096, lambda n: {"query": "q" * n, "documents": ["d"]}),
        Bound("documents", "MAX_DOCUMENTS", 100, lambda n: {"query": "q", "documents": ["d"] * n}),
        Bound("documents.0", "MAX_DOCUMENT_CHARS", 16384, lambda n: {"query": "q", "documents": ["d" * n]}),
        Bound("top_k", "MAX_TOP_K", 50, lambda n: {"query": "q", "documents": ["d"], "top_k": n}),
    ),
    client="reranker.py",
    largest=lambda limits, char: {
        "query": char * limits.MAX_QUERY_CHARS,
        "documents": [char * limits.MAX_DOCUMENT_CHARS] * limits.MAX_DOCUMENTS,
        "top_k": limits.MAX_TOP_K,
    },
)

_EMBEDDING = Sidecar(
    service="embedding-service",
    model="EmbedRequest",
    minimal={"texts": ["t"]},
    empty_field="texts",
    bounds=(
        Bound("texts", "MAX_TEXTS", 64, lambda n: {"texts": ["t"] * n}),
        Bound("texts.0", "MAX_TEXT_CHARS", 16384, lambda n: {"texts": ["t" * n]}),
        Bound("prefix", "MAX_PREFIX_CHARS", 64, lambda n: {"texts": ["t"], "prefix": "p" * n}),
        Bound("model", "MAX_MODEL_CHARS", 128, lambda n: {"texts": ["t"], "model": "m" * n}),
    ),
    client="embedding.py",
    largest=lambda limits, char: {
        "texts": [char * limits.MAX_TEXT_CHARS] * limits.MAX_TEXTS,
        "model": char * limits.MAX_MODEL_CHARS,
        "prefix": char * limits.MAX_PREFIX_CHARS,
    },
)

_SIDECARS = (_RERANKER, _EMBEDDING)
_BOUNDS = [
    pytest.param(sidecar, bound, id=f"{sidecar.service}:{bound.constant}")
    for sidecar in _SIDECARS
    for bound in sidecar.bounds
]
_BY_SERVICE = [pytest.param(sidecar, id=sidecar.service) for sidecar in _SIDECARS]


#: A runtime stage that ships a model an earlier stage produced — the same
#: signature ``test_model_images_prove_readiness.py`` finds model images by.
_MODEL_COPY = re.compile(r"^\s*COPY\s+--from=[\w.-]+\s+(?:--[\w-]+=\S+\s+)*/model\b", re.MULTILINE)


def _model_serving_images_under_docker() -> set[str]:
    """Every ``docker/<service>`` whose Dockerfile ships a build-stage model."""
    found = set()
    for dockerfile in sorted((_REPO_ROOT / "docker").glob("*/Dockerfile")):
        text = "\n".join(
            line for line in dockerfile.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#")
        )
        if _MODEL_COPY.search(text):
            found.add(dockerfile.parent.name)
    return found


def test_every_model_image_under_docker_is_a_governed_sidecar() -> None:
    """The class, not the two sites: a third ONNX sidecar must carry the same bounds.

    #1725 was found at one of two template copies and the other had every
    weakness too. This file governs a fixed list of services, so a new image
    under ``docker/`` that serves a model would otherwise be outside every
    assertion here — the sibling drift again, one copy later.
    """
    images = _model_serving_images_under_docker()
    assert images, "no model-serving Dockerfile under docker/ — the sweep stopped reaching the tree"
    governed = {sidecar.service for sidecar in _SIDECARS}
    assert images == governed, (
        f"model-serving images under docker/ {sorted(images)} != services this file governs {sorted(governed)}: "
        "add a Sidecar entry (bounds, cpu_budget, lock, runtime stage) for the new image, or remove the stale one"
    )


def _field_errors(model: type[BaseModel], payload: dict[str, Any]) -> list[str]:
    try:
        model.model_validate(payload)
    except ValidationError as exc:
        return [".".join(str(part) for part in error["loc"]) for error in exc.errors()]
    return []


# --------------------------------------------------------------------------
# request bounds
# --------------------------------------------------------------------------


class TestRequestBounds:
    @pytest.mark.parametrize(("sidecar", "bound"), _BOUNDS)
    def test_the_bound_has_its_contract_value(self, sidecar: Sidecar, bound: Bound) -> None:
        """A raised bound is a reviewed diff here, not a silent widening of the OOM surface."""
        assert getattr(sidecar.limits(), bound.constant) == bound.expected

    @pytest.mark.parametrize(("sidecar", "bound"), _BOUNDS)
    def test_a_request_at_the_bound_is_accepted(self, sidecar: Sidecar, bound: Bound) -> None:
        limits = sidecar.limits()
        model = getattr(limits, sidecar.model)
        limit = getattr(limits, bound.constant)

        assert _field_errors(model, bound.build(limit)) == []

    @pytest.mark.parametrize(("sidecar", "bound"), _BOUNDS)
    def test_a_request_one_past_the_bound_is_refused(self, sidecar: Sidecar, bound: Bound) -> None:
        limits = sidecar.limits()
        model = getattr(limits, sidecar.model)
        limit = getattr(limits, bound.constant)

        assert _field_errors(model, bound.build(limit + 1)) == [bound.field], (
            f"{sidecar.service}: {bound.field} one past {bound.constant}={limit} was not refused"
        )

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_an_empty_list_stays_a_valid_request(self, sidecar: Sidecar) -> None:
        """No minimum: ``documents: []`` / ``texts: []`` are answered, not refused."""
        model = getattr(sidecar.limits(), sidecar.model)

        assert _field_errors(model, {**sidecar.minimal, sidecar.empty_field: []}) == []

    @pytest.mark.parametrize(("sidecar", "bound"), _BOUNDS)
    def test_fastapi_answers_a_refused_bound_with_422(self, sidecar: Sidecar, bound: Bound) -> None:
        """The HTTP contract: a validation error of the body model is FastAPI's 422, not a 500."""
        limits = sidecar.limits()
        model = getattr(limits, sidecar.model)
        limit = getattr(limits, bound.constant)

        def endpoint(req: Any) -> dict[str, str]:
            return {"status": "accepted"}

        endpoint.__annotations__ = {"req": model, "return": dict[str, str]}
        app = FastAPI()
        app.post("/probe")(endpoint)
        client = TestClient(app)

        assert client.post("/probe", json=bound.build(limit)).status_code == 200
        assert client.post("/probe", json=bound.build(limit + 1)).status_code == 422


# --------------------------------------------------------------------------
# the bounds never refuse the real caller
# --------------------------------------------------------------------------


def _class_fields(tree: ast.Module, class_name: str) -> dict[str, ast.expr | None]:
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name]
    assert len(classes) == 1, f"class {class_name} not found exactly once"
    return {
        statement.target.id: statement.value
        for statement in classes[0].body
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)
    }


def _field_keyword(value: ast.expr | None, keyword: str) -> Any:
    assert isinstance(value, ast.Call), f"not a Field(...) call: {value and ast.unparse(value)}"
    found = [kw.value for kw in value.keywords if kw.arg == keyword]
    assert len(found) == 1 and isinstance(found[0], ast.Constant), f"no literal {keyword}= in {ast.unparse(value)}"
    return found[0].value


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _corpus_chunks() -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for path in sorted(_CORPUS.rglob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(document, dict) and isinstance(document.get("chunks"), list):
            chunks.extend(chunk for chunk in document["chunks"] if isinstance(chunk, dict))
    return chunks


def _corpus_chunks_per_file() -> int:
    counts = []
    for path in sorted(_CORPUS.rglob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(document, dict) and isinstance(document.get("chunks"), list):
            counts.append(len(document["chunks"]))
    return max(counts, default=0)


class TestTheCallerIsNeverRefused:
    def test_the_corpus_is_not_empty(self) -> None:
        """Every corpus maximum below is vacuous over an empty glob."""
        assert len(_corpus_chunks()) >= 100, f"only {len(_corpus_chunks())} chunks under {_CORPUS}"

    def test_the_reranker_takes_every_document_the_caller_retrieves(self) -> None:
        fields = _class_fields(_parse(_KNOWLEDGE_SERVICE / "config.py"), "Settings")
        initial_k = fields["reranker_initial_k"]
        assert isinstance(initial_k, ast.Constant) and isinstance(initial_k.value, int)

        assert initial_k.value <= _RERANKER.limits().MAX_DOCUMENTS

    def test_the_reranker_takes_every_question_the_caller_accepts(self) -> None:
        tree = _parse(_KNOWLEDGE_SERVICE / "schemas.py")
        longest = max(
            _field_keyword(_class_fields(tree, "AskRequest")["question"], "max_length"),
            _field_keyword(_class_fields(tree, "SearchRequest")["q"], "max_length"),
        )
        assert longest >= 2000, "the ask schema's bound was read wrongly"

        assert longest <= _RERANKER.limits().MAX_QUERY_CHARS

    def test_the_reranker_takes_every_document_of_the_corpus(self) -> None:
        """The caller sends ``f"{title}\\n{content}"`` per chunk (src/knowledge-service/app/reranker.py)."""
        longest = max(len(f"{chunk.get('title', '')}\n{chunk.get('content', '')}") for chunk in _corpus_chunks())

        assert longest <= _RERANKER.limits().MAX_DOCUMENT_CHARS

    def test_the_embedding_service_takes_every_chunk_of_the_corpus(self) -> None:
        """An upper bound of the ingestor's ``embed_text``: title, content and every metadata value."""
        longest = max(
            len(f"{chunk.get('title', '')}\n\n{chunk.get('content', '')}\n\n")
            + len(" | ".join(f"{key}: {value}" for key, value in (chunk.get("metadata") or {}).items()))
            for chunk in _corpus_chunks()
        )

        assert longest <= _EMBEDDING.limits().MAX_TEXT_CHARS

    def test_the_embedding_client_slices_well_below_the_count_bound(self) -> None:
        """Half the bound: headroom so a raised slice is a reviewed diff on both sides."""
        slices = [
            statement.value.value
            for statement in _parse(_KNOWLEDGE_SERVICE / "embedding.py").body
            if isinstance(statement, ast.Assign | ast.AnnAssign)
            for target in (statement.targets if isinstance(statement, ast.Assign) else [statement.target])
            if isinstance(target, ast.Name) and target.id == "_MAX_TEXTS_PER_REQUEST"
            if isinstance(statement.value, ast.Constant)
        ]
        assert len(slices) == 1, "src/knowledge-service/app/embedding.py has no literal _MAX_TEXTS_PER_REQUEST"
        assert slices[0] >= 1

        assert 2 * slices[0] <= _EMBEDDING.limits().MAX_TEXTS

    def test_a_file_of_today_s_corpus_fits_one_slice(self) -> None:
        """Not a requirement — a measurement: today one ingest is one request."""
        assert _corpus_chunks_per_file() <= _EMBEDDING.limits().MAX_TEXTS // 2

    def test_every_prefix_the_caller_sends_fits(self) -> None:
        prefixes = {
            keyword.value.value
            for path in sorted(_KNOWLEDGE_SERVICE.rglob("*.py"))
            for node in ast.walk(_parse(path))
            if isinstance(node, ast.Call)
            for keyword in node.keywords
            if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant)
            if isinstance(keyword.value.value, str)
        }
        assert {"query: ", "passage: "} <= prefixes, f"the caller's prefixes were read wrongly: {prefixes}"

        assert max(len(prefix) for prefix in prefixes) <= _EMBEDDING.limits().MAX_PREFIX_CHARS

    def test_the_caller_s_default_model_name_fits(self) -> None:
        model = _class_fields(_parse(_KNOWLEDGE_SERVICE / "config.py"), "Settings")["embedding_model"]
        assert isinstance(model, ast.Constant) and isinstance(model.value, str)

        assert len(model.value) <= _EMBEDDING.limits().MAX_MODEL_CHARS


# --------------------------------------------------------------------------
# the rerank budget (#1751)
# --------------------------------------------------------------------------

_RERANK_BUDGET_VARS = ("RERANKER_INITIAL_K", "RERANKER_MAX_DOCUMENT_CHARS")

#: Directories that never configure a deployment: VCS, dependencies, caches,
#: and prose (docs/spec quote the variables in examples).
_NOT_DEPLOYMENT_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "docs",
        "spec",
        "site",
        "dist",
        "build",
        ".worktrees",
    }
)


def _is_config_file(path: Path) -> bool:
    """Every file a deployment's env can be written in: YAML (chart values, compose, CI) and env files."""
    return path.suffix in {".yaml", ".yml", ".env"} or path.name.startswith(".env")


def _deployment_config_files() -> list[Path]:
    found = []
    for directory, subdirectories, files in os.walk(_REPO_ROOT):
        subdirectories[:] = sorted(d for d in subdirectories if d not in _NOT_DEPLOYMENT_DIRS)
        found.extend(Path(directory) / name for name in sorted(files) if _is_config_file(Path(directory) / name))
    return found


def _budget_assignment_patterns(name: str) -> list[re.Pattern[str]]:
    """The spellings a value of *name* is read in; group 1 is the integer."""
    quoted = r"[\"']?(\d+)[\"']?"
    return [
        # compose interpolation with a default: NAME: ${NAME:-15}
        re.compile(rf"\b{name}\s*[:=]\s*[\"']?\$\{{{name}:?-(\d+)\}}[\"']?"),
        # map (NAME: "15"), env file / compose list (NAME=15, - NAME=15)
        re.compile(rf"\b{name}\s*[:=]\s*{quoted}"),
        # Kubernetes env list: name: NAME / value: "15"
        re.compile(rf"\bname:\s*[\"']?{name}[\"']?\s*\n\s*value:\s*{quoted}"),
    ]


def _budget_settings_in(text: str) -> tuple[dict[str, list[int]], list[str]]:
    """Values set for the two budget variables in *text*, and every mention that is not one.

    Comment lines are ignored. A mention the patterns do not consume is
    returned as unparsed, so a new spelling fails the guard instead of being
    skipped by it.
    """
    body = "\n".join("" if line.lstrip().startswith("#") else line for line in text.splitlines())
    values: dict[str, list[int]] = {}
    unparsed: list[str] = []
    for name in _RERANK_BUDGET_VARS:
        covered: list[tuple[int, int]] = []
        for pattern in _budget_assignment_patterns(name):
            for match in pattern.finditer(body):
                if any(start <= match.start() < end for start, end in covered):
                    continue
                covered.append(match.span())
                values.setdefault(name, []).append(int(match.group(1)))
        for mention in re.finditer(rf"\b{name}\b", body):
            if not any(start <= mention.start() < end for start, end in covered):
                line = body.count("\n", 0, mention.start()) + 1
                unparsed.append(f"line {line}: {body.splitlines()[line - 1].strip()}")
    return values, unparsed


def _config_literal(name: str) -> int:
    values = [
        statement.value
        for statement in _parse(_KNOWLEDGE_SERVICE / "config.py").body
        if isinstance(statement, ast.Assign | ast.AnnAssign)
        for target in (statement.targets if isinstance(statement, ast.Assign) else [statement.target])
        if isinstance(target, ast.Name) and target.id == name
    ]
    assert len(values) == 1, f"no single module-level {name} in src/knowledge-service/app/config.py"
    value = values[0]
    assert isinstance(value, ast.Constant) and isinstance(value.value, int), f"{name} is not a literal int"
    return value.value


def _settings_default(field: str) -> int:
    value = _class_fields(_parse(_KNOWLEDGE_SERVICE / "config.py"), "Settings")[field]
    assert isinstance(value, ast.Constant) and isinstance(value.value, int), f"Settings.{field} is not a literal int"
    return value.value


class TestTheRerankBudgetHolds:
    def test_the_defaults_fit_the_budget(self) -> None:
        budget = _config_literal("RERANK_SCORED_CHARS_BUDGET")
        initial_k = _settings_default("reranker_initial_k")
        chars = _settings_default("reranker_max_document_chars")

        assert initial_k * chars <= budget, f"{initial_k} x {chars} > {budget}: re-measure before raising (#1751)"

    def test_every_deployment_file_fits_the_budget(self) -> None:
        budget = _config_literal("RERANK_SCORED_CHARS_BUDGET")
        defaults = {
            "RERANKER_INITIAL_K": _settings_default("reranker_initial_k"),
            "RERANKER_MAX_DOCUMENT_CHARS": _settings_default("reranker_max_document_chars"),
        }
        setting: dict[str, dict[str, list[int]]] = {}
        problems: list[str] = []
        for path in _deployment_config_files():
            try:
                text = path.read_text(encoding="utf-8")
            except OSError, UnicodeDecodeError:
                continue
            values, unparsed = _budget_settings_in(text)
            relative = path.relative_to(_REPO_ROOT).as_posix()
            problems.extend(f"{relative} {mention}: not read as a value" for mention in unparsed)
            if not values:
                continue
            setting[relative] = values
            # A file setting only one of the two combines with the other's default.
            initial_k = max(values.get("RERANKER_INITIAL_K", [defaults["RERANKER_INITIAL_K"]]))
            chars = max(values.get("RERANKER_MAX_DOCUMENT_CHARS", [defaults["RERANKER_MAX_DOCUMENT_CHARS"]]))
            if initial_k * chars > budget:
                problems.append(f"{relative}: {initial_k} x {chars} > {budget}")

        assert "helm/kamerplanter/values-dev-ki.yaml" in setting, f"the reader found no setting: {sorted(setting)}"
        assert not problems, "re-measure before raising the rerank budget (#1751):\n" + "\n".join(problems)

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            (
                'RERANKER_INITIAL_K: "15"\nRERANKER_MAX_DOCUMENT_CHARS: 500',
                {"RERANKER_INITIAL_K": [15], "RERANKER_MAX_DOCUMENT_CHARS": [500]},
            ),
            ("environment:\n  - RERANKER_INITIAL_K=20", {"RERANKER_INITIAL_K": [20]}),
            ("RERANKER_MAX_DOCUMENT_CHARS='800'", {"RERANKER_MAX_DOCUMENT_CHARS": [800]}),
            ("RERANKER_INITIAL_K: ${RERANKER_INITIAL_K:-25}", {"RERANKER_INITIAL_K": [25]}),
            ('- name: RERANKER_INITIAL_K\n  value: "30"', {"RERANKER_INITIAL_K": [30]}),
            ("# RERANKER_INITIAL_K: 99 is only a comment", {}),
        ],
    )
    def test_the_reader_reads_every_known_spelling(self, text: str, expected: dict[str, list[int]]) -> None:
        values, unparsed = _budget_settings_in(text)

        assert (values, unparsed) == (expected, [])

    @pytest.mark.parametrize(
        "text",
        [
            "RERANKER_INITIAL_K: ${RERANKER_INITIAL_K}",
            "- name: RERANKER_INITIAL_K\n  valueFrom:\n    configMapKeyRef: {name: rag, key: k}",
            "RERANKER_MAX_DOCUMENT_CHARS: twenty",
        ],
    )
    def test_a_spelling_the_reader_does_not_know_is_reported(self, text: str) -> None:
        _, unparsed = _budget_settings_in(text)

        assert unparsed


# --------------------------------------------------------------------------
# cpu_budget
# --------------------------------------------------------------------------


def _cgroup(root: Path, files: dict[str, str]) -> Path:
    for name, content in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(content)
    return root


class TestCpuBudget:
    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    @pytest.mark.parametrize(
        ("files", "available", "expected"),
        [
            pytest.param({"cpu.max": "200000 100000\n"}, 8, 2, id="v2-two-cpus-of-eight"),
            pytest.param({"cpu.max": "max 100000\n"}, 8, 8, id="v2-unlimited"),
            pytest.param({"cpu.max": "150000 100000\n"}, 8, 2, id="v2-fraction-rounds-up"),
            pytest.param({"cpu.max": "50000 100000\n"}, 8, 1, id="v2-half-cpu-is-one"),
            pytest.param({"cpu.max": "1600000 100000\n"}, 4, 4, id="v2-quota-above-affinity"),
            pytest.param({"cpu.max": "garbage\n"}, 6, 6, id="v2-unparseable"),
            pytest.param({"cpu/cpu.cfs_quota_us": "300000\n", "cpu/cpu.cfs_period_us": "100000\n"}, 8, 3, id="v1"),
            pytest.param(
                {"cpu,cpuacct/cpu.cfs_quota_us": "100000\n", "cpu,cpuacct/cpu.cfs_period_us": "100000\n"},
                8,
                1,
                id="v1-combined-controller",
            ),
            pytest.param({"cpu/cpu.cfs_quota_us": "-1\n", "cpu/cpu.cfs_period_us": "100000\n"}, 8, 8, id="v1-no-quota"),
            pytest.param({}, 5, 5, id="no-cgroup-files"),
            pytest.param({}, 0, 1, id="never-below-one"),
        ],
    )
    def test_the_budget(
        self, sidecar: Sidecar, files: dict[str, str], available: int, expected: int, tmp_path: Path
    ) -> None:
        budget = sidecar.limits().cpu_budget(_cgroup(tmp_path, files), available_cpus=available)

        assert budget == expected

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_without_a_quota_it_is_the_affinity_set(self, sidecar: Sidecar, tmp_path: Path) -> None:
        """The default affinity source, not an injected count."""
        expected = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)

        assert sidecar.limits().cpu_budget(tmp_path) == max(1, expected)

    def test_both_services_share_one_implementation(self) -> None:
        """Two build contexts, one rule: the copies may not drift apart."""
        names = (
            "cpu_budget",
            "_cgroup_cpu_limit",
            "_ceil_quota",
            "_read_fields",
            "_available_cpus",
            "JSONAnswer",
            "_declared_length",
            "BodySizeLimit",
            "ServiceUnavailableError",
            "inference_slot",
            "Deadline",
            "_HasErrors",
            "validation_error_handler",
            "unavailable_handler",
        )

        def functions(sidecar: Sidecar) -> dict[str, str]:
            tree = _parse(sidecar.dir / "limits.py")
            return {
                node.name: ast.dump(node)
                for node in tree.body
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) and node.name in names
            }

        reranker, embedding = functions(_RERANKER), functions(_EMBEDDING)
        assert set(reranker) == set(names)
        assert reranker == embedding


# --------------------------------------------------------------------------
# main.py wiring (AST — main.py needs onnxruntime and cannot be imported here)
# --------------------------------------------------------------------------


def _main(sidecar: Sidecar) -> ast.Module:
    return _parse(sidecar.dir / "main.py")


def _route(tree: ast.Module) -> ast.FunctionDef:
    routes = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        for decorator in node.decorator_list
        if isinstance(decorator, ast.Call) and ast.unparse(decorator.func) == "app.post"
    ]
    assert len(routes) == 1, f"expected exactly one POST route, found {[r.name for r in routes]}"
    return routes[0]


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}


def _module_locks(tree: ast.Module) -> set[str]:
    return {
        target.id
        for node in tree.body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
        if ast.unparse(node.value.func) == "threading.Lock"
        for target in node.targets
        if isinstance(target, ast.Name)
    }


def _slot_of(item: ast.withitem, locks: set[str]) -> bool:
    """``with inference_slot(<module lock>, ...)`` — the lock entered through the bounded wait."""
    call = item.context_expr
    return (
        isinstance(call, ast.Call)
        and ast.unparse(call.func) == "inference_slot"
        and bool(call.args)
        and ast.unparse(call.args[0]) in locks
    )


def _get_route(tree: ast.Module, path: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    routes = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        for decorator in node.decorator_list
        if isinstance(decorator, ast.Call) and ast.unparse(decorator.func) == "app.get"
        if decorator.args and isinstance(decorator.args[0], ast.Constant) and decorator.args[0].value == path
    ]
    assert len(routes) == 1, f"expected exactly one GET {path}, found {len(routes)}"
    return routes[0]


def _module_calls(tree: ast.Module, func: str) -> list[ast.Call]:
    """Calls of *func* made as statements at module level (``app.add_middleware(...)`` and the like)."""
    return [
        node.value
        for node in tree.body
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and ast.unparse(node.value.func) == func
    ]


class TestMainWiring:
    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_main_imports_its_request_model_from_limits(self, sidecar: Sidecar) -> None:
        """Otherwise the bounds tested above are not the bounds that run."""
        tree = _main(sidecar)
        imported = {
            alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "limits"
            for alias in node.names
        }
        defined = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}

        assert {sidecar.model, "cpu_budget"} <= imported
        assert sidecar.model not in defined

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_intra_op_threads_come_from_cpu_budget(self, sidecar: Sidecar) -> None:
        assignments = [
            node.value
            for node in ast.walk(_main(sidecar))
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Attribute) and target.attr == "intra_op_num_threads"
        ]

        assert len(assignments) == 1, f"{sidecar.service}: intra_op_num_threads assigned {len(assignments)} times"
        value = assignments[0]
        assert isinstance(value, ast.Call) and ast.unparse(value.func) == "cpu_budget", ast.unparse(value)

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_inter_op_threads_are_one(self, sidecar: Sidecar) -> None:
        values = [
            ast.unparse(node.value)
            for node in ast.walk(_main(sidecar))
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Attribute) and target.attr == "inter_op_num_threads"
        ]

        assert values == ["1"]

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_main_never_reads_the_host_cpu_count(self, sidecar: Sidecar) -> None:
        calls = [
            ast.unparse(node)
            for node in ast.walk(_main(sidecar))
            if isinstance(node, ast.Call)
            if (isinstance(node.func, ast.Attribute) and node.func.attr == "cpu_count")
            or (isinstance(node.func, ast.Name) and node.func.id == "cpu_count")
        ]

        assert calls == []

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_graph_runs_one_input_at_a_time_under_one_lock(self, sidecar: Sidecar) -> None:
        """B=1 under a module-level lock: bounded memory per request AND across requests.

        Measured 2026-09-24 (N=20 reranker / N=16 e5-large, ``-m 4g --cpus 2``):
        full batch 56.5 s / 47.9 s at 3001 / 2293 MiB maxrss; one input per run
        31.9 s / 24.7 s at 1595 / 1650 MiB, outputs identical (max |Δ| 0.0).
        """
        tree = _main(sidecar)
        locks = _module_locks(tree)
        assert len(locks) == 1, f"{sidecar.service}: expected one module-level threading.Lock(), found {locks}"

        route = _route(tree)
        runs = [
            node
            for node in ast.walk(route)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run"
        ]
        assert len(runs) == 1, f"{sidecar.service}: the route must call session.run exactly once"

        parents = _parents(route)
        chain = []
        node: ast.AST = runs[0]
        while node in parents:
            node = parents[node]
            chain.append(node)
        loops = [n for n in chain if isinstance(n, ast.For)]
        guarded = [n for n in chain if isinstance(n, ast.With) and any(_slot_of(item, locks) for item in n.items)]
        assert loops, f"{sidecar.service}: session.run is not inside a per-input loop"
        assert guarded, f"{sidecar.service}: session.run is not inside `with inference_slot({next(iter(locks))}, ...):`"
        assert chain.index(loops[0]) < chain.index(guarded[0]), "the lock must enclose the whole loop"

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    @pytest.mark.parametrize("path", ["/health", "/ready"])
    def test_the_probes_run_on_the_event_loop(self, sidecar: Sidecar, path: str) -> None:
        """A sync probe shares the 40-thread pool with requests queued on the lock and can starve."""
        route = _get_route(_main(sidecar), path)

        assert isinstance(route, ast.AsyncFunctionDef), f"{sidecar.service}: GET {path} is a sync `def`"

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_lock_is_only_ever_taken_with_a_bounded_wait(self, sidecar: Sidecar) -> None:
        """``inference_slot(lock, wait_seconds=LOCK_WAIT_SECONDS)`` — never ``with lock:`` or ``acquire()``."""
        tree = _main(sidecar)
        locks = _module_locks(tree)
        slots = [
            item.context_expr
            for node in ast.walk(tree)
            if isinstance(node, ast.With)
            for item in node.items
            if _slot_of(item, locks)
        ]
        bare = [
            ast.unparse(node)
            for node in ast.walk(tree)
            if (isinstance(node, ast.withitem) and ast.unparse(node.context_expr) in locks)
            or (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and ast.unparse(node.func.value) in locks
            )
        ]

        assert bare == [], f"{sidecar.service}: the inference lock is used without the bounded wait: {bare}"
        assert len(slots) == 1, f"{sidecar.service}: expected one `with inference_slot(...)`, found {len(slots)}"
        slot = slots[0]
        assert isinstance(slot, ast.Call)
        waits = [ast.unparse(keyword.value) for keyword in slot.keywords if keyword.arg == "wait_seconds"]
        assert waits == ["LOCK_WAIT_SECONDS"], ast.unparse(slot)

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_deadline_is_checked_before_every_graph_call(self, sidecar: Sidecar) -> None:
        """``Deadline(MAX_INFERENCE_SECONDS)`` started before the lock wait, checked first thing per input."""
        route = _route(_main(sidecar))
        deadlines = [
            node.targets[0].id
            for node in ast.walk(route)
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
            if ast.unparse(node.value) == "Deadline(MAX_INFERENCE_SECONDS)"
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        ]
        assert len(deadlines) == 1, f"{sidecar.service}: no single `x = Deadline(MAX_INFERENCE_SECONDS)` in the route"

        run = next(
            node
            for node in ast.walk(route)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "run"
        )
        parents = _parents(route)
        node: ast.AST = run
        while not isinstance(node, ast.For):
            node = parents[node]
        first = node.body[0]

        assert isinstance(first, ast.Expr) and ast.unparse(first.value) == f"{deadlines[0]}.check()", (
            f"{sidecar.service}: the per-input loop does not start with `{deadlines[0]}.check()`"
        )
        slot = next(n for n in ast.walk(route) if isinstance(n, ast.With))
        started = next(
            n for n in route.body if isinstance(n, ast.Assign) and ast.unparse(n.value).startswith("Deadline(")
        )
        assert started.lineno < slot.lineno, "the deadline must be started before the lock wait, so it includes it"

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_body_cap_and_both_handlers_are_registered(self, sidecar: Sidecar) -> None:
        """The functions tested below are the functions that run."""
        tree = _main(sidecar)
        middleware = [ast.unparse(call) for call in _module_calls(tree, "app.add_middleware")]
        handlers = {
            ast.unparse(call.args[0]): ast.unparse(call.args[1])
            for call in _module_calls(tree, "app.add_exception_handler")
            if len(call.args) == 2
        }
        imported = {
            alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "limits"
            for alias in node.names
        }

        assert middleware == ["app.add_middleware(BodySizeLimit, max_body_bytes=MAX_BODY_BYTES)"]
        assert handlers == {
            "RequestValidationError": "validation_error_handler",
            "ServiceUnavailableError": "unavailable_handler",
        }
        assert {
            "BodySizeLimit",
            "MAX_BODY_BYTES",
            "validation_error_handler",
            "unavailable_handler",
            "ServiceUnavailableError",
            "inference_slot",
            "Deadline",
            "LOCK_WAIT_SECONDS",
            "MAX_INFERENCE_SECONDS",
        } <= imported
        defined = {n.name for n in tree.body if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)}
        assert not defined & imported, f"{sidecar.service}: main.py shadows {defined & imported}"


# --------------------------------------------------------------------------
# serving under load: body cap, 422 shape, bounded lock wait, deadline
# --------------------------------------------------------------------------

#: Outside the Basic Multilingual Plane: ONE character for pydantic's
#: ``max_length``, TWELVE bytes in ``json.dumps`` (two ``\\uXXXX`` escapes).
_WORST_CHAR = "\U0001f600"


def _run(middleware: Any, scope: dict[str, Any], messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drive *middleware* with *messages* as the client side; return what it sent back."""
    inbox = list(messages)
    sent: list[dict[str, Any]] = []

    async def receive() -> dict[str, Any]:
        if not inbox:
            raise AssertionError("the middleware read past the last message the client sent")
        return inbox.pop(0)

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    asyncio.run(middleware(scope, receive, send))
    return sent


class _RecordingApp:
    """The application behind the middleware: records what it received, answers 200."""

    def __init__(self) -> None:
        self.calls = 0
        self.received: list[dict[str, Any]] = []

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        self.calls += 1
        if scope["type"] == "http":
            message = await receive()
            self.received.append(message)
            while message.get("more_body"):
                message = await receive()
                self.received.append(message)
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})


def _http(headers: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "type": "http",
        "method": "POST",
        "path": "/probe",
        "headers": [(name.encode(), value.encode()) for name, value in (headers or {}).items()],
    }


def _status(sent: list[dict[str, Any]]) -> int:
    starts = [message for message in sent if message["type"] == "http.response.start"]
    assert len(starts) == 1, sent
    return int(starts[0]["status"])


def _header(sent: list[dict[str, Any]], name: str) -> str | None:
    start = next(message for message in sent if message["type"] == "http.response.start")
    values = [value.decode() for key, value in start["headers"] if key.decode().lower() == name]
    return values[0] if values else None


class TestBodySizeLimit:
    """The ASGI callable itself, stdlib messages in and out — no server, no FastAPI."""

    CAP = 10

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_a_declared_length_over_the_cap_is_refused_unread(self, sidecar: Sidecar) -> None:
        app = _RecordingApp()
        middleware = sidecar.limits().BodySizeLimit(app, max_body_bytes=self.CAP)

        # No client messages at all: reading one would raise in `receive`.
        sent = _run(middleware, _http({"content-length": str(self.CAP + 1)}), [])

        assert _status(sent) == 413
        assert _header(sent, "connection") == "close"
        assert app.calls == 0

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_a_chunked_body_over_the_cap_is_refused_while_it_streams(self, sidecar: Sidecar) -> None:
        """No Content-Length: the bytes are counted, and nothing past the cap is read."""
        app = _RecordingApp()
        middleware = sidecar.limits().BodySizeLimit(app, max_body_bytes=self.CAP)
        chunks = [
            {"type": "http.request", "body": b"x" * 6, "more_body": True},
            {"type": "http.request", "body": b"x" * 5, "more_body": True},
        ]

        sent = _run(middleware, _http({"transfer-encoding": "chunked"}), chunks)

        assert _status(sent) == 413
        assert app.calls == 0

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_a_body_that_outgrows_its_declared_length_is_refused(self, sidecar: Sidecar) -> None:
        app = _RecordingApp()
        middleware = sidecar.limits().BodySizeLimit(app, max_body_bytes=self.CAP)
        chunks = [{"type": "http.request", "body": b"x" * (self.CAP + 1), "more_body": False}]

        sent = _run(middleware, _http({"content-length": "2"}), chunks)

        assert _status(sent) == 413
        assert app.calls == 0

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_a_body_at_the_cap_reaches_the_application_whole(self, sidecar: Sidecar) -> None:
        app = _RecordingApp()
        middleware = sidecar.limits().BodySizeLimit(app, max_body_bytes=self.CAP)
        chunks = [
            {"type": "http.request", "body": b"abcd", "more_body": True},
            {"type": "http.request", "body": b"efghij", "more_body": False},
        ]

        sent = _run(middleware, _http({"transfer-encoding": "chunked"}), chunks)

        assert _status(sent) == 200
        assert app.received == [{"type": "http.request", "body": b"abcdefghij", "more_body": False}]

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_a_client_that_leaves_mid_body_gets_no_answer_and_no_application(self, sidecar: Sidecar) -> None:
        app = _RecordingApp()
        middleware = sidecar.limits().BodySizeLimit(app, max_body_bytes=self.CAP)
        messages = [{"type": "http.request", "body": b"ab", "more_body": True}, {"type": "http.disconnect"}]

        sent = _run(middleware, _http(), messages)

        assert sent == []
        assert app.calls == 0

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_lifespan_passes_through(self, sidecar: Sidecar) -> None:
        app = _RecordingApp()
        middleware = sidecar.limits().BodySizeLimit(app, max_body_bytes=self.CAP)

        _run(middleware, {"type": "lifespan"}, [])

        assert app.calls == 1

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_service_cap_itself_splits_at_max_body_bytes(self, sidecar: Sidecar) -> None:
        """The same callable with the service's own cap: declared cap passes, cap + 1 does not."""
        limits = sidecar.limits()
        cap = limits.MAX_BODY_BYTES
        refused_app, passed_app = _RecordingApp(), _RecordingApp()

        refused = _run(
            limits.BodySizeLimit(refused_app, max_body_bytes=cap), _http({"content-length": str(cap + 1)}), []
        )
        passed = _run(
            limits.BodySizeLimit(passed_app, max_body_bytes=cap),
            _http({"content-length": str(cap)}),
            [{"type": "http.request", "body": b"x" * cap, "more_body": False}],
        )

        assert (_status(refused), refused_app.calls) == (413, 0)
        assert (_status(passed), passed_app.calls) == (200, 1)

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_fastapi_behind_it_answers_413_and_still_serves(self, sidecar: Sidecar) -> None:
        """Registered the way main.py registers it, in front of a real FastAPI app."""
        limits = sidecar.limits()
        app = FastAPI()
        app.add_middleware(limits.BodySizeLimit, max_body_bytes=64)

        @app.post("/probe")
        def probe(payload: dict[str, Any]) -> dict[str, int]:
            return {"keys": len(payload)}

        client = TestClient(app)

        assert client.post("/probe", json={"a": "b"}).json() == {"keys": 1}
        assert client.post("/probe", json={"a": "b" * 100}).status_code == 413
        streamed = client.post("/probe", content=iter([b'{"a": "', b"b" * 100, b'"}']))
        assert streamed.status_code == 413


class TestBodyCap:
    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_largest_request_the_bounds_accept_fits_under_the_cap(self, sidecar: Sidecar) -> None:
        """Computed, so a raised bound without a raised cap is red here — and so is a cap of 6 bytes per char."""
        limits = sidecar.limits()
        payload = sidecar.largest(limits, _WORST_CHAR)
        assert _field_errors(getattr(limits, sidecar.model), payload) == [], "the payload is not at the bounds"

        size = len(json.dumps(payload).encode())

        assert size <= limits.MAX_BODY_BYTES, f"{sidecar.service}: an accepted request of {size} bytes gets 413"

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_cap_is_not_much_more_than_that(self, sidecar: Sidecar) -> None:
        """At most the documented 64 KiB of slack above the largest acceptable request."""
        limits = sidecar.limits()
        size = len(json.dumps(sidecar.largest(limits, _WORST_CHAR)).encode())

        assert limits.MAX_BODY_BYTES - size <= limits.BODY_SLACK_BYTES


class TestValidationAnswer:
    @pytest.mark.parametrize(("sidecar", "bound"), _BOUNDS)
    def test_a_refused_bound_is_named_but_not_echoed(self, sidecar: Sidecar, bound: Bound) -> None:
        limits = sidecar.limits()
        model = getattr(limits, sidecar.model)
        limit = getattr(limits, bound.constant)

        def endpoint(req: Any) -> dict[str, str]:
            return {"status": "accepted"}

        endpoint.__annotations__ = {"req": model, "return": dict[str, str]}
        app = FastAPI()
        app.post("/probe")(endpoint)
        app.add_exception_handler(RequestValidationError, limits.validation_error_handler)
        client = TestClient(app)

        response = client.post("/probe", json=bound.build(limit + 1))

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert [".".join(str(part) for part in error["loc"][1:]) for error in detail] == [bound.field]
        assert all(set(error) == {"loc", "type", "msg"} for error in detail), detail
        assert len(response.content) < 512, f"{len(response.content)} bytes: the input is echoed"

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_malformed_json_carries_no_input_either(self, sidecar: Sidecar) -> None:
        limits = sidecar.limits()
        model = getattr(limits, sidecar.model)

        def endpoint(req: Any) -> dict[str, str]:
            return {"status": "accepted"}

        endpoint.__annotations__ = {"req": model, "return": dict[str, str]}
        app = FastAPI()
        app.post("/probe")(endpoint)
        app.add_exception_handler(RequestValidationError, limits.validation_error_handler)

        response = TestClient(app).post("/probe", content=b'{"x": ', headers={"content-type": "application/json"})

        assert response.status_code == 422
        assert all(set(error) == {"loc", "type", "msg"} for error in response.json()["detail"])


#: A wait of 0.05 s that has not ended after this long is an unbounded one.
_UNBOUNDED_AFTER_SECONDS = 5.0


def _within(seconds: float, call: Callable[[], Any]) -> Any:
    """``call()`` on a daemon thread; fail — instead of hanging the suite — if it has not returned in time.

    Every caller holds the lock the call waits on and releases it in a
    ``finally``, so a wait that turns out to be unbounded still ends and the
    thread does not outlive the test.
    """
    outcome: list[Any] = []
    worker = threading.Thread(target=lambda: outcome.append(call()), daemon=True)
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        pytest.fail(f"still waiting after {seconds}s: the lock wait is not bounded")
    assert outcome, "the call raised instead of returning (see the thread's traceback above)"
    return outcome[0]


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class TestBusyAndDeadline:
    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_a_free_lock_is_held_for_the_body_and_released(self, sidecar: Sidecar) -> None:
        lock = threading.Lock()

        with sidecar.limits().inference_slot(lock, wait_seconds=0.01):
            assert lock.locked()

        assert not lock.locked()

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_a_held_lock_is_busy_after_the_wait(self, sidecar: Sidecar) -> None:
        limits = sidecar.limits()
        lock = threading.Lock()

        def enter() -> str:
            try:
                with limits.inference_slot(lock, wait_seconds=0.05):
                    return "the body ran without the lock"
            except limits.ServiceUnavailableError as exc:
                return str(exc.status)

        lock.acquire()
        try:
            outcome = _within(_UNBOUNDED_AFTER_SECONDS, enter)
        finally:
            lock.release()

        assert outcome == "busy"

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_an_abort_inside_releases_the_lock(self, sidecar: Sidecar) -> None:
        limits = sidecar.limits()
        lock = threading.Lock()

        with pytest.raises(limits.ServiceUnavailableError), limits.inference_slot(lock, wait_seconds=0.01):
            raise limits.ServiceUnavailableError("timeout")

        assert not lock.locked()

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_deadline(self, sidecar: Sidecar) -> None:
        limits = sidecar.limits()
        clock = _Clock()
        deadline = limits.Deadline(limits.MAX_INFERENCE_SECONDS, clock=clock)

        clock.now += limits.MAX_INFERENCE_SECONDS - 0.001
        deadline.check()
        clock.now += 0.001
        with pytest.raises(limits.ServiceUnavailableError) as raised:
            deadline.check()

        assert raised.value.status == "timeout"

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    @pytest.mark.parametrize("status", ["busy", "timeout"])
    def test_fastapi_answers_503_with_retry_after(self, sidecar: Sidecar, status: str) -> None:
        """A sync route raising from the threadpool, as `/rerank` and `/embed` do."""
        limits = sidecar.limits()
        app = FastAPI()
        app.add_exception_handler(limits.ServiceUnavailableError, limits.unavailable_handler)

        @app.post("/probe")
        def probe() -> dict[str, str]:
            raise limits.ServiceUnavailableError(status)

        response = TestClient(app).post("/probe")

        assert response.status_code == 503
        assert response.json() == {"status": status}
        assert response.headers["retry-after"] == str(limits.LOCK_WAIT_SECONDS)

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_a_second_request_behind_a_held_lock_is_turned_away(self, sidecar: Sidecar) -> None:
        """End to end through FastAPI: the route waits the bounded time, then 503 busy."""
        limits = sidecar.limits()
        lock = threading.Lock()
        app = FastAPI()
        app.add_exception_handler(limits.ServiceUnavailableError, limits.unavailable_handler)

        @app.post("/probe")
        def probe() -> dict[str, str]:
            with limits.inference_slot(lock, wait_seconds=0.05):
                return {"status": "served"}

        client = TestClient(app)
        lock.acquire()
        try:
            busy = _within(_UNBOUNDED_AFTER_SECONDS, lambda: client.post("/probe"))
        finally:
            lock.release()
        served = client.post("/probe")

        assert (busy.status_code, busy.json()) == (503, {"status": "busy"})
        assert (served.status_code, served.json()) == (200, {"status": "served"})


class TestServingBudgets:
    @pytest.mark.parametrize(
        ("sidecar", "lock_wait", "max_inference"),
        [
            pytest.param(_RERANKER, 10, 25, id="reranker-service"),
            pytest.param(_EMBEDDING, 60, 110, id="embedding-service"),
        ],
    )
    def test_the_budgets_have_their_contract_values(self, sidecar: Sidecar, lock_wait: int, max_inference: int) -> None:
        """Measured values (limits.py): 20 long pairs 50.4 s, 16 long e5-large texts 40.3 s, at 2 CPUs."""
        limits = sidecar.limits()

        assert (lock_wait, max_inference) == (limits.LOCK_WAIT_SECONDS, limits.MAX_INFERENCE_SECONDS)

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_lock_wait_ends_before_the_caller_gives_up(self, sidecar: Sidecar) -> None:
        """A request that finally gets the lock must still have a caller to answer."""
        timeouts = [
            keyword.value.value
            for node in ast.walk(_parse(_KNOWLEDGE_SERVICE / sidecar.client))
            if isinstance(node, ast.Call) and ast.unparse(node.func) == "httpx.post"
            for keyword in node.keywords
            if keyword.arg == "timeout" and isinstance(keyword.value, ast.Constant)
        ]
        assert len(timeouts) == 1, f"{sidecar.client}: no single literal httpx.post(timeout=...)"
        limits = sidecar.limits()

        assert timeouts[0] > limits.LOCK_WAIT_SECONDS
        assert limits.LOCK_WAIT_SECONDS < limits.MAX_INFERENCE_SECONDS

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_no_request_outlives_its_caller(self, sidecar: Sidecar) -> None:
        """The deadline (lock wait included) ends before the caller's client timeout.

        Past the timeout nobody reads the answer; computing on only holds the
        process-wide lock against the next caller, who then waits
        ``LOCK_WAIT_SECONDS`` for a 503. The bundle's first budgets (reranker
        120 s, embedding 300 s against 30 s / 120 s) did exactly that.
        """
        timeouts = [
            keyword.value.value
            for node in ast.walk(_parse(_KNOWLEDGE_SERVICE / sidecar.client))
            if isinstance(node, ast.Call) and ast.unparse(node.func) == "httpx.post"
            for keyword in node.keywords
            if keyword.arg == "timeout" and isinstance(keyword.value, ast.Constant)
        ]
        assert len(timeouts) == 1, f"{sidecar.client}: no single literal httpx.post(timeout=...)"

        assert timeouts[0] > sidecar.limits().MAX_INFERENCE_SECONDS


# --------------------------------------------------------------------------
# the runtime image: files the server cannot rewrite, no uv
# --------------------------------------------------------------------------


def _instructions(dockerfile: Path) -> list[str]:
    folded = re.sub(r"\\\s*\n\s*", " ", dockerfile.read_text(encoding="utf-8"))
    return [line.strip() for line in folded.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def _stage(instructions: list[str], name: str) -> list[str]:
    """The instructions of stage *name*, its ``FROM`` line first."""
    stage: list[str] = []
    for line in instructions:
        if re.match(r"(?i)^FROM\s", line):
            if stage:
                break
            if re.search(rf"(?i)\sAS\s+{re.escape(name)}$", line):
                stage = [line]
        elif stage:
            stage.append(line)
    return stage


class TestRuntimeImage:
    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_limits_py_ships_with_main_py(self, sidecar: Sidecar) -> None:
        """``main.py`` imports it; an image without it never starts."""
        copies = [line for line in _stage(_instructions(sidecar.dir / "Dockerfile"), "runtime") if "main.py" in line]

        assert len(copies) == 1 and "limits.py" in copies[0].split(), copies

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_no_file_is_handed_to_the_server_uid(self, sidecar: Sidecar) -> None:
        """Root-owned code and model: UID 1000 can read them and rewrite nothing."""
        handing = [
            line
            for line in _instructions(sidecar.dir / "Dockerfile")
            if "--chown" in line or re.search(r"\bchown\b", line)
        ]

        assert handing == []

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_runtime_stage_does_not_carry_uv(self, sidecar: Sidecar) -> None:
        runtime = _stage(_instructions(sidecar.dir / "Dockerfile"), "runtime")
        assert runtime, f"{sidecar.service}: no stage named runtime"
        base = runtime[0].split()[1]

        assert base.startswith("python:"), (
            f"{sidecar.service}: the runtime stage inherits from {base!r}, not the base image"
        )
        assert not [line for line in runtime if "uv" in line.split() or "/uv" in line], runtime
        assert [line for line in runtime if line.startswith("COPY --from=venv /opt/venv ")], runtime

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_runtime_stage_does_not_carry_pip(self, sidecar: Sidecar) -> None:
        """The base image's pip is the last installer left in the runtime: removed as root, before USER.

        The venv (built by uv) never had one; python:3.14-slim ships pip and
        nothing else (no setuptools, no wheel — measured 2026-09-24 on the
        pinned digest). The interpreter is named absolutely: ``python`` on the
        runtime PATH is the venv's, which has no pip module to uninstall with.
        """
        runtime = _stage(_instructions(sidecar.dir / "Dockerfile"), "runtime")
        removals = [
            index
            for index, line in enumerate(runtime)
            if line.startswith("RUN ") and re.search(r"/usr/local/bin/python3 -m pip uninstall (--\S+ )*pip$", line)
        ]
        users = [index for index, line in enumerate(runtime) if line.startswith("USER ")]

        assert len(removals) == 1, f"{sidecar.service}: the runtime stage does not uninstall pip: {runtime}"
        assert not users or removals[0] < users[0]


# --------------------------------------------------------------------------
# the tokenizer: Rust `tokenizers`, never transformers (#1480, #1752)
# --------------------------------------------------------------------------

#: Packages a sidecar's runtime must not reach. ``transformers`` is the only one
#: either service ever used, and only for ``AutoTokenizer``: it carried three HIGH
#: CVEs on the line the reranker was held on (#1480), and in the embedding image
#: (transformers 5.17.0) it tokenized the MiniLM model — whose
#: ``tokenizer_config.json`` names ``BertTokenizer`` over a Unigram
#: ``tokenizer.json`` — through a WordPiece backend that mapped nearly every word
#: to ``<unk>`` (measured 2026-09-25: max |Δ| 0.309 against the reference
#: vectors, #1752). ``tokenizers`` reads ``tokenizer.json`` as published.
_FORBIDDEN_RUNTIME_PACKAGES = frozenset({"transformers"})


def _runtime_closure(lock_file: Path, project: str) -> set[str]:
    """Every package the runtime venv installs: the project's ``dependencies``, transitively.

    Exactly what ``uv sync --locked --no-dev`` in the ``venv`` stage installs:
    ``dev-dependencies`` (the ``build`` group) are left out, extras requested
    on an edge (``uvicorn[standard]``) are followed.
    """

    packages = {entry["name"]: entry for entry in tomllib.loads(lock_file.read_text(encoding="utf-8"))["package"]}
    assert project in packages, f"{lock_file}: no package {project!r}"

    def edges(entry: dict[str, Any], extras: frozenset[str]) -> list[tuple[str, frozenset[str]]]:
        found = [(dep["name"], frozenset(dep.get("extra", ()))) for dep in entry.get("dependencies", [])]
        for extra in extras:
            found += [
                (dep["name"], frozenset(dep.get("extra", ())))
                for dep in entry.get("optional-dependencies", {}).get(extra, [])
            ]
        return found

    seen: set[tuple[str, frozenset[str]]] = set()
    pending = edges(packages[project], frozenset())
    while pending:
        name, extras = pending.pop()
        if (name, extras) in seen:
            continue
        seen.add((name, extras))
        pending += edges(packages[name], extras)
    return {name for name, _ in seen}


class TestRuntimeTokenizer:
    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_the_runtime_lock_does_not_reach_transformers(self, sidecar: Sidecar) -> None:
        pyproject = sidecar.dir / "pyproject.toml"
        project = tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["name"]
        closure = _runtime_closure(sidecar.dir / "uv.lock", project)

        assert "onnxruntime" in closure and "tokenizers" in closure, (
            f"{sidecar.service}: the runtime closure lost onnxruntime/tokenizers — the walk stopped reaching the lock"
        )
        assert closure.isdisjoint(_FORBIDDEN_RUNTIME_PACKAGES), sorted(closure & _FORBIDDEN_RUNTIME_PACKAGES)

    @pytest.mark.parametrize("sidecar", _BY_SERVICE)
    def test_no_module_of_the_service_imports_transformers(self, sidecar: Sidecar) -> None:
        """Every ``*.py`` the service ships, read as AST: an import, not a comment, is what counts."""
        modules = sorted(sidecar.dir.glob("*.py"))
        assert any(module.name == "main.py" for module in modules), modules
        offending = []
        for module in modules:
            for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    names = [node.module]
                else:
                    continue
                offending += [
                    f"{module.name}:{node.lineno} {name}"
                    for name in names
                    if name.split(".")[0] in _FORBIDDEN_RUNTIME_PACKAGES
                ]

        assert offending == []


class TestComposeRuntime:
    """docker-compose.yml runs the reranker the way the chart and the CI probe do."""

    def test_the_reranker_runs_hardened(self) -> None:
        compose = yaml.safe_load((_REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
        service = compose["services"]["reranker-service"]
        tmpfs = service.get("tmpfs") or []
        tmpfs_options = {
            option
            for entry in tmpfs
            if entry.split(":", 1)[0] == "/tmp"
            for option in entry.partition(":")[2].split(",")
        }

        assert service.get("read_only") is True
        assert service.get("cap_drop") == ["ALL"]
        assert "no-new-privileges:true" in (service.get("security_opt") or [])
        assert service.get("user") == "1000:1000"
        assert {"noexec", "nosuid"} <= tmpfs_options, tmpfs
