"""LLM adapter factory."""

from app.config import Settings
from app.llm.interface import ILlmAdapter

#: The values of ``LLM_PROVIDER`` this factory dispatches on (#2176).
KNOWN_LLM_PROVIDERS: frozenset[str] = frozenset({"ollama", "openai_compatible", "anthropic"})


def create_llm_adapter(settings: Settings) -> ILlmAdapter:
    """Create the appropriate LLM adapter based on settings.

    Raises:
        ValueError: ``LLM_PROVIDER`` names none of :data:`KNOWN_LLM_PROVIDERS`.
            Called from the lifespan, so the service does not start.
    """
    provider = settings.llm_provider

    if provider == "ollama":
        from app.llm.ollama import OllamaLlmAdapter

        return OllamaLlmAdapter(
            api_url=settings.llm_api_url or "http://ollama:11434",
            model=settings.llm_model,
        )
    elif provider == "openai_compatible":
        from app.llm.openai_compatible import OpenAiCompatibleLlmAdapter

        return OpenAiCompatibleLlmAdapter(
            api_url=settings.llm_api_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    elif provider == "anthropic":
        from app.llm.anthropic import AnthropicLlmAdapter

        return AnthropicLlmAdapter(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
    # #2176: an unknown value used to fall through to the Anthropic adapter, so a
    # typo silently sent every question to a cloud API. Refuse to start instead.
    msg = f"Unknown LLM_PROVIDER {provider!r}; expected one of {sorted(KNOWN_LLM_PROVIDERS)}."
    raise ValueError(msg)
