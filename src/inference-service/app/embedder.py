"""DINOv2 ONNX embedder -- loads model.onnx into an ONNX Runtime session.

The model is loaded in a background thread at startup (non-blocking) so the
HTTP server can answer liveness probes while the (potentially large) model
file is being mapped. Until the load finishes, ``is_ready()`` returns False and
embedding calls raise ``ModelNotReadyError``.
"""

import os
import threading
import time
from pathlib import Path

import numpy as np
import structlog

from app.preprocessing import preprocess

logger = structlog.get_logger(__name__)

_MODEL_FILENAME = "model.onnx"


class ModelNotReadyError(RuntimeError):
    """Raised when an embedding is requested before the model has loaded."""


def _l2_normalize(vector: np.ndarray) -> np.ndarray:
    """L2-normalise a 1-D embedding so cosine similarity == dot product."""
    norm = float(np.linalg.norm(vector))
    if norm < 1e-12:
        return vector.astype(np.float32)
    return (vector / norm).astype(np.float32)


class Embedder:
    """Wraps an ONNX Runtime session for DINOv2 embedding extraction."""

    def __init__(self, model_path: str, input_size: int, expected_dim: int) -> None:
        self._model_path = Path(model_path)
        self._input_size = input_size
        self._expected_dim = expected_dim
        self._session = None
        self._input_name: str | None = None
        self._ready = False
        self._load_error: str | None = None
        self._lock = threading.Lock()

    # -- lifecycle ---------------------------------------------------------

    def start_load(self) -> None:
        """Kick off the model load in a daemon thread (non-blocking)."""
        threading.Thread(target=self._load, name="dinov2-load", daemon=True).start()

    def _load(self) -> None:
        import onnxruntime as ort

        start = time.monotonic()
        onnx_file = self._model_path / _MODEL_FILENAME
        if not onnx_file.exists():
            self._load_error = f"model file not found: {onnx_file}"
            logger.error("model_load_failed", reason=self._load_error)
            return

        try:
            opts = ort.SessionOptions()
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            opts.intra_op_num_threads = os.cpu_count() or 2
            session = ort.InferenceSession(str(onnx_file), opts, providers=["CPUExecutionProvider"])
        except Exception as exc:  # noqa: BLE001 -- surface any ORT load failure
            self._load_error = str(exc)
            logger.error("model_load_failed", reason=self._load_error)
            return

        with self._lock:
            self._session = session
            self._input_name = session.get_inputs()[0].name
            self._ready = True
            self._load_error = None

        elapsed = time.monotonic() - start
        logger.info("model_loaded", file=str(onnx_file), seconds=round(elapsed, 2))

    def is_ready(self) -> bool:
        """True once the ONNX session is loaded and usable."""
        return self._ready

    @property
    def load_error(self) -> str | None:
        """Last load error message, if loading failed."""
        return self._load_error

    # -- inference ---------------------------------------------------------

    def embed(self, image_bytes: bytes) -> np.ndarray:
        """Preprocess + run inference + L2-normalise. Returns a 1-D float32 vector."""
        batch = self.embed_batch([image_bytes])
        return batch[0]

    def embed_batch(self, images: list[bytes]) -> list[np.ndarray]:
        """Embed multiple images. Each input is preprocessed via the shared contract."""
        if not self._ready or self._session is None:
            raise ModelNotReadyError(self._load_error or "model not loaded yet")
        if not images:
            return []

        tensors = [preprocess(img, self._input_size) for img in images]
        batch = np.concatenate(tensors, axis=0)  # (N, 3, H, W)

        outputs = self._session.run(None, {self._input_name: batch})
        embeddings = np.asarray(outputs[0], dtype=np.float32)
        # DINOv2 backbone may emit (N, dim) directly or (N, tokens, dim); reduce
        # token dimension by mean pooling if present.
        if embeddings.ndim == 3:
            embeddings = embeddings.mean(axis=1)
        return [_l2_normalize(embeddings[i]) for i in range(embeddings.shape[0])]
