"""Ollama local LLM adapter — uses httpx against the Ollama REST API."""

import httpx
import structlog

from app.llm.interface import ILlmAdapter, LlmResponse

logger = structlog.get_logger(__name__)

_TIMEOUT_SECONDS = 600.0


class OllamaLlmAdapter(ILlmAdapter):
    """Calls a local Ollama instance via its /api/chat endpoint."""

    def __init__(self, api_url: str = "http://ollama:11434", model: str = "llama3") -> None:
        self._api_url = api_url.rstrip("/")
        self._model = model

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> LlmResponse:
        """Send a chat completion request to Ollama."""
        url = f"{self._api_url}/api/chat"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

        logger.debug("ollama_llm_request", model=self._model, url=self._api_url)

        try:
            response = httpx.post(url, json=payload, timeout=_TIMEOUT_SECONDS)
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.error("ollama_llm_timeout", model=self._model, url=self._api_url)
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(
                "ollama_llm_http_error",
                status_code=exc.response.status_code,
                model=self._model,
                url=self._api_url,
            )
            raise

        data = response.json()
        message = data.get("message", {})
        content = message.get("content", "")

        # Ollama provides eval_count / prompt_eval_count
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
        }

        logger.info(
            "ollama_llm_response",
            model=data.get("model", self._model),
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
        )

        return LlmResponse(
            content=content,
            model=data.get("model", self._model),
            usage=usage,
        )
