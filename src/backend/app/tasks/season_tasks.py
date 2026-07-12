"""REQ-047 §3.6 — daily Celery task that advances every site's season state.

For each ``outdoor``/``greenhouse`` site the task resolves the best season signal
(live → climatological → calendar), advances the season state machine and applies
the per-transition side effects (overwintering materialisation, dormancy-care mode).
Runs after the weather fetch. Guarded by the ``season_state_eval_enabled``
kill-switch. Idempotent: a second run on the same day neither re-transitions nor
duplicates side effects.
"""

import structlog

from app.config.settings import settings
from app.tasks import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def evaluate_season_states(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """Evaluate the season state for every outdoor/greenhouse site."""
    if not settings.season_state_eval_enabled:
        return {"status": "skipped", "reason": "season_state_eval_disabled"}

    from app.common.dependencies import get_season_state_service, get_site_repo
    from app.domain.models.site import Site

    site_repo = get_site_repo()
    service = get_season_state_service()

    # Cross-tenant iteration stays in the data-access layer (NFR-001); docs are
    # returned normalised so each Site is constructed defensively below.
    site_docs = site_repo.find_site_docs_by_types(["outdoor", "greenhouse"])

    evaluated = 0
    transitions = 0
    errors = 0
    for doc in site_docs:
        # AC-18: constructing the Site (Pydantic) is inside the guard, so a single
        # schema-drift document is logged and skipped instead of aborting the run.
        try:
            site = Site(**doc)
            state, changed = service.evaluate_site_detailed(site)
        except Exception as exc:  # noqa: BLE001 — one bad site must not abort the run
            logger.warning("season_evaluate_site_failed", site_key=doc.get("_key"), error=str(exc))
            errors += 1
            continue
        if state is None:
            continue
        evaluated += 1
        if changed:
            transitions += 1
            logger.info(
                "season_transition",
                site_key=site.key,
                phase=state.phase.value,
                trigger_tier=state.trigger_tier.value,
            )

    logger.info("season_evaluate_complete", evaluated=evaluated, transitions=transitions, errors=errors)
    return {"status": "ok", "evaluated": evaluated, "transitions": transitions, "errors": errors}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def evaluate_quarter_climate(self) -> dict:  # noqa: ANN001 — Celery bound-task self
    """REQ-047 §3.7.3 / AC-22 — raise HIGH warnings on winter-quarter band violations.

    Scans the active plants and, for every one that is in dormancy-care with a
    winter quarter that exposes live temperature data, compares the reading against
    the profile's temperature band and creates a ``quarter_climate_check`` task on a
    real violation. Idempotent and resilient: one bad plant is logged and skipped.
    """
    if not settings.season_state_eval_enabled:
        return {"status": "skipped", "reason": "season_state_eval_disabled"}

    from app.common.dependencies import get_plant_repo, get_quarter_climate_service

    plant_repo = get_plant_repo()
    service = get_quarter_climate_service()

    plants, _total = plant_repo.get_all(offset=0, limit=1000, all_tenants=True)
    evaluated = 0
    warnings = 0
    errors = 0
    for plant in plants:
        if plant.removed_on is not None or not plant.key:
            continue
        evaluated += 1
        try:
            if service.evaluate_plant(plant.key) is not None:
                warnings += 1
        except Exception as exc:  # noqa: BLE001 — one bad plant must not abort the run
            logger.warning("quarter_climate_evaluate_failed", plant_key=plant.key, error=str(exc))
            errors += 1

    logger.info("quarter_climate_evaluate_complete", evaluated=evaluated, warnings=warnings, errors=errors)
    return {"status": "ok", "evaluated": evaluated, "warnings": warnings, "errors": errors}
