"""Seed location_types stammdaten on app startup (REQ-002)."""

from datetime import UTC, datetime

import structlog
from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError

from app.data_access.arango import collections as col
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

#: ArangoDB "unique constraint violated": the key was inserted by someone else.
_ERR_UNIQUE_CONSTRAINT = 1210


def seed_location_types(db: StandardDatabase) -> None:
    """Ensure all system location types exist. Idempotent.

    The registry runs this under the migration lock (#2028), so two replicas no longer
    race here. The insert still reads a primary-key conflict as "exists" rather than a
    failure: this job is fatal, and a row another writer inserted between ``has`` and
    ``insert`` (a lock takeover, a manual run) must not abort a replica's startup.
    """
    data = load_yaml("location_types.yaml")
    lt_col = db.collection(col.LOCATION_TYPES)
    now = datetime.now(UTC).isoformat()
    created = 0
    for lt in data["location_types"]:
        lt_data = {
            "_key": lt["key"],
            "name": lt["name"],
            "name_en": lt["name_en"],
            "is_indoor": lt["is_indoor"],
            "icon": lt["icon"],
            "sort_order": lt["sort_order"],
            "is_system": True,
        }
        if not lt_col.has(lt_data["_key"]):
            lt_data_copy = {**lt_data, "created_at": now, "updated_at": now}
            try:
                lt_col.insert(lt_data_copy)
            except DocumentInsertError as exc:
                if exc.error_code != _ERR_UNIQUE_CONSTRAINT:
                    raise
                logger.info("location_type_exists", key=lt_data["_key"])
                continue
            created += 1
    if created:
        logger.info("location_types_seeded", count=created)
