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

    # Create or update named graph
    if not db.has_graph(GRAPH_NAME):
        db.create_graph(GRAPH_NAME, edge_definitions=GRAPH_EDGE_DEFINITIONS)
    else:
        graph = db.graph(GRAPH_NAME)
        existing = {ed["edge_collection"] for ed in graph.edge_definitions()}
        for ed in GRAPH_EDGE_DEFINITIONS:
            if ed["edge_collection"] not in existing:
                graph.create_edge_definition(**ed)
