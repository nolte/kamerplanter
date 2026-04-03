"""Cross-encoder reranker service using ONNX Runtime — no PyTorch dependency."""

import os
import threading
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI
from pydantic import BaseModel, Field
from transformers import AutoTokenizer

app = FastAPI(title="Kamerplanter Reranker Service")

_session = None
_tokenizer = None
_ready = False

DEFAULT_MODEL = os.environ.get("RERANKER_MODEL", "bge-reranker-v2-m3")
ONNX_PATH = Path(f"/app/models/onnx/{DEFAULT_MODEL}")


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


def _preload() -> None:
    global _session, _tokenizer, _ready
    start = time.monotonic()

    _tokenizer = AutoTokenizer.from_pretrained(str(ONNX_PATH))

    onnx_file = ONNX_PATH / "model.onnx"
    if not onnx_file.exists():
        onnx_file = ONNX_PATH / "model_optimized.onnx"

    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opts.intra_op_num_threads = os.cpu_count() or 2
    _session = ort.InferenceSession(str(onnx_file), opts, providers=["CPUExecutionProvider"])

    elapsed = time.monotonic() - start
    print(f"ONNX reranker model loaded in {elapsed:.2f}s from {onnx_file}")
    _ready = True


@app.on_event("startup")
def preload_model() -> None:
    threading.Thread(target=_preload, daemon=True).start()


@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest) -> RerankResponse:
    if _session is None or _tokenizer is None:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "loading"})

    # Cross-encoder: encode query-document pairs
    pairs = [[req.query, doc] for doc in req.documents]

    encoded = _tokenizer(
        pairs,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="np",
    )

    inputs = {
        "input_ids": encoded["input_ids"].astype(np.int64),
        "attention_mask": encoded["attention_mask"].astype(np.int64),
    }
    if "token_type_ids" in encoded:
        inputs["token_type_ids"] = encoded["token_type_ids"].astype(np.int64)

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
