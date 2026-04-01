"""Unit tests for KnowledgeServiceClient."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.data_access.external.knowledge_service_client import KnowledgeServiceClient


@pytest.fixture
def client():
    return KnowledgeServiceClient(base_url="http://knowledge-service:8000")


class TestSearch:
    @patch("app.data_access.external.knowledge_service_client.httpx.get")
    def test_search_success(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "query": "What is VPD?",
            "results": [
                {
                    "source_key": "knowledge_guide:vpd",
                    "source_type": "knowledge_guide",
                    "title": "VPD Guide",
                    "content": "VPD is the vapor pressure deficit.",
                    "score": 0.92,
                    "metadata": {},
                    "language": "en",
                }
            ],
            "total": 1,
            "doc_language": "en",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = client.search("What is VPD?", top_k=3, doc_language="en")

        assert result["query"] == "What is VPD?"
        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "VPD Guide"

        call_args = mock_get.call_args
        assert call_args[1]["params"]["q"] == "What is VPD?"
        assert call_args[1]["params"]["top_k"] == 3
        assert call_args[1]["params"]["doc_language"] == "en"

    @patch("app.data_access.external.knowledge_service_client.httpx.get")
    def test_search_without_language(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "query": "test",
            "results": [],
            "total": 0,
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client.search("test")

        params = mock_get.call_args[1]["params"]
        assert "doc_language" not in params

    @patch("app.data_access.external.knowledge_service_client.httpx.get")
    def test_search_http_error(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            client.search("test")


class TestAsk:
    @patch("app.data_access.external.knowledge_service_client.httpx.post")
    def test_ask_success(self, mock_post, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "VPD is the vapor pressure deficit.",
            "question_type": "factual",
            "model": "claude-sonnet-4-20250514",
            "usage": {"prompt_tokens": 200, "completion_tokens": 30},
            "sources": [
                {
                    "source_key": "knowledge_guide:vpd",
                    "source_type": "knowledge_guide",
                    "title": "VPD Guide",
                    "content": "VPD content.",
                    "score": 0.9,
                    "metadata": {},
                    "language": "de",
                }
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = client.ask("What is VPD?", top_k=3, doc_language="de", prompt_language="de")

        assert result["answer"] == "VPD is the vapor pressure deficit."
        assert result["question_type"] == "factual"
        assert len(result["sources"]) == 1

        payload = mock_post.call_args[1]["json"]
        assert payload["question"] == "What is VPD?"
        assert payload["top_k"] == 3
        assert payload["doc_language"] == "de"
        assert payload["prompt_language"] == "de"

    @patch("app.data_access.external.knowledge_service_client.httpx.post")
    def test_ask_with_context(self, mock_post, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "Answer.",
            "model": "test",
            "usage": {},
            "sources": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        context = {"species": "Tomato", "phase": "flowering", "ec": 2.0}
        client.ask("Help", context=context)

        payload = mock_post.call_args[1]["json"]
        assert payload["context"] == context

    @patch("app.data_access.external.knowledge_service_client.httpx.post")
    def test_ask_timeout(self, mock_post, client):
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")

        with pytest.raises(httpx.TimeoutException):
            client.ask("test")


class TestClassify:
    @patch("app.data_access.external.knowledge_service_client.httpx.post")
    def test_classify_success(self, mock_post, client):
        mock_response = MagicMock()
        mock_response.json.return_value = {"question_type": "diagnosis"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = client.classify("My leaves are yellow")

        assert result == "diagnosis"
        payload = mock_post.call_args[1]["json"]
        assert payload["question"] == "My leaves are yellow"


class TestHealth:
    @patch("app.data_access.external.knowledge_service_client.httpx.get")
    def test_health_ok(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ready": True}
        mock_get.return_value = mock_response

        assert client.health() is True

    @patch("app.data_access.external.knowledge_service_client.httpx.get")
    def test_health_not_ready(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ready": False}
        mock_get.return_value = mock_response

        assert client.health() is False

    @patch("app.data_access.external.knowledge_service_client.httpx.get")
    def test_health_connection_error(self, mock_get, client):
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        assert client.health() is False


class TestBaseUrlStripping:
    def test_trailing_slash_stripped(self):
        c = KnowledgeServiceClient(base_url="http://service:8000/")
        assert c._base_url == "http://service:8000"
