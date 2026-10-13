"""Seed the standard substrate catalog (REQ-019).

Loads ``seed_data/substrates.yaml`` into the ``substrates`` collection. The seed
is idempotent: an existing substrate is identified by the tuple
``(type, name_de or brand or "")`` and skipped on re-runs, so repeated startups
never duplicate the catalog.

The seeded media are **global** rows (``tenant_key`` empty) of a hybrid catalogue:
a tenant's own mixes live in the same collection (#1195). The identity check
therefore looks at the global rows only (:func:`_existing_identities`, #2027). It
used to read the whole collection, so a tenant's mix with a seed's identity counted
as the seed being present, and the global row was never created for anyone.
"""

from typing import Any

import structlog

from app.common.dependencies import get_substrate_repo
from app.data_access.arango.substrate_repository import ArangoSubstrateRepository
from app.domain.models.substrate import Substrate
from app.migrations.yaml_loader import load_yaml

logger = structlog.get_logger()


def _identity(substrate: Substrate) -> tuple[str, str]:
    """Return the dedup identity for a substrate: ``(type, name_de or brand)``."""
    return (substrate.type.value, substrate.name_de or substrate.brand or "")


def _existing_identities(repo: ArangoSubstrateRepository) -> set[tuple[str, str]]:
    """Collect the dedup identities of the global (seeded) substrates, never a tenant's mix."""
    return {_identity(s) for s in repo.get_global_substrates()}


def run_seed_substrates() -> None:
    """Create the standard substrate catalog from YAML seed data (idempotent)."""
    repo = get_substrate_repo()
    data = load_yaml("substrates.yaml")
    raw_substrates: list[dict[str, Any]] = data.get("substrates", [])

    seen = _existing_identities(repo)

    created = 0
    for raw in raw_substrates:
        substrate = Substrate.model_validate(raw)
        ident = _identity(substrate)
        if ident in seen:
            continue

        repo.create_substrate(substrate)
        seen.add(ident)
        created += 1
        logger.info(
            "substrate_seeded",
            type=substrate.type.value,
            name_de=substrate.name_de,
            brand=substrate.brand,
        )

    logger.info(
        "seed_substrates_complete",
        created=created,
        total=len(raw_substrates),
    )


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_substrates()
