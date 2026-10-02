import structlog

from app.common.log_privacy import loggable_error
from app.tasks import celery_app

logger = structlog.get_logger()


_PAGE_SIZE = 1000


def _iter_all_plants(plant_repo):
    """Every plant of every tenant, page by page (a single page silently dropped the rest)."""
    offset = 0
    while True:
        page, total = plant_repo.get_all(offset=offset, limit=_PAGE_SIZE, all_tenants=True)  # system task
        yield from page
        offset += _PAGE_SIZE
        if not page or offset >= total:
            return


@celery_app.task(name="update_vernalization_progress")
def update_vernalization_progress(avg_temp_c: float) -> dict:
    """Update vernalization tracking for biennial plants."""
    from app.common.dependencies import get_lifecycle_repo, get_plant_repo
    from app.domain.engines.vernalization_tracker import VernalizationTracker

    plant_repo = get_plant_repo()
    phase_repo = get_lifecycle_repo()
    tracker = VernalizationTracker()

    updated = 0
    is_cold = tracker.is_cold_day(avg_temp_c)
    for plant in _iter_all_plants(plant_repo):
        if plant.removed_on is not None:
            continue

        try:
            lifecycle = phase_repo.get_lifecycle_by_species(plant.species_key)
            if lifecycle is None or not lifecycle.vernalization_required:
                continue

            if is_cold:
                # Accumulate + persist the chill day (REQ-003 E2). The
                # vernalization_based trigger reads chill_days_accumulated.
                # One server-side increment (#1970): writing the snapshot back would
                # revert a phase change or removal made since the read.
                chill_days = plant_repo.increment_chill_days(plant.key or "")
                if chill_days is None:  # removed since the read
                    continue
                updated += 1
                logger.info(
                    "vernalization_cold_day",
                    plant_key=plant.key,
                    avg_temp=avg_temp_c,
                    chill_days=chill_days,
                )
        except Exception as e:
            logger.error("vernalization_error", plant_key=plant.key, error=loggable_error(e))

    return {"cold_day": is_cold, "plants_tracked": updated}
