"""Cross-encoder reranker service using ONNX Runtime — no PyTorch dependency."""

import json
import os
import threading
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI
from pydantic import BaseModel, Field
from tokenizers import Tokenizer

app = FastAPI(title="Kamerplanter Reranker Service")

_session = None
_tokenizer = None
_input_names: list[str] = []
_ready = False

DEFAULT_MODEL = os.environ.get("RERANKER_MODEL", "bge-reranker-v2-m3")
ONNX_PATH = Path(f"/app/models/onnx/{DEFAULT_MODEL}")

# Both cross-encoders were trained on 512-token pairs; this is the value the
# service passed as `max_length` when it still tokenized through transformers.
MAX_LENGTH = 512

# How each graph input is read off a `tokenizers.Encoding`. The graphs do NOT
# share one signature: the bge (XLM-RoBERTa) export takes `input_ids` and
# `attention_mask`, the MiniLM (BERT) one additionally `token_type_ids`. The
# feed is therefore built from `_session.get_inputs()`, never from what the
# tokenizer happens to produce — feeding a name the graph does not declare is an
# `INVALID_ARGUMENT` from onnxruntime.
_ENCODING_FIELDS = {
    "input_ids": "ids",
    "attention_mask": "attention_mask",
    "token_type_ids": "type_ids",
}


class RerankRequest(BaseModel):
    query: str
    documents: list[str]
    top_k: int = Field(default=5, ge=1, le=50)


class RerankResult(BaseModel):
    index: int
    score: float
    text: str


class RerankResponse(BaseModel):
    results: list[RerankResult]
    model: str


def _sigmoid(x):
    """Apply sigmoid activation to convert logits to probabilities."""
    return 1.0 / (1.0 + np.exp(-x))


def _pad_token(model_dir: Path) -> str:
    """Read the padding token the model was published with.

    `tokenizer_config.json` spells it either as a plain string or as an
    AddedToken dict (`{"content": "<pad>", ...}`), depending on which
    transformers version wrote the file. The two revisions pinned in the
    Dockerfile both use the plain string (`<pad>` for bge, `[PAD]` for MiniLM);
    the dict form is read so that a re-pin to a file written the other way does
    not break startup. A missing pad token is an error, not a default: the two
    vocabularies do not even agree on its spelling, and a guessed token that
    happens to be a real word piece would shift every score without failing.
    """
    config = json.loads((model_dir / "tokenizer_config.json").read_text(encoding="utf-8"))
    pad = config.get("pad_token")
    if isinstance(pad, dict):
        pad = pad.get("content")
    if not isinstance(pad, str) or not pad:
        raise ValueError(f"{model_dir / 'tokenizer_config.json'} declares no pad_token")
    return pad


def _load_tokenizer(model_dir: Path) -> Tokenizer:
    """Load the fast tokenizer straight from `tokenizer.json` (#1480).

    THIS REPLACES `transformers.AutoTokenizer`, AND THE CONFIGURATION BELOW IS
    WHAT MAKES IT A REPLACEMENT RATHER THAN AN APPROXIMATION. AutoTokenizer's
    fast path is this very Rust tokenizer; what transformers added on top was the
    call-time `padding=True, truncation=True, max_length=512`. Those are set
    here once: truncation to MAX_LENGTH (default strategy `longest_first`, the
    same as transformers' `truncation=True` for a pair) and padding to the
    longest sequence in the batch with the model's own pad token and id.
    Measured 2026-09-24 for both models, against AutoTokenizer from
    transformers 4.57.6: `input_ids`, `attention_mask` and `token_type_ids`
    identical for a normal batch, a >512-token document, a ragged batch and a
    single pair.

    Dropping transformers is the point: it was the only reason the image
    carried a package with three HIGH CVEs open against the line it was held on.
    """
    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    pad = _pad_token(model_dir)
    pad_id = tokenizer.token_to_id(pad)
    if pad_id is None:
        raise ValueError(f"pad_token {pad!r} is not in the vocabulary of {model_dir / 'tokenizer.json'}")
    tokenizer.enable_truncation(max_length=MAX_LENGTH)
    tokenizer.enable_padding(pad_id=pad_id, pad_token=pad)
    return tokenizer


def _preload() -> None:
    """Load tokenizer and graph, validate them, and only then publish them.

    EVERYTHING IS BUILT IN LOCALS AND PUBLISHED IN ONE STEP, `_ready` LAST. The
    first version of this function assigned `_session` straight away and the
    input names two statements later, while `/rerank` gated on `_session`: a
    request in that window built an empty feed and 500'd, and when the
    input-name check below raised, `_session` stayed set with `_ready` False —
    `/ready` said 503 while `/rerank` served a feed that could not work. Now a
    failure anywhere leaves every global untouched, and `/rerank` gates on the
    same `_ready` flag `/ready` reports, so the two can never disagree.
    """
    global _session, _tokenizer, _input_names, _ready
    start = time.monotonic()

    tokenizer = _load_tokenizer(ONNX_PATH)

    onnx_file = ONNX_PATH / "model.onnx"
    if not onnx_file.exists():
        onnx_file = ONNX_PATH / "model_optimized.onnx"

    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opts.intra_op_num_threads = os.cpu_count() or 2
    session = ort.InferenceSession(str(onnx_file), opts, providers=["CPUExecutionProvider"])

    # Refuse, at load time, a graph that asks for an input the tokenizer cannot
    # produce: failing here keeps `/ready` at 503 (which the image's HEALTHCHECK
    # and the CI smoke step both assert) instead of 500-ing every request.
    input_names = [graph_input.name for graph_input in session.get_inputs()]
    unknown = sorted(set(input_names) - _ENCODING_FIELDS.keys())
    if unknown:
        raise ValueError(f"{onnx_file} expects inputs this service cannot feed: {unknown}")

    _tokenizer = tokenizer
    _session = session
    _input_names = input_names
    elapsed = time.monotonic() - start
    print(f"ONNX reranker model loaded in {elapsed:.2f}s from {onnx_file}")
    _ready = True


@app.on_event("startup")
def preload_model() -> None:
    threading.Thread(target=_preload, daemon=True).start()


@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest) -> RerankResponse:
    # `_ready` is the one flag `_preload` sets after everything else is
    # published and validated; gating on `_session` alone let requests through a
    # half-loaded or rejected model (see `_preload`).
    if not _ready:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "loading"})

    # Nothing to rank. Answered without touching the tokenizer or the session:
    # an empty batch encodes to a 1-D empty array the graph rejects, so this
    # used to be a 500 — and was one on transformers too (`AutoTokenizer([])`
    # raises IndexError, measured with 4.57.6).
    if not req.documents:
        return RerankResponse(results=[], model=DEFAULT_MODEL)

    # Cross-encoder: encode query-document pairs. Padding to the batch's longest
    # pair is configured on the tokenizer, so every encoding has the same length
    # and the rows stack into a rectangular [N, L] tensor.
    encodings = _tokenizer.encode_batch([(req.query, doc) for doc in req.documents])

    inputs = {
        name: np.asarray([getattr(encoding, _ENCODING_FIELDS[name]) for encoding in encodings], dtype=np.int64)
        for name in _input_names
    }

    outputs = _session.run(None, inputs)
    logits = outputs[0]

    # Extract relevance scores — handle both [N, 1] and [N] shapes
    if logits.ndim == 2:
        scores = logits[:, 0]
    else:
        scores = logits

    scores = _sigmoid(scores)

    # Rank by score descending, take top_k
    ranked_indices = np.argsort(scores)[::-1][: req.top_k]

    results = [
        RerankResult(
            index=int(idx),
            score=float(scores[idx]),
            text=req.documents[idx],
        )
        for idx in ranked_indices
    ]

    return RerankResponse(results=results, model=DEFAULT_MODEL)


@app.get("/health")
def health() -> dict:
    return {"status": "ok" if _ready else "loading", "model": DEFAULT_MODEL, "ready": _ready}


@app.get("/ready")
def ready() -> dict:
    if not _ready:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "loading"})
    return {"status": "ok"}
