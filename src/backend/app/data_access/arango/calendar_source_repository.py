"""ArangoDB reads behind the aggregated calendar (REQ-015, #1638).

Moved verbatim out of
:class:`~app.domain.engines.calendar_aggregation_engine.CalendarAggregationEngine`,
which ran these queries against a ``StandardDatabase`` it held — an engine
with a persistence handle, one layer below where a handle may live (NFR-001).

**Lifecycle source.** The two plant queries still resolve a species' phases
through the legacy ``has_lifecycle`` → ``consists_of`` → ``growth_phases``
path. The ``has_phase_sequence`` edges the old engine TODO waited for do exist
(``lifecycle_to_phase_sequence_reconcile`` in ``app/migrations/seeds/registry.py``
creates them on every boot), so switching is no longer blocked on a migration —
but it is a behaviour change (phase definitions and sequence entries instead of
growth phases), not a move, and it is left to its own change so this module's
queries stay identical to the ones they replaced.
"""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.interfaces.calendar_source_repository import ICalendarSourceRepository


class ArangoCalendarSourceRepository(ICalendarSourceRepository):
    """Read-only, multi-collection: not a ``BaseArangoRepository`` of any one collection."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def list_tasks_due(self, start: str, end: str, *, tenant_key: str) -> list[dict]:
        aql = f"""
        FOR t IN {col.TASKS}
          FILTER t.due_date != null
          FILTER t.due_date >= @start AND t.due_date <= @end
          FILTER t.tenant_key == @tenant_key
          RETURN t
        """
        bind = {"start": start, "end": end, "tenant_key": tenant_key}
        return list(self._db.aql.execute(aql, bind_vars=bind))

    def list_phase_timeline_rows(self) -> list[dict]:
        aql = f"""
        FOR pi IN {col.PLANT_INSTANCES}
          FILTER pi.removed_on == null
          LET run_edge = FIRST(
            FOR e IN {col.RUN_CONTAINS}
              FILTER e._to == pi._id
              RETURN e
          )
          LET run = run_edge != null ? DOCUMENT(run_edge._from) : null
          FILTER run == null OR run.status IN ["active", "harvesting"]
          LET lc_edge = FIRST(
            FOR e IN {col.HAS_LIFECYCLE}
              FILTER e._from == CONCAT("{col.SPECIES}/", pi.species_key)
              RETURN e
          )
          LET lc = lc_edge != null ? DOCUMENT(lc_edge._to) : null
          FILTER lc != null
          LET gps = (
            FOR e IN {col.CONSISTS_OF}
              FILTER e._from == lc._id
              LET gp = DOCUMENT(e._to)
              FILTER gp != null
              SORT gp.sequence_order ASC
              RETURN gp
          )
          FILTER LENGTH(gps) > 0
          LET histories = (
            FOR ph IN {col.PHASE_HISTORIES}
              FILTER ph.plant_instance_key == pi._key
              RETURN ph
          )
          LET current_gp = DOCUMENT(CONCAT("{col.GROWTH_PHASES}/", pi.current_phase_key))
          RETURN {{
            plant_key: pi._key,
            instance_id: pi.instance_id,
            plant_name: pi.plant_name,
            species_key: pi.species_key,
            current_phase: current_gp != null ? current_gp.name : '',
            run_key: run._key,
            run_name: run.name,
            growth_phases: gps,
            phase_histories: histories
          }}
        """
        return list(self._db.aql.execute(aql))

    def list_maintenance_logs(self, start: str, end: str) -> list[dict]:
        aql = f"""
        FOR m IN {col.MAINTENANCE_LOGS}
          FILTER m.performed_at != null
          FILTER m.performed_at >= @start AND m.performed_at <= @end
          RETURN m
        """
        bind = {"start": start, "end": end}
        return list(self._db.aql.execute(aql, bind_vars=bind))

    def list_watering_logs(self, start: str, end: str) -> list[dict]:
        aql = f"""
        FOR w IN {col.WATERING_LOGS}
          FILTER w.logged_at != null
          FILTER w.logged_at >= @start AND w.logged_at <= @end
          LET plant_names = (
            FOR pk IN (w.plant_keys || [])
              LET pi = DOCUMENT(CONCAT("{col.PLANT_INSTANCES}/", pk))
              FILTER pi != null
              RETURN pi.plant_name || pi.instance_id || pk
          )
          RETURN MERGE(w, {{ resolved_plant_names: plant_names }})
        """
        bind = {"start": start, "end": end}
        return list(self._db.aql.execute(aql, bind_vars=bind))

    def list_watering_forecast_rows(self, *, tenant_key: str) -> list[dict]:
        aql = f"""
        FOR pi IN {col.PLANT_INSTANCES}
          FILTER pi.removed_on == null
          FILTER pi.tenant_key == @tenant_key
          LET cp = FIRST(
            FOR c IN {col.CARE_PROFILES}
              FILTER c.plant_key == pi._key
              RETURN c
          )
          FILTER cp != null
          LET last_confirm = FIRST(
            FOR cc IN {col.CARE_CONFIRMATIONS}
              FILTER cc.plant_key == pi._key
              FILTER cc.reminder_type == "watering"
              FILTER cc.action == "confirmed"
              SORT cc.confirmed_at DESC
              LIMIT 1
              RETURN cc
          )
          LET lc_edge = FIRST(
            FOR e IN {col.HAS_LIFECYCLE}
              FILTER e._from == CONCAT("{col.SPECIES}/", pi.species_key)
              RETURN e
          )
          LET lc = lc_edge != null ? DOCUMENT(lc_edge._to) : null
          LET gps = lc != null ? (
            FOR e IN {col.CONSISTS_OF}
              FILTER e._from == lc._id
              LET gp = DOCUMENT(e._to)
              FILTER gp != null
              SORT gp.sequence_order ASC
              RETURN gp
          ) : []
          LET histories = (
            FOR ph IN {col.PHASE_HISTORIES}
              FILTER ph.plant_instance_key == pi._key
              RETURN ph
          )
          LET cultivar = pi.cultivar_key != null ? DOCUMENT(CONCAT("{col.CULTIVARS}/", pi.cultivar_key)) : null
          LET plan_edge = FIRST(
            FOR e IN {col.FOLLOWS_PLAN}
              FILTER e._from == pi._id
              RETURN e
          )
          LET plan = plan_edge != null ? DOCUMENT(plan_edge._to) : null
          LET plan_entries = plan != null ? (
            FOR pe IN {col.NUTRIENT_PLAN_PHASE_ENTRIES}
              FILTER pe.plan_key == plan._key
              SORT pe.sequence_order ASC
              RETURN pe
          ) : []
          LET current_gp2 = DOCUMENT(CONCAT("{col.GROWTH_PHASES}/", pi.current_phase_key))
          RETURN {{
            plant_key: pi._key,
            plant_name: pi.plant_name,
            instance_id: pi.instance_id,
            species_key: pi.species_key,
            current_phase: current_gp2 != null ? current_gp2.name : '',
            planted_on: pi.planted_on,
            container_volume_liters: pi.container_volume_liters,
            substrate_type_override: pi.substrate_type_override,
            care_profile: cp,
            last_watering: last_confirm.confirmed_at,
            growth_phases: gps,
            phase_histories: histories,
            cultivar_phase_overrides: cultivar.phase_watering_overrides,
            plan_name: plan.name,
            plan_cycle_restart: plan.cycle_restart_from_sequence,
            plan_entries: plan_entries
          }}
        """
        bind = {"tenant_key": tenant_key}
        return list(self._db.aql.execute(aql, bind_vars=bind))

    def get_fertilizer_product_names(self, keys: list[str]) -> dict[str, str]:
        if not keys:
            return {}
        docs = self._db.collection(col.FERTILIZERS).get_many(keys)
        return {doc["_key"]: doc.get("product_name", doc["_key"]) for doc in docs}
