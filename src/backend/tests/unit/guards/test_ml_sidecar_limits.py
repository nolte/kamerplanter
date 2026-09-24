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

Traces to #1725 (no TC-ID: sidecar internals are not a user-facing case).
"""

from __future__ import annotations

import ast
import functools
import importlib.util
import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml
from fastapi import FastAPI
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
)

_SIDECARS = (_RERANKER, _EMBEDDING)
_BOUNDS = [
    pytest.param(sidecar, bound, id=f"{sidecar.service}:{bound.constant}")
    for sidecar in _SIDECARS
    for bound in sidecar.bounds
]
_BY_SERVICE = [pytest.param(sidecar, id=sidecar.service) for sidecar in _SIDECARS]


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
        names = ("cpu_budget", "_cgroup_cpu_limit", "_ceil_quota", "_read_fields", "_available_cpus")

        def functions(sidecar: Sidecar) -> dict[str, str]:
            tree = _parse(sidecar.dir / "limits.py")
            return {
                node.name: ast.dump(node)
                for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name in names
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
        locks = {
            target.id
            for node in tree.body
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
            if ast.unparse(node.value.func) == "threading.Lock"
            for target in node.targets
            if isinstance(target, ast.Name)
        }
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
        guarded = [
            n
            for n in chain
            if isinstance(n, ast.With) and any(ast.unparse(item.context_expr) in locks for item in n.items)
        ]
        assert loops, f"{sidecar.service}: session.run is not inside a per-input loop"
        assert guarded, f"{sidecar.service}: session.run is not inside `with {next(iter(locks))}:`"
        assert chain.index(loops[0]) < chain.index(guarded[0]), "the lock must enclose the whole loop"


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
