"""Seed data for REQ-020 Onboarding Starter Kits.

All data is loaded from seed_data/starter_kits.yaml.
"""

import structlog

from app.common.dependencies import get_db
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.starter_kit import StarterKit
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def run_seed_starter_kits() -> None:
    """Seed starter kits into the database. Idempotent."""
    db = get_db()
    repo = BaseArangoRepository(db, col.STARTER_KITS)
    data = load_yaml("starter_kits.yaml")

    # Build species scientific_name → _key map from DB
    species_col = db.collection(col.SPECIES)
    species_key_map: dict[str, str] = {}
    for doc in species_col.all():
        species_key_map[doc["scientific_name"]] = doc["_key"]

    kits = data.get("starter_kits", [])
    created = 0
    updated = 0

    for kit_data in kits:
        # Resolve species_names to species_keys
        species_names = kit_data.pop("species_names", [])
        resolved_keys = [species_key_map[n] for n in species_names if n in species_key_map]
        kit_data["species_keys"] = resolved_keys

        for name in species_names:
            if name not in species_key_map:
                logger.warning("species_not_found_for_kit", name=name, kit=kit_data["kit_id"])

        existing = repo.find_by_field("kit_id", kit_data["kit_id"])
        if not existing:
            kit = StarterKit(**kit_data)
            repo.create(kit)
            created += 1
            logger.info("starter_kit_created", kit_id=kit_data["kit_id"], species=len(resolved_keys))
        else:
            # Update species_keys if changed
            existing_doc = existing[0]
            if existing_doc.get("species_keys", []) != resolved_keys:
                db.collection(col.STARTER_KITS).update(
                    {"_key": existing_doc["_key"], "species_keys": resolved_keys}
                )
                updated += 1
                logger.info(
                    "starter_kit_species_updated",
                    kit_id=kit_data["kit_id"],
                    species=len(resolved_keys),
                )

    if created or updated:
        logger.info("starter_kits_seeded", created=created, updated=updated, total=len(kits))
