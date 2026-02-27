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
    NFT = "nft"
    EBB_FLOW = "ebb_flow"


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


class TankType(StrEnum):
    NUTRIENT = "nutrient"
    IRRIGATION = "irrigation"
    RESERVOIR = "reservoir"
    RECIRCULATION = "recirculation"


class TankMaterial(StrEnum):
    PLASTIC = "plastic"
    STAINLESS_STEEL = "stainless_steel"
    GLASS = "glass"
    IBC = "ibc"


class MaintenanceType(StrEnum):
    WATER_CHANGE = "water_change"
    CLEANING = "cleaning"
    SANITIZATION = "sanitization"
    CALIBRATION = "calibration"
    FILTER_CHANGE = "filter_change"
    PUMP_INSPECTION = "pump_inspection"


class MaintenancePriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MaintenanceStatus(StrEnum):
    OK = "ok"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"


class FertilizerType(StrEnum):
    BASE = "base"
    SUPPLEMENT = "supplement"
    BOOSTER = "booster"
    BIOLOGICAL = "biological"
    PH_ADJUSTER = "ph_adjuster"
    ORGANIC = "organic"


class PhEffect(StrEnum):
    ACIDIC = "acidic"
    ALKALINE = "alkaline"
    NEUTRAL = "neutral"


class ApplicationMethod(StrEnum):
    FERTIGATION = "fertigation"
    DRENCH = "drench"
    FOLIAR = "foliar"
    TOP_DRESS = "top_dress"
    ANY = "any"


class Bioavailability(StrEnum):
    IMMEDIATE = "immediate"
    SLOW_RELEASE = "slow_release"
    MICROBIAL_DEPENDENT = "microbial_dependent"


class IncompatibilitySeverity(StrEnum):
    CRITICAL = "critical"
    WARNING = "warning"
    MINOR = "minor"


class WaterSource(StrEnum):
    TANK = "tank"
    TAP = "tap"
    OSMOSE = "osmose"
    RAINWATER = "rainwater"
    DISTILLED = "distilled"
    WELL = "well"


class PhaseName(StrEnum):
    GERMINATION = "germination"
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    HARVEST = "harvest"


# ── REQ-010 IPM ──


class PestPressureLevel(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TreatmentType(StrEnum):
    CULTURAL = "cultural"
    BIOLOGICAL = "biological"
    CHEMICAL = "chemical"
    MECHANICAL = "mechanical"


class PathogenType(StrEnum):
    FUNGAL = "fungal"
    BACTERIAL = "bacterial"
    VIRAL = "viral"
    PHYSIOLOGICAL = "physiological"


class PlantPart(StrEnum):
    LEAF = "leaf"
    STEM = "stem"
    ROOT = "root"
    FLOWER = "flower"
    FRUIT = "fruit"


class TreatmentApplicationMethod(StrEnum):
    SPRAY = "spray"
    DRENCH = "drench"
    GRANULAR = "granular"
    RELEASE = "release"
    CULTURAL = "cultural"


class EfficacyRating(StrEnum):
    EFFECTIVE = "effective"
    PARTIAL = "partial"
    INEFFECTIVE = "ineffective"


# ── REQ-007 Harvest ──


class HarvestType(StrEnum):
    PARTIAL = "partial"
    FINAL = "final"
    CONTINUOUS = "continuous"


class QualityGrade(StrEnum):
    A_PLUS = "a_plus"
    A = "a"
    B = "b"
    C = "c"
    D = "d"


class HarvestIndicatorType(StrEnum):
    TRICHOME = "trichome"
    COLOR = "color"
    BRIX = "brix"
    SIZE = "size"
    DAYS_SINCE_FLOWERING = "days_since_flowering"
    AROMA = "aroma"
    TEXTURE = "texture"
    FOLIAGE = "foliage"


class RipenessStage(StrEnum):
    IMMATURE = "immature"
    APPROACHING = "approaching"
    PEAK = "peak"
    OVERRIPE = "overripe"


# ── REQ-006 Tasks ──


class TaskStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCategory(StrEnum):
    TRAINING = "training"
    PRUNING = "pruning"
    TRANSPLANT = "transplant"
    FEEDING = "feeding"
    IPM = "ipm"
    HARVEST = "harvest"
    OBSERVATION = "observation"
    MAINTENANCE = "maintenance"


class TaskTriggerType(StrEnum):
    PHASE_ENTRY = "phase_entry"
    DAYS_AFTER_PHASE = "days_after_phase"
    DAYS_AFTER_PLANTING = "days_after_planting"
    ABSOLUTE_DATE = "absolute_date"
    MANUAL = "manual"
    CONDITIONAL = "conditional"


class StressLevel(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DependencyType(StrEnum):
    BLOCKS = "blocks"
    REQUIRES = "requires"
    RECOMMENDED_AFTER = "recommended_after"


class SkillLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TimeOfDay(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    LIGHTS_OFF = "lights_off"


# ── REQ-023 Auth ──


class AuthProviderType(StrEnum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    APPLE = "apple"
    OIDC = "oidc"


class EmailVerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"


# ── REQ-024 Tenants ──


class TenantType(StrEnum):
    PERSONAL = "personal"
    ORGANIZATION = "organization"


class TenantRole(StrEnum):
    ADMIN = "admin"
    GROWER = "grower"
    VIEWER = "viewer"


class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class InvitationType(StrEnum):
    EMAIL = "email"
    LINK = "link"
