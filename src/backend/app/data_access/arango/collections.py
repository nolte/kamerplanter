from arango.database import StandardDatabase

# Document collections
SPECIES = "species"
CULTIVARS = "cultivars"
BOTANICAL_FAMILIES = "botanical_families"
LIFECYCLE_CONFIGS = "lifecycle_configs"
GROWTH_PHASES = "growth_phases"
SITES = "sites"
LOCATIONS = "locations"
SLOTS = "slots"
SUBSTRATES = "substrates"
SUBSTRATE_BATCHES = "substrate_batches"
PLANT_INSTANCES = "plant_instances"
REQUIREMENT_PROFILES = "requirement_profiles"
NUTRIENT_PROFILES = "nutrient_profiles"
PHASE_TRANSITION_RULES = "phase_transition_rules"
PHASE_HISTORIES = "phase_histories"
EXTERNAL_SOURCES = "external_sources"
EXTERNAL_MAPPINGS = "external_mappings"
SYNC_RUNS = "sync_runs"
PLANTING_RUNS = "planting_runs"
PLANTING_RUN_ENTRIES = "planting_run_entries"
TANKS = "tanks"
TANK_STATES = "tank_states"
MAINTENANCE_LOGS = "maintenance_logs"
MAINTENANCE_SCHEDULES = "maintenance_schedules"
FERTILIZERS = "fertilizers"
FERTILIZER_STOCKS = "fertilizer_stocks"
NUTRIENT_PLANS = "nutrient_plans"
NUTRIENT_PLAN_PHASE_ENTRIES = "nutrient_plan_phase_entries"
FEEDING_EVENTS = "feeding_events"
WATERING_EVENTS = "watering_events"
TANK_FILL_EVENTS = "tank_fill_events"

# REQ-010 IPM
PESTS = "pests"
DISEASES = "diseases"
TREATMENTS = "treatments"
INSPECTIONS = "inspections"
TREATMENT_APPLICATIONS = "treatment_applications"

# REQ-007 Harvest
HARVEST_INDICATORS = "harvest_indicators"
HARVEST_OBSERVATIONS = "harvest_observations"
HARVEST_BATCHES = "harvest_batches"
QUALITY_ASSESSMENTS = "quality_assessments"
YIELD_METRICS = "yield_metrics"

# REQ-006 Tasks
WORKFLOW_TEMPLATES = "workflow_templates"
TASK_TEMPLATES = "task_templates"
TASKS = "tasks"
WORKFLOW_EXECUTIONS = "workflow_executions"
TASK_COMMENTS = "task_comments"
TASK_AUDIT_ENTRIES = "task_audit_entries"

# REQ-023 Auth
USERS = "users"
AUTH_PROVIDERS = "auth_providers"
REFRESH_TOKENS = "refresh_tokens"
OIDC_PROVIDER_CONFIGS = "oidc_provider_configs"
API_KEYS = "api_keys"

# REQ-024 Tenants
TENANTS = "tenants"
MEMBERSHIPS = "memberships"
INVITATIONS = "invitations"
LOCATION_ASSIGNMENTS = "location_assignments"

# REQ-022 Care Reminders
CARE_PROFILES = "care_profiles"
CARE_CONFIRMATIONS = "care_confirmations"

# REQ-020 Onboarding
STARTER_KITS = "starter_kits"
ONBOARDING_STATES = "onboarding_states"
USER_PREFERENCES = "user_preferences"

# REQ-012 Import
IMPORT_JOBS = "import_jobs"

# REQ-015 Calendar
CALENDAR_FEEDS = "calendar_feeds"

# REQ-005 Sensors
SENSORS = "sensors"

# REQ-002 Location Types
LOCATION_TYPES = "location_types"

# System Settings (singleton)
SYSTEM_SETTINGS = "system_settings"

# Unified Watering Log (replaces WateringEvents + FeedingEvents)
WATERING_LOGS = "watering_logs"

# Activities (Stammdaten)
ACTIVITIES = "activities"

DOCUMENT_COLLECTIONS = [
    SPECIES,
    CULTIVARS,
    BOTANICAL_FAMILIES,
    LIFECYCLE_CONFIGS,
    GROWTH_PHASES,
    SITES,
    LOCATIONS,
    SLOTS,
    SUBSTRATES,
    SUBSTRATE_BATCHES,
    PLANT_INSTANCES,
    REQUIREMENT_PROFILES,
    NUTRIENT_PROFILES,
    PHASE_TRANSITION_RULES,
    PHASE_HISTORIES,
    EXTERNAL_SOURCES,
    EXTERNAL_MAPPINGS,
    SYNC_RUNS,
    PLANTING_RUNS,
    PLANTING_RUN_ENTRIES,
    TANKS,
    TANK_STATES,
    MAINTENANCE_LOGS,
    MAINTENANCE_SCHEDULES,
    FERTILIZERS,
    FERTILIZER_STOCKS,
    NUTRIENT_PLANS,
    NUTRIENT_PLAN_PHASE_ENTRIES,
    FEEDING_EVENTS,
    WATERING_EVENTS,
    PESTS,
    DISEASES,
    TREATMENTS,
    INSPECTIONS,
    TREATMENT_APPLICATIONS,
    HARVEST_INDICATORS,
    HARVEST_OBSERVATIONS,
    HARVEST_BATCHES,
    QUALITY_ASSESSMENTS,
    YIELD_METRICS,
    WORKFLOW_TEMPLATES,
    TASK_TEMPLATES,
    TASKS,
    WORKFLOW_EXECUTIONS,
    TASK_COMMENTS,
    TASK_AUDIT_ENTRIES,
    USERS,
    AUTH_PROVIDERS,
    REFRESH_TOKENS,
    OIDC_PROVIDER_CONFIGS,
    TENANTS,
    MEMBERSHIPS,
    INVITATIONS,
    LOCATION_ASSIGNMENTS,
    CARE_PROFILES,
    CARE_CONFIRMATIONS,
    STARTER_KITS,
    ONBOARDING_STATES,
    USER_PREFERENCES,
    IMPORT_JOBS,
    CALENDAR_FEEDS,
    API_KEYS,
    TANK_FILL_EVENTS,
    SENSORS,
    SYSTEM_SETTINGS,
    LOCATION_TYPES,
    WATERING_LOGS,
    ACTIVITIES,
]

# Edge collections
BELONGS_TO_FAMILY = "belongs_to_family"
HAS_CULTIVAR = "has_cultivar"
HAS_LIFECYCLE = "has_lifecycle"
CONSISTS_OF = "consists_of"
COMPATIBLE_WITH = "compatible_with"
INCOMPATIBLE_WITH = "incompatible_with"
ROTATION_AFTER = "rotation_after"
CONTAINS = "contains"
HAS_SLOT = "has_slot"
FILLED_WITH = "filled_with"
PLACED_IN = "placed_in"
GROWN_IN = "grown_in"
ADJACENT_TO = "adjacent_to"
NEXT_PHASE = "next_phase"
GOVERNED_BY = "governed_by"
REQUIRES_PROFILE = "requires_profile"
USES_NUTRIENTS = "uses_nutrients"
CURRENT_PHASE = "current_phase"
PHASE_HISTORY_EDGE = "phase_history_edge"
ENRICHED_BY = "enriched_by"
RUN_CONTAINS = "run_contains"
RUN_AT_LOCATION = "run_at_location"
RUN_USES_SUBSTRATE = "run_uses_substrate"
HAS_ENTRY = "has_entry"
ENTRY_FOR_SPECIES = "entry_for_species"
HAS_TANK = "has_tank"
SUPPLIES = "supplies"
FEEDS_FROM = "feeds_from"
HAS_STATE = "has_state"
HAS_MAINTENANCE = "has_maintenance"
HAS_SCHEDULE = "has_schedule"
HAS_COMPONENT = "has_component"
FERT_INCOMPATIBLE = "fert_incompatible"
HAS_STOCK = "has_stock"
FED_BY = "fed_by"
FEEDING_USED = "feeding_used"
HAS_PHASE_ENTRY = "has_phase_entry"
PLAN_USES_FERTILIZER = "plan_uses_fertilizer"
FOLLOWS_PLAN = "follows_plan"
CLONED_FROM = "cloned_from"
WATERED_PLANT = "watered_plant"
SHARES_PEST_RISK = "shares_pest_risk"
FAMILY_COMPATIBLE_WITH = "family_compatible_with"
FAMILY_INCOMPATIBLE_WITH = "family_incompatible_with"

# REQ-010 IPM edges
INSPECTED_BY = "inspected_by"
DETECTED_PEST = "detected_pest"
DETECTED_DISEASE = "detected_disease"
APPLIED_TO_PLANT = "applied_to_plant"
TREATMENT_USES = "treatment_uses"
TARGETS_PEST = "targets_pest"
TARGETS_DISEASE = "targets_disease"
CONTRAINDICATED_WITH = "contraindicated_with"
VULNERABLE_IN_PHASE = "vulnerable_in_phase"

# REQ-007 Harvest edges
HAS_HARVEST_INDICATOR = "has_harvest_indicator"
OBSERVED_FOR_HARVEST = "observed_for_harvest"
USES_INDICATOR = "uses_indicator"
HARVESTED_AS = "harvested_as"
ASSESSED_BY_QUALITY = "assessed_by_quality"
HAS_YIELD_METRIC = "has_yield_metric"

# REQ-006 Task edges
WF_CONTAINS = "wf_contains"
REQUIRES_PHASE = "requires_phase"
HAS_TASK = "has_task"
TASK_BLOCKS = "task_blocks"
INSTANCE_OF = "instance_of"
WF_EXECUTING = "wf_executing"
WF_GENERATED = "wf_generated"
FOLLOWS_WORKFLOW = "follows_workflow"
TASK_HAS_COMMENT = "task_has_comment"
TASK_HAS_AUDIT = "task_has_audit"
TASK_CLONED_FROM = "task_cloned_from"
TASK_RECURS_FROM = "task_recurs_from"
TASK_ASSIGNED_TO = "task_assigned_to"

# REQ-023 Auth edges
HAS_AUTH_PROVIDER = "has_auth_provider"
HAS_SESSION = "has_session"
HAS_API_KEY = "has_api_key"

# REQ-024 Tenant edges
HAS_MEMBERSHIP = "has_membership"
MEMBERSHIP_IN = "membership_in"
HAS_INVITATION = "has_invitation"
BELONGS_TO_TENANT = "belongs_to_tenant"
ASSIGNED_TO_LOCATION = "assigned_to_location"
ASSIGNMENT_FOR = "assignment_for"
ASSIGNMENT_IN_TENANT = "assignment_in_tenant"

# REQ-019 Substrate edges
USES_TYPE = "uses_type"

# REQ-022 Care Reminder edges
HAS_CARE_PROFILE = "has_care_profile"
CONFIRMS_CARE = "confirms_care"
CARE_EVENT_FOR = "care_event_for"

# REQ-014 Tank Fill edges
HAS_FILL_EVENT = "has_fill_event"
MIXED_INTO = "mixed_into"
WATERING_FROM = "watering_from"
GENERATED_TASK = "generated_task"

# REQ-005 Sensor edges
MONITORS_TANK = "monitors_tank"
LOCATED_AT = "located_at"

# Watering Log edges
LOG_SLOT = "log_slot"
LOG_PLANT = "log_plant"
LOG_FERTILIZER = "log_fertilizer"

# Activity edges
TASK_USES_ACTIVITY = "task_uses_activity"

# Watering Schedule edges
RUN_FOLLOWS_PLAN = "run_follows_plan"

# REQ-020 Onboarding edges
INCLUDES_SPECIES = "includes_species"
INCLUDES_CULTIVAR = "includes_cultivar"
INCLUDES_TEMPLATE = "includes_template"
CREATED_BY_WIZARD = "created_by_wizard"

EDGE_COLLECTIONS = [
    BELONGS_TO_FAMILY,
    HAS_CULTIVAR,
    HAS_LIFECYCLE,
    CONSISTS_OF,
    COMPATIBLE_WITH,
    INCOMPATIBLE_WITH,
    ROTATION_AFTER,
    CONTAINS,
    HAS_SLOT,
    FILLED_WITH,
    PLACED_IN,
    GROWN_IN,
    ADJACENT_TO,
    NEXT_PHASE,
    GOVERNED_BY,
    REQUIRES_PROFILE,
    USES_NUTRIENTS,
    CURRENT_PHASE,
    PHASE_HISTORY_EDGE,
    ENRICHED_BY,
    RUN_CONTAINS,
    RUN_AT_LOCATION,
    RUN_USES_SUBSTRATE,
    HAS_ENTRY,
    ENTRY_FOR_SPECIES,
    HAS_TANK,
    SUPPLIES,
    FEEDS_FROM,
    HAS_STATE,
    HAS_MAINTENANCE,
    HAS_SCHEDULE,
    HAS_COMPONENT,
    FERT_INCOMPATIBLE,
    HAS_STOCK,
    FED_BY,
    FEEDING_USED,
    HAS_PHASE_ENTRY,
    PLAN_USES_FERTILIZER,
    FOLLOWS_PLAN,
    CLONED_FROM,
    WATERED_PLANT,
    SHARES_PEST_RISK,
    FAMILY_COMPATIBLE_WITH,
    FAMILY_INCOMPATIBLE_WITH,
    INSPECTED_BY,
    DETECTED_PEST,
    DETECTED_DISEASE,
    APPLIED_TO_PLANT,
    TREATMENT_USES,
    TARGETS_PEST,
    TARGETS_DISEASE,
    CONTRAINDICATED_WITH,
    VULNERABLE_IN_PHASE,
    HAS_HARVEST_INDICATOR,
    OBSERVED_FOR_HARVEST,
    USES_INDICATOR,
    HARVESTED_AS,
    ASSESSED_BY_QUALITY,
    HAS_YIELD_METRIC,
    WF_CONTAINS,
    REQUIRES_PHASE,
    HAS_TASK,
    TASK_BLOCKS,
    INSTANCE_OF,
    WF_EXECUTING,
    WF_GENERATED,
    FOLLOWS_WORKFLOW,
    TASK_HAS_COMMENT,
    TASK_HAS_AUDIT,
    TASK_CLONED_FROM,
    TASK_RECURS_FROM,
    TASK_ASSIGNED_TO,
    HAS_AUTH_PROVIDER,
    HAS_SESSION,
    HAS_API_KEY,
    HAS_MEMBERSHIP,
    MEMBERSHIP_IN,
    HAS_INVITATION,
    BELONGS_TO_TENANT,
    ASSIGNED_TO_LOCATION,
    ASSIGNMENT_FOR,
    ASSIGNMENT_IN_TENANT,
    USES_TYPE,
    HAS_CARE_PROFILE,
    CONFIRMS_CARE,
    CARE_EVENT_FOR,
    INCLUDES_SPECIES,
    INCLUDES_CULTIVAR,
    INCLUDES_TEMPLATE,
    CREATED_BY_WIZARD,
    RUN_FOLLOWS_PLAN,
    MONITORS_TANK,
    LOCATED_AT,
    LOG_SLOT,
    LOG_PLANT,
    LOG_FERTILIZER,
    HAS_FILL_EVENT,
    MIXED_INTO,
    WATERING_FROM,
    GENERATED_TASK,
    TASK_USES_ACTIVITY,
]

GRAPH_NAME = "kamerplanter_graph"

GRAPH_EDGE_DEFINITIONS = [
    {
        "edge_collection": BELONGS_TO_FAMILY,
        "from_vertex_collections": [SPECIES],
        "to_vertex_collections": [BOTANICAL_FAMILIES],
    },
    {
        "edge_collection": HAS_CULTIVAR,
        "from_vertex_collections": [SPECIES],
        "to_vertex_collections": [CULTIVARS],
    },
    {
        "edge_collection": HAS_LIFECYCLE,
        "from_vertex_collections": [SPECIES],
        "to_vertex_collections": [LIFECYCLE_CONFIGS],
    },
    {
        "edge_collection": CONSISTS_OF,
        "from_vertex_collections": [LIFECYCLE_CONFIGS],
        "to_vertex_collections": [GROWTH_PHASES],
    },
    {
        "edge_collection": COMPATIBLE_WITH,
        "from_vertex_collections": [SPECIES],
        "to_vertex_collections": [SPECIES],
    },
    {
        "edge_collection": INCOMPATIBLE_WITH,
        "from_vertex_collections": [SPECIES],
        "to_vertex_collections": [SPECIES],
    },
    {
        "edge_collection": ROTATION_AFTER,
        "from_vertex_collections": [BOTANICAL_FAMILIES],
        "to_vertex_collections": [BOTANICAL_FAMILIES],
    },
    {
        "edge_collection": CONTAINS,
        "from_vertex_collections": [SITES, LOCATIONS],
        "to_vertex_collections": [LOCATIONS],
    },
    {
        "edge_collection": HAS_SLOT,
        "from_vertex_collections": [LOCATIONS],
        "to_vertex_collections": [SLOTS],
    },
    {
        "edge_collection": FILLED_WITH,
        "from_vertex_collections": [SLOTS],
        "to_vertex_collections": [SUBSTRATE_BATCHES],
    },
    {
        "edge_collection": PLACED_IN,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [SLOTS],
    },
    {
        "edge_collection": GROWN_IN,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [SUBSTRATE_BATCHES],
    },
    {
        "edge_collection": ADJACENT_TO,
        "from_vertex_collections": [SLOTS],
        "to_vertex_collections": [SLOTS],
    },
    {
        "edge_collection": NEXT_PHASE,
        "from_vertex_collections": [GROWTH_PHASES],
        "to_vertex_collections": [GROWTH_PHASES],
    },
    {
        "edge_collection": GOVERNED_BY,
        "from_vertex_collections": [GROWTH_PHASES],
        "to_vertex_collections": [PHASE_TRANSITION_RULES],
    },
    {
        "edge_collection": REQUIRES_PROFILE,
        "from_vertex_collections": [GROWTH_PHASES],
        "to_vertex_collections": [REQUIREMENT_PROFILES],
    },
    {
        "edge_collection": USES_NUTRIENTS,
        "from_vertex_collections": [GROWTH_PHASES],
        "to_vertex_collections": [NUTRIENT_PROFILES],
    },
    {
        "edge_collection": CURRENT_PHASE,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [GROWTH_PHASES],
    },
    {
        "edge_collection": PHASE_HISTORY_EDGE,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [PHASE_HISTORIES],
    },
    {
        "edge_collection": ENRICHED_BY,
        "from_vertex_collections": [SPECIES, CULTIVARS],
        "to_vertex_collections": [EXTERNAL_SOURCES],
    },
    {
        "edge_collection": RUN_CONTAINS,
        "from_vertex_collections": [PLANTING_RUNS],
        "to_vertex_collections": [PLANT_INSTANCES],
    },
    {
        "edge_collection": RUN_AT_LOCATION,
        "from_vertex_collections": [PLANTING_RUNS],
        "to_vertex_collections": [LOCATIONS],
    },
    {
        "edge_collection": RUN_USES_SUBSTRATE,
        "from_vertex_collections": [PLANTING_RUNS],
        "to_vertex_collections": [SUBSTRATE_BATCHES],
    },
    {
        "edge_collection": HAS_ENTRY,
        "from_vertex_collections": [PLANTING_RUNS],
        "to_vertex_collections": [PLANTING_RUN_ENTRIES],
    },
    {
        "edge_collection": ENTRY_FOR_SPECIES,
        "from_vertex_collections": [PLANTING_RUN_ENTRIES],
        "to_vertex_collections": [SPECIES],
    },
    {
        "edge_collection": HAS_TANK,
        "from_vertex_collections": [LOCATIONS],
        "to_vertex_collections": [TANKS],
    },
    {
        "edge_collection": SUPPLIES,
        "from_vertex_collections": [TANKS],
        "to_vertex_collections": [LOCATIONS],
    },
    {
        "edge_collection": FEEDS_FROM,
        "from_vertex_collections": [TANKS],
        "to_vertex_collections": [TANKS],
    },
    {
        "edge_collection": HAS_STATE,
        "from_vertex_collections": [TANKS],
        "to_vertex_collections": [TANK_STATES],
    },
    {
        "edge_collection": HAS_MAINTENANCE,
        "from_vertex_collections": [TANKS],
        "to_vertex_collections": [MAINTENANCE_LOGS],
    },
    {
        "edge_collection": HAS_SCHEDULE,
        "from_vertex_collections": [TANKS],
        "to_vertex_collections": [MAINTENANCE_SCHEDULES],
    },
    {
        "edge_collection": HAS_COMPONENT,
        "from_vertex_collections": [FERTILIZERS],
        "to_vertex_collections": [FERTILIZERS],
    },
    {
        "edge_collection": FERT_INCOMPATIBLE,
        "from_vertex_collections": [FERTILIZERS],
        "to_vertex_collections": [FERTILIZERS],
    },
    {
        "edge_collection": HAS_STOCK,
        "from_vertex_collections": [FERTILIZERS],
        "to_vertex_collections": [FERTILIZER_STOCKS],
    },
    {
        "edge_collection": FED_BY,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [FEEDING_EVENTS],
    },
    {
        "edge_collection": FEEDING_USED,
        "from_vertex_collections": [FEEDING_EVENTS],
        "to_vertex_collections": [FERTILIZERS],
    },
    {
        "edge_collection": HAS_PHASE_ENTRY,
        "from_vertex_collections": [NUTRIENT_PLANS],
        "to_vertex_collections": [NUTRIENT_PLAN_PHASE_ENTRIES],
    },
    {
        "edge_collection": PLAN_USES_FERTILIZER,
        "from_vertex_collections": [NUTRIENT_PLAN_PHASE_ENTRIES],
        "to_vertex_collections": [FERTILIZERS],
    },
    {
        "edge_collection": FOLLOWS_PLAN,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [NUTRIENT_PLANS],
    },
    {
        "edge_collection": CLONED_FROM,
        "from_vertex_collections": [NUTRIENT_PLANS],
        "to_vertex_collections": [NUTRIENT_PLANS],
    },
    {
        "edge_collection": WATERED_PLANT,
        "from_vertex_collections": [WATERING_EVENTS],
        "to_vertex_collections": [PLANT_INSTANCES],
    },
    {
        "edge_collection": SHARES_PEST_RISK,
        "from_vertex_collections": [BOTANICAL_FAMILIES],
        "to_vertex_collections": [BOTANICAL_FAMILIES],
    },
    {
        "edge_collection": FAMILY_COMPATIBLE_WITH,
        "from_vertex_collections": [BOTANICAL_FAMILIES],
        "to_vertex_collections": [BOTANICAL_FAMILIES],
    },
    {
        "edge_collection": FAMILY_INCOMPATIBLE_WITH,
        "from_vertex_collections": [BOTANICAL_FAMILIES],
        "to_vertex_collections": [BOTANICAL_FAMILIES],
    },
    # REQ-010 IPM
    {
        "edge_collection": INSPECTED_BY,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [INSPECTIONS],
    },
    {
        "edge_collection": DETECTED_PEST,
        "from_vertex_collections": [INSPECTIONS],
        "to_vertex_collections": [PESTS],
    },
    {
        "edge_collection": DETECTED_DISEASE,
        "from_vertex_collections": [INSPECTIONS],
        "to_vertex_collections": [DISEASES],
    },
    {
        "edge_collection": APPLIED_TO_PLANT,
        "from_vertex_collections": [TREATMENT_APPLICATIONS],
        "to_vertex_collections": [PLANT_INSTANCES],
    },
    {
        "edge_collection": TREATMENT_USES,
        "from_vertex_collections": [TREATMENT_APPLICATIONS],
        "to_vertex_collections": [TREATMENTS],
    },
    {
        "edge_collection": TARGETS_PEST,
        "from_vertex_collections": [TREATMENTS],
        "to_vertex_collections": [PESTS],
    },
    {
        "edge_collection": TARGETS_DISEASE,
        "from_vertex_collections": [TREATMENTS],
        "to_vertex_collections": [DISEASES],
    },
    {
        "edge_collection": CONTRAINDICATED_WITH,
        "from_vertex_collections": [TREATMENTS],
        "to_vertex_collections": [TREATMENTS],
    },
    {
        "edge_collection": VULNERABLE_IN_PHASE,
        "from_vertex_collections": [GROWTH_PHASES],
        "to_vertex_collections": [PESTS, DISEASES],
    },
    # REQ-007 Harvest
    {
        "edge_collection": HAS_HARVEST_INDICATOR,
        "from_vertex_collections": [SPECIES],
        "to_vertex_collections": [HARVEST_INDICATORS],
    },
    {
        "edge_collection": OBSERVED_FOR_HARVEST,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [HARVEST_OBSERVATIONS],
    },
    {
        "edge_collection": USES_INDICATOR,
        "from_vertex_collections": [HARVEST_OBSERVATIONS],
        "to_vertex_collections": [HARVEST_INDICATORS],
    },
    {
        "edge_collection": HARVESTED_AS,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [HARVEST_BATCHES],
    },
    {
        "edge_collection": ASSESSED_BY_QUALITY,
        "from_vertex_collections": [HARVEST_BATCHES],
        "to_vertex_collections": [QUALITY_ASSESSMENTS],
    },
    {
        "edge_collection": HAS_YIELD_METRIC,
        "from_vertex_collections": [HARVEST_BATCHES],
        "to_vertex_collections": [YIELD_METRICS],
    },
    # REQ-006 Tasks
    {
        "edge_collection": WF_CONTAINS,
        "from_vertex_collections": [WORKFLOW_TEMPLATES],
        "to_vertex_collections": [TASK_TEMPLATES],
    },
    {
        "edge_collection": REQUIRES_PHASE,
        "from_vertex_collections": [TASK_TEMPLATES],
        "to_vertex_collections": [GROWTH_PHASES],
    },
    {
        "edge_collection": HAS_TASK,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [TASKS],
    },
    {
        "edge_collection": TASK_BLOCKS,
        "from_vertex_collections": [TASKS],
        "to_vertex_collections": [TASKS],
    },
    {
        "edge_collection": INSTANCE_OF,
        "from_vertex_collections": [TASKS],
        "to_vertex_collections": [TASK_TEMPLATES],
    },
    {
        "edge_collection": WF_EXECUTING,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [WORKFLOW_EXECUTIONS],
    },
    {
        "edge_collection": WF_GENERATED,
        "from_vertex_collections": [WORKFLOW_EXECUTIONS],
        "to_vertex_collections": [TASKS],
    },
    {
        "edge_collection": FOLLOWS_WORKFLOW,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [WORKFLOW_TEMPLATES],
    },
    {
        "edge_collection": TASK_HAS_COMMENT,
        "from_vertex_collections": [TASKS],
        "to_vertex_collections": [TASK_COMMENTS],
    },
    {
        "edge_collection": TASK_HAS_AUDIT,
        "from_vertex_collections": [TASKS],
        "to_vertex_collections": [TASK_AUDIT_ENTRIES],
    },
    {
        "edge_collection": TASK_CLONED_FROM,
        "from_vertex_collections": [TASKS],
        "to_vertex_collections": [TASKS],
    },
    {
        "edge_collection": TASK_RECURS_FROM,
        "from_vertex_collections": [TASKS],
        "to_vertex_collections": [TASKS],
    },
    {
        "edge_collection": TASK_ASSIGNED_TO,
        "from_vertex_collections": [TASKS],
        "to_vertex_collections": [USERS],
    },
    # REQ-023 Auth
    {
        "edge_collection": HAS_AUTH_PROVIDER,
        "from_vertex_collections": [USERS],
        "to_vertex_collections": [AUTH_PROVIDERS],
    },
    {
        "edge_collection": HAS_SESSION,
        "from_vertex_collections": [USERS],
        "to_vertex_collections": [REFRESH_TOKENS],
    },
    {
        "edge_collection": HAS_API_KEY,
        "from_vertex_collections": [USERS],
        "to_vertex_collections": [API_KEYS],
    },
    # REQ-024 Tenants
    {
        "edge_collection": HAS_MEMBERSHIP,
        "from_vertex_collections": [TENANTS],
        "to_vertex_collections": [MEMBERSHIPS],
    },
    {
        "edge_collection": MEMBERSHIP_IN,
        "from_vertex_collections": [USERS],
        "to_vertex_collections": [MEMBERSHIPS],
    },
    {
        "edge_collection": HAS_INVITATION,
        "from_vertex_collections": [TENANTS],
        "to_vertex_collections": [INVITATIONS],
    },
    {
        "edge_collection": BELONGS_TO_TENANT,
        "from_vertex_collections": [SITES, PLANT_INSTANCES, PLANTING_RUNS, TANKS, FERTILIZERS, NUTRIENT_PLANS, TASKS],
        "to_vertex_collections": [TENANTS],
    },
    {
        "edge_collection": ASSIGNED_TO_LOCATION,
        "from_vertex_collections": [LOCATION_ASSIGNMENTS],
        "to_vertex_collections": [LOCATIONS],
    },
    {
        "edge_collection": ASSIGNMENT_FOR,
        "from_vertex_collections": [LOCATION_ASSIGNMENTS],
        "to_vertex_collections": [MEMBERSHIPS],
    },
    {
        "edge_collection": ASSIGNMENT_IN_TENANT,
        "from_vertex_collections": [LOCATION_ASSIGNMENTS],
        "to_vertex_collections": [TENANTS],
    },
    # REQ-019 Substrate
    {
        "edge_collection": USES_TYPE,
        "from_vertex_collections": [SUBSTRATE_BATCHES],
        "to_vertex_collections": [SUBSTRATES],
    },
    # REQ-022 Care Reminders
    {
        "edge_collection": HAS_CARE_PROFILE,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [CARE_PROFILES],
    },
    {
        "edge_collection": CONFIRMS_CARE,
        "from_vertex_collections": [CARE_CONFIRMATIONS],
        "to_vertex_collections": [CARE_PROFILES],
    },
    {
        "edge_collection": CARE_EVENT_FOR,
        "from_vertex_collections": [CARE_CONFIRMATIONS],
        "to_vertex_collections": [PLANT_INSTANCES],
    },
    # REQ-020 Onboarding
    {
        "edge_collection": INCLUDES_SPECIES,
        "from_vertex_collections": [STARTER_KITS],
        "to_vertex_collections": [SPECIES],
    },
    {
        "edge_collection": INCLUDES_CULTIVAR,
        "from_vertex_collections": [STARTER_KITS],
        "to_vertex_collections": [CULTIVARS],
    },
    {
        "edge_collection": INCLUDES_TEMPLATE,
        "from_vertex_collections": [STARTER_KITS],
        "to_vertex_collections": [WORKFLOW_TEMPLATES],
    },
    {
        "edge_collection": CREATED_BY_WIZARD,
        "from_vertex_collections": [ONBOARDING_STATES],
        "to_vertex_collections": [PLANT_INSTANCES],
    },
    # Watering Schedule
    {
        "edge_collection": RUN_FOLLOWS_PLAN,
        "from_vertex_collections": [PLANTING_RUNS],
        "to_vertex_collections": [NUTRIENT_PLANS],
    },
    # REQ-005 Sensors
    {
        "edge_collection": MONITORS_TANK,
        "from_vertex_collections": [SENSORS],
        "to_vertex_collections": [TANKS],
    },
    {
        "edge_collection": LOCATED_AT,
        "from_vertex_collections": [SENSORS],
        "to_vertex_collections": [SITES, LOCATIONS],
    },
    # Watering Log edges
    {
        "edge_collection": LOG_SLOT,
        "from_vertex_collections": [WATERING_LOGS],
        "to_vertex_collections": [SLOTS],
    },
    {
        "edge_collection": LOG_PLANT,
        "from_vertex_collections": [WATERING_LOGS],
        "to_vertex_collections": [PLANT_INSTANCES],
    },
    {
        "edge_collection": LOG_FERTILIZER,
        "from_vertex_collections": [WATERING_LOGS],
        "to_vertex_collections": [FERTILIZERS],
    },
    # Activity edges
    {
        "edge_collection": TASK_USES_ACTIVITY,
        "from_vertex_collections": [TASKS, TASK_TEMPLATES],
        "to_vertex_collections": [ACTIVITIES],
    },
    # REQ-014 Tank Fill
    {
        "edge_collection": HAS_FILL_EVENT,
        "from_vertex_collections": [TANKS],
        "to_vertex_collections": [TANK_FILL_EVENTS],
    },
    {
        "edge_collection": MIXED_INTO,
        "from_vertex_collections": [NUTRIENT_PLANS],
        "to_vertex_collections": [TANK_FILL_EVENTS],
    },
    {
        "edge_collection": WATERING_FROM,
        "from_vertex_collections": [WATERING_EVENTS],
        "to_vertex_collections": [TANK_FILL_EVENTS],
    },
    {
        "edge_collection": GENERATED_TASK,
        "from_vertex_collections": [MAINTENANCE_SCHEDULES],
        "to_vertex_collections": [TASKS],
    },
]


def ensure_collections(db: StandardDatabase) -> None:
    """Create all collections and the graph if they don't exist."""
    for name in DOCUMENT_COLLECTIONS:
        if not db.has_collection(name):
            db.create_collection(name)

    for name in EDGE_COLLECTIONS:
        if not db.has_collection(name):
            db.create_collection(name, edge=True)

    # Create indexes
    species_col = db.collection(SPECIES)
    species_col.add_hash_index(fields=["scientific_name"], unique=True)

    families_col = db.collection(BOTANICAL_FAMILIES)
    families_col.add_hash_index(fields=["name"], unique=True)

    slots_col = db.collection(SLOTS)
    slots_col.add_hash_index(fields=["slot_id"], unique=True)

    plants_col = db.collection(PLANT_INSTANCES)
    plants_col.add_hash_index(fields=["instance_id"], unique=True)

    mappings_col = db.collection(EXTERNAL_MAPPINGS)
    mappings_col.add_hash_index(fields=["internal_collection", "internal_key", "source_key"], unique=True)

    sync_runs_col = db.collection(SYNC_RUNS)
    sync_runs_col.add_hash_index(fields=["source_key"], unique=False)

    runs_col = db.collection(PLANTING_RUNS)
    runs_col.add_hash_index(fields=["name"], unique=False)

    tanks_col = db.collection(TANKS)
    tanks_col.add_hash_index(fields=["name"], unique=True)

    tank_states_col = db.collection(TANK_STATES)
    tank_states_col.add_hash_index(fields=["recorded_at"], unique=False)

    fertilizers_col = db.collection(FERTILIZERS)
    fertilizers_col.add_hash_index(fields=["product_name", "brand"], unique=True)

    feeding_events_col = db.collection(FEEDING_EVENTS)
    feeding_events_col.add_hash_index(fields=["plant_key"], unique=False)
    feeding_events_col.add_hash_index(fields=["timestamp"], unique=False)

    plan_entries_col = db.collection(NUTRIENT_PLAN_PHASE_ENTRIES)
    plan_entries_col.add_hash_index(fields=["plan_key"], unique=False)

    watering_events_col = db.collection(WATERING_EVENTS)
    watering_events_col.add_hash_index(fields=["watered_at"], unique=False)

    # REQ-010 IPM indexes
    pests_col = db.collection(PESTS)
    pests_col.add_hash_index(fields=["scientific_name"], unique=True)

    diseases_col = db.collection(DISEASES)
    diseases_col.add_hash_index(fields=["scientific_name"], unique=True)

    treatments_col = db.collection(TREATMENTS)
    treatments_col.add_hash_index(fields=["name"], unique=True)

    inspections_col = db.collection(INSPECTIONS)
    inspections_col.add_hash_index(fields=["plant_key"], unique=False)

    treatment_apps_col = db.collection(TREATMENT_APPLICATIONS)
    treatment_apps_col.add_hash_index(fields=["plant_key"], unique=False)
    treatment_apps_col.add_hash_index(fields=["treatment_key"], unique=False)

    # REQ-007 Harvest indexes
    harvest_obs_col = db.collection(HARVEST_OBSERVATIONS)
    harvest_obs_col.add_hash_index(fields=["plant_key"], unique=False)

    harvest_batches_col = db.collection(HARVEST_BATCHES)
    harvest_batches_col.add_hash_index(fields=["plant_key"], unique=False)
    harvest_batches_col.add_hash_index(fields=["batch_id"], unique=True)

    # REQ-006 Task indexes
    tasks_col = db.collection(TASKS)
    tasks_col.add_hash_index(fields=["plant_key"], unique=False)
    tasks_col.add_hash_index(fields=["status"], unique=False)
    tasks_col.add_hash_index(fields=["planting_run_key"], unique=False)

    wf_templates_col = db.collection(WORKFLOW_TEMPLATES)
    wf_templates_col.add_hash_index(fields=["name"], unique=True)

    # REQ-023 Auth indexes
    users_col = db.collection(USERS)
    users_col.add_hash_index(fields=["email"], unique=True)

    auth_providers_col = db.collection(AUTH_PROVIDERS)
    auth_providers_col.add_hash_index(fields=["provider", "provider_user_id"], unique=True)
    auth_providers_col.add_hash_index(fields=["user_key"], unique=False)

    refresh_tokens_col = db.collection(REFRESH_TOKENS)
    refresh_tokens_col.add_hash_index(fields=["token_hash"], unique=True)
    refresh_tokens_col.add_hash_index(fields=["user_key"], unique=False)

    oidc_configs_col = db.collection(OIDC_PROVIDER_CONFIGS)
    oidc_configs_col.add_hash_index(fields=["slug"], unique=True)

    api_keys_col = db.collection(API_KEYS)
    api_keys_col.add_hash_index(fields=["key_hash"], unique=True)
    api_keys_col.add_hash_index(fields=["user_key"], unique=False)

    # REQ-024 Tenant indexes
    tenants_col = db.collection(TENANTS)
    tenants_col.add_hash_index(fields=["slug"], unique=True)

    memberships_col = db.collection(MEMBERSHIPS)
    memberships_col.add_hash_index(fields=["user_key", "tenant_key"], unique=True)

    invitations_col = db.collection(INVITATIONS)
    invitations_col.add_hash_index(fields=["token_hash"], unique=True)
    invitations_col.add_hash_index(fields=["tenant_key"], unique=False)

    location_assignments_col = db.collection(LOCATION_ASSIGNMENTS)
    location_assignments_col.add_hash_index(fields=["membership_key", "location_key"], unique=True)

    # REQ-022 Care Reminder indexes
    care_confirmations_col = db.collection(CARE_CONFIRMATIONS)
    care_confirmations_col.add_hash_index(fields=["reminder_type", "confirmed_at"], unique=False)

    has_care_profile_col = db.collection(HAS_CARE_PROFILE)
    has_care_profile_col.add_hash_index(fields=["_from"], unique=True)

    # REQ-020 Onboarding indexes
    starter_kits_col = db.collection(STARTER_KITS)
    starter_kits_col.add_hash_index(fields=["kit_id"], unique=True)
    starter_kits_col.add_hash_index(fields=["difficulty", "sort_order"], unique=False)

    # REQ-012 Import indexes
    import_jobs_col = db.collection(IMPORT_JOBS)
    import_jobs_col.add_hash_index(fields=["entity_type"], unique=False)
    import_jobs_col.add_hash_index(fields=["status"], unique=False)

    # REQ-014 Tank Fill indexes
    tank_fill_events_col = db.collection(TANK_FILL_EVENTS)
    tank_fill_events_col.add_hash_index(fields=["tank_key", "filled_at"], unique=False)

    # REQ-005 Sensor indexes
    sensors_col = db.collection(SENSORS)
    sensors_col.add_hash_index(fields=["tank_key"], unique=False)
    sensors_col.add_hash_index(fields=["site_key"], unique=False)
    sensors_col.add_hash_index(fields=["location_key"], unique=False)

    # Watering Log indexes
    watering_logs_col = db.collection(WATERING_LOGS)
    watering_logs_col.add_hash_index(fields=["logged_at"], unique=False)
    watering_logs_col.add_hash_index(fields=["plant_keys[*]"], unique=False)
    watering_logs_col.add_hash_index(fields=["slot_keys[*]"], unique=False)

    # Activity indexes
    activities_col = db.collection(ACTIVITIES)
    activities_col.add_hash_index(fields=["name"], unique=True)

    # REQ-015 Calendar indexes
    calendar_feeds_col = db.collection(CALENDAR_FEEDS)
    calendar_feeds_col.add_hash_index(fields=["token"], unique=True)

    # Create or update named graph
    if not db.has_graph(GRAPH_NAME):
        db.create_graph(GRAPH_NAME, edge_definitions=GRAPH_EDGE_DEFINITIONS)
    else:
        graph = db.graph(GRAPH_NAME)
        existing_defs = {ed["edge_collection"]: ed for ed in graph.edge_definitions()}
        for ed in GRAPH_EDGE_DEFINITIONS:
            edge_col = ed["edge_collection"]
            if edge_col not in existing_defs:
                graph.create_edge_definition(**ed)
            else:
                # Update if from/to vertex collections changed
                old = existing_defs[edge_col]
                if set(old.get("from_vertex_collections", [])) != set(ed["from_vertex_collections"]) or set(
                    old.get("to_vertex_collections", [])
                ) != set(ed["to_vertex_collections"]):
                    graph.replace_edge_definition(**ed)
