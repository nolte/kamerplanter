"""Anthropic Messages API adapter — uses httpx, no SDK dependency."""

import httpx
import structlog

from app.domain.interfaces.llm_adapter import ILlmAdapter, LlmResponse

logger = structlog.get_logger(__name__)

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
_TIMEOUT_SECONDS = 120.0


class AnthropicLlmAdapter(ILlmAdapter):
    """Calls the Anthropic Messages API via httpx."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self._api_key = api_key
        self._model = model

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> LlmResponse:
        """Send a request to the Anthropic Messages API."""
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }

        logger.debug("anthropic_llm_request", model=self._model)

        try:
            response = httpx.post(
                _ANTHROPIC_API_URL,
                headers=headers,
                json=payload,
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.error("anthropic_llm_timeout", model=self._model)
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(
                "anthropic_llm_http_error",
                status_code=exc.response.status_code,
                model=self._model,
            )
            raise

        data = response.json()

        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block["text"]

        usage_data = data.get("usage", {})
        usage = {
            "prompt_tokens": usage_data.get("input_tokens", 0),
            "completion_tokens": usage_data.get("output_tokens", 0),
        }

        logger.info(
            "anthropic_llm_response",
            model=data.get("model", self._model),
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
        )

        return LlmResponse(
            content=content,
            model=data.get("model", self._model),
            usage=usage,
        )
