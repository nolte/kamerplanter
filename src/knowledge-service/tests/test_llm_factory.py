"""#2176: the LLM adapter factory picks the cloud adapter only when it is named.

``LLM_PROVIDER`` is the only switch that decides which LLM answers (REQ-027
§6.1.1). An unknown value used to fall through to the Anthropic adapter, so a
typo such as ``openai-compatible`` sent every question — together with a key
meant for a local server — to a cloud API. An unknown value now stops the start.
"""

import pytest

from app.config import Settings
from app.llm import create_llm_adapter
from app.llm.anthropic import AnthropicLlmAdapter
from app.llm.ollama import OllamaLlmAdapter
from app.llm.openai_compatible import OpenAiCompatibleLlmAdapter


def _settings(provider: str) -> Settings:
    return Settings(llm_provider=provider, llm_api_url="http://localhost:1234", llm_api_key="local-key")


class TestKnownProviders:
    def test_ollama_builds_the_ollama_adapter(self):
        assert isinstance(create_llm_adapter(_settings("ollama")), OllamaLlmAdapter)

    def test_openai_compatible_builds_the_openai_compatible_adapter(self):
        assert isinstance(create_llm_adapter(_settings("openai_compatible")), OpenAiCompatibleLlmAdapter)

    def test_anthropic_builds_the_anthropic_adapter(self):
        assert isinstance(create_llm_adapter(_settings("anthropic")), AnthropicLlmAdapter)


class TestUnknownProvider:
    @pytest.mark.parametrize("provider", ["openai-compatible", "Ollama", "claude", ""])
    def test_an_unknown_provider_is_refused_instead_of_falling_back_to_the_cloud(self, provider):
        with pytest.raises(ValueError, match="LLM_PROVIDER"):
            create_llm_adapter(_settings(provider))
