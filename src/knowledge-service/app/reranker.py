"""Optional cross-encoder reranker — calls the reranker microservice via HTTP."""

import httpx
import structlog

from app.vectordb.repository import VectorChunk

logger = structlog.get_logger(__name__)


class RerankerEngine:
    """HTTP client for the reranker microservice (optional).

    When ``reranker_url`` is *None*, :meth:`available` returns *False*
    and :meth:`rerank` returns chunks unchanged — the knowledge service
    degrades gracefully to hybrid-search-only mode.
    """

    def __init__(self, reranker_url: str | None) -> None:
        self._reranker_url = reranker_url.rstrip("/") if reranker_url else None

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

        On failure (timeout, connection error, HTTP error) the original
        chunk list is returned truncated to *top_k* with a warning log.
        """
        if not self.available or not chunks:
            return chunks[:top_k]

        documents = [f"{c.title}\n{c.content}" for c in chunks]

        try:
            response = httpx.post(
                f"{self._reranker_url}/rerank",
                json={"query": query, "documents": documents, "top_k": top_k},
                timeout=30.0,
            )
            response.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.warning("reranker_fallback", error=str(exc))
            return chunks[:top_k]

        results = response.json()["results"]

        reranked = []
        for r in results:
            chunk = chunks[r["index"]]
            # Preserve the reranker score for observability
            reranked.append(
                VectorChunk(
                    source_key=chunk.source_key,
                    source_type=chunk.source_type,
                    title=chunk.title,
                    content=chunk.content,
                    score=r["score"],
                    metadata=chunk.metadata,
                    language=chunk.language,
                )
            )

        logger.info(
            "reranker_complete",
            query=query[:80],
            input_chunks=len(chunks),
            output_chunks=len(reranked),
            top_score=reranked[0].score if reranked else 0.0,
        )
        return reranked
