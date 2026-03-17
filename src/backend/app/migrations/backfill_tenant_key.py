"""Backfill tenant_key on all tenant-scoped documents.

Phase 1: Assign tenant_key to top-level resources (sites, tanks, etc.)
         using the user's personal tenant from their membership.
Phase 2: Propagate tenant_key from parent documents to children
         (site -> locations -> slots, tank -> tank_states, etc.)
"""

import logging

from arango.database import StandardDatabase

from app.data_access.arango import collections as col

logger = logging.getLogger(__name__)

# Collections that are direct tenant-scoped resources
# These get tenant_key from the creator's personal tenant
TOP_LEVEL_COLLECTIONS = [
    col.SITES,
    col.PLANT_INSTANCES,
    col.PLANTING_RUNS,
    col.TANKS,
    col.FERTILIZERS,
    col.NUTRIENT_PLANS,
    col.FEEDING_EVENTS,
    col.WATERING_EVENTS,
    col.WATERING_LOGS,
    col.TASKS,
    col.WORKFLOW_TEMPLATES,
    col.TASK_TEMPLATES,
    col.WORKFLOW_EXECUTIONS,
    col.PESTS,
    col.DISEASES,
    col.TREATMENTS,
    col.INSPECTIONS,
    col.TREATMENT_APPLICATIONS,
    col.HARVEST_INDICATORS,
    col.HARVEST_OBSERVATIONS,
    col.HARVEST_BATCHES,
    col.QUALITY_ASSESSMENTS,
    col.YIELD_METRICS,
    col.CALENDAR_FEEDS,
    col.ONBOARDING_STATES,
    col.USER_PREFERENCES,
    col.SENSORS,
    col.CARE_PROFILES,
    col.CARE_CONFIRMATIONS,
]

# Child collections that inherit tenant_key from a parent via a foreign key
CHILD_PROPAGATION = [
    # (child_collection, parent_fk_field, parent_collection)
    (col.LOCATIONS, "site_key", col.SITES),
    (col.PLANTING_RUN_ENTRIES, "run_key", col.PLANTING_RUNS),
    (col.TANK_STATES, "tank_key", col.TANKS),
    (col.TANK_FILL_EVENTS, "tank_key", col.TANKS),
    (col.MAINTENANCE_LOGS, "tank_key", col.TANKS),
    (col.MAINTENANCE_SCHEDULES, "tank_key", col.TANKS),
    (col.FERTILIZER_STOCKS, "fertilizer_key", col.FERTILIZERS),
    (col.NUTRIENT_PLAN_PHASE_ENTRIES, "plan_key", col.NUTRIENT_PLANS),
    (col.TASK_COMMENTS, "task_key", col.TASKS),
    (col.TASK_AUDIT_ENTRIES, "task_key", col.TASKS),
]

# Slots inherit from locations (2nd level)
SLOT_PROPAGATION = (col.SLOTS, "location_key", col.LOCATIONS)


def _resolve_default_tenant(db: StandardDatabase) -> str | None:
    """Find the personal tenant to use as default for orphaned docs.

    Strategy: find a non-platform tenant where the user is admin,
    preferring newer tenants (likely the primary user's personal tenant).
    """
    query = """
    FOR m IN memberships
        FILTER m.role == "admin"
        LET t = DOCUMENT(CONCAT('tenants/', m.tenant_key))
        FILTER t != null AND t.slug != "platform"
        SORT t.created_at DESC
        LIMIT 1
        RETURN t._key
    """
    result = list(db.aql.execute(query))
    return result[0] if result else None


def backfill_tenant_key(db: StandardDatabase) -> dict[str, int]:
    """Assign tenant_key to all documents that are missing it.

    Returns counts of updated documents.
    """
    stats: dict[str, int] = {"total_updated": 0, "warnings": 0}

    default_tenant_key = _resolve_default_tenant(db)
    if not default_tenant_key:
        logger.error("No default tenant found — cannot backfill tenant_key")
        return stats

    logger.info("Using default tenant_key=%s for orphaned documents", default_tenant_key)

    # Phase 1: Assign tenant_key to top-level collections
    for coll_name in TOP_LEVEL_COLLECTIONS:
        query = f"""
        FOR doc IN {coll_name}
            FILTER doc.tenant_key == null OR doc.tenant_key == ""
            UPDATE doc WITH {{ tenant_key: @tenant_key }} IN {coll_name}
            RETURN 1
        """
        cursor = db.aql.execute(query, bind_vars={"tenant_key": default_tenant_key})
        count = sum(1 for _ in cursor)
        if count > 0:
            stats[f"{coll_name}_updated"] = count
            stats["total_updated"] += count
            logger.info("Phase 1: %s — %d documents updated", coll_name, count)

    # Phase 2: Propagate tenant_key from parent to child collections
    for child_coll, fk_field, parent_coll in CHILD_PROPAGATION:
        query = f"""
        FOR doc IN {child_coll}
            FILTER doc.tenant_key == null OR doc.tenant_key == ""
            LET parent = DOCUMENT(CONCAT('{parent_coll}/', doc.{fk_field}))
            FILTER parent != null AND parent.tenant_key != null AND parent.tenant_key != ""
            UPDATE doc WITH {{ tenant_key: parent.tenant_key }} IN {child_coll}
            RETURN 1
        """
        cursor = db.aql.execute(query)
        count = sum(1 for _ in cursor)
        if count > 0:
            stats[f"{child_coll}_updated"] = count
            stats["total_updated"] += count
            logger.info("Phase 2: %s (from %s) — %d documents updated", child_coll, parent_coll, count)

    # Phase 2b: Slots inherit from locations
    child_coll, fk_field, parent_coll = SLOT_PROPAGATION
    query = f"""
    FOR doc IN {child_coll}
        FILTER doc.tenant_key == null OR doc.tenant_key == ""
        LET parent = DOCUMENT(CONCAT('{parent_coll}/', doc.{fk_field}))
        FILTER parent != null AND parent.tenant_key != null AND parent.tenant_key != ""
        UPDATE doc WITH {{ tenant_key: parent.tenant_key }} IN {child_coll}
        RETURN 1
    """
    cursor = db.aql.execute(query)
    count = sum(1 for _ in cursor)
    if count > 0:
        stats[f"{child_coll}_updated"] = count
        stats["total_updated"] += count
        logger.info("Phase 2b: %s (from %s) — %d documents updated", child_coll, parent_coll, count)

    # Phase 3: Catch any remaining orphans with default tenant
    all_collections = TOP_LEVEL_COLLECTIONS + [c for c, _, _ in CHILD_PROPAGATION] + [SLOT_PROPAGATION[0]]
    for coll_name in all_collections:
        query = f"""
        FOR doc IN {coll_name}
            FILTER doc.tenant_key == null OR doc.tenant_key == ""
            UPDATE doc WITH {{ tenant_key: @tenant_key }} IN {coll_name}
            RETURN 1
        """
        cursor = db.aql.execute(query, bind_vars={"tenant_key": default_tenant_key})
        count = sum(1 for _ in cursor)
        if count > 0:
            stats[f"{coll_name}_fallback"] = count
            stats["total_updated"] += count
            stats["warnings"] += count
            logger.warning(
                "Phase 3 fallback: %s — %d documents assigned default tenant",
                coll_name,
                count,
            )

    logger.info(
        "Backfill complete: %d total documents updated, %d warnings",
        stats["total_updated"],
        stats["warnings"],
    )
    return stats
