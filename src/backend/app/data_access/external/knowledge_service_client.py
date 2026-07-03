"""HTTP client for the Knowledge Service microservice."""

import httpx
import structlog

from app.config.settings import settings

logger = structlog.get_logger(__name__)

_TIMEOUT_SECONDS = 120.0


class KnowledgeServiceClient:
    """Calls the standalone Knowledge Service via HTTP.

    Every request carries the shared service token as an
    ``Authorization: Bearer <token>`` header (AP-4, INF-S1). The token defaults
    to ``settings.internal_service_token`` so all call sites are authenticated
    without having to thread it through; it can be overridden per instance
    (e.g. in tests).
    """

    def __init__(self, base_url: str, *, service_token: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_token = service_token if service_token is not None else settings.internal_service_token

    def _auth_headers(self) -> dict[str, str]:
        """Build the service-token auth header (empty when no token is set)."""
        if not self._service_token:
            return {}
        return {"Authorization": f"Bearer {self._service_token}"}

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
            headers=self._auth_headers(),
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
            headers=self._auth_headers(),
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()

    def classify(self, question: str) -> str:
        """Classify a question type via the knowledge service."""
        response = httpx.post(
            f"{self._base_url}/classify",
            json={"question": question},
            headers=self._auth_headers(),
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
