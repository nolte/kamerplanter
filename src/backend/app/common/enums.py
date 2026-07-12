from enum import StrEnum


class DataOrigin(StrEnum):
    """Data-provenance / ownership marker for master-data records (REQ-001 / REQ-011).

    Drives the read-only / deletion-protection logic in the frontend
    (UI-NFR-018): ``system`` and ``enrichment`` records are curated and
    read-only, ``tenant`` records are user-owned and editable. Values mirror the
    frontend ``DataOrigin`` union in ``OriginChip.tsx`` exactly.
    """

    SYSTEM = "system"
    ENRICHMENT = "enrichment"
    IMPORT = "import"
    TENANT = "tenant"


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


class GraftType(StrEnum):
    """Graft union technique (REQ-017 §2 GraftType)."""

    WHIP = "whip"  # Kopulationsschnitt
    CLEFT = "cleft"  # Spaltpfropfen
    APPROACH = "approach"  # Annäherungspfropfen
    BUD = "bud"  # Okulation


class GraftCompatibilityLevel(StrEnum):
    """Taxonomy-derived graft-compatibility verdict (REQ-017 §3)."""

    COMPATIBLE = "compatible"  # same genus
    POSSIBLY_COMPATIBLE = "possibly_compatible"  # same family, different genus
    INCOMPATIBLE = "incompatible"  # different family


class PropagationEventStatus(StrEnum):
    """Lifecycle status of a single propagation attempt (REQ-017)."""

    IN_PROGRESS = "in_progress"
    ROOTED = "rooted"
    TRANSPLANTED = "transplanted"
    COMPLETED = "completed"
    FAILED = "failed"


class PropagationBatchStatus(StrEnum):
    """Lifecycle status of a propagation batch (REQ-017 §2 BatchStatus)."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PhenotypeCategory(StrEnum):
    """Phenotype-note category (REQ-017 §2 PhenotypeCategory)."""

    MORPHOLOGY = "morphology"
    AROMA = "aroma"
    FLAVOR = "flavor"
    VIGOR = "vigor"
    RESISTANCE = "resistance"
    YIELD = "yield"
    POTENCY = "potency"
    OTHER = "other"


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


class SeedType(StrEnum):
    """Reproduction / propagation type of a cultivar (REQ-008/REQ-017, Plan WP-6f).

    Replaces the former free-text ``Cultivar.seed_type``. Values are derived from
    the reproduction types actually present in the seed data (``open_pollinated``,
    ``f1_hybrid``, ``clone``) plus botanically sensible additions (``f2``,
    ``landrace``). The legacy free-text value ``cultivar`` is folded onto
    ``CLONE`` by the model validator for backward compatibility with old volumes.
    """

    OPEN_POLLINATED = "open_pollinated"  # samenfest / sortenecht
    F1_HYBRID = "f1_hybrid"  # F1-Hybride (nicht sortenecht)
    F2 = "f2"  # F2-Generation aus F1-Aussaat (aufspaltend)
    LANDRACE = "landrace"  # Landsorte / regional angepasste Population
    CLONE = "clone"  # vegetativ vermehrt (Steckling, Teilung, Meristem)


class ToxicitySeverity(StrEnum):
    """Severity of a species' toxicity (REQ-001 — toxicity object).

    Distinct from the flat ``Species.toxicity_severity`` passthrough, which uses a
    different scale (low/moderate/high) and is intentionally not auto-mapped onto
    this canonical enum.
    """

    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class LightGermination(StrEnum):
    """Light requirement for seed germination (REQ-001 seed_profile, REQ-006 sowing)."""

    LIGHT = "light"  # light germinator (Lichtkeimer) — do not cover the seed
    DARK = "dark"  # dark germinator (Dunkelkeimer) — cover the seed
    INDIFFERENT = "indifferent"


class SeedPretreatment(StrEnum):
    """Pre-sowing seed treatment to break dormancy (REQ-001 seed_profile)."""

    COLD_STRATIFICATION = "cold_stratification"
    WARM_STRATIFICATION = "warm_stratification"
    SCARIFICATION = "scarification"
    PRESOAK = "presoak"


class StressTolerance(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TransitionTriggerType(StrEnum):
    TIME_BASED = "time_based"
    MANUAL = "manual"
    EVENT_BASED = "event_based"
    CONDITIONAL = "conditional"
    GDD_BASED = "gdd_based"
    # ── REQ-003 Lifecycle-Audit II (E1/E2) ──
    PHOTOPERIOD_BASED = "photoperiod_based"
    VERNALIZATION_BASED = "vernalization_based"


class TransitionTrigger(StrEnum):
    """How a phase transition was initiated.

    ``AUTO`` — the Celery ``check_auto_transitions`` scan advanced the plant on a
    time/photoperiod/vernalization trigger. ``MANUAL`` — a user drove the change
    through the API. REQ-003 D10 clonal continuation only spawns a pup on an
    ``AUTO`` transition (Q1): a manual correction into the terminal phase must not
    create a clonal descendant.
    """

    AUTO = "auto"
    MANUAL = "manual"


class GrowthDeterminacy(StrEnum):
    """Whether a species finishes at a terminal phase or keeps a stable
    productive phase with concurrent growth/flower/fruit (REQ-003 E4)."""

    DETERMINATE = "determinate"
    INDETERMINATE = "indeterminate"
    SEMI_DETERMINATE = "semi_determinate"


class TerminationType(StrEnum):
    """How a plant instance's lifecycle ended (REQ-003 E5). Distinguishes the
    planned end (harvested/senesced) from an unplanned loss (died) and a user
    cancellation."""

    HARVESTED = "harvested"
    SENESCED = "senesced"
    DIED = "died"
    CANCELLED = "cancelled"


class MaturityStage(StrEnum):
    """Maturity stage of a perennial across its productive life (REQ-003 D-series).

    Drives the juvenile-skip of reproductive phases and yield expectations.
    """

    JUVENILE = "juvenile"  # too young to bear (age < first_bearing_year)
    PRODUCTIVE = "productive"
    DECLINING = "declining"  # past the expected productive span


class TerminationCause(StrEnum):
    """Cause of an unplanned plant loss — only set when termination_type='died'
    (REQ-003 E5). Feeds survival-rate / failure-cause analytics."""

    DISEASE = "disease"
    PEST = "pest"
    FROST = "frost"
    HEAT = "heat"
    DROUGHT = "drought"
    WATERLOGGING = "waterlogging"
    NEGLECT = "neglect"
    MECHANICAL = "mechanical"
    UNKNOWN = "unknown"


class SiteType(StrEnum):
    OUTDOOR = "outdoor"
    GREENHOUSE = "greenhouse"
    INDOOR = "indoor"
    WINDOWSILL = "windowsill"
    BALCONY = "balcony"
    GROW_TENT = "grow_tent"


#: REQ-047 §3.4/§3.6 — single source of truth for the frost-/overwintering-relevant
#: site types. A site of one of these types is exposed to outdoor winter frost, so a
#: plant on it carries a winter season and (when not winter-hardy) an overwintering
#: profile: season materialisation, the eager create/move trigger, the move-indoors
#: profile removal and the per-plant hardiness status all key off this ONE set.
#: BALCONY is included — a balcony is a frost-exposed outdoor location and its
#: container/balcony plants need winter protection just like ground/greenhouse ones.
#: INDOOR / WINDOWSILL / GROW_TENT stay excluded (climate-controlled, no winter).
#: Defining it once here structurally prevents the drift between the two services
#: that previously caused a bug.
OVERWINTERING_SITE_TYPES = frozenset({SiteType.OUTDOOR, SiteType.GREENHOUSE, SiteType.BALCONY})


#: REQ-002/REQ-046 — single source of truth for the "outdoor / weather-relevant"
#: site types, i.e. the types for which GPS coordinates, weather sources and
#: frost warnings make sense. It deliberately mirrors ``OVERWINTERING_SITE_TYPES``:
#: a site exposed to outdoor winter frost is, by the same token, a site whose
#: local weather (temperature, precipitation, frost) drives its plant care.
#: BALCONY is included — a balcony is a frost-exposed outdoor location, so its
#: plants benefit from GPS-based weather data and frost warnings just like
#: ground/greenhouse ones. Previously the frontend only unlocked GPS/weather for
#: OUTDOOR/GREENHOUSE, contradicting the frost classification above; keeping this
#: set aligned with ``OVERWINTERING_SITE_TYPES`` structurally prevents that drift.
#: INDOOR / WINDOWSILL / GROW_TENT stay excluded (climate-controlled, no weather).
WEATHER_RELEVANT_SITE_TYPES = frozenset({SiteType.OUTDOOR, SiteType.GREENHOUSE, SiteType.BALCONY})


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


class SuccessionPlanStatus(StrEnum):
    """REQ-013 §2 — lifecycle state of a succession (staggered sowing) plan."""

    PLANNED = "planned"
    ACTIVE = "active"
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
    CALMAG = "calmag"


class NutrientReleaseSpeed(StrEnum):
    """Nutrient release speed for organic/area-based fertilizers (REQ-004 W-013)."""

    IMMEDIATE = "immediate"
    WEEKS = "weeks"
    MONTHS = "months"
    SEASON_LONG = "season_long"


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
    # Nutrient-plan / EC phase vocabulary. `harvest` was retired as a phase
    # (issue #306): feeding harvest phases → `ripening`, 0-0-0 flush → `flushing`.
    # `harvest` survives only as an activity/task category, not a phase.
    GERMINATION = "germination"
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    RIPENING = "ripening"
    FLUSHING = "flushing"
    DORMANCY = "dormancy"


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


# ── REQ-008 Post-Harvest ──


class PostHarvestStage(StrEnum):
    """REQ-008 §5 (U-006) — per-batch post-harvest state machine.

    Forward-only lifecycle: a batch dries, then cures, is put into storage and
    finally released for consumption/sale. Backward transitions are rejected by
    the stage engine (a batch cannot become wetter again).
    """

    DRYING = "drying"
    CURING = "curing"
    STORED = "stored"
    RELEASED = "released"


class DryingMethod(StrEnum):
    """REQ-008 §3 — how a batch is being dried (drives duration estimates)."""

    HANG_DRY = "hang_dry"
    RACK_DRY = "rack_dry"
    DEHYDRATOR = "dehydrator"
    AIR_CURE = "air_cure"


class PostHarvestSpeciesType(StrEnum):
    """REQ-008 §3 — coarse produce class steering drying/curing behaviour."""

    FLOWER = "flower"
    HERB = "herb"
    ROOT = "root"
    FRUIT = "fruit"
    MUSHROOM = "mushroom"


class MoldAlertSeverity(StrEnum):
    """REQ-008 §2 — severity of an automatically raised mold warning."""

    WARNING = "warning"
    CRITICAL = "critical"


class StorageVisualCondition(StrEnum):
    """REQ-008 §2 — visual grading of a stored/curing batch."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    CONCERNING = "concerning"
    CRITICAL = "critical"


class StorageAromaQuality(StrEnum):
    """REQ-008 §2 — aroma grading; ``moldy``/``off`` signal spoilage."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    OFF = "off"
    MOLDY = "moldy"


class PesticideResidueStatus(StrEnum):
    """REQ-008 §5 / REQ-010 — residue clearance state carried on a batch."""

    UNTESTED = "untested"
    CLEAN = "clean"
    WITHIN_LIMITS = "within_limits"
    RESIDUE_DETECTED = "residue_detected"


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
    # Categories emitted by the task-template editor (TaskTemplateDialog.tsx).
    # Added additively — no existing value is removed (alt-volume seed-read
    # crash trap). i18n keys under enums.taskCategory.* already exist for all.
    WATERING = "watering"
    PEST_CONTROL = "pest_control"
    MONITORING = "monitoring"
    CLEANING = "cleaning"


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
    # REQ-047 §2.5 season-/dormancy-driven control reminders
    DORMANCY_HEALTH_CHECK = "dormancy_health_check"
    QUARTER_CLIMATE_CHECK = "quarter_climate_check"


# ── REQ-022 v2.5 Overwintering / Winter hardiness ──


class HardinessRating(StrEnum):
    """REQ-022 §OverwinteringProfile — overwintering strategy for a plant."""

    HARDY = "hardy"  # stays outdoors without protection
    NEEDS_PROTECTION = "needs_protection"  # fleece / mulch / earthing up
    FROST_FREE = "frost_free"  # move into a frost-free winter quarter (5-12 C)
    DIG_AND_STORE = "dig_and_store"  # dig tubers/bulbs up and store them


class WinterAction(StrEnum):
    """REQ-022 §OverwinteringProfile — concrete winter protection measure."""

    NONE = "none"
    MULCH = "mulch"
    FLEECE = "fleece"
    EARTH_UP = "earth_up"
    MOVE_INDOORS = "move_indoors"
    DIG_STORE = "dig_store"
    WRAP = "wrap"


class SpringAction(StrEnum):
    """REQ-022 §OverwinteringProfile — spring uncovering/reactivation action."""

    UNCOVER = "uncover"
    MOVE_OUTDOORS = "move_outdoors"
    REPLANT = "replant"
    PRUNE = "prune"
    HARDEN_OFF = "harden_off"


class TuberStatus(StrEnum):
    """REQ-022 §Knollen-/Zwiebel-Zyklus — tuber/bulb annual lifecycle status."""

    PLANTED = "planted"
    GROWING = "growing"
    DIG_PENDING = "dig_pending"
    DRYING = "drying"
    STORED = "stored"
    PRE_SPROUTING = "pre_sprouting"


class WinterQuarterLight(StrEnum):
    """REQ-022 §OverwinteringProfile — light level in the winter quarter."""

    BRIGHT = "bright"
    SEMI_BRIGHT = "semi_bright"
    DARK = "dark"


class WinterWatering(StrEnum):
    """REQ-022 §OverwinteringProfile — watering regime during overwintering."""

    NONE = "none"
    MINIMAL = "minimal"
    REDUCED = "reduced"
    NORMAL = "normal"


class WinterHardinessLight(StrEnum):
    """REQ-022 §Winterhärte-Ampel / REQ-039 — hardiness traffic light."""

    GREEN = "green"  # winter hardy in situ
    YELLOW = "yellow"  # needs protection in situ
    RED = "red"  # must be relocated / dug up


class SeasonPhase(StrEnum):
    """REQ-047 §2.2 — season state machine of an outdoor/greenhouse site.

    Directed cycle (one per ``season_year``):
    growing → pre_winter → winter_dormancy → pre_spring → growing.
    """

    GROWING = "growing"  # vegetation period — no winter activity
    PRE_WINTER = "pre_winter"  # winter approaching: preparation / action window
    WINTER_DORMANCY = "winter_dormancy"  # protected rest / in-situ dormancy (dormancy care mode)
    PRE_SPRING = "pre_spring"  # late winter / spring: reactivation window


class SeasonTriggerTier(StrEnum):
    """REQ-047 §1 — which cascade tier produced the current season state.

    Best-source-wins cascade: live weather → climatological (site frost dates) →
    calendar (hemisphere presets). Surfaced for UI transparency.
    """

    LIVE = "live"
    CLIMATOLOGICAL = "climatological"
    CALENDAR = "calendar"


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
    # REQ-010 — user-contributed reference photos for a global pest (Phase 1:
    # tenant-private gallery; Phase 2 may promote selected images globally).
    PEST_REFERENCE = "pest_reference"


class PestImageStatus(StrEnum):
    """REQ-010 — lifecycle state of a user-contributed pest reference image.

    Phase 1 only ever uses ``PRIVATE`` (the image stays inside the contributing
    tenant). ``PROMOTED`` is reserved for the later global-curation phase, where
    an admin may surface a tenant image as a global reference — the model field
    exists now so no migration is needed when that phase ships.
    """

    PRIVATE = "private"
    PROMOTED = "promoted"


class PestFindingCategory(StrEnum):
    """REQ-044 §4.2 — what kind of thing a pest-detection finding represents.

    ``BENEFICIAL`` findings are never presented as a pest to fight (§9.1).
    ``UNKNOWN`` is the open-set reject/abstention class (WP-4.3 / WP-5).
    """

    PEST = "pest"
    BENEFICIAL = "beneficial"
    SYMPTOM = "symptom"
    UNKNOWN = "unknown"


class DiagnosisCategory(StrEnum):
    """REQ-038 — what kind of condition a CV disease-diagnosis class represents.

    ``DEFICIENCY`` has no REQ-010 stammdaten collection yet, so a deficiency
    finding keeps ``matched_disease_key``/``matched_pest_key`` null and is matched
    via REQ-036 symptom slugs instead. ``HEALTHY`` is the negative class.
    """

    DISEASE = "disease"
    DEFICIENCY = "deficiency"
    PEST = "pest"
    HEALTHY = "healthy"


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


# ── REQ-026 Aquaponics ──────────────────────────────────────────────────


class AquaponicSystemType(StrEnum):
    """REQ-026 §3 — coupled fish/plant loop configuration."""

    MEDIA_BED = "media_bed"  # clay-pebble grow bed (integrated biofilter)
    DWC = "dwc"  # deep water culture
    NFT = "nft"  # nutrient film technique
    HYBRID = "hybrid"  # media bed combined with DWC/NFT
    WICKING_BED = "wicking_bed"  # wicking irrigation from reservoir


class CyclingStatus(StrEnum):
    """REQ-026 §3 — biofilter nitrification maturity state."""

    NEW = "new"  # freshly filled, no bacteria
    CYCLING = "cycling"  # colonisation in progress, ammonia/nitrite spikes
    CYCLED = "cycled"  # stable nitrification
    DORMANT = "dormant"  # winter dormancy below 10 C


class TemperatureZone(StrEnum):
    """REQ-026 §3 — fish/plant temperature compatibility band."""

    COLDWATER = "coldwater"  # 8-18 C
    TEMPERATE = "temperate"  # 18-24 C
    WARMWATER = "warmwater"  # 24-30 C


class BiofilterType(StrEnum):
    """REQ-026 §3 — nitrification filter media type."""

    MEDIA_BED_INTEGRATED = "media_bed_integrated"  # clay pebbles as biofilter
    MBBR = "mbbr"  # moving bed biofilm reactor (K1)
    TRICKLE = "trickle"  # trickle filter (lava, bioballs)
    FLUIDIZED_BED = "fluidized_bed"  # fluidized sand bed


class ClarifierType(StrEnum):
    """REQ-026 §3 — solids separation device type."""

    SWIRL = "swirl"
    SETTLING = "settling"
    DRUM = "drum"
    SCREEN = "screen"


class FishFeedType(StrEnum):
    """REQ-026 §3 — physical form of the fish feed used in a feeding event."""

    PELLET = "pellet"
    FLAKE = "flake"
    LIVE = "live"
    FROZEN = "frozen"
    PASTE = "paste"


class FishFeedingResponse(StrEnum):
    """REQ-026 §3 — observed feeding behaviour (refused is a health warning)."""

    EAGER = "eager"
    NORMAL = "normal"
    REDUCED = "reduced"
    REFUSED = "refused"


class FishFeedCategory(StrEnum):
    """REQ-026 §3 — trophic category of a fish species (drives protein default)."""

    CARNIVORE = "carnivore"
    OMNIVORE = "omnivore"
    HERBIVORE = "herbivore"


class AquaponicSupplementType(StrEnum):
    """REQ-026 §3 — fish-safe nutrient supplements allowed in aquaponics."""

    FE_DTPA = "fe_dtpa"  # iron chelate, stable up to pH 7.5
    FE_EDDHA = "fe_eddha"  # iron chelate, stable up to pH 9.0
    KOH = "koh"  # potassium hydroxide (K + pH up)
    K2CO3 = "k2co3"  # potassium carbonate (K + pH up)
    CA_OH_2 = "ca_oh_2"  # calcium hydroxide (Ca + pH up)
    MGSO4 = "mgso4"  # epsom salt (Mg, pH neutral)
    MNSO4 = "mnso4"  # manganese sulfate
    H3BO3 = "h3bo3"  # boric acid (narrow toxicity window)
    ZNSO4 = "znso4"  # zinc sulfate (narrow toxicity window)


class WaterTestSource(StrEnum):
    """REQ-026 §2 — provenance of a water-test measurement."""

    MANUAL = "manual"
    SENSOR = "sensor"
    TEST_KIT = "test_kit"


class TankRole(StrEnum):
    """REQ-026 §2 — role a tank plays inside an aquaponic system."""

    FISH_TANK = "fish_tank"
    BIOFILTER = "biofilter"
    SUMP = "sump"
    CLARIFIER = "clarifier"
    MINERALIZATION = "mineralization"
    GROWBED_RESERVOIR = "growbed_reservoir"


class PestDetectionNextStep(StrEnum):
    """REQ-044 §5.1 — suggested follow-up. Never an automatic treatment (§0)."""

    IPM_INSPECTION = "ipm_inspection"
    NONE = "none"


# ── REQ-018 Environment control / actuator system ──────────────────────


class ActuatorType(StrEnum):
    """REQ-018 §3 — controllable device category (19 types)."""

    LIGHT = "light"
    EXHAUST_FAN = "exhaust_fan"
    CIRCULATION_FAN = "circulation_fan"
    HEATER = "heater"
    COOLER = "cooler"
    HUMIDIFIER = "humidifier"
    DEHUMIDIFIER = "dehumidifier"
    CO2_DOSER = "co2_doser"
    IRRIGATION_VALVE = "irrigation_valve"
    PUMP = "pump"
    DOSING_PUMP = "dosing_pump"
    CHILLER = "chiller"
    AIR_PUMP = "air_pump"
    UV_STERILIZER = "uv_sterilizer"
    SHADE_SCREEN = "shade_screen"
    ROOF_VENT = "roof_vent"
    ENERGY_SCREEN = "energy_screen"
    FOGGER = "fogger"
    GENERIC_SWITCH = "generic_switch"


class ActuatorCapability(StrEnum):
    """REQ-018 §3 — capability an actuator exposes."""

    ON_OFF = "on_off"
    DIMMABLE = "dimmable"
    SPEED_CONTROL = "speed_control"
    TEMPERATURE_SETPOINT = "temperature_setpoint"
    TIMER = "timer"
    SPECTRUM_CONTROL = "spectrum_control"
    VOLUME_DOSING = "volume_dosing"


class ActuatorProtocol(StrEnum):
    """REQ-018 §1 — transport used to reach the physical device."""

    HOME_ASSISTANT = "home_assistant"
    MQTT = "mqtt"
    MANUAL = "manual"


class ScheduleType(StrEnum):
    """REQ-018 §2 — recurrence model of a control schedule."""

    DAILY = "daily"
    WEEKLY = "weekly"
    INTERVAL = "interval"
    SUNRISE_SUNSET = "sunrise_sunset"


class RuleType(StrEnum):
    """REQ-018 §2 — automation-rule evaluation model."""

    THRESHOLD = "threshold"
    RANGE = "range"
    DELTA = "delta"
    COMPOUND = "compound"


class ConditionOperator(StrEnum):
    """REQ-018 §3 — comparison operator of a rule condition."""

    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    BETWEEN = "between"
    OUTSIDE = "outside"


class ActionCommand(StrEnum):
    """REQ-018 §3 — command issued when a rule fires."""

    TURN_ON = "turn_on"
    TURN_OFF = "turn_off"
    SET_VALUE = "set_value"
    INCREASE = "increase"
    DECREASE = "decrease"


class ControlEventSource(StrEnum):
    """REQ-018 §2 — origin of a logged control action."""

    SCHEDULE = "schedule"
    RULE = "rule"
    PHASE_CHANGE = "phase_change"
    MANUAL = "manual"
    SAFETY = "safety"
    FALLBACK_TASK = "fallback_task"


class EmergencyStopScenario(StrEnum):
    """REQ-018 §1 — predefined emergency-stop scenario."""

    WATER_LEAK = "water_leak"
    CO2_LEAK = "co2_leak"
    FIRE_ALARM = "fire_alarm"


class EquipmentType(StrEnum):
    """REQ-016 §3.1 — type of an operating resource (equipment)."""

    TOOL = "tool"
    CONSUMABLE = "consumable"
    SENSOR = "sensor"
    LIGHTING = "lighting"
    PUMP = "pump"
    FILTER = "filter"
    CONTAINER = "container"
    CLEANING_AGENT = "cleaning_agent"
    OTHER = "other"


class EquipmentStatus(StrEnum):
    """REQ-016 §3.1 — lifecycle status of an equipment item."""

    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    STORED = "stored"
    DEFECTIVE = "defective"
    RETIRED = "retired"


class StockTransactionType(StrEnum):
    """REQ-016 §3.1 — kind of an InvenTree stock adjustment."""

    REMOVE = "remove"
    ADD = "add"
    COUNT = "count"


class StockTransactionStatus(StrEnum):
    """REQ-016 §3.1 — sync status of a stock transaction."""

    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"


class LinkableEntityCollection(StrEnum):
    """REQ-016 §3.2 — collections that may be linked to an InvenTree part.

    Mirrors the ``has_inventree_ref`` graph edge domain
    (``fertilizers | tanks | equipment → inventree_references``). Constraining the
    reference-link request to this allowlist (SEC/IT-003) prevents an arbitrary
    collection name from being pointed at InvenTree; a value outside the allowlist
    is rejected with HTTP 422.
    """

    FERTILIZERS = "fertilizers"
    TANKS = "tanks"
    EQUIPMENT = "equipment"


# ── REQ-033 MCP server (Model Context Protocol) ──────────────────────────────
class McpPermission(StrEnum):
    """The three MCP tool-permission classes (REQ-033 §4.4).

    Assigned to a service account *indirectly* through its tenant role: a
    read-only diagnose bot is a ``viewer``, a day-to-day bot is a ``grower`` and a
    one-off onboarding agent is an ``admin``. ``mcp.setup`` is the most
    destructive class (site/location deletion) and is therefore admin-only, so a
    diary bot can never delete a location — not even through a macro tool
    (AC-S6).
    """

    READ = "mcp.read"
    WRITE = "mcp.write"
    SETUP = "mcp.setup"


class McpToolStatus(StrEnum):
    """Audit-log outcome of a single MCP tool invocation (REQ-033 §3, §4.6)."""

    OK = "ok"
    DENIED = "denied"
    ERROR = "error"
    DRY_RUN = "dry_run"


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
