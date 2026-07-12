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
SUCCESSION_PLANS = "succession_plans"
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

# REQ-008 Post-Harvest
POST_HARVEST_BATCHES = "post_harvest_batches"
DRYING_PROGRESS = "drying_progress"
STORAGE_OBSERVATIONS = "storage_observations"
MOLD_ALERTS = "mold_alerts"
BURPING_EVENTS = "burping_events"

# REQ-006 Tasks
WORKFLOW_TEMPLATES = "workflow_templates"
WORKFLOW_PHASES = "workflow_phases"
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

# REQ-022 Overwintering (G-002)
OVERWINTERING_PROFILES = "overwintering_profiles"
#: Species-level overwintering *templates* curated from the plant Steckbriefe
#: (§4.3), distinct from the per-instance ``OVERWINTERING_PROFILES``.
OVERWINTERING_PROFILE_TEMPLATES = "overwintering_profile_templates"

# REQ-047 Season & overwintering automation
SEASON_STATES = "season_states"

# REQ-020 Onboarding
STARTER_KITS = "starter_kits"
ONBOARDING_STATES = "onboarding_states"
USER_PREFERENCES = "user_preferences"
USER_FAVORITES = "user_favorites"

# REQ-012 Import
IMPORT_JOBS = "import_jobs"

# REQ-015 Calendar
CALENDAR_FEEDS = "calendar_feeds"

# REQ-005 Sensors
SENSORS = "sensors"

# REQ-046 Weather data sources
WEATHER_FORECASTS = "weather_forecasts"
WEATHER_SOURCE_CONFIGS = "weather_source_configs"

# REQ-026 Aquaponics
FISH_SPECIES = "fish_species"
FISH_STOCKS = "fish_stocks"
AQUAPONIC_SYSTEMS = "aquaponic_systems"
WATER_TESTS = "water_tests"
FISH_FEEDING_EVENTS = "fish_feeding_events"
SUPPLEMENTATION_EVENTS = "supplementation_events"

# REQ-016 InvenTree integration (optional)
INVENTREE_CONNECTIONS = "inventree_connections"
INVENTREE_REFERENCES = "inventree_references"
STOCK_TRANSACTIONS = "stock_transactions"
EQUIPMENT = "equipment"

# REQ-041 NASA POWER — long-term monthly climate normals per site
CLIMATE_NORMALS = "climate_normals"

# REQ-039 — canonical plant hardiness-zone reference catalog (global, 1a…13b)
HARDINESS_ZONES = "hardiness_zones"

# REQ-037 — materialised daily irrigation demand (ET₀ → ETc → net demand) per site/run
IRRIGATION_DEMANDS = "irrigation_demands"

# REQ-002 Location Types
LOCATION_TYPES = "location_types"

# System Settings (singleton)
SYSTEM_SETTINGS = "system_settings"

# NFR-016 Schema-migration tracking (versioned migration framework)
SCHEMA_MIGRATIONS = "schema_migrations"

# Home Assistant publish selection (per-tenant, per-entity opt-in)
HA_PUBLISH_SETTINGS = "ha_publish_settings"

# Unified Watering Log (replaces WateringEvents + FeedingEvents)
WATERING_LOGS = "watering_logs"

# Activities (Stammdaten)
ACTIVITIES = "activities"

# REQ-013 v2.0 Plant Diary
PLANT_DIARY_ENTRIES = "plant_diary_entries"

# REQ-030 Notifications
NOTIFICATIONS = "notifications"
NOTIFICATION_PREFERENCES = "notification_preferences"

# Phase Sequences
PHASE_DEFINITIONS = "phase_definitions"
PHASE_SEQUENCES = "phase_sequences"
PHASE_SEQUENCE_ENTRIES = "phase_sequence_entries"

# REQ-029 Plant identification (Phase 1 — Pl@ntNet-first)
IDENTIFICATION_REQUESTS = "identification_requests"

# REQ-025 Privacy & GDPR
DATA_EXPORT_REQUESTS = "data_export_requests"
CONSENT_RECORDS = "consent_records"
PROCESSING_RESTRICTIONS = "processing_restrictions"
ERASURE_REQUESTS = "erasure_requests"
EMAIL_CHANGE_REQUESTS = "email_change_requests"

# REQ-029-A DINOv2 — diagnosis (task B, backlog) + reference-image acquisition
DIAGNOSIS_REQUESTS = "diagnosis_requests"
REFERENCE_IMAGE_JOBS = "reference_image_jobs"

# NFR-013 Object storage — attachment catalog
ATTACHMENTS = "attachments"

# REQ-044 Bildbasierte Schädlingserkennung
PEST_DETECTIONS = "pest_detections"
BENEFICIALS = "beneficials"  # WP-8 — Nützlings-Stammdaten

# REQ-010 User-contributed pest reference images (tenant-private gallery)
PEST_IMAGE_CONTRIBUTIONS = "pest_image_contributions"

# REQ-038 CV disease diagnosis — one document per diagnosis request. Only the
# classifications / phenotype metrics / provenance are kept; the original image
# is never persisted (``image_deleted_at`` set, §4.4).
PLANT_DIAGNOSIS_REQUESTS = "plant_diagnosis_requests"

# REQ-017 Propagation / lineage — one document per propagation event (clone /
# seed cross / graft / division). D10 persists the monocarpic-mother→pup clone
# event; the full propagation surface enriches the same document.
PROPAGATION_EVENTS = "propagation_events"
#: Groups propagation events started together (REQ-017 §2 propagation_batches).
PROPAGATION_BATCHES = "propagation_batches"
#: Reusable rooting / propagation protocol templates (REQ-017 §2 rooting_protocols).
#: ``tenant_key == ""`` marks a global system template.
ROOTING_PROTOCOLS = "rooting_protocols"
#: Free-text phenotype observations recorded against a plant instance (REQ-017 §2).
PHENOTYPE_NOTES = "phenotype_notes"

# REQ-031 KI-Assistent (AI assistant) — tenant/user KI data; vectors live in the
# Knowledge-Service microservice, never in the backend (§3.3).
AI_PROVIDER_CONFIGS = "ai_provider_configs"
AI_CONVERSATIONS = "ai_conversations"
AI_TIP_CACHE = "ai_tip_cache"
AI_AUDIT_LOG = "ai_audit_log"

# REQ-035 KI terminology glossary — curated term skeleton + RAG answer cache.
# Both are global (not tenant-scoped): the glossary is knowledge, not tenant
# data (§6, no PII). The RAG answer text lives in ``glossary_term_cache``; the
# vectors stay in the Knowledge-Service microservice.
GLOSSARY_TERMS = "glossary_terms"
GLOSSARY_TERM_CACHE = "glossary_term_cache"

# REQ-033 MCP server — adapter-layer collections only (no own domain data, §3).
# ``mcp_audit_log`` records one entry per tool call (no PII, only hashes/sizes,
# retention 90d via NFR-011). ``mcp_idempotency_record`` de-duplicates write
# tools by idempotency key (retention 24h).
MCP_AUDIT_LOG = "mcp_audit_log"
MCP_IDEMPOTENCY_RECORD = "mcp_idempotency_record"

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
    SUCCESSION_PLANS,
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
    POST_HARVEST_BATCHES,
    DRYING_PROGRESS,
    STORAGE_OBSERVATIONS,
    MOLD_ALERTS,
    BURPING_EVENTS,
    WORKFLOW_TEMPLATES,
    WORKFLOW_PHASES,
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
    OVERWINTERING_PROFILES,
    OVERWINTERING_PROFILE_TEMPLATES,
    SEASON_STATES,
    STARTER_KITS,
    ONBOARDING_STATES,
    USER_PREFERENCES,
    IMPORT_JOBS,
    CALENDAR_FEEDS,
    API_KEYS,
    TANK_FILL_EVENTS,
    SENSORS,
    SYSTEM_SETTINGS,
    SCHEMA_MIGRATIONS,
    HA_PUBLISH_SETTINGS,
    LOCATION_TYPES,
    WATERING_LOGS,
    ACTIVITIES,
    NOTIFICATIONS,
    NOTIFICATION_PREFERENCES,
    PLANT_DIARY_ENTRIES,
    PHASE_DEFINITIONS,
    PHASE_SEQUENCES,
    PHASE_SEQUENCE_ENTRIES,
    DATA_EXPORT_REQUESTS,
    CONSENT_RECORDS,
    PROCESSING_RESTRICTIONS,
    ERASURE_REQUESTS,
    EMAIL_CHANGE_REQUESTS,
    IDENTIFICATION_REQUESTS,
    PLANT_DIAGNOSIS_REQUESTS,
    DIAGNOSIS_REQUESTS,
    REFERENCE_IMAGE_JOBS,
    ATTACHMENTS,
    PEST_DETECTIONS,
    BENEFICIALS,
    PEST_IMAGE_CONTRIBUTIONS,
    PROPAGATION_EVENTS,
    PROPAGATION_BATCHES,
    ROOTING_PROTOCOLS,
    PHENOTYPE_NOTES,
    # REQ-046 Weather data sources
    WEATHER_FORECASTS,
    WEATHER_SOURCE_CONFIGS,
    # REQ-031 KI-Assistent
    AI_PROVIDER_CONFIGS,
    AI_CONVERSATIONS,
    AI_TIP_CACHE,
    AI_AUDIT_LOG,
    # REQ-035 KI terminology glossary
    GLOSSARY_TERMS,
    GLOSSARY_TERM_CACHE,
    # REQ-033 MCP server (adapter-layer only)
    MCP_AUDIT_LOG,
    MCP_IDEMPOTENCY_RECORD,
    # REQ-026 Aquaponics
    FISH_SPECIES,
    FISH_STOCKS,
    AQUAPONIC_SYSTEMS,
    WATER_TESTS,
    FISH_FEEDING_EVENTS,
    SUPPLEMENTATION_EVENTS,
    # REQ-016 InvenTree integration
    INVENTREE_CONNECTIONS,
    INVENTREE_REFERENCES,
    STOCK_TRANSACTIONS,
    EQUIPMENT,
    # REQ-041 NASA POWER climate normals
    CLIMATE_NORMALS,
    # REQ-039 hardiness-zone reference catalog
    HARDINESS_ZONES,
    # REQ-037 irrigation demands
    IRRIGATION_DEMANDS,
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
# REQ-013 §2 Succession (staggered sowing)
HAS_SUCCESSION_PLAN = "has_succession_plan"
SUCCESSION_AT = "succession_at"
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
# REQ-017 genetic lineage — child (descendant) → parent (ancestor). D10 links a
# monocarpic mother's clonal pup back to the mother instance.
DESCENDED_FROM = "descended_from"
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

# REQ-008 Post-Harvest edges
POST_HARVEST_OF = "post_harvest_of"
HAS_DRYING_PROGRESS = "has_drying_progress"
HAS_STORAGE_OBSERVATION = "has_storage_observation"
TRIGGERED_MOLD_ALERT = "triggered_mold_alert"
HAS_BURPING_EVENT = "has_burping_event"

# REQ-006 Task edges
WF_CONTAINS = "wf_contains"
WF_HAS_PHASE = "wf_has_phase"
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

# REQ-022 Overwintering edges (G-002)
HAS_OVERWINTERING_PROFILE = "has_overwintering_profile"
OVERWINTERS_AT = "overwinters_at"
#: Links a subject (plant instance / planting run) to a *shared, reusable*
#: species-level overwintering template (N subjects → 1 template). Unique on
#: ``_from`` so each subject references at most one shared template.
USES_OVERWINTERING_TEMPLATE = "uses_overwintering_template"

# REQ-047 Season & overwintering automation edge
HAS_SEASON_STATE = "has_season_state"  # sites → season_states (1:1)

# REQ-014 Tank Fill edges
HAS_FILL_EVENT = "has_fill_event"
MIXED_INTO = "mixed_into"
WATERING_FROM = "watering_from"
GENERATED_TASK = "generated_task"

# REQ-005 Sensor edges
MONITORS_TANK = "monitors_tank"
LOCATED_AT = "located_at"

# REQ-046 Weather data sources edges
HAS_FORECAST = "has_forecast"  # sites → weather_forecasts (all source values)
HAS_WEATHER_SOURCE_CONFIG = "has_weather_source_config"  # sites → weather_source_configs (1:1)

# REQ-026 Aquaponics edges
HAS_FISH_STOCK = "has_fish_stock"  # aquaponic_systems → fish_stocks
STOCK_OF_SPECIES = "stock_of_species"  # fish_stocks → fish_species
SYSTEM_HAS_TANK = "system_has_tank"  # aquaponic_systems → tanks (edge prop tank_role)
SYSTEM_HAS_GROWBED = "system_has_growbed"  # aquaponic_systems → slots
WATER_TEST_FOR = "water_test_for"  # water_tests → aquaponic_systems
FEEDING_FOR_STOCK = "feeding_for_stock"  # fish_feeding_events → fish_stocks
SUPPLEMENTATION_FOR = "supplementation_for"  # supplementation_events → aquaponic_systems
COMPATIBLE_FISH_PLANT = "compatible_fish_plant"  # fish_species → species
INCOMPATIBLE_FISH_PLANT = "incompatible_fish_plant"  # fish_species → species

# REQ-016 InvenTree integration edges
HAS_INVENTREE_REF = "has_inventree_ref"  # fertilizers | tanks | equipment → inventree_references
HAS_STOCK_TRANSACTION = "has_stock_transaction"  # inventree_references → stock_transactions
EQUIPMENT_AT = "equipment_at"  # equipment → locations

# REQ-041 NASA POWER climate-normal edge
HAS_CLIMATE_NORMAL = "has_climate_normal"  # sites → climate_normals (1 per source)

# REQ-039 hardiness-zone assignment edge
LOCATED_IN_ZONE = "located_in_zone"  # sites → hardiness_zones (1 per site)

# REQ-037 irrigation-demand edges
HAS_IRRIGATION_DEMAND = "has_irrigation_demand"  # sites → irrigation_demands
DEMAND_FOR_RUN = "demand_for_run"  # planting_runs → irrigation_demands

# Watering Log edges
LOG_SLOT = "log_slot"
LOG_PLANT = "log_plant"
LOG_FERTILIZER = "log_fertilizer"

# Activity edges
TASK_USES_ACTIVITY = "task_uses_activity"

# REQ-030 Notification edges
NOTIFIED_ABOUT_TASK = "notified_about_task"
NOTIFIED_ABOUT_PLANT = "notified_about_plant"

# REQ-013 v2.0 Plant Diary / Run-level edges
HAS_DIARY_ENTRY = "has_diary_entry"
TO_RUN = "to_run"
NOTIFICATION_FOR_RUN = "notification_for_run"

# Phase Sequence edges
SEQ_HAS_ENTRY = "seq_has_entry"
ENTRY_USES_DEFINITION = "entry_uses_definition"
HAS_PHASE_SEQUENCE = "has_phase_sequence"

# REQ-025 Privacy edges
REQUESTED_EXPORT = "requested_export"
HAS_CONSENT = "has_consent"
HAS_RESTRICTION = "has_restriction"
REQUESTED_ERASURE = "requested_erasure"
REQUESTED_EMAIL_CHANGE = "requested_email_change"

# Watering Schedule edges
RUN_FOLLOWS_PLAN = "run_follows_plan"

# REQ-020 Onboarding edges
INCLUDES_SPECIES = "includes_species"
INCLUDES_CULTIVAR = "includes_cultivar"
INCLUDES_TEMPLATE = "includes_template"
INCLUDES_NUTRIENT_PLAN = "includes_nutrient_plan"
CREATED_BY_WIZARD = "created_by_wizard"

# REQ-044 Pest detection edges (§5.2)
PEST_DETECTION_OF = "pest_detection_of"  # pest_detections → plant_instances/planting_runs
PEST_DETECTION_FLAGGED = "pest_detection_flagged"  # pest_detections → pests
PEST_DETECTION_SUGGESTED_INSPECTION = "pest_detection_suggested_inspection"  # → inspections

# REQ-031 KI-Assistent edges (§3.2)
AI_TIP_REFERENCES_PLANT = "ai_tip_references_plant"  # ai_tip_cache → plant_instances
AI_TIP_REFERENCES_RUN = "ai_tip_references_run"  # ai_tip_cache → planting_runs
AI_CONVERSATION_ABOUT = "ai_conversation_about"  # ai_conversations → plant_instances/planting_runs
AI_AUDIT_ABOUT = "ai_audit_about"  # ai_audit_log → plant_instances/planting_runs

# REQ-038 CV disease diagnosis edges
CV_DIAGNOSED_FOR = "cv_diagnosed_for"  # plant_diagnosis_requests → plant_instances/planting_runs
CV_DIAGNOSIS_FOUND = "cv_diagnosis_found"  # plant_diagnosis_requests → diseases/pests
CV_ATTACHED_TO_INSPECTION = "cv_attached_to_inspection"  # → inspections
CV_PHENOTYPE_OF = "cv_phenotype_of"  # plant_diagnosis_requests → harvest_observations

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
    HAS_SUCCESSION_PLAN,
    SUCCESSION_AT,
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
    DESCENDED_FROM,
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
    POST_HARVEST_OF,
    HAS_DRYING_PROGRESS,
    HAS_STORAGE_OBSERVATION,
    TRIGGERED_MOLD_ALERT,
    HAS_BURPING_EVENT,
    WF_CONTAINS,
    WF_HAS_PHASE,
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
    HAS_OVERWINTERING_PROFILE,
    OVERWINTERS_AT,
    USES_OVERWINTERING_TEMPLATE,
    HAS_SEASON_STATE,
    INCLUDES_SPECIES,
    INCLUDES_CULTIVAR,
    INCLUDES_TEMPLATE,
    INCLUDES_NUTRIENT_PLAN,
    CREATED_BY_WIZARD,
    USER_FAVORITES,
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
    NOTIFIED_ABOUT_TASK,
    NOTIFIED_ABOUT_PLANT,
    HAS_DIARY_ENTRY,
    TO_RUN,
    NOTIFICATION_FOR_RUN,
    SEQ_HAS_ENTRY,
    ENTRY_USES_DEFINITION,
    HAS_PHASE_SEQUENCE,
    REQUESTED_EXPORT,
    HAS_CONSENT,
    HAS_RESTRICTION,
    REQUESTED_ERASURE,
    REQUESTED_EMAIL_CHANGE,
    PEST_DETECTION_OF,
    PEST_DETECTION_FLAGGED,
    PEST_DETECTION_SUGGESTED_INSPECTION,
    # REQ-038 CV disease diagnosis
    CV_DIAGNOSED_FOR,
    CV_DIAGNOSIS_FOUND,
    CV_ATTACHED_TO_INSPECTION,
    CV_PHENOTYPE_OF,
    # REQ-046 Weather data sources
    HAS_FORECAST,
    HAS_WEATHER_SOURCE_CONFIG,
    # REQ-031 KI-Assistent
    AI_TIP_REFERENCES_PLANT,
    AI_TIP_REFERENCES_RUN,
    AI_CONVERSATION_ABOUT,
    AI_AUDIT_ABOUT,
    # REQ-026 Aquaponics
    HAS_FISH_STOCK,
    STOCK_OF_SPECIES,
    SYSTEM_HAS_TANK,
    SYSTEM_HAS_GROWBED,
    WATER_TEST_FOR,
    FEEDING_FOR_STOCK,
    SUPPLEMENTATION_FOR,
    COMPATIBLE_FISH_PLANT,
    INCOMPATIBLE_FISH_PLANT,
    # REQ-016 InvenTree integration
    HAS_INVENTREE_REF,
    HAS_STOCK_TRANSACTION,
    EQUIPMENT_AT,
    # REQ-041 NASA POWER climate normals
    HAS_CLIMATE_NORMAL,
    # REQ-039 hardiness-zone assignment
    LOCATED_IN_ZONE,
    # REQ-037 irrigation demands
    HAS_IRRIGATION_DEMAND,
    DEMAND_FOR_RUN,
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
        "from_vertex_collections": [PLANT_INSTANCES, PLANTING_RUNS],
        "to_vertex_collections": [GROWTH_PHASES],
    },
    {
        "edge_collection": PHASE_HISTORY_EDGE,
        "from_vertex_collections": [PLANT_INSTANCES, PLANTING_RUNS],
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
    # REQ-013 §2 Succession (staggered sowing)
    {
        "edge_collection": HAS_SUCCESSION_PLAN,
        "from_vertex_collections": [SUCCESSION_PLANS],
        "to_vertex_collections": [PLANTING_RUNS],
    },
    {
        "edge_collection": SUCCESSION_AT,
        "from_vertex_collections": [SUCCESSION_PLANS],
        "to_vertex_collections": [LOCATIONS],
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
        "from_vertex_collections": [PLANT_INSTANCES, PLANTING_RUNS],
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
        # REQ-017 lineage: child (descendant) instance → parent (ancestor) instance.
        "edge_collection": DESCENDED_FROM,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [PLANT_INSTANCES],
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
        "from_vertex_collections": [PLANT_INSTANCES, PLANTING_RUNS],
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
    # REQ-008 Post-Harvest
    {
        "edge_collection": POST_HARVEST_OF,
        "from_vertex_collections": [HARVEST_BATCHES],
        "to_vertex_collections": [POST_HARVEST_BATCHES],
    },
    {
        "edge_collection": HAS_DRYING_PROGRESS,
        "from_vertex_collections": [POST_HARVEST_BATCHES],
        "to_vertex_collections": [DRYING_PROGRESS],
    },
    {
        "edge_collection": HAS_STORAGE_OBSERVATION,
        "from_vertex_collections": [POST_HARVEST_BATCHES],
        "to_vertex_collections": [STORAGE_OBSERVATIONS],
    },
    {
        "edge_collection": TRIGGERED_MOLD_ALERT,
        "from_vertex_collections": [POST_HARVEST_BATCHES],
        "to_vertex_collections": [MOLD_ALERTS],
    },
    {
        "edge_collection": HAS_BURPING_EVENT,
        "from_vertex_collections": [POST_HARVEST_BATCHES],
        "to_vertex_collections": [BURPING_EVENTS],
    },
    # REQ-006 Tasks
    {
        "edge_collection": WF_CONTAINS,
        "from_vertex_collections": [WORKFLOW_TEMPLATES],
        "to_vertex_collections": [TASK_TEMPLATES],
    },
    {
        "edge_collection": WF_HAS_PHASE,
        "from_vertex_collections": [WORKFLOW_TEMPLATES],
        "to_vertex_collections": [WORKFLOW_PHASES],
    },
    {
        "edge_collection": REQUIRES_PHASE,
        "from_vertex_collections": [TASK_TEMPLATES],
        "to_vertex_collections": [GROWTH_PHASES],
    },
    {
        "edge_collection": HAS_TASK,
        "from_vertex_collections": [PLANT_INSTANCES, PLANTING_RUNS, LOCATIONS, TANKS],
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
        "from_vertex_collections": [PLANT_INSTANCES, PLANTING_RUNS, LOCATIONS, TANKS],
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
        "from_vertex_collections": [PLANT_INSTANCES, PLANTING_RUNS],
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
    # REQ-022 Overwintering (G-002)
    {
        "edge_collection": HAS_OVERWINTERING_PROFILE,
        "from_vertex_collections": [PLANTING_RUNS, PLANT_INSTANCES],
        "to_vertex_collections": [OVERWINTERING_PROFILES],
    },
    {
        "edge_collection": OVERWINTERS_AT,
        "from_vertex_collections": [OVERWINTERING_PROFILES],
        "to_vertex_collections": [LOCATIONS],
    },
    {
        "edge_collection": USES_OVERWINTERING_TEMPLATE,
        "from_vertex_collections": [PLANTING_RUNS, PLANT_INSTANCES],
        "to_vertex_collections": [OVERWINTERING_PROFILE_TEMPLATES],
    },
    # REQ-047 Season & overwintering automation
    {
        "edge_collection": HAS_SEASON_STATE,
        "from_vertex_collections": [SITES],
        "to_vertex_collections": [SEASON_STATES],
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
        "edge_collection": INCLUDES_NUTRIENT_PLAN,
        "from_vertex_collections": [STARTER_KITS],
        "to_vertex_collections": [NUTRIENT_PLANS],
    },
    {
        "edge_collection": CREATED_BY_WIZARD,
        "from_vertex_collections": [ONBOARDING_STATES],
        "to_vertex_collections": [PLANT_INSTANCES],
    },
    {
        "edge_collection": USER_FAVORITES,
        "from_vertex_collections": [USERS],
        "to_vertex_collections": [SPECIES, NUTRIENT_PLANS, FERTILIZERS],
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
    # REQ-030 Notifications
    {
        "edge_collection": NOTIFIED_ABOUT_TASK,
        "from_vertex_collections": [NOTIFICATIONS],
        "to_vertex_collections": [TASKS],
    },
    {
        "edge_collection": NOTIFIED_ABOUT_PLANT,
        "from_vertex_collections": [NOTIFICATIONS],
        "to_vertex_collections": [PLANT_INSTANCES],
    },
    # REQ-013 v2.0 Plant Diary / Run-level edges
    {
        "edge_collection": HAS_DIARY_ENTRY,
        "from_vertex_collections": [PLANT_INSTANCES],
        "to_vertex_collections": [PLANT_DIARY_ENTRIES],
    },
    {
        "edge_collection": TO_RUN,
        "from_vertex_collections": [TREATMENT_APPLICATIONS],
        "to_vertex_collections": [PLANTING_RUNS],
    },
    {
        "edge_collection": NOTIFICATION_FOR_RUN,
        "from_vertex_collections": [NOTIFICATIONS],
        "to_vertex_collections": [PLANTING_RUNS],
    },
    # Phase Sequences
    {
        "edge_collection": SEQ_HAS_ENTRY,
        "from_vertex_collections": [PHASE_SEQUENCES],
        "to_vertex_collections": [PHASE_SEQUENCE_ENTRIES],
    },
    {
        "edge_collection": ENTRY_USES_DEFINITION,
        "from_vertex_collections": [PHASE_SEQUENCE_ENTRIES],
        "to_vertex_collections": [PHASE_DEFINITIONS],
    },
    {
        "edge_collection": HAS_PHASE_SEQUENCE,
        "from_vertex_collections": [SPECIES],
        "to_vertex_collections": [PHASE_SEQUENCES],
    },
    # REQ-025 Privacy
    {
        "edge_collection": REQUESTED_EXPORT,
        "from_vertex_collections": [USERS],
        "to_vertex_collections": [DATA_EXPORT_REQUESTS],
    },
    {
        "edge_collection": HAS_CONSENT,
        "from_vertex_collections": [USERS],
        "to_vertex_collections": [CONSENT_RECORDS],
    },
    {
        "edge_collection": HAS_RESTRICTION,
        "from_vertex_collections": [USERS],
        "to_vertex_collections": [PROCESSING_RESTRICTIONS],
    },
    {
        "edge_collection": REQUESTED_ERASURE,
        "from_vertex_collections": [USERS],
        "to_vertex_collections": [ERASURE_REQUESTS],
    },
    {
        "edge_collection": REQUESTED_EMAIL_CHANGE,
        "from_vertex_collections": [USERS],
        "to_vertex_collections": [EMAIL_CHANGE_REQUESTS],
    },
    # REQ-044 Pest detection edges (§5.2)
    {
        "edge_collection": PEST_DETECTION_OF,
        "from_vertex_collections": [PEST_DETECTIONS],
        "to_vertex_collections": [PLANT_INSTANCES, PLANTING_RUNS],
    },
    {
        "edge_collection": PEST_DETECTION_FLAGGED,
        "from_vertex_collections": [PEST_DETECTIONS],
        "to_vertex_collections": [PESTS],
    },
    {
        "edge_collection": PEST_DETECTION_SUGGESTED_INSPECTION,
        "from_vertex_collections": [PEST_DETECTIONS],
        "to_vertex_collections": [INSPECTIONS],
    },
    # REQ-038 CV disease diagnosis edges
    {
        "edge_collection": CV_DIAGNOSED_FOR,
        "from_vertex_collections": [PLANT_DIAGNOSIS_REQUESTS],
        "to_vertex_collections": [PLANT_INSTANCES, PLANTING_RUNS],
    },
    {
        "edge_collection": CV_DIAGNOSIS_FOUND,
        "from_vertex_collections": [PLANT_DIAGNOSIS_REQUESTS],
        "to_vertex_collections": [DISEASES, PESTS],
    },
    {
        "edge_collection": CV_ATTACHED_TO_INSPECTION,
        "from_vertex_collections": [PLANT_DIAGNOSIS_REQUESTS],
        "to_vertex_collections": [INSPECTIONS],
    },
    {
        "edge_collection": CV_PHENOTYPE_OF,
        "from_vertex_collections": [PLANT_DIAGNOSIS_REQUESTS],
        "to_vertex_collections": [HARVEST_OBSERVATIONS],
    },
    # REQ-046 Weather data sources
    {
        "edge_collection": HAS_FORECAST,
        "from_vertex_collections": [SITES],
        "to_vertex_collections": [WEATHER_FORECASTS],
    },
    {
        "edge_collection": HAS_WEATHER_SOURCE_CONFIG,
        "from_vertex_collections": [SITES],
        "to_vertex_collections": [WEATHER_SOURCE_CONFIGS],
    },
    # REQ-026 Aquaponics
    {
        "edge_collection": HAS_FISH_STOCK,
        "from_vertex_collections": [AQUAPONIC_SYSTEMS],
        "to_vertex_collections": [FISH_STOCKS],
    },
    {
        "edge_collection": STOCK_OF_SPECIES,
        "from_vertex_collections": [FISH_STOCKS],
        "to_vertex_collections": [FISH_SPECIES],
    },
    {
        "edge_collection": SYSTEM_HAS_TANK,
        "from_vertex_collections": [AQUAPONIC_SYSTEMS],
        "to_vertex_collections": [TANKS],
    },
    {
        "edge_collection": SYSTEM_HAS_GROWBED,
        "from_vertex_collections": [AQUAPONIC_SYSTEMS],
        "to_vertex_collections": [SLOTS],
    },
    {
        "edge_collection": WATER_TEST_FOR,
        "from_vertex_collections": [WATER_TESTS],
        "to_vertex_collections": [AQUAPONIC_SYSTEMS],
    },
    {
        "edge_collection": FEEDING_FOR_STOCK,
        "from_vertex_collections": [FISH_FEEDING_EVENTS],
        "to_vertex_collections": [FISH_STOCKS],
    },
    {
        "edge_collection": SUPPLEMENTATION_FOR,
        "from_vertex_collections": [SUPPLEMENTATION_EVENTS],
        "to_vertex_collections": [AQUAPONIC_SYSTEMS],
    },
    {
        "edge_collection": COMPATIBLE_FISH_PLANT,
        "from_vertex_collections": [FISH_SPECIES],
        "to_vertex_collections": [SPECIES],
    },
    {
        "edge_collection": INCOMPATIBLE_FISH_PLANT,
        "from_vertex_collections": [FISH_SPECIES],
        "to_vertex_collections": [SPECIES],
    },
    # REQ-016 InvenTree integration
    {
        "edge_collection": HAS_INVENTREE_REF,
        "from_vertex_collections": [FERTILIZERS, TANKS, EQUIPMENT],
        "to_vertex_collections": [INVENTREE_REFERENCES],
    },
    {
        "edge_collection": HAS_STOCK_TRANSACTION,
        "from_vertex_collections": [INVENTREE_REFERENCES],
        "to_vertex_collections": [STOCK_TRANSACTIONS],
    },
    {
        "edge_collection": EQUIPMENT_AT,
        "from_vertex_collections": [EQUIPMENT],
        "to_vertex_collections": [LOCATIONS],
    },
    # REQ-041 NASA POWER climate normals
    {
        "edge_collection": HAS_CLIMATE_NORMAL,
        "from_vertex_collections": [SITES],
        "to_vertex_collections": [CLIMATE_NORMALS],
    },
    # REQ-039 hardiness-zone assignment
    {
        "edge_collection": LOCATED_IN_ZONE,
        "from_vertex_collections": [SITES],
        "to_vertex_collections": [HARDINESS_ZONES],
    },
    # REQ-037 irrigation demands
    {
        "edge_collection": HAS_IRRIGATION_DEMAND,
        "from_vertex_collections": [SITES],
        "to_vertex_collections": [IRRIGATION_DEMANDS],
    },
    {
        "edge_collection": DEMAND_FOR_RUN,
        "from_vertex_collections": [PLANTING_RUNS],
        "to_vertex_collections": [IRRIGATION_DEMANDS],
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
    species_col.add_persistent_index(fields=["scientific_name"], unique=True)
    # Canonical dedup key (REQ-048 Stufe 1) — non-unique so bootstrap never fails
    # on volumes that still carry un-reconciled normalization duplicates; the
    # dedup itself is enforced in the service/engine layer. add_persistent_index
    # is idempotent by field-set, so this also brings existing volumes to shape.
    species_col.add_persistent_index(fields=["scientific_name_normalized"], unique=False)

    families_col = db.collection(BOTANICAL_FAMILIES)
    families_col.add_persistent_index(fields=["name"], unique=True)

    slots_col = db.collection(SLOTS)
    slots_col.add_persistent_index(fields=["slot_id"], unique=True)

    plants_col = db.collection(PLANT_INSTANCES)
    plants_col.add_persistent_index(fields=["instance_id"], unique=True)

    mappings_col = db.collection(EXTERNAL_MAPPINGS)
    mappings_col.add_persistent_index(fields=["internal_collection", "internal_key", "source_key"], unique=True)

    sync_runs_col = db.collection(SYNC_RUNS)
    sync_runs_col.add_persistent_index(fields=["source_key"], unique=False)

    runs_col = db.collection(PLANTING_RUNS)
    runs_col.add_persistent_index(fields=["name"], unique=False)

    # REQ-013 §2 Succession plans — list queries always filter by tenant.
    succession_plans_col = db.collection(SUCCESSION_PLANS)
    succession_plans_col.add_persistent_index(fields=["tenant_key"], unique=False)

    tanks_col = db.collection(TANKS)
    tanks_col.add_persistent_index(fields=["name"], unique=True)

    tank_states_col = db.collection(TANK_STATES)
    tank_states_col.add_persistent_index(fields=["recorded_at"], unique=False)

    fertilizers_col = db.collection(FERTILIZERS)
    fertilizers_col.add_persistent_index(fields=["product_name", "brand"], unique=True)

    feeding_events_col = db.collection(FEEDING_EVENTS)
    feeding_events_col.add_persistent_index(fields=["plant_key"], unique=False)
    feeding_events_col.add_persistent_index(fields=["timestamp"], unique=False)

    plan_entries_col = db.collection(NUTRIENT_PLAN_PHASE_ENTRIES)
    plan_entries_col.add_persistent_index(fields=["plan_key"], unique=False)

    watering_events_col = db.collection(WATERING_EVENTS)
    watering_events_col.add_persistent_index(fields=["watered_at"], unique=False)

    # REQ-010 IPM indexes
    pests_col = db.collection(PESTS)
    pests_col.add_persistent_index(fields=["scientific_name"], unique=True)

    diseases_col = db.collection(DISEASES)
    diseases_col.add_persistent_index(fields=["scientific_name"], unique=True)

    treatments_col = db.collection(TREATMENTS)
    treatments_col.add_persistent_index(fields=["name"], unique=True)

    inspections_col = db.collection(INSPECTIONS)
    inspections_col.add_persistent_index(fields=["plant_key"], unique=False)

    treatment_apps_col = db.collection(TREATMENT_APPLICATIONS)
    treatment_apps_col.add_persistent_index(fields=["plant_key"], unique=False)
    treatment_apps_col.add_persistent_index(fields=["treatment_key"], unique=False)

    # REQ-007 Harvest indexes
    harvest_obs_col = db.collection(HARVEST_OBSERVATIONS)
    harvest_obs_col.add_persistent_index(fields=["plant_key"], unique=False)

    harvest_batches_col = db.collection(HARVEST_BATCHES)
    harvest_batches_col.add_persistent_index(fields=["plant_key"], unique=False)
    harvest_batches_col.add_persistent_index(fields=["batch_id"], unique=True)

    # REQ-008 Post-Harvest indexes
    post_harvest_batches_col = db.collection(POST_HARVEST_BATCHES)
    post_harvest_batches_col.add_persistent_index(fields=["tenant_key"], unique=False)
    post_harvest_batches_col.add_persistent_index(fields=["harvest_batch_key"], unique=False)
    drying_progress_col = db.collection(DRYING_PROGRESS)
    drying_progress_col.add_persistent_index(fields=["batch_key"], unique=False)
    storage_observations_col = db.collection(STORAGE_OBSERVATIONS)
    storage_observations_col.add_persistent_index(fields=["batch_key"], unique=False)
    mold_alerts_col = db.collection(MOLD_ALERTS)
    mold_alerts_col.add_persistent_index(fields=["batch_key"], unique=False)
    burping_events_col = db.collection(BURPING_EVENTS)
    burping_events_col.add_persistent_index(fields=["batch_key"], unique=False)

    # REQ-006 Task indexes
    tasks_col = db.collection(TASKS)
    tasks_col.add_persistent_index(fields=["plant_key"], unique=False)
    tasks_col.add_persistent_index(fields=["status"], unique=False)
    tasks_col.add_persistent_index(fields=["planting_run_key"], unique=False)

    wf_templates_col = db.collection(WORKFLOW_TEMPLATES)
    wf_templates_col.add_persistent_index(fields=["name"], unique=True)

    wf_phases_col = db.collection(WORKFLOW_PHASES)
    wf_phases_col.add_persistent_index(fields=["workflow_template_key"], unique=False)

    # REQ-023 Auth indexes
    users_col = db.collection(USERS)
    users_col.add_persistent_index(fields=["email"], unique=True)

    auth_providers_col = db.collection(AUTH_PROVIDERS)
    auth_providers_col.add_persistent_index(fields=["provider", "provider_user_id"], unique=True)
    auth_providers_col.add_persistent_index(fields=["user_key"], unique=False)

    refresh_tokens_col = db.collection(REFRESH_TOKENS)
    refresh_tokens_col.add_persistent_index(fields=["token_hash"], unique=True)
    refresh_tokens_col.add_persistent_index(fields=["user_key"], unique=False)

    oidc_configs_col = db.collection(OIDC_PROVIDER_CONFIGS)
    oidc_configs_col.add_persistent_index(fields=["slug"], unique=True)

    api_keys_col = db.collection(API_KEYS)
    api_keys_col.add_persistent_index(fields=["key_hash"], unique=True)
    api_keys_col.add_persistent_index(fields=["user_key"], unique=False)

    # REQ-024 Tenant indexes
    tenants_col = db.collection(TENANTS)
    tenants_col.add_persistent_index(fields=["slug"], unique=True)

    memberships_col = db.collection(MEMBERSHIPS)
    memberships_col.add_persistent_index(fields=["user_key", "tenant_key"], unique=True)

    invitations_col = db.collection(INVITATIONS)
    invitations_col.add_persistent_index(fields=["token_hash"], unique=True)
    invitations_col.add_persistent_index(fields=["tenant_key"], unique=False)

    location_assignments_col = db.collection(LOCATION_ASSIGNMENTS)
    location_assignments_col.add_persistent_index(fields=["membership_key", "location_key"], unique=True)

    # REQ-022 Care Reminder indexes
    care_confirmations_col = db.collection(CARE_CONFIRMATIONS)
    care_confirmations_col.add_persistent_index(fields=["reminder_type", "confirmed_at"], unique=False)

    has_care_profile_col = db.collection(HAS_CARE_PROFILE)
    has_care_profile_col.add_persistent_index(fields=["_from"], unique=True)

    # REQ-022 Overwintering indexes
    overwintering_profiles_col = db.collection(OVERWINTERING_PROFILES)
    overwintering_profiles_col.add_persistent_index(fields=["tenant_key"], unique=False)
    overwintering_profiles_col.add_persistent_index(fields=["plant_key"], unique=False)
    overwintering_profiles_col.add_persistent_index(fields=["planting_run_key"], unique=False)

    has_overwintering_profile_col = db.collection(HAS_OVERWINTERING_PROFILE)
    has_overwintering_profile_col.add_persistent_index(fields=["_from"], unique=True)

    # Shared reusable template link: one template per subject (unique _from),
    # while many subjects may point to the same template (N:1 reuse).
    uses_overwintering_template_col = db.collection(USES_OVERWINTERING_TEMPLATE)
    uses_overwintering_template_col.add_persistent_index(fields=["_from"], unique=True)
    uses_overwintering_template_col.add_persistent_index(fields=["_to"], unique=False)

    # REQ-047 Season state indexes — one state per site (unique site_key within a
    # tenant); the has_season_state edge is 1:1 on _from.
    season_states_col = db.collection(SEASON_STATES)
    season_states_col.add_persistent_index(fields=["tenant_key"], unique=False)
    season_states_col.add_persistent_index(fields=["tenant_key", "site_key"], unique=True)

    has_season_state_col = db.collection(HAS_SEASON_STATE)
    has_season_state_col.add_persistent_index(fields=["_from"], unique=True)

    # REQ-020 Onboarding indexes
    starter_kits_col = db.collection(STARTER_KITS)
    starter_kits_col.add_persistent_index(fields=["kit_id"], unique=True)
    starter_kits_col.add_persistent_index(fields=["difficulty", "sort_order"], unique=False)

    # REQ-020 User Favorites indexes
    user_favorites_col = db.collection(USER_FAVORITES)
    user_favorites_col.add_persistent_index(fields=["_from", "_to"], unique=True)
    user_favorites_col.add_persistent_index(fields=["_from"], unique=False)

    # REQ-012 Import indexes
    import_jobs_col = db.collection(IMPORT_JOBS)
    import_jobs_col.add_persistent_index(fields=["entity_type"], unique=False)
    import_jobs_col.add_persistent_index(fields=["status"], unique=False)

    # REQ-014 Tank Fill indexes
    tank_fill_events_col = db.collection(TANK_FILL_EVENTS)
    tank_fill_events_col.add_persistent_index(fields=["tank_key", "filled_at"], unique=False)

    # REQ-005 Sensor indexes
    sensors_col = db.collection(SENSORS)
    sensors_col.add_persistent_index(fields=["tank_key"], unique=False)
    sensors_col.add_persistent_index(fields=["site_key"], unique=False)
    sensors_col.add_persistent_index(fields=["location_key"], unique=False)

    # Home Assistant publish selection indexes
    ha_publish_settings_col = db.collection(HA_PUBLISH_SETTINGS)
    ha_publish_settings_col.add_persistent_index(fields=["tenant_key", "entity_type", "entity_key"], unique=True)
    ha_publish_settings_col.add_persistent_index(fields=["tenant_key", "entity_type", "enabled"], unique=False)

    # Watering Log indexes
    watering_logs_col = db.collection(WATERING_LOGS)
    watering_logs_col.add_persistent_index(fields=["logged_at"], unique=False)
    watering_logs_col.add_persistent_index(fields=["plant_keys[*]"], unique=False)
    watering_logs_col.add_persistent_index(fields=["slot_keys[*]"], unique=False)

    # Activity indexes
    activities_col = db.collection(ACTIVITIES)
    activities_col.add_persistent_index(fields=["name"], unique=True)

    # REQ-015 Calendar indexes
    calendar_feeds_col = db.collection(CALENDAR_FEEDS)
    calendar_feeds_col.add_persistent_index(fields=["token"], unique=True)

    # REQ-013 v2.0 Plant Diary indexes
    plant_diary_entries_col = db.collection(PLANT_DIARY_ENTRIES)
    plant_diary_entries_col.add_persistent_index(fields=["plant_key"], unique=False)
    plant_diary_entries_col.add_persistent_index(fields=["tenant_key"], unique=False)
    plant_diary_entries_col.add_persistent_index(fields=["entry_type"], unique=False)

    # REQ-030 Notification indexes
    notifications_col = db.collection(NOTIFICATIONS)
    notifications_col.add_persistent_index(fields=["user_key", "tenant_key"], unique=False)
    notifications_col.add_persistent_index(fields=["notification_type"], unique=False)
    notifications_col.add_persistent_index(fields=["created_at"], unique=False)
    # Issue #409 (F2) — backs the frost-forecast dedup / per-recipient top-up reads
    # (``exists_by_group_key`` / ``find_notified_user_keys``), tenant-scoped by the
    # (group_key, tenant_key) filter. Non-unique: many users share one group_key.
    notifications_col.add_persistent_index(fields=["group_key", "tenant_key"], unique=False)

    notification_prefs_col = db.collection(NOTIFICATION_PREFERENCES)
    notification_prefs_col.add_persistent_index(fields=["user_key"], unique=True)

    # Phase Sequence indexes
    phase_defs_col = db.collection(PHASE_DEFINITIONS)
    phase_defs_col.add_persistent_index(fields=["name"], unique=True)

    phase_seq_entries_col = db.collection(PHASE_SEQUENCE_ENTRIES)
    phase_seq_entries_col.add_persistent_index(fields=["phase_sequence_key", "sequence_order"], unique=True)

    # REQ-025 Privacy indexes
    data_export_requests_col = db.collection(DATA_EXPORT_REQUESTS)
    data_export_requests_col.add_persistent_index(fields=["user_key"], unique=False)
    data_export_requests_col.add_persistent_index(fields=["status"], unique=False)
    data_export_requests_col.add_persistent_index(fields=["expires_at"], unique=False)

    consent_records_col = db.collection(CONSENT_RECORDS)
    consent_records_col.add_persistent_index(fields=["user_key", "purpose"], unique=True)
    consent_records_col.add_persistent_index(fields=["user_key"], unique=False)

    processing_restrictions_col = db.collection(PROCESSING_RESTRICTIONS)
    processing_restrictions_col.add_persistent_index(fields=["user_key"], unique=False)
    processing_restrictions_col.add_persistent_index(fields=["user_key", "scope"], unique=True)

    erasure_requests_col = db.collection(ERASURE_REQUESTS)
    erasure_requests_col.add_persistent_index(fields=["user_key"], unique=False)
    erasure_requests_col.add_persistent_index(fields=["status"], unique=False)
    erasure_requests_col.add_persistent_index(fields=["hard_delete_scheduled_at"], unique=False)

    email_change_requests_col = db.collection(EMAIL_CHANGE_REQUESTS)
    email_change_requests_col.add_persistent_index(fields=["user_key"], unique=False)
    email_change_requests_col.add_persistent_index(fields=["verification_token_hash"], unique=True)

    # REQ-029 plant identification indexes
    identification_requests_col = db.collection(IDENTIFICATION_REQUESTS)
    identification_requests_col.add_persistent_index(fields=["tenant_key", "user_key"], unique=False)
    identification_requests_col.add_persistent_index(fields=["created_at"], unique=False)

    # REQ-029-A DINOv2 diagnosis + reference-image acquisition indexes
    diagnosis_requests_col = db.collection(DIAGNOSIS_REQUESTS)
    diagnosis_requests_col.add_persistent_index(fields=["tenant_key", "user_key"], unique=False)
    diagnosis_requests_col.add_persistent_index(fields=["plant_instance_key"], unique=False)
    diagnosis_requests_col.add_persistent_index(fields=["created_at"], unique=False)

    reference_image_jobs_col = db.collection(REFERENCE_IMAGE_JOBS)
    reference_image_jobs_col.add_persistent_index(fields=["species_key"], unique=True)
    reference_image_jobs_col.add_persistent_index(fields=["status"], unique=False)

    # REQ-044 Pest detection indexes (§5.1)
    pest_detections_col = db.collection(PEST_DETECTIONS)
    pest_detections_col.add_persistent_index(fields=["tenant_key"], unique=False)
    pest_detections_col.add_persistent_index(fields=["plant_instance_key"], unique=False)
    pest_detections_col.add_persistent_index(fields=["created_at"], unique=False)
    pest_detections_col.add_persistent_index(fields=["is_confident"], unique=False)

    beneficials_col = db.collection(BENEFICIALS)
    beneficials_col.add_persistent_index(fields=["slug"], unique=True)
    beneficials_col.add_persistent_index(fields=["scientific_name"], unique=True)

    # REQ-038 CV disease diagnosis index — the history query filters by
    # (tenant_key, user_key) and sorts by created_at.
    plant_diagnosis_requests_col = db.collection(PLANT_DIAGNOSIS_REQUESTS)
    plant_diagnosis_requests_col.add_persistent_index(fields=["tenant_key", "user_key", "created_at"], unique=False)

    # REQ-010 user-contributed pest reference image indexes — the gallery query
    # always filters by (tenant_key, pest_key); DSGVO lookup filters by tenant.
    pest_image_contributions_col = db.collection(PEST_IMAGE_CONTRIBUTIONS)
    pest_image_contributions_col.add_persistent_index(fields=["tenant_key", "pest_key"], unique=False)
    pest_image_contributions_col.add_persistent_index(fields=["tenant_key"], unique=False)
    pest_image_contributions_col.add_persistent_index(fields=["attachment_id"], unique=False)

    # NFR-013 Object storage — attachment catalog indexes
    attachments_col = db.collection(ATTACHMENTS)
    attachments_col.add_persistent_index(fields=["tenant_key", "created_by"], unique=False)
    attachments_col.add_persistent_index(fields=["tenant_key", "sha256"], unique=False)
    attachments_col.add_persistent_index(fields=["tenant_key", "category"], unique=False)
    attachments_col.add_persistent_index(fields=["storage_key"], unique=True)

    # REQ-046 Weather data sources indexes
    weather_forecasts_col = db.collection(WEATHER_FORECASTS)
    weather_forecasts_col.add_persistent_index(fields=["site_key", "forecast_date", "source"], unique=False)

    weather_source_configs_col = db.collection(WEATHER_SOURCE_CONFIGS)
    # 1:1 per site within a tenant (REQ-046 §2.1).
    weather_source_configs_col.add_persistent_index(fields=["tenant_key", "site_key"], unique=True)

    # REQ-031 KI-Assistent indexes (§3.1)
    ai_provider_configs_col = db.collection(AI_PROVIDER_CONFIGS)
    ai_provider_configs_col.add_persistent_index(fields=["tenant_key"], unique=False)

    ai_conversations_col = db.collection(AI_CONVERSATIONS)
    ai_conversations_col.add_persistent_index(fields=["tenant_key", "user_key"], unique=False)
    ai_conversations_col.add_persistent_index(fields=["expires_at"], unique=False)

    ai_tip_cache_col = db.collection(AI_TIP_CACHE)
    ai_tip_cache_col.add_persistent_index(fields=["tenant_key", "context_type", "context_key"], unique=False)
    ai_tip_cache_col.add_persistent_index(fields=["valid_until"], unique=False)

    ai_audit_log_col = db.collection(AI_AUDIT_LOG)
    ai_audit_log_col.add_persistent_index(fields=["tenant_key", "user_key"], unique=False)
    ai_audit_log_col.add_persistent_index(fields=["created_at"], unique=False)

    # REQ-035 KI terminology glossary indexes (§2.1, §2.2)
    glossary_terms_col = db.collection(GLOSSARY_TERMS)
    glossary_terms_col.add_persistent_index(fields=["slug"], unique=True)
    glossary_terms_col.add_persistent_index(fields=["category"], unique=False)
    glossary_terms_col.add_persistent_index(fields=["is_active"], unique=False)

    glossary_term_cache_col = db.collection(GLOSSARY_TERM_CACHE)
    glossary_term_cache_col.add_persistent_index(
        fields=["term_slug", "language", "expertise_level", "kb_version"], unique=True
    )
    glossary_term_cache_col.add_persistent_index(fields=["valid_until"], unique=False)

    # REQ-033 MCP server indexes (§3). Audit log queried by service account +
    # tenant (privacy self-service) and swept by created_at (90d retention).
    # Idempotency records keyed by (service_account_key, tenant_key, tool_name,
    # idempotency_key) — tenant_key is part of the unique scope (SEC-005) so a
    # multi-tenant service account cannot cross-replay — and swept by expires_at
    # (24h retention).
    mcp_audit_log_col = db.collection(MCP_AUDIT_LOG)
    mcp_audit_log_col.add_persistent_index(fields=["service_account_key"], unique=False)
    mcp_audit_log_col.add_persistent_index(fields=["tenant_key", "created_at"], unique=False)
    mcp_audit_log_col.add_persistent_index(fields=["created_at"], unique=False)

    mcp_idempotency_record_col = db.collection(MCP_IDEMPOTENCY_RECORD)
    mcp_idempotency_record_col.add_persistent_index(
        fields=["service_account_key", "tenant_key", "tool_name", "idempotency_key"], unique=True
    )
    mcp_idempotency_record_col.add_persistent_index(fields=["expires_at"], unique=False)

    # REQ-026 Aquaponics indexes
    fish_species_col = db.collection(FISH_SPECIES)
    fish_species_col.add_persistent_index(fields=["scientific_name"], unique=True)
    fish_species_col.add_persistent_index(fields=["temperature_zone"], unique=False)

    aquaponic_systems_col = db.collection(AQUAPONIC_SYSTEMS)
    aquaponic_systems_col.add_persistent_index(fields=["tenant_key"], unique=False)

    fish_stocks_col = db.collection(FISH_STOCKS)
    fish_stocks_col.add_persistent_index(fields=["tenant_key", "system_key"], unique=False)

    water_tests_col = db.collection(WATER_TESTS)
    water_tests_col.add_persistent_index(fields=["system_key", "tested_at"], unique=False)

    fish_feeding_events_col = db.collection(FISH_FEEDING_EVENTS)
    fish_feeding_events_col.add_persistent_index(fields=["system_key", "fed_at"], unique=False)
    fish_feeding_events_col.add_persistent_index(fields=["stock_key"], unique=False)

    supplementation_events_col = db.collection(SUPPLEMENTATION_EVENTS)
    supplementation_events_col.add_persistent_index(fields=["system_key", "applied_at"], unique=False)

    # REQ-016 InvenTree integration indexes (all tenant-scoped)
    inventree_connections_col = db.collection(INVENTREE_CONNECTIONS)
    inventree_connections_col.add_persistent_index(fields=["tenant_key"], unique=False)

    inventree_references_col = db.collection(INVENTREE_REFERENCES)
    inventree_references_col.add_persistent_index(
        fields=["tenant_key", "entity_collection", "entity_key"], unique=False
    )

    stock_transactions_col = db.collection(STOCK_TRANSACTIONS)
    stock_transactions_col.add_persistent_index(fields=["tenant_key", "status", "created_at"], unique=False)
    stock_transactions_col.add_persistent_index(fields=["reference_key"], unique=False)

    equipment_col = db.collection(EQUIPMENT)
    equipment_col.add_persistent_index(fields=["tenant_key", "equipment_type", "status"], unique=False)

    # REQ-041 NASA POWER climate normals — one record per (site, source) within a
    # tenant; upserts key off it, so the uniqueness is enforced at the storage layer.
    climate_normals_col = db.collection(CLIMATE_NORMALS)
    climate_normals_col.add_persistent_index(fields=["tenant_key", "site_key", "source"], unique=True)

    # REQ-039 hardiness zones — the label is also the ``_key``; the unique zone
    # index guards lookups and keeps the seed idempotent.
    hardiness_zones_col = db.collection(HARDINESS_ZONES)
    hardiness_zones_col.add_persistent_index(fields=["zone"], unique=True)

    # REQ-039 — one hardiness-zone assignment edge per site.
    located_in_zone_col = db.collection(LOCATED_IN_ZONE)
    located_in_zone_col.add_persistent_index(fields=["_from"], unique=False)

    # REQ-017 Propagation / lineage indexes — tenant-scoped event/batch/phenotype
    # reads and the global+tenant rooting-protocol union.
    propagation_events_col = db.collection(PROPAGATION_EVENTS)
    propagation_events_col.add_persistent_index(fields=["tenant_key"], unique=False)
    propagation_events_col.add_persistent_index(fields=["tenant_key", "batch_key"], unique=False)
    propagation_events_col.add_persistent_index(fields=["tenant_key", "species_key"], unique=False)

    propagation_batches_col = db.collection(PROPAGATION_BATCHES)
    propagation_batches_col.add_persistent_index(fields=["tenant_key"], unique=False)
    propagation_batches_col.add_persistent_index(fields=["tenant_key", "status"], unique=False)

    rooting_protocols_col = db.collection(ROOTING_PROTOCOLS)
    rooting_protocols_col.add_persistent_index(fields=["tenant_key"], unique=False)
    rooting_protocols_col.add_persistent_index(fields=["tenant_key", "method"], unique=False)

    phenotype_notes_col = db.collection(PHENOTYPE_NOTES)
    phenotype_notes_col.add_persistent_index(fields=["tenant_key", "plant_key"], unique=False)

    # REQ-037 irrigation demands — one record per (site, run, day) within a tenant;
    # the upsert keys off it, so uniqueness is enforced at the storage layer.
    irrigation_demands_col = db.collection(IRRIGATION_DEMANDS)
    irrigation_demands_col.add_persistent_index(
        fields=["tenant_key", "site_key", "run_key", "demand_date"], unique=True
    )

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
