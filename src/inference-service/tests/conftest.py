"""Shared fixtures for inference-service tests.

These run WITHOUT a real ONNX model or a live PostgreSQL: the embedder is a
deterministic fake and the repository is an in-memory fake. The FastAPI app's
module-level singletons are patched directly so the TestClient never triggers
the real lifespan (model load / DB connection).
"""

import io

import numpy as np
import pytest
from PIL import Image


def make_image_bytes(
    color: tuple[int, int, int] = (10, 120, 60),
    size: tuple[int, int] = (300, 200),
    fmt: str = "PNG",
) -> bytes:
    """Create a deterministic encoded test image."""
    image = Image.new("RGB", size, color)
    # Add a simple gradient so resize/crop are non-trivial but still deterministic.
    pixels = np.asarray(image, dtype=np.uint8).copy()
    pixels[:, : size[0] // 2] = (200, 40, 40)
    image = Image.fromarray(pixels)
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture
def image_bytes() -> bytes:
    """A deterministic PNG image."""
    return make_image_bytes()


class FakeEmbedder:
    """Deterministic stand-in for the ONNX Embedder.

    Produces a normalised vector derived from the byte content so equal inputs
    yield equal outputs (determinism) and different inputs differ.
    """

    def __init__(self, dim: int = 384, ready: bool = True) -> None:
        self._dim = dim
        self._ready = ready
        self.load_error = None

    def is_ready(self) -> bool:
        return self._ready

    def _vector_for(self, data: bytes) -> np.ndarray:
        seed = int.from_bytes(data[:8].ljust(8, b"\0"), "big") % (2**32)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self._dim).astype(np.float32)
        norm = float(np.linalg.norm(vec))
        return (vec / norm).astype(np.float32)

    def embed(self, data: bytes) -> np.ndarray:
        return self._vector_for(data)

    def embed_batch(self, images: list[bytes]) -> list[np.ndarray]:
        return [self._vector_for(d) for d in images]


class FakeRepo:
    """In-memory stand-in for SpeciesEmbeddingRepository."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.matches: list = []  # preloaded SpeciesMatch list for /match
        self._next_id = 1

    def upsert_reference(self, **kwargs) -> None:
        kwargs.setdefault("id", self._next_id)
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("exclusion_reason", None)
        self._next_id += 1
        self.rows.append(kwargs)

    def match(self, query_vector, k=5, model=None):
        return self.matches[:k]

    def list_by_species(self, species_key: str, limit: int = 50, *, active_only: bool = False) -> list[dict]:
        return [
            {
                "id": r.get("id"),
                "source_url": r.get("source_url"),
                "license": r.get("license"),
                "attribution": r.get("attribution"),
                "organ": r.get("organ"),
                "source": r.get("source"),
                "source_record_id": r.get("source_record_id"),
                "is_active": r.get("is_active", True),
                "exclusion_reason": r.get("exclusion_reason"),
            }
            for r in self.rows
            if r.get("species_key") == species_key
            and r.get("source_url")
            and (not active_only or r.get("is_active", True))
        ][:limit]

    def set_active(self, species_key: str, embedding_id: int, *, is_active: bool, reason=None) -> bool:
        for r in self.rows:
            if r.get("species_key") == species_key and r.get("id") == embedding_id:
                r["is_active"] = is_active
                r["exclusion_reason"] = reason if not is_active else None
                return True
        return False

    def delete_by_species(self, species_key: str) -> int:
        before = len(self.rows)
        self.rows = [r for r in self.rows if r.get("species_key") != species_key]
        return before - len(self.rows)

    def count(self, species_key=None) -> int:
        if species_key:
            return sum(1 for r in self.rows if r.get("species_key") == species_key)
        return len(self.rows)


class FakePestRepo:
    """In-memory stand-in for PestEmbeddingRepository."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.matches: list = []  # preloaded PestMatch list for /pest/detect

    def upsert_prototype(self, **kwargs) -> None:
        self.rows.append(kwargs)

    def classify(self, query_vector, k=5, model=None):
        return self.matches[:k]

    def delete_by_label(self, label: str) -> int:
        before = len(self.rows)
        self.rows = [r for r in self.rows if r.get("label") != label]
        return before - len(self.rows)

    def count(self, label=None) -> int:
        if label:
            return sum(1 for r in self.rows if r.get("label") == label)
        return len(self.rows)


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
def fake_repo() -> FakeRepo:
    return FakeRepo()


@pytest.fixture
def fake_pest_repo() -> FakePestRepo:
    return FakePestRepo()


class _FakeConn:
    """Stand-in for VectorDbConnection (always connected)."""

    def is_connected(self) -> bool:
        return True


@pytest.fixture
def client(fake_embedder, fake_repo, fake_pest_repo, monkeypatch):
    """A TestClient with the app singletons patched to fakes.

    The TestClient is used WITHOUT its context-manager form, so the real
    lifespan (pgvector connect + ONNX load) never runs. We inject the fakes
    directly into the module-level singletons the endpoints read.
    """
    from fastapi.testclient import TestClient

    from app import main

    monkeypatch.setattr(main, "_embedder", fake_embedder)
    monkeypatch.setattr(main, "_repo", fake_repo)
    monkeypatch.setattr(main, "_pest_repo", fake_pest_repo)
    monkeypatch.setattr(main, "_vec_conn", _FakeConn())
    monkeypatch.setattr(main, "_model_checksum", "test-checksum")

    # No `with` block -> lifespan is not invoked.
    return TestClient(main.app)
