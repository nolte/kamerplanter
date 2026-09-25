"""The knowledge service logs the length of a user's question, never its text (#1796).

A question typed into the assistant is free text a person wrote — it can name
them, their address, their garden, their health. ``search``/``ask`` and the
reranker logged it verbatim (``query=``, ``question=``, ``query[:80]``). Driven
through the real ``KnowledgeService`` with fakes for the owned I/O boundary.
"""

from __future__ import annotations

import httpx
import pytest
import structlog.testing

from app.llm.interface import LlmResponse
from app.prompt_engine import PromptEngine
from app.reranker import RerankerEngine
from app.service import KnowledgeService
from tests.test_service_rerank_budget import _FakeEmbedding, _FakeRepo, _FakeSidecar

QUESTION = "Ich bin Erika Mustermann aus der Musterstrasse 12, warum welkt meine Tomate?"


class _FakeLlm:
    def generate(self, system_prompt, user_message, *, max_tokens=None, temperature=None):
        return LlmResponse(content="answer", model="fake", usage={"prompt_tokens": 1, "completion_tokens": 1})


def _service(*, repo_size: int, verification: bool) -> KnowledgeService:
    service = KnowledgeService(
        embedding_engine=_FakeEmbedding(),  # type: ignore[arg-type]
        chunk_repo=_FakeRepo(size=repo_size),  # type: ignore[arg-type]
        llm_adapter=_FakeLlm(),  # type: ignore[arg-type]
        prompt_engine=PromptEngine(),
        reranker=RerankerEngine("http://reranker:8081"),
        reranker_initial_k=10,
    )
    service._answer_verification = verification
    return service


@pytest.fixture(autouse=True)
def sidecar(monkeypatch: pytest.MonkeyPatch) -> _FakeSidecar:
    fake = _FakeSidecar()
    monkeypatch.setattr(httpx, "post", fake)
    return fake


@pytest.mark.parametrize(
    ("call", "repo_size", "verification"),
    [
        (lambda s: s.search(QUESTION, top_k=5), 60, False),
        (lambda s: s.ask(QUESTION, top_k=5), 60, True),
        (lambda s: s.ask(QUESTION, top_k=5), 0, False),
    ],
    ids=["search", "ask-with-verification", "ask-no-context"],
)
def test_no_log_line_carries_the_question(call, repo_size: int, verification: bool) -> None:
    with structlog.testing.capture_logs() as logs:
        call(_service(repo_size=repo_size, verification=verification))

    assert logs, "nothing was logged — the assertion below would be vacuous"
    rendered = repr(logs)
    assert "Mustermann" not in rendered
    assert "Tomate" not in rendered
    lengths = [v for entry in logs for k, v in entry.items() if k in ("query_length", "question_length")]
    assert lengths and set(lengths) == {len(QUESTION)}, logs
