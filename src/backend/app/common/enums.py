from enum import StrEnum


class PlantCategory(StrEnum):
    INDOOR_HOUSEPLANT = "indoor_houseplant"
    OUTDOOR_ORNAMENTAL = "outdoor_ornamental"
    OUTDOOR_VEGETABLE = "outdoor_vegetable"
    BALCONY_PLANT = "balcony_plant"
    SUCCULENT_CACTUS = "succulent_cactus"
    TROPICAL_FOLIAGE = "tropical_foliage"
    ORCHID = "orchid"
    HERB = "herb"
    BULB_TUBER = "bulb_tuber"


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
    CORM = "corm"


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
    WINDOWSILL = "windowsill"
    BALCONY = "balcony"
    GROW_TENT = "grow_tent"


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
    CLAY_PEBBLES = "clay_pebbles"
    PERLITE = "perlite"
    LIVING_SOIL = "living_soil"
    PEAT = "peat"
    ROCKWOOL_SLAB = "rockwool_slab"
    ROCKWOOL_PLUG = "rockwool_plug"
    VERMICULITE = "vermiculite"
    NONE = "none"
    ORCHID_BARK = "orchid_bark"
    PON_MINERAL = "pon_mineral"
    SPHAGNUM = "sphagnum"
    HYDRO_SOLUTION = "hydro_solution"


class IrrigationStrategy(StrEnum):
    INFREQUENT = "infrequent"
    MODERATE = "moderate"
    FREQUENT = "frequent"
    CONTINUOUS = "continuous"


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


class Suitability(StrEnum):
    YES = "yes"
    LIMITED = "limited"
    NO = "no"


class NutrientDemandLevel(StrEnum):
    HEAVY_FEEDER = "heavy_feeder"
    MEDIUM_FEEDER = "medium_feeder"
    LIGHT_FEEDER = "light_feeder"
    NITROGEN_FIXER = "nitrogen_fixer"


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
    STOCK_SOLUTION = "stock_solution"


class FillType(StrEnum):
    FULL_CHANGE = "full_change"
    TOP_UP = "top_up"
    ADJUSTMENT = "adjustment"


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
    SILICATE = "silicate"


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
    MIXED = "mixed"


class PhaseName(StrEnum):
    GERMINATION = "germination"
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FLUSHING = "flushing"
    DORMANCY = "dormancy"
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
    OOMYCETE = "oomycete"


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
    DORMANT = "dormant"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskCategory(StrEnum):
    TRAINING = "training"
    PRUNING = "pruning"
    AUSGEIZEN = "ausgeizen"
    TRANSPLANT = "transplant"
    FEEDING = "feeding"
    IPM = "ipm"
    HARVEST = "harvest"
    OBSERVATION = "observation"
    MAINTENANCE = "maintenance"
    CARE_REMINDER = "care_reminder"
    SEASONAL = "seasonal"
    PHENOLOGICAL = "phenological"


class ActivityCategory(StrEnum):
    TRAINING_HST = "training_hst"
    TRAINING_LST = "training_lst"
    PRUNING = "pruning"
    AUSGEIZEN = "ausgeizen"
    TRANSPLANT = "transplant"
    HARVEST_PREP = "harvest_prep"
    PROPAGATION = "propagation"
    INSPECTION = "inspection"
    GENERAL = "general"


class TaskTriggerType(StrEnum):
    PHASE_ENTRY = "phase_entry"
    DAYS_AFTER_PHASE = "days_after_phase"
    DAYS_AFTER_PLANTING = "days_after_planting"
    ABSOLUTE_DATE = "absolute_date"
    MANUAL = "manual"
    CONDITIONAL = "conditional"
    GDD_THRESHOLD = "gdd_threshold"
    SEASONAL_MONTH = "seasonal_month"
    PHENOLOGICAL = "phenological"


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


# ── REQ-022 Care Reminders ──


class CareStyleType(StrEnum):
    TROPICAL = "tropical"
    SUCCULENT = "succulent"
    ORCHID = "orchid"
    CALATHEA = "calathea"
    HERB_TROPICAL = "herb_tropical"
    MEDITERRANEAN = "mediterranean"
    FERN = "fern"
    CACTUS = "cactus"
    OUTDOOR_ANNUAL_VEG = "outdoor_annual_veg"
    OUTDOOR_PERENNIAL = "outdoor_perennial"
    CUSTOM = "custom"


class ReminderType(StrEnum):
    WATERING = "watering"
    FERTILIZING = "fertilizing"
    REPOTTING = "repotting"
    PEST_CHECK = "pest_check"
    LOCATION_CHECK = "location_check"
    HUMIDITY_CHECK = "humidity_check"


class ConfirmAction(StrEnum):
    CONFIRMED = "confirmed"
    SNOOZED = "snoozed"
    SKIPPED = "skipped"


class WateringMethod(StrEnum):
    SOAK = "soak"
    DRENCH_AND_DRAIN = "drench_and_drain"
    TOP_WATER = "top_water"
    BOTTOM_WATER = "bottom_water"


# ── REQ-020 Onboarding ──


class ExperienceLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class StarterKitDifficulty(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# ── Watering Schedule ──


class ScheduleMode(StrEnum):
    WEEKDAYS = "weekdays"
    INTERVAL = "interval"


# ── REQ-012 Import ──


class EntityType(StrEnum):
    SPECIES = "species"
    CULTIVAR = "cultivar"
    BOTANICAL_FAMILY = "botanical_family"


class DuplicateStrategy(StrEnum):
    SKIP = "skip"
    UPDATE = "update"
    FAIL = "fail"


class ImportJobStatus(StrEnum):
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    PREVIEW_READY = "preview_ready"
    CONFIRMED = "confirmed"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"


class RowStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    DUPLICATE = "duplicate"


# ── REQ-015 Calendar ──


class CalendarEventCategory(StrEnum):
    TRAINING = "training"
    PRUNING = "pruning"
    TRANSPLANTING = "transplanting"
    FEEDING = "feeding"
    IPM = "ipm"
    HARVEST = "harvest"
    MAINTENANCE = "maintenance"
    PHASE_TRANSITION = "phase_transition"
    TANK_MAINTENANCE = "tank_maintenance"
    WATERING_FORECAST = "watering_forecast"
    CUSTOM = "custom"


class CalendarEventSource(StrEnum):
    TASK = "task"
    PHASE_TRANSITION = "phase_transition"
    MAINTENANCE_LOG = "maintenance_log"
    WATERING = "watering"
    WATERING_FORECAST = "watering_forecast"


CATEGORY_COLORS: dict[CalendarEventCategory, str] = {
    CalendarEventCategory.TRAINING: "#4CAF50",
    CalendarEventCategory.PRUNING: "#8BC34A",
    CalendarEventCategory.TRANSPLANTING: "#795548",
    CalendarEventCategory.FEEDING: "#2196F3",
    CalendarEventCategory.IPM: "#FF9800",
    CalendarEventCategory.HARVEST: "#F44336",
    CalendarEventCategory.MAINTENANCE: "#9E9E9E",
    CalendarEventCategory.PHASE_TRANSITION: "#9C27B0",
    CalendarEventCategory.TANK_MAINTENANCE: "#00BCD4",
    CalendarEventCategory.WATERING_FORECAST: "#42A5F5",
    CalendarEventCategory.CUSTOM: "#607D8B",
}
