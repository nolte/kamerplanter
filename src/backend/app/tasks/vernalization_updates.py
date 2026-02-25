import structlog

from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="update_vernalization_progress")
def update_vernalization_progress(avg_temp_c: float) -> dict:
    """Update vernalization tracking for biennial plants."""
    from app.common.dependencies import get_lifecycle_repo, get_plant_repo
    from app.domain.engines.vernalization_tracker import VernalizationTracker

    plant_repo = get_plant_repo()
    phase_repo = get_lifecycle_repo()
    tracker = VernalizationTracker()

    updated = 0
    plants, _ = plant_repo.get_all(offset=0, limit=1000)

    for plant in plants:
        if plant.removed_on is not None:
            continue

        try:
            lifecycle = phase_repo.get_lifecycle_by_species(plant.species_key)
            if lifecycle is None or not lifecycle.vernalization_required:
                continue

            is_cold = tracker.is_cold_day(avg_temp_c)
            if is_cold:
                updated += 1
                logger.info(
                    "vernalization_cold_day",
                    plant_key=plant.key,
                    avg_temp=avg_temp_c,
                )
        except Exception as e:
            logger.error("vernalization_error", plant_key=plant.key, error=str(e))

    return {"cold_day": tracker.is_cold_day(avg_temp_c), "plants_tracked": updated}
