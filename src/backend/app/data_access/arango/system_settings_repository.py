from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.interfaces.pest_prototype_store import IPestPrototypeContributionMarker
from app.domain.interfaces.reference_contribution_marker import IReferenceContributionMarker
from app.domain.models.system_settings import SystemSettings

SINGLETON_KEY = "default"

#: #1753 — set the contribution marker on the singleton, touching only that
#: field and only when it is unset. One statement, so two first contributions
#: racing each other cannot interleave a read and a write, and a concurrent
#: admin save of the other settings is not overwritten.
_RECORD_CONTRIBUTIONS_QUERY = """
UPSERT { _key: @key }
INSERT { _key: @key, reference_contributions_since: @now, created_at: @now, updated_at: @now }
UPDATE {
  reference_contributions_since: OLD.reference_contributions_since == null
    ? @now : OLD.reference_contributions_since
}
IN @@collection
"""


#: #1759 — the same statement for the pest-prototype marker.
_RECORD_PEST_PROTOTYPES_QUERY = """
UPSERT { _key: @key }
INSERT { _key: @key, pest_prototype_contributions_since: @now, created_at: @now, updated_at: @now }
UPDATE {
  pest_prototype_contributions_since: OLD.pest_prototype_contributions_since == null
    ? @now : OLD.pest_prototype_contributions_since
}
IN @@collection
"""


class ArangoSystemSettingsRepository(IReferenceContributionMarker, IPestPrototypeContributionMarker):
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

    def record_reference_contributions(self, now: datetime) -> None:
        if self.reference_contributions_since() is not None:
            # The common case: one cheap read, no write per contribution.
            return
        self._db.aql.execute(
            _RECORD_CONTRIBUTIONS_QUERY,
            bind_vars={"@collection": col.SYSTEM_SETTINGS, "key": SINGLETON_KEY, "now": now.isoformat()},
        )

    def reference_contributions_since(self) -> datetime | None:
        settings = self.get()
        return settings.reference_contributions_since if settings is not None else None

    def record_pest_prototype_contributions(self, now: datetime) -> None:
        if self.pest_prototype_contributions_since() is not None:
            return
        self._db.aql.execute(
            _RECORD_PEST_PROTOTYPES_QUERY,
            bind_vars={"@collection": col.SYSTEM_SETTINGS, "key": SINGLETON_KEY, "now": now.isoformat()},
        )

    def pest_prototype_contributions_since(self) -> datetime | None:
        settings = self.get()
        return settings.pest_prototype_contributions_since if settings is not None else None

    def delete_settings(self) -> bool:
        existing = self.collection.get(SINGLETON_KEY)
        if not existing:
            return False
        self.collection.delete(SINGLETON_KEY)
        return True
