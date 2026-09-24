"""Cross-encoder reranker service using ONNX Runtime — no PyTorch dependency."""

import json
import os
import threading
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI
from limits import RerankRequest, cpu_budget
from pydantic import BaseModel
from tokenizers import Tokenizer

app = FastAPI(title="Kamerplanter Reranker Service")

_session = None
_tokenizer = None
_input_names: list[str] = []
_ready = False

# ONE INFERENCE AT A TIME, PROCESS-WIDE (#1725). The route is a sync `def`, so
# FastAPI runs each request on its own threadpool thread, and every one of them
# used to start its own `session.run` — N concurrent requests held N sets of
# activations at once. The lock makes the memory of the process the memory of
# ONE request, and the request bounds in limits.py make that finite. The graph
# already uses every CPU the cgroup grants (`cpu_budget`), so running two
# requests side by side bought no throughput, only memory.
_inference_lock = threading.Lock()

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
    # The cgroup's CPU quota, not the host's CPU count (#1725): see
    # `limits.cpu_budget`. One inter-op thread, because the graph runs one
    # pair at a time under `_inference_lock` — there is no second operator
    # stream to schedule in parallel.
    opts.intra_op_num_threads = cpu_budget()
    opts.inter_op_num_threads = 1
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
    print(
        f"ONNX reranker model loaded in {elapsed:.2f}s from {onnx_file} "
        f"(intra-op threads: {opts.intra_op_num_threads}, inter-op threads: {opts.inter_op_num_threads})"
    )
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

    # ONE PAIR PER `session.run`, UNDER THE PROCESS-WIDE LOCK (#1725).
    #
    # This used to tokenize every pair into one [N, L] batch padded to the
    # longest pair and run it once. Measured 2026-09-24 in the bge image under
    # the chart's limits (`-m 4g --cpus 2`), 20 documents of more than 512
    # tokens: the full batch took 56.5 s at 3001 MiB maxrss, batches of 4 took
    # 54.8 s at 1852 MiB, and one pair per run took 31.9 s at 1595 MiB — lower
    # memory AND faster, because nothing is spent on padding — with logits
    # IDENTICAL to the full batch (max |Δ| 0.0, identical ranking). At 100 such
    # documents the full batch was OOMKilled. The tokenizer configuration is
    # unchanged (truncation to MAX_LENGTH); padding is a no-op for one pair.
    # Scores are collected in input order, so `index` still names the request's
    # document.
    # A list of the graph's own scalars, so the array below keeps the graph's
    # output dtype (float32), exactly as the batched `logits[:, 0]` did.
    pair_logits = []
    with _inference_lock:
        for document in req.documents:
            encoding = _tokenizer.encode_batch([(req.query, document)])[0]
            inputs = {
                name: np.asarray([getattr(encoding, _ENCODING_FIELDS[name])], dtype=np.int64) for name in _input_names
            }
            logits = _session.run(None, inputs)[0]
            # Extract the relevance score — handle both [1, 1] and [1] shapes
            pair_logits.append(logits[0, 0] if logits.ndim == 2 else logits[0])

    scores = _sigmoid(np.asarray(pair_logits))

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
