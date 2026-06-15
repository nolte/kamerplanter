"""REQ-029 §3.4 — Registry for plant-identification adapters.

Analogous to ``AdapterRegistry`` (REQ-011) but for image-based services.
Adapters register themselves via the ``@IdentificationAdapterRegistry.register``
class decorator. Availability is key-based (an adapter is available when its
API key is configured); a future local adapter (WS-3) reports availability
without an API key and can be registered as priority 1.
"""

from typing import ClassVar

from app.config.settings import settings
from app.domain.interfaces.plant_identification_adapter import PlantIdentificationAdapter


class IdentificationAdapterRegistry:
    """Class-level registry of plant-identification adapter classes."""

    # Insertion order defines priority; the configured primary adapter wins.
    _adapters: ClassVar[dict[str, type[PlantIdentificationAdapter]]] = {}

    @classmethod
    def register(
        cls,
        adapter_cls: type[PlantIdentificationAdapter],
    ) -> type[PlantIdentificationAdapter]:
        """Class decorator that registers an adapter by its ``adapter_key``."""
        key = adapter_cls.adapter_key
        if isinstance(key, property):
            raise ValueError("adapter_key must be a class attribute, not a property")
        cls._adapters[key] = adapter_cls
        return adapter_cls

    @classmethod
    def get(cls, adapter_key: str) -> PlantIdentificationAdapter:
        """Instantiate a registered adapter by key."""
        adapter_cls = cls._adapters.get(adapter_key)
        if adapter_cls is None:
            raise KeyError(f"Unknown identification adapter '{adapter_key}'. Available: {list(cls._adapters.keys())}")
        return adapter_cls()

    @classmethod
    def get_available(cls) -> list[PlantIdentificationAdapter]:
        """Return instances of all adapters that report themselves available.

        An adapter is available when it has no configurable API key (e.g. a
        self-hosted local adapter) or when its key is set.
        """
        available: list[PlantIdentificationAdapter] = []
        for adapter_cls in cls._adapters.values():
            instance = adapter_cls()
            if cls._is_available(instance):
                available.append(instance)
        return available

    @classmethod
    def get_preferred(cls) -> PlantIdentificationAdapter | None:
        """Return the preferred available adapter.

        Selection order:
        1. ``IDENTIFICATION_PRIMARY_ADAPTER`` setting, if available.
        2. First available adapter in registration order.
        """
        available = cls.get_available()
        if not available:
            return None

        primary_key = settings.identification_primary_adapter
        if primary_key:
            for adapter in available:
                if adapter.adapter_key == primary_key:
                    return adapter

        return available[0]

    @classmethod
    def get_fallback_chain(cls) -> list[PlantIdentificationAdapter]:
        """Return all available adapters ordered with the preferred one first.

        Used by the service to attempt the next adapter when confidence is
        below the configured threshold.
        """
        available = cls.get_available()
        if not available:
            return []

        preferred = cls.get_preferred()
        if preferred is None:
            return available

        chain = [preferred]
        chain.extend(a for a in available if a.adapter_key != preferred.adapter_key)
        return chain

    @classmethod
    def all_keys(cls) -> list[str]:
        """Return the keys of all registered adapters."""
        return list(cls._adapters.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters (for testing)."""
        cls._adapters = {}

    @staticmethod
    def _is_available(instance: PlantIdentificationAdapter) -> bool:
        """An adapter is available if it requires no key or its key is set."""
        api_key = getattr(instance, "_api_key", "sentinel-no-key-required")
        return bool(api_key)
