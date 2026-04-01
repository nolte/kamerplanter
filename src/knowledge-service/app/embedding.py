"""Generates text embeddings via an external embedding service."""

import httpx
import structlog

logger = structlog.get_logger(__name__)


class EmbeddingEngine:
    """Generates text embeddings via an external embedding service."""

    def __init__(self, service_url: str, model_name: str = "multilingual-e5-base") -> None:
        self._service_url = service_url.rstrip("/")
        self._model_name = model_name

    def embed(self, text: str, *, prefix: str = "") -> list[float]:
        """Embed a single text. Returns a list of floats."""
        result = self.embed_batch([text], prefix=prefix)
        return result[0]

    def embed_batch(self, texts: list[str], *, prefix: str = "") -> list[list[float]]:
        """Embed multiple texts in a single request. Returns list of embedding vectors."""
        response = httpx.post(
            f"{self._service_url}/embed",
            json={"texts": texts, "model": self._model_name, "prefix": prefix},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["embeddings"]
