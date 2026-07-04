from datetime import UTC, datetime

import structlog

from app.common.dependencies import (
    get_lifecycle_repo,
    get_phase_service,
    get_plant_repo,
    get_site_repo,
)
from app.common.enums import TransitionTriggerType
from app.domain.calculators.sun_calculator import calculate_sun_times
from app.domain.engines.transition_trigger_evaluator import TransitionTriggerEvaluator
from app.tasks import celery_app

logger = structlog.get_logger()


def _day_length_for_plant(plant, site_repo) -> float | None:
    """Effective outdoor day length (hours) for the plant's site, or None when
    no site / GPS is known (the photoperiod trigger is then skipped). Indoor
    light-schedule photoperiod (REQ-018) is a separate follow-up."""
    if not plant.site_key:
        return None
    site = site_repo.get_site_by_key(plant.site_key)
    if site is None or site.gps_coordinates is None:
        return None
    lat, lon = site.gps_coordinates
    times = calculate_sun_times(lat, lon, datetime.now(UTC).date(), site.timezone)
    return float(times["day_length_hours"])


@celery_app.task(name="check_auto_transitions")
def check_auto_transitions() -> dict:
    """Check active plants for automatic phase transitions.

    Evaluates time-based (elapsed days), photoperiod-based (E1) and
    vernalization-based (E2) triggers. gdd-based wiring needs a per-plant GDD
    accumulation source and is a follow-up.
    """
    plant_repo = get_plant_repo()
    phase_service = get_phase_service()
    lifecycle_repo = get_lifecycle_repo()
    site_repo = get_site_repo()
    evaluator = TransitionTriggerEvaluator()

    transitioned = 0
    errors = 0

    plants, total = plant_repo.get_all(offset=0, limit=1000, all_tenants=True)  # system task: all tenants
    for plant in plants:
        if plant.removed_on is not None:
            continue
        if not plant.current_phase_key:
            continue

        try:
            current_phase_info = phase_service.get_current_phase(plant.key or "")
            days_in_phase = current_phase_info["days_in_phase"]
            lifecycle = lifecycle_repo.get_lifecycle_by_species(plant.species_key)

            rules = phase_service.get_transition_rules(plant.current_phase_key)
            for rule in rules:
                fire = False
                reason = ""

                if (
                    rule.trigger_type == TransitionTriggerType.TIME_BASED
                    and rule.auto_transition_after_days
                    and days_in_phase >= rule.auto_transition_after_days
                ):
                    fire, reason = True, "auto_time_based"
                elif rule.trigger_type == TransitionTriggerType.PHOTOPERIOD_BASED and lifecycle:
                    day_length = _day_length_for_plant(plant, site_repo)
                    if day_length is not None and evaluator.photoperiod_should_fire(
                        lifecycle.photoperiod_type,
                        lifecycle.critical_day_length_hours,
                        day_length,
                    ):
                        fire, reason = True, "auto_photoperiod"
                elif (
                    rule.trigger_type == TransitionTriggerType.VERNALIZATION_BASED
                    and lifecycle
                    and evaluator.vernalization_should_fire(
                        lifecycle.vernalization_min_days,
                        plant.chill_days_accumulated,
                    )
                ):
                    fire, reason = True, "auto_vernalization"

                if fire:
                    phase_service.transition_phase(plant.key or "", rule.to_phase_key, reason=reason)
                    transitioned += 1
                    logger.info(
                        "auto_transition",
                        plant_key=plant.key,
                        to_phase=rule.to_phase_key,
                        trigger=rule.trigger_type.value,
                    )
                    break
        except Exception as e:
            errors += 1
            logger.error("auto_transition_error", plant_key=plant.key, error=str(e))

    return {"transitioned": transitioned, "errors": errors, "checked": total}
