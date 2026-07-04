"""Ordered seed registry with per-seed error isolation (NFR-016 S-2, S-4).

The registry mirrors, in order, the seed sequence that previously lived inline in
``main.py``'s ``lifespan``.  Each :class:`SeedJob` wraps one seed function with a
uniform ``run(db)`` signature (functions that take no argument are adapted).

Fatal jobs (structurally required reference data — e.g. location types) abort the
startup when they fail.  Non-fatal reference-data seeds are isolated: a failure is
logged as ``seed_failed`` and the remaining seeds still run (S-2), so a single bad
seed file can no longer wedge the whole startup.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import structlog
from arango.database import StandardDatabase

from app.config.settings import settings

logger = structlog.get_logger()


@dataclass(frozen=True)
class SeedJob:
    """A single seed step.

    Attributes
    ----------
    name:
        Stable identifier used in log events.
    run:
        Callable applying the seed. Always invoked as ``run(db)``; seeds that
        resolve their own connection ignore the argument.
    fatal:
        When ``True`` a failure aborts the startup; otherwise it is isolated.
    """

    name: str
    run: Callable[[StandardDatabase], None]
    fatal: bool = False


def _build_jobs() -> list[SeedJob]:
    """Return the ordered seed jobs, mirroring the historical ``main.py`` order.

    ``lifecycle_to_phase_sequence_reconcile`` is deliberately the last data step:
    it is a *post-seed reconcile* that links seed-created LifecycleConfigs to
    seed-created PhaseSequences, not a transformation of pre-existing user data —
    so it belongs here, after its input seeds, rather than in ``versions/``.
    """
    from app.migrations.migrate_lifecycle_to_phase_sequence import run_migrate_lifecycle_to_phase_sequence
    from app.migrations.seed_activities import run_seed_activities
    from app.migrations.seed_adventskalender import run_seed_adventskalender
    from app.migrations.seed_data import run_seed
    from app.migrations.seed_fertilizers import run_seed_fertilizers
    from app.migrations.seed_gardol import run_seed_gardol
    from app.migrations.seed_lifecycles_outdoor import run_seed_lifecycles_outdoor
    from app.migrations.seed_location_types import seed_location_types
    from app.migrations.seed_nutrient_plans_outdoor import run_seed_nutrient_plans_outdoor
    from app.migrations.seed_nutrient_plans_ro import run_seed_nutrient_plans_ro
    from app.migrations.seed_overwintering_profiles import run_seed_overwintering_profiles
    from app.migrations.seed_phase_sequences import run_seed_phase_sequences
    from app.migrations.seed_plagron import run_seed_plagron
    from app.migrations.seed_plant_info import run_seed_plant_info
    from app.migrations.seed_plant_info_extended import run_seed_plant_info_extended
    from app.migrations.seed_starter_kits import run_seed_starter_kits

    jobs: list[SeedJob] = [
        # Structurally required: location types are referenced by site/location setup.
        SeedJob("location_types", lambda db: seed_location_types(db), fatal=True),
        SeedJob("core_data", lambda db: run_seed()),
        SeedJob("starter_kits", lambda db: run_seed_starter_kits()),
        SeedJob("adventskalender", lambda db: run_seed_adventskalender()),
        SeedJob("plant_info", lambda db: run_seed_plant_info()),
        SeedJob("plant_info_extended", lambda db: run_seed_plant_info_extended()),
        SeedJob("overwintering_profiles", lambda db: run_seed_overwintering_profiles()),
        SeedJob("fertilizers", lambda db: run_seed_fertilizers()),
        SeedJob("plagron", lambda db: run_seed_plagron()),
        SeedJob("gardol", lambda db: run_seed_gardol()),
        SeedJob("nutrient_plans_outdoor", lambda db: run_seed_nutrient_plans_outdoor()),
        SeedJob("nutrient_plans_ro", lambda db: run_seed_nutrient_plans_ro()),
        SeedJob("activities", lambda db: run_seed_activities()),
        SeedJob("phase_sequences", lambda db: run_seed_phase_sequences()),
        SeedJob("lifecycles_outdoor", lambda db: run_seed_lifecycles_outdoor()),
        SeedJob("lifecycle_to_phase_sequence_reconcile", lambda db: run_migrate_lifecycle_to_phase_sequence()),
    ]

    if settings.kamerplanter_mode == "light":
        from app.migrations.seed_light_mode import run_seed_light_mode

        jobs.append(SeedJob("light_mode", lambda db: run_seed_light_mode()))

    return jobs


def run_seeds(db: StandardDatabase, jobs: list[SeedJob] | None = None) -> None:
    """Run the seed registry with per-seed error isolation (S-2).

    ``jobs`` may be injected for testing; otherwise the default registry is built.
    Fatal-job failures propagate (aborting startup); non-fatal failures are logged
    and skipped so the remaining seeds and the app still start.
    """
    for job in jobs if jobs is not None else _build_jobs():
        try:
            job.run(db)
            logger.info("seed_completed", seed=job.name)
        except Exception:
            if job.fatal:
                logger.critical("seed_failed_fatal", seed=job.name, exc_info=True)
                raise
            logger.error("seed_failed", seed=job.name, exc_info=True)
