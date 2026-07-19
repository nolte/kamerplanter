"""Apply the ADR-006 E6 ``cultivation_flexible`` capability flag to species.

The flag marks a species that can be genuinely grown EITHER as an annual OR as a
perennial (a frost-tender perennial overwintered indoors vs. re-bought each year,
a strawberry grown as an annual). Its authoritative source is the
``lifecycle_overrides`` map in ``species.yaml`` (#297 keeps that the single source
for the cultivation-practice axes), keyed by ``scientific_name``.

This runs as a dedicated post-seed pass — deliberately AFTER the core-data,
plant-info and plant-info-extended species seeds — so every species record already
exists regardless of which seed file created it (base species live in
``species.yaml`` ``species:``; a few facultative ones, e.g. Begonia semperflorens
and Impatiens walleriana, are only defined in the plant-info files). It sets the
Species field directly via an idempotent single-field update: re-running it is a
no-op once the flag already matches, and it only ever writes ``true`` for the
documented facultative cohort — species without a ``cultivation_flexible`` override
keep the model default (``false``).
"""

from __future__ import annotations

import structlog

from app.common.dependencies import get_species_repo
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def _load_flexible_species() -> set[str]:
    """Return the scientific names flagged ``cultivation_flexible: true``.

    Reads the same ``species.yaml`` ``lifecycle_overrides`` map that
    ``seed_data.py`` uses for the cultivation-practice axes; only entries whose
    override sets the flag truthy are returned.
    """
    data = load_yaml("species.yaml")
    overrides: dict[str, dict] = data.get("lifecycle_overrides", {}) or {}
    return {name for name, ov in overrides.items() if bool(ov.get("cultivation_flexible", False))}


def run_seed_cultivation_flexible() -> None:
    """Set ``Species.cultivation_flexible`` for the facultative cohort (ADR-006 E6)."""
    flexible_names = _load_flexible_species()
    if not flexible_names:
        logger.info("cultivation_flexible_seed_empty")
        return

    species_repo = get_species_repo()
    updated = 0
    missing = 0
    for scientific_name in sorted(flexible_names):
        species = species_repo.get_by_scientific_name(scientific_name)
        if species is None:
            missing += 1
            logger.info("cultivation_flexible_species_not_found", species=scientific_name)
            continue
        if species.cultivation_flexible:
            continue  # idempotent: already flagged
        species_repo.update_field(species.key or "", "cultivation_flexible", True)
        updated += 1
        logger.info("cultivation_flexible_set", species=scientific_name)

    logger.info(
        "cultivation_flexible_seed_done",
        flagged=len(flexible_names),
        updated=updated,
        missing=missing,
    )


if __name__ == "__main__":
    run_seed_cultivation_flexible()
