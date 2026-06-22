# Spezifikation: REQ-010 - Integriertes Pest Management (IPM)

```yaml
ID: REQ-010
Titel: Integriertes Schädlings- und Krankheitsmanagement (IPM)
Kategorie: Schädlingsmanagement
Fokus: Beides
Technologie: Python, ArangoDB
Status: Entwurf
Version: 1.4 (Nutzer-beigesteuerte Schädlings-Referenzbilder: Upload/Kamera, Freigabe, Erkennung)
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.4 | 2026-06-21 | **Nutzer-beigesteuerte Schädling-Referenzbilder:** Nutzer können eigene Fotos zu einem Schädling beitragen — per Datei-Upload oder Kamera (`ImageCapturePanel`). Neues Modell `PestImageContribution` (Collection `pest_image_contributions`, tenant-scoped) + Bilder als echte Attachments via `AttachmentService` (EXIF-Strip, Virus-Scan, Magic-Byte, SHA-256-Dedup; `AttachmentCategory.PEST_REFERENCE`). **Phase 1 (privat):** Endpoints `POST/GET/DELETE /api/v1/t/{slug}/ipm/pests/{key}/images`; eigene Bilder sofort in der privaten Galerie sichtbar/löschbar; strikte Tenant-Isolation; Light-Modus blockiert. **Phase 2 (Freigabe/global/Erkennung):** `status` (private/promoted); Admin-Moderation `GET/PATCH /api/v1/admin/pests/{key}/contributions` (Platform-Admin, cross-tenant); globaler read-only Content-Endpoint `GET /api/v1/ipm/pest-images/{id}[/thumbnails/{size}]` liefert NUR `promoted` (sonst 404) — tenant-Liste zeigt eigene + fremde promoted; bei Freigabe wird das Bild als Few-Shot-Referenz (`source=user_contributed`) in den Erkennungs-Index (REQ-044 inference-service) aufgenommen. **DSGVO:** `pest_image_contributions` + `pest_reference`-Attachments im ErasureEngine (Tenant- und User-Löschung). |
| 1.3 | 2026-06-21 | **Behandlungs-Detailseite + durchgängig mehrsprachige IPM-Inhalte:** `treatments`-Stammdaten mehrsprachig (Muster `name`/`name_de` über `useLocalizedField`; `name` bleibt englischer Edge-Schlüssel) und detailliert — neue Feldpaare `description(_de)`, `how_to_apply(_de)` (Anwendung), `mode_of_action(_de)` (Wirkweise), `precautions(_de)` (Sicherheitshinweise). Neuer aggregierter Endpoint `GET /ipm/treatments/{key}/detail` (Maßnahme + behandelte Schädlinge/Krankheiten via Reverse-`targets_pest`/`targets_disease`-Edges, dedupliziert). Frontend-Detailseite `pflanzenschutz/treatments/:key`, verlinkt aus der Behandlungs-Liste und aus den Gegenmaßnahmen der Schädlings-Detailseite. Alle 40 Treatment-Seeds in `ipm.yaml` vollständig DE+EN. **Auch die `pests`-Profil-Freitextfelder mehrsprachig** (`damage_symptoms(_de)`, `host_plants(_de)`, `prevention_tips(_de)`, `monitoring_hints(_de)`; Basis = EN, `_de` = Deutsch) sowie **`common_name(_de)`** (deutscher Name für Titel/Liste/Chips). **Gegenmaßnahmen auf der Schädlings-Detailseite zeigen je eine kurze, lokalisierte Wirkbeschreibung** (description/mode_of_action) statt nur des Namens. **Alle 33 Schädlinge im Seed** mit `common_name_de` versehen und mit vollständigen mehrsprachigen Detaildaten angereichert (Schadbild, Pflanzenteile, Wirtspflanzen, Prävention, Monitoring, Schweregrad). Alle neuen Felder optional → abwärtskompatibel. |
| 1.2 | 2026-06-21 | **Schädlings-Detailseite:** `pests`-Stammdaten um Detailfelder erweitert (`damage_symptoms`, `affected_plant_parts`, `host_plants`, `prevention_tips`, `monitoring_hints`, `severity`, `optimal_humidity_min/max`, `reference_image_refs`) sowie `detection_slug` als Brücke zur Erkennungs-Taxonomie (REQ-044 `PestTaxon.slug`). Neuer aggregierter Endpoint `GET /ipm/pests/{key}/detail` (Stammdaten + Gegenmaßnahmen nach IPM-Hierarchie + passende Nützlinge + Schadbild-Hinweis). Frontend-Detailseite `pflanzenschutz/pests/:key`, verlinkt aus der Schädlings-Liste und dem Erkennungs-Dialog (REQ-044). Kuratierte Referenzbilder via Admin-Upload (Object-Storage, NFR-013); Galerie anfangs leer. Alle neuen Felder optional → abwärtskompatibel zu bestehenden Seeds. |
| 1.1 | 2026-04-27 | **ADR-001 (W-009 Karenz-Detach):** `to_plant`-Edge um Snapshot-Felder `inherited_from_run` + `inherited_at` erweitert. `SafetyIntervalValidator.collect_relevant_treatments()` ergänzt — sammelt direkte, run-aktive und geerbte Treatments und dedupliziert über `_key` (Re-attach-sicher). AQL-Lookup im Repository-Layer dokumentiert. |
| 1.0 | (vorher) | Erstversion. |

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
- **Hermaphrodismus** (Nanners, Pollensäcke, gemischte Formen) — mit Sofortmaßnahmen-Protokoll und genetischer Rückverfolgung <!-- Quelle: Cannabis Indoor Grower Review G-010 -->

## 2. ArangoDB-Modellierung

### Document Collections:
- **`pests`** - Schädlingstyp (z.B. Spinnmilbe, Blattlaus, Thripse)
  - Felder: `scientific_name`, `common_name`, `lifecycle_days`, `optimal_temp_range`, `detection_difficulty`
  - **Detailseiten-Felder (v1.2, alle optional):** `damage_symptoms` (Schadbild-Beschreibung), `affected_plant_parts` (`leaf`|`stem`|`root`|`flower`|`fruit`), `host_plants`, `prevention_tips`, `monitoring_hints`, `severity` (`low`|`medium`|`high`), `optimal_humidity_min`/`optimal_humidity_max`, `reference_image_refs` (kuratierte Referenzbilder als Object-Storage-Refs, NFR-013), `detection_slug` (Brücke zur REQ-044-Erkennungs-Taxonomie `PestTaxon.slug` — verknüpft den Stammdatensatz mit der Bilderkennungs-Klasse für Schadbild-Hinweis und Nützlings-Lookup)
    - **v1.3 mehrsprachig:** die Freitextfelder `damage_symptoms`, `host_plants`, `prevention_tips`, `monitoring_hints` (sowie `description`) haben `_de`-Varianten (Basisfeld = EN-Fallback, `_de` = Deutsch; Anzeige über `useLocalizedField`).
- **`diseases`** - Krankheitserreger (z.B. Echter Mehltau, Botrytis)
  - Felder: `pathogen_type: ['fungal', 'bacterial', 'viral']`, `incubation_period`, `environmental_triggers`
- **`symptoms`** - Visuelles/physisches Anzeichen
  - Felder: `description`, `severity_level`, `affected_plant_part: ['leaf', 'stem', 'root', 'flower']`
- **`treatments`** - Gegenmaßnahme
  - Felder: `type: ['cultural', 'biological', 'chemical', 'mechanical']`, `active_ingredient`, `application_method`, `safety_interval_days`
  - **Mehrsprachig + Detailseiten-Felder (v1.3, alle optional):** `name` (englisch, stabiler Edge-Schlüssel) + `name_de` (deutsche Anzeige); `description(_de)`, `how_to_apply(_de)` (Anwendung), `mode_of_action(_de)` (Wirkweise), `precautions(_de)` (Sicherheits-/Vorsichtshinweise). Anzeige-Sprachwahl im Frontend über `useLocalizedField` (DE → `_de`, sonst englisches Basisfeld als Fallback). Inhalte vollständig seed-getrieben (`ipm.yaml`).
- **`beneficial_organisms`** - Nützling
  - Felder: `species`, `target_pests`, `release_rate_per_m2`, `establishment_time_days`
- **`inspections`** - Befallskontrolle
  - Felder: `timestamp`, `inspector`, `pressure_level: ['none', 'low', 'medium', 'high', 'critical']`, `photo_refs`
- **`treatment_applications`** - Durchgeführte Maßnahme
  - Felder: `applied_at`, `dosage`, `efficacy_rating`, `weather_conditions`
<!-- Quelle: Cannabis Indoor Grower Review G-010 -->
- **`hermaphroditism_findings`** - Hermaphrodismus-Befund
  - Felder: `finding_type: ['nanners', 'pollen_sacs', 'mixed']`, `severity: ['isolated', 'spreading', 'critical']`, `location_on_plant` (z.B. obere Cola, untere Seitentriebe), `estimated_pollen_release: bool`, `stress_correlation: ['light_leak', 'heat_stress', 'overfeeding', 'training_stress', 'genetic', 'unknown']`, `immediate_action_taken: ['nanners_removed', 'plant_isolated', 'plant_removed', 'monitoring_increased']`, `photo_refs`, `notes`
- **`pollination_checks`** - Bestäubungs-Check nach Hermie-Befund
  - Felder: `timestamp`, `inspector`, `check_type: ['visual', 'calyx_squeeze', 'seed_search']`, `pollination_detected: bool`, `affected_plants: list[str]`, `seed_count_estimate: int`, `calyx_swelling_without_trichome_maturity: bool`, `notes`

### Edge Collections:
```aql
// Edge Collection: inspected_by (planting_runs|plant_instances → inspections)  // Dual-Support (REQ-013 v2.0)
// Edge Collection: detected (inspections → pests / diseases)
// Edge Collection: shows_symptom (pests / diseases → symptoms)
// Edge Collection: treated_with (pests / diseases → treatments)
// Edge Collection: applied_as (treatments → treatment_applications)
// Edge Collection: to_run (treatment_applications → planting_runs)            // REQ-013 v2.0: Run-Level (ex to_plant)
// Edge Collection: to_plant (treatment_applications → plant_instances)        // ADR-001: Direkt-Behandlung (standalone) ODER Snapshot beim Detach
//   Properties (für Snapshot, ADR-001):
//     - inherited_from_run: Optional[str]   // Run-Key, aus dem die Behandlung beim Detach geerbt wurde; null = Direkt-Behandlung
//     - inherited_at: Optional[datetime]    // Zeitpunkt des Detach (kopiert von run_contains.detached_at)
// Edge Collection: controls (beneficial_organisms → pests)
// Edge Collection: vulnerable_to (growth_phases → pests / diseases)
// Edge Collection: resistant_to (species → pests / diseases)
// Edge Collection: contraindicated_with (treatments → treatments)  // Inkompatible Wirkstoffe
// Edge Collection: requires_harvest_delay (treatment_applications → harvests, mit {days: int})
// --- Hermaphrodismus-Edges (Quelle: Cannabis Indoor Grower Review G-010) ---
// Edge Collection: hermaphroditism_found_at (inspections → hermaphroditism_findings)
// Edge Collection: hermie_on_plant (hermaphroditism_findings → plant_instances)
// Edge Collection: stress_caused_by (hermaphroditism_findings → sensor_observations / manual_events)  // Korrelation zu Stress-Events
// Edge Collection: hermie_prone_cultivar (hermaphroditism_findings → cultivars, mit {confirmed_at, stress_context})  // Genetische Markierung
// Edge Collection: pollination_check_for (pollination_checks → hermaphroditism_findings)  // Nachkontrolle
// Edge Collection: pollination_affected (pollination_checks → plant_instances)  // Betroffene Nachbarpflanzen
```

### AQL-Beispiellogik:

**Befallshistorie eines Standorts:**
```aql
LET cutoff = DATE_SUBTRACT(DATE_NOW(), 90, "days")
FOR slot IN slots
    FILTER slot._key == @slot_id
    // Dual-Support: Inspections liegen auf Runs oder standalone Plants
    FOR plant IN 1..1 INBOUND slot GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['placed_in'] }
        // Pflanze im Run? → Inspection ueber Run. Standalone? → direkt.
        LET run = FIRST(FOR r, e IN 1..1 INBOUND plant run_contains FILTER e.detached_at == null RETURN r)
        LET entity = run != null ? run : plant
        FOR inspection IN 1..1 OUTBOUND entity GRAPH 'kamerplanter_graph'
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
// Dual-Support (REQ-013 v2.0): Ueber Runs + standalone Plants
FOR entity IN UNION_DISTINCT(
    (FOR r IN planting_runs FILTER r.status IN ['active', 'harvesting'] RETURN r),
    (FOR p IN plant_instances FILTER p.removed_on == null
        LET in_run = LENGTH(FOR run, e IN 1..1 INBOUND p run_contains FILTER e.detached_at == null RETURN 1)
        FILTER in_run == 0 RETURN p)
)
    FOR inspection IN 1..1 OUTBOUND entity GRAPH 'kamerplanter_graph'
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

<!-- Quelle: Cannabis Indoor Grower Review G-010 -->
**Hermaphrodismus-Historie eines Cultivars (Hermie-Prone-Check):**
```aql
FOR cultivar IN cultivars
    FILTER cultivar._key == @cultivar_id
    FOR finding IN 1..1 INBOUND cultivar GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['hermie_prone_cultivar'] }
        FOR plant IN 1..1 OUTBOUND finding GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['hermie_on_plant'] }
            FOR run IN 1..1 INBOUND plant GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['contains_plant'] }
                COLLECT severity = finding.severity,
                        stress = finding.stress_correlation
                    AGGREGATE occurrences = COUNT(1)
                SORT occurrences DESC
                RETURN {
                    severity,
                    stress_correlation: stress,
                    occurrences,
                    recommendation: severity == 'critical'
                        ? "WARNUNG: Cultivar zeigt wiederholten schweren Hermaphrodismus"
                        : "Erhöhte Überwachung empfohlen"
                }
```

**Bestäubungs-Risiko nach Hermie-Befund (Nachbarpflanzen im selben Slot/Location):**
```aql
FOR finding IN hermaphroditism_findings
    FILTER finding._key == @finding_id
    FOR plant IN 1..1 OUTBOUND finding GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['hermie_on_plant'] }
        FOR slot IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['placed_in'] }
            FOR neighbor IN 1..1 INBOUND slot GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['placed_in'] }
                FILTER neighbor._key != plant._key
                LET has_check = (
                    FOR check IN 1..1 INBOUND neighbor GRAPH 'kamerplanter_graph'
                        OPTIONS { edgeCollections: ['pollination_affected'] }
                        RETURN check
                )
                RETURN {
                    plant_id: neighbor._key,
                    plant_name: neighbor.name,
                    pollination_check_done: LENGTH(has_check) > 0,
                    needs_inspection: LENGTH(has_check) == 0
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

<!-- Quelle: Cannabis Indoor Grower Review G-010 -->
**4. Hermaphrodismus-Protokoll-Engine:**
```python
from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime

HermieFindingType = Literal['nanners', 'pollen_sacs', 'mixed']
HermieSeverity = Literal['isolated', 'spreading', 'critical']
HermieStressCorrelation = Literal[
    'light_leak', 'heat_stress', 'overfeeding', 'training_stress', 'genetic', 'unknown'
]
HermieImmediateAction = Literal[
    'nanners_removed', 'plant_isolated', 'plant_removed', 'monitoring_increased'
]

class HermaphroditismFinding(BaseModel):
    """Befund-Modell für Hermaphrodismus-Erkennung"""
    plant_id: str
    inspection_id: str
    finding_type: HermieFindingType
    severity: HermieSeverity
    location_on_plant: str = Field(description="z.B. 'obere Cola', 'untere Seitentriebe'")
    estimated_pollen_release: bool = False
    stress_correlation: HermieStressCorrelation = 'unknown'
    immediate_action_taken: HermieImmediateAction
    photo_references: list[str] = Field(default_factory=list)
    notes: Optional[str] = None

class PollinationCheck(BaseModel):
    """Bestäubungs-Check für Nachbarpflanzen nach Hermie-Befund"""
    hermaphroditism_finding_id: str
    inspector_id: str
    timestamp: datetime
    check_type: Literal['visual', 'calyx_squeeze', 'seed_search']
    pollination_detected: bool = False
    affected_plant_ids: list[str] = Field(default_factory=list)
    seed_count_estimate: int = Field(default=0, ge=0)
    calyx_swelling_without_trichome_maturity: bool = False
    notes: Optional[str] = None


# Sofortmaßnahmen-Protokoll nach Schweregrad
HERMIE_RESPONSE_PROTOCOL: dict[HermieSeverity, dict] = {
    'isolated': {
        'description': 'Einzelne Nanners, lokal entfernbar',
        'immediate_actions': [
            'Nanners vorsichtig mit Pinzette entfernen (nicht schütteln!)',
            'Betroffene Stelle mit Wasser besprühen (Pollen deaktivieren)',
            'Foto-Dokumentation der Stelle',
        ],
        'follow_up': [
            'Tägliche Kontrolle der betroffenen Pflanze für 7 Tage',
            'Inspektionsintervall für gesamten Run auf 1 Tag reduzieren',
            'Stress-Ursache identifizieren und beheben',
        ],
        'plant_action': 'keep_with_monitoring',
        'inspection_interval_days': 1,
    },
    'spreading': {
        'description': 'Mehrere Stellen betroffen, Pflanze gefährdet',
        'immediate_actions': [
            'Pflanze sofort isolieren (separater Raum/Zelt)',
            'Alle sichtbaren Nanners/Pollensäcke entfernen',
            'Nachbarpflanzen auf Pollenspuren untersuchen',
            'Foto-Dokumentation aller betroffenen Stellen',
        ],
        'follow_up': [
            'Tägliche Kontrolle der isolierten Pflanze',
            'Bestäubungs-Check aller Pflanzen im selben Raum',
            'Entscheidung: Pflanze behalten (isoliert) oder entfernen',
            'Cultivar als hermie_prone markieren',
        ],
        'plant_action': 'isolate',
        'inspection_interval_days': 1,
    },
    'critical': {
        'description': 'Massive Bestäubungsgefahr, Pflanze sofort entfernen',
        'immediate_actions': [
            'Pflanze SOFORT und VORSICHTIG aus dem Grow entfernen',
            'Nicht schütteln — Pollen verbreitet sich über Luft',
            'In Müllsack einpacken bevor Transport',
            'Alle Nachbarpflanzen auf Bestäubung prüfen',
        ],
        'follow_up': [
            'Bestäubungs-Check aller Pflanzen (Calyx-Schwellung, Samenbildung)',
            'Wiederholter Check nach 7 und 14 Tagen',
            'Cultivar als hermie_prone markieren (kritisch)',
            'Genetische Linie dokumentieren (Cross-Ref REQ-017)',
            'Stress-Analyse: Lichtleck, Temperatur >30°C, Überdüngung prüfen',
        ],
        'plant_action': 'remove_immediately',
        'inspection_interval_days': 1,
    },
}


class HermaphrodismProtocolEngine:
    """Engine für Hermaphrodismus-Erkennung, Sofortmaßnahmen und genetische Markierung"""

    def __init__(self, db):
        self.db = db

    def get_response_protocol(self, severity: HermieSeverity) -> dict:
        """Gibt das Sofortmaßnahmen-Protokoll für den gegebenen Schweregrad zurück"""
        return HERMIE_RESPONSE_PROTOCOL[severity]

    def check_cultivar_hermie_history(self, cultivar_id: str) -> dict:
        """
        Prüft ob ein Cultivar bereits Hermaphrodismus-Vorfälle hatte.
        Gibt Warnung zurück für zukünftige Runs.
        """
        query = """
        FOR edge IN hermie_prone_cultivar
            FILTER edge._to == CONCAT('cultivars/', @cultivar_id)
            FOR finding IN hermaphroditism_findings
                FILTER finding._id == edge._from
                COLLECT severity = finding.severity
                    AGGREGATE count = COUNT(1)
                RETURN { severity, count }
        """
        cursor = self.db.aql.execute(query, bind_vars={'cultivar_id': cultivar_id})
        history = list(cursor)

        if not history:
            return {'hermie_prone': False, 'warning': None}

        total = sum(h['count'] for h in history)
        max_severity = max(history, key=lambda h:
            ['isolated', 'spreading', 'critical'].index(h['severity'])
        )['severity']

        return {
            'hermie_prone': True,
            'total_incidents': total,
            'max_severity': max_severity,
            'warning': (
                f"WARNUNG: Cultivar hat {total} Hermaphrodismus-Vorfall/-fälle. "
                f"Höchster Schweregrad: {max_severity}. "
                "Erhöhte Überwachung ab Blütewoche 3 empfohlen."
            ),
        }

    def flag_cultivar_hermie_prone(
        self, cultivar_id: str, finding_id: str, stress_context: str
    ) -> None:
        """Markiert einen Cultivar als hermie_prone nach bestätigtem Befall"""
        self.db.collection('hermie_prone_cultivar').insert({
            '_from': f'hermaphroditism_findings/{finding_id}',
            '_to': f'cultivars/{cultivar_id}',
            'confirmed_at': datetime.utcnow().isoformat(),
            'stress_context': stress_context,
        })

    def get_neighboring_plants_for_check(
        self, plant_id: str, location_id: str
    ) -> list[dict]:
        """
        Ermittelt alle Pflanzen im selben Standort/Slot die nach einem
        Hermie-Befund auf Bestäubung geprüft werden müssen.
        """
        query = """
        FOR plant IN plant_instances
            FILTER plant._key == @plant_id
            FOR slot IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['placed_in'] }
                FOR neighbor IN 1..1 INBOUND slot GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['placed_in'] }
                    FILTER neighbor._key != @plant_id
                    RETURN {
                        plant_id: neighbor._key,
                        plant_name: neighbor.name,
                        current_phase: neighbor.current_phase,
                        cultivar: neighbor.cultivar_name
                    }
        """
        cursor = self.db.aql.execute(
            query, bind_vars={'plant_id': plant_id}
        )
        return list(cursor)
```

**5. Karenzzeit-Validator:**
```python
from datetime import datetime, timedelta

class SafetyIntervalValidator:
    """Prüft Erntefähigkeit unter Berücksichtigung von Pflanzenschutzmittel-Anwendungen.

    ADR-001 (W-009 Karenz-Detach):
    Für eine Plant werden ALLE relevanten Treatments gesammelt:
    1. Direkte to_plant-Edges ohne inherited_from_run (Standalone-Behandlung)
    2. Aktive to_run-Edges, solange Plant Run-Mitglied ist (run_contains.detached_at == null)
    3. Geerbte to_plant-Edges mit inherited_from_run != null (Snapshot beim Detach)

    DISTINCT-Logik via treatment_application._key, damit Re-attach-Szenarien
    (ADR-001 Frage 3) keine Doppelzählung erzeugen.
    """

    @staticmethod
    def collect_relevant_treatments(plant_key: str, repo) -> list[dict]:
        """W-009 / ADR-001: Sammelt alle für eine Plant relevanten Treatments.

        Wird vom Karenz-Gate (REQ-007) und vom Validator selbst verwendet.
        Garantiert DISTINCT auf treatment_applications._key.
        """
        # 1. Direkte + geerbte to_plant-Edges (gleiche Collection, deduppliziert)
        plant_treatments = repo.find_treatments_via_to_plant(plant_key)

        # 2. Run-Treatments während aktiver Run-Mitgliedschaft
        active_run = repo.find_active_run_for_plant(plant_key)
        run_treatments = (
            repo.find_treatments_via_to_run(active_run.key)
            if active_run is not None
            else []
        )

        # DISTINCT via _key (Treatment kann theoretisch via to_plant UND to_run
        # erreichbar sein, wenn eine Plant nach Re-attach im Run ist)
        seen = {}
        for t in plant_treatments + run_treatments:
            seen[t["_key"]] = t
        return list(seen.values())

    @staticmethod
    def can_harvest(
        treatment_applications: list[dict],
        planned_harvest_date: datetime
    ) -> tuple[bool, list[str]]:
        """
        Args:
            treatment_applications: Liste von {applied_at, safety_interval_days, active_ingredient}.
                Aufrufer MUSS collect_relevant_treatments() für die korrekte Liste verwenden,
                damit detachte Plants nicht versehentlich am Run-Karenz-Gate vorbeikommen
                (ADR-001 / W-009).
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

<!-- Quelle: ADR-001 / W-009 -->
**5a. AQL-Lookup für `collect_relevant_treatments` (Repository-Layer):**

```aql
LET plant = DOCUMENT("plant_instances", @plant_key)

// Direkte + geerbte to_plant-Edges (Snapshot beim Detach hat inherited_from_run != null)
LET plant_treatments = (
    FOR t IN treatment_applications
        FOR e IN to_plant
            FILTER e._from == t._id AND e._to == plant._id
            RETURN MERGE(t, {
                _source: e.inherited_from_run == null ? "direct" : "inherited",
                inherited_from_run: e.inherited_from_run,
                inherited_at: e.inherited_at,
            })
)

// Run-Treatments nur, solange Plant aktives Run-Mitglied ist
LET active_run = FIRST(
    FOR rc IN run_contains
        FILTER rc._to == plant._id AND rc.detached_at == null
        FOR run IN planting_runs FILTER run._id == rc._from
        FILTER run.status == "active"
        RETURN run
)

LET run_treatments = active_run == null ? [] : (
    FOR t IN treatment_applications
        FOR e IN to_run
            FILTER e._from == t._id AND e._to == active_run._id
            RETURN MERGE(t, { _source: "run_active", run_key: active_run._key })
)

// DISTINCT via _key
LET combined = APPEND(plant_treatments, run_treatments)
LET unique_keys = UNIQUE(combined[*]._key)
RETURN (
    FOR k IN unique_keys
        RETURN FIRST(FOR t IN combined FILTER t._key == k RETURN t)
)
```
<!-- /Quelle: ADR-001 / W-009 -->

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

PestPressureLevel = Literal['none', 'low', 'medium', 'high', 'critical']
TreatmentType = Literal['cultural', 'biological', 'chemical', 'mechanical']
PathogenType = Literal['fungal', 'bacterial', 'viral', 'physiological']
# Hermaphrodismus-Typen (Quelle: Cannabis Indoor Grower Review G-010)
HermieFindingType = Literal['nanners', 'pollen_sacs', 'mixed']
HermieSeverity = Literal['isolated', 'spreading', 'critical']
HermieStressCorrelation = Literal[
    'light_leak', 'heat_stress', 'overfeeding', 'training_stress', 'genetic', 'unknown'
]

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
    # Hermaphrodismus-Felder (Quelle: Cannabis Indoor Grower Review G-010)
    hermaphroditism_detected: bool = False
    hermaphroditism_finding_type: Optional[HermieFindingType] = None
    hermaphroditism_severity: Optional[HermieSeverity] = None
    hermaphroditism_stress_correlation: Optional[HermieStressCorrelation] = None

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
| HermaphroditismFindings (Tenant-scoped) | Mitglied | Mitglied | Admin | <!-- Quelle: Cannabis Indoor Grower Review G-010 -->
| PollinationChecks (Tenant-scoped) | Mitglied | Mitglied | Admin | <!-- Quelle: Cannabis Indoor Grower Review G-010 -->

## 5. Abhängigkeiten

**Erforderliche existierende Collections/Beziehungen:**
- `plant_instances` aus REQ-001 (Stammdatenverwaltung)
- `growth_phases` aus REQ-003 (Phasensteuerung)
- `slots` / `locations` aus REQ-002 (Standortverwaltung)
- `sensors` / `observations` aus REQ-005 (Hybrid-Sensorik) für Umweltbedingungen
- `tasks` aus REQ-006 (Aufgabenplanung) für automatische Inspektions-Tasks
- `harvests` aus REQ-007 (Erntemanagement) für Karenzzeit-Validierung
- `cultivars` aus REQ-001 (Stammdatenverwaltung) für genetische Hermie-Prone-Markierung <!-- Quelle: Cannabis Indoor Grower Review G-010 -->

**Integrationsschnittstellen:**
- **REQ-005 (Sensorik):** Klimadaten (Temp, RLF) als Risikoindikator für Pathogene
- **REQ-003 (Phasen):** Phasenspezifische Vulnerabilitäten (z.B. Blüte anfällig für Botrytis)
- **REQ-006 (Tasks):** Automatische Generierung von Inspektions- und Behandlungs-Tasks
- **REQ-009 (Dashboard):** Alert-Integration bei kritischem Befallsdruck
<!-- Quelle: Cannabis Indoor Grower Review G-010 -->
- **REQ-001 (Stammdaten):** Cultivar-Flag `hermie_prone` nach bestätigtem Hermaphrodismus-Befall. Warnung bei zukünftigen Runs mit diesem Cultivar.
- **REQ-017 (Vermehrung):** Genetische Linie dokumentieren — Hermie-Disposition über `descended_from`-Kanten an Nachkommen weitergeben. Mutterpflanzen mit Hermie-Historie kennzeichnen.
- **REQ-013 (Pflanzdurchlauf):** Bestäubungs-Check-Protokoll bei allen Pflanzen im selben PlantingRun nach Hermie-Befund.

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
<!-- Quelle: Tabellen-Analyse UI-NFR-010 §7.2, §9.2 -->
- [ ] **Listenansicht-Filter:** Pest-Liste bietet Befallstyp-Filter (Enum-Chip: insect, mite, fungus, bacteria, virus, nematode); Disease-Liste bietet Krankheitstyp-Filter; Treatment-Liste bietet Behandlungsmethode-Filter (cultural, biological, chemical) und Karenz-Status-Toggle („Aktive Karenz" / „Alle"); alle URL-persistiert (UI-NFR-010 §7.2)
- [ ] **Tablet-Spaltenprioritäten:** Pest/Disease-ListPages blenden auf Tablet wissenschaftl. Namen aus; Treatment-ListPage blendet Hersteller aus; Primärspalten: dt. Name, Typ, Methode/Wirkstoff (UI-NFR-010 §8.1)
- [ ] **Compliance-Export:** TreatmentApplication-Liste bietet CSV- und PDF-Export der gefilterten Ansicht für Pflanzenschutz-Protokolle mit Karenzzeiten (UI-NFR-010 §9.2)
- [ ] **Batch-Traceability:** Alle Behandlungen sind mit erntefähigen Batches verknüpft (für Seed-to-Shelf-Tracking aus REQ-008)
- [ ] **Prävention-Score:** Dashboard zeigt präventive Gesundheits-Indikatoren (z.B. "Letzte Inspektion vor 5 Tagen, Risiko: Mittel")
<!-- Quelle: Cannabis Indoor Grower Review G-010 -->
- [ ] **Hermaphrodismus-Erkennung:** Befund-Typ `hermaphroditism` mit Subtypen (`nanners`, `pollen_sacs`, `mixed`) ist als Inspektions-Befund dokumentierbar
- [ ] **Hermaphrodismus-Schweregrad:** Drei Stufen (`isolated`, `spreading`, `critical`) mit jeweils spezifischem Sofortmaßnahmen-Protokoll
- [ ] **Sofortmaßnahmen-Protokoll:** System zeigt bei Hermie-Befund automatisch die schweregraddabhängigen Sofortmaßnahmen an (Entfernung, Isolierung, Monitoring)
- [ ] **Stress-Korrelation:** Hermaphrodismus-Befund kann mit dokumentierten Stress-Events verknüpft werden (Lichtleck, Hitzestress >30°C, Überdüngung, extremer Training-Stress)
- [ ] **Genetische Markierung:** Cultivar wird nach bestätigtem Befall als `hermie_prone` markiert. Bei zukünftigen Runs mit diesem Cultivar wird eine Warnung angezeigt (Cross-Ref REQ-001/REQ-017).
- [ ] **Bestäubungs-Check:** Nach Hermie-Befund generiert das System automatisch Inspektions-Tasks für alle Nachbarpflanzen im selben Slot/Location (Samen in Buds? Calyx-Schwellung ohne Trichom-Reife?)
- [ ] **Hermie-Historie:** Befallsmuster pro Cultivar können über mehrere Runs hinweg analysiert werden (genetische Disposition vs. Stress-bedingt)
<!-- Quelle: ADR-001 / W-009 -->
- [ ] **Karenz-Detach-Bypass-Schutz (ADR-001):** Eine PlantInstance, die mit aktiver Run-Level-Karenz aus einem Run detached wird, hat danach geerbte `to_plant`-Edges zu allen aktiven Treatments des ursprünglichen Runs. `inherited_from_run` und `inherited_at` sind gesetzt; Original-`applied_at` und `safety_interval_days` sind kopiert.
- [ ] **Karenz-Bypass-Test (ADR-001):** Ein automatisierter Test stellt sicher: Plant aus Run mit aktiver Karenz detachen → direkter Ernte-Versuch auf der detachten Plant wird mit `KarenzViolationError` blockiert, bis die Karenzzeit abgelaufen ist. Ohne Snapshot würde die Ernte fälschlich freigegeben — der Test darf nicht grün werden, wenn der Snapshot fehlt.
- [ ] **Re-attach-DISTINCT (ADR-001):** Eine Plant, die detached war (mit Snapshot von T1) und später in einen neuen Run mit ebenfalls T1 als Run-Treatment kommt, hat T1 sowohl als geerbte `to_plant`-Edge als auch als aktive `to_run`-Edge erreichbar. `SafetyIntervalValidator.collect_relevant_treatments()` deduppliziert via `_key` und liefert T1 genau einmal zurück.
- [ ] **Snapshot-Cutoff (ADR-001 Frage 1):** Beim Detach werden NUR Treatments mit `applied_at + safety_interval_days >= detached_at` als geerbte Edges erzeugt — abgelaufene Treatments werden übersprungen.
- [ ] **Snapshot-Immutability (ADR-001 Frage 2):** Korrektur eines Run-Treatments (z.B. `applied_at` ändern) propagiert NICHT auf bestehende geerbte Edges. Anwender muss die geerbte Edge separat editieren.
- [ ] **Migrations-Task (ADR-001 Frage 4):** Beim REQ-013-v2.0-Rollout läuft ein einmaliger Celery-Task, der für alle bestehenden detachten PlantInstances rückwirkend Snapshots erzeugt. Idempotent (mehrfacher Lauf erzeugt keine Duplikate).
<!-- /Quelle: ADR-001 / W-009 -->
<!-- Quelle: REQ-010 v1.2 — Schädlings-Detailseite -->
- [ ] **Schädlings-Detailseite:** Eine eigene Seite (`pflanzenschutz/pests/:key`) zeigt pro Schädling Steckbrief (Schadbild, betroffene Pflanzenteile, Wirtspflanzen, Lebenszyklus, Temperatur-/Feuchtebereich, Schweregrad), kuratierte Referenzbilder (Galerie; sauberer Leer-Zustand wenn keine vorhanden), Gegenmaßnahmen nach IPM-Hierarchie gruppiert (kulturell → biologisch → mechanisch → chemisch, mit sichtbarer Karenzzeit) sowie passende Nützlinge.
- [ ] **Aggregierter Endpoint:** `GET /ipm/pests/{key}/detail` liefert Stammdaten + nach IPM-Hierarchie sortierte Gegenmaßnahmen + Nützlinge (über `detection_slug` → `preys_on`) + Schadbild-Hinweis aus der REQ-044-Erkennungs-Taxonomie. 404 bei unbekanntem Schlüssel.
- [ ] **Verlinkung:** Schädlings-Liste (Zeilen-Klick, Desktop + Mobile) und der REQ-044-Erkennungs-Dialog (Link „Mehr über diesen Schädling" via `matched_pest_key`) führen auf die Detailseite.
- [ ] **Abwärtskompatibilität:** Alle neuen `pests`-Felder sind optional; bestehende Seeds ohne Detailfelder bleiben gültig und die Detailseite blendet leere Abschnitte aus.
<!-- /Quelle: REQ-010 v1.2 -->
<!-- Quelle: REQ-010 v1.3 — Behandlungs-Detailseite + mehrsprachige Gegenmaßnahmen -->
- [ ] **Mehrsprachige Gegenmaßnahmen:** Treatment-Namen und -Detailtexte liegen mehrsprachig vor (`name`/`name_de`, `description(_de)`, `how_to_apply(_de)`, `mode_of_action(_de)`, `precautions(_de)`); die UI zeigt die Sprache des Nutzers (DE → `_de`, sonst englisches Basisfeld). Inhalte stammen vollständig aus `ipm.yaml` (kein hartkodierter Fachtext im Code).
- [ ] **Behandlungs-Detailseite:** Eine eigene Seite (`pflanzenschutz/treatments/:key`) zeigt pro Maßnahme Eckdaten (Anwendungsart, Wirkstoff, Dosierung, Karenzzeit, Schutzausrüstung), Anwendung, Wirkweise, Sicherheitshinweise sowie die behandelten Schädlinge (verlinkt) und Krankheiten.
- [ ] **Aggregierter Endpoint:** `GET /ipm/treatments/{key}/detail` liefert die Maßnahme + die behandelten Schädlinge/Krankheiten (Reverse-Edges, dedupliziert). 404 bei unbekanntem Schlüssel.
- [ ] **Verlinkung:** Behandlungs-Liste (Zeilen-Klick) und die Gegenmaßnahmen auf der Schädlings-Detailseite verlinken auf die Behandlungs-Detailseite; die behandelten Schädlinge dort verlinken zurück auf die Schädlings-Detailseite.
- [ ] **Abwärtskompatibilität (Treatments):** Alle neuen `treatments`-Felder sind optional; `name` (englisch) bleibt unverändert als Edge-Schlüssel der `pest_treatments`/`disease_treatments`-Mappings.
<!-- /Quelle: REQ-010 v1.3 -->
<!-- Quelle: REQ-010 v1.4 — Nutzer-beigesteuerte Schädling-Referenzbilder -->
- [ ] **Bild-Beitrag (Upload/Kamera):** Ein Nutzer kann zu einem Schädling eigene Fotos beitragen — per Datei-Upload oder Kamera. Bilder werden über den `AttachmentService` (EXIF-Strip, Virus-Scan, Magic-Byte, Dedup) gespeichert und erscheinen sofort in der privaten Galerie der Detailseite (tenant-scoped); eigene Bilder sind löschbar. Im Light-Modus nicht verfügbar.
- [ ] **Tenant-Isolation:** Private Bilder eines Tenants sind für andere Tenants nicht sichtbar/löschbar.
- [ ] **Globale Freigabe (Moderation):** Ein Platform-Admin kann beigesteuerte Bilder global freigeben (`status=promoted`); freigegebene Bilder werden für alle Nutzer über einen globalen, read-only Content-Endpoint sichtbar, der ausschließlich `promoted` ausliefert (private/unbekannt → 404).
- [ ] **Erkennung:** Bei Freigabe wird das Bild als Few-Shot-Referenz (`source=user_contributed`) in den Erkennungs-Index (REQ-044) aufgenommen, sofern der Schädling eine Erkennungsklasse (`detection_slug`) hat; nur Embedding/Provenienz, kein Originalpixel im Index.
- [ ] **DSGVO:** Beigesteuerte Bilder (Dokumente + Attachment-Bytes) werden bei Tenant- und Nutzer-Löschung vollständig entfernt.
<!-- /Quelle: REQ-010 v1.4 -->

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

<!-- Quelle: Cannabis Indoor Grower Review G-010 -->
**Szenario 4: Hermaphrodismus — Isolated (Einzelne Nanners)**
```
GIVEN: PlantInstance "White Widow #3" in Blütephase Woche 5
  AND: Letzte Inspektion vor 2 Tagen ohne Befund
WHEN: Neue Inspektion erkennt einzelne gelbe "Banane" (Nanner) in oberer Cola
  AND: Inspector dokumentiert finding_type = 'nanners', severity = 'isolated'
  AND: Stress-Korrelation: Lichtleck am Zelt-Reißverschluss entdeckt
THEN:
  - System zeigt Sofortmaßnahmen-Protokoll für 'isolated':
    "Nanners vorsichtig mit Pinzette entfernen, Stelle mit Wasser besprühen"
  - Inspektionsintervall wird auf 1 Tag reduziert (für gesamten Run)
  - Stress-Ursache "light_leak" wird am Befund dokumentiert
  - System generiert Empfehlung: "Lichtleck beheben"
  - Pflanze bleibt im Grow (plant_action = 'keep_with_monitoring')
```

**Szenario 5: Hermaphrodismus — Critical (Massive Bestäubungsgefahr)**
```
GIVEN: PlantInstance "Bagseed #1" in Blütephase Woche 6
  AND: 5 weitere Pflanzen im selben Location/Slot
  AND: Mehrere vollständige Pollensäcke an verschiedenen Colas gefunden
WHEN: Inspector dokumentiert finding_type = 'pollen_sacs', severity = 'critical'
  AND: estimated_pollen_release = true
THEN:
  - System zeigt Sofortmaßnahmen-Protokoll für 'critical':
    "Pflanze SOFORT und VORSICHTIG entfernen, in Müllsack einpacken"
  - System generiert automatisch Bestäubungs-Check-Tasks für alle 5 Nachbarpflanzen
  - Bestäubungs-Check beinhaltet: Calyx-Schwellung ohne Trichom-Reife, Samenbildung
  - Cultivar wird als hermie_prone markiert (Cross-Ref REQ-001)
  - Warnung wird für alle zukünftigen Runs mit diesem Cultivar hinterlegt
```

**Szenario 6: Hermie-Prone-Cultivar-Warnung bei neuem Run**
```
GIVEN: Cultivar "Bagseed #1" ist als hermie_prone markiert (1 critical-Vorfall)
WHEN: Nutzer erstellt neuen PlantingRun mit diesem Cultivar
THEN:
  - System zeigt Warnung: "ACHTUNG: Cultivar hat 1 Hermaphrodismus-Vorfall
    (Schweregrad: critical). Erhöhte Überwachung ab Blütewoche 3 empfohlen."
  - Inspektions-Scheduler erhöht automatisch die Frequenz ab Blütephase
  - System schlägt vor: Stress-Faktoren minimieren (kein Lichtleck, Temperatur <28°C)
```

**Szenario 7: Bestäubungs-Check nach Hermie-Befund**
```
GIVEN: Hermie-Befund (severity = 'spreading') wurde vor 7 Tagen dokumentiert
  AND: Pflanze wurde isoliert, 4 Nachbarpflanzen befinden sich weiter im Run
WHEN: Inspector führt Bestäubungs-Check an Nachbarpflanze durch
  AND: check_type = 'calyx_squeeze', calyx_swelling_without_trichome_maturity = true
THEN:
  - System markiert Pflanze als potenziell bestäubt
  - Warnung: "Calyx-Schwellung ohne Trichom-Reife deutet auf Bestäubung hin"
  - System empfiehlt Nachkontrolle in 7 Tagen (Samen werden nach 2-3 Wochen sichtbar)
  - Ernte-Qualitätsprognose wird nach unten korrigiert
```

---

**Hinweise für RAG-Integration:**
- Keywords: IPM, Schädling, Krankheit, Nützling, Karenzzeit, Resistenz, Inspektion, Behandlung, Hermaphrodismus, Nanners, Pollensäcke, Hermie, Bestäubung, hermie_prone <!-- Quelle: Cannabis Indoor Grower Review G-010 -->
- Verknüpfung: Alle REQ-001 bis REQ-009, besonders REQ-003 (Phasen), REQ-005 (Sensorik), REQ-007 (Ernte), REQ-013 (Pflanzdurchlauf), REQ-017 (Vermehrung) <!-- Quelle: Cannabis Indoor Grower Review G-010 -->
- Botanische Fachbegriffe: Phytopathologie, Entomologie, Akarizide, Fungizide, Predatoren, Parasitismus, Hermaphrodismus, Monözie, Bestäubung, Samenbildung <!-- Quelle: Cannabis Indoor Grower Review G-010 -->
