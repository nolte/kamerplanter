"""Generates text embeddings via an external embedding service."""

import httpx
import structlog

logger = structlog.get_logger(__name__)

#: Texts per ``POST /embed``. The embedding service refuses more than
#: ``MAX_TEXTS`` (64) with a 422 — see docker/embedding-service/limits.py
#: (#1725) — so ``embed_batch`` slices below it. Half the bound, so raising this
#: is a deliberate diff on both sides:
#: src/backend/tests/unit/guards/test_ml_sidecar_limits.py requires
#: ``MAX_TEXTS >= 2 * _MAX_TEXTS_PER_REQUEST``. The service runs one text per
#: graph call anyway, so a slice costs one HTTP round trip and nothing else.
_MAX_TEXTS_PER_REQUEST = 32


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
        """Embed *texts*, in requests of at most ``_MAX_TEXTS_PER_REQUEST``.

        Returns one embedding vector per text, in the order of *texts*. An empty
        list sends no request.
        """
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), _MAX_TEXTS_PER_REQUEST):
            response = httpx.post(
                f"{self._service_url}/embed",
                json={
                    "texts": texts[start : start + _MAX_TEXTS_PER_REQUEST],
                    "model": self._model_name,
                    "prefix": prefix,
                },
                timeout=120.0,
            )
            response.raise_for_status()
            embeddings.extend(response.json()["embeddings"])
        return embeddings
