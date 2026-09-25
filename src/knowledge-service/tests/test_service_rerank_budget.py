"""#1751: the rerank budget bounds how many candidates are SCORED, never how many results a caller gets.

The reranker double is the real :class:`RerankerEngine` with ``httpx.post``
replaced by a fake sidecar that, like docker/reranker-service, scores every
document it receives and answers at most ``top_k`` results in descending score
order. The repository double honours ``top_k`` like ``hybrid_search`` does.
"""

import httpx
import pytest

from app.prompt_engine import PromptEngine
from app.reranker import RerankerEngine
from app.service import KnowledgeService
from app.vectordb.repository import VectorChunk

INITIAL_K = 10


def _hybrid_score(position: int) -> float:
    """An RRF-sized score (``hybrid_search`` scores are at most ~0.016), falling with the position."""
    return round(0.016 - position * 0.0001, 6)


def _chunk(position: int) -> VectorChunk:
    return VectorChunk(
        source_key=f"h{position}",
        source_type="care_rule",
        title=f"T{position}",
        content=f"content {position}",
        score=_hybrid_score(position),
        metadata={},
        language="de",
    )


class _FakeRepo:
    """Hybrid order is h0, h1, ...; returns at most ``top_k`` like the real query's LIMIT."""

    def __init__(self, size: int = 60) -> None:
        self._chunks = [_chunk(i) for i in range(size)]
        self.requested_top_k: list[int] = []

    def hybrid_search(self, query_embedding, query_text, top_k=5, source_types=None, vector_weight=0.5, language=None):
        self.requested_top_k.append(top_k)
        return self._chunks[:top_k]


class _FakeEmbedding:
    def embed(self, text: str, *, prefix: str = "") -> list[float]:
        return [0.0]


class _FakeSidecar:
    """Scores ``T<n>`` as ``n`` — so it reverses the hybrid order — and answers at most ``top_k``."""

    def __init__(self) -> None:
        self.document_counts: list[int] = []

    def __call__(self, url, *, json=None, timeout=None):
        documents = json["documents"]
        self.document_counts.append(len(documents))
        scored = sorted(
            ({"index": i, "score": float(doc.split("\n", 1)[0][1:])} for i, doc in enumerate(documents)),
            key=lambda entry: entry["score"],
            reverse=True,
        )
        return httpx.Response(200, json={"results": scored[: json["top_k"]]}, request=httpx.Request("POST", url))


def _service(repo: _FakeRepo, reranker: RerankerEngine | None) -> KnowledgeService:
    return KnowledgeService(
        embedding_engine=_FakeEmbedding(),  # type: ignore[arg-type]
        chunk_repo=repo,  # type: ignore[arg-type]
        llm_adapter=object(),  # type: ignore[arg-type]
        prompt_engine=PromptEngine(),
        reranker=reranker,
        reranker_initial_k=INITIAL_K,
    )


def _keys(chunks: list[VectorChunk]) -> list[str]:
    return [chunk.source_key for chunk in chunks]


@pytest.fixture
def sidecar(monkeypatch) -> _FakeSidecar:
    fake = _FakeSidecar()
    monkeypatch.setattr(httpx, "post", fake)
    return fake


class TestRerankBudget:
    def test_a_top_k_above_initial_k_returns_every_result_scored_head_first(self, sidecar):
        repo = _FakeRepo()
        result = _service(repo, RerankerEngine("http://reranker:8081")).search("q", top_k=20)

        assert repo.requested_top_k == [20]
        assert _keys(result) == [f"h{i}" for i in range(9, -1, -1)] + [f"h{i}" for i in range(10, 20)]

    def test_a_top_k_below_initial_k_returns_the_best_of_the_scored_set(self, sidecar):
        repo = _FakeRepo()
        result = _service(repo, RerankerEngine("http://reranker:8081")).search("q", top_k=5)

        assert repo.requested_top_k == [INITIAL_K]
        assert _keys(result) == ["h9", "h8", "h7", "h6", "h5"]

    @pytest.mark.parametrize("top_k", [1, 5, 10, 11, 20, 50])
    def test_the_reranker_never_scores_more_than_initial_k_documents(self, sidecar, top_k):
        _service(_FakeRepo(), RerankerEngine("http://reranker:8081")).search("q", top_k=top_k)

        assert sidecar.document_counts == [INITIAL_K]

    @pytest.mark.parametrize("top_k", [5, 10, 20, 50])
    def test_a_reranker_fallback_keeps_the_hybrid_order_for_every_result(self, monkeypatch, top_k):
        def deadline(url, *, json=None, timeout=None):
            return httpx.Response(503, json={"status": "timeout"}, request=httpx.Request("POST", url))

        monkeypatch.setattr(httpx, "post", deadline)

        result = _service(_FakeRepo(), RerankerEngine("http://reranker:8081")).search("q", top_k=top_k)

        assert _keys(result) == [f"h{i}" for i in range(top_k)]

    @pytest.mark.parametrize("top_k", [5, 20])
    def test_without_a_reranker_the_hybrid_top_k_is_returned(self, top_k):
        repo = _FakeRepo()
        result = _service(repo, None).search("q", top_k=top_k)

        assert repo.requested_top_k == [top_k]
        assert _keys(result) == [f"h{i}" for i in range(top_k)]

    def test_the_tail_keeps_its_hybrid_score_and_the_head_carries_the_reranker_score(self, sidecar):
        """Scores are not invented: the unscored tail keeps its RRF score, far below any citable threshold."""
        result = _service(_FakeRepo(), RerankerEngine("http://reranker:8081")).search("q", top_k=20)

        # The fake sidecar scores ``T<n>`` as ``n``: the head h9..h0 carries 9.0..0.0.
        assert [chunk.score for chunk in result[:INITIAL_K]] == [float(i) for i in range(9, -1, -1)]
        assert [chunk.score for chunk in result[INITIAL_K:]] == [_hybrid_score(i) for i in range(10, 20)]
