from app.config.constants import EC_DEFAULTS, NPK_DEFAULTS, PHOTOPERIOD_DEFAULTS, VPD_RANGES
from app.domain.models.phase import NutrientProfile, RequirementProfile


class ResourceProfileGenerator:
    """Generates default resource profiles for growth phases."""

    def generate_requirement_profile(self, phase_name: str, phase_key: str = "") -> RequirementProfile:
        """Generate a default requirement profile for a given phase."""
        vpd_range = VPD_RANGES.get(phase_name, (0.8, 1.2))
        vpd_target = (vpd_range[0] + vpd_range[1]) / 2
        photoperiod = PHOTOPERIOD_DEFAULTS.get(phase_name, 18.0)

        # Default temps vary by phase
        temp_day = 25.0
        temp_night = 20.0
        humidity_day = 60
        humidity_night = 65
        ppfd = 400

        if phase_name == "seedling":
            temp_day = 24.0
            temp_night = 20.0
            humidity_day = 70
            humidity_night = 75
            ppfd = 200
        elif phase_name == "flowering":
            temp_day = 26.0
            temp_night = 20.0
            humidity_day = 50
            humidity_night = 55
            ppfd = 600
        elif phase_name == "ripening":
            temp_day = 24.0
            temp_night = 18.0
            humidity_day = 45
            humidity_night = 50
            ppfd = 500

        return RequirementProfile(
            phase_key=phase_key,
            light_ppfd_target=ppfd,
            photoperiod_hours=photoperiod,
            temperature_day_c=temp_day,
            temperature_night_c=temp_night,
            humidity_day_percent=humidity_day,
            humidity_night_percent=humidity_night,
            vpd_target_kpa=round(vpd_target, 2),
        )

    def generate_nutrient_profile(self, phase_name: str, phase_key: str = "") -> NutrientProfile:
        """Generate a default nutrient profile for a given phase."""
        npk = NPK_DEFAULTS.get(phase_name, (3, 1, 2))
        ec = EC_DEFAULTS.get(phase_name, 1.5)

        return NutrientProfile(
            phase_key=phase_key,
            npk_ratio=npk,
            target_ec_ms=ec,
            target_ph=6.0,
        )
