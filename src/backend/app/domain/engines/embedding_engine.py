import httpx
import structlog

logger = structlog.get_logger(__name__)


class EmbeddingEngine:
    """Generates text embeddings via an external embedding service."""

    def __init__(self, service_url: str, model_name: str = "multilingual-e5-base") -> None:
        self._service_url = service_url.rstrip("/")
        self._model_name = model_name

    def embed(self, text: str, *, prefix: str = "") -> list[float]:
        """Generate a normalized embedding for the given text.

        Args:
            text: Input text to embed.
            prefix: Optional prefix prepended to text before tokenization.
                    E5 models expect ``"query: "`` for queries and
                    ``"passage: "`` for documents.

        Returns:
            Normalized embedding vector.
        """
        result = self.embed_batch([text], prefix=prefix)
        return result[0]

    def embed_batch(self, texts: list[str], *, prefix: str = "") -> list[list[float]]:
        """Generate normalized embeddings for a batch of texts.

        Args:
            texts: List of input texts to embed.
            prefix: Optional prefix prepended to each text before tokenization.

        Returns:
            List of normalized embedding vectors.
        """
        response = httpx.post(
            f"{self._service_url}/embed",
            json={"texts": texts, "model": self._model_name, "prefix": prefix},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["embeddings"]
