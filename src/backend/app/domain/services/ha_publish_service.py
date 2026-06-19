"""Home Assistant publish-selection service.

Lets a tenant choose which plants, tanks and locations are exported to Home
Assistant as sensors. The policy is **opt-in**: nothing is published until a
setting is created with ``enabled=True`` (see ``HaPublishSetting``).

The ``list_enabled_keys`` helper is the export-facing read a Home Assistant
coordinator polls to learn which entities it should surface.
"""

import structlog

from app.domain.interfaces.ha_publish_repository import IHaPublishRepository
from app.domain.models.ha_publish_setting import HaPublishEntityType, HaPublishSetting

logger = structlog.get_logger(__name__)


class HaPublishService:
    def __init__(self, repo: IHaPublishRepository) -> None:
        self._repo = repo

    def list_settings(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType | None = None,
    ) -> list[HaPublishSetting]:
        return self._repo.list_for_tenant(tenant_key, entity_type)

    def is_published(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType,
        entity_key: str,
    ) -> bool:
        """Opt-in: True only when an enabled setting exists for the entity."""
        setting = self._repo.get_for_entity(tenant_key, entity_type, entity_key)
        return bool(setting and setting.enabled)

    def set_published(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType,
        entity_key: str,
        enabled: bool,
    ) -> HaPublishSetting:
        setting = self._repo.upsert(
            HaPublishSetting(
                tenant_key=tenant_key,
                entity_type=entity_type,
                entity_key=entity_key,
                enabled=enabled,
            )
        )
        logger.info(
            "ha_publish_setting_updated",
            tenant_key=tenant_key,
            entity_type=entity_type.value,
            entity_key=entity_key,
            enabled=enabled,
        )
        return setting

    def bulk_set_published(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType,
        entries: dict[str, bool],
    ) -> list[HaPublishSetting]:
        return [
            self.set_published(tenant_key, entity_type, entity_key, enabled) for entity_key, enabled in entries.items()
        ]

    def list_enabled_keys(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType,
    ) -> list[str]:
        """Entity keys a Home Assistant coordinator should publish."""
        return self._repo.list_enabled_keys(tenant_key, entity_type)
