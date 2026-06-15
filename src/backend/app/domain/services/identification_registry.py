"""REQ-029 §3.4 / REQ-029-A §0.1.1 point 1 — identification adapter registry.

Analogous to the REQ-011 ``AdapterRegistry`` but for image-based services.
The preferred adapter is resolved from configuration
(``IDENTIFICATION_PRIMARY_ADAPTER``, Phase-1 default ``"plantnet"``) — never
hard-coded. Switching to Phase 2 means registering ``LocalEmbeddingAdapter``
and setting that key as primary; no engine/service/API change.
"""

import structlog

from app.config.settings import settings
from app.domain.interfaces.plant_identification_adapter import PlantIdentificationAdapter

logger = structlog.get_logger()


class IdentificationAdapterRegistry:
    """Registry of plant-identification adapters with config-driven priority."""

    _adapters: dict[str, PlantIdentificationAdapter] = {}

    @classmethod
    def register(cls, adapter_cls: type[PlantIdentificationAdapter]) -> type[PlantIdentificationAdapter]:
        """Class decorator that registers an adapter instance under its key."""
        instance = adapter_cls()
        key = instance.adapter_key
        if not key:
            raise ValueError(f"Adapter {adapter_cls.__name__} must define a non-empty 'adapter_key'.")
        cls._adapters[key] = instance
        return adapter_cls

    @classmethod
    def get(cls, adapter_key: str) -> PlantIdentificationAdapter:
        adapter = cls._adapters.get(adapter_key)
        if adapter is None:
            raise KeyError(f"Unknown identification adapter '{adapter_key}'. Available: {list(cls._adapters.keys())}")
        return adapter

    @classmethod
    def get_available(cls) -> list[PlantIdentificationAdapter]:
        """Return all registered adapters that are configured (have credentials)."""
        return [adapter for adapter in cls._adapters.values() if adapter.is_configured()]

    @classmethod
    def get_preferred(cls) -> PlantIdentificationAdapter | None:
        """Return the configured preferred adapter, falling back by availability.

        Resolution order (REQ-029-A §0.1.1 point 1):
        1. ``IDENTIFICATION_PRIMARY_ADAPTER`` if it is registered and configured.
        2. Otherwise the first other configured adapter (graceful degradation).
        3. ``None`` when nothing is configured (feature disabled).
        """
        primary_key = settings.identification_primary_adapter
        primary = cls._adapters.get(primary_key)
        if primary is not None and primary.is_configured():
            return primary

        available = cls.get_available()
        if not available:
            return None

        if primary is not None and not primary.is_configured():
            logger.info(
                "identification_primary_adapter_unconfigured",
                primary=primary_key,
                fallback=available[0].adapter_key,
            )
        return available[0]

    @classmethod
    def all_keys(cls) -> list[str]:
        return list(cls._adapters.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters (for testing)."""
        cls._adapters = {}
