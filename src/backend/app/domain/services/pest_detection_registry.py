"""REQ-044 §4.2 — pest-detection adapter registry (config-driven priority).

Analogous to the REQ-029 ``IdentificationAdapterRegistry``. The preferred
adapter is resolved from ``PEST_DETECTION_PRIMARY_ADAPTER`` (default
``"local_pest_symptom"``) — never hard-coded. Self-hosted is the default; the
Cloud adapter is opt-in (§3.3). When nothing is configured the feature is simply
unavailable and the app stays fully functional (§9.1).
"""

import structlog

from app.config.settings import settings
from app.domain.interfaces.pest_detection_adapter import PestDetectionAdapter

logger = structlog.get_logger()


class PestDetectionAdapterRegistry:
    """Registry of pest-detection adapters with config-driven priority."""

    _adapters: dict[str, PestDetectionAdapter] = {}

    @classmethod
    def register(cls, adapter_cls: type[PestDetectionAdapter]) -> type[PestDetectionAdapter]:
        """Class decorator that registers an adapter instance under its key."""
        instance = adapter_cls()
        key = instance.adapter_key
        if not key:
            raise ValueError(f"Adapter {adapter_cls.__name__} must define a non-empty 'adapter_key'.")
        cls._adapters[key] = instance
        return adapter_cls

    @classmethod
    def get(cls, adapter_key: str) -> PestDetectionAdapter:
        adapter = cls._adapters.get(adapter_key)
        if adapter is None:
            raise KeyError(f"Unknown pest-detection adapter '{adapter_key}'. Available: {list(cls._adapters.keys())}")
        return adapter

    @classmethod
    def get_available(cls) -> list[PestDetectionAdapter]:
        """Return all registered adapters that are configured and enabled."""
        if not settings.pest_detection_enabled:
            return []
        return [adapter for adapter in cls._adapters.values() if adapter.is_configured()]

    @classmethod
    def get_preferred(cls) -> PestDetectionAdapter | None:
        """Return the configured preferred adapter, falling back by availability.

        1. ``PEST_DETECTION_PRIMARY_ADAPTER`` if registered and configured.
        2. Otherwise the first other configured adapter (graceful degradation).
        3. ``None`` when nothing is configured (feature disabled).
        """
        if not settings.pest_detection_enabled:
            return None

        primary_key = settings.pest_detection_primary_adapter
        primary = cls._adapters.get(primary_key)
        if primary is not None and primary.is_configured():
            return primary

        available = cls.get_available()
        if not available:
            return None

        if primary is not None and not primary.is_configured():
            logger.info(
                "pest_detection_primary_adapter_unconfigured",
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
