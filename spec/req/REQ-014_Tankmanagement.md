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

**User Story:** "Als Gärtner möchte ich meine Nährstoff-/Gießwasser-Tanks als eigenständige Objekte verwalten — mit Zuordnung zu einem Bereich, lückenloser Pflegehistorie und automatisierter Aufgabenplanung — damit ich den Überblick über Wasserwechsel, Reinigungen und Reservoirzustand behalte und die Bewässerung meiner Pflanzen zuverlässig läuft."

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

**Zustandsüberwachung:**
- Kontinuierliches Tracking von pH, EC, Wassertemperatur und Füllstand (manuell oder via REQ-005 Sensorik)
- Automatische Alerts bei Grenzwert-Überschreitung (pH-Drift > 0.5, EC-Abweichung > 20%, Temperatur > 25°C)
- Füllstandswarnung bei < 20% Restvolumen
- Algenrisiko-Warnung bei Wassertemperatur > 22°C (Nährlösungstanks)

## 2. GraphDB-Modellierung

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

### Edges:
```cypher
(:Location)-[:HAS_TANK]->(:Tank)                      // Location besitzt Tank
(:Tank)-[:SUPPLIES]->(:Location)                       // Tank versorgt Location (kann gleiche oder andere sein)
(:Tank)-[:FEEDS_FROM]->(:Tank)                         // Tankkaskade: Reservoir → Nährstofftank
(:Tank)-[:HAS_STATE]->(:TankState)                     // Zeitserie von Zustandsmessungen
(:Tank)-[:HAS_MAINTENANCE]->(:MaintenanceLog)          // Wartungshistorie
(:Tank)-[:HAS_SCHEDULE]->(:MaintenanceSchedule)        // Geplante Wartungsintervalle
(:MaintenanceLog)-[:GENERATED_TASK]->(:Task)           // Verknüpfung zu REQ-006 Tasks
(:MixingResult)-[:MIXED_INTO]->(:Tank)                 // Nährstofflösung aus REQ-004 geht in Tank
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

**4. Locations ohne zugeordneten Tank bei automatischer Bewässerung:**
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

**Szenario 8: Manuelle Zustandserfassung**
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
- Keywords: Tank, Reservoir, Bewässerung, Nährstofflösung, Wasserwechsel, Reinigung, Desinfektion, Kalibrierung, Wartungsplan, Wartungshistorie, Füllstand, Algenrisiko, Rezirkulation, Tankkaskade
- Technische Begriffe: MaintenanceSchedule, TankState, TankType, MaintenanceType, feeds_from, has_tank, supplies, auto_create_task, Celery-Beat
- Verknüpfung: Zentral für REQ-002 (Standort), REQ-004 (Düngung), REQ-005 (Sensorik), REQ-006 (Aufgabenplanung)
