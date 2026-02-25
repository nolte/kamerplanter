import math


def calculate_max_capacity(
    area_m2: float,
    plant_spacing_cm: float,
) -> int:
    """Calculate max number of plants fitting in area with given spacing."""
    if plant_spacing_cm <= 0 or area_m2 <= 0:
        return 0
    spacing_m = plant_spacing_cm / 100.0
    area_per_plant = spacing_m * spacing_m
    return int(math.floor(area_m2 / area_per_plant))


def calculate_optimal_range(
    area_m2: float,
    plant_spacing_cm: float,
    density_factor_low: float = 0.7,
    density_factor_high: float = 0.9,
) -> tuple[int, int]:
    """Calculate optimal plant count range (min, max) for an area.
    Uses density factors to account for walkways, equipment, etc.
    """
    max_cap = calculate_max_capacity(area_m2, plant_spacing_cm)
    return (
        max(1, int(math.floor(max_cap * density_factor_low))),
        int(math.floor(max_cap * density_factor_high)),
    )


def calculate_plants_per_m2(plant_spacing_cm: float) -> float:
    """Calculate plant density per square meter."""
    if plant_spacing_cm <= 0:
        return 0.0
    spacing_m = plant_spacing_cm / 100.0
    return 1.0 / (spacing_m * spacing_m)
