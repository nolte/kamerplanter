"""Seed location_types stammdaten on app startup (REQ-002)."""

from datetime import UTC, datetime

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def seed_location_types(db: StandardDatabase) -> None:
    """Ensure all system location types exist. Idempotent."""
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
            lt_col.insert(lt_data_copy)
            created += 1
    if created:
        logger.info("location_types_seeded", count=created)
