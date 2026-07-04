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
    is_cold = tracker.is_cold_day(avg_temp_c)
    plants, _ = plant_repo.get_all(offset=0, limit=1000, all_tenants=True)  # system task: all tenants

    for plant in plants:
        if plant.removed_on is not None:
            continue

        try:
            lifecycle = phase_repo.get_lifecycle_by_species(plant.species_key)
            if lifecycle is None or not lifecycle.vernalization_required:
                continue

            if is_cold:
                # Accumulate + persist the chill day (REQ-003 E2). The
                # vernalization_based trigger reads chill_days_accumulated.
                plant.chill_days_accumulated += 1
                plant_repo.update(plant.key or "", plant)
                updated += 1
                logger.info(
                    "vernalization_cold_day",
                    plant_key=plant.key,
                    avg_temp=avg_temp_c,
                    chill_days=plant.chill_days_accumulated,
                )
        except Exception as e:
            logger.error("vernalization_error", plant_key=plant.key, error=str(e))

    return {"cold_day": is_cold, "plants_tracked": updated}
