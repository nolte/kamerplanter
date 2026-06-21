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
    SUBSHRUB = "subshrub"
    TREE = "tree"
    VINE = "vine"
    GROUNDCOVER = "groundcover"
    GRASS = "grass"
    SUCCULENT = "succulent"
    BULB_GEOPHYTE = "bulb_geophyte"
    FERN = "fern"
    AQUATIC = "aquatic"
    EPIPHYTE = "epiphyte"


class RootType(StrEnum):
    FIBROUS = "fibrous"
    TAPROOT = "taproot"
    TUBEROUS = "tuberous"
    BULBOUS = "bulbous"
    CORM = "corm"


class PropagationMethod(StrEnum):
    SEED = "seed"
    CUTTING = "cutting"
    LEAF_CUTTING = "leaf_cutting"
    DIVISION = "division"
    RHIZOME_DIVISION = "rhizome_division"
    BULB = "bulb"
    BULBIL = "bulbil"
    TUBER = "tuber"
    OFFSET = "offset"
    RUNNER = "runner"
    GRAFTING = "grafting"
    LAYERING = "layering"
    AIR_LAYERING = "air_layering"
    WATER_PROPAGATION = "water_propagation"
    TISSUE_CULTURE = "tissue_culture"
    SPORE = "spore"
    SELF_SEEDING = "self_seeding"


class WoodStage(StrEnum):
    """Cutting maturity stage — drives the propagation time-window per method (REQ-017)."""

    SOFTWOOD = "softwood"
    SEMI_HARDWOOD = "semi_hardwood"
    HARDWOOD = "hardwood"
    HERBACEOUS = "herbaceous"


class PropagationDifficulty(StrEnum):
    EASY = "easy"
    MODERATE = "moderate"
    DIFFICULT = "difficult"


class PhotoperiodType(StrEnum):
    SHORT_DAY = "short_day"
    LONG_DAY = "long_day"
    DAY_NEUTRAL = "day_neutral"


class CycleType(StrEnum):
    ANNUAL = "annual"
    BIENNIAL = "biennial"
    PERENNIAL = "perennial"


class FloweringStrategy(StrEnum):
    """Reproductive strategy — orthogonal to lifespan (REQ-003, Plan WP-4)."""

    MONOCARPIC = "monocarpic"  # flowers once, then dies (e.g. agave, many bamboos)
    POLYCARPIC = "polycarpic"  # flowers repeatedly over years (default for most perennials)


class HarvestPattern(StrEnum):
    """Lifetime harvest pattern of a species (REQ-007, Plan WP-6a).

    Distinct from HarvestType, which describes a single harvest *event*.
    """

    SINGLE = "single"  # one (or few) concentrated harvests, often the whole plant
    CONTINUOUS = "continuous"  # repeated pick-over within one season (indeterminate)
    PERENNIAL = "perennial"  # recurring harvests across years, after a juvenile phase


class HarvestedPart(StrEnum):
    """The plant part that is harvested (REQ-007, Plan WP-6b)."""

    FRUIT = "fruit"
    SEED = "seed"
    LEAF = "leaf"
    ROOT = "root"
    TUBER = "tuber"
    BULB = "bulb"
    FLOWER_BUD = "flower_bud"
    FLOWER = "flower"
    STEM = "stem"
    WHOLE_PLANT = "whole_plant"


class ClimactericClass(StrEnum):
    """Post-harvest ripening behaviour of fruit (REQ-008, Plan WP-6d).

    The third value is required: several species are genuine borderline cases.
    """

    CLIMACTERIC = "climacteric"  # ripens after harvest (apple, banana, tomato)
    NON_CLIMACTERIC = "non_climacteric"  # does not ripen further (strawberry, citrus)
    ATYPICAL = "atypical"  # contested / borderline (honeydew, blueberry, fig, pepper)


class DtmReference(StrEnum):
    """Reference point for days_to_maturity (REQ-007, Plan WP-6c)."""

    DIRECT_SEED = "direct_seed"
    TRANSPLANT = "transplant"


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


class PlantingRunStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE = "active"
    HARVESTING = "harvesting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiaryEntryType(StrEnum):
    OBSERVATION = "observation"
    PROBLEM = "problem"
    MILESTONE = "milestone"
    MEASUREMENT = "measurement"
    PHOTO = "photo"
    NOTE = "note"


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
    PROTIST = "protist"


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


class PestSeverity(StrEnum):
    """Schadpotenzial eines Schädlings (REQ-010 — Detailseite)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


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
    DAYS_SINCE_SOWING = "days_since_sowing"
    AROMA = "aroma"
    TEXTURE = "texture"
    FOLIAGE = "foliage"


class RipenessStage(StrEnum):
    IMMATURE = "immature"
    APPROACHING = "approaching"
    PEAK = "peak"
    OVERRIPE = "overripe"


# ── REQ-006 Tasks ──


class WorkflowTargetType(StrEnum):
    PLANT_INSTANCE = "plant_instance"
    PLANTING_RUN = "planting_run"
    LOCATION = "location"
    TANK = "tank"


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
    # Outdoor presets — REQ-022 v2.5 §3.1
    OUTDOOR_ANNUAL_VEG = "outdoor_annual_veg"
    OUTDOOR_ANNUAL_ORNAMENTAL = "outdoor_annual_ornamental"
    OUTDOOR_PERENNIAL = "outdoor_perennial"
    FRUIT_TREE = "fruit_tree"
    BERRY_SHRUB = "berry_shrub"
    ROSE = "rose"
    FROST_TENDER_TUBER = "frost_tender_tuber"
    FROST_TENDER_CONTAINER = "frost_tender_container"
    WINTER_VEGETABLE = "winter_vegetable"
    SPRING_BULB = "spring_bulb"
    CUSTOM = "custom"


class ReminderType(StrEnum):
    WATERING = "watering"
    FERTILIZING = "fertilizing"
    REPOTTING = "repotting"
    PEST_CHECK = "pest_check"
    LOCATION_CHECK = "location_check"
    HUMIDITY_CHECK = "humidity_check"
    # REQ-022 v2.5 outdoor + overwintering reminder types §3.2
    DEADHEADING = "deadheading"
    TUBER_DIG = "tuber_dig"
    STORAGE_CHECK = "storage_check"
    SPRING_UNCOVER = "spring_uncover"
    WINTER_PROTECTION = "winter_protection"


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


class ModuleVisibilityState(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    # Note: 'default' is NOT stored — absence of a key means 'default'.


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


class AttachmentCategory(StrEnum):
    """NFR-013 §2.2 — logical category an attachment belongs to.

    Drives the storage key prefix and the DSGVO erasure scope mapping.
    """

    DIARY = "diary"
    IPM = "ipm"
    HARVEST = "harvest"
    POST_HARVEST = "post_harvest"
    TASK = "task"
    IMPORT = "import"
    EXPORT = "export"
    ID_RECOGNITION = "id_recognition"
    TENANT_EXPORT = "tenant_export"
    PLANT = "plant"


class PestFindingCategory(StrEnum):
    """REQ-044 §4.2 — what kind of thing a pest-detection finding represents.

    ``BENEFICIAL`` findings are never presented as a pest to fight (§9.1).
    ``UNKNOWN`` is the open-set reject/abstention class (WP-4.3 / WP-5).
    """

    PEST = "pest"
    BENEFICIAL = "beneficial"
    SYMPTOM = "symptom"
    UNKNOWN = "unknown"


class PestFindingMode(StrEnum):
    """REQ-044 — detection mode a finding originates from.

    ``DIRECT`` = the pest/beneficial itself is visible (Mode 1, with box).
    ``SYMPTOM`` = inferred from damage pattern without a visible insect (Mode 2).
    """

    DIRECT = "direct"
    SYMPTOM = "symptom"


class PestDetectionSource(StrEnum):
    """REQ-044 §5.1 — which backend produced a detection result."""

    CLOUD_KINDWISE = "cloud_kindwise"
    LOCAL_DETECTOR = "local_detector"
    LOCAL_SYMPTOM = "local_symptom"


class PestDetectionTrigger(StrEnum):
    """REQ-044 §5.1 — what initiated a detection."""

    USER_PHOTO = "user_photo"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


class PestDetectionNextStep(StrEnum):
    """REQ-044 §5.1 — suggested follow-up. Never an automatic treatment (§0)."""

    IPM_INSPECTION = "ipm_inspection"
    NONE = "none"


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
