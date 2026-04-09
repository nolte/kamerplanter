"""Migrate LifecycleConfig data into PhaseSequence entities.

Ensures all species that have a LifecycleConfig with a phase_sequence_key
also have a corresponding HAS_PHASE_SEQUENCE edge.  Idempotent — safe to
run multiple times on the same database.
"""

import structlog

from app.common.dependencies import get_db, get_phase_sequence_repo
from app.data_access.arango import collections as col

logger = structlog.get_logger()


def run_migrate_lifecycle_to_phase_sequence() -> None:
    """Ensure all species with a LifecycleConfig have a HAS_PHASE_SEQUENCE edge.

    Iterates over every LifecycleConfig document and, if a phase_sequence_key
    is set but no HAS_PHASE_SEQUENCE edge exists for that species, creates the
    edge.  Shared sequences are linked without modification — no species_key
    is written onto the PhaseSequence document itself, since multiple species
    may share the same sequence.
    """
    db = get_db()
    ps_repo = get_phase_sequence_repo()

    # Get all lifecycle configs
    lifecycles = list(
        db.aql.execute(
            "FOR doc IN @@col RETURN doc",
            bind_vars={"@col": col.LIFECYCLE_CONFIGS},
        )
    )

    migrated = 0
    skipped = 0

    for lc_doc in lifecycles:
        species_key = lc_doc.get("species_key", "")
        if not species_key:
            skipped += 1
            continue

        species_id = f"{col.SPECIES}/{species_key}"

        # Check if HAS_PHASE_SEQUENCE edge already exists for this species
        existing_edges = list(
            db.aql.execute(
                "FOR e IN @@edge_col FILTER e._from == @from_id RETURN e._to",
                bind_vars={
                    "@edge_col": col.HAS_PHASE_SEQUENCE,
                    "from_id": species_id,
                },
            )
        )

        if existing_edges:
            skipped += 1
            continue

        # No edge yet — check if LifecycleConfig has phase_sequence_key
        ps_key = lc_doc.get("phase_sequence_key", "")
        if not ps_key:
            skipped += 1
            logger.debug("lifecycle_no_sequence", species_key=species_key)
            continue

        # Verify the PhaseSequence actually exists
        seq = ps_repo.get_sequence_by_key(ps_key)
        if not seq:
            skipped += 1
            logger.warning(
                "phase_sequence_key_dangling",
                species_key=species_key,
                phase_sequence_key=ps_key,
            )
            continue

        # Create edge
        seq_id = f"{col.PHASE_SEQUENCES}/{ps_key}"
        edge_col = db.collection(col.HAS_PHASE_SEQUENCE)
        edge_col.insert({"_from": species_id, "_to": seq_id})
        migrated += 1
        logger.info(
            "phase_sequence_edge_created",
            species_key=species_key,
            sequence=seq.name,
        )

    logger.info(
        "migrate_lifecycle_to_phase_sequence_complete",
        migrated=migrated,
        skipped=skipped,
    )
