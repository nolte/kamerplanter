"""REQ-038 -- ONNX disease/deficiency classifier.

A dedicated supervised classifier, SEPARATE from the DINOv2 embedder used for
species matching (REQ-029) and pest few-shot (REQ-044). Where REQ-044 matches an
image against a few-shot prototype index, REQ-038 runs a fine-tuned softmax head
that emits a fixed set of disease / deficiency classes.

Provenance (model card): the classifier is fine-tuned on the PlantDoc dataset
(CC-BY-4.0, field images) plus curated own data. PlantVillage is deliberately
NOT used (unclear licence + lab->field domain gap) and is never listed in the
model card.

Like the embedder, the ONNX session is loaded in a background thread at startup
so liveness probes stay responsive; until it finishes ``is_ready()`` is False and
``classify`` raises ``DiseaseModelNotReadyError``. The model artifact and its
label map are mounted at runtime (volume / init-container), never baked into the
image -- only this loader lives in the repo.
"""

import json
import threading
import time
from pathlib import Path

import numpy as np
import structlog

from app.preprocessing import preprocess

logger = structlog.get_logger(__name__)

_MODEL_FILENAME = "model.onnx"
_LABELS_FILENAME = "labels.json"
_MODELINFO_FILENAME = "diseasemodelinfo.json"

# Categories a class can carry. ``deficiency`` has no REQ-010 stammdaten
# collection yet, so the backend leaves ``matched_*_key`` null for it and matches
# via REQ-036 symptom slugs instead.
_KNOWN_CATEGORIES = {"disease", "deficiency", "pest", "healthy"}


class DiseaseModelNotReadyError(RuntimeError):
    """Raised when a classification is requested before the model has loaded."""


class DiseaseLabel:
    """One output class of the classifier (index-aligned with the ONNX head)."""

    __slots__ = ("label", "category", "scientific_name")

    def __init__(self, label: str, category: str, scientific_name: str | None = None) -> None:
        self.label = label
        self.category = category if category in _KNOWN_CATEGORIES else "disease"
        self.scientific_name = scientific_name


def _softmax(logits: np.ndarray) -> np.ndarray:
    """Numerically stable softmax over the last axis of a 1-D logit vector."""
    shifted = logits - np.max(logits)
    exp = np.exp(shifted)
    total = float(np.sum(exp))
    if total < 1e-12:
        return np.full_like(exp, 1.0 / exp.shape[0])
    return exp / total


class DiseaseClassification:
    """A single scored class result."""

    __slots__ = ("label", "category", "scientific_name", "probability")

    def __init__(self, label: str, category: str, scientific_name: str | None, probability: float) -> None:
        self.label = label
        self.category = category
        self.scientific_name = scientific_name
        self.probability = probability


class DiseaseClassifier:
    """Wraps an ONNX Runtime session for disease/deficiency classification."""

    def __init__(self, model_path: str, input_size: int) -> None:
        self._model_path = Path(model_path)
        self._input_size = input_size
        self._session = None
        self._input_name: str | None = None
        self._labels: list[DiseaseLabel] = []
        self._ready = False
        self._load_error: str | None = None
        self._lock = threading.Lock()

    # -- lifecycle ---------------------------------------------------------

    def start_load(self) -> None:
        """Kick off the model load in a daemon thread (non-blocking)."""
        threading.Thread(target=self._load, name="disease-load", daemon=True).start()

    def _load(self) -> None:
        import onnxruntime as ort

        start = time.monotonic()
        onnx_file = self._model_path / _MODEL_FILENAME
        labels_file = self._model_path / _LABELS_FILENAME
        if not onnx_file.exists():
            self._load_error = f"disease model file not found: {onnx_file}"
            logger.warning("disease_model_load_skipped", reason=self._load_error)
            return
        if not labels_file.exists():
            self._load_error = f"disease label map not found: {labels_file}"
            logger.error("disease_model_load_failed", reason=self._load_error)
            return

        try:
            labels = self._parse_labels(labels_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            self._load_error = f"invalid disease label map: {exc}"
            logger.error("disease_model_load_failed", reason=self._load_error)
            return

        try:
            opts = ort.SessionOptions()
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session = ort.InferenceSession(str(onnx_file), opts, providers=["CPUExecutionProvider"])
        except Exception as exc:  # noqa: BLE001 -- surface any ORT load failure
            self._load_error = str(exc)
            logger.error("disease_model_load_failed", reason=self._load_error)
            return

        with self._lock:
            self._session = session
            self._input_name = session.get_inputs()[0].name
            self._labels = labels
            self._ready = True
            self._load_error = None

        elapsed = time.monotonic() - start
        logger.info("disease_model_loaded", file=str(onnx_file), classes=len(labels), seconds=round(elapsed, 2))

    @staticmethod
    def _parse_labels(raw: str) -> list[DiseaseLabel]:
        """Parse ``labels.json`` (index-ordered list of class descriptors)."""
        data = json.loads(raw)
        entries = data["classes"] if isinstance(data, dict) else data
        if not isinstance(entries, list) or not entries:
            raise ValueError("label map must be a non-empty list of classes")
        labels: list[DiseaseLabel] = []
        for entry in entries:
            if isinstance(entry, str):
                labels.append(DiseaseLabel(label=entry, category="disease"))
                continue
            label = entry.get("label")
            if not label:
                raise ValueError("each class entry needs a 'label'")
            labels.append(
                DiseaseLabel(
                    label=label,
                    category=entry.get("category", "disease"),
                    scientific_name=entry.get("scientific_name"),
                )
            )
        return labels

    def is_ready(self) -> bool:
        """True once the ONNX session and label map are loaded and usable."""
        return self._ready

    @property
    def load_error(self) -> str | None:
        """Last load error message, if loading failed or was skipped."""
        return self._load_error

    @property
    def class_count(self) -> int:
        """Number of output classes (0 until loaded)."""
        return len(self._labels)

    # -- inference ---------------------------------------------------------

    def classify(self, image_bytes: bytes, *, k: int = 5) -> list[DiseaseClassification]:
        """Preprocess + run inference + softmax; return the top-k classes.

        Results are ordered by descending probability. No threshold is applied
        here -- the caller (endpoint) drops classes below the configured floor so
        the floor stays a single tunable setting.
        """
        if not self._ready or self._session is None:
            raise DiseaseModelNotReadyError(self._load_error or "disease model not loaded yet")

        tensor = preprocess(image_bytes, self._input_size)  # (1, 3, H, W)
        outputs = self._session.run(None, {self._input_name: tensor})
        logits = np.asarray(outputs[0], dtype=np.float32).reshape(-1)
        if logits.shape[0] != len(self._labels):
            raise DiseaseModelNotReadyError(
                f"model emits {logits.shape[0]} logits but label map has {len(self._labels)} classes"
            )

        probabilities = _softmax(logits)
        order = np.argsort(probabilities)[::-1][: max(1, k)]
        return [
            DiseaseClassification(
                label=self._labels[i].label,
                category=self._labels[i].category,
                scientific_name=self._labels[i].scientific_name,
                probability=round(float(probabilities[i]), 6),
            )
            for i in order
        ]
