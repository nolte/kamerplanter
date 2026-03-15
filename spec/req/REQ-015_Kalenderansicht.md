# Spezifikation: REQ-015 - Kalenderansicht & Kalender-Integration

```yaml
ID: REQ-015
Titel: Kalenderansicht & Kalender-Integration (iCal/webcal)
Kategorie: Visualisierung & Integration
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, React (FullCalendar), iCalendar (RFC 5545)
Status: Entwurf
Version: 1.4 (Zierpflanzen-Aussaatkalender + Agrarbiologie-Review)
```

## 1. Business Case

**User Story (Kalenderansicht):** "Als Gärtner möchte ich alle anstehenden Aufgaben, Phasentransitionen, Düngetermine, Wartungen und Inspektionen in einer zentralen Kalenderansicht sehen — damit ich meinen Tag, meine Woche und meinen Monat effektiv planen kann, ohne zwischen verschiedenen Modulen hin- und hernavigieren zu müssen."

**User Story (Filterung):** "Als Gärtner möchte ich den Kalender nach Kategorie, Standort, Pflanze, Priorität und Status filtern können — damit ich gezielt die für mich relevanten Termine sehe, z.B. nur die kritischen Aufgaben für Zelt 1 oder alle IPM-Inspektionen im nächsten Monat."

**User Story (Externe Integration):** "Als Gärtner möchte ich meinen Kamerplanter-Kalender in Thunderbird, Apple Calendar oder Google Calendar abonnieren können — damit ich Push-Benachrichtigungen auf allen Geräten erhalte und meine Gartenarbeit zusammen mit privaten Terminen sehen kann, ohne die Kamerplanter-App öffnen zu müssen."

<!-- Quelle: Outdoor-Garden-Planner Review G-001, G-005 -->
**User Story (Aussaatkalender):** "Als Freilandgärtnerin möchte ich einen Aussaatkalender sehen, der mir pro Pflanze zeigt: wann Voranzucht starten, wann Direktsaat möglich, wann Ernte erwartet — alles angepasst an meinen letzten Frosttermin und meine Klimazone."

**User Story (Saisonübersicht):** "Als Gartenplanerin möchte ich eine Jahresübersicht sehen, die mir Monat für Monat zeigt, welche Pflanzen gesät, gepflanzt, gepflegt und geerntet werden — damit ich den Überblick über meinen Garten behalte."

**User Story (Frostkalender):** "Als Gärtnerin möchte ich den letzten und ersten Frosttermin für meinen Standort einstellen können, damit alle Aussaat- und Pflanztermine automatisch darauf berechnet werden."

**Beschreibung:**
Events und geplante Tätigkeiten entstehen in zahlreichen Modulen: Tasks (REQ-006), Phasentransitionen (REQ-003), Düngung (REQ-004), Ernte (REQ-007), Post-Harvest (REQ-008), IPM-Inspektionen (REQ-010), Tankwartung (REQ-014) und Pflanzdurchlauf-Meilensteine (REQ-013). Aktuell fehlt eine zentrale Kalenderdarstellung sowie die Möglichkeit, diese Termine in externe Kalender-Apps zu exportieren.

**Kernkonzepte:**

**REQ-006 Tasks als primäre Kalenderquelle:**
Alle Module erzeugen bereits Tasks über REQ-006 (Phasenwechsel-Tasks, Wartungs-Tasks, Inspektions-Tasks, etc.). Der Kalender nutzt die `:Task`-Collection als **primäre Datenquelle**. Damit entfällt die Notwendigkeit einer separaten Event-Collection — der Kalender aggregiert, was bereits existiert.

**Timeline-Events als informelle Ergänzung:**
Neben geplanten Tasks gibt es **vergangene Events**, die keine Tasks sind, aber für den zeitlichen Überblick relevant: abgeschlossene Phasentransitionen, durchgeführte Düngungen, aufgezeichnete Tankbefüllungen, Bewässerungen. Diese werden als optionale Timeline-Events aus bestehenden Collections aggregiert (read-only, nicht gespeichert).

**CalendarEvent — Unified View-Modell:**
Ein `CalendarEvent` ist ein **virtuelles Aggregat** (computed at query time, nicht persistiert). Es vereinheitlicht Tasks und Timeline-Events in ein gemeinsames Schema für Frontend und iCal-Export.

**CalendarFeed — Personalisierter iCal-Feed:**
Ein `CalendarFeed` ist ein persistiertes Konfigurationsobjekt mit Token-basiertem Zugang. Jeder Feed hat eigene Filter (Kategorien, Locations, Prioritäten) und eine eindeutige URL, die in externen Kalender-Apps abonniert werden kann. Feeds sind Read-Only — keine bidirektionale Synchronisation.

**Farbkodierung pro Kategorie:**
Jede `CalendarEventCategory` hat eine fest zugeordnete Farbe für konsistente visuelle Unterscheidung in der Kalenderansicht und im Export (via `X-APPLE-CALENDAR-COLOR`, `COLOR`-Property).

**Abgrenzung:**
- Kein CalDAV-Server — zu komplex für MVP. Nur Read-Only-Feeds via `webcal://`
- Keine bidirektionale Sync — Events in Thunderbird bearbeiten aktualisiert Kamerplanter nicht
- Keine neue Event-Collection — CalendarEvent ist ein virtuelles Aggregat aus bestehenden Daten

## 2. ArangoDB-Modellierung

### Nodes:

- **`:CalendarFeed`** — Persistierte Feed-Konfiguration für iCal-Export
  - Collection: `calendar_feeds`
  - Properties:
    - `name: str` (z.B. "Mein Hauptkalender", "Nur Zelt 1 kritisch")
    - `token: str` (URL-sicherer Random-Token, 32 Zeichen, hex)
    - `filters: CalendarFeedFilters` (embedded, siehe Python-Modelle)
    - `include_timeline: bool` (Timeline-Events in Feed einschließen, Default: false)
    - `alarm_enabled: bool` (VALARM in Events einschließen, Default: true)
    - `created_at: datetime`
    - `updated_at: datetime`
    - `last_accessed_at: Optional[datetime]` (für Monitoring toter Feeds)

### Edges:

- **`owns_feed`** — (Zukünftig: `users → calendar_feeds`, aktuell ohne Auth global)
  - Vorbereitet für JWT-Auth, aktuell werden alle Feeds global behandelt
  - Edge-Collection angelegt aber erst mit Auth-Modul aktiv genutzt

### Indizes:

```
calendar_feeds:
  - PERSISTENT INDEX on [token] UNIQUE    -- Feed-Lookup via URL-Token
```

### AQL — Multi-Source-Aggregation:

**Primär: Tasks als Kalender-Events**

```aql
// Alle Tasks im Zeitraum als CalendarEvents
FOR task IN tasks
  FILTER task.due_date >= @start AND task.due_date <= @end
  FILTER LENGTH(@categories) == 0 OR task.category IN @categories
  FILTER @priority == null OR task.priority == @priority
  FILTER LENGTH(@statuses) == 0 OR task.status IN @statuses

  // Optional: Location-Filter via assigned_to Edge
  LET location = (
    FOR v, e IN 1..1 OUTBOUND task assigned_to
      FILTER IS_SAME_COLLECTION("locations", v)
      RETURN v
  )[0]
  FILTER @location_id == null OR location._key == @location_id

  // Optional: Plant-Filter via assigned_to Edge
  LET plant = (
    FOR v, e IN 1..1 OUTBOUND task assigned_to
      FILTER IS_SAME_COLLECTION("plants", v)
      RETURN v
  )[0]
  FILTER @plant_id == null OR plant._key == @plant_id

  RETURN {
    id: task._key,
    source: "task",
    source_id: task._key,
    title: task.name,
    description: task.instruction,
    category: task.category,
    start: task.due_date,
    end: task.due_date,
    all_day: task.scheduled_time == null,
    scheduled_time: task.scheduled_time,
    priority: task.priority,
    status: task.status,
    location_id: location._key,
    location_name: location.name,
    plant_id: plant._key,
    estimated_duration_minutes: task.estimated_duration_minutes
  }
```

**Ergänzend: Timeline-Events (optional, wenn `include_timeline=true`)**

```aql
// Phasentransitionen als Timeline-Events
FOR ph IN phase_histories
  FILTER ph.transitioned_at >= @start AND ph.transitioned_at <= @end
  FILTER @location_id == null  // Location-Filter über Plant → Location
    OR (
      FOR plant IN 1..1 INBOUND ph GRAPH "kamerplanter_graph"
        FOR loc IN 1..1 OUTBOUND plant planted_in
          FILTER loc._key == @location_id
          RETURN true
    )[0] == true
  RETURN {
    id: CONCAT("phase_", ph._key),
    source: "phase_transition",
    source_id: ph._key,
    title: CONCAT("Phase: ", ph.from_phase, " → ", ph.to_phase),
    description: ph.notes,
    category: "phase_transition",
    start: ph.transitioned_at,
    end: ph.transitioned_at,
    all_day: false,
    priority: "medium",
    status: "completed"
  }
```

```aql
// Tank-Wartungs-Logs als Timeline-Events
FOR ml IN maintenance_logs
  FILTER ml.performed_at >= @start AND ml.performed_at <= @end
  LET tank = DOCUMENT(CONCAT("tanks/", ml.tank_id))
  RETURN {
    id: CONCAT("maint_", ml._key),
    source: "maintenance_log",
    source_id: ml._key,
    title: CONCAT("Wartung: ", ml.maintenance_type, " — ", tank.name),
    description: ml.notes,
    category: "tank_maintenance",
    start: ml.performed_at,
    end: ml.performed_at,
    all_day: false,
    priority: "low",
    status: "completed"
  }
```

```aql
// Tank-Befüllungen als Timeline-Events
FOR fe IN tank_fill_events
  FILTER fe.filled_at >= @start AND fe.filled_at <= @end
  LET tank = DOCUMENT(CONCAT("tanks/", fe.tank_id))
  RETURN {
    id: CONCAT("fill_", fe._key),
    source: "tank_fill",
    source_id: fe._key,
    title: CONCAT("Befüllung: ", fe.fill_type, " — ", tank.name),
    description: CONCAT(fe.volume_liters, "L, EC: ", fe.measured_ec, ", pH: ", fe.measured_ph),
    category: "feeding",
    start: fe.filled_at,
    end: fe.filled_at,
    all_day: false,
    priority: "low",
    status: "completed"
  }
```

```aql
// Bewässerungs-Events als Timeline-Events
FOR we IN watering_events
  FILTER we.watered_at >= @start AND we.watered_at <= @end
  RETURN {
    id: CONCAT("water_", we._key),
    source: "watering",
    source_id: we._key,
    title: CONCAT("Bewässerung: ", we.application_method, " — ", we.volume_ml, "ml"),
    category: "feeding",
    start: we.watered_at,
    end: we.watered_at,
    all_day: false,
    priority: "low",
    status: "completed"
  }
```

**Feed-Lookup via Token:**

```aql
FOR feed IN calendar_feeds
  FILTER feed.token == @token
  RETURN feed
```

## 3. Technische Umsetzung (Python)

### 3.1 Enums & Typen

```python
from enum import StrEnum


class CalendarEventCategory(StrEnum):
    """Kategorien für Kalender-Events mit Farbzuordnung."""
    TRAINING = "training"             # #4CAF50 Grün
    PRUNING = "pruning"               # #8BC34A Hellgrün
    TRANSPLANTING = "transplanting"   # #795548 Braun
    FEEDING = "feeding"               # #2196F3 Blau
    IPM = "ipm"                       # #FF9800 Orange
    HARVEST = "harvest"               # #FFC107 Gold
    MAINTENANCE = "maintenance"       # #9E9E9E Grau
    PHASE_TRANSITION = "phase_transition"  # #9C27B0 Violett
    TANK_MAINTENANCE = "tank_maintenance"  # #607D8B Blaugrau
    POST_HARVEST = "post_harvest"     # #E91E63 Pink
    CUSTOM = "custom"                 # #00BCD4 Cyan


CATEGORY_COLORS: dict[CalendarEventCategory, str] = {
    CalendarEventCategory.TRAINING: "#4CAF50",
    CalendarEventCategory.PRUNING: "#8BC34A",
    CalendarEventCategory.TRANSPLANTING: "#795548",
    CalendarEventCategory.FEEDING: "#2196F3",
    CalendarEventCategory.IPM: "#FF9800",
    CalendarEventCategory.HARVEST: "#FFC107",
    CalendarEventCategory.MAINTENANCE: "#9E9E9E",
    CalendarEventCategory.PHASE_TRANSITION: "#9C27B0",
    CalendarEventCategory.TANK_MAINTENANCE: "#607D8B",
    CalendarEventCategory.POST_HARVEST: "#E91E63",
    CalendarEventCategory.CUSTOM: "#00BCD4",
}


class CalendarEventSource(StrEnum):
    """Herkunft eines Kalender-Events."""
    TASK = "task"
    PHASE_TRANSITION = "phase_transition"
    MAINTENANCE_LOG = "maintenance_log"
    TANK_FILL = "tank_fill"
    WATERING = "watering"
```

### 3.2 Pydantic-Modelle

```python
from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, Field

from app.common.enums import CalendarEventCategory, CalendarEventSource


class CalendarEvent(BaseModel):
    """Unified View-Modell — virtuelles Aggregat, nicht persistiert."""
    id: str
    source: CalendarEventSource
    source_id: str
    title: str
    description: Optional[str] = None
    category: CalendarEventCategory
    start: datetime
    end: Optional[datetime] = None
    all_day: bool = False
    scheduled_time: Optional[time] = None
    priority: str = "medium"  # low | medium | high | critical
    status: str = "pending"   # pending | in_progress | completed | skipped
    location_id: Optional[str] = None
    location_name: Optional[str] = None
    plant_id: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    color: Optional[str] = None  # Hex-Farbe, abgeleitet aus Kategorie


class CalendarFeedFilters(BaseModel):
    """Persistierte Filter-Konfiguration für einen Feed."""
    categories: list[CalendarEventCategory] = Field(default_factory=list)
    location_ids: list[str] = Field(default_factory=list)
    plant_ids: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    statuses: list[str] = Field(default_factory=list)


class CalendarFeed(BaseModel):
    """Persistierter iCal-Feed mit Token-basiertem Zugang."""
    key: Optional[str] = Field(None, alias="_key")
    name: str
    token: str
    filters: CalendarFeedFilters = Field(default_factory=CalendarFeedFilters)
    include_timeline: bool = False
    alarm_enabled: bool = True
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None


class CalendarFeedCreate(BaseModel):
    """DTO für Feed-Erstellung."""
    name: str = Field(min_length=1, max_length=100)
    filters: CalendarFeedFilters = Field(default_factory=CalendarFeedFilters)
    include_timeline: bool = False
    alarm_enabled: bool = True


class CalendarFeedUpdate(BaseModel):
    """DTO für Feed-Aktualisierung."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    filters: Optional[CalendarFeedFilters] = None
    include_timeline: Optional[bool] = None
    alarm_enabled: Optional[bool] = None


class CalendarEventsQuery(BaseModel):
    """Query-Parameter für den Aggregations-Endpoint."""
    start: date
    end: date
    categories: list[CalendarEventCategory] = Field(default_factory=list)
    location_id: Optional[str] = None
    plant_id: Optional[str] = None
    priority: Optional[str] = None
    statuses: list[str] = Field(default_factory=list)
    include_timeline: bool = False
```

### 3.3 CalendarAggregationEngine

```python
from datetime import date

from app.common.enums import (
    CATEGORY_COLORS,
    CalendarEventCategory,
    CalendarEventSource,
)
from app.domain.models.calendar import CalendarEvent, CalendarEventsQuery


class CalendarAggregationEngine:
    """Aggregiert Events aus mehreren Quellen zu CalendarEvents.

    Primärquelle: Tasks (REQ-006)
    Optionale Timeline-Quellen: phase_histories, maintenance_logs,
    tank_fill_events, watering_events
    """

    def __init__(self, db):
        self._db = db

    def aggregate_events(
        self, query: CalendarEventsQuery
    ) -> list[CalendarEvent]:
        """Aggregiert Tasks + optional Timeline-Events."""
        events = self._query_tasks(query)

        if query.include_timeline:
            events.extend(self._query_phase_transitions(query))
            events.extend(self._query_maintenance_logs(query))
            events.extend(self._query_tank_fills(query))
            events.extend(self._query_watering_events(query))

        # Sortierung: Datum aufsteigend, dann Priorität absteigend
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        events.sort(
            key=lambda e: (e.start, priority_order.get(e.priority, 2))
        )

        # Farbe aus Kategorie ableiten
        for event in events:
            event.color = CATEGORY_COLORS.get(event.category)

        return events

    def _query_tasks(self, query: CalendarEventsQuery) -> list[CalendarEvent]:
        """AQL-Query gegen tasks Collection."""
        aql = """
        FOR task IN tasks
          FILTER task.due_date >= @start AND task.due_date <= @end
          FILTER LENGTH(@categories) == 0 OR task.category IN @categories
          FILTER @priority == null OR task.priority == @priority
          FILTER LENGTH(@statuses) == 0 OR task.status IN @statuses
          LET location = (
            FOR v IN 1..1 OUTBOUND task assigned_to
              FILTER IS_SAME_COLLECTION("locations", v)
              RETURN v
          )[0]
          FILTER @location_id == null OR location._key == @location_id
          LET plant = (
            FOR v IN 1..1 OUTBOUND task assigned_to
              FILTER IS_SAME_COLLECTION("plants", v)
              RETURN v
          )[0]
          FILTER @plant_id == null OR plant._key == @plant_id
          RETURN {
            id: task._key,
            source: "task",
            source_id: task._key,
            title: task.name,
            description: task.instruction,
            category: task.category,
            start: task.due_date,
            end: task.due_date,
            all_day: task.scheduled_time == null,
            scheduled_time: task.scheduled_time,
            priority: task.priority,
            status: task.status,
            location_id: location._key,
            location_name: location.name,
            plant_id: plant._key,
            estimated_duration_minutes: task.estimated_duration_minutes
          }
        """
        bind_vars = {
            "start": query.start.isoformat(),
            "end": query.end.isoformat(),
            "categories": [c.value for c in query.categories],
            "priority": query.priority,
            "statuses": query.statuses,
            "location_id": query.location_id,
            "plant_id": query.plant_id,
        }
        cursor = self._db.aql.execute(aql, bind_vars=bind_vars)
        return [CalendarEvent(**doc) for doc in cursor]

    def _query_phase_transitions(
        self, query: CalendarEventsQuery
    ) -> list[CalendarEvent]:
        """Phase-Transitionen aus phase_histories."""
        if (
            query.categories
            and CalendarEventCategory.PHASE_TRANSITION not in query.categories
        ):
            return []

        aql = """
        FOR ph IN phase_histories
          FILTER ph.transitioned_at >= @start AND ph.transitioned_at <= @end
          RETURN {
            id: CONCAT("phase_", ph._key),
            source: "phase_transition",
            source_id: ph._key,
            title: CONCAT("Phase: ", ph.from_phase, " → ", ph.to_phase),
            description: ph.notes,
            start: ph.transitioned_at,
            end: ph.transitioned_at,
            all_day: false,
            priority: "medium",
            status: "completed"
          }
        """
        cursor = self._db.aql.execute(aql, bind_vars={
            "start": query.start.isoformat(),
            "end": query.end.isoformat(),
        })
        return [
            CalendarEvent(
                category=CalendarEventCategory.PHASE_TRANSITION,
                **doc,
            )
            for doc in cursor
        ]

    def _query_maintenance_logs(
        self, query: CalendarEventsQuery
    ) -> list[CalendarEvent]:
        """Wartungs-Logs aus maintenance_logs."""
        if (
            query.categories
            and CalendarEventCategory.TANK_MAINTENANCE not in query.categories
        ):
            return []

        aql = """
        FOR ml IN maintenance_logs
          FILTER ml.performed_at >= @start AND ml.performed_at <= @end
          LET tank = DOCUMENT(CONCAT("tanks/", ml.tank_id))
          RETURN {
            id: CONCAT("maint_", ml._key),
            source: "maintenance_log",
            source_id: ml._key,
            title: CONCAT("Wartung: ", ml.maintenance_type, " — ", tank.name),
            description: ml.notes,
            start: ml.performed_at,
            end: ml.performed_at,
            all_day: false,
            priority: "low",
            status: "completed"
          }
        """
        cursor = self._db.aql.execute(aql, bind_vars={
            "start": query.start.isoformat(),
            "end": query.end.isoformat(),
        })
        return [
            CalendarEvent(
                category=CalendarEventCategory.TANK_MAINTENANCE,
                **doc,
            )
            for doc in cursor
        ]

    def _query_tank_fills(
        self, query: CalendarEventsQuery
    ) -> list[CalendarEvent]:
        """Tank-Befüllungen aus tank_fill_events."""
        if (
            query.categories
            and CalendarEventCategory.FEEDING not in query.categories
        ):
            return []

        aql = """
        FOR fe IN tank_fill_events
          FILTER fe.filled_at >= @start AND fe.filled_at <= @end
          LET tank = DOCUMENT(CONCAT("tanks/", fe.tank_id))
          RETURN {
            id: CONCAT("fill_", fe._key),
            source: "tank_fill",
            source_id: fe._key,
            title: CONCAT("Befüllung: ", fe.fill_type, " — ", tank.name),
            description: CONCAT(fe.volume_liters, "L"),
            start: fe.filled_at,
            end: fe.filled_at,
            all_day: false,
            priority: "low",
            status: "completed"
          }
        """
        cursor = self._db.aql.execute(aql, bind_vars={
            "start": query.start.isoformat(),
            "end": query.end.isoformat(),
        })
        return [
            CalendarEvent(
                category=CalendarEventCategory.FEEDING,
                **doc,
            )
            for doc in cursor
        ]

    def _query_watering_events(
        self, query: CalendarEventsQuery
    ) -> list[CalendarEvent]:
        """Bewässerungs-Events aus watering_events."""
        if (
            query.categories
            and CalendarEventCategory.FEEDING not in query.categories
        ):
            return []

        aql = """
        FOR we IN watering_events
          FILTER we.watered_at >= @start AND we.watered_at <= @end
          RETURN {
            id: CONCAT("water_", we._key),
            source: "watering",
            source_id: we._key,
            title: CONCAT("Bewässerung: ", we.application_method,
                          " — ", we.volume_ml, "ml"),
            start: we.watered_at,
            end: we.watered_at,
            all_day: false,
            priority: "low",
            status: "completed"
          }
        """
        cursor = self._db.aql.execute(aql, bind_vars={
            "start": query.start.isoformat(),
            "end": query.end.isoformat(),
        })
        return [
            CalendarEvent(
                category=CalendarEventCategory.FEEDING,
                **doc,
            )
            for doc in cursor
        ]
```

### 3.4 ICalGenerator — RFC 5545 iCalendar-Generierung

```python
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from app.common.enums import CATEGORY_COLORS, CalendarEventCategory
from app.domain.models.calendar import CalendarEvent


class ICalGenerator:
    """Generiert RFC 5545-konformes iCalendar aus CalendarEvents.

    Unterstützt:
    - VCALENDAR mit PRODID, VERSION, CALSCALE, X-WR-CALNAME
    - VEVENT mit SUMMARY, DTSTART/DTEND, DESCRIPTION, CATEGORIES,
      PRIORITY, STATUS, COLOR
    - VALARM (Erinnerungen, konfigurierbar)
    - X-APPLE-CALENDAR-COLOR für Apple Calendar Farbunterstützung
    """

    PRIORITY_MAP = {
        "critical": 1,   # RFC 5545: 1 = höchste
        "high": 3,
        "medium": 5,
        "low": 9,        # RFC 5545: 9 = niedrigste
    }

    STATUS_MAP = {
        "pending": "TENTATIVE",
        "in_progress": "CONFIRMED",
        "completed": "CANCELLED",
        "skipped": "CANCELLED",
        "failed": "CANCELLED",
    }

    ALARM_MINUTES = {
        "critical": 60,
        "high": 45,
        "medium": 30,
        "low": 15,
    }

    def generate(
        self,
        events: list[CalendarEvent],
        feed_name: str = "Kamerplanter",
        alarm_enabled: bool = True,
    ) -> str:
        """Generiert vollständigen iCalendar-String."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Kamerplanter//Calendar//DE",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:{self._escape(feed_name)}",
            "X-WR-TIMEZONE:Europe/Berlin",
        ]

        for event in events:
            lines.extend(self._event_to_vevent(event, alarm_enabled))

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    def _event_to_vevent(
        self, event: CalendarEvent, alarm_enabled: bool
    ) -> list[str]:
        """Konvertiert ein CalendarEvent in VEVENT-Zeilen."""
        uid = f"{event.source.value}-{event.source_id}@kamerplanter"
        now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

        lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now}",
        ]

        # DTSTART/DTEND
        if event.all_day:
            dt_str = event.start.strftime("%Y%m%d")
            lines.append(f"DTSTART;VALUE=DATE:{dt_str}")
            if event.end and event.end != event.start:
                end_str = event.end.strftime("%Y%m%d")
                lines.append(f"DTEND;VALUE=DATE:{end_str}")
        else:
            dt_str = event.start.strftime("%Y%m%dT%H%M%S")
            lines.append(f"DTSTART:{dt_str}")
            if event.estimated_duration_minutes:
                end_dt = event.start + timedelta(
                    minutes=event.estimated_duration_minutes
                )
                lines.append(f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}")

        # SUMMARY & DESCRIPTION
        lines.append(f"SUMMARY:{self._escape(event.title)}")
        if event.description:
            lines.append(
                f"DESCRIPTION:{self._escape(event.description)}"
            )

        # CATEGORIES
        lines.append(f"CATEGORIES:{event.category.value.upper()}")

        # PRIORITY (RFC 5545: 1=highest, 9=lowest)
        priority = self.PRIORITY_MAP.get(event.priority, 5)
        lines.append(f"PRIORITY:{priority}")

        # STATUS
        status = self.STATUS_MAP.get(event.status, "TENTATIVE")
        lines.append(f"STATUS:{status}")

        # COLOR (RFC 7986)
        color = CATEGORY_COLORS.get(event.category)
        if color:
            lines.append(f"COLOR:{color}")
            lines.append(f"X-APPLE-CALENDAR-COLOR:{color}")

        # Location-Info als LOCATION-Property
        if event.location_name:
            lines.append(f"LOCATION:{self._escape(event.location_name)}")

        # VALARM (Erinnerung)
        if alarm_enabled and event.status in ("pending", "in_progress"):
            alarm_min = self.ALARM_MINUTES.get(event.priority, 30)
            lines.extend([
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"DESCRIPTION:{self._escape(event.title)}",
                f"TRIGGER:-PT{alarm_min}M",
                "END:VALARM",
            ])

        lines.append("END:VEVENT")
        return lines

    @staticmethod
    def _escape(text: str) -> str:
        """Escaped Text gemäß RFC 5545."""
        return (
            text.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
        )
```

### 3.5 CalendarService

```python
import secrets
from datetime import datetime

from app.domain.engines.calendar_aggregation_engine import (
    CalendarAggregationEngine,
)
from app.domain.interfaces.calendar_feed_repository import (
    ICalendarFeedRepository,
)
from app.domain.models.calendar import (
    CalendarEvent,
    CalendarEventsQuery,
    CalendarFeed,
    CalendarFeedCreate,
    CalendarFeedUpdate,
)
from app.domain.services.ical_generator import ICalGenerator


class CalendarService:
    """Orchestriert Kalender-Aggregation, Feed-Management und iCal-Export."""

    def __init__(
        self,
        aggregation_engine: CalendarAggregationEngine,
        feed_repository: ICalendarFeedRepository,
        ical_generator: ICalGenerator,
    ):
        self._engine = aggregation_engine
        self._feeds = feed_repository
        self._ical = ical_generator

    # --- Event-Aggregation ---

    def get_events(
        self, query: CalendarEventsQuery
    ) -> list[CalendarEvent]:
        """Aggregierte Kalender-Events mit Filtern."""
        return self._engine.aggregate_events(query)

    # --- Feed CRUD ---

    def create_feed(self, dto: CalendarFeedCreate) -> CalendarFeed:
        """Erstellt einen neuen iCal-Feed mit generiertem Token."""
        now = datetime.utcnow()
        feed = CalendarFeed(
            name=dto.name,
            token=secrets.token_hex(16),
            filters=dto.filters,
            include_timeline=dto.include_timeline,
            alarm_enabled=dto.alarm_enabled,
            created_at=now,
            updated_at=now,
        )
        return self._feeds.create(feed)

    def get_feed(self, feed_id: str) -> CalendarFeed:
        return self._feeds.get_by_id(feed_id)

    def list_feeds(self) -> list[CalendarFeed]:
        return self._feeds.list_all()

    def update_feed(
        self, feed_id: str, dto: CalendarFeedUpdate
    ) -> CalendarFeed:
        feed = self._feeds.get_by_id(feed_id)
        update_data = dto.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(feed, field, value)
        feed.updated_at = datetime.utcnow()
        return self._feeds.update(feed)

    def delete_feed(self, feed_id: str) -> None:
        self._feeds.delete(feed_id)

    def regenerate_token(self, feed_id: str) -> CalendarFeed:
        """Generiert einen neuen Token für einen bestehenden Feed."""
        feed = self._feeds.get_by_id(feed_id)
        feed.token = secrets.token_hex(16)
        feed.updated_at = datetime.utcnow()
        return self._feeds.update(feed)

    # --- iCal-Export ---

    def generate_ical_for_feed(self, token: str) -> str:
        """Generiert iCal-String für einen Feed (via Token-Lookup).

        Aktualisiert last_accessed_at für Monitoring.
        Standard-Zeitraum: heute ± 90 Tage.
        """
        feed = self._feeds.get_by_token(token)
        feed.last_accessed_at = datetime.utcnow()
        self._feeds.update(feed)

        from datetime import date, timedelta
        today = date.today()
        query = CalendarEventsQuery(
            start=today - timedelta(days=90),
            end=today + timedelta(days=90),
            categories=feed.filters.categories,
            location_id=(
                feed.filters.location_ids[0]
                if feed.filters.location_ids
                else None
            ),
            plant_id=(
                feed.filters.plant_ids[0]
                if feed.filters.plant_ids
                else None
            ),
            priority=(
                feed.filters.priorities[0]
                if feed.filters.priorities
                else None
            ),
            statuses=feed.filters.statuses,
            include_timeline=feed.include_timeline,
        )
        events = self._engine.aggregate_events(query)
        return self._ical.generate(
            events,
            feed_name=feed.name,
            alarm_enabled=feed.alarm_enabled,
        )
```

### 3.6 Repository-Interface

```python
from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models.calendar import CalendarFeed


class ICalendarFeedRepository(ABC):
    """Interface für CalendarFeed-Persistierung."""

    @abstractmethod
    def create(self, feed: CalendarFeed) -> CalendarFeed: ...

    @abstractmethod
    def get_by_id(self, feed_id: str) -> CalendarFeed: ...

    @abstractmethod
    def get_by_token(self, token: str) -> CalendarFeed: ...

    @abstractmethod
    def list_all(self) -> list[CalendarFeed]: ...

    @abstractmethod
    def update(self, feed: CalendarFeed) -> CalendarFeed: ...

    @abstractmethod
    def delete(self, feed_id: str) -> None: ...
```

### 3.7 Frontend-Konzept

**Bibliothek:** [FullCalendar](https://fullcalendar.io/) React-Komponente (MIT-Lizenz)

**Ansichten:**
- **Monatsansicht** (Default Desktop): Grid mit farbkodierten Event-Blöcken
- **Wochenansicht:** Zeitraster mit Stunden-Slots
- **Tagesansicht:** Detaillierte Stunden-Darstellung
- **Agenda-Ansicht:** Listenformat, Default auf Mobile

**Kalenderseite (`/calendar`):**

```
┌─────────────────────────────────────────────────────────┐
│  ◀  Februar 2026  ▶     [Monat] [Woche] [Tag] [Agenda] │
├──────────┬──────────────────────────────────────────────┤
│ Filter   │                                              │
│          │  Mo    Di    Mi    Do    Fr    Sa    So       │
│ □ Alle   │ ┌────┬────┬────┬────┬────┬────┬────┐       │
│          │ │    │    │    │    │    │    │    │       │
│ Kategorie│ │    │ 🟢 │    │ 🔵 │    │    │    │       │
│ □ Train. │ │    │Top │    │Düng│    │    │    │       │
│ □ Fütt.  │ │    │    │    │    │    │    │    │       │
│ □ IPM    │ ├────┼────┼────┼────┼────┼────┼────┤       │
│ □ Ernte  │ │ 🟣 │    │ 🟠 │    │ 🔴 │    │    │       │
│ □ Wartung│ │Pha │    │IPM │    │Ern │    │    │       │
│ □ Phase  │ │    │    │    │    │    │    │    │       │
│          │ └────┴────┴────┴────┴────┴────┴────┘       │
│ Standort │                                              │
│ [Alle  ▾]│                                              │
│          │                                              │
│ Priorität│                                              │
│ [Alle  ▾]│                                              │
│          │                                              │
│ Status   │  ☑ Timeline anzeigen                         │
│ [Alle  ▾]│                                              │
│          │                                              │
│ ──────── │  [📥 Feed verwalten]                         │
│ Feeds    │                                              │
│ [Manage] │                                              │
└──────────┴──────────────────────────────────────────────┘
```

**Event-Interaktion:**
- **Click auf Event:** Popover mit Details (Titel, Beschreibung, Priorität, Status, Kategorie)
- **Click-through:** Link zur Quell-Entität (Task-Detailseite, Phasen-Historie, Tank-Seite)
- **Drag & Drop:** Deaktiviert (Events werden über ihre Quell-Module verwaltet)

**Feed-Management-Dialog:**

```
┌─────────────────────────────────────────────┐
│  Kalender-Feeds verwalten                   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ 📅 Mein Hauptkalender              │   │
│  │ Alle Kategorien · Alle Standorte    │   │
│  │ webcal://host/api/v1/calendar/      │   │
│  │   feeds/abc123/feed.ics?token=...   │   │
│  │ [📋 URL kopieren] [✏️ Bearbeiten]   │   │
│  │ [🔄 Token erneuern] [🗑️ Löschen]   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ 📅 Zelt 1 — Nur Kritisch           │   │
│  │ Alle Kategorien · Location: Zelt 1  │   │
│  │ Priorität: critical, high           │   │
│  │ webcal://host/api/v1/calendar/      │   │
│  │   feeds/def456/feed.ics?token=...   │   │
│  │ [📋 URL kopieren] [✏️ Bearbeiten]   │   │
│  │ [🔄 Token erneuern] [🗑️ Löschen]   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [+ Neuen Feed erstellen]                   │
│                                        [OK] │
└─────────────────────────────────────────────┘
```

**Responsive Verhalten:**
- **Desktop (≥1024px):** Kalender-Grid mit Filter-Sidebar
- **Tablet (768–1023px):** Kalender-Grid, Filter als Drawer
- **Mobile (<768px):** Agenda-Listenansicht als Default, Filter als Bottom-Sheet

**Redux Slice:**
- `calendarSlice`: Events, aktive Filter, ausgewählter Zeitraum, Ansichtsmodus
- `calendarFeedsSlice`: Feed-Liste, CRUD-Status

**i18n-Keys (DE/EN):**
- `calendar.title` / `calendar.title`
- `calendar.month` / `calendar.month`
- `calendar.week` / `calendar.week`
- `calendar.day` / `calendar.day`
- `calendar.agenda` / `calendar.agenda`
- `calendar.filter.*` / `calendar.filter.*`
- `calendar.feeds.*` / `calendar.feeds.*`
- `calendar.categories.*` für alle `CalendarEventCategory`-Werte
- `calendar.sowingCalendar.*` / `calendar.sowingCalendar.*` (Aussaatkalender)
- `calendar.sowingCalendar.flowering` / `calendar.sowingCalendar.flowering` (Blüte-Phase für Zierpflanzen)
- `calendar.sowingCalendar.annualRepeat` / `calendar.sowingCalendar.annualRepeat` (Jährlich wiederkehrend)
- `calendar.sowingCalendar.yearComparison` / `calendar.sowingCalendar.yearComparison` (Jahresvergleich)
- `calendar.seasonOverview.*` / `calendar.seasonOverview.*` (Saisonübersicht)
- `calendar.frost.*` / `calendar.frost.*` (Frosttermin-Labels)

<!-- Quelle: Outdoor-Garden-Planner Review G-001, G-005 -->
### 3.8 Aussaatkalender-Modus (Sowing Calendar View)

Der Aussaatkalender ist eine spezialisierte Ansicht, die den gesamten Anbauzyklus pro Pflanze als horizontale Zeitbalken darstellt. Er ergänzt die bestehenden Kalender-Ansichten (Monat/Woche/Tag/Agenda) als fünfter Ansichtsmodus.

**Darstellung:**
- **X-Achse:** Monate (Januar–Dezember)
- **Y-Achse:** Pflanzen (sortiert nach Aussaat-Zeitpunkt)
- **Balken pro Pflanze:**
  - Voranzucht (Indoor): Berechnet aus `sowing_indoor_weeks_before_last_frost` (REQ-001) rückwärts vom konfigurierten letzten Frosttermin
  - Direktsaat/Auspflanzen: Berechnet aus `sowing_outdoor_after_last_frost_days` oder `direct_sow_months`
  - Wachstum: Zeitraum zwischen Auspflanzen und Ernte
  - Ernte: Aus `harvest_months` (REQ-001)

**Farbkodierung der Balken:**

| Phase | Farbe | Hex | Pflanzentyp |
|-------|-------|-----|-------------|
| Voranzucht (Indoor) | Gelb | `#FDD835` | Alle |
| Direktsaat/Auspflanzen | Grün | `#66BB6A` | Alle |
| Wachstum | Blau | `#42A5F5` | Alle |
| Ernte | Orange | `#FFA726` | Nutzpflanzen (`allows_harvest: true`) |
| Blüte | Pink | `#EC407A` | Zierpflanzen (`traits: ['ornamental']`, `allows_harvest: false`) |

<!-- Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03 -->
> **Hinweis Zierpflanzen:** Für Zierpflanzen ohne Erntephase (REQ-003: `allows_harvest: false`) wird statt des orangenen Ernte-Balkens ein pinker Blüte-Balken angezeigt. Die Blütezeit wird aus `bloom_months` (REQ-001 Species) oder `harvest_months` (Fallback) gelesen. Pflanzen mit `traits: ['ornamental']` werden automatisch der Kategorie "Blumen" zugeordnet.

**Frosttermin-Konfiguration (auf Site-Level, Verweis auf REQ-002):**

Die Frosttermine werden auf der `:Site`-Node in REQ-002 konfiguriert und hier referenziert:

- `last_frost_date_avg: Optional[date]` (Durchschnittlicher letzter Frost, z.B. "2026-05-15")
- `first_frost_date_avg: Optional[date]` (Durchschnittlicher erster Frost, z.B. "2026-10-05")
- `eisheilige_date: Optional[date]` (Eisheilige, Default: "YYYY-05-15" — konfigurierbar für Süddeutschland/Alpenregion)

> **Hinweis:** Diese Felder gehören auf die `:Site`-Node in REQ-002. REQ-015 liest sie nur.

**Defaults basierend auf Klimazone (USDA Hardiness Zone):**

| Klimazone | Letzter Frost | Erster Frost |
|-----------|---------------|-------------|
| USDA 6b | ~15. Mai | ~5. Oktober |
| USDA 7a | ~1. Mai | ~20. Oktober |
| USDA 7b | ~15. April | ~1. November |
| USDA 8a | ~1. April | ~15. November |

**Eisheiligen-Markierung:**
Eine vertikale Linie bei den Eisheiligen (11.–15. Mai, konfigurierbar) markiert den sicheren Zeitpunkt für frostempfindliche Pflanzen. Pflanzen mit `frost_sensitivity: 'tender'` werden erst NACH dieser Linie zum Auspflanzen vorgeschlagen.

**Beispiel-Darstellung (vereinfacht):**
```
Pflanze          Jan  Feb  Mär  Apr  Mai  Jun  Jul  Aug  Sep  Okt  Nov  Dez
                                       |← Eisheilige
── Gemüse ──
Paprika          ·····🟡🟡🟡🟡·····🟢🟢🔵🔵🔵🔵🟠🟠🟠·····
Tomate           ··········🟡🟡🟡···🟢🔵🔵🔵🔵🟠🟠🟠🟠····
Möhre            ·············🟢🟢🟢🔵🔵🔵🔵🟠🟠🟠🟠·······
Salat            ········🟢🟢🟢🔵🟠🟢🟢🔵🟠🟢🟢🔵🟠·······  (Sukzession!)
Radieschen       ·······🟢🔵🟠🟢🔵🟠🟢🔵🟠🟢🔵🟠···········
Grünkohl         ···············🟡🟡🟢🟢🔵🔵🔵🔵🔵🟠🟠🟠🟠  (Wintergemüse)
── Blumen ──
Stiefmütterchen  🟡🟡🟡🟡🟡·····🟢🟢🩷🩷🩷🩷·······🩷🩷····  (12 Wo. Voranzucht, 2 Blühphasen)
Petunie          ·····🟡🟡🟡🟡···🟢🟢🔵🩷🩷🩷🩷🩷🩷🩷······  (frostempfindlich)
Tagetes          ··········🟡🟡···🟢🟢🔵🩷🩷🩷🩷🩷🩷········
```
Legende: 🟡 Voranzucht | 🟢 Direktsaat/Auspflanzen | 🔵 Wachstum | 🟠 Ernte | 🩷 Blüte

**Interaktion:**
- Klick auf einen Balken öffnet Detail-Panel mit konkreten Terminen
- Hover zeigt Tooltip: "Tomate San Marzano: Voranzucht ab 1. März, Auspflanzen ab 15. Mai, Ernte Juli–Oktober"
- Filter: Nur meine geplanten Pflanzen / Alle verfügbaren Pflanzen
- Druckversion für Aushang im Gewächshaus/Gartenhäuschen

**Kalenderseite — Aussaatkalender-Tab (`/calendar?view=sowing`):**

```
┌──────────────────────────────────────────────────────────────────┐
│  Kalender  [Monat] [Woche] [Tag] [Agenda] [🌱 Aussaat] [📊 Saison] │
├──────────┬───────────────────────────────────────────────────────┤
│ Standort │  Aussaatkalender 2026                                │
│ [Garten▾]│  Letzter Frost: 15. Mai · Eisheilige: 11.–15. Mai   │
│          │                                                       │
│ Filter   │  Pflanze    J  F  M  A  M  J  J  A  S  O  N  D      │
│ □ Geplant│             ─────────────|──────────────────          │
│ □ Alle   │  Paprika    ···🟡🟡🟡🟡··🟢🟢🔵🔵🔵🔵🟠🟠🟠···  │
│          │  Tomate     ·····🟡🟡🟡··🟢🔵🔵🔵🔵🟠🟠🟠🟠··   │
│ Kategorie│  Möhre      ········🟢🟢🟢🔵🔵🔵🔵🟠🟠🟠🟠···   │
│ □ Gemüse │  Salat      ·····🟢🟢🟢🔵🟠🟢🟢🔵🟠🟢🟢🔵🟠·   │
│ □ Kräuter│  Radieschen ····🟢🔵🟠🟢🔵🟠🟢🔵🟠🟢🔵🟠·····   │
│ □ Blumen │  Grünkohl   ···········🟡🟡🟢🟢🔵🔵🔵🔵🔵🟠🟠🟠 │
│          │  ── Blumen ──                                        │
│ Zyklus   │  Stiefm.    🟡🟡🟡🟡🟡🟢🟢🩷🩷🩷🩷·····🩷🩷···  │
│ □ Jährl. │  Petunie    ·····🟡🟡🟡·🟢🟢🔵🩷🩷🩷🩷🩷🩷····   │
│ □ Einmal │                                                      │
│          │                                                       │
│ [🖨 Druck]│  Legende: 🟡 Voranzucht 🟢 Auspflanzen 🔵 Wachstum 🟠 Ernte│
└──────────┴───────────────────────────────────────────────────────┘
```

**SowingCalendarEngine:**

```python
from datetime import date, timedelta
from typing import Optional

from pydantic import BaseModel, Field


class FrostConfig(BaseModel):
    """Frosttermin-Konfiguration einer Site."""
    last_frost_date_avg: Optional[date] = None
    first_frost_date_avg: Optional[date] = None
    eisheilige_date: Optional[date] = None  # Default: YYYY-05-15


class SowingBar(BaseModel):
    """Einzelner Zeitbalken im Aussaatkalender."""
    phase: str  # "indoor_sowing" | "outdoor_planting" | "growth" | "harvest" | "flowering"
    start_date: date
    end_date: date
    color: str


class SowingCalendarEntry(BaseModel):
    """Ein Eintrag im Aussaatkalender (eine Pflanze/Sorte)."""
    species_key: str
    species_name: str
    cultivar_key: Optional[str] = None
    cultivar_name: Optional[str] = None
    frost_sensitive: bool = False
    is_ornamental: bool = False  # True wenn traits enthält 'ornamental'
    annual_repeat: bool = False  # True wenn jährlich wiederkehrend (REQ-013)
    bars: list[SowingBar] = Field(default_factory=list)


class SowingCalendarEngine:
    """Berechnet Aussaat-Zeitbalken basierend auf Pflanzen-Stammdaten
    und Frosttermin-Konfiguration.

    Liest Stammdaten aus REQ-001 (Species/Cultivar):
    - sowing_indoor_weeks_before_last_frost
    - sowing_outdoor_after_last_frost_days
    - direct_sow_months
    - harvest_months (Nutzpflanzen)
    - bloom_months (Zierpflanzen — bevorzugt bei ornamental trait)
    - frost_sensitivity
    - traits (zur Erkennung von Zierpflanzen: 'ornamental')

    Liest Frosttermine aus REQ-002 (Site):
    - last_frost_date_avg
    - first_frost_date_avg
    - eisheilige_date

    Liest Pflanzdurchlauf-Daten aus REQ-013:
    - annual_repeat (jährlich wiederkehrend)
    - repeat_month (Startmonat für Voranzucht)
    - previous_run_key (Vorjahres-Vergleich)
    """

    PHASE_COLORS = {
        "indoor_sowing": "#FDD835",    # Gelb
        "outdoor_planting": "#66BB6A",  # Grün
        "growth": "#42A5F5",            # Blau
        "harvest": "#FFA726",           # Orange — Nutzpflanzen
        "flowering": "#EC407A",         # Pink — Zierpflanzen
    }

    def calculate_bars(
        self,
        species: dict,
        frost_config: FrostConfig,
        year: int,
    ) -> list[SowingBar]:
        """Berechnet die Zeitbalken für eine Pflanze/Sorte.

        Args:
            species: Stammdaten-Dict mit Aussaat-Feldern aus REQ-001
            frost_config: Frosttermin-Konfiguration der Site
            year: Bezugsjahr für die Berechnung

        Returns:
            Liste von SowingBar mit Phase, Start/End-Datum und Farbe
        """
        bars: list[SowingBar] = []
        last_frost = frost_config.last_frost_date_avg or date(year, 5, 15)
        eisheilige = frost_config.eisheilige_date or date(year, 5, 15)

        # 1. Voranzucht (Indoor)
        weeks_before = species.get("sowing_indoor_weeks_before_last_frost")
        if weeks_before:
            indoor_start = last_frost - timedelta(weeks=weeks_before)
            indoor_end = last_frost - timedelta(days=1)
            bars.append(SowingBar(
                phase="indoor_sowing",
                start_date=indoor_start,
                end_date=indoor_end,
                color=self.PHASE_COLORS["indoor_sowing"],
            ))

        # 2. Auspflanzen / Direktsaat
        days_after = species.get("sowing_outdoor_after_last_frost_days", 0)
        frost_sensitive = species.get("frost_sensitivity") == "tender"
        if frost_sensitive:
            outdoor_start = max(
                last_frost + timedelta(days=days_after),
                eisheilige + timedelta(days=1),
            )
        else:
            outdoor_start = last_frost + timedelta(days=days_after)

        # Auspflanzen-Phase: ca. 2 Wochen Eingewöhnung
        outdoor_end = outdoor_start + timedelta(days=14)
        bars.append(SowingBar(
            phase="outdoor_planting",
            start_date=outdoor_start,
            end_date=outdoor_end,
            color=self.PHASE_COLORS["outdoor_planting"],
        ))

        # 3. Wachstum + 4. Ernte ODER Blüte
        # Zierpflanzen (ornamental trait, allows_harvest: false):
        #   → bloom_months als Blütephase (pink), kein Ernte-Balken
        # Nutzpflanzen (allows_harvest: true):
        #   → harvest_months als Erntephase (orange)
        is_ornamental = "ornamental" in species.get("traits", [])
        bloom_months = species.get("bloom_months", [])
        harvest_months = species.get("harvest_months", [])

        # Für Zierpflanzen: bloom_months bevorzugen, harvest_months als Fallback
        target_months = bloom_months if (is_ornamental and bloom_months) else harvest_months
        target_phase = "flowering" if is_ornamental else "harvest"

        if target_months:
            # AB-010: Lücken in bloom_months erkennen und getrennte Balken zeichnen
            # z.B. Viola bloom_months=[3,4,5,6,9,10] → Perioden [3-6] und [9-10]
            periods = self._split_into_periods(sorted(target_months))

            growth_start = outdoor_end + timedelta(days=1)
            first_period_start = date(year, periods[0][0], 1)

            if growth_start < first_period_start:
                bars.append(SowingBar(
                    phase="growth",
                    start_date=growth_start,
                    end_date=first_period_start - timedelta(days=1),
                    color=self.PHASE_COLORS["growth"],
                ))

            for period_start_month, period_end_month in periods:
                period_start = date(year, period_start_month, 1)
                if period_end_month == 12:
                    period_end = date(year, 12, 31)
                else:
                    period_end = date(year, period_end_month + 1, 1) - timedelta(days=1)
                bars.append(SowingBar(
                    phase=target_phase,
                    start_date=period_start,
                    end_date=period_end,
                    color=self.PHASE_COLORS[target_phase],
                ))

        return bars

    @staticmethod
    def _split_into_periods(months: list[int]) -> list[tuple[int, int]]:
        """Teilt eine sortierte Monatsliste in zusammenhängende Perioden.

        Erkennt Lücken und erzeugt getrennte (start, end)-Tupel.
        z.B. [3,4,5,6,9,10] → [(3,6), (9,10)]
             [5,6,7,8,9,10] → [(5,10)]
        """
        if not months:
            return []
        periods = []
        start = months[0]
        prev = months[0]
        for m in months[1:]:
            if m != prev + 1:
                periods.append((start, prev))
                start = m
            prev = m
        periods.append((start, prev))
        return periods

    def build_calendar(
        self,
        species_list: list[dict],
        frost_config: FrostConfig,
        year: int,
    ) -> list[SowingCalendarEntry]:
        """Erstellt den kompletten Aussaatkalender für alle Pflanzen.

        Sortiert nach frühestem Aussaat-Zeitpunkt.
        """
        entries = []
        for sp in species_list:
            bars = self.calculate_bars(sp, frost_config, year)
            entries.append(SowingCalendarEntry(
                species_key=sp["_key"],
                species_name=sp["common_name"],
                cultivar_key=sp.get("cultivar_key"),
                cultivar_name=sp.get("cultivar_name"),
                frost_sensitive=sp.get("frost_sensitivity") == "tender",
                is_ornamental="ornamental" in sp.get("traits", []),
                annual_repeat=sp.get("annual_repeat", False),
                bars=bars,
            ))
        # Sortierung: frühester Balken-Start zuerst
        entries.sort(
            key=lambda e: min(b.start_date for b in e.bars) if e.bars else date.max
        )
        return entries
```

<!-- Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03 -->
#### 3.8.1 Jährlich wiederkehrende Pflanzen im Aussaatkalender

Für Zierpflanzen und Einjährige, die jedes Jahr neu vorgezogen werden (REQ-013: `annual_repeat: true`), bietet der Aussaatkalender zusätzliche Funktionen:

**Automatische Voranzucht-Erinnerung:**
- Wenn ein `PlantingRun` mit `annual_repeat: true` und `repeat_month` existiert (REQ-013), wird die Pflanze automatisch im Aussaatkalender des Folgejahres angezeigt
- Der Voranzucht-Balken berechnet sich aus `sowing_indoor_weeks_before_last_frost` (REQ-001) und dem konfigurierten Frosttermin (REQ-002)
- Beispiel: Stiefmütterchen mit `repeat_month: 2` und `sowing_indoor_weeks_before_last_frost: 8` → Voranzucht-Balken ab Mitte Februar

**Jahresvergleich (optional):**
- Über `previous_run_key` (REQ-013) kann der Verlauf des Vorjahres als Referenz eingeblendet werden
- Darstellung: dünne, halbtransparente Linie unter dem aktuellen Balken
- Zeigt: tatsächlicher Voranzucht-Start, Auspflanz-Datum, Blüte-Beginn des Vorjahres

**Kategorie-Filter "Jährlich wiederkehrend":**
- Neuer Filter `□ Jährlich` im Aussaatkalender zeigt nur Pflanzen mit `annual_repeat: true`
- Kombinierbar mit bestehenden Filtern (Gemüse, Kräuter, Blumen)

<!-- Quelle: Outdoor-Garden-Planner Review G-001, G-005 -->
### 3.9 Saisonübersicht-Modus (Monthly Overview)

Ergänzend zum detaillierten Aussaatkalender eine kompakte Monatsübersicht als sechster Ansichtsmodus:

**Darstellung:**
- **12 Monatskarten** (Grid-Layout, 3x4 oder 4x3)
- Jede Karte zeigt:
  - Anzahl fälliger Tasks (aus REQ-006)
  - Anzahl zu säender/pflanzender Pflanzen (aus Aussaatkalender-Daten)
  - Anzahl erwarteter Ernten (aus Aussaatkalender-Daten)
  - Wetter-Trend (wenn REQ-005 Wetter-Integration aktiv)
  - Top-3 wichtigste Aufgaben des Monats

**Aktueller-Monat-Highlight:** Der aktuelle Monat ist visuell hervorgehoben und expandiert (mehr Details sichtbar).

**Kalenderseite — Saisonübersicht-Tab (`/calendar?view=season`):**

```
┌──────────────────────────────────────────────────────────────────┐
│  Kalender  [Monat] [Woche] [Tag] [Agenda] [🌱 Aussaat] [📊 Saison] │
├──────────────────────────────────────────────────────────────────┤
│  Saisonübersicht 2026 — Standort: Garten                        │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Januar   │  │ Februar  │  │ März     │  │ April    │        │
│  │ 0 Saat   │  │ 0 Saat   │  │ 3 Saat   │  │ 5 Saat   │        │
│  │ 0 Ernte  │  │ 0 Ernte  │  │ 0 Ernte  │  │ 0 Ernte  │        │
│  │ 2 Tasks  │  │ 1 Task   │  │ 8 Tasks  │  │ 12 Tasks │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Mai      │  │ Juni     │  │ Juli     │  │ August   │        │
│  │ 8 Saat   │  │ 2 Saat   │  │ 0 Saat   │  │ 0 Saat   │        │
│  │ 2 Ernte  │  │ 5 Ernte  │  │ 8 Ernte  │  │ 10 Ernte │        │
│  │ 18 Tasks │  │ 15 Tasks │  │ 12 Tasks │  │ 14 Tasks │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │September │  │ Oktober  │  │ November │  │ Dezember │        │
│  │ 0 Saat   │  │ 0 Saat   │  │ 0 Saat   │  │ 0 Saat   │        │
│  │ 12 Ernte │  │ 6 Ernte  │  │ 2 Ernte  │  │ 0 Ernte  │        │
│  │ 10 Tasks │  │ 8 Tasks  │  │ 3 Tasks  │  │ 1 Task   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  ██ = Aktueller Monat (expandiert mit Top-3 Aufgaben)           │
└──────────────────────────────────────────────────────────────────┘
```

**Klick auf Monatskarte:** Wechselt zur Monatsansicht des gewählten Monats (bestehende Ansicht aus §3.7).

**SeasonOverviewEngine:**

```python
from datetime import date

from pydantic import BaseModel, Field


class MonthSummary(BaseModel):
    """Zusammenfassung eines Monats für die Saisonübersicht."""
    month: int  # 1–12
    month_name: str
    sowing_count: int = 0       # Pflanzen, die in diesem Monat gesät/gepflanzt werden
    harvest_count: int = 0      # Pflanzen, die in diesem Monat geerntet werden
    task_count: int = 0         # Fällige Tasks (aus REQ-006)
    top_tasks: list[dict] = Field(default_factory=list)  # Top-3 Tasks des Monats
    is_current: bool = False    # Aktueller Monat?


class SeasonOverview(BaseModel):
    """Jahres-Saisonübersicht mit 12 Monatskarten."""
    year: int
    site_key: str
    site_name: str
    months: list[MonthSummary] = Field(default_factory=list)


class SeasonOverviewEngine:
    """Aggregiert Saisonübersicht-Daten aus Aussaatkalender und Tasks.

    Kombiniert:
    - SowingCalendarEngine-Ergebnisse für Saat-/Erntezahlen
    - CalendarAggregationEngine-Ergebnisse für Task-Zahlen
    """

    MONTH_NAMES_DE = [
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ]

    def build_overview(
        self,
        sowing_entries: list,
        task_events: list,
        site_key: str,
        site_name: str,
        year: int,
    ) -> SeasonOverview:
        """Erstellt die Saisonübersicht aus Aussaatkalender-Einträgen und Tasks.

        Args:
            sowing_entries: Liste von SowingCalendarEntry
            task_events: Liste von CalendarEvent (Tasks für das gesamte Jahr)
            site_key: Key der Site
            site_name: Name der Site
            year: Bezugsjahr
        """
        today = date.today()
        months = []

        for m in range(1, 13):
            # Saat-/Pflanz-Zählung: Pflanzen mit outdoor_planting-Balken in diesem Monat
            sowing_count = sum(
                1 for entry in sowing_entries
                for bar in entry.bars
                if bar.phase in ("indoor_sowing", "outdoor_planting")
                and bar.start_date.month <= m <= bar.end_date.month
            )

            # Ernte-Zählung: Pflanzen mit harvest-Balken in diesem Monat
            harvest_count = sum(
                1 for entry in sowing_entries
                for bar in entry.bars
                if bar.phase == "harvest"
                and bar.start_date.month <= m <= bar.end_date.month
            )

            # Task-Zählung
            month_tasks = [
                e for e in task_events
                if e.start.month == m and e.start.year == year
            ]
            task_count = len(month_tasks)

            # Top-3 nach Priorität
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            sorted_tasks = sorted(
                month_tasks,
                key=lambda t: priority_order.get(t.priority, 2),
            )
            top_tasks = [
                {"title": t.title, "priority": t.priority, "date": t.start.isoformat()}
                for t in sorted_tasks[:3]
            ]

            months.append(MonthSummary(
                month=m,
                month_name=self.MONTH_NAMES_DE[m - 1],
                sowing_count=sowing_count,
                harvest_count=harvest_count,
                task_count=task_count,
                top_tasks=top_tasks,
                is_current=(today.year == year and today.month == m),
            ))

        return SeasonOverview(
            year=year,
            site_key=site_key,
            site_name=site_name,
            months=months,
        )
```

## 4. API-Endpunkte

### 4.1 Kalender-Events (Aggregation)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/calendar/events` | Aggregierte Events mit Filtern | Mitglied |

**Query-Parameter:**

| Parameter | Typ | Pflicht | Beschreibung |
|-----------|-----|---------|-------------|
| `start` | `date` | ✅ | Beginn des Zeitraums (ISO 8601) |
| `end` | `date` | ✅ | Ende des Zeitraums (ISO 8601) |
| `category` | `str[]` | ❌ | Filter nach Kategorien (mehrfach möglich) |
| `location_id` | `str` | ❌ | Filter nach Location |
| `plant_id` | `str` | ❌ | Filter nach Pflanze |
| `priority` | `str` | ❌ | Filter nach Priorität |
| `status` | `str[]` | ❌ | Filter nach Status (mehrfach möglich) |
| `include_timeline` | `bool` | ❌ | Timeline-Events einschließen (Default: false) |

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "task_abc123",
      "source": "task",
      "source_id": "abc123",
      "title": "Topping — Northern Lights #3",
      "description": "Haupttrieb auf 5. Node kappen",
      "category": "training",
      "start": "2026-03-15T10:00:00",
      "end": "2026-03-15T10:30:00",
      "all_day": false,
      "priority": "high",
      "status": "pending",
      "location_id": "loc_zelt1",
      "location_name": "Zelt 1",
      "plant_id": "plant_nl3",
      "estimated_duration_minutes": 30,
      "color": "#4CAF50"
    }
  ],
  "total": 42
}
```

### 4.2 iCal-Feed (Read-Only Export)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/calendar/feeds/{feed_id}/feed.ics` | iCal-Feed abrufen | Nein (Feed-Token) |

**Query-Parameter:**

| Parameter | Typ | Pflicht | Beschreibung |
|-----------|-----|---------|-------------|
| `token` | `str` | ✅ | Authentifizierungs-Token des Feeds |

**Response:** `200 OK` (Content-Type: `text/calendar; charset=utf-8`)
```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Kamerplanter//Calendar//DE
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Mein Hauptkalender
X-WR-TIMEZONE:Europe/Berlin
BEGIN:VEVENT
UID:task-abc123@kamerplanter
DTSTAMP:20260315T080000Z
DTSTART:20260315T100000
DTEND:20260315T103000
SUMMARY:Topping — Northern Lights #3
DESCRIPTION:Haupttrieb auf 5. Node kappen
CATEGORIES:TRAINING
PRIORITY:3
STATUS:TENTATIVE
COLOR:#4CAF50
X-APPLE-CALENDAR-COLOR:#4CAF50
LOCATION:Zelt 1
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:Topping — Northern Lights #3
TRIGGER:-PT45M
END:VALARM
END:VEVENT
END:VCALENDAR
```

**webcal:// URL für Kalender-Abonnement:**
```
webcal://kamerplanter.local/api/v1/calendar/feeds/{feed_id}/feed.ics?token={token}
```

**Einrichtung in externen Kalender-Apps:**
- **Thunderbird:** Neuer Kalender → Im Netzwerk → URL einfügen (webcal:// wird automatisch erkannt)
- **Apple Calendar:** Kalender → Abonnements → URL einfügen
- **Google Calendar:** Andere Kalender → Per URL → URL einfügen (nur https://, webcal:// manuell ersetzen)

<!-- Quelle: Smart-Home-HA-Integration Review A-008 -->
**Einrichtung in Home Assistant:**

- **HA Custom Integration (`kamerplanter-ha`):** Der `CalendarCoordinator` pollt den iCal-Feed-Endpoint (`GET /api/v1/calendar/feeds/{feed_id}/feed.ics?token={token}`) und erstellt eine native HA `calendar`-Entity. Konfiguration erfolgt automatisch im Config Flow (Feed-Auswahl in Step 4).

- **HA Generic Calendar Platform (ohne Custom Integration):** Alternativ kann der iCal-Feed direkt in der HA `configuration.yaml` eingebunden werden:

```yaml
# configuration.yaml
calendar:
  - platform: generic
    name: "Kamerplanter Aufgaben"
    url: "webcal://kamerplanter.local/api/v1/calendar/feeds/{feed_id}/feed.ics?token={token}"
```

**HA Calendar-Entity Attribute:**

| Attribut | Kamerplanter-Quelle | Beschreibung |
|----------|---------------------|-------------|
| `event.start` | `DTSTART` (iCal) | Beginn des Kalender-Events |
| `event.end` | `DTEND` (iCal) | Ende des Kalender-Events |
| `event.summary` | `SUMMARY` (iCal) | Event-Titel (z.B. "FEEDING — Northern Lights #3") |
| `event.description` | `DESCRIPTION` (iCal) | Details (Düngerrezept, Aufgabenbeschreibung) |

**HA-Automation-Beispiel — Kalender-Event als Trigger:**

```yaml
# Trigger: Kamerplanter-Calendar-Event startet → Aktion auslösen
alias: "KP: Düngetermin → Pumpe einschalten"
description: "Bei FEEDING-Event im Kamerplanter-Kalender die Dosierpumpe starten"
trigger:
  - platform: calendar
    entity_id: calendar.kamerplanter_aufgaben
    event: start
    offset: "0:0:0"
condition:
  - condition: template
    value_template: "{{ 'FEEDING' in trigger.calendar_event.summary }}"
action:
  - service: switch.turn_on
    target:
      entity_id: switch.dosierpumpe_zelt1
  - delay: "00:00:30"
  - service: switch.turn_off
    target:
      entity_id: switch.dosierpumpe_zelt1
mode: single
```

### 4.3 Feed-Management (CRUD)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `POST` | `/api/v1/calendar/feeds` | Neuen Feed erstellen | Mitglied |
| `GET` | `/api/v1/calendar/feeds` | Alle Feeds auflisten | Mitglied |
| `GET` | `/api/v1/calendar/feeds/{feed_id}` | Feed-Details abrufen | Mitglied |
| `PUT` | `/api/v1/calendar/feeds/{feed_id}` | Feed aktualisieren | Mitglied |
| `DELETE` | `/api/v1/calendar/feeds/{feed_id}` | Feed löschen | Mitglied |
| `POST` | `/api/v1/calendar/feeds/{feed_id}/regenerate-token` | Token erneuern | Mitglied |

**POST /api/v1/calendar/feeds — Request:**
```json
{
  "name": "Zelt 1 — Nur Kritisch",
  "filters": {
    "categories": [],
    "location_ids": ["loc_zelt1"],
    "priorities": ["critical", "high"],
    "statuses": []
  },
  "include_timeline": false,
  "alarm_enabled": true
}
```

**Response:** `201 Created`
```json
{
  "_key": "feed_abc123",
  "name": "Zelt 1 — Nur Kritisch",
  "token": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "filters": {
    "categories": [],
    "location_ids": ["loc_zelt1"],
    "priorities": ["critical", "high"],
    "statuses": []
  },
  "include_timeline": false,
  "alarm_enabled": true,
  "created_at": "2026-02-26T14:00:00",
  "updated_at": "2026-02-26T14:00:00",
  "last_accessed_at": null,
  "webcal_url": "webcal://kamerplanter.local/api/v1/calendar/feeds/feed_abc123/feed.ics?token=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
}
```

**POST /api/v1/calendar/feeds/{feed_id}/regenerate-token — Response:** `200 OK`
```json
{
  "_key": "feed_abc123",
  "token": "new_token_here_replacing_old_one",
  "webcal_url": "webcal://kamerplanter.local/api/v1/calendar/feeds/feed_abc123/feed.ics?token=new_token_here_replacing_old_one"
}
```

> **Sicherheitshinweis:** Nach Token-Rotation müssen alle externen Kalender-Apps die URL aktualisieren. Das alte Token wird sofort ungültig.

<!-- Quelle: Outdoor-Garden-Planner Review G-001, G-005 -->
### 4.4 Aussaatkalender (Sowing Calendar)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/calendar/sowing` | Aussaatkalender für ein Jahr und eine Site | Mitglied |

**Query-Parameter:**

| Parameter | Typ | Pflicht | Beschreibung |
|-----------|-----|---------|-------------|
| `year` | `int` | ❌ | Bezugsjahr (Default: aktuelles Jahr) |
| `site_id` | `str` | ✅ | Site-ID für Frosttermin-Lookup |
| `planned_only` | `bool` | ❌ | Nur geplante Pflanzen (Default: false) |
| `category` | `str` | ❌ | Filter: `vegetables`, `herbs`, `flowers` (Default: alle) |
| `annual_only` | `bool` | ❌ | Nur jährlich wiederkehrende Pflanzen (Default: false) |

**Response:** `200 OK`
```json
{
  "year": 2026,
  "site_id": "site_garten1",
  "frost_config": {
    "last_frost_date_avg": "2026-05-15",
    "first_frost_date_avg": "2026-10-05",
    "eisheilige_date": "2026-05-15"
  },
  "entries": [
    {
      "species_key": "sp_paprika",
      "species_name": "Paprika",
      "cultivar_key": "cv_california_wonder",
      "cultivar_name": "California Wonder",
      "frost_sensitive": true,
      "is_ornamental": false,
      "annual_repeat": false,
      "bars": [
        {
          "phase": "indoor_sowing",
          "start_date": "2026-02-15",
          "end_date": "2026-04-30",
          "color": "#FDD835"
        },
        {
          "phase": "outdoor_planting",
          "start_date": "2026-05-16",
          "end_date": "2026-05-30",
          "color": "#66BB6A"
        },
        {
          "phase": "growth",
          "start_date": "2026-05-31",
          "end_date": "2026-07-14",
          "color": "#42A5F5"
        },
        {
          "phase": "harvest",
          "start_date": "2026-07-15",
          "end_date": "2026-09-30",
          "color": "#FFA726"
        }
      ]
    },
    {
      "species_key": "sp_viola_wittrockiana",
      "species_name": "Stiefmütterchen",
      "cultivar_key": null,
      "cultivar_name": null,
      "frost_sensitive": false,
      "is_ornamental": true,
      "annual_repeat": true,
      "bars": [
        {
          "phase": "indoor_sowing",
          "start_date": "2026-02-15",
          "end_date": "2026-03-14",
          "color": "#FDD835"
        },
        {
          "phase": "outdoor_planting",
          "start_date": "2026-03-15",
          "end_date": "2026-03-29",
          "color": "#66BB6A"
        },
        {
          "phase": "flowering",
          "start_date": "2026-03-01",
          "end_date": "2026-06-30",
          "color": "#EC407A"
        },
        {
          "phase": "flowering",
          "start_date": "2026-09-01",
          "end_date": "2026-10-31",
          "color": "#EC407A"
        }
      ]
    }
  ],
  "total": 12
}
```

### 4.5 Saisonübersicht (Season Overview)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/calendar/season-overview` | Saisonübersicht (12 Monatskarten) | Mitglied |

**Query-Parameter:**

| Parameter | Typ | Pflicht | Beschreibung |
|-----------|-----|---------|-------------|
| `year` | `int` | ❌ | Bezugsjahr (Default: aktuelles Jahr) |
| `site_id` | `str` | ✅ | Site-ID für Standort-Kontext |

**Response:** `200 OK`
```json
{
  "year": 2026,
  "site_key": "site_garten1",
  "site_name": "Garten Süd",
  "months": [
    {
      "month": 3,
      "month_name": "März",
      "sowing_count": 3,
      "harvest_count": 0,
      "task_count": 8,
      "top_tasks": [
        {"title": "Paprika Voranzucht starten", "priority": "high", "date": "2026-03-01"},
        {"title": "Tomate Voranzucht starten", "priority": "high", "date": "2026-03-15"},
        {"title": "Kompost umsetzen", "priority": "medium", "date": "2026-03-20"}
      ],
      "is_current": false
    }
  ]
}
```

## 5. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Kalender-Events | Mitglied | Mitglied | Mitglied |
| iCal-Feed (`feed.ics`) | Nein (Feed-Token) | — | — |
| Feed-Verwaltung | Mitglied | Mitglied | Mitglied |
| Aussaatkalender | Mitglied | — | — |
| Saisonübersicht | Mitglied | — | — |

## 6. Abhängigkeiten

### Hard Dependencies (funktional notwendig)

| REQ | Abhängigkeit | Impact |
|-----|-------------|--------|
| REQ-006 | Tasks = primäre Kalender-Datenquelle | **Hoch** — ohne Tasks kein Kalender |

### Read Dependencies (lesender Zugriff auf deren Daten)

| REQ | Zugriff | Beschreibung |
|-----|---------|-------------|
| REQ-001 | `species`, `cultivars` Collections | Aussaat-Stammdaten (sowing_indoor_weeks_before_last_frost, harvest_months, bloom_months, frost_sensitivity, traits) für Aussaatkalender |
| REQ-002 | `locations`, `sites` Collections | Location-Namen für Event-Kontext und Filter; Frosttermin-Konfiguration (last_frost_date_avg, first_frost_date_avg, eisheilige_date) auf Site-Level für Aussaatkalender |
| REQ-003 | `phase_histories` Collection | Phasentransitionen als Timeline-Events |
| REQ-004 | `mixing_results`, `nutrient_plans` | Dünge-Events als Timeline-Kontext |
| REQ-007 | Tasks mit Kategorie `harvest` | Ernte-Tasks im Kalender |
| REQ-008 | Tasks mit Kategorie `post_harvest` | Post-Harvest-Tasks im Kalender |
| REQ-010 | Tasks mit Kategorie `ipm` | IPM-Inspektions-Tasks im Kalender |
| REQ-013 | Tasks via `PlantingRun`, `annual_repeat`, `repeat_month`, `previous_run_key` | Pflanzdurchlauf-bezogene Tasks; jährlich wiederkehrende Pflanzen im Aussaatkalender; Jahresvergleich über previous_run_key |
| REQ-014 | `maintenance_logs`, `tank_fill_events`, `watering_events` | Tank-Events als Timeline |

### Wer liest REQ-015?

| REQ | Nutzung |
|-----|---------|
| REQ-009 | Dashboard könnte Kalender-Widget einbetten |

## 7. Akzeptanzkriterien

### Definition of Done

- [ ] Kalenderansicht zeigt alle Tasks (REQ-006) im gewählten Zeitraum als farbkodierte Events
- [ ] Monats-, Wochen-, Tages- und Agenda-Ansicht funktionieren korrekt
- [ ] Filter nach Kategorie, Location, Pflanze, Priorität und Status funktionieren einzeln und kombiniert
- [ ] Timeline-Toggle blendet vergangene Events (Phasen, Düngungen, Wartungen) ein/aus
- [ ] Click auf Event öffnet Popover mit Details und Link zur Quell-Entität
- [ ] Feed-CRUD (Erstellen, Auflisten, Bearbeiten, Löschen) funktioniert über UI-Dialog
- [ ] Generierter iCal-Feed ist RFC 5545-konform und importierbar in Thunderbird
- [ ] webcal:// URL wird korrekt generiert und kann als Abo hinzugefügt werden
- [ ] Token-Rotation invalidiert alten Token sofort
- [ ] VEVENT enthält SUMMARY, DTSTART/DTEND, CATEGORIES, PRIORITY, STATUS, VALARM
- [ ] Farbkodierung ist konsistent zwischen Web-Kalender und Apple Calendar (X-APPLE-CALENDAR-COLOR)
- [ ] Responsive: Mobile zeigt Agenda-Liste, Desktop zeigt Grid mit Sidebar
- [ ] i18n: Alle Labels in DE und EN vorhanden
- [ ] Performance: Aggregations-Query liefert ≤500 Events in <200ms
- [ ] Keine neue ArangoDB-Collection für Events — nur `calendar_feeds` für Feed-Konfiguration
- [ ] Aussaatkalender zeigt horizontale Zeitbalken pro Pflanze (Voranzucht, Direktsaat, Wachstum, Ernte)
- [ ] Frosttermine (letzter/erster Frost, Eisheilige) sind pro Site konfigurierbar
- [ ] Eisheiligen-Markierung ist als vertikale Linie sichtbar
- [ ] Frostempfindliche Pflanzen (`frost_sensitivity: tender`) werden erst nach Eisheiligen zum Auspflanzen vorgeschlagen
- [ ] Aussaatkalender unterstützt Filter: geplante Pflanzen vs. alle verfügbaren
- [ ] Druckversion des Aussaatkalenders ist abrufbar
- [ ] Saisonübersicht zeigt 12 Monatskarten mit Saat-/Ernte-/Task-Zählern
- [ ] Aktueller Monat ist in der Saisonübersicht visuell hervorgehoben
- [ ] Klick auf Monatskarte wechselt zur Monatsansicht des gewählten Monats
- [ ] Aussaatkalender-API liefert korrekte Zeitbalken basierend auf Frosttermin und Stammdaten
- [ ] Zierpflanzen (`traits: ['ornamental']`) zeigen pinken Blüte-Balken statt orangenem Ernte-Balken
- [ ] Zierpflanzen nutzen `bloom_months` für Blüte-Zeitraum (Fallback: `harvest_months`)
- [ ] Lücken in `bloom_months` werden erkannt und als getrennte Blüte-Balken dargestellt (AB-010: z.B. Viola [3,4,5,6,9,10] → zwei Balken mit Pause Jul/Aug)
- [ ] Kategorie-Filter "Blumen" filtert korrekt auf Pflanzen mit `traits: ['ornamental']`
- [ ] Filter "Jährlich wiederkehrend" zeigt nur Pflanzen mit `annual_repeat: true` (REQ-013)
- [ ] Jährlich wiederkehrende Pflanzen mit `repeat_month` erscheinen automatisch im Aussaatkalender des Folgejahres
- [ ] Jahresvergleich: Vorjahres-Daten werden als halbtransparente Referenzlinie angezeigt (wenn `previous_run_key` gesetzt)

### Testszenarien

**Szenario 1: Monatsansicht mit Events**
```
GIVEN 15 Tasks existieren im März 2026 (verschiedene Kategorien, Prioritäten)
WHEN ich die Kalenderansicht für März 2026 öffne
THEN sehe ich alle 15 Events als farbkodierte Blöcke im Monats-Grid
AND die Farben entsprechen den Kategorie-Zuordnungen
AND kritische Events sind visuell hervorgehoben
```

**Szenario 2: Location-Filterung**
```
GIVEN 10 Tasks existieren, davon 4 für "Zelt 1" und 6 für "Garten"
WHEN ich den Location-Filter auf "Zelt 1" setze
THEN sehe ich nur die 4 Tasks für Zelt 1
AND der Zähler zeigt "4 Events" an
```

**Szenario 3: Thunderbird-Import**
```
GIVEN ein Feed "Mein Kalender" existiert mit Token
WHEN ich die webcal:// URL in Thunderbird als neuen Netzwerk-Kalender eintrage
THEN lädt Thunderbird den Feed erfolgreich
AND alle Events erscheinen mit korrekten Titeln, Zeiten und Kategorien
AND Erinnerungen werden als VALARM-Trigger angezeigt
AND die Kalenderfarbe entspricht X-APPLE-CALENDAR-COLOR (falls unterstützt)
```

**Szenario 4: Timeline-Toggle**
```
GIVEN 5 aktive Tasks UND 3 abgeschlossene Phasentransitionen im Zeitraum
WHEN Timeline deaktiviert ist
THEN sehe ich nur die 5 Tasks
WHEN ich "Timeline anzeigen" aktiviere
THEN sehe ich 8 Events (5 Tasks + 3 Phasentransitionen)
AND die Phasentransitionen sind als violette, abgeschlossene Events dargestellt
```

**Szenario 5: Mobile Agenda-Ansicht**
```
GIVEN 8 Events existieren für die kommende Woche
WHEN ich die Kalenderseite auf einem Smartphone (<768px) öffne
THEN wird die Agenda-Listenansicht angezeigt (nicht das Grid)
AND Events sind chronologisch sortiert mit Datum-Gruppierung
AND jedes Event zeigt Farb-Indikator, Titel, Uhrzeit und Priorität
AND Tap auf Event öffnet Bottom-Sheet mit Details
```

<!-- Quelle: Outdoor-Garden-Planner Review G-001, G-005 -->
**Szenario 6: Aussaatkalender mit Frosttermin**
```
GIVEN eine Site "Garten Süd" hat last_frost_date_avg = 15. Mai
AND Paprika hat sowing_indoor_weeks_before_last_frost = 10, frost_sensitivity = "tender"
AND Möhre hat direct_sow_months = [3,4,5,6,7], frost_sensitivity = "hardy"
WHEN ich den Aussaatkalender für 2026 und Site "Garten Süd" öffne
THEN zeigt Paprika einen gelben Voranzucht-Balken ab ca. Anfang März
AND Paprika zeigt einen grünen Auspflanzen-Balken NACH den Eisheiligen (nach 15. Mai)
AND Möhre zeigt einen grünen Direktsaat-Balken ab März (vor Eisheiligen, da "hardy")
AND eine vertikale Linie markiert die Eisheiligen (11.–15. Mai)
```

**Szenario 7: Aussaatkalender — Filter geplante Pflanzen**
```
GIVEN 20 Pflanzen existieren in den Stammdaten
AND 5 davon sind in einem aktiven Pflanzdurchlauf (REQ-013) für Site "Garten Süd"
WHEN ich den Filter "Nur meine geplanten Pflanzen" aktiviere
THEN sehe ich nur die 5 geplanten Pflanzen im Aussaatkalender
WHEN ich den Filter deaktiviere
THEN sehe ich alle 20 verfügbaren Pflanzen
```

**Szenario 8: Saisonübersicht**
```
GIVEN Aussaatkalender-Daten existieren für 12 Pflanzen im Jahr 2026
AND 45 Tasks existieren verteilt über das Jahr
WHEN ich die Saisonübersicht für 2026 öffne
THEN sehe ich 12 Monatskarten mit je Saat-/Ernte-/Task-Zählern
AND der aktuelle Monat ist visuell hervorgehoben
AND jede Monatskarte zeigt die Top-3 wichtigsten Tasks
WHEN ich auf die Karte "Mai" klicke
THEN wechselt die Ansicht zur Monatsansicht Mai 2026
```

<!-- Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03 -->
**Szenario 10: Aussaatkalender — Zierpflanzen mit Blüte-Balken und Blühpause (AB-010)**
```
GIVEN Stiefmütterchen hat traits = ['ornamental'], bloom_months = [3,4,5,6,9,10]
AND sowing_indoor_weeks_before_last_frost = 12, frost_sensitivity = "hardy"
AND Site "Balkon" hat last_frost_date_avg = 15. Mai
WHEN ich den Aussaatkalender für 2026 und Site "Balkon" öffne
THEN zeigt Stiefmütterchen einen gelben Voranzucht-Balken ab ca. Mitte Februar (12 Wochen vor 15. Mai)
AND einen grünen Auspflanzen-Balken ab ca. Anfang März (hardy → vor Eisheiligen erlaubt)
AND ZWEI getrennte pinke Blüte-Balken: März–Juni UND September–Oktober (Blühpause Jul/Aug)
AND KEINEN durchgehenden Balken von März bis Oktober
AND keinen orangenen Ernte-Balken (da allows_harvest: false)
```

**Szenario 11: Aussaatkalender — Jährlich wiederkehrende Pflanze**
```
GIVEN ein PlantingRun "Stiefmütterchen 2025" existiert mit annual_repeat = true, repeat_month = 2
AND ein abgeschlossener Run "Stiefmütterchen 2024" ist als previous_run_key verknüpft
WHEN ich den Aussaatkalender für 2026 öffne
THEN erscheint Stiefmütterchen automatisch im Kalender (aus annual_repeat)
AND der Voranzucht-Balken startet im Februar (repeat_month = 2)
AND eine halbtransparente Referenzlinie zeigt die Zeitbalken des Vorjahres-Runs
```

**Szenario 12: Aussaatkalender — Kategorie-Filter Blumen**
```
GIVEN 8 Nutzpflanzen und 4 Zierpflanzen (traits: ['ornamental']) existieren
WHEN ich den Kategorie-Filter auf "Blumen" setze
THEN sehe ich nur die 4 Zierpflanzen im Aussaatkalender
AND alle zeigen pinke Blüte-Balken (nicht orangene Ernte-Balken)
WHEN ich zusätzlich "Jährlich wiederkehrend" aktiviere
AND 2 der 4 Zierpflanzen haben annual_repeat = true
THEN sehe ich nur die 2 jährlich wiederkehrenden Zierpflanzen
```

**Szenario 9: Aussaatkalender — Druckversion**
```
GIVEN der Aussaatkalender zeigt 8 Pflanzen mit Zeitbalken
WHEN ich auf "Drucken" klicke
THEN wird eine druckoptimierte Version des Aussaatkalenders generiert
AND die Legende (Voranzucht/Auspflanzen/Wachstum/Ernte) ist auf dem Ausdruck sichtbar
AND die Eisheiligen-Markierung ist auf dem Ausdruck sichtbar
```
