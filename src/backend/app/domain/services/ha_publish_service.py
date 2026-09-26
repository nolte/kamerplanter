"""Home Assistant publish-selection service.

Lets a tenant choose which plants, tanks and locations are exported to Home
Assistant as sensors. The policy is **opt-in**: nothing is published until a
setting is created with ``enabled=True`` (see ``HaPublishSetting``).

The ``list_enabled_keys`` helper is the export-facing read a Home Assistant
coordinator polls to learn which entities it should surface.
"""

from typing import Any, Protocol

import structlog

from app.common.exceptions import NotFoundError
from app.domain.interfaces.ha_publish_repository import IHaPublishRepository
from app.domain.models.ha_publish_setting import HaPublishEntityType, HaPublishSetting
from app.domain.services.location_ownership import SiteAnchorSource, resolve_owned_location

logger = structlog.get_logger(__name__)


class _ByKey(Protocol):
    def get_by_key(self, key: str) -> Any: ...


_ENTITY_NAMES = {
    HaPublishEntityType.PLANT: "PlantInstance",
    HaPublishEntityType.TANK: "Tank",
    HaPublishEntityType.LOCATION: "Location",
}


class HaPublishService:
    def __init__(
        self,
        repo: IHaPublishRepository,
        *,
        plant_repo: _ByKey | None = None,
        tank_repo: _ByKey | None = None,
        site_anchors: SiteAnchorSource | None = None,
    ) -> None:
        self._repo = repo
        # #1872 C8: the entity a setting names, resolved under the tenant.
        self._plant_repo = plant_repo
        self._tank_repo = tank_repo
        self._site_anchors = site_anchors

    def _require_owned_entity(self, tenant_key: str, entity_type: HaPublishEntityType, entity_key: str) -> None:
        """404 unless *entity_key* is a plant, tank or location of *tenant_key* (#1872 C8).

        The upsert stored any key, and a foreign one then showed up in the
        tenant's own ``enabled-keys`` list. Fails closed without the collaborator.
        """
        name = _ENTITY_NAMES[entity_type]
        if not tenant_key:
            raise NotFoundError(name, entity_key)
        if entity_type == HaPublishEntityType.LOCATION:
            if self._site_anchors is None:
                raise NotFoundError(name, entity_key)
            resolve_owned_location(self._site_anchors, entity_key, tenant_key)
            return
        source = self._plant_repo if entity_type == HaPublishEntityType.PLANT else self._tank_repo
        entity = source.get_by_key(entity_key) if source is not None else None
        if entity is None or getattr(entity, "tenant_key", None) != tenant_key:
            raise NotFoundError(name, entity_key)

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
        # Switching off a setting the tenant already has needs no resolution
        # (/code-review of #1899): a row stored before #1872 — or whose entity was
        # deleted since — must stay switchable off, or it would sit in the
        # enabled-keys list for good.
        if enabled or self._repo.get_for_entity(tenant_key, entity_type, entity_key) is None:
            self._require_owned_entity(tenant_key, entity_type, entity_key)
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
        # Every key before the first write: a foreign key refuses the whole batch
        # (switching off an existing setting excepted, as in ``set_published``).
        for entity_key, enabled in entries.items():
            if enabled or self._repo.get_for_entity(tenant_key, entity_type, entity_key) is None:
                self._require_owned_entity(tenant_key, entity_type, entity_key)
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
