# Spezifikation: REQ-010 - Integriertes Pest Management (IPM)

```yaml
ID: REQ-010
Titel: Integriertes Schädlings- und Krankheitsmanagement (IPM)
Kategorie: Schädlingsmanagement
Fokus: Beides
Technologie: Python, ArangoDB
Status: Entwurf
Version: 1.0
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich Schädlingsbefall und Krankheiten frühzeitig erkennen, präventive Maßnahmen planen und biologische sowie chemische Gegenmaßnahmen dokumentieren, um Ernteausfälle zu minimieren und die Produktqualität zu sichern."

**Beschreibung:** 
Das System implementiert einen mehrstufigen IPM-Ansatz (Integrated Pest Management) mit Fokus auf Prävention, Monitoring und zielgerichteter Intervention. Es berücksichtigt:
- **Präventive Kulturmaßnahmen:** Standorthygiene, Fruchtfolge, resistente Sorten
- **Monitoring-Strategien:** Regelmäßige Inspektionen, Fallen-Systeme, Symptom-Erkennung
- **Biologische Kontrolle:** Nützlingseinsatz, Mikrobiom-Management
- **Chemische Intervention:** Zielgerichteter Einsatz von Pflanzenschutzmitteln mit Karenzzeiten
- **Resistenzmanagement:** Wirkstoff-Rotation, Vermeidung von Überdosierung

Das System unterscheidet zwischen:
- **Pathogenen** (Pilze, Bakterien, Viren)
- **Schädlingen** (Insekten, Milben, Nematoden, Mollusken)
- **Physiologischen Störungen** (Nährstoffmangel, abiotischer Stress)

## 2. ArangoDB-Modellierung

### Document Collections:
- **`pests`** - Schädlingstyp (z.B. Spinnmilbe, Blattlaus, Thripse)
  - Felder: `scientific_name`, `common_name`, `lifecycle_days`, `optimal_temp_range`, `detection_difficulty`
- **`diseases`** - Krankheitserreger (z.B. Echter Mehltau, Botrytis)
  - Felder: `pathogen_type: ['fungal', 'bacterial', 'viral']`, `incubation_period`, `environmental_triggers`
- **`symptoms`** - Visuelles/physisches Anzeichen
  - Felder: `description`, `severity_level`, `affected_plant_part: ['leaf', 'stem', 'root', 'flower']`
- **`treatments`** - Gegenmaßnahme
  - Felder: `type: ['cultural', 'biological', 'chemical', 'mechanical']`, `active_ingredient`, `application_method`, `safety_interval_days`
- **`beneficial_organisms`** - Nützling
  - Felder: `species`, `target_pests`, `release_rate_per_m2`, `establishment_time_days`
- **`inspections`** - Befallskontrolle
  - Felder: `timestamp`, `inspector`, `pressure_level: ['none', 'low', 'medium', 'high', 'critical']`, `photo_refs`
- **`treatment_applications`** - Durchgeführte Maßnahme
  - Felder: `applied_at`, `dosage`, `efficacy_rating`, `weather_conditions`

### Edge Collections:
```aql
// Edge Collection: inspected_by (plant_instances → inspections)
// Edge Collection: detected (inspections → pests / diseases)
// Edge Collection: shows_symptom (pests / diseases → symptoms)
// Edge Collection: treated_with (pests / diseases → treatments)
// Edge Collection: applied_as (treatments → treatment_applications)
// Edge Collection: to_plant (treatment_applications → plant_instances)
// Edge Collection: controls (beneficial_organisms → pests)
// Edge Collection: vulnerable_to (growth_phases → pests / diseases)
// Edge Collection: resistant_to (species → pests / diseases)
// Edge Collection: contraindicated_with (treatments → treatments)  // Inkompatible Wirkstoffe
// Edge Collection: requires_harvest_delay (treatment_applications → harvests, mit {days: int})
```

### AQL-Beispiellogik:

**Befallshistorie eines Standorts:**
```aql
LET cutoff = DATE_SUBTRACT(DATE_NOW(), 90, "days")
FOR slot IN slots
    FILTER slot._key == @slot_id
    FOR plant IN 1..1 INBOUND slot GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['placed_in'] }
        FOR inspection IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['inspected_by'] }
            FILTER inspection.timestamp > cutoff
            FOR pest IN 1..1 OUTBOUND inspection GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['detected'] }
                FILTER IS_SAME_COLLECTION('pests', pest)
                COLLECT pest_name = pest.common_name
                    AGGREGATE occurrences = COUNT(1)
                SORT occurrences DESC
                RETURN { pest_name, occurrences }
```

**Nützlings-Empfehlung basierend auf aktuellem Befall:**
```aql
LET cutoff_7d = DATE_SUBTRACT(DATE_NOW(), 7, "days")
LET cutoff_14d = DATE_SUBTRACT(DATE_NOW(), 14, "days")
FOR plant IN plant_instances
    FOR inspection IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['inspected_by'] }
        FILTER inspection.pressure_level IN ['medium', 'high']
            AND inspection.timestamp > cutoff_7d
        FOR pest IN 1..1 OUTBOUND inspection GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['detected'] }
            FILTER IS_SAME_COLLECTION('pests', pest)
            // Ausschluss: keine chemische Behandlung in letzten 14 Tagen
            LET recent_chemical = (
                FOR ta IN 1..2 OUTBOUND plant GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['treated_with', 'applied_as'] }
                    FILTER IS_SAME_COLLECTION('treatment_applications', ta)
                        AND ta.applied_at > cutoff_14d
                    FOR t IN 1..1 INBOUND ta GRAPH 'kamerplanter_graph'
                        OPTIONS { edgeCollections: ['applied_as'] }
                        FILTER t.type == 'chemical'
                        RETURN t
            )
            FILTER LENGTH(recent_chemical) == 0
            FOR beneficial IN 1..1 INBOUND pest GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['controls'] }
                COLLECT b = beneficial INTO pest_groups
                RETURN DISTINCT {
                    beneficial: b,
                    targets: pest_groups[*].pest.common_name
                }
```

**Karenzzeit-Prüfung vor Ernte:**
```aql
FOR plant IN plant_instances
    FILTER plant._key == @plant_id
    FOR t IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['treated_with'] }
        FOR ta IN 1..1 OUTBOUND t GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['applied_as'] }
            LET safe_until = DATE_ADD(ta.applied_at, t.safety_interval_days, "days")
            FILTER safe_until > DATE_NOW()
            LET days_since = DATE_DIFF(ta.applied_at, DATE_NOW(), "days")
            LET days_remaining = t.safety_interval_days - days_since
            RETURN {
                active_ingredient: t.active_ingredient,
                safety_interval_days: t.safety_interval_days,
                days_since_application: days_since,
                days_remaining: days_remaining
            }
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Inspektions-Scheduler:**
```python
from datetime import datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field

class InspectionSchedule(BaseModel):
    frequency_days: int = Field(ge=1, le=14, description="Inspektionsintervall")
    growth_phase_modifiers: dict[str, float] = Field(
        default={
            "vegetative": 1.0,
            "flowering": 0.5,  # Höhere Frequenz in Blüte
            "harvest": 0.33     # Kritische Phase
        }
    )
    
    def next_inspection_date(
        self, 
        last_inspection: datetime, 
        current_phase: str,
        pest_pressure: Literal['none', 'low', 'medium', 'high', 'critical']
    ) -> datetime:
        """Berechnet dynamisches Inspektionsdatum basierend auf Risikofaktoren"""
        base_interval = self.frequency_days
        phase_multiplier = self.growth_phase_modifiers.get(current_phase, 1.0)
        
        # Erhöhe Frequenz bei aktuellem Befall
        pressure_multipliers = {
            'none': 1.0,
            'low': 0.8,
            'medium': 0.5,
            'high': 0.33,
            'critical': 0.25
        }
        
        adjusted_interval = base_interval * phase_multiplier * pressure_multipliers[pest_pressure]
        return last_inspection + timedelta(days=max(1, int(adjusted_interval)))
```

**2. Resistenzmanagement-Engine:**
```python
from collections import defaultdict
from typing import Optional

class ResistanceManager:
    """Verhindert Resistenzbildung durch Wirkstoff-Rotation"""
    
    MAX_CONSECUTIVE_APPLICATIONS = 3
    ROTATION_WINDOW_DAYS = 90
    
    def __init__(self, db):
        self.db = db  # python-arango StandardDatabase instance

    def validate_treatment(
        self,
        plant_id: str,
        proposed_treatment_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Prüft, ob Behandlung das Resistenzrisiko erhöht
        Returns: (is_valid, warning_message)
        """
        query = """
        LET cutoff = DATE_SUBTRACT(DATE_NOW(), @window, "days")
        FOR plant IN plant_instances
            FILTER plant._key == @plant_id
            FOR t IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['treated_with'] }
                FOR ta IN 1..1 OUTBOUND t GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['applied_as'] }
                    FILTER ta.applied_at > cutoff
                    COLLECT ingredient = t.active_ingredient,
                            mode = t.mode_of_action
                        AGGREGATE applications = COUNT(1)
                    SORT applications DESC
                    RETURN { ingredient, mode, applications }
        """

        cursor = self.db.aql.execute(
            query,
            bind_vars={
                'plant_id': plant_id,
                'window': self.ROTATION_WINDOW_DAYS,
            }
        )
        history = list(cursor)
        
        # Prüfe auf zu häufige Wiederholung desselben Wirkstoffs
        ingredient_counts = defaultdict(int)
        for record in history:
            ingredient_counts[record['ingredient']] += record['applications']
        
        if any(count >= self.MAX_CONSECUTIVE_APPLICATIONS for count in ingredient_counts.values()):
            return False, "RESISTENZWARNUNG: Wirkstoff-Rotation erforderlich"
        
        return True, None
```

**3. Nützlings-Release-Kalkulator:**
```python
from pydantic import BaseModel, field_validator

class BeneficialReleaseCalculation(BaseModel):
    organism_species: str
    target_pest: str
    affected_area_m2: float
    pest_density_per_plant: int
    release_rate_base: float = Field(description="Nützlinge pro m²")

    @field_validator('affected_area_m2')
    @classmethod
    def validate_area(cls, v):
        if v <= 0:
            raise ValueError("Fläche muss positiv sein")
        return v
    
    def calculate_release_quantity(self, infestation_level: Literal['low', 'medium', 'high']) -> dict:
        """Berechnet Ausbringungsmenge basierend on Befallsdruck"""
        multipliers = {'low': 1.0, 'medium': 1.5, 'high': 2.5}
        base_quantity = self.affected_area_m2 * self.release_rate_base
        adjusted_quantity = base_quantity * multipliers[infestation_level]
        
        return {
            'total_organisms': int(adjusted_quantity),
            'distribution_points': max(4, int(self.affected_area_m2 / 2)),
            'organisms_per_point': int(adjusted_quantity / max(4, int(self.affected_area_m2 / 2))),
            'recommended_releases': 2 if infestation_level == 'low' else 3,
            'interval_days': 7
        }
```

**4. Karenzzeit-Validator:**
```python
from datetime import datetime, timedelta

class SafetyIntervalValidator:
    """Prüft Erntefähigkeit unter Berücksichtigung von Pflanzenschutzmittel-Anwendungen"""
    
    @staticmethod
    def can_harvest(
        treatment_applications: list[dict],
        planned_harvest_date: datetime
    ) -> tuple[bool, list[str]]:
        """
        Args:
            treatment_applications: Liste von {applied_at, safety_interval_days, active_ingredient}
        Returns:
            (is_safe, list_of_blocking_treatments)
        """
        blocking_treatments = []
        
        for app in treatment_applications:
            safe_date = app['applied_at'] + timedelta(days=app['safety_interval_days'])
            if safe_date > planned_harvest_date:
                days_remaining = (safe_date - planned_harvest_date).days
                blocking_treatments.append(
                    f"{app['active_ingredient']}: Noch {days_remaining} Tage Karenzzeit"
                )
        
        return len(blocking_treatments) == 0, blocking_treatments
```

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

PestPressureLevel = Literal['none', 'low', 'medium', 'high', 'critical']
TreatmentType = Literal['cultural', 'biological', 'chemical', 'mechanical']
PathogenType = Literal['fungal', 'bacterial', 'viral', 'physiological']

class InspectionRecord(BaseModel):
    plant_id: str
    inspector_id: str
    timestamp: datetime
    pressure_level: PestPressureLevel
    detected_pests: list[str] = Field(default_factory=list)
    detected_diseases: list[str] = Field(default_factory=list)
    symptoms_observed: list[str]
    environmental_conditions: dict[str, float] = Field(
        description="temp_c, humidity_percent, vpd_kpa"
    )
    photo_references: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    
    @field_validator('symptoms_observed')
    @classmethod
    def validate_symptoms(cls, v):
        if not v:
            raise ValueError("Mindestens ein Symptom muss dokumentiert werden")
        return v

class TreatmentProtocol(BaseModel):
    treatment_id: str
    type: TreatmentType
    active_ingredient: Optional[str] = None
    target_organisms: list[str]
    application_method: Literal['spray', 'drench', 'granular', 'release', 'cultural']
    dosage_per_liter: Optional[float] = Field(None, ge=0)
    water_volume_liters: Optional[float] = Field(None, ge=0)
    safety_interval_days: int = Field(default=0, ge=0, le=180)
    application_temperature_range: tuple[float, float] = Field(default=(15.0, 30.0))
    contraindications: list[str] = Field(
        default_factory=list,
        description="Inkompatible Wirkstoffe/Bedingungen"
    )
    protective_equipment_required: list[str] = Field(default_factory=list)
    
    @field_validator('safety_interval_days')
    @classmethod
    def validate_chemical_safety(cls, v, info):
        if info.data.get('type') == 'chemical' and v == 0:
            raise ValueError("Chemische Behandlungen benötigen Karenzzeit")
        return v
```

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Pests (globale Stammdaten) | Nein | Ja | Ja |
| Diseases (globale Stammdaten) | Nein | Ja | Ja |
| Treatments (globale Stammdaten) | Nein | Ja | Ja |
| Inspections (Tenant-scoped) | Mitglied | Mitglied | Admin |
| TreatmentApplications (Tenant-scoped) | Mitglied | Mitglied | Admin |
| Karenz-Status (Tenant-scoped) | Mitglied | — | — |

## 5. Abhängigkeiten

**Erforderliche existierende Collections/Beziehungen:**
- `plant_instances` aus REQ-001 (Stammdatenverwaltung)
- `growth_phases` aus REQ-003 (Phasensteuerung)
- `slots` / `locations` aus REQ-002 (Standortverwaltung)
- `sensors` / `observations` aus REQ-005 (Hybrid-Sensorik) für Umweltbedingungen
- `tasks` aus REQ-006 (Aufgabenplanung) für automatische Inspektions-Tasks
- `harvests` aus REQ-007 (Erntemanagement) für Karenzzeit-Validierung

**Integrationsschnittstellen:**
- **REQ-005 (Sensorik):** Klimadaten (Temp, RLF) als Risikoindikator für Pathogene
- **REQ-003 (Phasen):** Phasenspezifische Vulnerabilitäten (z.B. Blüte anfällig für Botrytis)
- **REQ-006 (Tasks):** Automatische Generierung von Inspektions- und Behandlungs-Tasks
- **REQ-009 (Dashboard):** Alert-Integration bei kritischem Befallsdruck

**Externe Datenquellen (optional):**
- Pflanzenschutzmittel-Datenbank (BVL/EPA) für Zulassungsstatus
- Schädlings-Phänologie-Modelle (Gradtagsummen)

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Pest/Disease-Katalog:** Mindestens 20 häufige Schädlinge und 15 Krankheiten sind im System hinterlegt mit wissenschaftlichen Namen, Symptomen und Behandlungsoptionen
- [ ] **Inspektions-Workflow:** System generiert automatisch Inspektions-Tasks basierend auf Phasen- und Befallsrisiko
- [ ] **Befallsdokumentation:** Inspektionen können mit Fotos, Druckeinschätzung und Symptomen erfasst werden
- [ ] **Behandlungsempfehlung:** System schlägt bei erkanntem Befall passende Treatments vor, sortiert nach IPM-Hierarchie (Kulturmaßnahme > Biologisch > Chemisch)
- [ ] **Resistenzmanagement:** Warnung bei Überschreitung der maximalen Anwendungen desselben Wirkstoffs innerhalb 90 Tagen
- [ ] **Karenzzeit-Enforcement:** Harvest-Tasks werden blockiert, wenn aktive Karenzzeiten bestehen
- [ ] **Nützlings-Kalkulation:** Ausbringungsmengen für biologische Kontrolle werden automatisch berechnet
- [ ] **Chemie-Inkompatibilität:** System verhindert gleichzeitige Anwendung inkompatibler Wirkstoffe
- [ ] **Standort-Historie:** Befallsmuster können pro Slot über mehrere Zyklen analysiert werden
- [ ] **Mobile-Erfassung:** Inspektionen können vor Ort via Mobile-Interface mit Kamera-Upload durchgeführt werden
- [ ] **Alert-System:** Push-Benachrichtigungen bei kritischem Befallsdruck (Schwellenwert konfigurierbar)
- [ ] **Wetter-Integration:** Risiko-Scores für pilzliche Erreger basierend auf RLF/Temperatur (z.B. Mehltau-Warnung bei >80% RLF)
- [ ] **Behandlungs-Tracking:** Efficacy-Rating kann nach Behandlung erfasst werden (Wirksam/Teilweise/Unwirksam)
- [ ] **Batch-Traceability:** Alle Behandlungen sind mit erntefähigen Batches verknüpft (für Seed-to-Shelf-Tracking aus REQ-008)
- [ ] **Prävention-Score:** Dashboard zeigt präventive Gesundheits-Indikatoren (z.B. "Letzte Inspektion vor 5 Tagen, Risiko: Mittel")

### Testszenarien:

**Szenario 1: Früherkennung + Biologische Intervention**
```
GIVEN: PlantInstance in Blütephase mit letzter Inspektion vor 4 Tagen
WHEN: Neue Inspektion erkennt Spinnmilben (Druck: Medium)
THEN: 
  - System schlägt Phytoseiulus persimilis vor
  - Berechnet 500 Nützlinge für 10m² Fläche
  - Warnt vor chemischer Behandlung (würde Nützlinge töten)
  - Generiert Follow-up-Inspektion in 3 Tagen
```

**Szenario 2: Karenzzeit-Blockierung**
```
GIVEN: Pflanze wurde vor 10 Tagen mit Pestizid (Karenzzeit: 21 Tage) behandelt
WHEN: Nutzer versucht, Ernte-Task zu erstellen
THEN:
  - System blockiert Erstellung
  - Zeigt verbleibende 11 Tage bis sicherer Ernte
  - Bietet alternative Termine an
```

**Szenario 3: Resistenz-Prävention**
```
GIVEN: Pflanze wurde 3x mit Pyrethroid behandelt (innerhalb 60 Tagen)
WHEN: Erneuter Thripse-Befall erkannt
THEN:
  - System markiert Pyrethroid als "NICHT EMPFOHLEN - Resistenzrisiko"
  - Schlägt Wirkstoff-Alternative (z.B. Spinosad) vor
  - Dokumentiert Rotations-Historie
```

---

**Hinweise für RAG-Integration:**
- Keywords: IPM, Schädling, Krankheit, Nützling, Karenzzeit, Resistenz, Inspektion, Behandlung
- Verknüpfung: Alle REQ-001 bis REQ-009, besonders REQ-003 (Phasen), REQ-005 (Sensorik), REQ-007 (Ernte)
- Botanische Fachbegriffe: Phytopathologie, Entomologie, Akarizide, Fungizide, Predatoren, Parasitismus
