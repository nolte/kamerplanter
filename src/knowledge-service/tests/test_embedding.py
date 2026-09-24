"""Unit tests for the EmbeddingEngine (#1725: requests stay below the service's text bound)."""

import httpx
import pytest

from app.embedding import _MAX_TEXTS_PER_REQUEST, EmbeddingEngine


class _FakeEmbedService:
    """Answers ``POST /embed`` like the service: one vector per text, in order.

    Each vector carries the text it was computed from, so the test can see which
    text ended up at which position after the client concatenated its slices.
    It also refuses more than 64 texts with a 422, as
    docker/embedding-service/limits.py does.
    """

    def __init__(self) -> None:
        self.requests: list[dict] = []

    def post(self, url, *, json=None, timeout=None):
        self.requests.append({"url": url, "json": json, "timeout": timeout})
        request = httpx.Request("POST", url)
        if len(json["texts"]) > 64:
            return httpx.Response(422, json={"detail": "too many texts"}, request=request)
        vectors = [[float(int(text.removeprefix("t")))] for text in json["texts"]]
        return httpx.Response(
            200, json={"embeddings": vectors, "model": json["model"], "dimensions": 1}, request=request
        )


@pytest.fixture
def service(monkeypatch) -> _FakeEmbedService:
    fake = _FakeEmbedService()
    monkeypatch.setattr(httpx, "post", fake.post)
    return fake


def test_the_slice_stays_below_the_service_bound():
    assert 1 <= _MAX_TEXTS_PER_REQUEST <= 16


def test_seventy_texts_go_out_in_slices_of_16_and_come_back_in_order(service):
    texts = [f"t{i}" for i in range(70)]

    result = EmbeddingEngine("http://embedding:8080/", model_name="m").embed_batch(texts, prefix="passage: ")

    assert [len(r["json"]["texts"]) for r in service.requests] == [16, 16, 16, 16, 6]
    assert [text for r in service.requests for text in r["json"]["texts"]] == texts
    assert result == [[float(i)] for i in range(70)]
    assert {r["url"] for r in service.requests} == {"http://embedding:8080/embed"}
    assert {(r["json"]["model"], r["json"]["prefix"]) for r in service.requests} == {("m", "passage: ")}
    assert {r["timeout"] for r in service.requests} == {120.0}


def test_exactly_one_slice_is_one_request(service):
    texts = [f"t{i}" for i in range(_MAX_TEXTS_PER_REQUEST)]

    result = EmbeddingEngine("http://embedding:8080").embed_batch(texts)

    assert len(service.requests) == 1
    assert len(result) == _MAX_TEXTS_PER_REQUEST


def test_an_empty_list_sends_no_request(service):
    assert EmbeddingEngine("http://embedding:8080").embed_batch([]) == []
    assert service.requests == []


def test_embed_sends_one_text_and_returns_its_vector(service):
    assert EmbeddingEngine("http://embedding:8080").embed("t7", prefix="query: ") == [7.0]
    assert service.requests[0]["json"] == {"texts": ["t7"], "model": "multilingual-e5-base", "prefix": "query: "}


def test_an_http_error_of_any_slice_propagates(monkeypatch):
    calls = []

    def failing_second(url, *, json=None, timeout=None):
        calls.append(len(json["texts"]))
        status = 200 if len(calls) == 1 else 503
        body = {"embeddings": [[0.0]] * len(json["texts"])} if status == 200 else {"status": "loading"}
        return httpx.Response(status, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", failing_second)

    with pytest.raises(httpx.HTTPStatusError):
        EmbeddingEngine("http://embedding:8080").embed_batch([f"t{i}" for i in range(20)])
    assert calls == [16, 4]
