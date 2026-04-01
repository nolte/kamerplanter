"""Lightweight embedding service using ONNX Runtime — no PyTorch, no optimum."""

import os
import threading
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer

app = FastAPI(title="Kamerplanter Embedding Service")

_session = None
_tokenizer = None
_ready = False

DEFAULT_MODEL = os.environ.get("EMBEDDING_MODEL", "multilingual-e5-base")
ONNX_PATH = Path(f"/app/models/onnx/{DEFAULT_MODEL}")


def _mean_pooling(token_embeddings, attention_mask):
    """Mean pooling — take attention mask into account for averaging."""
    input_mask_expanded = np.broadcast_to(
        np.expand_dims(attention_mask, -1), token_embeddings.shape
    )
    return np.sum(token_embeddings * input_mask_expanded, axis=1) / np.clip(
        np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None
    )


def _normalize(embeddings):
    """L2-normalize embeddings."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / np.clip(norms, a_min=1e-9, a_max=None)


class EmbedRequest(BaseModel):
    texts: list[str]
    model: str = DEFAULT_MODEL
    prefix: str = ""


class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    model: str
    dimensions: int


def _preload() -> None:
    global _session, _tokenizer, _ready
    start = time.monotonic()

    _tokenizer = AutoTokenizer.from_pretrained(str(ONNX_PATH))

    # Find the ONNX model file
    onnx_file = ONNX_PATH / "model.onnx"
    if not onnx_file.exists():
        # Some exports use model_optimized.onnx
        onnx_file = ONNX_PATH / "model_optimized.onnx"

    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opts.intra_op_num_threads = os.cpu_count() or 2
    _session = ort.InferenceSession(str(onnx_file), opts, providers=["CPUExecutionProvider"])

    elapsed = time.monotonic() - start
    print(f"ONNX model loaded in {elapsed:.2f}s from {onnx_file}")
    _ready = True


@app.on_event("startup")
def preload_model() -> None:
    threading.Thread(target=_preload, daemon=True).start()


@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest) -> EmbedResponse:
    if _session is None or _tokenizer is None:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "loading"})

    texts = [f"{req.prefix}{t}" for t in req.texts] if req.prefix else req.texts

    encoded = _tokenizer(
        texts, padding=True, truncation=True, max_length=512, return_tensors="np"
    )

    inputs = {
        "input_ids": encoded["input_ids"].astype(np.int64),
        "attention_mask": encoded["attention_mask"].astype(np.int64),
    }
    if "token_type_ids" in encoded:
        inputs["token_type_ids"] = encoded["token_type_ids"].astype(np.int64)

    outputs = _session.run(None, inputs)
    embeddings = _mean_pooling(outputs[0], encoded["attention_mask"])
    embeddings = _normalize(embeddings)

    return EmbedResponse(
        embeddings=[e.tolist() for e in embeddings],
        model=req.model,
        dimensions=int(embeddings.shape[1]) if len(embeddings) > 0 else 0,
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok" if _ready else "loading", "model": DEFAULT_MODEL, "ready": _ready}


@app.get("/ready")
def ready() -> dict:
    if not _ready:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "loading"})
    return {"status": "ok"}
