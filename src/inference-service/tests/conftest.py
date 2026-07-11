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

    def active_species_keys(self) -> set[str]:
        """Species with at least one active embedding.

        Mirrors the real ``/match`` SQL invariant (``WHERE is_active = TRUE``,
        with NO ``source_url`` dependency), so an activated user contribution —
        which never carries a source_url — is match-eligible.
        """
        return {r["species_key"] for r in self.rows if r.get("is_active", True)}

    def list_by_species(
        self,
        species_key: str,
        limit: int = 50,
        *,
        active_only: bool = False,
        include_contributions: bool = False,
    ) -> list[dict]:
        def _displayable(r: dict) -> bool:
            if r.get("source_url"):
                return True
            return include_contributions and r.get("source") == "user_contributed"

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
                "contributed_by": r.get("contributed_by"),
                "tenant_key": r.get("tenant_key"),
                "contributed_at": r.get("contributed_at"),
            }
            for r in self.rows
            if r.get("species_key") == species_key and _displayable(r) and (not active_only or r.get("is_active", True))
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

    def list_by_label(self, label: str, limit: int = 200, *, active_only: bool = False) -> list[dict]:
        return [
            {
                "id": r.get("id", i + 1),
                "source_url": r.get("source_url"),
                "license": r.get("license"),
                "attribution": r.get("attribution"),
                "source": r.get("source"),
                "source_record_id": r.get("source_record_id"),
                "is_active": r.get("is_active", True),
                "exclusion_reason": r.get("exclusion_reason"),
            }
            for i, r in enumerate(self.rows)
            if r.get("label") == label and r.get("source_url") and (not active_only or r.get("is_active", True))
        ][:limit]

    def set_active(self, label: str, prototype_id: int, *, is_active: bool, reason=None) -> bool:
        for r in self.rows:
            if r.get("label") == label and r.get("id") == prototype_id:
                r["is_active"] = is_active
                r["exclusion_reason"] = reason if not is_active else None
                return True
        return False

    def coverage(self) -> list[dict]:
        from collections import Counter

        totals: Counter = Counter()
        actives: Counter = Counter()
        cats: dict = {}
        for r in self.rows:
            key = r.get("label")
            cats[key] = r.get("category", "pest")
            totals[key] += 1
            if r.get("is_active", True):
                actives[key] += 1
        return [{"label": k, "category": cats[k], "total": totals[k], "active": actives[k]} for k in totals]

    def delete_by_label(self, label: str) -> int:
        before = len(self.rows)
        self.rows = [r for r in self.rows if r.get("label") != label]
        return before - len(self.rows)

    def count(self, label=None) -> int:
        if label:
            return sum(1 for r in self.rows if r.get("label") == label)
        return len(self.rows)


class FakeDiseaseClassifier:
    """Deterministic stand-in for the ONNX DiseaseClassifier (REQ-038)."""

    def __init__(self, ready: bool = True) -> None:
        self._ready = ready
        self.load_error: str | None = None
        # Preloaded (label, category, scientific_name, probability) tuples.
        self.results: list = []
        self.class_count = 3

    def is_ready(self) -> bool:
        return self._ready

    def classify(self, image_bytes: bytes, *, k: int = 5):
        from app.disease_classifier import DiseaseClassification

        return [
            DiseaseClassification(label=label, category=category, scientific_name=sci, probability=prob)
            for (label, category, sci, prob) in self.results[:k]
        ]


class FakePhenotypeEngine:
    """Stand-in for PhenotypeEngine -- no PlantCV needed (REQ-038)."""

    def __init__(self, available: bool = True) -> None:
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def measure(self, image_bytes: bytes):
        from app.phenotype_engine import PhenotypeMetrics, PhenotypeUnavailableError

        if not self._available:
            raise PhenotypeUnavailableError("unavailable")
        return PhenotypeMetrics(
            leaf_area_px=1234,
            green_index=0.62,
            discolored_area_ratio=0.08,
            necrotic_area_ratio=0.02,
            solidity=0.71,
            hue_circular_mean_deg=110.5,
            plantcv_version="4.0-fake",
        )


@pytest.fixture
def fake_disease_classifier() -> FakeDiseaseClassifier:
    return FakeDiseaseClassifier()


@pytest.fixture
def fake_phenotype_engine() -> FakePhenotypeEngine:
    return FakePhenotypeEngine()


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


# Shared service token used across the auth tests (AP-4, INF-S2).
TEST_SERVICE_TOKEN = "test-service-token"


def _patch_singletons(monkeypatch, fake_embedder, fake_repo, fake_pest_repo) -> None:
    """Inject fakes into the app module singletons (skips the real lifespan)."""
    from app import main

    monkeypatch.setattr(main, "_embedder", fake_embedder)
    monkeypatch.setattr(main, "_repo", fake_repo)
    monkeypatch.setattr(main, "_pest_repo", fake_pest_repo)
    monkeypatch.setattr(main, "_vec_conn", _FakeConn())
    monkeypatch.setattr(main, "_model_checksum", "test-checksum")
    # REQ-038: phenotype available by default; disease classifier disabled by
    # default (None) so the /disease/status "disabled" path is the baseline. The
    # ``disease_client`` fixture enables it explicitly.
    monkeypatch.setattr(main, "_phenotype_engine", FakePhenotypeEngine())
    monkeypatch.setattr(
        main,
        "_disease_model_meta",
        {"model_name": "plantdoc_disease_v1", "fine_tuned_on": ["PlantDoc"]},
    )
    # Configure the shared service token so the app-level auth dependency has a
    # secret to compare against.
    monkeypatch.setattr(main.settings, "internal_service_token", TEST_SERVICE_TOKEN)


@pytest.fixture
def client(fake_embedder, fake_repo, fake_pest_repo, monkeypatch):
    """A TestClient with the app singletons patched to fakes.

    The TestClient is used WITHOUT its context-manager form, so the real
    lifespan (pgvector connect + ONNX load) never runs. We inject the fakes
    directly into the module-level singletons the endpoints read. The valid
    service token is sent by default so the business-endpoint tests are
    authenticated (AP-4).
    """
    from fastapi.testclient import TestClient

    from app import main

    _patch_singletons(monkeypatch, fake_embedder, fake_repo, fake_pest_repo)
    return TestClient(main.app, headers={"Authorization": f"Bearer {TEST_SERVICE_TOKEN}"})


@pytest.fixture
def disease_client(client, fake_disease_classifier, monkeypatch):
    """Authenticated TestClient with the REQ-038 disease classifier enabled."""
    from app import main

    monkeypatch.setattr(main, "_disease_classifier", fake_disease_classifier)
    return client


@pytest.fixture
def unauth_client(fake_embedder, fake_repo, fake_pest_repo, monkeypatch):
    """A TestClient with fakes patched but NO Authorization header.

    Used by the auth negative tests to assert protected endpoints reject
    unauthenticated callers while probes stay reachable.
    """
    from fastapi.testclient import TestClient

    from app import main

    _patch_singletons(monkeypatch, fake_embedder, fake_repo, fake_pest_repo)
    return TestClient(main.app)
