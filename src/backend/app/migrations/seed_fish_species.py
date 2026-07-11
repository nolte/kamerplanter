"""Seed the global fish-species catalog and fish/plant compatibility edges (REQ-026).

Loads ``seed_data/fish_species.yaml`` into the ``fish_species`` collection
(idempotent by ``_key``). Fish species are global reference data, not
tenant-scoped.

Compatibility edges (``compatible_fish_plant`` / ``incompatible_fish_plant``) are
generated from the temperature overlap between each fish's optimal band and each
plant's germination-temperature band (a proxy for the root-zone preference). Edge
generation is skipped for a fish species once it already carries edges, so
repeated startups never duplicate the graph.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.common.dependencies import get_db
from app.data_access.arango import collections as col
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def _temperature_match(fish_min: float, fish_max: float, plant_min: float, plant_max: float) -> float:
    """Fraction of overlap between the two temperature bands (0.0-1.0)."""
    overlap = min(fish_max, plant_max) - max(fish_min, plant_min)
    total = max(fish_max, plant_max) - min(fish_min, plant_min)
    if total <= 0:
        return 0.0
    return round(max(0.0, overlap / total), 3)


def _seed_species(db: Any) -> int:
    data = load_yaml("fish_species.yaml")
    raw_species: list[dict[str, Any]] = data.get("fish_species", [])
    species_col = db.collection(col.FISH_SPECIES)
    created = 0
    for raw in raw_species:
        if species_col.has(raw["_key"]):
            continue
        species_col.insert(raw)
        created += 1
        logger.info("fish_species_seeded", key=raw["_key"])
    return created


def _seed_compatibility_edges(db: Any) -> int:
    """Generate fish/plant compatibility edges from temperature-band overlap."""
    species_col = db.collection(col.FISH_SPECIES)
    plants_col = db.collection(col.SPECIES)
    compatible_col = db.collection(col.COMPATIBLE_FISH_PLANT)
    incompatible_col = db.collection(col.INCOMPATIBLE_FISH_PLANT)

    fish_species = list(species_col.all())
    # Plants with usable germination-temperature data act as the root-zone proxy.
    plants = [
        p
        for p in plants_col.all()
        if p.get("germination_temp_min_c") is not None and p.get("germination_temp_max_c") is not None
    ]
    if not plants:
        return 0

    created = 0
    for fish in fish_species:
        fish_id = f"{col.FISH_SPECIES}/{fish['_key']}"
        # Idempotency: skip a fish that already has any compatibility edge.
        already = db.aql.execute(
            "RETURN LENGTH(FOR e IN @@edge FILTER e._from == @from LIMIT 1 RETURN 1)",
            bind_vars={"@edge": col.COMPATIBLE_FISH_PLANT, "from": fish_id},
        )
        if next(already, 0):
            continue
        f_min = fish["temperature_optimal_min_c"]
        f_max = fish["temperature_optimal_max_c"]
        for plant in plants:
            match = _temperature_match(f_min, f_max, plant["germination_temp_min_c"], plant["germination_temp_max_c"])
            plant_id = f"{col.SPECIES}/{plant['_key']}"
            if match > 0.3:
                compatible_col.insert(
                    {
                        "_from": fish_id,
                        "_to": plant_id,
                        "temperature_match": match,
                        "nutrient_match": 0.5,
                        "notes": "Auto-generated from temperature overlap.",
                    }
                )
            else:
                incompatible_col.insert(
                    {
                        "_from": fish_id,
                        "_to": plant_id,
                        "reason": f"Temperaturzone inkompatibel (Overlap {match}).",
                    }
                )
            created += 1
    return created


def run_seed_fish_species() -> None:
    """Seed fish species and their plant-compatibility edges (idempotent)."""
    db = get_db()
    species_created = _seed_species(db)
    edges_created = _seed_compatibility_edges(db)
    logger.info(
        "seed_fish_species_complete",
        species_created=species_created,
        edges_created=edges_created,
    )


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_fish_species()
