# Spezifikation: REQ-020 - Onboarding-Wizard

```yaml
ID: REQ-020
Titel: Geführter Onboarding-Wizard für Erstnutzer
Kategorie: Benutzerführung
Fokus: Frontend (Backend-Unterstützung für Starter-Kits und Präferenzen)
Technologie: React, TypeScript, MUI, Redux Toolkit, FastAPI, ArangoDB
Status: Entwurf
Version: 1.3 (Agrarbiologie-Review Korrekturen)
```

## 1. Business Case

**User Story (Erstnutzer):** "Als Hobby-Gärtner, der zum ersten Mal Kamerplanter öffnet, möchte ich in weniger als 3 Minuten meine ersten Pflanzen im System haben — ohne Fachbegriffe verstehen oder komplexe Formulare ausfüllen zu müssen."

**User Story (Szenario-Auswahl):** "Als Einsteiger möchte ich aus vorkonfigurierten Szenarien wählen können (z.B. 'Kräuter auf der Fensterbank', 'Tomaten auf dem Balkon') — damit das System automatisch alle nötigen Stammdaten, Standorte und Pflanzen für mich anlegt."

**User Story (Erfahrungsstufe):** "Als Nutzer möchte ich beim ersten Start meine Erfahrungsstufe angeben können — damit das System mir nur die Funktionen und Felder zeigt, die zu meinem Wissensstand passen."

**User Story (Wiederaufruf):** "Als Nutzer möchte ich den Onboarding-Wizard jederzeit erneut aufrufen können — um ein weiteres Anbau-Szenario hinzuzufügen oder meine Erfahrungsstufe zu ändern."

**Beschreibung:**
Das aktuelle System setzt bei der Erstnutzung umfangreiches Domänenwissen voraus: Um eine einzelne Pflanze anzulegen, sind mindestens 5–6 Schritte über verschiedene Entitäten nötig (BotanicalFamily → Species → Site → Location → PlantInstance → GrowthPhase). Der Onboarding-Wizard reduziert diesen Prozess auf 4 interaktive Schritte und erstellt alle benötigten Entitäten automatisch im Hintergrund.

**Kernkonzepte:**

**Starter-Kits als vorkonfigurierte Datenpakete:**
Ein Starter-Kit bündelt alle Stammdaten, die für ein bestimmtes Anbau-Szenario benötigt werden: BotanicalFamilies, Species mit Cultivars, vorkonfigurierte GrowthPhases mit RequirementProfiles und optionale WorkflowTemplates. Starter-Kits werden als Seed-Daten im Backend bereitgestellt und beim Onboarding in die Nutzerdaten übernommen.

**Erfahrungsstufe als systemweite Präferenz:**
Die im Wizard gewählte Erfahrungsstufe wird als `UserPreference` persistiert und steuert den UI-Modus (siehe REQ-021). Der Wizard ist der primäre Einstiegspunkt für die Modus-Auswahl, kann aber jederzeit in den Einstellungen geändert werden.

**Automatische Entitäts-Erzeugung:**
Der Wizard erstellt auf Basis der Nutzer-Eingaben automatisch alle benötigten Entitäten in der korrekten Reihenfolge, einschließlich Graph-Kanten (belongs_to, grows_at, etc.).

**Abgrenzung:**
- Kein Account-Management — der Wizard setzt ein existierendes (ggf. anonymes) System voraus. Authentifizierung ist nicht Teil dieser REQ (siehe NFR-001 JWT-Auth).
- Kein Import externer Daten — der Wizard nutzt ausschließlich vorkonfigurierte Starter-Kits.
- Keine KI-basierte Empfehlung — die Szenario-Auswahl ist manuell.

## 2. ArangoDB-Modellierung

### Nodes:

- **`:StarterKit`** — Vorkonfiguriertes Anbau-Szenario
  - Collection: `starter_kits`
  - Properties:
    - `kit_id: str` (eindeutig, z.B. `"balkon-tomaten"`, `"fensterbank-kraeuter"`)
    - `name_i18n: dict[str, str]` (z.B. `{"de": "Balkon-Tomaten", "en": "Balcony Tomatoes"}`)
    - `description_i18n: dict[str, str]` (Kurzbeschreibung, 1–2 Sätze)
    - `difficulty: Literal['beginner', 'intermediate', 'advanced']`
    - `icon: str` (MUI-Icon-Name oder Emoji-Code)
    - `image_url: Optional[str]` (Vorschaubild)
    - `plant_count_suggestion: int` (Empfohlene Pflanzenanzahl, z.B. 3 für Tomaten)
    - `site_type: Literal['indoor', 'outdoor', 'windowsill', 'balcony', 'greenhouse', 'grow_tent']`
    - `species_keys: list[str]` (Referenzen auf Species-Dokumente)
    - `cultivar_keys: list[str]` (Optionale Cultivar-Referenzen)
    - `toxicity_warning: Optional[dict]` (Toxizitätshinweis, z.B. `{"cats": "warning", "dogs": "warning", "children": "warning"}`. Werte: `"safe"`, `"caution"`, `"warning"`, `"danger"`. Wird aus dem höchsten `ToxicityInfo.severity`-Wert der enthaltenen Species abgeleitet — siehe REQ-001 Species-Toxizität.)
    - `workflow_template_keys: list[str]` (Optionale WorkflowTemplate-Referenzen aus REQ-006)
    - `includes_nutrient_plan: bool` (Ob ein vereinfachter Düngeplan mitgeliefert wird)
    - `tags: list[str]` (z.B. `["indoor", "anfaenger", "essbar"]`)
    - `sort_order: int` (Anzeige-Reihenfolge im Wizard)

- **`:OnboardingState`** — Onboarding-Fortschritt des Nutzers
  - Collection: `onboarding_states`
  - Properties:
    - `completed: bool` (Wizard vollständig durchlaufen)
    - `skipped: bool` (Wizard übersprungen)
    - `completed_at: Optional[datetime]`
    - `selected_kit_id: Optional[str]` (Gewähltes Starter-Kit)
    - `selected_experience_level: Literal['beginner', 'intermediate', 'expert']`
    - `created_entities: OnboardingCreatedEntities` (embedded, siehe unten)
    - `wizard_step: int` (Aktueller Schritt für Resume-Funktion)

- **`:UserPreference`** — Nutzerpräferenzen (**serverseitig persistiert** in ArangoDB, geräte- und sitzungsübergreifend verfügbar)
  - Collection: `user_preferences`
  - Zuordnung: Jeder User hat genau ein UserPreference-Dokument (1:1-Beziehung über `user_key`)
  - Speicherung: Serverseitig in ArangoDB — beim Login werden die Präferenzen vom Server geladen, sodass Einstellungen (z.B. Erfahrungsstufe, Theme, Locale) auf jedem Gerät und in jeder Session sofort verfügbar sind
  - Properties:
    - `experience_level: Literal['beginner', 'intermediate', 'expert']` (Default: `'beginner'`)
    - `onboarding_completed: bool`
    - `locale: str` (z.B. `"de"`, `"en"`)
    - `theme: Literal['light', 'dark', 'system']`
    - `temperature_unit: Literal['celsius', 'fahrenheit']` (Default: `'celsius'`) — Bestimmt die Temperaturanzeige im gesamten System. Alle Temperaturen werden intern in °C gespeichert und bei der Anzeige gemäß dieser Präferenz konvertiert (°C ↔ °F).

### Edges:

```
includes_species:   starter_kits → species             (Kit enthält Species)
includes_cultivar:  starter_kits → cultivars            (Kit enthält Cultivar)
includes_template:  starter_kits → workflow_templates    (Kit enthält WorkflowTemplate)
created_by_wizard:  onboarding_states → plant_instances  (Wizard hat PlantInstance erstellt)
```

### Indizes:

```
starter_kits:
  - PERSISTENT INDEX on [kit_id] UNIQUE
  - PERSISTENT INDEX on [difficulty, sort_order]

onboarding_states:
  - PERSISTENT INDEX on [completed]
```

## 3. Technische Umsetzung (Python)

### Pydantic-Modelle:

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class StarterKitSummary(BaseModel):
    """Kompakte Darstellung für die Kit-Auswahl im Wizard."""
    kit_id: str
    name: str  # Lokalisiert nach Accept-Language
    description: str
    difficulty: str
    icon: str
    image_url: Optional[str] = None
    plant_count_suggestion: int
    site_type: str
    species_count: int
    tags: list[str]

class StarterKitDetail(StarterKitSummary):
    """Vollständige Kit-Daten mit Species-Details."""
    species: list[dict]  # Vereinfachte Species-Darstellung mit common_name, image
    cultivars: list[dict]
    workflow_templates: list[dict]
    includes_nutrient_plan: bool

class OnboardingCreatedEntities(BaseModel):
    """Tracking der vom Wizard erstellten Entitäten."""
    site_key: Optional[str] = None
    location_keys: list[str] = Field(default_factory=list)
    plant_instance_keys: list[str] = Field(default_factory=list)
    planting_run_key: Optional[str] = None

class OnboardingWizardRequest(BaseModel):
    """Wizard-Abschluss: Alle Daten aus den 4 Schritten."""
    experience_level: str = Field(
        pattern=r'^(beginner|intermediate|expert)$'
    )
    kit_id: str
    site_name: str = Field(min_length=1, max_length=100)
    site_type: str
    plant_count: int = Field(ge=1, le=50)
    selected_species_keys: list[str] = Field(min_length=1)
    selected_cultivar_keys: list[str] = Field(default_factory=list)
    # Optionale Wasserquellen-Konfiguration (ab Erfahrungsstufe 'intermediate')
    has_ro_system: Optional[bool] = Field(
        None,
        description="Osmoseanlage vorhanden? Wird in Site.water_source.has_ro_system übernommen. "
                    "null = nicht angegeben (Beginner überspringt diesen Abschnitt)."
    )
    tap_water_ec_ms: Optional[float] = Field(
        None, ge=0, le=2.0,
        description="EC des Leitungswassers in mS/cm. Schnelleingabe für Wizard — "
                    "detaillierte Analyse kann später in den Site-Einstellungen ergänzt werden."
    )
    tap_water_ph: Optional[float] = Field(
        None, ge=4.0, le=9.5,
        description="pH des Leitungswassers. Schnelleingabe für Wizard."
    )

class OnboardingWizardResponse(BaseModel):
    """Ergebnis des Wizard-Abschlusses."""
    success: bool
    created: OnboardingCreatedEntities
    dashboard_message: str  # Lokalisierte Willkommensnachricht
    next_tasks: list[dict]  # Erste automatisch generierte Tasks
```

### Logik-Anforderungen:

**1. OnboardingEngine — Entitäts-Erzeugung:**
```python
class OnboardingEngine:
    """Orchestriert die automatische Erstellung aller Entitäten."""

    def execute_onboarding(
        self, request: OnboardingWizardRequest
    ) -> OnboardingWizardResponse:
        """
        Erstellt in korrekter Reihenfolge:
        1. Site (aus site_name + site_type)
        2. Location (1 Default-Location für die Site)
        3. PlantInstances (plant_count × gewählte Species/Cultivars)
        4. PlantingRun (1 Run mit allen Instances als Entries)
        5. GrowthPhases (aus Seed-Daten der Species)
        6. Optional: Initiale Tasks aus WorkflowTemplate

        Alle Operationen in einer ArangoDB-Transaktion.
        Rollback bei Fehler in beliebigem Schritt.
        """
        ...

    def _create_site(self, name: str, site_type: str) -> str:
        """Erstellt Site mit sinnvollen Defaults."""
        ...

    def _create_location(self, site_key: str, site_type: str) -> str:
        """Erstellt Default-Location passend zum Site-Typ."""
        ...

    def _create_plant_instances(
        self,
        species_keys: list[str],
        cultivar_keys: list[str],
        location_key: str,
        count: int,
    ) -> list[str]:
        """
        Verteilt plant_count gleichmäßig auf gewählte Species.
        Generiert automatische Instance-IDs (z.B. TOMATE-001, TOMATE-002).
        Setzt current_phase auf erste Phase der Species.
        """
        ...

    def _create_planting_run(
        self,
        plant_instance_keys: list[str],
        site_key: str,
        location_key: str,
    ) -> str:
        """Erstellt PlantingRun mit allen Instances als Entries."""
        ...

    def _generate_initial_tasks(
        self,
        kit_id: str,
        plant_instance_keys: list[str],
    ) -> list[dict]:
        """Generiert erste Tasks aus WorkflowTemplate des Kits."""
        ...
```

**2. StarterKitService — Kit-Verwaltung:**
```python
class StarterKitService:
    """Verwaltung und Auslieferung der Starter-Kits."""

    def list_kits(
        self,
        difficulty: Optional[str] = None,
        locale: str = "de",
    ) -> list[StarterKitSummary]:
        """Alle Kits, optional nach Schwierigkeit gefiltert."""
        ...

    def get_kit_detail(
        self, kit_id: str, locale: str = "de"
    ) -> StarterKitDetail:
        """Vollständige Kit-Daten mit aufgelösten Species."""
        ...
```

### Seed-Daten — Starter-Kits:

| Kit-ID | Name (DE) | Species | Cultivars | Schwierigkeit |
|--------|-----------|---------|-----------|---------------|
| `fensterbank-kraeuter` | Fensterbank-Kräuter | *Ocimum basilicum*, *Mentha spicata*, *Petroselinum crispum*, *Allium schoenoprasum*, *Anethum graveolens* | Genovese-Basilikum, Krause Petersilie, Schnittlauch | `beginner` |
| `balkon-tomaten` | Balkon-Tomaten | *Solanum lycopersicum* | Tiny Tim, Balkonstar, Tumbling Tom Red | `beginner` |
| `kleines-gemusebeet` | Kleines Gemüsebeet | *Solanum lycopersicum*, *Ocimum basilicum*, *Lactuca sativa*, *Phaseolus vulgaris*, *Daucus carota* | Cherry-Tomate, Kopfsalat Maikönig, Buschbohne Saxa | `beginner` |
| `zimmerpflanzen` | Zimmerpflanzen | *Monstera deliciosa*, *Ficus lyrata*, *Epipremnum aureum*, *Dracaena trifasciata* (syn. *Sansevieria trifasciata*) | Golden Pothos, Ficus lyrata 'Bambino' | `beginner` |
| `zimmerpflanzen-haustierfreundlich` | Zimmerpflanzen (haustierfreundlich) | *Chlorophytum comosum*, *Chamaedorea elegans*, *Pilea peperomioides*, *Maranta leuconeura* | Grünlilie, Bergpalme, Glückstaler, Pfeilwurz | `beginner` |
| `indoor-growzelt` | Indoor Growzelt | *Cannabis sativa* | Northern Lights Auto, White Widow, Critical Mass | `intermediate` |
| `chili-zucht` | Chili-Zucht (Einsteiger) | *Capsicum annuum* | Jalapeño, Cayenne, Hungarian Wax | `beginner` |
| `superhot-chili` | Superhot-Chili | *Capsicum chinense*, *Capsicum annuum* | Habanero Orange, Carolina Reaper, Trinidad Scorpion | `advanced` |
| `microgreens` | Microgreens | *Brassica oleracea* var. *italica*, *Raphanus sativus*, *Helianthus annuus* | Brokkoli-Microgreens 'Calabrese', Radieschen-Microgreens 'China Rose', Sonnenblumen-Microgreens | `beginner` |
| `balkon-blumen` | Balkonblumen | *Viola x wittrockiana*, *Petunia x hybrida*, *Tagetes patula*, *Lobelia erinus* | Schweizer Riesen (Stiefmütterchen), Surfinia Blue (Petunie), Bonanza Yellow (Tagetes), Crystal Palace (Lobelie) | `beginner` |
| `balkon-blumen-voranzucht` | Balkonblumen (Voranzucht) | *Viola x wittrockiana*, *Petunia x hybrida*, *Lobelia erinus*, *Impatiens walleriana* | Schweizer Riesen, Surfinia Blue, Crystal Palace, Accent White | `intermediate` |

<!-- Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03 -->
**Balkonblumen-Kit Beschreibung:**

Das Kit `balkon-blumen` erstellt automatisch:
- **Site:** "Mein Balkon" (`location_type: balcony`, `is_indoor: false`)
- **Location:** "Balkonkasten" (`bed_type: container`)
- **PlantingRun:** Monokultur-Run pro Art mit artspezifischen Pflanzzeiten
- **WorkflowTemplate:** Einsteiger-Workflow mit: Pflanzen einsetzen, erstes Gießen, Langzeitdünger einarbeiten, wöchentlich Verblühtes entfernen
- **CareProfile:** `outdoor_annual_ornamental` (siehe REQ-022)

Das Kit `balkon-blumen-voranzucht` erstellt zusätzlich:
- **Location:** "Fensterbank" (`location_type: room`, `is_indoor: true`, `window_orientation: south`)
- **WorkflowTemplate:** Voranzucht-Workflow mit: Aussaat (Jan/Feb), Pikieren (Mär), Abhärten (Apr), Auspflanzen (Mai)
- Phasen: `germination` → `seedling` → `vegetative` → `hardening_off` → `flowering` → `senescence`

<!-- Quelle: Agrarbiologie-Review AB-006, AB-007, AB-008, AB-009, 2026-03 -->
**Voranzucht-Hinweise (im Kit-Beschreibungstext, i18n):**
- **Lichtbedarf (AB-006):** "Für erfolgreiche Voranzucht wird ein Pflanzenlichtsystem empfohlen (DLI min. 8 mol/m²/d, 100–200 µmol/m²/s PPFD). Fensterbank-Aufzucht nur bei Südfenster mit direkter Sonne von Februar an. Nordfenster im Februar liefert nur 1–3 mol/m²/d — das reicht nicht für gesunde Sämlinge."
- **Keimtemperaturen (AB-007):** "Achtung: Nicht alle Balkonblumen keimen bei gleicher Temperatur! Stiefmütterchen (Viola) brauchen Kühle (15–18°C, NICHT auf Heizmatte!), Petunien dagegen Wärme (22–25°C, Heizmatte empfohlen). Getrennte Keimung empfohlen."
- **Pikieren (AB-008):** "3–5 Tage nach dem Pikieren: erhöhte Luftfeuchtigkeit, gedämpftes Licht, kein Dünger (Erholungsphase)."
- **Abhärten (AB-009):** "7–14 Tage vor dem Auspflanzen schrittweise an Außenluft gewöhnen: Tag 1–3: 2 Stunden geschützt, dann täglich steigern. Plötzliches Auspflanzen führt zu Sonnenbrand und Welke."
- **Geranien-Überwinterung (AB-003):** "Geranien (*Pelargonium*) können im Herbst eingewintert werden (hell, 5–10°C, stark zurückschneiden) oder werden jährlich neu gekauft."
<!-- /Quelle: Zierpflanzen-Analyse Stiefmütterchen-Use-Case 2026-03 -->

**Toxizitätswarnungen pro Kit:**

| Kit-ID | `toxicity_warning` |
|--------|-------------------|
| `fensterbank-kraeuter` | `{"cats": "safe", "dogs": "safe", "children": "safe"}` |
| `balkon-tomaten` | `{"cats": "caution", "dogs": "caution", "children": "safe"}` |
| `kleines-gemusebeet` | `{"cats": "caution", "dogs": "caution", "children": "safe"}` |
| `zimmerpflanzen` | `{"cats": "warning", "dogs": "warning", "children": "warning"}` |
| `zimmerpflanzen-haustierfreundlich` | `{"cats": "safe", "dogs": "safe", "children": "safe"}` |
| `indoor-growzelt` | `{"cats": "caution", "dogs": "caution", "children": "danger"}` |
| `chili-zucht` | `{"cats": "safe", "dogs": "safe", "children": "safe"}` |
| `superhot-chili` | `{"cats": "safe", "dogs": "safe", "children": "caution"}` |
| `microgreens` | `{"cats": "safe", "dogs": "safe", "children": "safe"}` |
| `balkon-blumen` | `{"cats": "caution", "dogs": "caution", "children": "safe"}` |
| `balkon-blumen-voranzucht` | `{"cats": "caution", "dogs": "caution", "children": "safe"}` |

<!-- Quelle: Agrarbiologie-Review AB-015, 2026-03 -->
> **Toxizitäts-Korrektur (AB-015):** Die Balkonblumen-Kits enthalten *Tagetes patula* (mild toxisch: Thiophenderivate, kutane Irritation bei Katzen/Hunden, ASPCA) und *Lobelia erinus* (moderat toxisch: Lobeliin-Alkaloid, ASPCA/Giftnotruf Bonn). Daher `"caution"` statt `"safe"` für cats/dogs. *Pelargonium zonale* ist ebenfalls mild toxisch (Geraniol/Linalool). Children: `"safe"`, da die enthaltenen Species bei oraler Aufnahme nur milde Symptome verursachen.

Hinweis: Tomate (*Solanum lycopersicum*) enthält Solanin/Tomatidin in Blättern und unreifen Früchten — milde Toxizität für Haustiere. Alle vier Zimmerpflanzen-Kit-Species sind für Haustiere toxisch (Calciumoxalat-Raphide bzw. Saponine).

Jedes Kit liefert für jede enthaltene Species:
- Vollständige BotanicalFamily-Referenz (aus bestehenden Seed-Daten)
- Mindestens 3 vorkonfigurierte GrowthPhases mit Dauern (artspezifisch, siehe unten)
- RequirementProfiles mit Anfänger-tauglichen Werten
- Deutsche und englische Trivialnamen
- 1 WorkflowTemplate mit Einsteiger-Tasks (REQ-006, `difficulty_level: 'beginner'`)

**Zimmerpflanzen-spezifische GrowthPhases:**

Dekorative Zimmerpflanzen (Kits `zimmerpflanzen` und `zimmerpflanzen-haustierfreundlich`) verwenden einen eigenen Phasen-Satz, da die Standard-Phasen (seedling → vegetative → flowering → ripening) auf einjährige Nutzpflanzen zugeschnitten sind und für mehrjährige Zimmerpflanzen biologisch nicht sinnvoll sind:

| Phase | Dauer | Beschreibung |
|-------|-------|-------------|
| `acclimatization` | 14–28 Tage | Eingewöhnung nach Kauf oder Umtopfen. Reduziertes Gießen, kein Dünger, kein Umstellen. |
| `active_growth` | Ganzjährig (bei Kunstlicht) oder saisonal (Frühling–Herbst) | Aktives Wachstum. Regelmäßig gießen und düngen. |
| `maintenance` | An Jahreszeit gekoppelt (Winter) | Erhaltungspflege / Winter-Verlangsamung. Weniger gießen, nicht düngen, kühlere Temperaturen tolerieren. |
| `repotting_recovery` | 7–14 Tage (event-triggered) | Erholungsphase nach Umtopfen. Ähnlich wie acclimatization, aber kürzer. |

## 4. API-Endpunkte

### Router: `/api/v1/onboarding`

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/onboarding/state` | Onboarding-Status abfragen (completed/skipped/step) | Ja |
| `POST` | `/api/v1/onboarding/complete` | Wizard abschließen — erstellt alle Entitäten | Ja |
| `POST` | `/api/v1/onboarding/skip` | Wizard überspringen | Ja |
| `PATCH` | `/api/v1/onboarding/state` | Wizard-Fortschritt speichern (für Resume) | Ja |

### Router: `/api/v1/starter-kits`

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/starter-kits` | Alle Kits auflisten (mit `?difficulty=beginner`-Filter) | Nein |
| `GET` | `/api/v1/starter-kits/{kit_id}` | Kit-Detail mit aufgelösten Species/Cultivars | Nein |
| `POST` | `/api/v1/starter-kits/{kit_id}/apply` | Kit nachträglich anwenden (ohne Wizard) | Ja |

### Router: `/api/v1/user-preferences`

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/user-preferences` | Aktuelle Präferenzen abfragen | Ja |
| `PATCH` | `/api/v1/user-preferences` | Präferenzen aktualisieren (experience_level, locale, theme, temperature_unit) | Ja |

### Response-Beispiele:

**GET /api/v1/starter-kits**
```json
[
  {
    "kit_id": "fensterbank-kraeuter",
    "name": "Fensterbank-Kräuter",
    "description": "5 beliebte Küchenkräuter für die sonnige Fensterbank — ideal für Einsteiger.",
    "difficulty": "beginner",
    "icon": "local_florist",
    "image_url": null,
    "plant_count_suggestion": 5,
    "site_type": "windowsill",
    "species_count": 5,
    "tags": ["indoor", "anfaenger", "essbar", "kraeuter"]
  }
]
```

**POST /api/v1/onboarding/complete**
```json
// Request:
{
  "experience_level": "beginner",
  "kit_id": "fensterbank-kraeuter",
  "site_name": "Meine Fensterbank",
  "site_type": "windowsill",
  "plant_count": 5,
  "selected_species_keys": [
    "species/ocimum-basilicum",
    "species/mentha-spicata",
    "species/petroselinum-crispum",
    "species/allium-schoenoprasum",
    "species/anethum-graveolens"
  ]
}

// Response:
{
  "success": true,
  "created": {
    "site_key": "sites/meine-fensterbank",
    "location_keys": ["locations/fensterbank-1"],
    "plant_instance_keys": [
      "plant_instances/BASIL-001",
      "plant_instances/MINZE-001",
      "plant_instances/PETER-001",
      "plant_instances/SCHNIT-001",
      "plant_instances/DILL-001"
    ],
    "planting_run_key": "planting_runs/fensterbank-kraeuter-2026"
  },
  "dashboard_message": "Willkommen! Deine 5 Kräuter sind eingerichtet. Hier sind deine ersten Aufgaben:",
  "next_tasks": [
    {
      "title": "Basilikum gießen",
      "description": "Obere Erdschicht trocken? Dann gießen (ca. 100ml).",
      "due_in_days": 1,
      "estimated_duration_minutes": 2
    },
    {
      "title": "Schnittlauch Standort prüfen",
      "description": "Steht er sonnig genug? Mindestens 4 Stunden direkte Sonne.",
      "due_in_days": 0,
      "estimated_duration_minutes": 1
    }
  ]
}
```

## 5. Frontend-Spezifikation

### 5.1 Wizard-Komponenten

```
src/frontend/src/pages/onboarding/
├── OnboardingWizard.tsx           # Wizard-Container (MUI Stepper)
├── steps/
│   ├── WelcomeStep.tsx            # Schritt 1: Begrüßung & Erfahrungsstufe
│   ├── ScenarioStep.tsx           # Schritt 2: Starter-Kit-Auswahl
│   ├── SiteSetupStep.tsx          # Schritt 3: Standort einrichten
│   ├── PlantSelectionStep.tsx     # Schritt 4: Pflanzen auswählen & Anzahl
│   └── CompletionStep.tsx         # Schritt 5: Zusammenfassung & erste Tasks
├── components/
│   ├── StarterKitCard.tsx         # Kit-Vorschaukarte (Bild, Name, Schwierigkeit)
│   ├── ExperienceLevelSelector.tsx # 3-stufige Auswahl mit Icons und Beschreibung
│   ├── PlantCountSlider.tsx       # Slider für Pflanzenanzahl (1-20)
│   └── SiteTypeSelector.tsx       # Standorttyp-Auswahl mit Icons
└── hooks/
    ├── useOnboardingState.ts      # Onboarding-Status aus API
    └── useStarterKits.ts          # Starter-Kit-Daten aus API
```

### 5.2 Wizard-Schritte im Detail

**Schritt 1 — Begrüßung & Erfahrungsstufe:**
- Große, freundliche Überschrift: "Willkommen bei Kamerplanter!"
- Unterzeile: "Lass uns dein Setup in wenigen Schritten einrichten."
- 3 Karten zur Auswahl der Erfahrungsstufe:
  - **Einsteiger** (Icon: Seedling) — "Ich fange gerade an. Zeig mir nur das Wichtigste."
  - **Fortgeschritten** (Icon: Plant) — "Ich habe Erfahrung und möchte mehr Kontrolle."
  - **Experte** (Icon: Science) — "Ich kenne VPD, EC und NPK. Zeig mir alles."
- "Überspringen"-Link am unteren Rand (setzt Default: `beginner`)

**Schritt 2 — Anbau-Szenario wählen:**
- Grid (2 Spalten Desktop, 1 Spalte Mobile) mit StarterKitCards
- Jede Karte zeigt: Icon/Bild, Name, Kurzbeschreibung, Schwierigkeits-Badge, Pflanzenanzahl
- Filterbar nach Schwierigkeit (Tabs: Alle / Einsteiger / Fortgeschritten)
- Option "Eigenes Setup" am Ende (überspringt Schritt 3+4 und leitet zum manuellen Flow)
- Karten sind nach `sort_order` sortiert, Einsteiger-Kits zuerst

**Schritt 3 — Standort einrichten:**
- 1 Textfeld: Standort-Name (Default aus Kit: z.B. "Meine Fensterbank")
- Standorttyp als Icon-Auswahl (vorbelegt aus Kit, änderbar):
  - Fensterbank (Icon: Window)
  - Balkon (Icon: Balcony)
  - Garten (Icon: Yard)
  - Growzelt (Icon: Tent)
  - Gewächshaus (Icon: Greenhouse)
  - Innenraum (Icon: Room)
- Optionaler Freitext für Notizen
- **Optionaler Abschnitt "Dein Wasser"** (nur ab Erfahrungsstufe `intermediate`, bei `beginner` ausgeblendet gemäß REQ-021):
  - Toggle: "Osmoseanlage vorhanden?" (Switch, Default: aus)
  - Schnelleingabe: EC-Wert des Leitungswassers (Textfeld, Einheit: mS/cm, Placeholder: "z.B. 0.4")
  - Schnelleingabe: pH-Wert des Leitungswassers (Textfeld, Placeholder: "z.B. 7.2")
  - Hinweistext: "Du kannst dein Wasserprofil später in den Standort-Einstellungen erweitern."
  - Die eingegebenen Werte werden beim Wizard-Abschluss in `Site.water_source` übernommen (TapWaterProfile mit `ec_ms` und `ph`, WaterSource mit `has_ro_system`)

**Schritt 4 — Pflanzen auswählen:**
- Liste der im Kit enthaltenen Species mit Checkbox (alle vorausgewählt)
- Jede Species-Zeile zeigt: Trivialname (DE), wissenschaftlicher Name (grau), Schwierigkeits-Badge
- Pflanzenanzahl-Slider (1–20, Default aus Kit)
- Hinweistext: "Du kannst später jederzeit weitere Pflanzen hinzufügen."

**Schritt 5 — Zusammenfassung & Abschluss:**
- Übersicht aller erstellten Entitäten:
  - "Standort: Meine Fensterbank (Fensterbank)"
  - "5 Pflanzen: Basilikum, Minze, Petersilie, Schnittlauch, Dill"
- "Setup abschließen"-Button (ruft POST /onboarding/complete auf)
- Loading-Animation während der Entitäts-Erzeugung
- Nach Erfolg: Konfetti-Animation (optional), Weiterleitung zum Dashboard mit Willkommensnachricht
- Erste Tasks werden direkt auf dem Dashboard angezeigt

### 5.3 Wizard-Trigger

- **Erststart:** Wizard startet automatisch, wenn `onboarding_state.completed == false && onboarding_state.skipped == false`
- **Wiederaufruf:** Über Hauptmenü → Einstellungen → "Neues Szenario hinzufügen" oder über `/onboarding`-Route
- **Skip:** "Überspringen"-Link auf Schritt 1. Setzt `skipped: true`, experience_level auf `beginner`

### 5.4 Responsive Design

| Breakpoint | Layout |
|-----------|--------|
| `>= 1024px` (Desktop) | Zentrierter Wizard-Container (max 800px breit), Kit-Grid 2 Spalten |
| `768px–1023px` (Tablet) | Volle Breite, Kit-Grid 2 Spalten |
| `< 768px` (Mobile) | Volle Breite, Kit-Grid 1 Spalte, Swipe zwischen Steps möglich |

### 5.5 i18n-Schlüssel

```
pages.onboarding.welcome.title
pages.onboarding.welcome.subtitle
pages.onboarding.experience.beginner.label
pages.onboarding.experience.beginner.description
pages.onboarding.experience.intermediate.label
pages.onboarding.experience.intermediate.description
pages.onboarding.experience.expert.label
pages.onboarding.experience.expert.description
pages.onboarding.scenario.title
pages.onboarding.scenario.subtitle
pages.onboarding.scenario.customSetup
pages.onboarding.site.title
pages.onboarding.site.namePlaceholder
pages.onboarding.site.water.title
pages.onboarding.site.water.roToggle
pages.onboarding.site.water.ecLabel
pages.onboarding.site.water.ecPlaceholder
pages.onboarding.site.water.phLabel
pages.onboarding.site.water.phPlaceholder
pages.onboarding.site.water.hint
pages.onboarding.plants.title
pages.onboarding.plants.countLabel
pages.onboarding.plants.addLaterHint
pages.onboarding.completion.title
pages.onboarding.completion.summary
pages.onboarding.completion.finishButton
pages.onboarding.skip
pages.onboarding.back
pages.onboarding.next
```

### 5.6 Redux-State

```typescript
interface OnboardingState {
  status: 'idle' | 'loading' | 'completed' | 'skipped' | 'error';
  currentStep: number;
  experienceLevel: 'beginner' | 'intermediate' | 'expert';
  selectedKitId: string | null;
  siteName: string;
  siteType: string;
  plantCount: number;
  selectedSpeciesKeys: string[];
  selectedCultivarKeys: string[];
  createdEntities: OnboardingCreatedEntities | null;
  error: string | null;
}
```

## 6. Akzeptanzkriterien

### Funktional:
- [ ] Wizard startet automatisch beim ersten Systemzugang (wenn `onboarding_state` nicht existiert oder `completed == false && skipped == false`)
- [ ] Wizard ist in weniger als 3 Minuten abschließbar
- [ ] Nach Wizard-Abschluss existieren mindestens: 1 Site, 1 Location, 1+ PlantInstances, 1 PlantingRun
- [ ] Alle erstellten Entitäten haben sinnvolle Vorgabewerte aus dem Starter-Kit
- [ ] GrowthPhases werden automatisch aus den Species-Seed-Daten konfiguriert
- [ ] Der gewählte UI-Modus wird als `UserPreference.experience_level` persistiert
- [ ] Initiale Tasks werden basierend auf dem WorkflowTemplate des Kits generiert
- [ ] Wizard ist i18n-fähig (DE/EN)
- [ ] Jeder Schritt hat einen Zurück-Button (außer Schritt 1)
- [ ] Wizard kann jederzeit über Einstellungen erneut aufgerufen werden
- [ ] "Überspringen" setzt `experience_level` auf `beginner` und markiert Onboarding als übersprungen
- [ ] Mindestens 5 Starter-Kits mit vollständigen Seed-Daten vorhanden
- [ ] Alle in Starter-Kits referenzierten Species existieren als vollständige Seed-Daten (BotanicalFamily, Species, LifecycleConfig, GrowthPhases, RequirementProfiles)
- [ ] Optionaler "Dein Wasser"-Abschnitt in Schritt 3 wird ab Erfahrungsstufe `intermediate` angezeigt, bei `beginner` ausgeblendet (REQ-021)
- [ ] Wizard-Abschluss mit `has_ro_system`, `tap_water_ec_ms` und `tap_water_ph` erstellt `Site.water_source` mit TapWaterProfile
- [ ] Wizard-Abschluss ohne Wasserquellen-Daten erstellt Site mit `water_source=null` (Abwärtskompatibilität)
- [ ] Starter-Kits mit toxischen Pflanzen zeigen `toxicity_warning` an (Haustier-Hinweis)

### Technisch:
- [ ] Alle Entitäts-Erzeugungen in einer ArangoDB-Transaktion
- [ ] Rollback bei Fehler in beliebigem Erzeugungsschritt
- [ ] OnboardingState wird bei jedem Wizard-Schritt gespeichert (Resume nach Browser-Schließen)
- [ ] API-Endpunkte folgen NFR-006 Error-Handling (ErrorResponse-Format)
- [ ] Frontend-Komponenten haben vitest-Tests
- [ ] Responsive Design für Desktop, Tablet und Mobile

## 7. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Onboarding-Status | Ja | Ja | — |
| Starter-Kits (Katalog) | Nein | — | — |
| Starter-Kits (Anwenden) | — | Ja | — |
| User Preferences | Ja | Ja | Ja |

## 8. Abhängigkeiten

| REQ/NFR | Art | Beschreibung |
|---------|-----|-------------|
| REQ-001 | Liest/Erzeugt | BotanicalFamily, Species, Cultivar aus Starter-Kit-Daten |
| REQ-002 | Erzeugt | Site und Location im Wizard; optional `Site.water_source` mit TapWaterProfile aus Wizard-Eingaben |
| REQ-003 | Erzeugt | GrowthPhases und RequirementProfiles aus Seed-Daten |
| REQ-006 | Erzeugt | Initiale Tasks aus WorkflowTemplates des Kits |
| REQ-013 | Erzeugt | PlantingRun mit Entries für die angelegten PlantInstances |
| REQ-021 | Setzt | `experience_level` als Grundlage für den UI-Modus |
| NFR-006 | Einhält | API-Fehlerbehandlung (ErrorResponse) |
| NFR-010 | Erweitert | Neue Seitentypen (Wizard) ergänzend zu CRUD-Masken |
