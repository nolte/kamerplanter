"""Seed species-level overwintering *templates* (REQ-022 §OverwinteringProfile).

Loads ``seed_data/overwintering_profiles.yaml`` — generated from the plant
Steckbriefe (§4.3 Überwinterung) by ``scripts/extract_overwintering_templates.py`` —
into the ``overwintering_profile_templates`` collection. Each template is keyed by
the species slug (idempotent upsert) and, where the species is already seeded, linked
via ``species_key``.

Unlike the per-instance ``OverwinteringProfile`` these are reference data: not
tenant-scoped and consulted so that instance-profile auto-generation can start from
species-accurate values instead of generic traffic-light defaults.
"""

import structlog

from app.common.dependencies import get_db, get_species_repo
from app.data_access.arango import collections as col
from app.domain.models.overwintering_profile_template import OverwinteringProfileTemplate
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def run_seed_overwintering_profiles() -> None:
    """Upsert overwintering-profile templates from YAML seed data (idempotent)."""
    data = load_yaml("overwintering_profiles.yaml")
    entries = data.get("overwintering_profiles", [])

    species_repo = get_species_repo()
    collection = get_db().collection(col.OVERWINTERING_PROFILE_TEMPLATES)

    created = 0
    updated = 0
    unresolved = 0

    for entry in entries:
        template = OverwinteringProfileTemplate.model_validate(entry)
        doc = template.model_dump(by_alias=True, exclude_none=True, mode="json")

        species = species_repo.get_by_scientific_name(template.species_scientific_name)
        if species and species.key:
            doc["species_key"] = species.key
        else:
            unresolved += 1

        key = entry["_key"]
        doc["_key"] = key
        if collection.has(key):
            # replace (not update): a merge would keep stale fields that a later
            # Steckbrief edit dropped (e.g. tuber_status after a rating change),
            # which would then fail model validation on read.
            collection.replace(doc)
            updated += 1
        else:
            collection.insert(doc)
            created += 1

    logger.info(
        "seed_overwintering_profiles_complete",
        created=created,
        updated=updated,
        unresolved_species=unresolved,
        total=len(entries),
    )
