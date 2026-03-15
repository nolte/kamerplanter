from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.data_access.arango import collections as col
from app.domain.models.system_settings import SystemSettings

if TYPE_CHECKING:
    from arango.database import StandardDatabase

SINGLETON_KEY = "default"


class ArangoSystemSettingsRepository:
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    @property
    def collection(self):  # type: ignore[no-untyped-def]
        return self._db.collection(col.SYSTEM_SETTINGS)

    def get(self) -> SystemSettings | None:
        doc = self.collection.get(SINGLETON_KEY)
        if doc is None:
            return None
        return SystemSettings(**doc)

    def upsert(self, settings: SystemSettings) -> SystemSettings:
        now = datetime.now(UTC).isoformat()
        data = settings.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        data["updated_at"] = now

        existing = self.collection.get(SINGLETON_KEY)
        if existing:
            result = self.collection.update({"_key": SINGLETON_KEY, **data}, return_new=True)
        else:
            data["_key"] = SINGLETON_KEY
            data["created_at"] = now
            result = self.collection.insert(data, return_new=True)

        return SystemSettings(**result["new"])

    def delete_settings(self) -> bool:
        existing = self.collection.get(SINGLETON_KEY)
        if not existing:
            return False
        self.collection.delete(SINGLETON_KEY)
        return True
