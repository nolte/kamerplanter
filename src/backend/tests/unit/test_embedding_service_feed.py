"""#1724 — the embedding sidecar feeds exactly the inputs its ONNX graph declares.

Measured 2026-09-24 on the develop image ``--target e5-small``: ``/ready`` 200,
every ``POST /embed`` a 500 — the graph declares ``token_type_ids``, the
XLM-RoBERTa tokenizer never returns it, and the feed was built from the
tokenizer's output. ``docker/embedding-service/feed.py`` now builds the feed
from the graph's input names; it imports only numpy, so it is loaded here by
path and exercised without onnxruntime, tokenizers or a model.

#1752 — the tokenizer is Rust ``tokenizers`` read from ``tokenizer.json``, no
longer transformers. ``docker/embedding-service/tokenization.py`` holds the
pad-token lookup and the truncation/padding configuration; ``tokenizers`` is not
a backend dependency, so the module is loaded here against a stand-in
``tokenizers`` module that records how it is configured.

``main.py`` itself cannot be imported here (onnxruntime and tokenizers are not
backend dependencies), so the wiring — ``_preload`` refuses unfeedable inputs
and publishes ``_ready`` last, ``/embed`` gates on ``_ready`` and runs the feed
``build_feed`` returns — is asserted on its AST.

Traces to #1724 and #1752 (no TC-ID: sidecar internals are not a user-facing case).
"""

from __future__ import annotations

import ast
import importlib.util
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

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

    def test_preload_loads_the_tokenizer_from_tokenization(self) -> None:
        """#1752: ``tokenization.load_tokenizer``, not ``AutoTokenizer.from_pretrained``."""
        assert "load_tokenizer" in _called_names(_function(self._TREE, "_preload"))
        imported = {
            node.module if isinstance(node, ast.ImportFrom) else alias.name
            for node in ast.walk(self._TREE)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for alias in node.names
        }
        assert "transformers" not in imported, imported

    def test_embed_passes_no_token_type_ids(self) -> None:
        """The reference pipeline omits them, so ``build_feed`` feeds zeros as before #1752."""
        keys = {
            key.value
            for node in ast.walk(_function(self._TREE, "embed"))
            if isinstance(node, ast.Dict)
            for key in node.keys
            if isinstance(key, ast.Constant)
        }
        assert keys >= {"input_ids", "attention_mask"}, keys
        assert "token_type_ids" not in keys, keys

    def test_every_local_module_main_imports_ships_in_the_image(self) -> None:
        """An image without ``tokenization.py`` (or ``feed.py``, ``limits.py``) never starts."""
        local = {
            node.module
            for node in self._TREE.body
            if isinstance(node, ast.ImportFrom) and node.module and (_SERVICE / f"{node.module}.py").is_file()
        }
        copies = [
            line.split()
            for line in (_SERVICE / "Dockerfile").read_text(encoding="utf-8").splitlines()
            if line.startswith("COPY ") and "main.py" in line.split()
        ]
        assert len(copies) == 1, copies
        assert {"tokenization", "feed", "limits"} <= local, local
        assert {f"{module}.py" for module in local} <= set(copies[0]), copies[0]


# --------------------------------------------------------------------------
# tokenization.py (#1752)
# --------------------------------------------------------------------------


class _FakeTokenizer:
    """Stand-in for ``tokenizers.Tokenizer``: a vocabulary and the calls made on it.

    ``token_to_id`` returns ``None`` for a token outside the vocabulary, as the
    real one does.
    """

    VOCAB = {"<s>": 0, "<pad>": 1, "</s>": 2, "<unk>": 3}

    def __init__(self, path: str) -> None:
        self.path = path
        self.truncation: dict[str, Any] | None = None
        self.padding: dict[str, Any] | None = None

    @classmethod
    def from_file(cls, path: str) -> _FakeTokenizer:
        return cls(path)

    def token_to_id(self, token: str) -> int | None:
        return self.VOCAB.get(token)

    def enable_truncation(self, **kwargs: Any) -> None:
        self.truncation = kwargs

    def enable_padding(self, **kwargs: Any) -> None:
        self.padding = kwargs


@pytest.fixture
def tokenization(monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    """``tokenization.py`` loaded by path against the stand-in ``tokenizers``."""
    fake = ModuleType("tokenizers")
    fake.Tokenizer = _FakeTokenizer  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tokenizers", fake)
    spec = importlib.util.spec_from_file_location("_embedding_service_tokenization", _SERVICE / "tokenization.py")
    assert spec is not None and spec.loader is not None, "docker/embedding-service/tokenization.py is not loadable"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    yield module


def _model_dir(tmp_path: Path, config: dict[str, Any], window: Any = 512) -> Path:
    """A model directory with *config* as ``tokenizer_config.json``.

    ``window`` is written as ``sentence_bert_config.json``'s ``max_seq_length``
    (#1774) — the value every pinned e5 revision publishes by default.
    """
    (tmp_path / "tokenizer_config.json").write_text(json.dumps(config), encoding="utf-8")
    _write_sentence_bert_config(tmp_path, {"max_seq_length": window, "do_lower_case": False})
    return tmp_path


def _write_sentence_bert_config(model_dir: Path, config: Any) -> None:
    (model_dir / "sentence_bert_config.json").write_text(json.dumps(config), encoding="utf-8")


class TestPadToken:
    def test_a_plain_string_is_read(self, tokenization: ModuleType, tmp_path: Path) -> None:
        """The spelling all four pinned revisions use."""
        assert tokenization.pad_token(_model_dir(tmp_path, {"pad_token": "<pad>"})) == "<pad>"

    def test_the_added_token_dict_form_is_read(self, tokenization: ModuleType, tmp_path: Path) -> None:
        config = {"pad_token": {"content": "<pad>", "lstrip": False, "normalized": True, "special": True}}
        assert tokenization.pad_token(_model_dir(tmp_path, config)) == "<pad>"

    @pytest.mark.parametrize(
        "config",
        [
            pytest.param({}, id="missing"),
            pytest.param({"pad_token": None}, id="null"),
            pytest.param({"pad_token": ""}, id="empty"),
            pytest.param({"pad_token": {"content": ""}}, id="empty-dict"),
            pytest.param({"pad_token": {"lstrip": False}}, id="dict-without-content"),
        ],
    )
    def test_no_usable_pad_token_fails_loud(
        self, tokenization: ModuleType, tmp_path: Path, config: dict[str, Any]
    ) -> None:
        """Never a default: a guessed token that is a real word piece shifts every vector."""
        with pytest.raises(ValueError, match="declares no pad_token"):
            tokenization.pad_token(_model_dir(tmp_path, config))


class TestLoadTokenizer:
    def test_truncates_to_512_and_pads_with_the_models_pad_token(
        self, tokenization: ModuleType, tmp_path: Path
    ) -> None:
        """An e5 model: its ``sentence_bert_config.json`` says 512, and ``padding=True``."""
        tokenizer = tokenization.load_tokenizer(_model_dir(tmp_path, {"pad_token": "<pad>"}, window=512))

        assert tokenizer.path == str(tmp_path / "tokenizer.json")
        assert tokenizer.truncation == {"max_length": 512}
        assert tokenizer.padding == {"pad_id": 1, "pad_token": "<pad>"}

    def test_truncates_at_the_window_the_model_publishes(self, tokenization: ModuleType, tmp_path: Path) -> None:
        """#1774: MiniLM publishes 128 — the service must not feed it 512 tokens."""
        tokenizer = tokenization.load_tokenizer(_model_dir(tmp_path, {"pad_token": "<pad>"}, window=128))

        assert tokenizer.truncation == {"max_length": 128}

    def test_a_pad_token_outside_the_vocabulary_fails_loud(self, tokenization: ModuleType, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match=r"'\[PAD\]' is not in the vocabulary"):
            tokenization.load_tokenizer(_model_dir(tmp_path, {"pad_token": "[PAD]"}))

    def test_a_missing_pad_token_fails_loud(self, tokenization: ModuleType, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="declares no pad_token"):
            tokenization.load_tokenizer(_model_dir(tmp_path, {}))


class TestMaxSeqLength:
    """#1774 — the truncation window is the model's published ``max_seq_length``, never a default.

    Until #1774 every model was truncated at a hard-coded 512; MiniLM publishes
    128 (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2,
    ``sentence_bert_config.json``). A missing or unusable value fails the load
    rather than falling back: a guessed window is silently different vectors.
    """

    @pytest.mark.parametrize("window", [128, 512])
    def test_the_published_value_is_read(self, tokenization: ModuleType, tmp_path: Path, window: int) -> None:
        assert tokenization.max_seq_length(_model_dir(tmp_path, {"pad_token": "<pad>"}, window=window)) == window

    def test_a_missing_file_fails_loud(self, tokenization: ModuleType, tmp_path: Path) -> None:
        model_dir = _model_dir(tmp_path, {"pad_token": "<pad>"})
        (model_dir / "sentence_bert_config.json").unlink()
        with pytest.raises(ValueError, match="sentence_bert_config.json"):
            tokenization.load_tokenizer(model_dir)

    def test_a_file_that_is_not_json_fails_loud(self, tokenization: ModuleType, tmp_path: Path) -> None:
        model_dir = _model_dir(tmp_path, {"pad_token": "<pad>"})
        (model_dir / "sentence_bert_config.json").write_text("max_seq_length: 128\n", encoding="utf-8")
        with pytest.raises(ValueError, match="sentence_bert_config.json"):
            tokenization.load_tokenizer(model_dir)

    @pytest.mark.parametrize(
        "config",
        [
            pytest.param({"do_lower_case": False}, id="missing-key"),
            pytest.param({"max_seq_length": 0}, id="zero"),
            pytest.param({"max_seq_length": -1}, id="negative"),
            pytest.param({"max_seq_length": True}, id="bool"),
            pytest.param({"max_seq_length": "128"}, id="string"),
            pytest.param({"max_seq_length": 128.0}, id="float"),
            pytest.param({"max_seq_length": None}, id="null"),
            pytest.param([128], id="not-an-object"),
        ],
    )
    def test_an_unusable_value_fails_loud(self, tokenization: ModuleType, tmp_path: Path, config: Any) -> None:
        model_dir = _model_dir(tmp_path, {"pad_token": "<pad>"})
        _write_sentence_bert_config(model_dir, config)
        with pytest.raises(ValueError, match="sentence_bert_config.json"):
            tokenization.load_tokenizer(model_dir)
