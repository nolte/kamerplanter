from typing import TYPE_CHECKING

from app.common.enums import ApplicationMethod, IrrigationSystem

if TYPE_CHECKING:
    from app.domain.models.watering_event import WateringEvent

HYDRO_SYSTEMS = {IrrigationSystem.HYDRO, IrrigationSystem.NFT, IrrigationSystem.EBB_FLOW}
MAX_VOLUME_PER_SLOT = 20.0


class WateringEngine:
    """Pure logic for watering event validation — no DB access."""

    def validate_and_warn(
        self,
        event: WateringEvent,
        irrigation_system: IrrigationSystem | None,
    ) -> list[dict]:
        """Return non-blocking warnings for the watering event."""
        warnings: list[dict] = []

        # Fertigation on manual system
        if (
            event.application_method == ApplicationMethod.FERTIGATION
            and irrigation_system == IrrigationSystem.MANUAL
        ):
            warnings.append({
                "type": "fertigation_on_manual",
                "message": "Fertigation selected but location uses manual irrigation",
            })

        # Drench on automated system without is_supplemental
        if (
            event.application_method == ApplicationMethod.DRENCH
            and irrigation_system is not None
            and irrigation_system in HYDRO_SYSTEMS
            and not event.is_supplemental
        ):
            warnings.append({
                "type": "drench_on_auto",
                "message": "Drench on automated system without supplemental flag",
            })

        # Volume exceeds threshold per plant
        volume_per_plant = event.volume_liters / len(event.plant_keys)
        if volume_per_plant > MAX_VOLUME_PER_SLOT:
            warnings.append({
                "type": "high_volume",
                "message": (
                    f"Volume per plant ({volume_per_plant:.1f} L) "
                    f"exceeds {MAX_VOLUME_PER_SLOT} L threshold"
                ),
            })

        return warnings
