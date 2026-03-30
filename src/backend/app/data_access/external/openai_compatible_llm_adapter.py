"""OpenAI-compatible API adapter — works with vLLM, LM Studio, llama.cpp, OpenAI, etc."""

import httpx
import structlog

from app.domain.interfaces.llm_adapter import ILlmAdapter, LlmResponse

logger = structlog.get_logger(__name__)

_TIMEOUT_SECONDS = 120.0


class OpenAiCompatibleLlmAdapter(ILlmAdapter):
    """Calls any OpenAI-compatible /v1/chat/completions endpoint via httpx."""

    def __init__(
        self,
        api_url: str,
        api_key: str = "",
        model: str = "gpt-4o-mini",
    ) -> None:
        self._api_url = api_url.rstrip("/")
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
        """Send a chat completion request to an OpenAI-compatible API."""
        url = f"{self._api_url}/v1/chat/completions"
        headers: dict[str, str] = {"content-type": "application/json"}
        if self._api_key:
            headers["authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }

        logger.debug("openai_compat_llm_request", model=self._model, url=self._api_url)

        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=_TIMEOUT_SECONDS)
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.error("openai_compat_llm_timeout", model=self._model, url=self._api_url)
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(
                "openai_compat_llm_http_error",
                status_code=exc.response.status_code,
                model=self._model,
                url=self._api_url,
            )
            raise

        data = response.json()

        choices = data.get("choices", [])
        content = choices[0]["message"]["content"] if choices else ""

        usage_data = data.get("usage", {})
        usage = {
            "prompt_tokens": usage_data.get("prompt_tokens", 0),
            "completion_tokens": usage_data.get("completion_tokens", 0),
        }

        model_name = data.get("model", self._model)

        logger.info(
            "openai_compat_llm_response",
            model=model_name,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
        )

        return LlmResponse(
            content=content,
            model=model_name,
            usage=usage,
        )
