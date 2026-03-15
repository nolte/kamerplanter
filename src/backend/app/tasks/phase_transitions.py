import structlog

from app.common.dependencies import get_phase_service, get_plant_repo
from app.tasks import celery_app

logger = structlog.get_logger()


@celery_app.task(name="check_auto_transitions")
def check_auto_transitions() -> dict:
    """Check all active plants for auto-transitions based on time."""
    plant_repo = get_plant_repo()
    phase_service = get_phase_service()

    transitioned = 0
    errors = 0

    plants, total = plant_repo.get_all(offset=0, limit=1000)
    for plant in plants:
        if plant.removed_on is not None:
            continue
        if not plant.current_phase_key:
            continue

        try:
            current_phase_info = phase_service.get_current_phase(plant.key or "")
            days_in_phase = current_phase_info["days_in_phase"]

            rules = phase_service.get_transition_rules(plant.current_phase_key)
            for rule in rules:
                if (
                    rule.trigger_type == "time_based"
                    and rule.auto_transition_after_days
                    and days_in_phase >= rule.auto_transition_after_days
                ):
                    phase_service.transition_phase(
                        plant.key or "",
                        rule.to_phase_key,
                        reason="auto_time_based",
                    )
                    transitioned += 1
                    logger.info(
                        "auto_transition",
                        plant_key=plant.key,
                        to_phase=rule.to_phase_key,
                    )
                    break
        except Exception as e:
            errors += 1
            logger.error("auto_transition_error", plant_key=plant.key, error=str(e))

    return {"transitioned": transitioned, "errors": errors, "checked": total}
