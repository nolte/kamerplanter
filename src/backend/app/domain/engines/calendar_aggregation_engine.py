from datetime import UTC, datetime, time

from arango.database import StandardDatabase

from app.common.enums import (
    CATEGORY_COLORS,
    CalendarEventCategory,
    CalendarEventSource,
)
from app.data_access.arango import collections as col
from app.domain.models.calendar import CalendarEvent, CalendarEventsQuery


class CalendarAggregationEngine:
    """Aggregate calendar events from multiple sources (tasks, phase transitions, maintenance, watering)."""

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def get_events(self, query: CalendarEventsQuery) -> list[CalendarEvent]:
        start_dt = datetime.combine(query.start_date, time.min, tzinfo=UTC)
        end_dt = datetime.combine(query.end_date, time(23, 59, 59), tzinfo=UTC)

        events: list[CalendarEvent] = []
        events.extend(self._task_events(start_dt, end_dt, query))
        events.extend(self._phase_transition_events(start_dt, end_dt, query))
        events.extend(self._maintenance_events(start_dt, end_dt, query))
        events.extend(self._watering_events(start_dt, end_dt, query))

        if query.categories:
            events = [e for e in events if e.category in query.categories]

        events.sort(key=lambda e: e.start or datetime.min.replace(tzinfo=UTC))
        return events

    def _task_events(
        self, start: datetime, end: datetime, query: CalendarEventsQuery,
    ) -> list[CalendarEvent]:
        aql = f"""
        FOR t IN {col.TASKS}
          FILTER t.due_date != null
          FILTER t.due_date >= @start AND t.due_date <= @end
          FILTER t.tenant_key == @tenant_key
          RETURN t
        """
        bind = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "tenant_key": query.tenant_key,
        }
        cursor = self._db.aql.execute(aql, bind_vars=bind)
        events = []
        for doc in cursor:
            category = self._task_category_map(doc.get("category", ""))
            events.append(CalendarEvent(
                id=f"task:{doc['_key']}",
                title=doc.get("name", ""),
                description=doc.get("instruction", ""),
                category=category,
                source=CalendarEventSource.TASK,
                color=CATEGORY_COLORS.get(category, "#607D8B"),
                start=self._parse_dt(doc.get("due_date")),
                all_day=True,
                plant_key=doc.get("plant_key"),
                task_key=doc.get("_key"),
            ))
        return events

    def _phase_transition_events(
        self, start: datetime, end: datetime, query: CalendarEventsQuery,
    ) -> list[CalendarEvent]:
        aql = f"""
        FOR ph IN {col.PHASE_HISTORIES}
          FILTER ph.transitioned_at != null
          FILTER ph.transitioned_at >= @start AND ph.transitioned_at <= @end
          RETURN ph
        """
        bind = {"start": start.isoformat(), "end": end.isoformat()}
        cursor = self._db.aql.execute(aql, bind_vars=bind)
        events = []
        for doc in cursor:
            cat = CalendarEventCategory.PHASE_TRANSITION
            events.append(CalendarEvent(
                id=f"phase:{doc['_key']}",
                title=f"Phase: {doc.get('to_phase', 'unknown')}",
                description=doc.get("notes", ""),
                category=cat,
                source=CalendarEventSource.PHASE_TRANSITION,
                color=CATEGORY_COLORS.get(cat, "#9C27B0"),
                start=self._parse_dt(doc.get("transitioned_at")),
                all_day=True,
                plant_key=doc.get("plant_key"),
            ))
        return events

    def _maintenance_events(
        self, start: datetime, end: datetime, query: CalendarEventsQuery,
    ) -> list[CalendarEvent]:
        aql = f"""
        FOR m IN {col.MAINTENANCE_LOGS}
          FILTER m.performed_at != null
          FILTER m.performed_at >= @start AND m.performed_at <= @end
          RETURN m
        """
        bind = {"start": start.isoformat(), "end": end.isoformat()}
        cursor = self._db.aql.execute(aql, bind_vars=bind)
        events = []
        for doc in cursor:
            cat = CalendarEventCategory.TANK_MAINTENANCE
            events.append(CalendarEvent(
                id=f"maint:{doc['_key']}",
                title=doc.get("action", "Maintenance"),
                description=doc.get("notes", ""),
                category=cat,
                source=CalendarEventSource.MAINTENANCE_LOG,
                color=CATEGORY_COLORS.get(cat, "#00BCD4"),
                start=self._parse_dt(doc.get("performed_at")),
                all_day=False,
            ))
        return events

    def _watering_events(
        self, start: datetime, end: datetime, query: CalendarEventsQuery,
    ) -> list[CalendarEvent]:
        aql = f"""
        FOR w IN {col.WATERING_EVENTS}
          FILTER w.watered_at != null
          FILTER w.watered_at >= @start AND w.watered_at <= @end
          RETURN w
        """
        bind = {"start": start.isoformat(), "end": end.isoformat()}
        cursor = self._db.aql.execute(aql, bind_vars=bind)
        events = []
        for doc in cursor:
            cat = CalendarEventCategory.FEEDING
            events.append(CalendarEvent(
                id=f"water:{doc['_key']}",
                title="Watering",
                description=doc.get("notes", ""),
                category=cat,
                source=CalendarEventSource.WATERING,
                color=CATEGORY_COLORS.get(cat, "#2196F3"),
                start=self._parse_dt(doc.get("watered_at")),
                all_day=False,
            ))
        return events

    @staticmethod
    def _task_category_map(category: str) -> CalendarEventCategory:
        mapping = {
            "training": CalendarEventCategory.TRAINING,
            "pruning": CalendarEventCategory.PRUNING,
            "transplanting": CalendarEventCategory.TRANSPLANTING,
            "feeding": CalendarEventCategory.FEEDING,
            "ipm": CalendarEventCategory.IPM,
            "harvest": CalendarEventCategory.HARVEST,
            "maintenance": CalendarEventCategory.MAINTENANCE,
        }
        return mapping.get(category, CalendarEventCategory.CUSTOM)

    @staticmethod
    def _parse_dt(value: str | datetime | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None
