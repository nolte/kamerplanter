"""REQ-047 §3.5 — toggle the winter-rest care plan on the CareProfile.

On entry into ``winter_dormancy`` the plant's :class:`CareProfile` switches into
the dormancy-care mode: the discrete ``dormancy_watering`` regime and the winter
control interval are materialised from the plant's ``OverwinteringProfile``. On the
``pre_spring`` / ``growing`` transition the mode is cleared and the plant returns to
seasonal normal operation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from app.domain.interfaces.care_reminder_repository import ICareReminderRepository
    from app.domain.models.care_reminder import CareProfile
    from app.domain.models.overwintering_profile import OverwinteringProfile

logger = structlog.get_logger(__name__)


class DormancyCareActivator:
    def __init__(self, care_repo: ICareReminderRepository) -> None:
        self._care_repo = care_repo

    def activate(
        self,
        plant_key: str,
        overwintering_profile: OverwinteringProfile | None,
    ) -> CareProfile | None:
        """Switch the plant's CareProfile into dormancy-care mode."""
        profile = self._care_repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            return None

        watering = None
        interval = 30
        if overwintering_profile is not None:
            if overwintering_profile.winter_watering is not None:
                watering = overwintering_profile.winter_watering.value
            if overwintering_profile.storage_check_interval_days:
                interval = overwintering_profile.storage_check_interval_days

        merged = profile.model_copy(
            update={
                "dormancy_care_mode": True,
                "dormancy_watering": watering,
                "dormancy_check_interval_days": interval,
            }
        )
        result = self._care_repo.update_profile(profile.key or "", merged)
        logger.info("dormancy_care_activated", plant_key=plant_key, dormancy_watering=watering)
        return result

    def deactivate(self, plant_key: str) -> CareProfile | None:
        """Leave dormancy-care mode, returning to seasonal normal operation."""
        profile = self._care_repo.get_profile_by_plant_key(plant_key)
        if profile is None:
            return None
        merged = profile.model_copy(update={"dormancy_care_mode": False, "dormancy_watering": None})
        result = self._care_repo.update_profile(profile.key or "", merged)
        logger.info("dormancy_care_deactivated", plant_key=plant_key)
        return result
