from __future__ import annotations

from app.domain.models.phase import NutrientProfile, RequirementProfile

# Fallback defaults used when no YAML profile data is provided.
# These match the values formerly in config/constants.py.
_DEFAULT_PROFILES: dict[str, dict] = {
    "seedling": {
        "requirement": {
            "light_ppfd_target": 200,
            "photoperiod_hours": 18.0,
            "temperature_day_c": 24.0,
            "temperature_night_c": 20.0,
            "humidity_day_percent": 70,
            "humidity_night_percent": 75,
            "vpd_range": (0.4, 0.8),
        },
        "nutrient": {"npk_ratio": (1, 1, 1), "target_ec_ms": 0.8, "target_ph": 6.0},
    },
    "vegetative": {
        "requirement": {
            "light_ppfd_target": 400,
            "photoperiod_hours": 18.0,
            "temperature_day_c": 25.0,
            "temperature_night_c": 20.0,
            "humidity_day_percent": 60,
            "humidity_night_percent": 65,
            "vpd_range": (0.8, 1.2),
        },
        "nutrient": {"npk_ratio": (3, 1, 2), "target_ec_ms": 1.5, "target_ph": 6.0},
    },
    "flowering": {
        "requirement": {
            "light_ppfd_target": 600,
            "photoperiod_hours": 12.0,
            "temperature_day_c": 26.0,
            "temperature_night_c": 20.0,
            "humidity_day_percent": 50,
            "humidity_night_percent": 55,
            "vpd_range": (1.0, 1.5),
        },
        "nutrient": {"npk_ratio": (1, 3, 2), "target_ec_ms": 1.8, "target_ph": 6.0},
    },
    "flushing": {
        "requirement": {
            "light_ppfd_target": 400,
            "photoperiod_hours": 12.0,
            "temperature_day_c": 25.0,
            "temperature_night_c": 20.0,
            "humidity_day_percent": 60,
            "humidity_night_percent": 65,
            "vpd_range": (0.8, 1.2),
        },
        "nutrient": {"npk_ratio": (0, 0, 0), "target_ec_ms": 0.0, "target_ph": 6.0},
    },
    "ripening": {
        "requirement": {
            "light_ppfd_target": 500,
            "photoperiod_hours": 12.0,
            "temperature_day_c": 24.0,
            "temperature_night_c": 18.0,
            "humidity_day_percent": 45,
            "humidity_night_percent": 50,
            "vpd_range": (1.2, 1.6),
        },
        "nutrient": {"npk_ratio": (0, 1, 2), "target_ec_ms": 1.2, "target_ph": 6.0},
    },
    "dormancy": {
        "requirement": {
            "light_ppfd_target": 400,
            "photoperiod_hours": 18.0,
            "temperature_day_c": 25.0,
            "temperature_night_c": 20.0,
            "humidity_day_percent": 60,
            "humidity_night_percent": 65,
            "vpd_range": (0.4, 0.8),
        },
        "nutrient": {"npk_ratio": (3, 1, 2), "target_ec_ms": 1.5, "target_ph": 6.0},
    },
}


class ResourceProfileGenerator:
    """Generates default resource profiles for growth phases.

    Accepts phase profile data (typically loaded from YAML seed data).
    Falls back to built-in defaults when no data is provided.
    """

    def __init__(self, phase_profiles: dict[str, dict] | None = None) -> None:
        self._profiles = phase_profiles or _DEFAULT_PROFILES

    def generate_requirement_profile(self, phase_name: str, phase_key: str = "") -> RequirementProfile:
        """Generate a requirement profile for a given phase."""
        profile = self._profiles.get(phase_name, {})
        req = profile.get("requirement", {})

        vpd_range = req.get("vpd_range", (0.8, 1.2))
        vpd_target = (vpd_range[0] + vpd_range[1]) / 2

        return RequirementProfile(
            phase_key=phase_key,
            light_ppfd_target=req.get("light_ppfd_target", 400),
            photoperiod_hours=req.get("photoperiod_hours", 18.0),
            temperature_day_c=req.get("temperature_day_c", 25.0),
            temperature_night_c=req.get("temperature_night_c", 20.0),
            humidity_day_percent=req.get("humidity_day_percent", 60),
            humidity_night_percent=req.get("humidity_night_percent", 65),
            vpd_target_kpa=round(vpd_target, 2),
        )

    def generate_nutrient_profile(self, phase_name: str, phase_key: str = "") -> NutrientProfile:
        """Generate a nutrient profile for a given phase."""
        profile = self._profiles.get(phase_name, {})
        nut = profile.get("nutrient", {})

        npk = nut.get("npk_ratio", (3, 1, 2))

        return NutrientProfile(
            phase_key=phase_key,
            npk_ratio=tuple(npk),
            target_ec_ms=nut.get("target_ec_ms", 1.5),
            target_ph=nut.get("target_ph", 6.0),
        )

    @staticmethod
    def from_yaml_phases(default_phases: list[dict]) -> ResourceProfileGenerator:
        """Construct a generator from YAML default_phases data.

        Each phase dict may contain 'requirement_profile' and 'nutrient_profile' sub-dicts.
        """
        profiles: dict[str, dict] = {}
        for phase in default_phases:
            name = phase["name"]
            entry: dict = {}
            if "requirement_profile" in phase:
                rp = phase["requirement_profile"]
                entry["requirement"] = {
                    "light_ppfd_target": rp["light_ppfd_target"],
                    "photoperiod_hours": rp["photoperiod_hours"],
                    "temperature_day_c": rp["temperature_day_c"],
                    "temperature_night_c": rp["temperature_night_c"],
                    "humidity_day_percent": rp["humidity_day_percent"],
                    "humidity_night_percent": rp["humidity_night_percent"],
                    "vpd_range": tuple(rp["vpd_range"]),
                }
            if "nutrient_profile" in phase:
                np_data = phase["nutrient_profile"]
                entry["nutrient"] = {
                    "npk_ratio": tuple(np_data["npk_ratio"]),
                    "target_ec_ms": np_data["target_ec_ms"],
                    "target_ph": np_data["target_ph"],
                }
            if entry:
                profiles[name] = entry
        return ResourceProfileGenerator(profiles)

    def get_vpd_ranges(self) -> dict[str, tuple[float, float]]:
        """Extract VPD ranges from the loaded profile data."""
        result: dict[str, tuple[float, float]] = {}
        for phase_name, data in self._profiles.items():
            req = data.get("requirement", {})
            vpd = req.get("vpd_range")
            if vpd:
                result[phase_name] = tuple(vpd)  # type: ignore[assignment]
        return result
