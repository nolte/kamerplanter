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
    from app.data_access.arango.collections import SITES
    from app.domain.models.site import Site

    site_repo = get_site_repo()
    service = get_season_state_service()

    db = site_repo._db  # noqa: SLF001 — direct AQL for cross-tenant iteration
    cursor = db.aql.execute(
        "FOR s IN @@col FILTER s.type IN @types RETURN s",
        bind_vars={"@col": SITES, "types": ["outdoor", "greenhouse"]},
    )

    evaluated = 0
    transitions = 0
    errors = 0
    for doc in cursor:
        site = Site(**site_repo._from_doc(doc))  # noqa: SLF001
        try:
            before = service._repo.get_by_site(site.key or "", site.tenant_key)  # noqa: SLF001
            state = service.evaluate_site(site)
        except Exception as exc:  # noqa: BLE001 — one bad site must not abort the run
            logger.warning("season_evaluate_site_failed", site_key=site.key, error=str(exc))
            errors += 1
            continue
        if state is None:
            continue
        evaluated += 1
        if before is None or before.phase != state.phase:
            transitions += 1
            logger.info(
                "season_transition",
                site_key=site.key,
                phase=state.phase.value,
                trigger_tier=state.trigger_tier.value,
            )

    logger.info("season_evaluate_complete", evaluated=evaluated, transitions=transitions, errors=errors)
    return {"status": "ok", "evaluated": evaluated, "transitions": transitions, "errors": errors}
