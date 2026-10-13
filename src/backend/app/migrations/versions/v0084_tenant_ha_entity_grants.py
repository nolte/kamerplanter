"""v0084 - MT-015 (#2112): the per-tenant Home Assistant entity allowlist, seeded from existing references.

Creates ``tenant_ha_entity_grants`` with its unique ``(tenant_key, entity_id)``
index on existing volumes, and **grants every Home Assistant entity a tenant
already references**, so the upgrade stops nothing that worked before it:

* sensors (``ha_entity_id``) - the tenant is the parent's: a tank's or a site's
  ``tenant_key``, or for a location its site's (a sensor and a location carry no
  ``tenant_key`` of their own);
* actuators (``tenant_key`` + ``ha_entity_id``);
* weather-source configurations (``tenant_key`` + each Home Assistant source's
  ``weather_entity_id`` and ``sensor_mapping.*``);
* Home Assistant notification destinations of an **enabled** channel
  (``notify.<service>`` - ``notify.notify`` when mobile push is on and no
  service is set, the send default - and ``tts_entity_id`` when TTS is on). A
  preference is per user, not per tenant, so these are granted to every tenant
  the user is an active member of: exactly the reach the destination had before.

Why a seed and not a lazy "grandfather" rule: a rule that admits ungranted
references made before a cut-off would keep the cross-tenant read alive forever
for exactly the rows the audit found, and nobody could see or withdraw it. A
seeded grant is an ordinary row the platform admin sees in the panel (``source:
migration``) and can withdraw.

Only well-formed entity ids are seeded (``HA_ENTITY_ID_PATTERN``); a malformed one
was never readable by Home Assistant and is counted, not granted.

Fresh databases get the collection and index from the idempotent startup
``ensure_collections``, which runs before migrations; there is nothing to seed
there. Idempotent (M-3): the seed upserts on the unique pair, a re-run grants
nothing new (``changed == 0``). Irreversible (M-6): a seeded grant cannot be told
from one the admin confirmed later, so no inverse is offered.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.support.legacy_indexes import is_index_on

logger = structlog.get_logger()

#: Mirrors ``app.domain.models.ha_entity_grant.HA_ENTITY_ID_PATTERN`` - a migration
#: is frozen at its version, so it does not import the live pattern.
_ENTITY_ID_REGEX = "^[a-z0-9_]{1,64}[.][a-z0-9_]{1,191}$"

#: Every ``(tenant_key, entity_id)`` pair referenced today. Parametrised AQL only.
_REFERENCES_AQL = """
LET sensor_refs = (
  FOR s IN @@sensors
    FILTER s.ha_entity_id != null AND s.ha_entity_id != ""
    LET tank_tenant = s.tank_key ? DOCUMENT(@@tanks, s.tank_key).tenant_key : null
    LET site_tenant = s.site_key ? DOCUMENT(@@sites, s.site_key).tenant_key : null
    LET location = s.location_key ? DOCUMENT(@@locations, s.location_key) : null
    LET location_tenant = location ? DOCUMENT(@@sites, location.site_key).tenant_key : null
    RETURN { tenant_key: FIRST([tank_tenant, site_tenant, location_tenant][* FILTER CURRENT != null]),
             entity_id: s.ha_entity_id }
)
LET actuator_refs = (
  FOR a IN @@actuators
    FILTER a.ha_entity_id != null AND a.ha_entity_id != ""
    RETURN { tenant_key: a.tenant_key, entity_id: a.ha_entity_id }
)
LET weather_refs = FLATTEN(
  FOR c IN @@weather_configs
    FOR src IN (c.sources || [])
      FILTER src.kind == "home_assistant" AND IS_OBJECT(src.config)
      LET mapping = IS_OBJECT(src.config.sensor_mapping) ? VALUES(src.config.sensor_mapping) : []
      RETURN (
        FOR entity_id IN APPEND([src.config.weather_entity_id], mapping)
          FILTER entity_id != null AND entity_id != ""
          RETURN { tenant_key: c.tenant_key, entity_id: entity_id }
      )
)
LET notify_refs = FLATTEN(
  FOR p IN @@preferences
    LET ha = p.channels.home_assistant
    FILTER IS_OBJECT(ha) AND ha.enabled == true
    LET cfg = IS_OBJECT(ha.config) ? ha.config : {}
    LET notify_value = (cfg.notify_service != null AND cfg.notify_service != "")
        ? cfg.notify_service
        : (cfg.mobile_push != false ? "notify" : null)
    LET notify_id = notify_value == null ? null
        : (STARTS_WITH(notify_value, "notify.") ? notify_value : CONCAT("notify.", notify_value))
    LET tts_id = (cfg.tts_enabled == true AND cfg.tts_entity_id != null AND cfg.tts_entity_id != "")
        ? cfg.tts_entity_id : null
    LET destinations = [notify_id, tts_id][* FILTER CURRENT != null]
    FILTER LENGTH(destinations) > 0
    RETURN (
      FOR m IN @@memberships
        FILTER m.user_key == p.user_key AND m.is_active != false
        FOR entity_id IN destinations
          RETURN { tenant_key: m.tenant_key, entity_id: entity_id }
    )
)
FOR ref IN UNION(sensor_refs, actuator_refs, weather_refs, notify_refs)
  FILTER ref.tenant_key != null AND ref.tenant_key != ""
  COLLECT tenant_key = ref.tenant_key, entity_id = ref.entity_id
  RETURN { tenant_key, entity_id, well_formed: IS_STRING(entity_id) AND REGEX_TEST(entity_id, @entity_regex) }
"""

_SEED_AQL = """
FOR ref IN @refs
  UPSERT { tenant_key: ref.tenant_key, entity_id: ref.entity_id }
  INSERT { tenant_key: ref.tenant_key, entity_id: ref.entity_id, source: "migration", created_at: @now }
  UPDATE {}
  IN @@grants
  RETURN OLD ? 0 : 1
"""

#: The collections a reference can live in; a volume without one has nothing there.
_SOURCES = {
    "@sensors": col.SENSORS,
    "@tanks": col.TANKS,
    "@sites": col.SITES,
    "@locations": col.LOCATIONS,
    "@actuators": col.ACTUATORS,
    "@weather_configs": col.WEATHER_SOURCE_CONFIGS,
    "@preferences": col.NOTIFICATION_PREFERENCES,
    "@memberships": col.MEMBERSHIPS,
}


def _has_identity_index(indexes: object) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(isinstance(idx, dict) and is_index_on(idx, col.HA_ENTITY_GRANT_IDENTITY_FIELDS) for idx in indexes)


class TenantHaEntityGrantsMigration(Migration):
    version = "0084"
    name = "tenant_ha_entity_grants"
    description = (
        "Create the MT-015 tenant_ha_entity_grants collection and grant every Home Assistant entity "
        "a tenant already references (sensors, actuators, weather sources, HA notification destinations)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        collection_missing = not db.has_collection(col.TENANT_HA_ENTITY_GRANTS)
        index_missing = collection_missing or not _has_identity_index(
            db.collection(col.TENANT_HA_ENTITY_GRANTS).indexes()
        )

        references = self._references(db)
        well_formed = [
            {"tenant_key": r["tenant_key"], "entity_id": r["entity_id"]} for r in references if r["well_formed"]
        ]
        malformed = len(references) - len(well_formed)
        already = set() if collection_missing else self._existing(db)
        pending_grants = [r for r in well_formed if (r["tenant_key"], r["entity_id"]) not in already]

        details: dict[str, Any] = {
            "document_collections": [col.TENANT_HA_ENTITY_GRANTS] if collection_missing else [],
            "indexes": [f"{col.TENANT_HA_ENTITY_GRANTS}:{col.HA_ENTITY_GRANT_IDENTITY_FIELDS}"]
            if index_missing
            else [],
            "references": len(references),
            "malformed_not_granted": malformed,
            "grants_to_seed": len(pending_grants),
            "tenants": len({r["tenant_key"] for r in pending_grants}),
        }
        scanned = len(references) + 2

        if dry_run:
            logger.info("tenant_ha_entity_grants_migration_dry_run", **details)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=details
            )

        if collection_missing:
            db.create_collection(col.TENANT_HA_ENTITY_GRANTS)
        grants = db.collection(col.TENANT_HA_ENTITY_GRANTS)
        if not _has_identity_index(grants.indexes()):
            grants.add_persistent_index(fields=col.HA_ENTITY_GRANT_IDENTITY_FIELDS, unique=True)

        seeded = 0
        if pending_grants:
            cursor = cast(
                Cursor,
                db.aql.execute(
                    _SEED_AQL,
                    bind_vars={
                        "refs": pending_grants,
                        "now": datetime.now(UTC).isoformat(),
                        "@grants": col.TENANT_HA_ENTITY_GRANTS,
                    },
                ),
            )
            seeded = sum(int(created) for created in cursor)

        changed = int(collection_missing) + int(index_missing) + seeded
        details["grants_seeded"] = seeded
        # Counts only - an entity id names a device of somebody's household.
        logger.info("tenant_ha_entity_grants_migration_applied", changed=changed, **details)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=changed, dry_run=False, details=details
        )

    @staticmethod
    def _references(db: StandardDatabase) -> list[dict[str, Any]]:
        if not all(db.has_collection(name) for name in _SOURCES.values()):
            missing = [name for name in _SOURCES.values() if not db.has_collection(name)]
            logger.info("tenant_ha_entity_grants_migration_sources_missing", collections=missing)
            return []
        cursor = cast(
            Cursor,
            db.aql.execute(_REFERENCES_AQL, bind_vars={**_SOURCES, "entity_regex": _ENTITY_ID_REGEX}),
        )
        return list(cursor)

    @staticmethod
    def _existing(db: StandardDatabase) -> set[tuple[str, str]]:
        cursor = cast(
            Cursor,
            db.aql.execute(
                "FOR g IN @@grants RETURN [g.tenant_key, g.entity_id]",
                bind_vars={"@grants": col.TENANT_HA_ENTITY_GRANTS},
            ),
        )
        return {(str(t), str(e)) for t, e in cursor}


migration = TenantHaEntityGrantsMigration()
