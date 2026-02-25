from typing import TypeVar

from app.common.exceptions import AdapterNotFoundError
from app.domain.interfaces.external_source_adapter import ExternalSourceAdapter

T = TypeVar("T", bound=type[ExternalSourceAdapter])


class AdapterRegistry:
    _adapters: dict[str, ExternalSourceAdapter] = {}

    @classmethod
    def register(cls, adapter_cls: T) -> T:
        """Class decorator that registers an adapter instance."""
        instance = adapter_cls()
        cls._adapters[instance.source_key] = instance
        return adapter_cls

    @classmethod
    def get(cls, source_key: str) -> ExternalSourceAdapter:
        adapter = cls._adapters.get(source_key)
        if adapter is None:
            raise AdapterNotFoundError(source_key)
        return adapter

    @classmethod
    def all_keys(cls) -> list[str]:
        return list(cls._adapters.keys())

    @classmethod
    def all_adapters(cls) -> list[ExternalSourceAdapter]:
        return list(cls._adapters.values())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters (for testing)."""
        cls._adapters = {}
