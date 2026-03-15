import structlog

from app.common.dependencies import get_lifecycle_repo, get_plant_repo, get_species_repo
from app.domain.engines.dormancy_trigger import DormancyTrigger
from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="check_dormancy_triggers")
def check_dormancy_triggers(current_temp_c: float, day_length_hours: float) -> dict:
    """Check all active perennial plants for dormancy triggers."""
    plant_repo = get_plant_repo()
    species_repo = get_species_repo()
    phase_repo = get_lifecycle_repo()
    trigger = DormancyTrigger(phase_repo, species_repo)

    triggered = 0
    plants, _ = plant_repo.get_all(offset=0, limit=1000)

    for plant in plants:
        if plant.removed_on is not None:
            continue
        # Resolve phase name from key to check for dormancy
        phase_name = plant_repo.resolve_phase_name(plant.current_phase_key or "") if plant.current_phase_key else ""
        if phase_name == "dormancy":
            continue

        try:
            if trigger.should_trigger_dormancy(plant.species_key, current_temp_c, day_length_hours):
                dormancy_key = trigger.get_dormancy_phase_key(plant.species_key)
                if dormancy_key:
                    from app.common.dependencies import get_phase_service

                    phase_service = get_phase_service()
                    phase_service.transition_phase(plant.key or "", dormancy_key, reason="dormancy_trigger")
                    triggered += 1
                    logger.info("dormancy_triggered", plant_key=plant.key)
        except Exception as e:
            logger.error("dormancy_check_error", plant_key=plant.key, error=str(e))

    return {"triggered": triggered}
