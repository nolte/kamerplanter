"""Lightweight embedding service using ONNX Runtime — no PyTorch, no optimum."""

import threading
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from feed import build_feed, unfeedable_inputs
from limits import (
    DEFAULT_MODEL,
    LOCK_WAIT_SECONDS,
    MAX_BODY_BYTES,
    MAX_INFERENCE_SECONDS,
    BodySizeLimit,
    Deadline,
    EmbedRequest,
    ServiceUnavailableError,
    cpu_budget,
    inference_slot,
    unavailable_handler,
    validation_error_handler,
)
from pydantic import BaseModel
from tokenization import load_tokenizer

app = FastAPI(title="Kamerplanter Embedding Service")

# THE ORDER OF DEFENCES, OUTSIDE IN (security review of #1725; all in limits.py).
# `BodySizeLimit` refuses a body past `MAX_BODY_BYTES` with 413 before FastAPI
# reads it into memory; `validation_error_handler` answers a body past the
# request bounds with a 422 that names the field and never echoes the input;
# `unavailable_handler` turns `ServiceUnavailableError` — the lock not
# obtained within `LOCK_WAIT_SECONDS`, or the request past its
# `MAX_INFERENCE_SECONDS` deadline — into 503 with `Retry-After`.
app.add_middleware(BodySizeLimit, max_body_bytes=MAX_BODY_BYTES)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(ServiceUnavailableError, unavailable_handler)

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
#
# NEVER `with _inference_lock:` — always `inference_slot(...)`, which waits at
# most `LOCK_WAIT_SECONDS` and then answers 503 busy. A bare `with` waits
# forever while holding one of the AnyIO threadpool's 40 threads.
_inference_lock = threading.Lock()

ONNX_PATH = Path(f"/app/models/onnx/{DEFAULT_MODEL}")


def _mean_pooling(token_embeddings, attention_mask):
    """Mean pooling — take attention mask into account for averaging."""
    input_mask_expanded = np.broadcast_to(np.expand_dims(attention_mask, -1), token_embeddings.shape)
    return np.sum(token_embeddings * input_mask_expanded, axis=1) / np.clip(
        np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None
    )


def _normalize(embeddings):
    """L2-normalize embeddings."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / np.clip(norms, a_min=1e-9, a_max=None)


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    dimensions: int


def _preload() -> None:
    """Load tokenizer and graph, validate them, and only then publish them.

    EVERYTHING IS BUILT IN LOCALS AND PUBLISHED IN ONE STEP, `_ready` LAST.
    This function used to assign the globals as it went, and `/embed` gated on
    `_session`/`_tokenizer` while `/ready` gated on `_ready` — two flags for one
    fact. With the input-name check below, that shape would let `/embed` serve a
    session the check had just rejected while `/ready` said 503 (the race the
    reranker's `_preload` hit in #1480). Now a failure anywhere leaves every
    global untouched, and `/embed` gates on the same `_ready` flag `/ready`
    reports, so the two can never disagree.
    """
    global _session, _tokenizer, _input_names, _ready
    start = time.monotonic()

    # Rust `tokenizers` from `tokenizer.json`, configured to truncate at the
    # model's published `max_seq_length` (sentence_bert_config.json: 512 for
    # the e5 models, 128 for MiniLM — #1774) and pad with the model's own pad
    # token (#1752; the measured parity and the MiniLM defect this fixes are in
    # `load_tokenizer`).
    tokenizer = load_tokenizer(ONNX_PATH)

    # Find the ONNX model file
    onnx_file = ONNX_PATH / "model.onnx"
    if not onnx_file.exists():
        # Some exports use model_optimized.onnx
        onnx_file = ONNX_PATH / "model_optimized.onnx"

    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    # The cgroup's CPU quota, not the host's CPU count (#1725): see
    # `limits.cpu_budget`. One inter-op thread, because the graph runs one
    # text at a time under `_inference_lock` — there is no second operator
    # stream to schedule in parallel.
    opts.intra_op_num_threads = cpu_budget()
    opts.inter_op_num_threads = 1
    session = ort.InferenceSession(str(onnx_file), opts, providers=["CPUExecutionProvider"])

    # Refuse, at load time, a graph that asks for an input this service cannot
    # produce: failing here keeps `/ready` at 503 (which the image's HEALTHCHECK
    # and the CI smoke step both assert) instead of 500-ing every request. The
    # feed is built from these names, never from what the tokenizer happens to
    # return (#1724: e5-small declares `token_type_ids`, its tokenizer omits it).
    input_names = [graph_input.name for graph_input in session.get_inputs()]
    unknown = unfeedable_inputs(input_names)
    if unknown:
        raise ValueError(f"{onnx_file} expects inputs this service cannot feed: {unknown}")

    _tokenizer = tokenizer
    _session = session
    _input_names = input_names
    elapsed = time.monotonic() - start
    print(
        f"ONNX model loaded in {elapsed:.2f}s from {onnx_file} "
        f"(intra-op threads: {opts.intra_op_num_threads}, inter-op threads: {opts.inter_op_num_threads})"
    )
    _ready = True


@app.on_event("startup")
def preload_model() -> None:
    threading.Thread(target=_preload, daemon=True).start()


@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest) -> EmbedResponse:
    # `_ready` is the one flag `_preload` sets after everything else is
    # published and validated; gating on `_session` alone let requests through a
    # half-loaded or rejected model (see `_preload`).
    if not _ready:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "loading"})

    # Nothing to embed. Answered without touching the tokenizer or the graph:
    # when this service still tokenized through transformers, an empty batch
    # raised IndexError (measured with 5.17.0), so `texts: []` used to be a 500.
    # The short-circuit stays — with no vector there is no `dimensions` to read
    # off, so it is 0, as it always was for an empty result.
    if not req.texts:
        return EmbedResponse(embeddings=[], model=req.model, dimensions=0)

    texts = [f"{req.prefix}{t}" for t in req.texts] if req.prefix else req.texts

    # ONE TEXT PER `session.run`, UNDER THE PROCESS-WIDE LOCK (#1725).
    #
    # This used to tokenize every text into one batch padded to the longest and
    # run it once. Measured 2026-09-24 in the e5-large image under the chart's
    # limits (`-m 4g --cpus 2`), 16 texts of more than 512 tokens: the full
    # batch took 47.9 s at 2293 MiB maxrss, batches of 4 took 42.2 s at
    # 1845 MiB, and one text per run took 24.7 s at 1650 MiB — lower memory AND
    # faster, because nothing is spent on padding — with embeddings IDENTICAL
    # to the full batch (max |Δ| 0.0). At 64 such texts the full batch was
    # OOMKilled. The tokenizer truncates at the model's published window
    # (`load_tokenizer`: 512 tokens for e5, 128 for MiniLM since #1774);
    # padding is a no-op for one text. Vectors are collected in input order.
    #
    # The encoded dict deliberately carries NO `token_type_ids`: the reference
    # pipeline omits them, so `build_feed` feeds zeros to a graph that declares
    # the input — exactly what it did before #1752. (The `type_ids` tokenizers
    # returns are all zeros for a single sequence anyway, measured for all four
    # models.)
    #
    # BOUNDED WAIT, BOUNDED HOLD. The lock is waited for at most
    # `LOCK_WAIT_SECONDS` (then 503 busy), and the deadline — started here, so
    # it includes that wait — is checked before every text: a request past
    # `MAX_INFERENCE_SECONDS` is abandoned with 503 timeout and the lock
    # released, instead of computing on for a caller that timed out long ago.
    deadline = Deadline(MAX_INFERENCE_SECONDS)
    vectors = []
    with inference_slot(_inference_lock, wait_seconds=LOCK_WAIT_SECONDS):
        for text in texts:
            deadline.check()
            encoding = _tokenizer.encode(text)
            encoded = {
                "input_ids": np.asarray([encoding.ids], dtype=np.int64),
                "attention_mask": np.asarray([encoding.attention_mask], dtype=np.int64),
            }
            outputs = _session.run(None, build_feed(_input_names, encoded))
            vectors.append(_normalize(_mean_pooling(outputs[0], encoded["attention_mask"]))[0])

    return EmbedResponse(
        embeddings=[vector.tolist() for vector in vectors],
        model=req.model,
        dimensions=int(vectors[0].shape[0]),
    )


# `/health` AND `/ready` ARE `async def`, AND THAT IS THE POINT. A sync route
# runs on the AnyIO threadpool (40 threads), which is exactly where requests
# waiting on `_inference_lock` sit; with enough of them queued, a probe would
# wait for a free thread past its timeout, and a failed liveness probe restarts
# a pod that is merely busy — killing the inference everyone queued behind.
# These two only read module flags, so they run on the event loop and answer
# regardless of the threadpool.
@app.get("/health")
async def health() -> dict:
    return {"status": "ok" if _ready else "loading", "model": DEFAULT_MODEL, "ready": _ready}


@app.get("/ready")
async def ready() -> dict:
    if not _ready:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "loading"})
    return {"status": "ok"}
