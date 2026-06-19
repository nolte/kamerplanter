from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.interfaces.ha_publish_repository import IHaPublishRepository
from app.domain.models.ha_publish_setting import HaPublishEntityType, HaPublishSetting


class ArangoHaPublishRepository(IHaPublishRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    @property
    def collection(self):  # type: ignore[no-untyped-def]
        return self._db.collection(col.HA_PUBLISH_SETTINGS)

    def get_for_entity(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType,
        entity_key: str,
    ) -> HaPublishSetting | None:
        query = f"""
        FOR doc IN {col.HA_PUBLISH_SETTINGS}
          FILTER doc.tenant_key == @tenant_key
            AND doc.entity_type == @entity_type
            AND doc.entity_key == @entity_key
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "tenant_key": tenant_key,
                "entity_type": entity_type.value,
                "entity_key": entity_key,
            },
        )
        doc = next(cursor, None)
        return HaPublishSetting(**doc) if doc else None

    def list_for_tenant(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType | None = None,
    ) -> list[HaPublishSetting]:
        bind_vars: dict[str, str] = {"tenant_key": tenant_key}
        type_filter = ""
        if entity_type is not None:
            type_filter = "AND doc.entity_type == @entity_type"
            bind_vars["entity_type"] = entity_type.value
        query = f"""
        FOR doc IN {col.HA_PUBLISH_SETTINGS}
          FILTER doc.tenant_key == @tenant_key {type_filter}
          SORT doc.entity_type, doc.entity_key
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [HaPublishSetting(**doc) for doc in cursor]

    def list_enabled_keys(
        self,
        tenant_key: str,
        entity_type: HaPublishEntityType,
    ) -> list[str]:
        query = f"""
        FOR doc IN {col.HA_PUBLISH_SETTINGS}
          FILTER doc.tenant_key == @tenant_key
            AND doc.entity_type == @entity_type
            AND doc.enabled == true
          SORT doc.entity_key
          RETURN doc.entity_key
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"tenant_key": tenant_key, "entity_type": entity_type.value},
        )
        return list(cursor)

    def upsert(self, setting: HaPublishSetting) -> HaPublishSetting:
        now = datetime.now(UTC).isoformat()
        existing = self.get_for_entity(setting.tenant_key, setting.entity_type, setting.entity_key)
        if existing is not None:
            result = self.collection.update(
                {"_key": existing.key, "enabled": setting.enabled, "updated_at": now},
                return_new=True,
            )
            return HaPublishSetting(**result["new"])

        data = setting.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        data["entity_type"] = setting.entity_type.value
        data["created_at"] = now
        data["updated_at"] = now
        result = self.collection.insert(data, return_new=True)
        return HaPublishSetting(**result["new"])
