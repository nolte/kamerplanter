"""Domain constants for VPD ranges, NPK defaults, and system parameters."""

# VPD target ranges (kPa) per growth phase
VPD_RANGES: dict[str, tuple[float, float]] = {
    "seedling": (0.4, 0.8),
    "vegetative": (0.8, 1.2),
    "flowering": (1.0, 1.5),
    "ripening": (1.2, 1.6),
    "dormancy": (0.4, 0.8),
    "flushing": (0.8, 1.2),
}

# Default NPK ratios per phase (N:P:K)
NPK_DEFAULTS: dict[str, tuple[int, int, int]] = {
    "seedling": (1, 1, 1),
    "vegetative": (3, 1, 2),
    "flowering": (1, 3, 2),
    "ripening": (0, 1, 2),
    "flushing": (0, 0, 0),
}

# Default EC targets (mS/cm) per phase
EC_DEFAULTS: dict[str, float] = {
    "seedling": 0.8,
    "vegetative": 1.5,
    "flowering": 1.8,
    "ripening": 1.2,
    "flushing": 0.0,
}

# EC limits per substrate type (min, max)
EC_LIMITS: dict[str, tuple[float, float]] = {
    "hydro_solution": (0.5, 3.0),
    "coco": (0.8, 2.2),
    "soil": (0.4, 1.6),
    "living_soil": (0.0, 0.8),
    "rockwool_slab": (0.5, 2.5),
    "rockwool_plug": (0.5, 2.5),
    "clay_pebbles": (0.5, 2.5),
    "perlite": (0.5, 2.5),
}

# Photoperiod defaults per phase (hours)
PHOTOPERIOD_DEFAULTS: dict[str, float] = {
    "seedling": 18.0,
    "vegetative": 18.0,
    "flowering": 12.0,
    "ripening": 12.0,
    "flushing": 12.0,
}

# Inspection frequency multipliers by phase
INSPECTION_PHASE_MULTIPLIERS: dict[str, float] = {
    "vegetative": 1.0,
    "flowering": 0.5,
    "harvest": 0.33,
}

# Inspection frequency multipliers by pest pressure
INSPECTION_PRESSURE_MULTIPLIERS: dict[str, float] = {
    "none": 1.0,
    "low": 0.8,
    "medium": 0.5,
    "high": 0.33,
    "critical": 0.25,
}

# Flushing durations per substrate type (days)
FLUSHING_DURATIONS: dict[str, tuple[int, int]] = {
    "hydro_solution": (7, 10),
    "coco": (10, 14),
    "soil": (14, 21),
}

# Default rotation window in years
DEFAULT_ROTATION_WINDOW_YEARS: int = 3

# Fertilizer mixing order priorities
MIXING_ORDER: dict[str, int] = {
    "silicone": 1,
    "calmag": 2,
    "base_a": 3,
    "base_b": 4,
    "supplement": 5,
    "ph_adjuster": 100,
}

# Safety limits
MAX_DOSAGE_ML_PER_LITER: float = 20.0
OPTIMAL_MIXING_TEMP_RANGE: tuple[float, float] = (18.0, 22.0)
RUNOFF_TARGET_PERCENT: tuple[float, float] = (15.0, 20.0)
EC_DRIFT_WARNING_THRESHOLD: float = 0.5
PH_DRIFT_WARNING_THRESHOLD: float = 1.0
MAX_CONSECUTIVE_SAME_TREATMENT: int = 3

# Drying targets
DRYING_WEIGHT_LOSS_PERCENT: dict[str, tuple[float, float]] = {
    "cannabis": (60.0, 65.0),
    "herbs": (60.0, 65.0),
}

# Curing jar humidity target
CURING_HUMIDITY_RANGE: tuple[float, float] = (55.0, 65.0)
MAX_DRYING_TEMP_C: float = 21.0
MOLD_PREVENTION_MAX_RH: float = 68.0
