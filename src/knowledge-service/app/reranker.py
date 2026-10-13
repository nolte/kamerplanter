"""Optional cross-encoder reranker — calls the reranker microservice via HTTP."""

import time
from collections.abc import Mapping
from typing import Any, Final

import httpx
import structlog

from app.vectordb.repository import VectorChunk

logger = structlog.get_logger(__name__)

#: Closed set of ``reason`` values carried by every ``reranker_fallback`` warning.
#:
#: - ``deadline``: 503 ``{"status": "timeout"}`` — the sidecar's server-side inference deadline fired.
#: - ``busy``: 503 ``{"status": "busy"}`` — the sidecar's inference lock was not obtained in time.
#: - ``loading``: 503 ``{"status": "loading"}`` — the sidecar is still loading its model.
#: - ``http_status``: any other non-2xx answer, including a 503 with an unknown or unparsable body.
#: - ``client_timeout``: this client's own ``timeout`` expired (``httpx.TimeoutException``).
#: - ``transport``: any other httpx transport error (connection refused, DNS, protocol error).
#: - ``malformed_response``: a 2xx whose body is not JSON or lacks a well-formed ``results`` list.
RERANKER_FALLBACK_REASONS: Final[frozenset[str]] = frozenset(
    {
        "deadline",
        "busy",
        "loading",
        "http_status",
        "client_timeout",
        "transport",
        "malformed_response",
    }
)

#: The sidecar's 503 body ``status`` values and the fallback reason each one maps to.
_SIDECAR_UNAVAILABLE_REASONS: Final[Mapping[str, str]] = {
    "timeout": "deadline",
    "busy": "busy",
    "loading": "loading",
}


class MalformedRerankResponseError(ValueError):
    """A 2xx reranker answer whose body does not have the expected shape."""


def _reason_for_status(response: httpx.Response) -> str:
    """Classify a non-2xx answer; only a 503 with a known sidecar ``status`` gets a specific reason."""
    if response.status_code != 503:
        return "http_status"
    try:
        body = response.json()
    except ValueError:
        return "http_status"
    if not isinstance(body, dict):
        return "http_status"
    status = body.get("status")
    if not isinstance(status, str):
        return "http_status"
    return _SIDECAR_UNAVAILABLE_REASONS.get(status, "http_status")


def _parse_results(response: httpx.Response, chunk_count: int) -> list[tuple[int, float]]:
    """Return ``(index, score)`` pairs from a 2xx body, or raise :class:`MalformedRerankResponseError`."""
    try:
        body: Any = response.json()
    except ValueError as exc:
        raise MalformedRerankResponseError(f"response body is not JSON: {exc}") from exc
    if not isinstance(body, dict):
        raise MalformedRerankResponseError("response body is not a JSON object")
    results = body.get("results")
    if not isinstance(results, list):
        raise MalformedRerankResponseError("response body has no 'results' list")

    parsed: list[tuple[int, float]] = []
    for position, entry in enumerate(results):
        if not isinstance(entry, dict):
            raise MalformedRerankResponseError(f"results[{position}] is not an object")
        index = entry.get("index")
        score = entry.get("score")
        # bool is an int subclass; a JSON true/false is not an index or a score.
        if not isinstance(index, int) or isinstance(index, bool):
            raise MalformedRerankResponseError(f"results[{position}].index is not an integer")
        if not 0 <= index < chunk_count:
            raise MalformedRerankResponseError(f"results[{position}].index {index} is outside 0..{chunk_count - 1}")
        if not isinstance(score, int | float) or isinstance(score, bool):
            raise MalformedRerankResponseError(f"results[{position}].score is not a number")
        parsed.append((index, float(score)))
    return parsed


class RerankerEngine:
    """HTTP client for the reranker microservice (optional).

    When ``reranker_url`` is *None*, :meth:`available` returns *False*
    and :meth:`rerank` returns chunks unchanged — the knowledge service
    degrades gracefully to hybrid-search-only mode.

    Each document sent for scoring is ``title + "\\n" + content`` cut to
    *max_document_chars* characters (must be at least 1).
    """

    def __init__(self, reranker_url: str | None, *, max_document_chars: int = 500) -> None:
        if max_document_chars < 1:
            raise ValueError(f"max_document_chars must be at least 1, got {max_document_chars}")
        self._reranker_url = reranker_url.rstrip("/") if reranker_url else None
        self._max_document_chars = max_document_chars

    @property
    def available(self) -> bool:
        return self._reranker_url is not None

    def rerank(
        self,
        query: str,
        chunks: list[VectorChunk],
        *,
        top_k: int = 5,
    ) -> list[VectorChunk]:
        """Re-rank *chunks* by cross-encoder relevance to *query*.

        On any failure (sidecar deadline/busy/loading 503, other HTTP error,
        client timeout, transport error, malformed 2xx body) the original
        chunk list is returned truncated to *top_k* and exactly one
        ``reranker_fallback`` warning is logged whose ``reason`` is one of
        :data:`RERANKER_FALLBACK_REASONS`.
        """
        if not self.available or not chunks:
            return chunks[:top_k]

        # Cut client-side so the sidecar finishes inside its 25 s deadline
        # (#1751, budget in app/config.py). Only the scored text is cut: the
        # chunks returned below keep their full content.
        documents = [f"{c.title}\n{c.content}"[: self._max_document_chars] for c in chunks]

        started = time.perf_counter()
        try:
            response = httpx.post(
                f"{self._reranker_url}/rerank",
                json={"query": query, "documents": documents, "top_k": top_k},
                timeout=30.0,
            )
            response.raise_for_status()
        # TimeoutException subclasses HTTPError: it must be handled first.
        except httpx.TimeoutException as exc:
            return self._fallback(chunks, top_k, reason="client_timeout", status_code=None, exc=exc, started=started)
        except httpx.HTTPStatusError as exc:
            return self._fallback(
                chunks,
                top_k,
                reason=_reason_for_status(exc.response),
                status_code=exc.response.status_code,
                exc=exc,
                started=started,
            )
        except httpx.HTTPError as exc:
            return self._fallback(chunks, top_k, reason="transport", status_code=None, exc=exc, started=started)

        try:
            results = _parse_results(response, len(chunks))
        except MalformedRerankResponseError as exc:
            return self._fallback(
                chunks,
                top_k,
                reason="malformed_response",
                status_code=response.status_code,
                exc=exc,
                started=started,
            )

        reranked = []
        for index, score in results:
            chunk = chunks[index]
            # Preserve the reranker score for observability
            reranked.append(
                VectorChunk(
                    source_key=chunk.source_key,
                    source_type=chunk.source_type,
                    title=chunk.title,
                    content=chunk.content,
                    score=score,
                    metadata=chunk.metadata,
                    language=chunk.language,
                )
            )

        logger.info(
            "reranker_complete",
            query_length=len(query),
            input_chunks=len(chunks),
            output_chunks=len(reranked),
            top_score=reranked[0].score if reranked else 0.0,
            elapsed_s=_elapsed_since(started),
        )
        return reranked

    @staticmethod
    def _fallback(
        chunks: list[VectorChunk],
        top_k: int,
        *,
        reason: str,
        status_code: int | None,
        exc: Exception,
        started: float,
    ) -> list[VectorChunk]:
        """Log the single ``reranker_fallback`` warning and return the unranked order."""
        logger.warning(
            "reranker_fallback",
            reason=reason,
            status_code=status_code,
            documents=len(chunks),
            elapsed_s=_elapsed_since(started),
            error=str(exc),
        )
        return chunks[:top_k]


def _elapsed_since(started: float) -> float:
    """Wall time since *started* (``time.perf_counter``) in seconds, rounded to 2 decimals."""
    return round(time.perf_counter() - started, 2)
