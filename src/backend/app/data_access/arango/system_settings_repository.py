from collections.abc import Iterable
from datetime import UTC, datetime
from typing import cast

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.interfaces.pest_prototype_store import IPestPrototypeContributionMarker, IPestPrototypeOrphanSweepLog
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

#: #1771 — record one orphan-sweep run on the singleton, touching only that
#: field, so a concurrent admin save of the other settings is not overwritten.
_RECORD_ORPHAN_SWEEP_QUERY = """
LET run = {
  last_run_at: @now, last_examined: @examined, last_orphaned: @orphaned,
  last_removed: @removed, binding: @binding
}
UPSERT { _key: @key }
INSERT {
  _key: @key, created_at: @now, updated_at: @now,
  pest_prototype_orphan_sweep: MERGE(run, { first_run_at: @now, total_removed: @removed })
}
UPDATE {
  pest_prototype_orphan_sweep: MERGE(run, {
    first_run_at: OLD.pest_prototype_orphan_sweep.first_run_at || @now,
    total_removed: (OLD.pest_prototype_orphan_sweep.total_removed || 0) + @removed
  })
}
IN @@collection
"""


#: #2113 — replace one secret stored in clear (under its ``_encrypted`` name or
#: the legacy plaintext name) by its ciphertext, only while it still holds that
#: plaintext. ``keepNull: false`` removes the legacy attribute.
_REPLACE_PLAINTEXT_SECRET_QUERY = """
FOR doc IN @@collection
  FILTER doc._key == @key
  LET current = doc[@block][@field] != null ? doc[@block][@field] : doc[@block][@legacy]
  FILTER current == @plaintext
  UPDATE doc WITH { [@block]: { [@field]: @ciphertext, [@legacy]: null } } IN @@collection
    OPTIONS { keepNull: false, mergeObjects: true }
  RETURN true
"""


#: Fields only their own single-statement writers set. ``upsert`` is the admin
#: settings' read-modify-write; carrying these back would reset a run the sweep
#: recorded between the read and the write (code review of #1771).
_SELF_WRITTEN_FIELDS = ("pest_prototype_orphan_sweep",)


class ArangoSystemSettingsRepository(
    IReferenceContributionMarker, IPestPrototypeContributionMarker, IPestPrototypeOrphanSweepLog
):
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
        for field in _SELF_WRITTEN_FIELDS:
            data.pop(field, None)
        data["updated_at"] = now

        existing = self.collection.get(SINGLETON_KEY)
        if existing:
            # ``merge=False`` (#2113): a settings block is written whole. With the
            # default merge, ``exclude_none`` dropped a cleared field from the
            # payload and the stored value survived — ``delete_ha_settings`` left
            # the HA token in the document and ``delete_global_openweathermap_key``
            # the OWM ciphertext, both answering success (measured 2026-10-05). It
            # also removes a legacy plaintext key (``ha_access_token``) the model
            # no longer carries. Top-level fields not in the payload (the
            # self-written ones above) are untouched: merge concerns nested objects.
            result = self.collection.update({"_key": SINGLETON_KEY, **data}, return_new=True, merge=False)
        else:
            data["_key"] = SINGLETON_KEY
            data["created_at"] = now
            result = self.collection.insert(data, return_new=True)

        return SystemSettings(**result["new"])

    def replace_plaintext_secret(
        self, *, block: str, field: str, legacy_field: str, plaintext: str, ciphertext: str
    ) -> bool:
        """Swap one secret stored in clear for its ciphertext — only if it is still that value (#2113).

        The lazy re-encryption on read. One conditional statement rather than a
        read-modify-write ``upsert``: it touches ``<block>.<field>`` and removes
        ``<block>.<legacy_field>``, nothing else, so a concurrent admin save of
        any other setting is not overwritten, and a save of *this* secret between
        the read and the write wins (the condition no longer matches). Returns
        whether it wrote.
        """
        cursor = self._db.aql.execute(
            _REPLACE_PLAINTEXT_SECRET_QUERY,
            bind_vars={
                "@collection": col.SYSTEM_SETTINGS,
                "key": SINGLETON_KEY,
                "block": block,
                "field": field,
                "legacy": legacy_field,
                "plaintext": plaintext,
                "ciphertext": ciphertext,
            },
        )
        return any(cast(Iterable[bool], cursor))

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

    def record_pest_prototype_orphan_sweep(
        self, *, now: datetime, examined: int, orphaned: int, removed: int, binding: str
    ) -> None:
        self._db.aql.execute(
            _RECORD_ORPHAN_SWEEP_QUERY,
            bind_vars={
                "@collection": col.SYSTEM_SETTINGS,
                "key": SINGLETON_KEY,
                "now": now.isoformat(),
                "examined": examined,
                "orphaned": orphaned,
                "removed": removed,
                "binding": binding,
            },
        )

    def delete_settings(self) -> bool:
        existing = self.collection.get(SINGLETON_KEY)
        if not existing:
            return False
        self.collection.delete(SINGLETON_KEY)
        return True
