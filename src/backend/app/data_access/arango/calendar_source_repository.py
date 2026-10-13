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

**Window bounds compare instants** (#1784): ``DATE_TIMESTAMP`` on both sides,
see :mod:`app.data_access.arango.query_builder`. Compared as text, an entry half
a second inside a bound spelled ``…:00.5Z`` fell outside a bound spelled
``…:00+00:00``.
"""

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.fertilizer_repository import visible_fertilizer_labels
from app.domain.interfaces.calendar_source_repository import ICalendarSourceRepository


class ArangoCalendarSourceRepository(ICalendarSourceRepository):
    """Read-only, multi-collection: not a ``BaseArangoRepository`` of any one collection."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def list_tasks_due(self, start: str, end: str, *, tenant_key: str) -> list[dict]:
        aql = f"""
        FOR t IN {col.TASKS}
          FILTER DATE_TIMESTAMP(t.due_date) != null
          FILTER DATE_TIMESTAMP(t.due_date) >= DATE_TIMESTAMP(@start)
            AND DATE_TIMESTAMP(t.due_date) <= DATE_TIMESTAMP(@end)
          FILTER t.tenant_key == @tenant_key
          RETURN t
        """
        bind = {"start": start, "end": end, "tenant_key": tenant_key}
        return list(self._db.aql.execute(aql, bind_vars=bind))

    def list_phase_timeline_rows(self, *, tenant_key: str) -> list[dict]:
        aql = f"""
        FOR pi IN {col.PLANT_INSTANCES}
          FILTER pi.removed_on == null
          FILTER pi.tenant_key == @tenant_key
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
        return list(self._db.aql.execute(aql, bind_vars={"tenant_key": tenant_key}))

    def list_maintenance_logs(self, start: str, end: str, *, tenant_key: str) -> list[dict]:
        # A maintenance log carries no tenant of its own (``MaintenanceLog`` has
        # no ``tenant_key``); it belongs to the tenant of its tank, which the
        # tank router stamps from the request context on create (#1704).
        aql = f"""
        FOR m IN {col.MAINTENANCE_LOGS}
          FILTER DATE_TIMESTAMP(m.performed_at) != null
          FILTER DATE_TIMESTAMP(m.performed_at) >= DATE_TIMESTAMP(@start)
            AND DATE_TIMESTAMP(m.performed_at) <= DATE_TIMESTAMP(@end)
          LET tank = DOCUMENT(CONCAT("{col.TANKS}/", m.tank_key))
          FILTER tank != null AND tank.tenant_key == @tenant_key
          RETURN m
        """
        bind = {"start": start, "end": end, "tenant_key": tenant_key}
        return list(self._db.aql.execute(aql, bind_vars=bind))

    def list_watering_logs(self, start: str, end: str, *, tenant_key: str) -> list[dict]:
        # Every creator stamps ``tenant_key`` on the log (router, watering
        # service, care-reminder confirmation). The resolved plant names are
        # held to the same tenant so a stray foreign key cannot surface a
        # foreign plant's name either (#1704).
        aql = f"""
        FOR w IN {col.WATERING_LOGS}
          FILTER DATE_TIMESTAMP(w.logged_at) != null
          FILTER DATE_TIMESTAMP(w.logged_at) >= DATE_TIMESTAMP(@start)
            AND DATE_TIMESTAMP(w.logged_at) <= DATE_TIMESTAMP(@end)
          FILTER w.tenant_key == @tenant_key
          LET plant_names = (
            FOR pk IN (w.plant_keys || [])
              LET pi = DOCUMENT(CONCAT("{col.PLANT_INSTANCES}/", pk))
              FILTER pi != null AND pi.tenant_key == @tenant_key
              RETURN pi.plant_name || pi.instance_id || pk
          )
          RETURN MERGE(w, {{ resolved_plant_names: plant_names }})
        """
        bind = {"start": start, "end": end, "tenant_key": tenant_key}
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
              SORT DATE_TIMESTAMP(cc.confirmed_at) DESC
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

    def get_fertilizer_product_names(self, keys: list[str], *, tenant_key: str) -> dict[str, str]:
        """Product names of the fertilizers ``tenant_key`` may see (#1708).

        The keys come out of the tenant's own nutrient plans, but a plan entry
        names its fertilizer by key, and a bare ``get_many`` resolved a foreign
        tenant's private product as readily as a global one. The lookup is the
        shared :func:`~app.data_access.arango.fertilizer_repository.visible_fertilizer_labels`;
        a key it rejects is omitted and the calendar shows the key instead.
        """
        labels = visible_fertilizer_labels(self._db, keys, tenant_key=tenant_key)
        return {key: name or key for key, (name, _brand) in labels.items()}
