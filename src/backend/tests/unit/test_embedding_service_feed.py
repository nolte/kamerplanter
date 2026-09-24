"""#1724 — the embedding sidecar feeds exactly the inputs its ONNX graph declares.

Measured 2026-09-24 on the develop image ``--target e5-small``: ``/ready`` 200,
every ``POST /embed`` a 500 — the graph declares ``token_type_ids``, the
XLM-RoBERTa tokenizer never returns it, and the feed was built from the
tokenizer's output. ``docker/embedding-service/feed.py`` now builds the feed
from the graph's input names; it imports only numpy, so it is loaded here by
path and exercised without onnxruntime, transformers or a model.

``main.py`` itself cannot be imported here (onnxruntime and transformers are not
backend dependencies), so the wiring — ``_preload`` refuses unfeedable inputs
and publishes ``_ready`` last, ``/embed`` gates on ``_ready`` and runs the feed
``build_feed`` returns — is asserted on its AST.

Traces to #1724 (no TC-ID: sidecar internals are not a user-facing case).
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_SERVICE = _REPO_ROOT / "docker" / "embedding-service"


def _load_feed() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_embedding_service_feed", _SERVICE / "feed.py")
    assert spec is not None and spec.loader is not None, "docker/embedding-service/feed.py is not loadable"
    module = importlib.util.module_from_spec(spec)
    sys.modules["_embedding_service_feed"] = module
    spec.loader.exec_module(module)
    return module


feed = _load_feed()

_IDS = np.array([[0, 5, 7, 2], [0, 9, 2, 1]], dtype=np.int32)
_MASK = np.array([[1, 1, 1, 1], [1, 1, 1, 0]], dtype=np.int32)


class TestBuildFeed:
    def test_a_declared_token_type_ids_the_tokenizer_omits_is_zeros(self) -> None:
        """The e5-small case: graph declares three inputs, tokenizer returns two."""
        result = feed.build_feed(
            ["input_ids", "attention_mask", "token_type_ids"],
            {"input_ids": _IDS, "attention_mask": _MASK},
        )
        assert list(result) == ["input_ids", "attention_mask", "token_type_ids"]
        assert result["token_type_ids"].shape == _IDS.shape
        assert not result["token_type_ids"].any()
        assert all(array.dtype == np.int64 for array in result.values())
        np.testing.assert_array_equal(result["input_ids"], _IDS)
        np.testing.assert_array_equal(result["attention_mask"], _MASK)

    def test_the_tokenizers_token_type_ids_are_used_when_present(self) -> None:
        """The MiniLM (BERT tokenizer) case: the tokenizer's own value wins."""
        types = np.array([[0, 0, 1, 1], [0, 1, 1, 1]], dtype=np.int32)
        result = feed.build_feed(
            ["input_ids", "attention_mask", "token_type_ids"],
            {"input_ids": _IDS, "attention_mask": _MASK, "token_type_ids": types},
        )
        np.testing.assert_array_equal(result["token_type_ids"], types)

    def test_an_input_the_graph_does_not_declare_is_not_fed(self) -> None:
        """The e5-base case: onnxruntime rejects an undeclared name as INVALID_ARGUMENT."""
        result = feed.build_feed(
            ["input_ids", "attention_mask"],
            {"input_ids": _IDS, "attention_mask": _MASK, "token_type_ids": np.zeros_like(_IDS)},
        )
        assert list(result) == ["input_ids", "attention_mask"]

    def test_an_unfeedable_input_is_refused(self) -> None:
        with pytest.raises(ValueError, match="position_ids"):
            feed.build_feed(["input_ids", "position_ids"], {"input_ids": _IDS, "attention_mask": _MASK})


class TestUnfeedableInputs:
    def test_the_three_producible_inputs_are_feedable(self) -> None:
        assert feed.unfeedable_inputs(["input_ids", "attention_mask", "token_type_ids"]) == []

    def test_unknown_inputs_are_named_sorted(self) -> None:
        assert feed.unfeedable_inputs(["pixel_values", "input_ids", "position_ids"]) == [
            "pixel_values",
            "position_ids",
        ]


def _function(tree: ast.Module, name: str) -> ast.FunctionDef:
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    assert found, f"main.py defines no top-level `{name}`"
    return found[0]


def _called_names(node: ast.AST) -> set[str]:
    return {
        call.func.id if isinstance(call.func, ast.Name) else getattr(call.func, "attr", "")
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
    }


class TestMainWiring:
    """``main.py`` uses ``feed`` the way the module above is tested."""

    _TREE = ast.parse((_SERVICE / "main.py").read_text(encoding="utf-8"))

    def test_preload_refuses_unfeedable_inputs(self) -> None:
        assert "unfeedable_inputs" in _called_names(_function(self._TREE, "_preload"))

    def test_preload_publishes_ready_last(self) -> None:
        """Every global is assigned before ``_ready``; nothing after it."""
        body = _function(self._TREE, "_preload").body
        assigned = [
            target.id
            for statement in body
            if isinstance(statement, ast.Assign)
            for target in statement.targets
            if isinstance(target, ast.Name) and target.id.startswith("_")
        ]
        assert assigned[-1] == "_ready", assigned
        assert {"_session", "_tokenizer", "_input_names"} <= set(assigned[:-1]), assigned

    def test_embed_gates_on_ready_and_runs_the_built_feed(self) -> None:
        embed = _function(self._TREE, "embed")
        gate = embed.body[0]
        assert isinstance(gate, ast.If), "the first statement of `embed` is not its readiness gate"
        assert ast.unparse(gate.test) == "not _ready", ast.unparse(gate.test)
        runs = [
            call
            for call in ast.walk(embed)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "run"
        ]
        assert len(runs) == 1, "`embed` must run the session exactly once"
        fed = runs[0].args[1]
        assert isinstance(fed, ast.Call) and ast.unparse(fed.func) == "build_feed", ast.unparse(fed)
