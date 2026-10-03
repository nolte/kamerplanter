"""Ordered seed registry with per-seed error isolation (NFR-016 S-2, S-4).

The registry mirrors, in order, the seed sequence that previously lived inline in
``main.py``'s ``lifespan``.  Each :class:`SeedJob` wraps one seed function with a
uniform ``run(db)`` signature (functions that take no argument are adapted).

Fatal jobs (structurally required reference data — e.g. location types) abort the
startup when they fail.  Non-fatal reference-data seeds are isolated: a failure is
logged as ``seed_failed`` and the remaining seeds still run (S-2), so a single bad
seed file can no longer wedge the whole startup.

**One seeding replica at a time (#2028).** Most loaders look a row up by name and
create it when absent, on collections without a unique index for that identity. Two
replicas booting together both read "absent" and both create: a measured concurrent
first boot left 40 phase sequences instead of 21, 66 nutrient plans instead of 38,
and the replica that lost the ``location_types`` insert race aborted its startup.
:func:`run_seeds` therefore runs under the migration lock (``tracking``), the same
document the versioned migrations already serialise on — no second lock:

* the replica that holds the lock seeds; it renews the lock after every job
  (:func:`~app.migrations.framework.tracking.refresh_lock`) and records the completed
  run in ``schema_migrations/__seed_run__`` before releasing;
* a replica that finds the lock held waits, polling like the migration barrier
  (``BARRIER_TIMEOUT_SECONDS``). When it gets the lock and a run with the same seed
  inputs (:func:`seed_fingerprint`) and no failed job completed while it waited, it
  does not seed again: the other replica's run is the one this boot needed. Otherwise
  (no run completed meanwhile, other seed inputs, a failed job) it seeds itself, which
  is safe because it is now the only seeder;
* a holder that crashes leaves a lock that goes stale after ``LOCK_TTL_SECONDS``; a
  waiter takes it over (revision-checked, as for migrations) and seeds. The crashed
  run recorded nothing, so nobody skips on its account;
* a holder that finds its lock taken over between two jobs stops with
  :class:`SeedLockLostError` instead of seeding beside the new holder;
* a waiter that does not get the lock within the budget fails startup with
  :class:`SeedBarrierTimeoutError` (readiness fails, the pod restarts) rather than
  skipping the seeds silently: on a fresh volume that would serve an application
  without its reference data.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.config.settings import settings
from app.migrations.framework import tracking
from app.migrations.framework.report import MigrationLockError, SeedBarrierTimeoutError, SeedLockLostError
from app.migrations.framework.runner import BARRIER_POLL_INTERVAL_SECONDS, BARRIER_TIMEOUT_SECONDS

logger = structlog.get_logger()

#: ``app/migrations``: the seed loaders and their ``seed_data`` files live here.
_MIGRATIONS_DIR = Path(__file__).resolve().parents[1]


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
    from app.migrations.seed_cultivation_flexible import run_seed_cultivation_flexible
    from app.migrations.seed_data import run_seed
    from app.migrations.seed_fertilizers import run_seed_fertilizers
    from app.migrations.seed_fish_species import run_seed_fish_species
    from app.migrations.seed_gardol import run_seed_gardol
    from app.migrations.seed_glossary import run_seed_glossary
    from app.migrations.seed_hardiness_zones import run_seed_hardiness_zones
    from app.migrations.seed_harvest_indicators import run_seed_harvest_indicators
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
    from app.migrations.seed_substrates import run_seed_substrates

    jobs: list[SeedJob] = [
        # Structurally required: location types are referenced by site/location setup.
        SeedJob("location_types", lambda db: seed_location_types(db), fatal=True),
        SeedJob("core_data", lambda db: run_seed()),
        SeedJob("starter_kits", lambda db: run_seed_starter_kits()),
        SeedJob("adventskalender", lambda db: run_seed_adventskalender()),
        SeedJob("plant_info", lambda db: run_seed_plant_info()),
        SeedJob("plant_info_extended", lambda db: run_seed_plant_info_extended()),
        # Post-species pass: applies the ADR-006 E6 cultivation_flexible flag once
        # every species record exists (base + plant-info), so facultative species
        # defined only in the plant-info files are covered too.
        SeedJob("cultivation_flexible", lambda db: run_seed_cultivation_flexible()),
        # After every species exists (base + plant-info): an indicator is created only for a
        # species it resolves to, and create-if-absent by (species, type, unit) (#1956).
        SeedJob("harvest_indicators", lambda db: run_seed_harvest_indicators()),
        SeedJob("substrates", lambda db: run_seed_substrates()),
        SeedJob("hardiness_zones", lambda db: run_seed_hardiness_zones()),
        SeedJob("fish_species", lambda db: run_seed_fish_species()),
        SeedJob("glossary", lambda db: run_seed_glossary()),
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

    # E2E only (#1155). Appended unconditionally; the seed itself decides, and it
    # refuses unless *both* its gates hold — see its module docstring for why a
    # single environment variable is not allowed to mint a platform admin. Kept
    # non-fatal like the other data seeds: a failure here must not wedge startup.
    if settings.e2e_platform_admin_email:
        from app.migrations.seed_e2e_platform_admin import run_seed_e2e_platform_admin

        jobs.append(SeedJob("e2e_platform_admin", lambda db: run_seed_e2e_platform_admin()))

    return jobs


def seed_fingerprint(job_names: Iterable[str], root: Path = _MIGRATIONS_DIR) -> str:
    """A digest of what a seed run applies: the job list, the loaders and their data files.

    Two replicas of the same image compute the same value; a replica of another image
    (a rolling update racing a restart) computes another, so it never skips a run
    whose inputs differ from its own. Covers ``app/migrations/*.py`` (the loaders),
    ``seeds/`` and every file under ``seed_data/``.
    """
    digest = hashlib.sha256()
    for name in job_names:
        digest.update(name.encode())
        digest.update(b"\0")
    files = sorted([*root.glob("*.py"), *(root / "seeds").glob("*.py"), *(root / "seed_data").rglob("*")])
    for path in files:
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


class _Uncontended:
    """Sentinel: the lock was free on the first attempt, nobody else was seeding."""


_UNCONTENDED = _Uncontended()


def _acquire_seed_lock(db: StandardDatabase) -> tuple[str, dict[str, Any] | None | _Uncontended]:
    """Take the migration lock, waiting (bounded) while another replica holds it.

    Returns the owner token and what this replica knew about the last seed run when it
    started to wait — :data:`_UNCONTENDED` if it never had to.
    """
    deadline = time.monotonic() + BARRIER_TIMEOUT_SECONDS
    seen: dict[str, Any] | None | _Uncontended = _UNCONTENDED
    attempt = 0
    while True:
        try:
            return tracking.acquire_lock(db), seen
        except MigrationLockError:
            if isinstance(seen, _Uncontended):
                # Read once, after the first refusal: a run recorded after this read
                # completed while we waited. A run that completed between the refusal
                # and this read is missed, which only costs a redundant re-seed.
                seen = tracking.seed_run_marker(db)
            attempt += 1
            if time.monotonic() >= deadline:
                raise SeedBarrierTimeoutError(
                    f"Timed out waiting for the seeding replica to release the lock (attempts={attempt})"
                ) from None
            logger.info("seeds_locked_by_other_runner_waiting", attempt=attempt)
            time.sleep(BARRIER_POLL_INTERVAL_SECONDS)


def _seeded_while_waiting(
    seen: dict[str, Any] | None | _Uncontended, current: dict[str, Any] | None, fingerprint: str
) -> bool:
    """Whether a complete, failure-free run of these seed inputs finished while we waited."""
    if isinstance(seen, _Uncontended) or current is None:
        return False
    seen_run = seen.get("run_id") if seen is not None else None
    return (
        current.get("run_id") != seen_run
        and current.get("fingerprint") == fingerprint
        and not current.get("failed_jobs")
    )


def _run_jobs(db: StandardDatabase, jobs: list[SeedJob], owner: str) -> list[str]:
    """Run the jobs in order with per-seed isolation (S-2); return the names that failed.

    The lock is renewed after every job; a lock that is no longer ours stops the run.
    """
    failed: list[str] = []
    for job in jobs:
        try:
            job.run(db)
            logger.info("seed_completed", seed=job.name)
        except Exception:
            if job.fatal:
                logger.critical("seed_failed_fatal", seed=job.name, exc_info=True)
                raise
            logger.error("seed_failed", seed=job.name, exc_info=True)
            failed.append(job.name)
        if not tracking.refresh_lock(db, owner):
            raise SeedLockLostError(f"the migration lock was taken over while seeding (after seed={job.name})")
    return failed


def run_seeds(db: StandardDatabase, jobs: list[SeedJob] | None = None) -> None:
    """Run the seed registry under the migration lock, with per-seed error isolation (S-2).

    ``jobs`` may be injected for testing; otherwise the default registry is built.
    Fatal-job failures propagate (aborting startup); non-fatal failures are logged
    and skipped so the remaining seeds and the app still start. Concurrency, waiting,
    the skip after another replica's run and the failure modes: module docstring
    (#2028).
    """
    selected = jobs if jobs is not None else _build_jobs()
    fingerprint = seed_fingerprint(job.name for job in selected)
    owner, seen = _acquire_seed_lock(db)
    try:
        current = tracking.seed_run_marker(db)
        if _seeded_while_waiting(seen, current, fingerprint):
            logger.info("seeds_completed_by_other_replica", run_id=current.get("run_id") if current else None)
            return
        failed = _run_jobs(db, selected, owner)
        tracking.record_seed_run(db, run_id=str(uuid.uuid4()), fingerprint=fingerprint, failed_jobs=failed)
    finally:
        tracking.release_lock(db, owner)
