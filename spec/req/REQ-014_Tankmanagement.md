# Spezifikation: REQ-014 - Tankmanagement

```yaml
ID: REQ-014
Titel: Tank-Verwaltung für Nährstofflösungen & Bewässerung
Kategorie: Bewässerung & Düngung
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Celery
Status: Entwurf
Version: 1.0
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich meine Nährstoff-/Gießwasser-Tanks als eigenständige Objekte verwalten — mit Zuordnung zu einem Bereich, lückenloser Pflegehistorie, nachvollziehbarer Befüllungshistorie und automatisierter Aufgabenplanung — damit ich den Überblick über Wasserwechsel, Reinigungen, Düngerzusammensetzungen und Reservoirzustand behalte und die Bewässerung meiner Pflanzen zuverlässig läuft."

**User Story (Befüllungshistorie):** "Als Gärtner möchte ich bei jedem Befüllen meines Tanks dokumentieren, welche Lösung ich in welcher Menge und nach welchem Rezept eingefüllt habe — damit ich nachvollziehen kann, was meine Pflanzen wann bekommen haben, und meine Düngeprogramme über die Zeit optimieren kann."

**Beschreibung:**
Das System führt den **Tank (Reservoir)** als zentrale Infrastruktur-Entität ein. Ein Tank versorgt genau einen Bereich (Location) mit Nährstofflösung oder Gießwasser und ist der zentrale Knotenpunkt zwischen Bewässerung, Düngung und Standort-Verwaltung.

**Kernkonzepte:**

**Tank als Infrastruktur-Objekt:**
- Jeder Tank hat ein festes Volumen, einen Typ und einen aktuellen Zustand (Füllstand, EC, pH, Wassertemperatur)
- Tanks werden genau einer Location zugeordnet — die Location bestimmt, welche Slots/Pflanzen über diesen Tank versorgt werden
- Bei automatischer Bewässerung (`irrigation_system != 'manual'`) ist ein zugeordneter Tank **Pflicht** für die Location
- Bei manueller Bewässerung ist der Tank optional (Gießkanne statt Reservoir)

**Tank-Typen:**
- **Nährstofflösung (nutrient):** Fertig gemischte Lösung für Hydro-/Drip-Systeme
- **Gießwasser (irrigation):** Aufbereitetes Wasser (ggf. mit pH-Korrektur) für Erde/Coco
- **Reservoir (reservoir):** Vorratstank für Rohwasser (Regenwasser, Osmose, Leitungswasser)
- **Rezirkulation (recirculation):** Rücklauftank bei geschlossenen Hydro-Systemen (NFT, Ebb&Flow)

**Tankpflege & Wartungsaufgaben:**
Die Pflege des Tanks erzeugt direkte Auswirkungen auf die Aufgabenplanung (REQ-006):

- **Wasserwechsel (water_change):** Kompletter Austausch der Nährstofflösung — Intervall abhängig vom Tank-Typ und System (z.B. alle 7 Tage bei DWC, 14 Tage bei Drip)
- **Reinigung (cleaning):** Tankinneres + Leitungen von Algen, Biofilm und Ablagerungen befreien — z.B. bei sichtbarem Bewuchs oder nach jeder Ernte
- **Desinfektion (sanitization):** Sterile Reinigung mit H2O2 oder Enzymen — pflichtmäßig zwischen Grow-Zyklen
- **Kalibrierung (calibration):** EC-/pH-Sonden im Tank kalibrieren — alle 2-4 Wochen
- **Filterwechsel (filter_change):** Vorfilter, Inline-Filter, UV-Lampen austauschen
- **Pumpeninspektion (pump_inspection):** Umwälzpumpe, Druckpumpe, Dosierperistaltik prüfen

**Befüllungshistorie (Tank Fill Events):**
Jede Tankbefüllung — ob Vollwechsel, Auffüllen oder Korrektur — wird als eigenständiges, unveränderliches Event historisiert. Damit entsteht eine lückenlose Nachvollziehbarkeit, *welche* Lösung *wann* in *welcher Menge* und nach *welchem Rezept* in den Tank eingefüllt wurde.

- **Befüllungstypen:** Vollwechsel (full_change), Auffüllen (top_up), Korrektur/Nachdosierung (adjustment)
- **Rezept-Verknüpfung:** Optionale Referenz auf ein MixingResult (REQ-004), um das exakte Mischrezept mit Düngern und Dosierungen zu verknüpfen
- **Plan-Verknüpfung:** Optionale Referenz auf den NutrientPlan (REQ-004), nach dem dosiert wurde
- **Soll/Ist-Vergleich:** Ziel-EC/pH aus dem Plan vs. gemessene Werte nach Befüllung
- **Dünger-Snapshot:** Kopie der verwendeten Dünger + Dosierungen (unveränderlich, auch wenn das Quell-Rezept später geändert wird)
- **Wasserquelle:** Herkunft des Wassers (Osmose, Leitungswasser, Regenwasser) oder Referenz auf einen Quell-Tank bei Kaskaden
- **Automatische TankState-Erstellung:** Nach Erfassung eines Fill-Events wird ein TankState-Record mit den gemessenen Werten erzeugt

**Ergänzende manuelle Bewässerung (WateringEvent):**
Auch bei Locations mit automatischer Bewässerung (`irrigation_system != 'manual'`) kann es notwendig sein, einzelne Pflanzen oder Slots **zusätzlich per Hand** zu gießen — z.B. um organische Dünger auszubringen, die Tropfer verstopfen oder Biofilm im Tank verursachen würden. Das System modelliert dies über **WateringEvents** auf Slot-/Pflanzenebene:

- **Abgrenzung TankFillEvent vs. WateringEvent:**

| Aspekt | TankFillEvent | WateringEvent |
|--------|--------------|---------------|
| Ebene | Tank (Infrastruktur) | Slot/Pflanze (Pflanzenpflege) |
| Was wird dokumentiert? | Was geht IN den Tank | Was bekommt die PFLANZE tatsächlich |
| Typischer Anlass | Wasserwechsel, Auffüllung | Gießen, Blattdüngung, Top-Dressing |
| Verknüpfung | → MixingResult, NutrientPlan | → FeedingEvent (REQ-004), optional → TankFillEvent |

- **Applikationsmethoden:** Fertigation (Tank/Tropfer), Drench (Gießkanne), Foliar (Blattdüngung), Top Dress (Feststoffe auf Substrat) — siehe REQ-004 ApplicationMethod
- **Hybride Versorgung:** Eine Location kann gleichzeitig Tank-basiert (mineralisch via Drip) UND manuell (organisch via Gießkanne) versorgt werden. Das `irrigation_system` in REQ-002 beschreibt das primäre System, nicht die einzige Methode.
- **Tank-Safety-Warnung:** Wenn ein Nutzer einen Dünger mit `tank_safe=false` (REQ-004) in ein TankFillEvent einfügen möchte, warnt das System und schlägt manuelles Gießen per WateringEvent vor

**Zustandsüberwachung:**
- Kontinuierliches Tracking von pH, EC, Wassertemperatur und Füllstand (manuell oder via REQ-005 Sensorik)
- Automatische Alerts bei Grenzwert-Überschreitung (pH-Drift > 0.5, EC-Abweichung > 20%, Temperatur > 25°C)
- Füllstandswarnung bei < 20% Restvolumen
- Algenrisiko-Warnung bei Wassertemperatur > 22°C (Nährlösungstanks)

## 2. ArangoDB-Modellierung

### Nodes:

- **`:Tank`** — Physischer Tank/Reservoir
  - Collection: `tanks`
  - Properties:
    - `name: str` (z.B. "Haupttank Zelt 1", "Regenwasser Garten")
    - `tank_type: TankType` (nutrient | irrigation | reservoir | recirculation)
    - `volume_liters: float` (Nennvolumen)
    - `material: Optional[Literal['plastic', 'stainless_steel', 'glass', 'ibc']]`
    - `has_lid: bool` (Deckel vorhanden — Algenrisiko ohne Deckel)
    - `has_air_pump: bool` (Belüftung — wichtig für DWC)
    - `has_circulation_pump: bool` (Umwälzpumpe)
    - `has_heater: bool` (Heizstab für Winterbetrieb)
    - `installed_on: date` (Installationsdatum)
    - `notes: Optional[str]`

- **`:TankState`** — Momentaufnahme des Tank-Zustands (immutable)
  - Collection: `tank_states`
  - Properties:
    - `recorded_at: datetime`
    - `fill_level_liters: Optional[float]`
    - `fill_level_percent: Optional[float]`
    - `ph: Optional[float]`
    - `ec_ms: Optional[float]`
    - `water_temp_celsius: Optional[float]`
    - `tds_ppm: Optional[int]`
    - `source: Literal['manual', 'sensor', 'home_assistant']` (Datenherkunft analog REQ-005)

- **`:TankFillEvent`** — Einzelne Tankbefüllung (immutable)
  - Collection: `tank_fill_events`
  - Properties:
    - `filled_at: datetime`
    - `fill_type: Literal['full_change', 'top_up', 'adjustment']` (Vollwechsel | Auffüllen | Korrektur)
    - `volume_liters: float` (eingefülltes Volumen)
    - `mixing_result_key: Optional[str]` (Referenz auf MixingResult aus REQ-004)
    - `nutrient_plan_key: Optional[str]` (Referenz auf NutrientPlan aus REQ-004)
    - `target_ec_ms: Optional[float]` (Ziel-EC laut Plan/Rezept)
    - `target_ph: Optional[float]` (Ziel-pH laut Plan/Rezept)
    - `measured_ec_ms: Optional[float]` (gemessen nach Befüllung)
    - `measured_ph: Optional[float]` (gemessen nach Befüllung)
    - `water_source: Optional[Literal['tap', 'osmose', 'rainwater', 'distilled', 'well']]` (Wasserherkunft)
    - `source_tank_key: Optional[str]` (Quell-Tank bei Kaskade, z.B. Reservoir)
    - `fertilizers_used: Optional[list[FertilizerSnapshot]]` (Dünger-Snapshot: [{name, ml_per_liter, product_key}])
    - `base_water_ec_ms: Optional[float]` (EC des Ausgangswassers)
    - `performed_by: Optional[str]` (Benutzer)
    - `notes: Optional[str]`

- **`:WateringEvent`** — Einzelner Gießvorgang auf Slot-/Pflanzenebene (immutable)
  - Collection: `watering_events`
  - Properties:
    - `watered_at: datetime`
    - `application_method: Literal['fertigation', 'drench', 'foliar', 'top_dress']` (Art der Ausbringung — analog REQ-004 ApplicationMethod)
    - `is_supplemental: bool` (Ergänzend zur automatischen Bewässerung — z.B. organische Düngung per Gießkanne bei Drip-versorgten Pflanzen)
    - `volume_liters: float` (Gesamtvolumen)
    - `slot_keys: list[str]` (Betroffene Slots — mindestens 1)
    - `tank_fill_event_key: Optional[str]` (Referenz auf TankFillEvent, wenn aus dokumentierter Tankbefüllung)
    - `nutrient_plan_key: Optional[str]` (Referenz auf NutrientPlan aus REQ-004)
    - `fertilizers_used: Optional[list[FertilizerSnapshot]]` (Dünger-Snapshot mit Dosierungen)
    - `target_ec_ms: Optional[float]`
    - `target_ph: Optional[float]`
    - `measured_ec_ms: Optional[float]` (gemessen im Substrat/Runoff nach Gießen)
    - `measured_ph: Optional[float]`
    - `runoff_ec_ms: Optional[float]` (Drain-Messung bei Drain-to-Waste)
    - `runoff_ph: Optional[float]`
    - `water_source: Optional[Literal['tank', 'tap', 'osmose', 'rainwater', 'distilled', 'well']]`
    - `performed_by: Optional[str]`
    - `notes: Optional[str]`

- **`:MaintenanceLog`** — Einzelne Wartungsaktion (immutable)
  - Collection: `maintenance_logs`
  - Properties:
    - `maintenance_type: MaintenanceType` (water_change | cleaning | sanitization | calibration | filter_change | pump_inspection)
    - `performed_at: datetime`
    - `performed_by: Optional[str]` (Benutzer)
    - `duration_minutes: Optional[int]`
    - `products_used: Optional[list[str]]` (z.B. ["H2O2 3%", "Enzym-Reiniger"])
    - `notes: Optional[str]`
    - `next_due_at: Optional[datetime]` (Nächste Fälligkeit, berechnet aus Intervall)

- **`:MaintenanceSchedule`** — Wiederkehrender Wartungsplan pro Tank
  - Collection: `maintenance_schedules`
  - Properties:
    - `maintenance_type: MaintenanceType`
    - `interval_days: int` (z.B. 7 für wöchentlichen Wasserwechsel)
    - `reminder_days_before: int` (z.B. 1 Tag vorher erinnern)
    - `is_active: bool`
    - `priority: Literal['low', 'medium', 'high', 'critical']`
    - `auto_create_task: bool` (Task in REQ-006 automatisch anlegen)
    - `instructions: Optional[str]` (Spezielle Anweisungen)

### Edge-Collections:
```
has_tank:          locations → tanks                   // Location besitzt Tank
supplies:          tanks → locations                   // Tank versorgt Location (kann gleiche oder andere sein)
feeds_from:        tanks → tanks                       // Tankkaskade: Reservoir → Nährstofftank
has_state:         tanks → tank_states                 // Zeitserie von Zustandsmessungen
has_fill_event:    tanks → tank_fill_events            // Befüllungshistorie
has_maintenance:   tanks → maintenance_logs            // Wartungshistorie
has_schedule:      tanks → maintenance_schedules       // Geplante Wartungsintervalle
watered_slot:      watering_events → slots              // Gießvorgang betrifft Slot(s)
watering_from:     watering_events → tank_fill_events   // Gießvorgang stammt aus dokumentierter Tankbefüllung (optional)
generated_task:    maintenance_logs → tasks            // Verknüpfung zu REQ-006 Tasks
mixed_into:        mixing_results → tank_fill_events   // Nährstofflösung aus REQ-004 verknüpft mit Befüllungs-Event
```

**ArangoDB-Graph-Definition:**
```json
{
  "edge_collection": "has_tank",
  "from_vertex_collections": ["locations"],
  "to_vertex_collections": ["tanks"]
}
```
```json
{
  "edge_collection": "supplies",
  "from_vertex_collections": ["tanks"],
  "to_vertex_collections": ["locations"]
}
```
```json
{
  "edge_collection": "feeds_from",
  "from_vertex_collections": ["tanks"],
  "to_vertex_collections": ["tanks"]
}
```

### AQL-Beispielqueries:

**1. Alle Tanks einer Location inkl. aktuellstem Zustand:**
```aql
FOR tank IN tanks
    FOR edge IN has_tank
        FILTER edge._to == tank._id
        FILTER edge._from == CONCAT('locations/', @location_key)
        LET latest_state = FIRST(
            FOR state IN tank_states
                FOR se IN has_state
                    FILTER se._from == tank._id AND se._to == state._id
                    SORT state.recorded_at DESC
                    LIMIT 1
                    RETURN state
        )
        RETURN {
            tank: tank,
            current_state: latest_state
        }
```

**2. Fällige Wartungen über alle Tanks:**
```aql
FOR tank IN tanks
    FOR edge IN has_schedule
        FILTER edge._from == tank._id
        LET schedule = DOCUMENT(edge._to)
        FILTER schedule.is_active == true
        LET last_maintenance = FIRST(
            FOR log IN maintenance_logs
                FOR me IN has_maintenance
                    FILTER me._from == tank._id AND me._to == log._id
                    FILTER log.maintenance_type == schedule.maintenance_type
                    SORT log.performed_at DESC
                    LIMIT 1
                    RETURN log
        )
        LET days_since = last_maintenance != null
            ? DATE_DIFF(last_maintenance.performed_at, DATE_NOW(), "day")
            : 999
        FILTER days_since >= schedule.interval_days - schedule.reminder_days_before
        RETURN {
            tank_name: tank.name,
            tank_key: tank._key,
            maintenance_type: schedule.maintenance_type,
            interval_days: schedule.interval_days,
            days_since_last: days_since,
            days_overdue: days_since - schedule.interval_days,
            priority: schedule.priority,
            last_performed: last_maintenance.performed_at
        }
```

**3. Tank-Kaskade auflösen (Reservoir → Mischtank → Location):**
```aql
FOR v, e, p IN 1..3 OUTBOUND CONCAT('tanks/', @tank_key)
    GRAPH 'kamerplanter_graph'
    OPTIONS { uniqueVertices: "global" }
    FILTER IS_SAME_COLLECTION('feeds_from', e) OR IS_SAME_COLLECTION('supplies', e)
    RETURN {
        vertex: v,
        edge_type: PARSE_IDENTIFIER(e).collection,
        depth: LENGTH(p.edges)
    }
```

**4. Befüllungshistorie eines Tanks (chronologisch, mit Rezept-Details):**
```aql
FOR tank IN tanks
    FILTER tank._key == @tank_key
    FOR edge IN has_fill_event
        FILTER edge._from == tank._id
        LET fill_event = DOCUMENT(edge._to)
        SORT fill_event.filled_at DESC
        LIMIT @offset, @limit
        LET mixing_result = fill_event.mixing_result_key != null
            ? DOCUMENT(CONCAT('mixing_results/', fill_event.mixing_result_key))
            : null
        LET nutrient_plan = fill_event.nutrient_plan_key != null
            ? DOCUMENT(CONCAT('nutrient_plans/', fill_event.nutrient_plan_key))
            : null
        LET source_tank = fill_event.source_tank_key != null
            ? DOCUMENT(CONCAT('tanks/', fill_event.source_tank_key))
            : null
        RETURN {
            fill_event: fill_event,
            mixing_result: mixing_result ? { name: mixing_result.name, total_ec: mixing_result.total_ec } : null,
            nutrient_plan: nutrient_plan ? { name: nutrient_plan.name } : null,
            source_tank: source_tank ? { name: source_tank.name, tank_type: source_tank.tank_type } : null,
            ec_deviation: fill_event.target_ec_ms != null AND fill_event.measured_ec_ms != null
                ? ABS(fill_event.target_ec_ms - fill_event.measured_ec_ms)
                : null
        }
```

**5. Befüllungsstatistik pro Tank (Aggregation über Zeitraum):**
```aql
FOR tank IN tanks
    FILTER tank._key == @tank_key
    LET fill_events = (
        FOR edge IN has_fill_event
            FILTER edge._from == tank._id
            LET fe = DOCUMENT(edge._to)
            FILTER fe.filled_at >= @start_date AND fe.filled_at <= @end_date
            RETURN fe
    )
    RETURN {
        tank_key: tank._key,
        tank_name: tank.name,
        period: { start: @start_date, end: @end_date },
        total_fills: LENGTH(fill_events),
        full_changes: LENGTH(fill_events[* FILTER CURRENT.fill_type == 'full_change']),
        top_ups: LENGTH(fill_events[* FILTER CURRENT.fill_type == 'top_up']),
        adjustments: LENGTH(fill_events[* FILTER CURRENT.fill_type == 'adjustment']),
        total_volume_liters: SUM(fill_events[*].volume_liters),
        avg_ec_deviation: AVERAGE(
            fill_events[* FILTER CURRENT.target_ec_ms != null AND CURRENT.measured_ec_ms != null
                RETURN ABS(CURRENT.target_ec_ms - CURRENT.measured_ec_ms)]
        )
    }
```

**6. Gießhistorie eines Slots (alle Applikationsmethoden):**
```aql
FOR slot IN slots
    FILTER slot._key == @slot_key
    LET watering_events = (
        FOR edge IN watered_slot
            FILTER edge._to == slot._id
            LET we = DOCUMENT(edge._from)
            SORT we.watered_at DESC
            LIMIT @offset, @limit
            LET fill_event = we.tank_fill_event_key != null
                ? DOCUMENT(CONCAT('tank_fill_events/', we.tank_fill_event_key))
                : null
            RETURN {
                event: we,
                application_method: we.application_method,
                is_supplemental: we.is_supplemental,
                fertilizers: we.fertilizers_used,
                from_tank_fill: fill_event ? {
                    filled_at: fill_event.filled_at,
                    fill_type: fill_event.fill_type
                } : null
            }
    )
    RETURN {
        slot_key: slot._key,
        total_events: LENGTH(watering_events),
        events: watering_events
    }
```

**7. Vergleich: Tank-Fertigation vs. manuelle Ergänzungsdüngung pro Location:**
```aql
FOR loc IN locations
    FILTER loc._key == @location_key
    LET all_slots = (
        FOR edge IN has_slot
            FILTER edge._from == loc._id
            RETURN DOCUMENT(edge._to)
    )
    LET all_watering = (
        FOR slot IN all_slots
            FOR edge IN watered_slot
                FILTER edge._to == slot._id
                LET we = DOCUMENT(edge._from)
                FILTER we.watered_at >= @start_date AND we.watered_at <= @end_date
                RETURN we
    )
    RETURN {
        location: loc.name,
        period: { start: @start_date, end: @end_date },
        total_waterings: LENGTH(all_watering),
        fertigation_count: LENGTH(all_watering[* FILTER CURRENT.application_method == 'fertigation']),
        drench_count: LENGTH(all_watering[* FILTER CURRENT.application_method == 'drench']),
        foliar_count: LENGTH(all_watering[* FILTER CURRENT.application_method == 'foliar']),
        top_dress_count: LENGTH(all_watering[* FILTER CURRENT.application_method == 'top_dress']),
        supplemental_count: LENGTH(all_watering[* FILTER CURRENT.is_supplemental == true]),
        total_volume: SUM(all_watering[*].volume_liters)
    }
```

**8. Locations ohne zugeordneten Tank bei automatischer Bewässerung:**
```aql
FOR loc IN locations
    FILTER loc.irrigation_system != 'manual' AND loc.irrigation_system != null
    LET tank_count = LENGTH(
        FOR edge IN has_tank
            FILTER edge._from == loc._id
            RETURN 1
    )
    FILTER tank_count == 0
    RETURN {
        location_key: loc._key,
        location_name: loc.name,
        irrigation_system: loc.irrigation_system,
        warning: "Automatische Bewässerung konfiguriert, aber kein Tank zugeordnet"
    }
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Tank-Pydantic-Modelle:**
```python
from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

class TankType(str, Enum):
    NUTRIENT = "nutrient"           # Nährstofflösung
    IRRIGATION = "irrigation"       # Gießwasser
    RESERVOIR = "reservoir"         # Vorratstank (Regen/Osmose/Leitung)
    RECIRCULATION = "recirculation" # Rücklauftank (geschlossene Systeme)

class MaintenanceType(str, Enum):
    WATER_CHANGE = "water_change"
    CLEANING = "cleaning"
    SANITIZATION = "sanitization"
    CALIBRATION = "calibration"
    FILTER_CHANGE = "filter_change"
    PUMP_INSPECTION = "pump_inspection"

class TankDefinition(BaseModel):
    """Stammdaten eines physischen Tanks"""

    name: str = Field(min_length=1, max_length=100)
    tank_type: TankType
    volume_liters: float = Field(gt=0, le=10000)
    material: Optional[Literal['plastic', 'stainless_steel', 'glass', 'ibc']] = None
    has_lid: bool = Field(default=True)
    has_air_pump: bool = Field(default=False)
    has_circulation_pump: bool = Field(default=False)
    has_heater: bool = Field(default=False)
    installed_on: date = Field(default_factory=date.today)
    notes: Optional[str] = Field(None, max_length=1000)

class TankStateRecord(BaseModel):
    """Einzelne Zustandsmessung (immutable)"""

    recorded_at: datetime = Field(default_factory=datetime.now)
    fill_level_liters: Optional[float] = Field(None, ge=0)
    fill_level_percent: Optional[float] = Field(None, ge=0, le=100)
    ph: Optional[float] = Field(None, ge=0, le=14)
    ec_ms: Optional[float] = Field(None, ge=0, le=10)
    water_temp_celsius: Optional[float] = Field(None, ge=0, le=50)
    tds_ppm: Optional[int] = Field(None, ge=0)
    source: Literal['manual', 'sensor', 'home_assistant'] = 'manual'

    @model_validator(mode='after')
    def validate_fill_level_consistency(self):
        """Wenn beide Füllstands-Werte gegeben, müssen sie konsistent sein."""
        if self.fill_level_liters is not None and self.fill_level_percent is not None:
            # Konsistenz-Check wird im Service mit tank.volume_liters durchgeführt
            pass
        return self

class FillType(str, Enum):
    FULL_CHANGE = "full_change"     # Kompletter Lösungswechsel
    TOP_UP = "top_up"               # Auffüllen (Verdunstung/Verbrauch ausgleichen)
    ADJUSTMENT = "adjustment"       # Korrektur/Nachdosierung (pH/EC anpassen)

class FertilizerSnapshot(BaseModel):
    """Unveränderliche Kopie der Dünger-Dosierung zum Zeitpunkt der Befüllung"""

    product_key: Optional[str] = Field(None, description="ArangoDB _key des Fertilizer-Dokuments")
    product_name: str = Field(min_length=1, max_length=200)
    ml_per_liter: float = Field(gt=0, le=50.0)

class TankFillEvent(BaseModel):
    """Einzelne Tankbefüllung (immutable) — historisiert Rezept, Menge und Messwerte"""

    filled_at: datetime = Field(default_factory=datetime.now)
    fill_type: FillType
    volume_liters: float = Field(gt=0, le=10000, description="Eingefülltes Volumen in Litern")

    # Rezept-Verknüpfung (REQ-004)
    mixing_result_key: Optional[str] = Field(None, description="Referenz auf MixingResult aus REQ-004")
    nutrient_plan_key: Optional[str] = Field(None, description="Referenz auf NutrientPlan aus REQ-004")

    # Soll/Ist-Vergleich
    target_ec_ms: Optional[float] = Field(None, ge=0, le=10)
    target_ph: Optional[float] = Field(None, ge=0, le=14)
    measured_ec_ms: Optional[float] = Field(None, ge=0, le=10)
    measured_ph: Optional[float] = Field(None, ge=0, le=14)

    # Wasserherkunft
    water_source: Optional[Literal['tap', 'osmose', 'rainwater', 'distilled', 'well']] = None
    source_tank_key: Optional[str] = Field(None, description="Quell-Tank bei Kaskade")
    base_water_ec_ms: Optional[float] = Field(None, ge=0, le=5, description="EC des Ausgangswassers")

    # Dünger-Snapshot (unveränderliche Kopie)
    fertilizers_used: list[FertilizerSnapshot] = Field(default_factory=list)

    performed_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_full_change_has_volume(self):
        """Bei Vollwechsel sollte das Volumen dem Tankvolumen nahekommen (Warnung im Service)."""
        return self

    @model_validator(mode='after')
    def validate_adjustment_has_target(self):
        """Bei Korrektur muss mindestens ein Zielwert (EC oder pH) angegeben sein."""
        if self.fill_type == FillType.ADJUSTMENT:
            if self.target_ec_ms is None and self.target_ph is None:
                raise ValueError(
                    "Bei einer Korrektur (adjustment) muss mindestens "
                    "target_ec_ms oder target_ph angegeben werden"
                )
        return self

class ApplicationMethod(str, Enum):
    """Art der Ausbringung — identisch mit REQ-004 ApplicationMethod"""
    FERTIGATION = "fertigation"   # Über Tank/Tropfer/Pumpe
    DRENCH = "drench"             # Manuelles Gießen per Gießkanne
    FOLIAR = "foliar"             # Blattdüngung per Sprüher
    TOP_DRESS = "top_dress"       # Feststoff auf Substratoberfläche

class WateringEvent(BaseModel):
    """Einzelner Gießvorgang auf Slot-/Pflanzenebene (immutable)"""

    watered_at: datetime = Field(default_factory=datetime.now)
    application_method: ApplicationMethod
    is_supplemental: bool = Field(
        default=False,
        description="Ergänzend zur automatischen Tank-Bewässerung — "
                    "z.B. organische Düngung per Gießkanne bei Drip-System"
    )
    volume_liters: float = Field(gt=0, le=1000, description="Gesamtvolumen in Litern")
    slot_keys: list[str] = Field(min_length=1, description="Betroffene Slot-Keys")

    # Verknüpfung zu Tank/Rezept
    tank_fill_event_key: Optional[str] = Field(
        None, description="Referenz auf TankFillEvent, wenn aus Tank gegossen"
    )
    nutrient_plan_key: Optional[str] = Field(
        None, description="Referenz auf NutrientPlan (REQ-004)"
    )

    # Dünger-Snapshot
    fertilizers_used: list[FertilizerSnapshot] = Field(default_factory=list)

    # Soll/Ist
    target_ec_ms: Optional[float] = Field(None, ge=0, le=10)
    target_ph: Optional[float] = Field(None, ge=0, le=14)
    measured_ec_ms: Optional[float] = Field(None, ge=0, le=10)
    measured_ph: Optional[float] = Field(None, ge=0, le=14)
    runoff_ec_ms: Optional[float] = Field(None, ge=0, le=10)
    runoff_ph: Optional[float] = Field(None, ge=0, le=14)

    # Wasserherkunft
    water_source: Optional[Literal['tank', 'tap', 'osmose', 'rainwater', 'distilled', 'well']] = None

    performed_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_supplemental_not_fertigation(self):
        """Ergänzende Handdüngung ist per Definition nicht fertigation."""
        if self.is_supplemental and self.application_method == ApplicationMethod.FERTIGATION:
            raise ValueError(
                "Ergänzende Handdüngung (is_supplemental=true) kann nicht "
                "application_method='fertigation' sein — verwende 'drench', "
                "'foliar' oder 'top_dress'"
            )
        return self

class MaintenanceLogEntry(BaseModel):
    """Dokumentation einer durchgeführten Wartung"""

    maintenance_type: MaintenanceType
    performed_at: datetime = Field(default_factory=datetime.now)
    performed_by: Optional[str] = Field(None, max_length=100)
    duration_minutes: Optional[int] = Field(None, ge=0, le=1440)
    products_used: Optional[list[str]] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=2000)

class MaintenanceScheduleDefinition(BaseModel):
    """Wiederkehrender Wartungsplan"""

    maintenance_type: MaintenanceType
    interval_days: int = Field(ge=1, le=365)
    reminder_days_before: int = Field(ge=0, le=30)
    is_active: bool = True
    priority: Literal['low', 'medium', 'high', 'critical'] = 'medium'
    auto_create_task: bool = True
    instructions: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_reminder_before_interval(self):
        if self.reminder_days_before >= self.interval_days:
            raise ValueError(
                f"Erinnerung ({self.reminder_days_before}d) muss vor "
                f"dem Intervall ({self.interval_days}d) liegen"
            )
        return self
```

**2. Tank-Service-Logik:**
```python
from datetime import datetime, timedelta

class TankService:
    """Zentrale Geschäftslogik für Tank-Verwaltung"""

    def validate_tank_assignment(
        self,
        location_key: str,
        location_irrigation_system: str,
        existing_tanks: list[dict],
    ) -> tuple[bool, Optional[str]]:
        """
        Validiert Tank-Zuordnung zu einer Location.
        Bei automatischer Bewässerung ist ein Tank Pflicht.
        """
        is_automated = location_irrigation_system not in ('manual', None)

        if is_automated and len(existing_tanks) == 0:
            return False, (
                f"Location '{location_key}' hat Bewässerungssystem "
                f"'{location_irrigation_system}' konfiguriert — "
                f"ein Tank muss zugeordnet werden."
            )
        return True, None

    def check_alerts(
        self,
        tank: dict,
        current_state: dict,
    ) -> list[dict]:
        """
        Prüft Tank-Zustand gegen Grenzwerte und erzeugt Alerts.
        """
        alerts = []

        if current_state.get('ph') is not None:
            # pH-Drift-Check: Vergleich zum letzten Wasserwechsel
            # (vereinfacht: absolute Grenzen)
            ph = current_state['ph']
            if ph < 5.0 or ph > 7.0:
                alerts.append({
                    'type': 'ph_out_of_range',
                    'severity': 'high',
                    'message': f"pH {ph:.1f} außerhalb Zielbereich (5.0–7.0)",
                    'value': ph,
                })

        if current_state.get('ec_ms') is not None:
            ec = current_state['ec_ms']
            if tank['tank_type'] == 'nutrient' and ec > 3.0:
                alerts.append({
                    'type': 'ec_too_high',
                    'severity': 'high',
                    'message': f"EC {ec:.1f} mS zu hoch — Salzakkumulation?",
                    'value': ec,
                })

        if current_state.get('water_temp_celsius') is not None:
            temp = current_state['water_temp_celsius']
            if temp > 25.0:
                alerts.append({
                    'type': 'temperature_high',
                    'severity': 'medium',
                    'message': f"Wassertemperatur {temp:.1f}°C — erhöhtes Algenrisiko",
                    'value': temp,
                })
            if temp > 28.0:
                alerts[-1]['severity'] = 'critical'
                alerts[-1]['message'] = (
                    f"Wassertemperatur {temp:.1f}°C — kritisch! "
                    f"Gelöster Sauerstoff sinkt, Wurzelfäule-Gefahr."
                )

        if current_state.get('fill_level_percent') is not None:
            fill = current_state['fill_level_percent']
            if fill < 20:
                alerts.append({
                    'type': 'low_fill_level',
                    'severity': 'high',
                    'message': f"Füllstand {fill:.0f}% — Nachfüllen erforderlich",
                    'value': fill,
                })

        if not tank.get('has_lid', True):
            if current_state.get('water_temp_celsius', 0) > 22:
                alerts.append({
                    'type': 'algae_risk',
                    'severity': 'medium',
                    'message': "Tank ohne Deckel bei >22°C — hohes Algenrisiko",
                })

        return alerts

    def record_fill_event(
        self,
        tank: dict,
        fill_event: 'TankFillEvent',
    ) -> dict:
        """
        Erfasst eine Tankbefüllung und erzeugt automatisch einen TankState-Record.

        Returns: {fill_event: dict, tank_state: dict, warnings: list}
        """
        warnings = []

        # Plausibilitätsprüfung: Volumen vs. Tank-Kapazität
        if fill_event.fill_type == FillType.FULL_CHANGE:
            ratio = fill_event.volume_liters / tank['volume_liters']
            if ratio < 0.5:
                warnings.append(
                    f"Vollwechsel mit nur {fill_event.volume_liters}L "
                    f"bei {tank['volume_liters']}L Tank — wirklich Vollwechsel?"
                )
        elif fill_event.fill_type == FillType.TOP_UP:
            if fill_event.volume_liters > tank['volume_liters'] * 0.5:
                warnings.append(
                    f"Auffüllung von {fill_event.volume_liters}L ist >50% "
                    f"des Tank-Volumens — Vollwechsel stattdessen?"
                )

        # EC-Abweichungs-Check
        if fill_event.target_ec_ms is not None and fill_event.measured_ec_ms is not None:
            deviation = abs(fill_event.target_ec_ms - fill_event.measured_ec_ms)
            if deviation > 0.3:
                warnings.append(
                    f"EC-Abweichung: Ziel {fill_event.target_ec_ms} mS, "
                    f"gemessen {fill_event.measured_ec_ms} mS "
                    f"(Δ {deviation:.2f} mS)"
                )

        # pH-Abweichungs-Check
        if fill_event.target_ph is not None and fill_event.measured_ph is not None:
            ph_deviation = abs(fill_event.target_ph - fill_event.measured_ph)
            if ph_deviation > 0.5:
                warnings.append(
                    f"pH-Abweichung: Ziel {fill_event.target_ph}, "
                    f"gemessen {fill_event.measured_ph} "
                    f"(Δ {ph_deviation:.1f})"
                )

        # Automatisch TankState-Record erzeugen (wenn Messwerte vorhanden)
        tank_state = None
        if fill_event.measured_ec_ms is not None or fill_event.measured_ph is not None:
            tank_state = {
                'recorded_at': fill_event.filled_at,
                'ph': fill_event.measured_ph,
                'ec_ms': fill_event.measured_ec_ms,
                'fill_level_liters': fill_event.volume_liters if fill_event.fill_type == FillType.FULL_CHANGE else None,
                'source': 'manual',
            }

        return {
            'fill_event': fill_event.model_dump(),
            'tank_state': tank_state,
            'warnings': warnings,
        }

    def validate_tank_safe_fertilizers(
        self,
        fertilizers: list[dict],
    ) -> tuple[bool, list[str]]:
        """
        Prüft ob alle Dünger tank-sicher sind.
        Returns: (all_safe, warnings)
        """
        warnings = []
        for fert in fertilizers:
            if not fert.get('tank_safe', True):
                warnings.append(
                    f"'{fert['product_name']}' ist nicht tank-sicher "
                    f"(organisch/Schwebstoffe) — manuelles Gießen per "
                    f"Gießkanne empfohlen (WateringEvent mit "
                    f"application_method='drench')"
                )
        return len(warnings) == 0, warnings

    def record_watering_event(
        self,
        watering: 'WateringEvent',
        location_irrigation_system: str,
    ) -> dict:
        """
        Erfasst einen Gießvorgang auf Slot-Ebene.
        Erzeugt automatisch FeedingEvents (REQ-004) pro betroffener Pflanze.

        Returns: {watering_event: dict, feeding_events: list, warnings: list}
        """
        warnings = []

        # Bei fertigation auf manuellem System warnen
        if (watering.application_method == ApplicationMethod.FERTIGATION
                and location_irrigation_system == 'manual'):
            warnings.append(
                "Fertigation auf Location mit manuellem Bewässerungssystem — "
                "kein Tank/Tropfer vorhanden. Meintest du 'drench' (Gießkanne)?"
            )

        # Bei Drench auf automatischem System: is_supplemental vorschlagen
        if (watering.application_method in (ApplicationMethod.DRENCH, ApplicationMethod.FOLIAR,
                                             ApplicationMethod.TOP_DRESS)
                and location_irrigation_system != 'manual'
                and not watering.is_supplemental):
            warnings.append(
                "Manuelles Gießen auf Location mit automatischem System — "
                "is_supplemental=true empfohlen für korrekte Dokumentation."
            )

        # Volumen-Plausibilität pro Slot
        volume_per_slot = watering.volume_liters / len(watering.slot_keys)
        if volume_per_slot > 20:
            warnings.append(
                f"Hohe Gießmenge ({volume_per_slot:.1f}L pro Slot) — "
                f"Substratüberschwemmung möglich."
            )

        return {
            'watering_event': watering.model_dump(),
            'warnings': warnings,
        }

    def calculate_next_maintenance(
        self,
        schedule: dict,
        last_maintenance: Optional[dict],
    ) -> dict:
        """
        Berechnet nächsten Wartungstermin und Fälligkeitsstatus.
        """
        interval = timedelta(days=schedule['interval_days'])

        if last_maintenance is None:
            # Noch nie gewartet — sofort fällig
            return {
                'maintenance_type': schedule['maintenance_type'],
                'next_due': datetime.now(),
                'is_overdue': True,
                'days_overdue': 0,
                'status': 'overdue',
            }

        last_date = last_maintenance['performed_at']
        if isinstance(last_date, str):
            last_date = datetime.fromisoformat(last_date)

        next_due = last_date + interval
        now = datetime.now()
        reminder_start = next_due - timedelta(days=schedule['reminder_days_before'])

        if now > next_due:
            status = 'overdue'
            days_overdue = (now - next_due).days
        elif now >= reminder_start:
            status = 'due_soon'
            days_overdue = 0
        else:
            status = 'ok'
            days_overdue = 0

        return {
            'maintenance_type': schedule['maintenance_type'],
            'next_due': next_due,
            'is_overdue': status == 'overdue',
            'days_overdue': days_overdue,
            'status': status,
        }
```

**3. Standard-Wartungsintervalle je Tank-Typ:**
```python
DEFAULT_MAINTENANCE_SCHEDULES: dict[str, list[dict]] = {
    "nutrient": [
        {"type": "water_change", "interval_days": 7, "priority": "high"},
        {"type": "cleaning", "interval_days": 30, "priority": "medium"},
        {"type": "sanitization", "interval_days": 90, "priority": "high"},
        {"type": "calibration", "interval_days": 14, "priority": "medium"},
        {"type": "pump_inspection", "interval_days": 30, "priority": "low"},
    ],
    "irrigation": [
        {"type": "water_change", "interval_days": 14, "priority": "medium"},
        {"type": "cleaning", "interval_days": 60, "priority": "medium"},
        {"type": "sanitization", "interval_days": 90, "priority": "medium"},
        {"type": "filter_change", "interval_days": 90, "priority": "medium"},
    ],
    "reservoir": [
        {"type": "cleaning", "interval_days": 90, "priority": "low"},
        {"type": "sanitization", "interval_days": 180, "priority": "low"},
        {"type": "filter_change", "interval_days": 60, "priority": "medium"},
    ],
    "recirculation": [
        {"type": "water_change", "interval_days": 7, "priority": "critical"},
        {"type": "cleaning", "interval_days": 14, "priority": "high"},
        {"type": "sanitization", "interval_days": 60, "priority": "high"},
        {"type": "calibration", "interval_days": 14, "priority": "high"},
        {"type": "pump_inspection", "interval_days": 14, "priority": "medium"},
        {"type": "filter_change", "interval_days": 30, "priority": "high"},
    ],
}
```

**4. Task-Integration (REQ-006 Anbindung):**
```python
class MaintenanceTaskGenerator:
    """Erzeugt Aufgaben in REQ-006 basierend auf Wartungsplänen."""

    def generate_tasks_for_due_maintenance(
        self,
        tank_key: str,
        tank_name: str,
        due_maintenances: list[dict],
    ) -> list[dict]:
        """
        Wandelt fällige Wartungen in Task-Definitionen um (REQ-006 kompatibel).
        """
        tasks = []
        for m in due_maintenances:
            if m['status'] in ('overdue', 'due_soon'):
                task = {
                    'task_type': 'maintenance',
                    'trigger_type': 'schedule',
                    'title': f"Tank '{tank_name}': {m['maintenance_type'].replace('_', ' ').title()}",
                    'description': self._get_description(m),
                    'priority': 'critical' if m['status'] == 'overdue' else 'medium',
                    'due_date': m['next_due'],
                    'entity_type': 'tank',
                    'entity_key': tank_key,
                    'tags': ['tank', 'maintenance', m['maintenance_type']],
                }
                tasks.append(task)
        return tasks

    def _get_description(self, maintenance: dict) -> str:
        descriptions = {
            'water_change': "Nährstofflösung komplett wechseln. Alt-Lösung entsorgen, Tank spülen, frisch anmischen.",
            'cleaning': "Tank-Innenwände und Leitungen von Algen/Biofilm reinigen.",
            'sanitization': "Sterile Reinigung mit H2O2 (3%) oder Enzym-Reiniger. 30 Min einwirken lassen, gründlich spülen.",
            'calibration': "EC- und pH-Sonden mit Referenzlösungen kalibrieren (pH 4.0, 7.0; EC 1.413 mS).",
            'filter_change': "Inline-Filter und Vorfilter prüfen und bei Bedarf wechseln.",
            'pump_inspection': "Umwälz-/Druckpumpe auf Geräusche, Durchfluss und Dichtigkeit prüfen.",
        }
        base = descriptions.get(maintenance['maintenance_type'], "Wartung durchführen.")
        if maintenance['status'] == 'overdue':
            base = f"ÜBERFÄLLIG ({maintenance['days_overdue']} Tage)! " + base
        return base
```

### Datenvalidierung:
```python
from pydantic import BaseModel, Field, model_validator
from typing import Optional

class TankAssignmentValidator(BaseModel):
    """Validiert die Zuordnung Tank → Location"""

    tank_key: str
    location_key: str
    tank_type: TankType
    location_irrigation_system: Optional[str]

    @model_validator(mode='after')
    def validate_type_compatibility(self):
        """
        Recirculation-Tanks nur bei geschlossenen Systemen (hydro, nft, ebb_flow).
        """
        closed_systems = {'hydro', 'nft', 'ebb_flow'}
        if self.tank_type == TankType.RECIRCULATION:
            if self.location_irrigation_system not in closed_systems:
                raise ValueError(
                    f"Rezirkulationstank nur bei geschlossenen Systemen "
                    f"({', '.join(closed_systems)}), nicht bei "
                    f"'{self.location_irrigation_system}'"
                )
        return self

class FillLevelValidator(BaseModel):
    """Plausibilitätsprüfung für Füllstandsmeldungen"""

    tank_volume_liters: float
    fill_level_liters: Optional[float] = None
    fill_level_percent: Optional[float] = None

    @model_validator(mode='after')
    def validate_and_normalize(self):
        if self.fill_level_liters is not None:
            if self.fill_level_liters > self.tank_volume_liters * 1.05:
                raise ValueError(
                    f"Füllstand ({self.fill_level_liters}L) übersteigt "
                    f"Tankvolumen ({self.tank_volume_liters}L) um >5%"
                )
            # Prozent automatisch berechnen wenn nicht gegeben
            if self.fill_level_percent is None:
                self.fill_level_percent = round(
                    (self.fill_level_liters / self.tank_volume_liters) * 100, 1
                )
        return self
```

### REST-API-Endpunkte:
```
# Tank-CRUD
POST   /api/v1/locations/{location_key}/tanks          — Tank erstellen und Location zuordnen
GET    /api/v1/locations/{location_key}/tanks           — Alle Tanks einer Location
GET    /api/v1/tanks                                     — Alle Tanks (mit Filter: type, has_alerts)
GET    /api/v1/tanks/{tank_key}                          — Tank-Details inkl. aktuellem Zustand
PUT    /api/v1/tanks/{tank_key}                          — Tank-Stammdaten aktualisieren
DELETE /api/v1/tanks/{tank_key}                          — Tank entfernen (nur wenn nicht aktiv versorgt)

# Zustandsmessungen
POST   /api/v1/tanks/{tank_key}/states                  — Neue Messung erfassen
GET    /api/v1/tanks/{tank_key}/states                  — Messverlauf (Pagination + Zeitraum-Filter)
GET    /api/v1/tanks/{tank_key}/states/latest            — Aktuellste Messung
GET    /api/v1/tanks/{tank_key}/alerts                   — Aktuelle Alerts basierend auf letztem State

# Befüllungshistorie
POST   /api/v1/tanks/{tank_key}/fills                    — Befüllung dokumentieren (erzeugt TankFillEvent + optional TankState)
GET    /api/v1/tanks/{tank_key}/fills                    — Befüllungshistorie (Pagination + Zeitraum-Filter)
GET    /api/v1/tanks/{tank_key}/fills/latest              — Letzte Befüllung
GET    /api/v1/tanks/{tank_key}/fills/stats               — Befüllungsstatistik (Aggregation über Zeitraum)

# Gießvorgänge (Slot-/Pflanzenebene)
POST   /api/v1/watering-events                           — Gießvorgang dokumentieren (Slot-Auswahl im Body)
GET    /api/v1/slots/{slot_key}/watering-events           — Gießhistorie eines Slots (Pagination + Zeitraum-Filter)
GET    /api/v1/locations/{location_key}/watering-events   — Gießhistorie aller Slots einer Location
GET    /api/v1/locations/{location_key}/watering-stats    — Statistik: Fertigation vs. manuelle Ergänzung

# Wartung
POST   /api/v1/tanks/{tank_key}/maintenance              — Wartung dokumentieren
GET    /api/v1/tanks/{tank_key}/maintenance               — Wartungshistorie
GET    /api/v1/tanks/{tank_key}/maintenance/due           — Fällige Wartungen

# Wartungspläne
POST   /api/v1/tanks/{tank_key}/schedules                — Wartungsplan anlegen
GET    /api/v1/tanks/{tank_key}/schedules                — Alle Pläne eines Tanks
PUT    /api/v1/tanks/{tank_key}/schedules/{schedule_key} — Plan anpassen
DELETE /api/v1/tanks/{tank_key}/schedules/{schedule_key} — Plan deaktivieren

# Übergreifend
GET    /api/v1/maintenance/due                            — Alle fälligen Wartungen (tankübergreifend)
GET    /api/v1/locations/{location_key}/tanks/validation  — Prüfe ob Location Tank braucht
```

### Seed-Daten:
```json
// tanks collection
{ "_key": "tank_zelt1", "name": "Haupttank Grow Zelt 1", "tank_type": "nutrient", "volume_liters": 50, "material": "plastic", "has_lid": true, "has_air_pump": true, "has_circulation_pump": true, "has_heater": false, "installed_on": "2025-06-01" }
{ "_key": "tank_regenwasser", "name": "Regenwassertonne Garten", "tank_type": "reservoir", "volume_liters": 300, "material": "plastic", "has_lid": true, "has_air_pump": false, "has_circulation_pump": false, "has_heater": false, "installed_on": "2024-03-15" }
{ "_key": "tank_recirc_nft", "name": "NFT-Rücklauf Zelt 2", "tank_type": "recirculation", "volume_liters": 20, "material": "plastic", "has_lid": true, "has_air_pump": true, "has_circulation_pump": true, "has_heater": false, "installed_on": "2025-09-10" }

// has_tank edge collection
{ "_from": "locations/growzelt1", "_to": "tanks/tank_zelt1" }
{ "_from": "locations/garten", "_to": "tanks/tank_regenwasser" }
{ "_from": "locations/growzelt2", "_to": "tanks/tank_recirc_nft" }

// supplies edge collection
{ "_from": "tanks/tank_zelt1", "_to": "locations/growzelt1" }
{ "_from": "tanks/tank_regenwasser", "_to": "locations/garten" }
{ "_from": "tanks/tank_recirc_nft", "_to": "locations/growzelt2" }

// feeds_from edge collection (Kaskade: Regenwasser → Mischtank)
{ "_from": "tanks/tank_zelt1", "_to": "tanks/tank_regenwasser" }

// tank_fill_events collection
{ "_key": "fill_zelt1_001", "filled_at": "2026-02-19T10:00:00Z", "fill_type": "full_change", "volume_liters": 48, "mixing_result_key": null, "nutrient_plan_key": "plan_tomato_coco", "target_ec_ms": 1.8, "target_ph": 5.8, "measured_ec_ms": 1.75, "measured_ph": 5.9, "water_source": "osmose", "source_tank_key": "tank_regenwasser", "base_water_ec_ms": 0.05, "fertilizers_used": [{"product_name": "CalMag", "ml_per_liter": 1.0, "product_key": "fert_calmag"}, {"product_name": "Flora Micro", "ml_per_liter": 1.5, "product_key": "fert_micro"}, {"product_name": "Flora Bloom", "ml_per_liter": 2.0, "product_key": "fert_bloom"}], "performed_by": "admin", "notes": "Wöchentlicher Vollwechsel" }
{ "_key": "fill_zelt1_002", "filled_at": "2026-02-22T08:30:00Z", "fill_type": "top_up", "volume_liters": 12, "mixing_result_key": null, "nutrient_plan_key": "plan_tomato_coco", "target_ec_ms": 1.8, "target_ph": null, "measured_ec_ms": 1.7, "measured_ph": 6.0, "water_source": "osmose", "source_tank_key": null, "base_water_ec_ms": 0.05, "fertilizers_used": [{"product_name": "Flora Micro", "ml_per_liter": 1.5, "product_key": "fert_micro"}, {"product_name": "Flora Bloom", "ml_per_liter": 2.0, "product_key": "fert_bloom"}], "performed_by": "admin", "notes": "Verdunstung ausgeglichen" }
{ "_key": "fill_zelt1_003", "filled_at": "2026-02-24T14:00:00Z", "fill_type": "adjustment", "volume_liters": 2, "mixing_result_key": null, "nutrient_plan_key": null, "target_ec_ms": null, "target_ph": 5.8, "measured_ec_ms": 1.85, "measured_ph": 5.7, "water_source": null, "source_tank_key": null, "base_water_ec_ms": null, "fertilizers_used": [], "performed_by": "admin", "notes": "pH-Down Korrektur (pH war auf 6.5 gedriftet)" }

// has_fill_event edge collection
{ "_from": "tanks/tank_zelt1", "_to": "tank_fill_events/fill_zelt1_001" }
{ "_from": "tanks/tank_zelt1", "_to": "tank_fill_events/fill_zelt1_002" }
{ "_from": "tanks/tank_zelt1", "_to": "tank_fill_events/fill_zelt1_003" }

// watering_events collection (Slot-/Pflanzenebene)
{ "_key": "water_evt_001", "watered_at": "2026-02-19T11:00:00Z", "application_method": "fertigation", "is_supplemental": false, "volume_liters": 2.5, "slot_keys": ["GROWZELT1_A1", "GROWZELT1_A2", "GROWZELT1_A3"], "tank_fill_event_key": "fill_zelt1_001", "nutrient_plan_key": "plan_tomato_coco", "fertilizers_used": [], "target_ec_ms": 1.8, "measured_ec_ms": null, "runoff_ec_ms": 1.6, "runoff_ph": 6.1, "water_source": "tank", "performed_by": "admin", "notes": "Reguläre Tropfer-Bewässerung nach Vollwechsel" }
{ "_key": "water_evt_002", "watered_at": "2026-02-20T09:00:00Z", "application_method": "drench", "is_supplemental": true, "volume_liters": 1.5, "slot_keys": ["GROWZELT1_A1", "GROWZELT1_A2"], "tank_fill_event_key": null, "nutrient_plan_key": null, "fertilizers_used": [{"product_name": "Komposttee (selbst gebraut)", "ml_per_liter": 0, "product_key": null}, {"product_name": "Mykorrhiza-Suspension", "ml_per_liter": 2.0, "product_key": "fert_myko"}], "target_ec_ms": null, "measured_ec_ms": null, "water_source": "rainwater", "performed_by": "admin", "notes": "Organische Ergänzungsdüngung per Gießkanne — Komposttee + Mykorrhiza, nicht über Tropfer" }
{ "_key": "water_evt_003", "watered_at": "2026-02-22T16:00:00Z", "application_method": "foliar", "is_supplemental": true, "volume_liters": 0.3, "slot_keys": ["GROWZELT1_A1", "GROWZELT1_A2", "GROWZELT1_A3"], "tank_fill_event_key": null, "nutrient_plan_key": null, "fertilizers_used": [{"product_name": "CalMag Foliar Spray", "ml_per_liter": 0.5, "product_key": "fert_calmag_foliar"}], "target_ec_ms": null, "measured_ec_ms": null, "water_source": "osmose", "performed_by": "admin", "notes": "Blattdüngung mit Kalzium gegen Blütenend-Fäule" }

// watered_slot edge collection
{ "_from": "watering_events/water_evt_001", "_to": "slots/GROWZELT1_A1" }
{ "_from": "watering_events/water_evt_001", "_to": "slots/GROWZELT1_A2" }
{ "_from": "watering_events/water_evt_001", "_to": "slots/GROWZELT1_A3" }
{ "_from": "watering_events/water_evt_002", "_to": "slots/GROWZELT1_A1" }
{ "_from": "watering_events/water_evt_002", "_to": "slots/GROWZELT1_A2" }
{ "_from": "watering_events/water_evt_003", "_to": "slots/GROWZELT1_A1" }
{ "_from": "watering_events/water_evt_003", "_to": "slots/GROWZELT1_A2" }
{ "_from": "watering_events/water_evt_003", "_to": "slots/GROWZELT1_A3" }

// watering_from edge collection (WateringEvent → TankFillEvent)
{ "_from": "watering_events/water_evt_001", "_to": "tank_fill_events/fill_zelt1_001" }

// maintenance_schedules (automatisch bei Tank-Erstellung generiert)
{ "_key": "sched_zelt1_wc", "maintenance_type": "water_change", "interval_days": 7, "reminder_days_before": 1, "is_active": true, "priority": "high", "auto_create_task": true }
{ "_key": "sched_zelt1_clean", "maintenance_type": "cleaning", "interval_days": 30, "reminder_days_before": 3, "is_active": true, "priority": "medium", "auto_create_task": true }
{ "_key": "sched_zelt1_cal", "maintenance_type": "calibration", "interval_days": 14, "reminder_days_before": 1, "is_active": true, "priority": "medium", "auto_create_task": true }

// has_schedule edges
{ "_from": "tanks/tank_zelt1", "_to": "maintenance_schedules/sched_zelt1_wc" }
{ "_from": "tanks/tank_zelt1", "_to": "maintenance_schedules/sched_zelt1_clean" }
{ "_from": "tanks/tank_zelt1", "_to": "maintenance_schedules/sched_zelt1_cal" }
```

## 4. Abhängigkeiten

**Erforderliche Module:**
- REQ-002 (Standort): Location für Tank-Zuordnung, `irrigation_system` für Pflicht-Validierung
- REQ-004 (Düngung): MixingResult als Input für Tank-Befüllung (Nährstofflösung)
- REQ-005 (Sensorik): Sensor-Daten für automatische Zustandserfassung (pH, EC, Füllstand, Temperatur)

**Wird benötigt von:**
- REQ-004 (Düngung): **HOCH** — Tank als Zielgefäß für MixingResult; EC-Budget basiert auf Tank-Volumen
- REQ-005 (Sensorik): **MITTEL** — Tank-Sensoren als zusätzliche Sensor-Locations (Füllstand, Wassertemperatur)
- REQ-006 (Aufgabenplanung): **HOCH** — Wartungs-Tasks werden automatisch aus MaintenanceSchedule generiert
- REQ-009 (Dashboard): **MITTEL** — Tank-Status-Widget, Alert-Anzeige, fällige Wartungen
- REQ-013 (Pflanzdurchlauf): **NIEDRIG** — PlantingRun referenziert Tank als Versorgungsquelle

**Celery-Tasks:**
- `check_maintenance_due` — Täglich: Prüft alle Tanks auf fällige Wartungen, erzeugt Tasks (REQ-006)
- `check_tank_alerts` — Stündlich: Prüft Tank-Zustände gegen Grenzwerte, erzeugt Alerts

## 5. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Tank-CRUD:** Vollständiges Erstellen, Lesen, Aktualisieren und Löschen von Tanks
- [ ] **Location-Zuordnung:** Tank wird über `has_tank`-Edge einer Location zugeordnet
- [ ] **Pflicht-Validierung:** Bei `irrigation_system != 'manual'` wird ein zugeordneter Tank erzwungen
- [ ] **Tank-Typen:** Alle 4 Typen (nutrient, irrigation, reservoir, recirculation) unterstützt
- [ ] **Typ-Kompatibilität:** Recirculation-Tank nur bei geschlossenen Systemen erlaubt
- [ ] **Zustandserfassung:** Manuelle und automatische (REQ-005) Messungen für pH, EC, Temperatur, Füllstand
- [ ] **Zustandshistorie:** Zeitserie von TankState-Records mit Pagination und Zeitraum-Filter
- [ ] **Alert-System:** Automatische Grenzwert-Prüfung (pH, EC, Temperatur, Füllstand, Algenrisiko)
- [ ] **Befüllungshistorie:** Jede Tankbefüllung wird als immutables TankFillEvent dokumentiert
- [ ] **Befüllungstypen:** Vollwechsel, Auffüllen und Korrektur werden unterschieden
- [ ] **Rezept-Verknüpfung:** TankFillEvent kann optional auf MixingResult und NutrientPlan (REQ-004) referenzieren
- [ ] **Dünger-Snapshot:** Verwendete Dünger + Dosierungen werden als unveränderliche Kopie im Event gespeichert
- [ ] **Soll/Ist-Vergleich:** Ziel-EC/pH und gemessene Werte nach Befüllung werden erfasst
- [ ] **Automatischer TankState:** Bei Befüllung mit Messwerten wird automatisch ein TankState-Record erzeugt
- [ ] **Befüllungsstatistik:** Aggregierte Auswertung über Zeiträume (Anzahl, Volumen, EC-Abweichung)
- [ ] **WateringEvent:** Gießvorgänge auf Slot-/Pflanzenebene werden als immutable Events dokumentiert
- [ ] **Applikationsmethoden:** Fertigation, Drench, Foliar und Top Dress werden unterschieden
- [ ] **Ergänzende Handdüngung:** Manuelles Gießen per Gießkanne kann als `is_supplemental=true` neben automatischer Bewässerung dokumentiert werden
- [ ] **Tank-Safety-Warnung:** Bei nicht-tanksicheren Düngern (`tank_safe=false` aus REQ-004) im TankFillEvent wird Warnung ausgegeben und Drench empfohlen
- [ ] **Slot-Gießhistorie:** Vollständige Gießhistorie pro Slot abrufbar (alle Applikationsmethoden)
- [ ] **Statistik:** Vergleich Fertigation vs. manuelle Ergänzungsdüngung pro Location/Zeitraum
- [ ] **Wartungshistorie:** Alle Wartungsaktionen dokumentiert mit Typ, Datum, Produkten
- [ ] **Wartungspläne:** Wiederkehrende Schedules mit konfigurierbarem Intervall und Erinnerung
- [ ] **Standard-Schedules:** Bei Tank-Erstellung werden Default-Wartungspläne automatisch angelegt (je nach Tank-Typ)
- [ ] **Task-Generierung:** Fällige Wartungen erzeugen automatisch Tasks in REQ-006
- [ ] **Tank-Kaskade:** `feeds_from`-Edge für Tankketten (Reservoir → Mischtank)
- [ ] **Lösch-Schutz:** Tank kann nicht gelöscht werden, wenn er aktive Location versorgt
- [ ] **Füllstand-Plausibilität:** Füllstand kann Tank-Volumen nicht signifikant übersteigen
- [ ] **Celery-Beat:** `check_maintenance_due` (täglich) und `check_tank_alerts` (stündlich) registriert

### Testszenarien:

**Szenario 1: Tank-Pflicht bei automatischer Bewässerung**
```
GIVEN: Location "Grow Zelt 1" mit irrigation_system="drip", kein Tank zugeordnet
WHEN: System validiert Location-Konfiguration
THEN:
  - Warnung: "Automatische Bewässerung konfiguriert, aber kein Tank zugeordnet"
  - Validierung schlägt fehl bei Versuch, Bewässerung zu starten
  - Nach Zuordnung eines Tanks: Validierung OK
```

**Szenario 2: Wasserwechsel-Fälligkeit und Task-Generierung**
```
GIVEN: Tank "Haupttank Zelt 1" (nutrient), Wasserwechsel-Intervall 7 Tage,
       letzter Wechsel vor 8 Tagen
WHEN: Celery-Task `check_maintenance_due` läuft
THEN:
  - Wartung "water_change" ist 1 Tag überfällig
  - Neuer Task wird in REQ-006 generiert:
    Titel: "Tank 'Haupttank Zelt 1': Water Change"
    Priorität: critical (überfällig)
  - Dashboard zeigt Alert
```

**Szenario 3: Tank-Alerts bei kritischen Werten**
```
GIVEN: Nährstofftank mit Zustand: pH=7.5, EC=3.2, Wassertemp=29°C, Füllstand=15%
WHEN: System prüft Grenzwerte
THEN:
  - 4 Alerts erzeugt:
    1. "pH 7.5 außerhalb Zielbereich (5.0–7.0)" — severity: high
    2. "EC 3.2 mS zu hoch — Salzakkumulation?" — severity: high
    3. "Wassertemperatur 29.0°C — kritisch! Wurzelfäule-Gefahr." — severity: critical
    4. "Füllstand 15% — Nachfüllen erforderlich" — severity: high
```

**Szenario 4: Recirculation-Tank nur bei geschlossenem System**
```
GIVEN: Location "Beet A" mit irrigation_system="drip" (offenes System)
WHEN: Nutzer versucht einen Recirculation-Tank zuzuordnen
THEN:
  - System lehnt ab: "Rezirkulationstank nur bei geschlossenen Systemen (hydro, nft, ebb_flow)"
  - Bei Location mit irrigation_system="nft": Zuordnung erfolgreich
```

**Szenario 5: Tank-Kaskade (Reservoir → Mischtank)**
```
GIVEN: "Regenwassertonne" (reservoir, 300L) → feeds_from → "Haupttank Zelt 1" (nutrient, 50L)
WHEN: Nutzer füllt Haupttank auf und mischt Nährstofflösung
THEN:
  - System zeigt Quell-Tank (Regenwassertonne) als Wasserquelle
  - Basis-EC wird von Regenwasser-Tank übernommen (nicht Leitungswasser-Default)
  - REQ-004 MixingResult referenziert beide Tanks
```

**Szenario 6: Standard-Wartungspläne bei Tank-Erstellung**
```
GIVEN: Nutzer erstellt neuen Tank vom Typ "recirculation"
WHEN: Tank wird gespeichert
THEN:
  - 6 Wartungspläne automatisch angelegt:
    water_change (7d, critical), cleaning (14d, high),
    sanitization (60d, high), calibration (14d, high),
    pump_inspection (14d, medium), filter_change (30d, high)
  - Alle Pläne mit auto_create_task=true
  - Nutzer kann Intervalle individuell anpassen
```

**Szenario 7: Tank-Löschung mit aktiver Versorgung**
```
GIVEN: Tank "Haupttank Zelt 1" versorgt Location "Grow Zelt 1" (3 aktive Pflanzen)
WHEN: Nutzer versucht Tank zu löschen
THEN:
  - System blockiert: "Tank kann nicht gelöscht werden — versorgt aktiv 'Grow Zelt 1'"
  - Nutzer muss zuerst Zuordnung auflösen oder Pflanzen umsetzen
```

**Szenario 8: Tankbefüllung als Vollwechsel mit Rezept dokumentieren**
```
GIVEN: Tank "Haupttank Zelt 1" (nutrient, 50L),
       NutrientPlan "Tomato Heavy Coco" mit Phase vegetative (Ziel-EC 1.8, pH 5.8),
       Dünger: CalMag 1.0 ml/L, Flora Micro 1.5 ml/L, Flora Bloom 2.0 ml/L
WHEN: POST /api/v1/tanks/tank_zelt1/fills
      Body: { fill_type: "full_change", volume_liters: 48,
              nutrient_plan_key: "plan_tomato_coco",
              target_ec_ms: 1.8, target_ph: 5.8,
              measured_ec_ms: 1.75, measured_ph: 5.9,
              water_source: "osmose", base_water_ec_ms: 0.05,
              fertilizers_used: [{product_name: "CalMag", ml_per_liter: 1.0}, ...] }
THEN:
  - TankFillEvent immutabel gespeichert mit allen Feldern
  - has_fill_event-Edge von Tank zum Event erstellt
  - Automatisch TankState-Record erzeugt (ec_ms: 1.75, ph: 5.9, source: 'manual')
  - Dünger-Snapshot ist unabhängig vom Quell-Fertilizer-Dokument
  - Response enthält warnings: [] (EC-Abweichung 0.05 < 0.3 Toleranz)
```

**Szenario 9: Auffüllung mit Volumen-Warnung**
```
GIVEN: Tank "Haupttank Zelt 1" (nutrient, 50L), letzte Befüllung vor 3 Tagen
WHEN: POST /api/v1/tanks/tank_zelt1/fills
      Body: { fill_type: "top_up", volume_liters: 30, target_ec_ms: 1.8 }
THEN:
  - TankFillEvent wird gespeichert
  - Warnung: "Auffüllung von 30L ist >50% des Tank-Volumens — Vollwechsel stattdessen?"
```

**Szenario 10: pH-Korrektur ohne Rezept**
```
GIVEN: Tank "Haupttank Zelt 1", pH ist auf 6.5 gedriftet
WHEN: POST /api/v1/tanks/tank_zelt1/fills
      Body: { fill_type: "adjustment", volume_liters: 0.5,
              target_ph: 5.8, measured_ph: 5.7,
              notes: "pH-Down Korrektur" }
THEN:
  - TankFillEvent gespeichert (kein mixing_result_key, kein nutrient_plan_key)
  - TankState-Record mit ph: 5.7 erzeugt
  - Keine Warnung (pH-Abweichung 0.1 < 0.5 Toleranz)
```

**Szenario 11: Befüllungshistorie abrufen**
```
GIVEN: Tank "Haupttank Zelt 1" mit 3 historischen Befüllungen im Februar
WHEN: GET /api/v1/tanks/tank_zelt1/fills?start=2026-02-01&end=2026-02-28
THEN:
  - 3 Events chronologisch absteigend sortiert
  - Jedes Event enthält: fill_type, volume_liters, target/measured EC/pH, Dünger-Snapshot
  - Verknüpfte NutrientPlan-Namen werden aufgelöst
```

**Szenario 12: Befüllungsstatistik für Verbrauchsanalyse**
```
GIVEN: Tank "Haupttank Zelt 1" mit 4 Vollwechseln, 8 Auffüllungen, 2 Korrekturen im Januar
WHEN: GET /api/v1/tanks/tank_zelt1/fills/stats?start=2026-01-01&end=2026-01-31
THEN:
  - total_fills: 14
  - full_changes: 4, top_ups: 8, adjustments: 2
  - total_volume_liters: 288 (4×48 + 8×12 + 2×0.5)
  - avg_ec_deviation: 0.12
```

**Szenario 13: Ergänzende organische Düngung per Gießkanne neben Drip-System**
```
GIVEN: Location "Grow Zelt 1" mit irrigation_system="drip", Tank zugeordnet,
       Slots A1, A2 mit Tomaten in Coco,
       Dünger "Komposttee" (is_organic=true, tank_safe=false, recommended_application="drench"),
       Dünger "Mykorrhiza-Suspension" (is_organic=true, tank_safe=false)
WHEN: POST /api/v1/watering-events
      Body: { application_method: "drench", is_supplemental: true,
              volume_liters: 1.5, slot_keys: ["GROWZELT1_A1", "GROWZELT1_A2"],
              fertilizers_used: [{product_name: "Komposttee"}, {product_name: "Mykorrhiza-Suspension", ml_per_liter: 2.0}],
              water_source: "rainwater", notes: "Organische Ergänzung per Gießkanne" }
THEN:
  - WateringEvent immutabel gespeichert mit is_supplemental=true
  - watered_slot-Edges zu beiden Slots erstellt
  - FeedingEvents (REQ-004) pro betroffener Pflanze erzeugt mit application_method="drench"
  - Dünger-Snapshot unveränderlich im Event gespeichert
  - Keine Tank-Interaktion (kein TankFillEvent, kein TankState)
```

**Szenario 14: Tank-Safety-Warnung bei nicht-tanksicherem Dünger**
```
GIVEN: Tank "Haupttank Zelt 1" (nutrient),
       Dünger "Fischemulsion" (is_organic=true, tank_safe=false)
WHEN: Nutzer versucht TankFillEvent zu erstellen mit Fischemulsion in fertilizers_used
THEN:
  - Warnung: "'Fischemulsion' ist nicht tank-sicher (organisch/Schwebstoffe) —
    manuelles Gießen per Gießkanne empfohlen (WateringEvent mit application_method='drench')"
  - TankFillEvent wird NICHT blockiert (Warnung, kein Fehler — Nutzer entscheidet)
```

**Szenario 15: Blattdüngung als Ergänzung**
```
GIVEN: Location "Grow Zelt 1" mit irrigation_system="drip",
       Pflanzen zeigen Kalzium-Mangel (Blütenend-Fäule)
WHEN: POST /api/v1/watering-events
      Body: { application_method: "foliar", is_supplemental: true,
              volume_liters: 0.3, slot_keys: ["GROWZELT1_A1", "GROWZELT1_A2", "GROWZELT1_A3"],
              fertilizers_used: [{product_name: "CalMag Foliar Spray", ml_per_liter: 0.5}],
              water_source: "osmose" }
THEN:
  - WateringEvent mit application_method="foliar" gespeichert
  - Niedrige Gießmenge (0.1L pro Slot) — keine Volumen-Warnung
  - Slot-Gießhistorie zeigt Foliar-Event separat von Fertigation-Events
```

**Szenario 16: Gießhistorie eines Slots zeigt alle Applikationsmethoden**
```
GIVEN: Slot "GROWZELT1_A1" mit 3 Gießvorgängen im Februar:
       - 19.02. fertigation (aus Tank, 0.83L)
       - 20.02. drench (Komposttee per Gießkanne, 0.75L, supplemental)
       - 22.02. foliar (CalMag Spray, 0.1L, supplemental)
WHEN: GET /api/v1/slots/GROWZELT1_A1/watering-events?start=2026-02-01&end=2026-02-28
THEN:
  - 3 Events chronologisch absteigend sortiert
  - Jedes Event enthält: application_method, is_supplemental, volume, Dünger-Snapshot
  - Fertigation-Event verlinkt auf TankFillEvent, Drench/Foliar nicht
  - Nutzer sieht vollständiges Bild: mineralische Basis-Ernährung + organische Ergänzung
```

**Szenario 17: Statistik zeigt hybride Versorgung**
```
GIVEN: Location "Grow Zelt 1" im Februar: 12 Fertigations, 4 Drenches (supplemental),
       2 Foliars (supplemental), 1 Top Dress
WHEN: GET /api/v1/locations/growzelt1/watering-stats?start=2026-02-01&end=2026-02-28
THEN:
  - total_waterings: 19
  - fertigation_count: 12, drench_count: 4, foliar_count: 2, top_dress_count: 1
  - supplemental_count: 7
  - total_volume: ~35L
```

**Szenario 18: Manuelle Zustandserfassung**
```
GIVEN: Tank "Haupttank Zelt 1", letzte Messung vor 3 Tagen
WHEN: Nutzer erfasst neue Werte: pH=6.2, EC=1.8, Temp=21°C, Füllstand=35L
THEN:
  - Neuer TankState-Record mit source='manual' erstellt
  - fill_level_percent automatisch berechnet (35/50 = 70%)
  - Keine Alerts (alle Werte im Zielbereich)
  - Messung in Zustandsverlauf sichtbar
```

---

**Hinweise für RAG-Integration:**
- Keywords: Tank, Reservoir, Bewässerung, Nährstofflösung, Wasserwechsel, Reinigung, Desinfektion, Kalibrierung, Wartungsplan, Wartungshistorie, Befüllungshistorie, Tankbefüllung, Vollwechsel, Auffüllung, Korrektur, Dünger-Snapshot, Rezept-Verknüpfung, Füllstand, Algenrisiko, Rezirkulation, Tankkaskade, Gießkanne, Gießvorgang, manuelle Bewässerung, ergänzende Handdüngung, Blattdüngung, Komposttee, organischer Dünger, Applikationsmethode, Fertigation, Drench, Foliar, Top Dress
- Technische Begriffe: MaintenanceSchedule, TankState, TankFillEvent, WateringEvent, ApplicationMethod, FillType, FertilizerSnapshot, TankType, MaintenanceType, feeds_from, has_tank, has_fill_event, watered_slot, watering_from, supplies, mixed_into, auto_create_task, tank_safe, is_organic, is_supplemental, Celery-Beat
- Verknüpfung: Zentral für REQ-002 (Standort — irrigation_system), REQ-004 (Düngung — MixingResult, NutrientPlan, FeedingEvent, ApplicationMethod, Fertilizer.tank_safe), REQ-005 (Sensorik), REQ-006 (Aufgabenplanung)
