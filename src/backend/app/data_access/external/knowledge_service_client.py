"""HTTP client for the Knowledge Service microservice."""

import httpx
import structlog

logger = structlog.get_logger(__name__)

_TIMEOUT_SECONDS = 120.0


class KnowledgeServiceClient:
    """Calls the standalone Knowledge Service via HTTP."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        doc_language: str | None = None,
    ) -> dict:
        """Semantic search via the knowledge service."""
        params: dict = {"q": query, "top_k": top_k}
        if doc_language:
            params["doc_language"] = doc_language

        response = httpx.get(
            f"{self._base_url}/search",
            params=params,
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def ask(
        self,
        question: str,
        *,
        top_k: int = 5,
        doc_language: str | None = None,
        prompt_language: str | None = None,
        context: dict | None = None,
    ) -> dict:
        """RAG question answering via the knowledge service."""
        payload: dict = {"question": question, "top_k": top_k}
        if doc_language:
            payload["doc_language"] = doc_language
        if prompt_language:
            payload["prompt_language"] = prompt_language
        if context:
            payload["context"] = context

        response = httpx.post(
            f"{self._base_url}/ask",
            json=payload,
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def classify(self, question: str) -> str:
        """Classify a question type via the knowledge service."""
        response = httpx.post(
            f"{self._base_url}/classify",
            json={"question": question},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["question_type"]

    def health(self) -> bool:
        """Check if the knowledge service is healthy."""
        try:
            response = httpx.get(f"{self._base_url}/health", timeout=5.0)
            return response.status_code == 200 and response.json().get("ready", False)
        except Exception:
            return False
