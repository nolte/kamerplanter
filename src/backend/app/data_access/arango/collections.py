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
WATERED_SLOT = "watered_slot"
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
    WATERED_SLOT,
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
        "from_vertex_collections": [SITES],
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
        "to_vertex_collections": [SUBSTRATES],
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
        "edge_collection": WATERED_SLOT,
        "from_vertex_collections": [WATERING_EVENTS],
        "to_vertex_collections": [SLOTS],
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

    wf_templates_col = db.collection(WORKFLOW_TEMPLATES)
    wf_templates_col.add_hash_index(fields=["name"], unique=True)

    # Create or update named graph
    if not db.has_graph(GRAPH_NAME):
        db.create_graph(GRAPH_NAME, edge_definitions=GRAPH_EDGE_DEFINITIONS)
    else:
        graph = db.graph(GRAPH_NAME)
        existing = {ed["edge_collection"] for ed in graph.edge_definitions()}
        for ed in GRAPH_EDGE_DEFINITIONS:
            if ed["edge_collection"] not in existing:
                graph.create_edge_definition(**ed)
