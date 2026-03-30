"""Unit tests for LLM adapters (Anthropic, Ollama, OpenAI-compatible)."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.data_access.external.anthropic_llm_adapter import AnthropicLlmAdapter
from app.data_access.external.ollama_llm_adapter import OllamaLlmAdapter
from app.data_access.external.openai_compatible_llm_adapter import OpenAiCompatibleLlmAdapter
from app.domain.interfaces.llm_adapter import ILlmAdapter, LlmResponse


class TestLlmResponseDataclass:
    def test_defaults(self):
        resp = LlmResponse(content="hello", model="test")
        assert resp.content == "hello"
        assert resp.model == "test"
        assert resp.usage == {}

    def test_with_usage(self):
        resp = LlmResponse(content="hi", model="m", usage={"prompt_tokens": 10, "completion_tokens": 5})
        assert resp.usage["prompt_tokens"] == 10


# ── Anthropic Adapter ──────────────────────────────────────────────


class TestAnthropicLlmAdapter:
    @pytest.fixture
    def adapter(self):
        return AnthropicLlmAdapter(api_key="sk-test-key", model="claude-sonnet-4-20250514")

    def test_implements_interface(self, adapter):
        assert isinstance(adapter, ILlmAdapter)

    @patch("app.data_access.external.anthropic_llm_adapter.httpx.post")
    def test_generate_success(self, mock_post, adapter):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "VPD should be between 0.8 and 1.5 kPa."}],
            "model": "claude-sonnet-4-20250514",
            "usage": {"input_tokens": 100, "output_tokens": 25},
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = adapter.generate("system prompt", "What is VPD?")

        assert result.content == "VPD should be between 0.8 and 1.5 kPa."
        assert result.model == "claude-sonnet-4-20250514"
        assert result.usage["prompt_tokens"] == 100
        assert result.usage["completion_tokens"] == 25

        call_kwargs = mock_post.call_args
        assert call_kwargs[1]["headers"]["x-api-key"] == "sk-test-key"
        assert call_kwargs[1]["headers"]["anthropic-version"] == "2023-06-01"

    @patch("app.data_access.external.anthropic_llm_adapter.httpx.post")
    def test_generate_timeout(self, mock_post, adapter):
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")

        with pytest.raises(httpx.TimeoutException):
            adapter.generate("sys", "question")

    @patch("app.data_access.external.anthropic_llm_adapter.httpx.post")
    def test_generate_http_error(self, mock_post, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limited", request=MagicMock(), response=mock_response
        )
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            adapter.generate("sys", "question")

    @patch("app.data_access.external.anthropic_llm_adapter.httpx.post")
    def test_generate_empty_content(self, mock_post, adapter):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [],
            "model": "claude-sonnet-4-20250514",
            "usage": {"input_tokens": 50, "output_tokens": 0},
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = adapter.generate("sys", "q")
        assert result.content == ""

    @patch("app.data_access.external.anthropic_llm_adapter.httpx.post")
    def test_passes_max_tokens_and_temperature(self, mock_post, adapter):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "ok"}],
            "model": "claude-sonnet-4-20250514",
            "usage": {"input_tokens": 10, "output_tokens": 1},
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        adapter.generate("sys", "q", max_tokens=2048, temperature=0.7)

        payload = mock_post.call_args[1]["json"]
        assert payload["max_tokens"] == 2048
        assert payload["temperature"] == 0.7


# ── Ollama Adapter ─────────────────────────────────────────────────


class TestOllamaLlmAdapter:
    @pytest.fixture
    def adapter(self):
        return OllamaLlmAdapter(api_url="http://localhost:11434", model="llama3")

    def test_implements_interface(self, adapter):
        assert isinstance(adapter, ILlmAdapter)

    @patch("app.data_access.external.ollama_llm_adapter.httpx.post")
    def test_generate_success(self, mock_post, adapter):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "llama3",
            "message": {"role": "assistant", "content": "Water your tomatoes regularly."},
            "prompt_eval_count": 80,
            "eval_count": 15,
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = adapter.generate("system prompt", "How to water tomatoes?")

        assert result.content == "Water your tomatoes regularly."
        assert result.model == "llama3"
        assert result.usage["prompt_tokens"] == 80
        assert result.usage["completion_tokens"] == 15

        url = mock_post.call_args[0][0]
        assert url == "http://localhost:11434/api/chat"

    @patch("app.data_access.external.ollama_llm_adapter.httpx.post")
    def test_generate_timeout(self, mock_post, adapter):
        mock_post.side_effect = httpx.TimeoutException("timeout")

        with pytest.raises(httpx.TimeoutException):
            adapter.generate("sys", "q")

    @patch("app.data_access.external.ollama_llm_adapter.httpx.post")
    def test_strips_trailing_slash_from_url(self, mock_post):
        adapter = OllamaLlmAdapter(api_url="http://localhost:11434/", model="llama3")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "llama3",
            "message": {"role": "assistant", "content": "ok"},
            "prompt_eval_count": 5,
            "eval_count": 1,
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        adapter.generate("sys", "q")

        url = mock_post.call_args[0][0]
        assert url == "http://localhost:11434/api/chat"


# ── OpenAI-Compatible Adapter ──────────────────────────────────────


class TestOpenAiCompatibleLlmAdapter:
    @pytest.fixture
    def adapter(self):
        return OpenAiCompatibleLlmAdapter(
            api_url="http://vllm:8000",
            api_key="sk-test",
            model="mistral-7b",
        )

    def test_implements_interface(self, adapter):
        assert isinstance(adapter, ILlmAdapter)

    @patch("app.data_access.external.openai_compatible_llm_adapter.httpx.post")
    def test_generate_success(self, mock_post, adapter):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "mistral-7b",
            "choices": [{"message": {"content": "EC should be between 1.2 and 2.0."}}],
            "usage": {"prompt_tokens": 120, "completion_tokens": 20},
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = adapter.generate("sys", "What EC for flowering?")

        assert result.content == "EC should be between 1.2 and 2.0."
        assert result.model == "mistral-7b"
        assert result.usage["prompt_tokens"] == 120

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["headers"]["authorization"] == "Bearer sk-test"

        url = mock_post.call_args[0][0]
        assert url == "http://vllm:8000/v1/chat/completions"

    @patch("app.data_access.external.openai_compatible_llm_adapter.httpx.post")
    def test_generate_no_api_key(self, mock_post):
        adapter = OpenAiCompatibleLlmAdapter(api_url="http://lmstudio:1234", model="local")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "local",
            "choices": [{"message": {"content": "answer"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        adapter.generate("sys", "q")

        headers = mock_post.call_args[1]["headers"]
        assert "authorization" not in headers

    @patch("app.data_access.external.openai_compatible_llm_adapter.httpx.post")
    def test_generate_empty_choices(self, mock_post, adapter):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "mistral-7b",
            "choices": [],
            "usage": {"prompt_tokens": 10, "completion_tokens": 0},
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = adapter.generate("sys", "q")
        assert result.content == ""

    @patch("app.data_access.external.openai_compatible_llm_adapter.httpx.post")
    def test_generate_http_error(self, mock_post, adapter):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )
        mock_post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            adapter.generate("sys", "q")
