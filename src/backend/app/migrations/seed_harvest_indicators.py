"""Seed the global harvest-readiness indicator catalogue (REQ-007).

Create-if-absent by the identity the YAML gives an entry: ``(species,
indicator_type, measurement_unit)``. ``(species, indicator_type)`` is not unique
in ``harvest_indicators.yaml`` (a species lists several ``texture`` or ``color``
indicators measured in different units), and the collection carries no unique
index — so the loader itself must look before it writes. It used to call
``create_indicator`` inside a ``try/except`` that logged ``harvest_indicator_exists``;
the insert never fails, the ``except`` never fired, and every start appended the
whole set again (173 rows per boot, #1956).

A row that exists is left exactly as it is: an operator may have tuned its
reliability score, and the seed does not own the catalogue after the first write.

Runs after the plant-info seeds (see ``seeds/registry.py``): the species an entry
names are resolved against the whole species catalogue, and about a third of them
exist only in the plant-info files. Resolved from ``core_data`` they were created
with no species at all — rows no species could ever reach.
"""

import structlog

from app.common.dependencies import get_db, get_harvest_repo
from app.domain.models.harvest import HarvestIndicator
from app.migrations.seed_upsert_helpers import load_species_key_map
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def load_harvest_indicator_entries() -> list[dict]:
    """The indicator entries of ``harvest_indicators.yaml``."""
    return load_yaml("harvest_indicators.yaml").get("harvest_indicators", [])


def run_seed_harvest_indicators() -> None:
    """Create the harvest indicators the YAML names that do not exist yet."""
    entries = load_harvest_indicator_entries()
    harvest_repo = get_harvest_repo()
    species_key_map = load_species_key_map(get_db())

    created = 0
    existing = 0
    unresolved = 0
    for entry in entries:
        species_key = species_key_map.get(entry["species_name"])
        if not species_key:
            # Not created without a species: such a row is reachable through no species
            # and has no identity a later run could find it by.
            unresolved += 1
            logger.info("harvest_indicator_species_not_found", species=entry["species_name"])
            continue
        if harvest_repo.find_indicator(species_key, entry["indicator_type"], entry["measurement_unit"]):
            existing += 1
            continue
        harvest_repo.create_indicator(
            HarvestIndicator(
                indicator_type=entry["indicator_type"],
                measurement_unit=entry["measurement_unit"],
                measurement_method=entry["measurement_method"],
                observation_frequency=entry["observation_frequency"],
                reliability_score=entry["reliability_score"],
                species_key=species_key,
            )
        )
        created += 1
        logger.info("harvest_indicator_created", type=entry["indicator_type"], species=entry["species_name"])

    logger.info(
        "seed_harvest_indicators_complete",
        created=created,
        existing=existing,
        species_not_found=unresolved,
    )
