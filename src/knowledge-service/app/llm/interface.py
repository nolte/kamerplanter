"""Abstract interface for LLM adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class LlmResponse:
    """Response from an LLM generation call."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)


class ILlmAdapter(ABC):
    """Interface for LLM providers."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> LlmResponse:
        """Generate a completion from the LLM.

        Args:
            system_prompt: System-level instruction for the LLM.
            user_message: The user query with optional context.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0.0 = deterministic).

        Returns:
            LlmResponse with content, model name, and token usage.
        """
        ...
