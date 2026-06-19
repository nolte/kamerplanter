from abc import ABC, abstractmethod

from app.domain.models.ha_publish_setting import HaPublishEntityType, HaPublishSetting


class IHaPublishRepository(ABC):
    @abstractmethod
    def get_for_entity(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType,
        entity_key: str,
    ) -> HaPublishSetting | None: ...

    @abstractmethod
    def list_for_tenant(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType | None = None,
    ) -> list[HaPublishSetting]: ...

    @abstractmethod
    def list_enabled_keys(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType,
    ) -> list[str]: ...

    @abstractmethod
    def upsert(self, setting: HaPublishSetting) -> HaPublishSetting: ...
