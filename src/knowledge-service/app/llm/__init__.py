"""LLM adapter factory."""

from app.config import Settings
from app.llm.interface import ILlmAdapter


def create_llm_adapter(settings: Settings) -> ILlmAdapter:
    """Create the appropriate LLM adapter based on settings."""
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
    else:
        from app.llm.anthropic import AnthropicLlmAdapter

        return AnthropicLlmAdapter(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
        )
