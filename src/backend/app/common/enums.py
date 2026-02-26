from enum import StrEnum


class GrowthHabit(StrEnum):
    HERB = "herb"
    SHRUB = "shrub"
    TREE = "tree"
    VINE = "vine"
    GROUNDCOVER = "groundcover"


class RootType(StrEnum):
    FIBROUS = "fibrous"
    TAPROOT = "taproot"
    TUBEROUS = "tuberous"
    BULBOUS = "bulbous"


class PhotoperiodType(StrEnum):
    SHORT_DAY = "short_day"
    LONG_DAY = "long_day"
    DAY_NEUTRAL = "day_neutral"


class CycleType(StrEnum):
    ANNUAL = "annual"
    BIENNIAL = "biennial"
    PERENNIAL = "perennial"


class StressTolerance(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TransitionTriggerType(StrEnum):
    TIME_BASED = "time_based"
    MANUAL = "manual"
    EVENT_BASED = "event_based"
    CONDITIONAL = "conditional"


class SiteType(StrEnum):
    OUTDOOR = "outdoor"
    GREENHOUSE = "greenhouse"
    INDOOR = "indoor"


class LightType(StrEnum):
    NATURAL = "natural"
    LED = "led"
    HPS = "hps"
    CMH = "cmh"
    MIXED = "mixed"


class IrrigationSystem(StrEnum):
    MANUAL = "manual"
    DRIP = "drip"
    HYDRO = "hydro"
    MIST = "mist"


class SubstrateType(StrEnum):
    SOIL = "soil"
    COCO = "coco"
    ROCKWOOL = "rockwool"
    CLAY_PEBBLES = "clay_pebbles"
    PERLITE = "perlite"
    LIVING_SOIL = "living_soil"
    HYDRO_SOLUTION = "hydro_solution"


class NutrientDemand(StrEnum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"


class RootDepth(StrEnum):
    SHALLOW = "shallow"
    MEDIUM = "medium"
    DEEP = "deep"


class FrostTolerance(StrEnum):
    SENSITIVE = "sensitive"
    MODERATE = "moderate"
    HARDY = "hardy"
    VERY_HARDY = "very_hardy"


class PollinationType(StrEnum):
    INSECT = "insect"
    WIND = "wind"
    SELF = "self"


class WaterRetention(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BufferCapacity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Orientation(StrEnum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"


class SyncStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class AuthType(StrEnum):
    NONE = "none"
    API_KEY = "api_key"


class SyncTrigger(StrEnum):
    MANUAL = "manual"
    CELERY_SCHEDULE = "celery_schedule"


class PlantTrait(StrEnum):
    DISEASE_RESISTANT = "disease_resistant"
    PEST_RESISTANT = "pest_resistant"
    HIGH_YIELD = "high_yield"
    COMPACT = "compact"
    DROUGHT_TOLERANT = "drought_tolerant"
    COLD_HARDY = "cold_hardy"
    HEAT_TOLERANT = "heat_tolerant"
    EARLY_MATURING = "early_maturing"
    LONG_SEASON = "long_season"
    ORNAMENTAL = "ornamental"
    HEIRLOOM = "heirloom"
    HYBRID = "hybrid"
    F1 = "f1"


class PlantingRunType(StrEnum):
    MONOCULTURE = "monoculture"
    CLONE = "clone"
    MIXED_CULTURE = "mixed_culture"


class PlantingRunStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    HARVESTING = "harvesting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EntryRole(StrEnum):
    PRIMARY = "primary"
    COMPANION = "companion"
    TRAP_CROP = "trap_crop"
