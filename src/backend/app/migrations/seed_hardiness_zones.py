"""Seed the canonical hardiness-zone catalog (REQ-039).

Materialises all 26 USDA half-zones (``1a`` … ``13b``) into the global
``hardiness_zones`` collection. The temperature bounds are computed
*algorithmically* from the license-free USDA zone schema
(:mod:`app.domain.engines.hardiness_zone_resolver`) — no proprietary
USDA/PHZM/PRISM data is embedded. The curated German descriptions, representative
regions and frost-date defaults for the DACH-relevant zones (5a–9a) come from
``seed_data/hardiness_zones.yaml``; all other zones get a generic description.

Hardiness-zone reference data is not tenant-scoped — it is a global catalog
consulted by the winter-hardiness ampel and the zone resolver. The seed is
idempotent: it upserts each zone by its label (also the ``_key``), so repeated
startups never duplicate the catalog.
"""

from typing import Any

import structlog

from app.common.dependencies import get_hardiness_zone_repo
from app.domain.engines.hardiness_zone_resolver import (
    MAX_ZONE_INDEX,
    MIN_ZONE_INDEX,
    zone_bounds_c,
    zone_bounds_f,
    zone_label_for_index,
)
from app.domain.models.hardiness_zone import HardinessZone
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()

_GENERIC_DESCRIPTION_DE = (
    "USDA-Winterhaertezone {zone}: mittleres jaehrliches Minimum etwa "
    "{temp_min_c:.0f} bis {temp_max_c:.0f} Grad-Celsius. Ausserhalb des "
    "mitteleuropaeischen DACH-Spektrums."
)


def _curated_by_zone() -> dict[str, dict[str, Any]]:
    """Load the curated DACH content keyed by zone label."""
    data = load_yaml("hardiness_zones.yaml")
    return {entry["zone"]: entry for entry in data.get("zones", [])}


def _build_zone(index: int, curated: dict[str, dict[str, Any]]) -> HardinessZone:
    label = zone_label_for_index(index)
    temp_min_c, temp_max_c = zone_bounds_c(index)
    temp_min_f, temp_max_f = zone_bounds_f(index)
    entry = curated.get(label, {})
    description = entry.get("description_de") or _GENERIC_DESCRIPTION_DE.format(
        zone=label, temp_min_c=temp_min_c, temp_max_c=temp_max_c
    )
    return HardinessZone(
        zone=label,
        zone_number=1 + index // 2,
        subzone="a" if index % 2 == 0 else "b",
        temp_min_c=temp_min_c,
        temp_max_c=temp_max_c,
        temp_min_f=temp_min_f,
        temp_max_f=temp_max_f,
        description_de=description,
        representative_regions_de=entry.get("representative_regions_de", []),
        typical_last_frost_md=entry.get("typical_last_frost_md"),
        typical_first_frost_md=entry.get("typical_first_frost_md"),
    )


def run_seed_hardiness_zones() -> None:
    """Create/refresh the 26-entry hardiness-zone catalog (idempotent)."""
    repo = get_hardiness_zone_repo()
    curated = _curated_by_zone()

    upserted = 0
    for index in range(MIN_ZONE_INDEX, MAX_ZONE_INDEX + 1):
        zone = _build_zone(index, curated)
        repo.upsert_zone(zone)
        upserted += 1

    logger.info("seed_hardiness_zones_complete", upserted=upserted)


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_hardiness_zones()
