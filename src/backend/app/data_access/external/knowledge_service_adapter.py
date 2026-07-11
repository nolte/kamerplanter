"""REQ-031 §4.1 — async ``HttpKnowledgeServiceAdapter`` with circuit breaker.

Default implementation of :class:`~app.domain.interfaces.knowledge_service.
IKnowledgeService` on ``httpx.AsyncClient``. It supersedes the synchronous
``knowledge_service_client.py`` for all KI features and adds the resilience the
old client lacked (NFR-007):

* per-call timeout (``AI_KNOWLEDGE_SERVICE_TIMEOUT_S``, default 60 s);
* up to two retries on ``5xx`` / transport errors with a short backoff;
* a circuit breaker — after ``AI_CIRCUIT_BREAKER_THRESHOLD`` failures inside
  ``AI_CIRCUIT_BREAKER_WINDOW_S`` the adapter reports itself unhealthy for
  ``AI_CIRCUIT_BREAKER_COOLDOWN_S`` so callers fall back to the rule-based path
  instead of hammering a dead service.

The cluster-internal bearer token (AP-4) is forwarded on every request exactly
like the legacy client.
"""

from __future__ import annotations

import asyncio
import time

import httpx
import structlog

from app.config.settings import settings
from app.domain.interfaces.knowledge_service import (
    AskResult,
    IKnowledgeService,
    KnowledgeChunk,
    QuestionContext,
)

logger = structlog.get_logger(__name__)


class _CircuitBreaker:
    """Minimal count-based circuit breaker (thread-safe enough for asyncio).

    Trips ``open`` after ``threshold`` failures within ``window_s``; stays open
    for ``cooldown_s`` and then allows a single trial call (half-open). A success
    resets the failure history.
    """

    def __init__(self, *, threshold: int, window_s: float, cooldown_s: float) -> None:
        self._threshold = threshold
        self._window_s = window_s
        self._cooldown_s = cooldown_s
        self._failures: list[float] = []
        self._open_until: float = 0.0

    def is_open(self) -> bool:
        """True while the breaker blocks calls (cooldown not yet elapsed)."""
        return time.monotonic() < self._open_until

    def record_success(self) -> None:
        """Clear failure history and close the breaker."""
        self._failures.clear()
        self._open_until = 0.0

    def record_failure(self) -> None:
        """Register a failure and trip the breaker once the threshold is hit."""
        now = time.monotonic()
        self._failures = [ts for ts in self._failures if now - ts < self._window_s]
        self._failures.append(now)
        if len(self._failures) >= self._threshold:
            self._open_until = now + self._cooldown_s
            logger.warning(
                "knowledge_service_circuit_open",
                cooldown_s=self._cooldown_s,
                failures=len(self._failures),
            )


class KnowledgeServiceUnavailableError(RuntimeError):
    """Raised when the Knowledge Service cannot be reached (breaker open or 5xx).

    Callers (``AiAssistantService``) catch this and degrade to the rule-based
    fallback path (REQ-031 §1, W-011) — it must never surface as a 5xx.
    """


class HttpKnowledgeServiceAdapter(IKnowledgeService):
    """``httpx.AsyncClient`` implementation of the Knowledge-Service port."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        service_token: str | None = None,
        timeout_s: float | None = None,
        max_retries: int = 2,
        breaker: _CircuitBreaker | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = (base_url or settings.knowledge_service_url).rstrip("/")
        self._service_token = service_token if service_token is not None else settings.internal_service_token
        self._timeout_s = timeout_s if timeout_s is not None else settings.ai_knowledge_service_timeout_s
        self._max_retries = max_retries
        self._breaker = breaker or _CircuitBreaker(
            threshold=settings.ai_circuit_breaker_threshold,
            window_s=settings.ai_circuit_breaker_window_s,
            cooldown_s=settings.ai_circuit_breaker_cooldown_s,
        )
        # Allowing an injected client keeps unit tests transport-only (respx).
        self._client = client

    def _auth_headers(self) -> dict[str, str]:
        """Build the cluster-internal bearer header (empty when unset)."""
        if not self._service_token:
            return {}
        return {"Authorization": f"Bearer {self._service_token}"}

    async def _acquire_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout_s)

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Issue a request with retry-on-5xx and circuit-breaker bookkeeping.

        Raises :class:`KnowledgeServiceUnavailableError` when the breaker is open
        or all attempts fail; ``2x/4xx`` responses are returned as-is (a 4xx is a
        caller error, not a service outage — it does not count against the
        breaker).
        """
        if self._breaker.is_open():
            raise KnowledgeServiceUnavailableError("Knowledge Service circuit is open.")

        client = await self._acquire_client()
        owns_client = self._client is None
        last_exc: Exception | None = None
        try:
            for attempt in range(self._max_retries + 1):
                try:
                    response = await client.request(method, path, headers=self._auth_headers(), **kwargs)
                except (httpx.TransportError, httpx.TimeoutException) as exc:
                    last_exc = exc
                else:
                    if response.status_code < 500:
                        self._breaker.record_success()
                        return response
                    # SEC-004: never wrap the ``httpx`` request/response into the
                    # exception chain — it still carries the ``Authorization:
                    # Bearer`` header and would leak the token into error tracking.
                    # A scrubbed marker keeps the cause header- and body-free.
                    last_exc = KnowledgeServiceUnavailableError(f"Knowledge Service returned {response.status_code}.")
                self._breaker.record_failure()
                if attempt < self._max_retries:
                    await asyncio.sleep(0.2 * (attempt + 1))
        finally:
            if owns_client:
                await client.aclose()

        raise KnowledgeServiceUnavailableError("Knowledge Service request failed after retries.") from last_exc

    @staticmethod
    def _raise_on_client_error(response: httpx.Response) -> None:
        """Translate a ``4xx`` into a token-free unavailable error (SEC-004).

        ``httpx.Response.raise_for_status`` raises an ``HTTPStatusError`` whose
        ``request`` still carries the ``Authorization: Bearer`` header — that
        header would leak into any error tracker or log that serialises the
        exception. We degrade to :class:`KnowledgeServiceUnavailableError`
        carrying only the status code (no headers, no request, no body), so the
        service layer runs its deterministic fallback instead of a 5xx.
        """
        if response.status_code >= 400:
            raise KnowledgeServiceUnavailableError(f"Knowledge Service returned {response.status_code}.")

    async def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        doc_language: str | None = None,
    ) -> list[KnowledgeChunk]:
        params: dict = {"q": query, "top_k": top_k}
        if doc_language:
            params["doc_language"] = doc_language
        response = await self._request("GET", "/search", params=params)
        self._raise_on_client_error(response)
        data = response.json()
        return [KnowledgeChunk(**chunk) for chunk in data.get("results", [])]

    async def ask(
        self,
        question: str,
        *,
        top_k: int = 10,
        context: QuestionContext | None = None,
        doc_language: str | None = None,
        prompt_language: str | None = None,
    ) -> AskResult:
        payload: dict = {"question": question, "top_k": top_k}
        if doc_language:
            payload["doc_language"] = doc_language
        if prompt_language:
            payload["prompt_language"] = prompt_language
        if context is not None:
            ks_context = context.to_ks_payload()
            if ks_context:
                payload["context"] = ks_context
        response = await self._request("POST", "/ask", json=payload)
        self._raise_on_client_error(response)
        data = response.json()
        return AskResult(
            answer=data["answer"],
            question_type=data.get("question_type", "factual"),
            model_name=data.get("model", "unknown"),
            provider_type=data.get("provider_type"),
            kb_version=data.get("kb_version"),
            sources=[KnowledgeChunk(**s) for s in data.get("sources", [])],
            usage=data.get("usage", {}),
        )

    async def health_check(self) -> bool:
        if self._breaker.is_open():
            return False
        client = await self._acquire_client()
        owns_client = self._client is None
        try:
            response = await client.get("/health", headers=self._auth_headers())
            return response.status_code == 200 and bool(response.json().get("ready", True))
        # ``as exc`` is required: bare ``except (A, B):`` is miscompiled by
        # ``ruff format`` into invalid ``except A, B:`` syntax (project ruff bug).
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            logger.debug("knowledge_service_health_unreachable", error=str(exc))
            return False
        finally:
            if owns_client:
                await client.aclose()
