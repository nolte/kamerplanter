import httpx
import structlog

logger = structlog.get_logger(__name__)


class EmbeddingEngine:
    """Generates text embeddings via an external embedding service."""

    def __init__(self, service_url: str, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> None:
        self._service_url = service_url.rstrip("/")
        self._model_name = model_name

    def embed(self, text: str) -> list[float]:
        """Generate a normalized embedding for the given text."""
        result = self.embed_batch([text])
        return result[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate normalized embeddings for a batch of texts."""
        response = httpx.post(
            f"{self._service_url}/embed",
            json={"texts": texts, "model": self._model_name},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["embeddings"]
