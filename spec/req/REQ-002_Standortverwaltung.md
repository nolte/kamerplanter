# Spezifikation: REQ-002 - Standortverwaltung

```yaml
ID: REQ-002
Titel: Räumliche Platzierung und Standort-Hierarchie
Kategorie: Infrastruktur
Fokus: Beides
Technologie: Python, ArangoDB
Status: Entwurf
Version: 4.0
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich jede Pflanze einem exakten Platz zuordnen, um Ressourcen präzise zu steuern, Fruchtfolgen einzuhalten und Mikroklimata optimal zu nutzen."

**Beschreibung:**
Das System verwaltet eine **rekursiv verschachtelbare** Standort-Struktur: **Site → Location (beliebig tief) → Slot**. Locations können weitere Locations enthalten (z.B. Haus → Zimmer → Grow Zelt). Slots (Pflanzplätze) sind immer Blatt-Ebene und können an jeder Location-Tiefe angehängt werden.

**Outdoor-Bereich:**
- **Beetflächen** mit GPS-Koordinaten und Himmelsrichtung
- **Freiland-Reihen** mit Pflanzabständen und Wegeplanung
- **Container/Hochbeete** mit mobiler Positionierung

**Indoor-Bereich:**
- **Growzelte** mit Raster-Slot-System und kontrolliertem Klima
- **Hydroponik-Systeme** (NFT, DWC, Aeroponik) mit Nährlösungs-Kreisläufen
- **Vertikale Farmen** mit mehreren Ebenen

**Fruchtfolge-Engine:**
- Tracking der letzten 3-5 Jahre Kulturhistorie pro Standort
- Automatische Warnung bei kritischen Wiederholungen (gleiche Pflanzenfamilie)
- Berücksichtigung von Vor-/Nachfrucht-Effekten und Gründüngung

## 2. ArangoDB-Modellierung

### Nodes:
- **`:Site`** - Oberste Ebene (z.B. Garten, Gewächshaus, Indoor-Facility)
  - Properties:
    - `name: str`
    - `type: Literal['outdoor', 'greenhouse', 'indoor']`
    - `gps_coordinates: Optional[tuple[float, float]]` (Latitude, Longitude)
    - `climate_zone: str` (USDA Hardiness Zone)
    - `total_area_m2: float`
    - `timezone: str` — IANA-Zeitzone (z.B. "Europe/Berlin"), Default: "UTC"

- **`:Location`** - Räumlicher Container (Beet, Zelt, Raum) — rekursiv verschachtelbar
  - Properties:
    - `name: str` (z.B. "Beet A", "Growzelt 1")
    - `site_key: str` — Referenz auf das Root-Site (wird bei Erstellung vom Eltern-Standort geerbt)
    - `parent_location_key: Optional[str]` — Eltern-Location (`null` = direkt unter Site)
    - `location_type_key: str` — Referenz auf `location_types._key` (nutzerpflegbare Stammdaten, siehe Collection unten)
    - `depth: int` — Tiefe in der Hierarchie (0 = direkt unter Site), berechnet
    - `path: str` — Materialisierter Pfad für Baum-Abfragen (z.B. `"haus/arbeitszimmer/growzelt1"`)
    - `area_m2: float`
    - `orientation: Optional[Literal['north', 'south', 'east', 'west']]`
    - `light_type: Literal['natural', 'led', 'hps', 'cmh', 'mixed']`
    - `irrigation_system: Literal['manual', 'drip', 'hydro', 'mist']` (Primäres Bewässerungssystem — beschreibt die Infrastruktur. Ergänzendes manuelles Gießen per Gießkanne ist immer möglich, auch bei automatischen Systemen, z.B. für organische Dünger, die nicht über Tropfer/Pumpen appliziert werden sollten. Siehe REQ-004 Applikationsmethoden und REQ-014 WateringEvent.)
    - `dimensions: tuple[float, float, float]` (length, width, height in meters)
    - `lights_on: Optional[str]` — Uhrzeit Licht-Ein im Format HH:MM (z.B. "06:00")
    - `lights_off: Optional[str]` — Uhrzeit Licht-Aus im Format HH:MM (z.B. "22:00")
    - `use_dynamic_sunrise: bool` — Dynamische Sonnenstandberechnung aus GPS-Koordinaten aktivieren (nur bei `light_type: natural` oder `mixed`)

  **LocationType-Collection (`location_types`):**

  Nutzerpflegbare Stammdaten (CRUD) — analog zu Species/Cultivar. Der Nutzer kann eigene Standort-Typen anlegen (z.B. "Hügelbeet", "Hochbeet", "Frühbeetkasten").

  Document-Collection `location_types`:
  - `_key: str` — Slug-Identifier (z.B. `"garden"`, `"tent"`, `"hugelbeet"`)
  - `name: str` — Anzeigename (z.B. `"Garten"`, `"Grow-Zelt"`, `"Hügelbeet"`)
  - `name_en: Optional[str]` — Englischer Name für i18n
  - `icon: Optional[str]` — MUI-Icon-Name für UI (z.B. `"Park"`, `"Yard"`)
  - `is_indoor: bool` — Unterscheidung indoor/outdoor für kontextabhängige Logik (z.B. Lichtsteuerung)
  - `is_system: bool` — System-Seed vs. nutzerdefiniert (System-Einträge können nicht gelöscht werden)
  - `sort_order: int` — Reihenfolge in Dropdowns
  - `description: Optional[str]` — Kurzbeschreibung
  - `created_at: datetime`
  - `updated_at: datetime`

  **10 Default-Seed-Einträge** (werden bei Erstinstallation angelegt, `is_system: true`):

  | `_key` | `name` | `name_en` | `is_indoor` | `icon` | `sort_order` |
  |--------|--------|-----------|-------------|--------|-------------|
  | `garden` | Garten | Garden | `false` | `Park` | 10 |
  | `greenhouse` | Gewächshaus | Greenhouse | `false` | `Warehouse` | 20 |
  | `building` | Gebäude | Building | `true` | `Home` | 30 |
  | `room` | Zimmer | Room | `true` | `MeetingRoom` | 40 |
  | `balcony` | Balkon | Balcony | `false` | `Balcony` | 50 |
  | `terrace` | Terrasse | Terrace | `false` | `Deck` | 60 |
  | `tent` | Grow-Zelt | Grow Tent | `true` | `Campaign` | 70 |
  | `bed` | Beet | Bed | `false` | `Grass` | 80 |
  | `shelf` | Regal | Shelf | `true` | `Shelves` | 90 |
  | `container` | Topf-/Container-Gruppe | Container Group | `false` | `Inventory2` | 100 |

  > **Hinweis:** `location_type_key` ist ein einfaches String-Feld (Fremdschlüssel) — keine Edge-Collection nötig, da 1:1-Beziehung ohne Graph-Traversal-Bedarf. Konsistent mit `site_key`, `species_key` etc.

- **`:Slot`** - Einzelner Pflanzplatz
  - Properties:
    - `id: str` (Format: "LOCATION_SLOT_NUMBER", z.B. "TENT01_A1")
    - `position: tuple[int, int]` (Grid-Position oder Reihe/Platz)
    - `capacity_plants: int` (1 für Einzelkultur, >1 für Mischkultur)
    - `currently_occupied: bool`
    - `last_sanitization: Optional[datetime]`

### Lichtzeiten-Verwaltung (Sunrise/Sunset)

Das System unterstützt die Verwaltung von Lichtzeiten pro Location. Das Verhalten richtet sich nach dem `light_type`:

| `light_type` | Verhalten |
|---|---|
| `natural` | Dynamische Berechnung aus GPS-Koordinaten + Datum mittels SunCalculator. Optional manueller Override durch `lights_on`/`lights_off`. |
| `led`, `hps`, `cmh` | Nutzer setzt `lights_on` und `lights_off` frei (Kunstlicht-Zeitplan). |
| `mixed` | Nutzer setzt Kunstlicht-Zeiten; natürlicher Sonnenstand wird informativ aus GPS berechnet. |

**SunCalculator:**
- Algorithmus: Astronomische Sonnenstandberechnung basierend auf GPS-Koordinaten (Latitude, Longitude), Datum und Zeitzone
- Eingabe: `latitude: float`, `longitude: float`, `date: date`, `timezone: str` (IANA)
- Ausgabe: `sunrise: time`, `sunset: time`, `dawn: time` (bürgerliche Dämmerung), `dusk: time`, `day_length_hours: float`
- Bibliothek: `astral` (Python, MIT-Lizenz)

**Akzeptanzkriterien:**
- Für `light_type=natural`: Sonnenauf-/untergang wird aus GPS + Datum dynamisch berechnet, falls `use_dynamic_sunrise=true`
- Für `light_type=led/hps/cmh`: Nutzer kann `lights_on` und `lights_off` im Format HH:MM setzen
- Für `light_type=mixed`: Kunstlicht-Zeiten werden gepflegt, Sonnenstand informativ angezeigt
- Der PhotoperiodCalculator verwendet `lights_on` aus dem Standort statt des Hardcodes 06:00
- Site-Zeitzone wird bei Sonnenstandberechnung berücksichtigt

- **`:PlantInstance`** - Konkrete Pflanze (aus REQ-001)
  - Properties:
    - `instance_id: str`
    - `planted_on: date`
    - `removed_on: Optional[date]`

- **`:CropRotationPlan`** - Fruchtfolge-Plan
  - Properties:
    - `season: str` (z.B. "2025_Spring")
    - `planned_families: list[str]`
    - `optimization_goal: Literal['nutrient_balance', 'pest_control', 'soil_health']`

### Edges (ArangoDB Edge Collections):
```
contains:        sites/locations → locations           (Rekursive Verschachtelung)
has_slot:        locations → slots
placed_in:       plant_instances → slots
succeeds:        plant_instances → plant_instances     (Fruchtfolge-Kette, Attribut: interval_days)
follows_plan:    locations → crop_rotation_plans
adjacent_to:     slots → slots                         (Nachbarschafts-Beziehungen, Attribut: distance_cm)
```

**ArangoDB-Graph-Definition für `contains`-Edge:**
```json
{
  "edge_collection": "contains",
  "from_vertex_collections": ["sites", "locations"],
  "to_vertex_collections": ["locations"]
}
```
> **Hinweis:** Die `contains`-Edge-Collection akzeptiert sowohl `sites` als auch `locations` als Ausgangspunkt, um die rekursive Standort-Hierarchie abzubilden.

### AQL-Beispiellogik:

**Fruchtfolge-Historie eines Slots (letzte 3 Jahre):**
```aql
// Alle Pflanzen eines Slots mit Spezies und botanischer Familie
// Zeitfenster: letzte 3 Jahre (1095 Tage)
LET slot = DOCUMENT(CONCAT('slots/', @slot_id))
LET cutoff = DATE_SUBTRACT(DATE_NOW(), 1095, 'day')

FOR plant IN plant_instances
    FOR pi_edge IN placed_in
        FILTER pi_edge._from == plant._id AND pi_edge._to == slot._id
        FILTER plant.planted_on > cutoff
        FOR species_edge IN belongs_to_species
            FILTER species_edge._from == plant._id
            LET species = DOCUMENT(species_edge._to)
            FOR family_edge IN belongs_to_family
                FILTER family_edge._from == species._id
                LET family = DOCUMENT(family_edge._to)
                SORT plant.planted_on DESC
                RETURN {
                    family: family.name,
                    planted: plant.planted_on,
                    harvested: plant.removed_on,
                    species: species.scientific_name
                }
```

**Verfügbare Slots fur neue Anpflanzung finden:**
```aql
// Findet alle Slots einer Location, die nicht belegt sind
FOR loc IN locations
    FILTER loc.location_type_key == @location_type_key
    FOR slot IN 1..1 OUTBOUND loc GRAPH 'kamerplanter_graph'
        FILTER IS_SAME_COLLECTION('has_slot', CURRENT_EDGE)
        // Pruefen ob Slot aktuell belegt ist
        LET is_occupied = LENGTH(
            FOR plant IN plant_instances
                FILTER plant.removed_on == null
                FOR pi_edge IN placed_in
                    FILTER pi_edge._from == plant._id AND pi_edge._to == slot._id
                    RETURN 1
        ) > 0
        FILTER NOT is_occupied
        // Letzten abgeschlossenen Anbau finden
        LET last_plant = FIRST(
            FOR plant IN plant_instances
                FILTER plant.removed_on != null
                FOR pi_edge IN placed_in
                    FILTER pi_edge._from == plant._id AND pi_edge._to == slot._id
                    SORT plant.removed_on DESC
                    LIMIT 1
                    RETURN plant
        )
        LET days_fallow = last_plant != null
            ? DATE_DIFF(last_plant.removed_on, DATE_ISO8601(DATE_NOW()), 'day')
            : null
        SORT days_fallow DESC
        RETURN {
            slot_id: slot._key,
            position: slot.position,
            last_used: last_plant.removed_on,
            days_fallow: days_fallow
        }
```

**Fruchtfolge-Validierung vor Anpflanzung:**
```aql
// Prueft ob die geplante Spezies eine kritische Familien-Wiederholung darstellt
LET slot = DOCUMENT(CONCAT('slots/', @slot_id))
LET cutoff = DATE_SUBTRACT(DATE_NOW(), @rotation_window_days, 'day')

// Vorherige Pflanzen im Rotationsfenster mit ihren Familien
LET previous_families = (
    FOR plant IN plant_instances
        FOR pi_edge IN placed_in
            FILTER pi_edge._from == plant._id AND pi_edge._to == slot._id
            FILTER plant.planted_on > cutoff
            FOR v, e IN 2..2 OUTBOUND plant
                GRAPH 'kamerplanter_graph'
                FILTER IS_SAME_COLLECTION('botanical_families', v)
                RETURN DISTINCT {
                    family_name: v.name,
                    rotation_category: v.rotation_category
                }
)

// Familie der geplanten Spezies
LET new_species = FIRST(
    FOR s IN species
        FILTER s.scientific_name == @new_species_name
        FOR family_edge IN belongs_to_family
            FILTER family_edge._from == s._id
            LET fam = DOCUMENT(family_edge._to)
            RETURN { family_name: fam.name, rotation_category: fam.rotation_category }
)

FOR prev_fam IN previous_families
    RETURN {
        same_family: prev_fam.family_name == new_species.family_name,
        previous_category: prev_fam.rotation_category,
        planned_category: new_species.rotation_category,
        rotation_status: prev_fam.family_name == new_species.family_name
            ? 'CRITICAL'
            : (prev_fam.rotation_category == new_species.rotation_category
                ? 'WARNING'
                : 'OK')
    }
```

**Optimale Mischkultur-Nachbarn finden:**
```aql
// Findet Nachbar-Slots und prueft Kompatibilitaet mit geplanter Spezies
LET target_slot = DOCUMENT(CONCAT('slots/', @slot_id))

FOR neighbor IN 1..1 OUTBOUND target_slot adjacent_to
    // Aktuelle Pflanze im Nachbar-Slot
    FOR neighbor_plant IN plant_instances
        FILTER neighbor_plant.removed_on == null
        FOR pi_edge IN placed_in
            FILTER pi_edge._from == neighbor_plant._id AND pi_edge._to == neighbor._id
            // Spezies der Nachbar-Pflanze
            FOR ns_edge IN belongs_to_species
                FILTER ns_edge._from == neighbor_plant._id
                LET neighbor_species = DOCUMENT(ns_edge._to)
                // Geplante Spezies
                LET planned = FIRST(
                    FOR s IN species FILTER s.scientific_name == @planned_species RETURN s
                )
                // Kompatibilitaet pruefen
                LET compat = FIRST(
                    FOR c IN compatible_with
                        FILTER c._from == planned._id AND c._to == neighbor_species._id
                        RETURN c
                )
                LET incompat = FIRST(
                    FOR i IN incompatible_with
                        FILTER i._from == planned._id AND i._to == neighbor_species._id
                        RETURN i
                )
                RETURN {
                    neighbor_slot_id: neighbor._key,
                    neighbor_plant: neighbor_species.common_names[0],
                    compatibility: compat != null ? compat.compatibility_score : 0,
                    incompatibility_reason: incompat != null ? incompat.reason : null
                }
```

### AQL-Beispielqueries (Rekursive Standort-Hierarchie):

**1. Vollständigen Standort-Baum ab Site laden:**
```aql
// Traversiert den gesamten Baum: Site → Locations (beliebige Tiefe) → Slots
FOR site IN sites
    FILTER site._key == @site_key
    LET tree = (
        FOR v, e, p IN 1..10 OUTBOUND site
            GRAPH 'kamerplanter_graph'
            OPTIONS { order: "bfs", uniqueVertices: "global" }
            FILTER IS_SAME_COLLECTION('contains', e) OR IS_SAME_COLLECTION('has_slot', e)
            RETURN { vertex: v, edge: e, depth: LENGTH(p.edges) }
    )
    RETURN {
        site: site,
        locations: (FOR t IN tree FILTER IS_SAME_COLLECTION('locations', t.vertex) RETURN t),
        slots: (FOR t IN tree FILTER IS_SAME_COLLECTION('slots', t.vertex) RETURN t)
    }
```

**2. Alle Slots eines Standorts inkl. Kind-Standorte:**
```aql
// Findet alle Slots unterhalb einer Location (z.B. alle Plätze im "Arbeitszimmer")
FOR v, e, p IN 1..10 OUTBOUND CONCAT('locations/', @location_key)
    GRAPH 'kamerplanter_graph'
    OPTIONS { uniqueVertices: "global" }
    FILTER IS_SAME_COLLECTION('contains', e) OR IS_SAME_COLLECTION('has_slot', e)
    FILTER IS_SAME_COLLECTION('slots', v)
    RETURN {
        slot: v,
        path_names: (FOR vertex IN p.vertices[* FILTER IS_SAME_COLLECTION('locations', CURRENT)] RETURN vertex.name)
    }
```

**3. Breadcrumb-Pfad eines Standorts auflösen:**
```aql
// Traversiert rückwärts zum Root-Site für Breadcrumb-Navigation
// Ergebnis z.B.: ["Zuhause", "Haus", "Arbeitszimmer", "Grow Zelt 1"]
FOR v, e, p IN 0..10 INBOUND CONCAT('locations/', @location_key)
    GRAPH 'kamerplanter_graph'
    OPTIONS { uniqueVertices: "path" }
    FILTER IS_SAME_COLLECTION('contains', e) OR e == null
    PRUNE IS_SAME_COLLECTION('sites', v)
    RETURN v.name
```

**4. Freie Slots in einem Teilbaum finden:**
```aql
// Findet alle unbelegten Slots unter einem Standort (z.B. freie Plätze im Arbeitszimmer-Bereich)
FOR v, e, p IN 1..10 OUTBOUND CONCAT('locations/', @location_key)
    GRAPH 'kamerplanter_graph'
    OPTIONS { uniqueVertices: "global" }
    FILTER IS_SAME_COLLECTION('slots', v)
    LET is_occupied = LENGTH(
        FOR plant IN plant_instances
            FILTER plant.removed_on == null
            FOR pe IN placed_in
                FILTER pe._from == plant._id AND pe._to == v._id
                RETURN 1
    ) > 0
    FILTER NOT is_occupied
    RETURN {
        slot_id: v._key,
        slot_name: v.id,
        parent_location: LAST(p.vertices[* FILTER IS_SAME_COLLECTION('locations', CURRENT)]).name,
        last_sanitization: v.last_sanitization
    }
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Fruchtfolge-Engine:**
```python
from datetime import datetime, timedelta
from typing import Literal, Optional
from pydantic import BaseModel, Field

class CropRotationValidator(BaseModel):
    """Validiert Fruchtfolge-Konformität vor Anpflanzung"""

    rotation_window_years: int = Field(default=3, ge=1, le=5)
    family_repeat_penalty: float = Field(default=1.0, ge=0, le=1.0)
    nutrient_demand_balance: bool = True

    def validate_planting(
        self,
        slot_id: str,
        planned_species: str,
        previous_crops: list[dict],  # [{family, planted_on, nutrient_demand}]
        db  # python-arango StandardDatabase
    ) -> tuple[bool, str, dict]:
        """
        Returns: (is_valid, message, recommendations)
        """
        window_start = datetime.now() - timedelta(days=365 * self.rotation_window_years)

        # Prüfe auf Familien-Wiederholung
        recent_families = [
            crop['family'] for crop in previous_crops
            if crop['planted_on'] > window_start
        ]

        # Hole Familie der geplanten Spezies (AQL)
        cursor = db.aql.execute("""
            FOR s IN species
                FILTER s.scientific_name == @species_name
                FOR edge IN belongs_to_family
                    FILTER edge._from == s._id
                    LET f = DOCUMENT(edge._to)
                    RETURN { family: f.name, demand: f.typical_nutrient_demand }
        """, bind_vars={'species_name': planned_species})

        result = next(cursor, None)

        if not result:
            return False, "Spezies nicht in Datenbank", {}

        planned_family = result['family']
        planned_demand = result['demand']

        # KRITISCH: Gleiche Familie in Rotation
        if planned_family in recent_families:
            last_occurrence = max([
                crop['planted_on'] for crop in previous_crops
                if crop['family'] == planned_family
            ])
            years_since = (datetime.now() - last_occurrence).days / 365

            return False, (
                f"KRITISCH: {planned_family} wurde vor {years_since:.1f} Jahren "
                f"am gleichen Standort angebaut. Empfohlener Abstand: {self.rotation_window_years} Jahre."
            ), self._get_alternative_families(planned_family, db)

        # WARNUNG: Nährstoff-Ungleichgewicht
        if self.nutrient_demand_balance:
            recent_demands = [crop['nutrient_demand'] for crop in previous_crops[-2:]]
            if all(d == 'heavy' for d in recent_demands) and planned_demand == 'heavy':
                return True, (
                    "WARNUNG: Drei aufeinanderfolgende Starkzehrer. "
                    "Erwäge Gründüngung oder Schwachzehrer."
                ), {}

        return True, "Fruchtfolge OK", {}

    def _get_alternative_families(self, current_family: str, db) -> dict:
        """Schlägt alternative Pflanzenfamilien vor"""
        cursor = db.aql.execute("""
            FOR current IN botanical_families
                FILTER current.name == @family_name
                FOR v, e, p IN 1..2 OUTBOUND current
                    GRAPH 'kamerplanter_graph'
                    FILTER IS_SAME_COLLECTION('rotation_after', e)
                    LIMIT 5
                    RETURN {
                        family: v.name,
                        demand: v.typical_nutrient_demand
                    }
        """, bind_vars={'family_name': current_family})

        return {'alternatives': list(cursor)}
```

**2. Slot-Kapazitäts-Manager:**
```python
from typing import Optional
from pydantic import BaseModel, field_validator

class SlotCapacityCalculator(BaseModel):
    """Berechnet optimale Pflanzendichte basierend on Slot-Dimensionen"""

    slot_area_m2: float = Field(gt=0)
    plant_spacing_cm: int = Field(ge=10, le=200)
    plant_diameter_cm: int = Field(ge=5, le=150)
    cultivation_system: Literal['soil', 'hydro', 'aeroponic', 'vertical']

    @field_validator('plant_spacing_cm')
    @classmethod
    def validate_spacing(cls, v, info):
        plant_diam = info.data.get('plant_diameter_cm', 0)
        if v < plant_diam:
            raise ValueError("Pflanzabstand muss mindestens Pflanzendurchmesser entsprechen")
        return v

    def calculate_capacity(self) -> dict:
        """
        Berechnet maximale Pflanzenanzahl pro Slot
        """
        area_cm2 = self.slot_area_m2 * 10000

        # Effektive Fläche pro Pflanze (Quadratisch angeordnet)
        space_per_plant_cm2 = self.plant_spacing_cm ** 2

        # Basis-Kapazität
        base_capacity = int(area_cm2 / space_per_plant_cm2)

        # System-spezifische Modifikatoren
        system_multipliers = {
            'soil': 1.0,
            'hydro': 1.2,  # Dichtere Bepflanzung möglich
            'aeroponic': 1.3,
            'vertical': 2.5  # Mehrere Ebenen
        }

        adjusted_capacity = int(base_capacity * system_multipliers[self.cultivation_system])

        # Optimalbereich (80-90% der Max-Kapazität für Luftzirkulation)
        optimal_min = int(adjusted_capacity * 0.8)
        optimal_max = int(adjusted_capacity * 0.9)

        return {
            'max_capacity': adjusted_capacity,
            'optimal_range': (optimal_min, optimal_max),
            'spacing_cm': self.plant_spacing_cm,
            'area_per_plant_m2': space_per_plant_cm2 / 10000,
            'cultivation_system': self.cultivation_system
        }
```

**3. Hydro-System-Monitor:**
```python
from datetime import datetime, timedelta

class HydroSystemMonitor(BaseModel):
    """Spezielle Überwachung für hydroponische Systeme"""

    system_type: Literal['dwc', 'nft', 'ebb_flow', 'aeroponics', 'drip']
    reservoir_volume_liters: float
    plant_count: int
    target_ph: float = Field(ge=4.0, le=8.0)
    target_ec_ms: float = Field(ge=0.5, le=3.5)

    def calculate_monitoring_frequency(self, current_phase: str) -> dict:
        """
        Bestimmt Mess-Intervalle basierend auf System-Typ und Phase
        """

        # Basis-Frequenz nach System-Typ
        base_intervals = {
            'dwc': 12,  # Stunden
            'nft': 8,
            'ebb_flow': 12,
            'aeroponics': 4,  # Kritischstes System
            'drip': 24
        }

        base_interval = base_intervals[self.system_type]

        # Phase-spezifische Modifikatoren
        phase_multipliers = {
            'germination': 1.0,
            'seedling': 0.8,  # Häufiger messen
            'vegetative': 1.0,
            'flowering': 0.6,  # Kritische Phase
            'harvest': 1.2
        }

        multiplier = phase_multipliers.get(current_phase, 1.0)
        adjusted_interval = base_interval * multiplier

        # Warnung bei kleinen Reservoirs
        if self.reservoir_volume_liters / self.plant_count < 5:
            adjusted_interval *= 0.5
            warning = "WARNUNG: Reservoir zu klein - erhöhte Instabilität"
        else:
            warning = None

        return {
            'measurement_interval_hours': adjusted_interval,
            'daily_measurements': int(24 / adjusted_interval),
            'warning': warning,
            'parameters': ['pH', 'EC', 'temperature', 'dissolved_oxygen']
        }

    def calculate_solution_change_schedule(
        self,
        last_change: datetime,
        ec_drift: float,
        ph_drift: float
    ) -> dict:
        """Berechnet wann Nährlösung gewechselt werden sollte"""

        # Basis-Wechselintervall nach System
        base_change_days = {
            'dwc': 7,
            'nft': 10,
            'ebb_flow': 14,
            'aeroponics': 7,
            'drip': 21
        }

        days_since_change = (datetime.now() - last_change).days
        scheduled_change_days = base_change_days[self.system_type]

        # Früher wechseln bei Drift
        critical_drift = (abs(ph_drift) > 0.5) or (abs(ec_drift) > 0.3)

        if critical_drift:
            recommended_change = datetime.now()
            reason = "Kritische Parameter-Drift erkannt"
        elif days_since_change >= scheduled_change_days:
            recommended_change = datetime.now()
            reason = "Regulärer Wechsel-Zeitpunkt erreicht"
        else:
            recommended_change = last_change + timedelta(days=scheduled_change_days)
            reason = "Auf Plan"

        return {
            'next_change_date': recommended_change,
            'days_until_change': (recommended_change - datetime.now()).days,
            'reason': reason,
            'current_age_days': days_since_change,
            'max_age_days': scheduled_change_days
        }
```

### Datenvalidierung:
```python
from typing import Literal, Optional, Tuple
from pydantic import BaseModel, field_validator, Field, model_validator
from datetime import date

class LocationTypeDefinition(BaseModel):
    """Nutzerpflegbare Stammdaten für Standort-Typen (CRUD)"""

    name: str = Field(min_length=1, max_length=100, description="Anzeigename (z.B. 'Garten', 'Hügelbeet')")
    name_en: Optional[str] = Field(None, max_length=100, description="Englischer Name für i18n")
    icon: Optional[str] = Field(None, max_length=50, description="MUI-Icon-Name (z.B. 'Park', 'Yard')")
    is_indoor: bool = Field(description="Indoor/Outdoor-Unterscheidung für kontextabhängige Logik")
    is_system: bool = Field(default=False, description="System-Seed (true) vs. nutzerdefiniert (false)")
    sort_order: int = Field(default=0, ge=0, description="Reihenfolge in Dropdowns")
    description: Optional[str] = Field(None, max_length=500)

    # _key wird auto-generiert aus name (slugify) oder manuell gesetzt


MAX_LOCATION_DEPTH = 5  # Empfohlene maximale Verschachtelungstiefe (konfigurierbar, kein harter Fehler)

class LocationDefinition(BaseModel):
    """Definition eines Anbau-Standorts — rekursiv verschachtelbar"""

    name: str = Field(min_length=1, max_length=100)
    site_key: str = Field(description="Referenz auf das Root-Site (geerbt vom Eltern-Standort)")
    parent_location_key: Optional[str] = Field(
        None, description="Eltern-Location (null = direkt unter Site)"
    )
    location_type_key: str = Field(description="Referenz auf location_types._key")
    depth: int = Field(ge=0, description="Tiefe in der Hierarchie (0 = direkt unter Site), berechnet")
    path: str = Field(
        description="Materialisierter Pfad für Baum-Abfragen, z.B. 'haus/arbeitszimmer/growzelt1'"
    )
    area_m2: float = Field(gt=0, le=10000)
    orientation: Optional[Literal['north', 'south', 'east', 'west']] = None
    light_type: Optional[Literal['natural', 'led', 'hps', 'cmh', 'mixed']] = Field(
        None, description="Wenn nicht gesetzt, wird vom Eltern-Standort geerbt (Runtime)"
    )
    irrigation_system: Optional[Literal['manual', 'drip', 'sprinkler', 'hydro', 'sub_irrigation']] = Field(
        None, description="Wenn nicht gesetzt, wird vom Eltern-Standort geerbt (Runtime)"
    )
    dimensions: Optional[Tuple[float, float, float]] = None  # L, W, H in meters
    gps_coordinates: Optional[Tuple[float, float]] = Field(None)
    climate_zone: Optional[str] = Field(None, regex=r'^\d{1,2}[a-b]$')

    @field_validator('gps_coordinates')
    @classmethod
    def validate_coordinates(cls, v):
        if v is not None:
            lat, lon = v
            if not (-90 <= lat <= 90):
                raise ValueError("Latitude muss zwischen -90 und 90 liegen")
            if not (-180 <= lon <= 180):
                raise ValueError("Longitude muss zwischen -180 und 180 liegen")
        return v

    @model_validator(mode='after')
    def validate_depth_warning(self):
        """Warnung bei Überschreitung der empfohlenen Tiefe"""
        if self.depth > MAX_LOCATION_DEPTH:
            import warnings
            warnings.warn(
                f"Verschachtelungstiefe {self.depth} überschreitet Empfehlung von {MAX_LOCATION_DEPTH}"
            )
        return self

class SlotDefinition(BaseModel):
    """Einzelner Pflanzplatz"""

    id: str = Field(regex=r'^[A-Z0-9]+_[A-Z0-9]+$')  # Format: LOCATION_POSITION
    position: Tuple[int, int] = Field(description="Grid-Position (row, col)")
    capacity_plants: int = Field(ge=1, le=20)
    dimensions_cm: Optional[Tuple[int, int, int]] = None  # L, W, H

    @field_validator('id')
    @classmethod
    def validate_slot_format(cls, v):
        if '_' not in v:
            raise ValueError("Slot-ID muss Format LOCATION_POSITION haben")
        return v.upper()

IrrigationSystem = Literal[
    'manual', 'drip', 'sprinkler', 'hydro', 'sub_irrigation',
    'ebb_flow', 'nft', 'aeroponics'
]
```

### API-Endpoints für LocationType-Stammdaten:

```
GET    /api/v1/location-types          — Alle Typen auflisten (sortiert nach sort_order)
POST   /api/v1/location-types          — Neuen Typ anlegen
GET    /api/v1/location-types/{key}    — Einzelnen Typ abrufen
PUT    /api/v1/location-types/{key}    — Typ aktualisieren
DELETE /api/v1/location-types/{key}    — Typ löschen (nur wenn is_system=false UND nicht in Verwendung)
```

**Lösch-Schutz-Validierung:**
```python
def validate_location_type_deletion(location_type_key: str, repository) -> None:
    """Prüft ob ein LocationType gelöscht werden darf."""
    location_type = repository.get_location_type(location_type_key)

    # System-Typen sind geschützt
    if location_type.is_system:
        raise PermissionError("System-Typen können nicht gelöscht werden")  # HTTP 403

    # Referenzielle Integrität prüfen
    usage_count = repository.count_locations_by_type(location_type_key)
    if usage_count > 0:
        raise ConflictError(
            f"Typ wird von {usage_count} Location(s) verwendet"
        )  # HTTP 409
```

### Validierungsregeln (Rekursive Standort-Hierarchie):

**1. Zirkuläre Referenzen verhindern:**
Beim Erstellen oder Updaten einer Location muss sichergestellt werden, dass kein Zyklus entsteht. Der Service traversiert die Eltern-Kette aufwärts und prüft, ob die Ziel-Location bereits im Pfad vorkommt.

```python
def validate_no_circular_reference(location_key: str, new_parent_key: str, repository) -> bool:
    """
    Traversiert die Eltern-Kette von new_parent_key aufwärts.
    Wenn location_key gefunden wird → Zirkularität → Fehler.
    """
    current = new_parent_key
    visited = set()
    while current is not None:
        if current == location_key:
            raise ValueError(f"Zirkuläre Referenz: {location_key} ist bereits Vorfahre von {new_parent_key}")
        if current in visited:
            raise ValueError("Korrupte Hierarchie: Zyklus in Eltern-Kette erkannt")
        visited.add(current)
        parent = repository.get_location(current)
        current = parent.parent_location_key if parent else None
    return True
```

**2. Site-Konsistenz:**
Der `site_key` eines Kind-Standorts muss mit dem `site_key` des Eltern-Standorts übereinstimmen. Wird automatisch beim Erstellen gesetzt:

```python
def resolve_site_key(parent_location_key: Optional[str], explicit_site_key: str, repository) -> str:
    """Stellt sicher, dass site_key mit der Eltern-Kette konsistent ist."""
    if parent_location_key is not None:
        parent = repository.get_location(parent_location_key)
        if parent.site_key != explicit_site_key:
            raise ValueError(
                f"Site-Inkonsistenz: Eltern-Location gehört zu Site '{parent.site_key}', "
                f"aber '{explicit_site_key}' wurde angegeben"
            )
    return explicit_site_key
```

**3. Tiefenlimit (Soft):**
- Empfohlene maximale Tiefe: 5 Ebenen (konfigurierbar via `MAX_LOCATION_DEPTH`)
- Überschreitung erzeugt eine Warnung, keinen harten Fehler
- UI zeigt Hinweis ab Tiefe > `MAX_LOCATION_DEPTH`

**4. Slot-Platzierung:**
- Slots können an jeder Location-Ebene hängen, nicht nur an Blättern
- Ein Raum kann gleichzeitig Slots und Kind-Locations haben

**5. Properties-Vererbung (optional-override Pattern):**
Einige Location-Properties werden vom Eltern-Standort geerbt, wenn nicht explizit gesetzt:
- `light_type`: Grow Zelt erbt von Room, wenn nicht überschrieben
- `irrigation_system`: gleiches Prinzip
- `orientation`: Zimmer erbt von Gebäude

Die Vererbung wird **nicht** in der DB gespeichert, sondern zur Laufzeit im Service-Layer aufgelöst:

```python
def resolve_inherited_property(location: LocationDefinition, prop: str, repository) -> Optional[str]:
    """Löst vererbte Properties auf, indem die Eltern-Kette traversiert wird."""
    current = location
    while current is not None:
        value = getattr(current, prop, None)
        if value is not None:
            return value
        if current.parent_location_key is None:
            break
        current = repository.get_location(current.parent_location_key)
    return None
```

**6. Kaskadierendes Löschen:**
Beim Löschen einer Location werden alle Kind-Locations und deren Slots rekursiv gelöscht. Vor dem Löschen wird geprüft, ob belegte Slots im Teilbaum existieren:

```python
def validate_cascading_delete(location_key: str, repository) -> list[str]:
    """
    Prüft ob der Teilbaum löschbar ist (keine aktiven Pflanzen).
    Gibt Liste aller betroffenen Slot-IDs zurück.
    """
    # AQL: Alle Slots im Teilbaum finden
    affected_slots = repository.find_slots_in_subtree(location_key)
    occupied = [s for s in affected_slots if s.currently_occupied]
    if occupied:
        raise ValueError(
            f"Kann nicht löschen: {len(occupied)} belegte Slots im Teilbaum "
            f"({', '.join(s.id for s in occupied[:3])}...)"
        )
    return [s.id for s in affected_slots]
```

### Beispiel-Daten (Rekursive Standort-Hierarchie):

```
Site: "Zuhause" (indoor, Klimazone 8a, GPS: 52.52°N 13.405°E)
├── Location: "Garten" (location_type_key=garden, depth=0, path="garten")
│   └── Slot: GARTEN_1, GARTEN_2, ...
└── Location: "Haus" (location_type_key=building, depth=0, path="haus")
    ├── Location: "Wohnzimmer" (location_type_key=room, depth=1, path="haus/wohnzimmer")
    ├── Location: "Schlafzimmer" (location_type_key=room, depth=1, path="haus/schlafzimmer")
    └── Location: "Arbeitszimmer" (location_type_key=room, depth=1, path="haus/arbeitszimmer")
        ├── Location: "Grow Zelt 1" (location_type_key=tent, depth=2, path="haus/arbeitszimmer/growzelt1")
        │   dimensions: 120×120×200cm, light_type=led, irrigation_system=manual
        │   ├── Slot: GROWZELT1_1 (pos 0,0)
        │   ├── Slot: GROWZELT1_2 (pos 0,1)
        │   └── Slot: GROWZELT1_3 (pos 1,0)
        └── Location: "Grow Zelt 2" (location_type_key=tent, depth=2, path="haus/arbeitszimmer/growzelt2")
            dimensions: 60×60×160cm, light_type=led, irrigation_system=manual
            ├── Slot: GROWZELT2_1 (pos 0,0)
            └── Slot: GROWZELT2_2 (pos 0,1)
```

**ArangoDB-Dokumente (Auszug):**
```json
// sites collection
{ "_key": "zuhause", "name": "Zuhause", "type": "indoor", "climate_zone": "8a" }

// location_types collection (Seed-Daten, is_system: true)
{ "_key": "garden", "name": "Garten", "name_en": "Garden", "is_indoor": false, "is_system": true, "icon": "Park", "sort_order": 10 }
{ "_key": "greenhouse", "name": "Gewächshaus", "name_en": "Greenhouse", "is_indoor": false, "is_system": true, "icon": "Warehouse", "sort_order": 20 }
{ "_key": "building", "name": "Gebäude", "name_en": "Building", "is_indoor": true, "is_system": true, "icon": "Home", "sort_order": 30 }
{ "_key": "room", "name": "Zimmer", "name_en": "Room", "is_indoor": true, "is_system": true, "icon": "MeetingRoom", "sort_order": 40 }
{ "_key": "balcony", "name": "Balkon", "name_en": "Balcony", "is_indoor": false, "is_system": true, "icon": "Balcony", "sort_order": 50 }
{ "_key": "terrace", "name": "Terrasse", "name_en": "Terrace", "is_indoor": false, "is_system": true, "icon": "Deck", "sort_order": 60 }
{ "_key": "tent", "name": "Grow-Zelt", "name_en": "Grow Tent", "is_indoor": true, "is_system": true, "icon": "Campaign", "sort_order": 70 }
{ "_key": "bed", "name": "Beet", "name_en": "Bed", "is_indoor": false, "is_system": true, "icon": "Grass", "sort_order": 80 }
{ "_key": "shelf", "name": "Regal", "name_en": "Shelf", "is_indoor": true, "is_system": true, "icon": "Shelves", "sort_order": 90 }
{ "_key": "container", "name": "Topf-/Container-Gruppe", "name_en": "Container Group", "is_indoor": false, "is_system": true, "icon": "Inventory2", "sort_order": 100 }

// locations collection
{ "_key": "garten", "name": "Garten", "site_key": "zuhause", "parent_location_key": null, "location_type_key": "garden", "depth": 0, "path": "garten" }
{ "_key": "haus", "name": "Haus", "site_key": "zuhause", "parent_location_key": null, "location_type_key": "building", "depth": 0, "path": "haus" }
{ "_key": "arbeitszimmer", "name": "Arbeitszimmer", "site_key": "zuhause", "parent_location_key": "haus", "location_type_key": "room", "depth": 1, "path": "haus/arbeitszimmer" }
{ "_key": "growzelt1", "name": "Grow Zelt 1", "site_key": "zuhause", "parent_location_key": "arbeitszimmer", "location_type_key": "tent", "depth": 2, "path": "haus/arbeitszimmer/growzelt1", "dimensions": [1.2, 1.2, 2.0], "light_type": "led", "irrigation_system": "manual" }
{ "_key": "growzelt2", "name": "Grow Zelt 2", "site_key": "zuhause", "parent_location_key": "arbeitszimmer", "location_type_key": "tent", "depth": 2, "path": "haus/arbeitszimmer/growzelt2", "dimensions": [0.6, 0.6, 1.6], "light_type": "led", "irrigation_system": "manual" }

// contains edge collection
{ "_from": "sites/zuhause", "_to": "locations/garten" }
{ "_from": "sites/zuhause", "_to": "locations/haus" }
{ "_from": "locations/haus", "_to": "locations/arbeitszimmer" }
{ "_from": "locations/arbeitszimmer", "_to": "locations/growzelt1" }
{ "_from": "locations/arbeitszimmer", "_to": "locations/growzelt2" }

// has_slot edge collection
{ "_from": "locations/growzelt1", "_to": "slots/GROWZELT1_1" }
{ "_from": "locations/growzelt1", "_to": "slots/GROWZELT1_2" }
{ "_from": "locations/growzelt1", "_to": "slots/GROWZELT1_3" }
{ "_from": "locations/growzelt2", "_to": "slots/GROWZELT2_1" }
{ "_from": "locations/growzelt2", "_to": "slots/GROWZELT2_2" }
```

## 4. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 (Stammdaten): Species und BotanicalFamily für Fruchtfolge
- ArangoDB Geo-Index für räumliche Queries bei GPS-Koordinaten

**Wird benötigt von:**
- REQ-019 (Substrat): Slot-Zuordnung via `filled_with`-Edge
- REQ-003 (Phasen): Slot-Belegung für Ressourcen-Zuweisung
- REQ-004 (Düngung): Location-Kontext für Düngeereignisse
- REQ-005 (Sensorik): Slot-Position für Sensor-Zuordnung
- REQ-006 (Tasks): Standort-spezifische Aufgaben
- REQ-010 (IPM): Standort-Historie für Schädlings-Muster
- REQ-014 (Tankmanagement): **HOCH** — Location für Tank-Zuordnung, `irrigation_system` für Pflicht-Validierung

## 5. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Hierarchische Struktur:** Site → Location (rekursiv) → Slot voll implementiert
- [ ] **Rekursive Location-Hierarchie:** Location unterstützt beliebige Verschachtelungstiefe via `parent_location_key`
- [ ] **Zirkularitäts-Prüfung:** Zirkuläre Referenzen werden beim Erstellen/Updaten verhindert
- [ ] **Site-Konsistenz:** `site_key` wird automatisch vom Eltern-Standort geerbt und validiert
- [ ] **Standort-Baum:** Vollständiger Standort-Baum per AQL-Graph-Traversal ladbar
- [ ] **Teilbaum-Slots:** Alle Slots eines Teilbaums effizient abfragbar
- [ ] **Breadcrumb-Pfad:** Breadcrumb-Pfad für jeden Standort generierbar
- [ ] **LocationType-CRUD:** Nutzer kann eigene Standort-Typen anlegen, bearbeiten und löschen
- [ ] **LocationType-System-Seed:** 10 vordefinierte Typen (garden, greenhouse, building, room, balcony, terrace, tent, bed, shelf, container) werden bei Erstinstallation als `is_system=true` angelegt
- [ ] **LocationType-Lösch-Schutz:** System-Typen (`is_system=true`) können nicht gelöscht werden (HTTP 403)
- [ ] **LocationType-Referenzielle Integrität:** Typen, die von Locations referenziert werden, können nicht gelöscht werden (HTTP 409)
- [ ] **LocationType-Dropdown:** LocationType-Dropdown im Create/Edit-Dialog zeigt alle verfügbaren Typen (sortiert nach `sort_order`)
- [ ] **LocationType-Indoor/Outdoor:** Typ-Eigenschaft `is_indoor` steuert kontextabhängige UI-Logik (z.B. Lichtsteuerung)
- [ ] **Kaskadierendes Löschen:** Funktioniert über beliebige Verschachtelungstiefe mit Prüfung auf belegte Slots
- [ ] **Properties-Vererbung:** `light_type`, `irrigation_system`, `orientation` werden bei Bedarf vom Eltern-Standort geerbt
- [ ] **Slot-ID-Generierung:** Automatische Generierung eindeutiger IDs nach Schema
- [ ] **Fruchtfolge-Validierung:** 3-Jahres-Historie wird bei Anpflanzung geprüft
- [ ] **Kapazitätsberechnung:** Automatische Berechnung optimaler Pflanzendichte
- [ ] **Hydro-Monitoring:** Spezielle Überwachungslogik für NFT, DWC, Aero-Systeme
- [ ] **Nachbarschafts-Graph:** ADJACENT_TO-Beziehungen für Mischkultur-Analyse
- [ ] **GPS-Integration:** Outdoor-Beete mit Koordinaten für Sonnenstand-Berechnung
- [ ] **Slot-Verfügbarkeit:** Echtzeit-Status "belegt/frei" mit Last-Used-Datum
- [ ] **Sanitärungs-Tracking:** Letzte Desinfektion pro Slot dokumentiert
- [ ] **Mischkultur-Planer:** Kompatibilitäts-Check mit benachbarten Slots
- [ ] **Vertical-Farming:** Support für mehrere Ebenen (z-Koordinate)
- [ ] **Mobile-Erfassung:** QR-Codes für Slots zur schnellen Identifikation

### Testszenarien:

**Szenario 1: Fruchtfolge-Kritische Wiederholung**
```
GIVEN: Slot "BEET_A_ROW1" hatte 2023 Tomaten, 2024 Paprika (beide Solanaceae)
WHEN: Nutzer plant Aubergine (Solanaceae) für 2025
THEN:
  - System blockiert Anpflanzung
  - Zeigt Warnung: "KRITISCH: Solanaceae 3 Jahre in Folge"
  - Schlägt Alternativen vor: Fabaceae (Bohnen), Brassicaceae (Kohl)
```

**Szenario 2: Hydroponik Parameter-Drift**
```
GIVEN: DWC-System, letzte Messung pH 5.8, aktuelle Messung pH 7.2
WHEN: System berechnet Monitoring-Frequenz
THEN:
  - Empfohlene Nährlösungs-Wechsel: SOFORT
  - Messfrequenz erhöht auf 4h (statt 12h)
  - Alert: "Kritische pH-Drift: +1.4 Einheiten"
```

**Szenario 3: Kapazitäts-Optimierung**
```
GIVEN: Growzelt 120x120cm, Cannabis, 30cm Pflanzabstand
WHEN: System berechnet optimale Belegung
THEN:
  - Max Kapazität: 16 Pflanzen (4x4 Grid)
  - Optimal: 12-14 Pflanzen (für Luftzirkulation)
  - Warnung wenn >14: "Überbelegung erhöht Schimmel-Risiko"
```

**Szenario 4: 5-Ebenen-Standort-Hierarchie**
```
GIVEN: Site "Zuhause" mit verschachtelter Struktur:
       Zuhause > Haus > Arbeitszimmer > Grow Zelt 1 > (Slots)
WHEN: Nutzer lädt den vollständigen Standort-Baum für "Zuhause"
THEN:
  - Baum enthält alle 5 Ebenen (Site + 4 Location-Ebenen + Slots)
  - Jeder Standort hat korrekten depth-Wert (Haus=0, Arbeitszimmer=1, Grow Zelt=2)
  - Materialisierte Pfade stimmen (z.B. "haus/arbeitszimmer/growzelt1")
  - Alle Slots unter Grow Zelt 1 und 2 sind im Ergebnis enthalten
```

**Szenario 5: Zirkuläre Referenz verhindern**
```
GIVEN: Location "Arbeitszimmer" (parent: "Haus"), Location "Haus" (parent: null)
WHEN: Nutzer versucht "Haus" als Kind von "Arbeitszimmer" zu setzen
       (parent_location_key von "Haus" → "Arbeitszimmer")
THEN:
  - System lehnt die Änderung ab
  - Fehlermeldung: "Zirkuläre Referenz: 'Haus' ist bereits Vorfahre von 'Arbeitszimmer'"
  - Bestehende Hierarchie bleibt unverändert
```

**Szenario 6: Teilbaum-Slot-Abfrage**
```
GIVEN: "Arbeitszimmer" enthält "Grow Zelt 1" (3 Slots) und "Grow Zelt 2" (2 Slots)
       Slot GROWZELT1_1 ist belegt, alle anderen frei
WHEN: Nutzer sucht freie Slots unter "Arbeitszimmer"
THEN:
  - Ergebnis enthält 4 freie Slots (GROWZELT1_2, GROWZELT1_3, GROWZELT2_1, GROWZELT2_2)
  - GROWZELT1_1 wird nicht angezeigt (belegt)
  - Jeder Slot zeigt seinen Eltern-Standort-Namen (z.B. "Grow Zelt 1")
```

**Szenario 7: Kaskadierendes Löschen mit Belegungs-Check**
```
GIVEN: "Arbeitszimmer" mit 2 Kind-Locations (Grow Zelte) und 5 Slots insgesamt
       Slot GROWZELT1_1 ist belegt (aktive Pflanze)
WHEN: Nutzer versucht "Arbeitszimmer" zu löschen
THEN:
  - System blockiert das Löschen
  - Fehlermeldung: "Kann nicht löschen: 1 belegter Slot im Teilbaum (GROWZELT1_1)"
  - Keine Daten werden gelöscht
```

---

**Hinweise für RAG-Integration:**
- Keywords: Standort, Slot, Fruchtfolge, Hydroponik, Kapazität, Rotation, Hierarchie, Verschachtelung, LocationType, location_types, Stammdaten, CRUD, Teilbaum, Breadcrumb
- Technische Begriffe: ArangoDB Geo-Index, GPS-Koordinaten, NFT, DWC, Aeroponik, EC-Drift, Graph-Traversal, AQL, materialisierter Pfad, kaskadierendes Löschen
- Verknüpfung: Zentral für REQ-019, REQ-003, REQ-004, REQ-005, REQ-010, REQ-014
