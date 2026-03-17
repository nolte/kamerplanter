# Spezifikation: REQ-020 - Onboarding-Wizard

```yaml
ID: REQ-020
Titel: Geführter Onboarding-Wizard für Erstnutzer
Kategorie: Benutzerführung
Fokus: Frontend (Backend-Unterstützung für Starter-Kits und Präferenzen)
Technologie: React, TypeScript, MUI, Redux Toolkit, FastAPI, ArangoDB
Status: Entwurf
Version: 1.6 (Smart-Home-Deaktivierung: UserPreference smart_home_enabled)
Abhängigkeit: REQ-001 v4.0 (Stammdaten-Scoping), REQ-004 v3.2 (Nährstoffpläne), REQ-024 v1.3 (Platform-Tenant), REQ-027 v1.2 (Moduswechsel)
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.6 | 2026-03-17 | **Smart-Home-Deaktivierung:** Neues `UserPreference`-Feld `smart_home_enabled: bool` (Default: `false`). Erlaubt Nutzern die vollständige Deaktivierung aller Smart-Home- und Sensor-Funktionen. Bei `smart_home_enabled == false` werden Sensoren, Aktoren, Live-EC-Berechnung, automatische EC-Übernahme beim Düngen und alle sensorabhängigen Dashboard-Widgets ausgeblendet. Vereinfacht die UI für Nutzer ohne Home Assistant / IoT-Hardware. Toggle im Onboarding (Schritt 2) und AccountSettingsPage. Querverweis: REQ-005 §4b, REQ-004, REQ-014. |
| 1.5 | 2026-03-16 | **Favoriten-System im Onboarding:** Neues Konzept `user_favorites` (Edge-Collection). Schritt 4 erweitert um Favoriten-Toggle pro Species. Neuer Schritt 4b: Passende Nährstoffpläne für favorisierte Pflanzen anzeigen und als Favorit wählen. **Dünger-Kaskade:** Beim Favorisieren eines Nährstoffplans werden alle enthaltenen Dünger automatisch als Favoriten markiert (`source: 'cascade'`). StarterKit um `nutrient_plan_keys` erweitert. Neue API-Endpoints für Favoriten. Neue User Stories, Akzeptanzkriterien. |
| 1.4 | 2026-03-16 | **Moduswechsel-Onboarding:** OnboardingState-Ownership bei Moduswechsel (Light→Full: neuer User bekommt eigenen State; Full→Light: System-User-State wird zurückgesetzt). Onboarding-Trigger nach Übernahme/Ablehnung des System-Tenants. **Starter-Kit tenant_has_access:** Kit-Validierung gegen `tenant_has_access`-Kanten — nicht zugewiesene Species werden ausgefiltert oder Kit wird ausgeblendet. Neue Szenarien, Abnahmekriterien. |
| 1.3 | 2026-03 | Agrarbiologie-Review Korrekturen |

## 1. Business Case

**User Story (Erstnutzer):** "Als Hobby-Gärtner, der zum ersten Mal Kamerplanter öffnet, möchte ich in weniger als 3 Minuten meine ersten Pflanzen im System haben — ohne Fachbegriffe verstehen oder komplexe Formulare ausfüllen zu müssen."

**User Story (Szenario-Auswahl):** "Als Einsteiger möchte ich aus vorkonfigurierten Szenarien wählen können (z.B. 'Kräuter auf der Fensterbank', 'Tomaten auf dem Balkon') — damit das System automatisch alle nötigen Stammdaten, Standorte und Pflanzen für mich anlegt."

**User Story (Erfahrungsstufe):** "Als Nutzer möchte ich beim ersten Start meine Erfahrungsstufe angeben können — damit das System mir nur die Funktionen und Felder zeigt, die zu meinem Wissensstand passen."

**User Story (Wiederaufruf):** "Als Nutzer möchte ich den Onboarding-Wizard jederzeit erneut aufrufen können — um ein weiteres Anbau-Szenario hinzuzufügen oder meine Erfahrungsstufe zu ändern."

**User Story (Smart-Home-Deaktivierung):** "Als Nutzer ohne Smart-Home-Geräte möchte ich beim Onboarding angeben können, dass ich keine Sensoren oder Aktoren nutze — damit die Oberfläche übersichtlicher wird und ich nicht von technischen Optionen verwirrt werde, die für mich irrelevant sind."

<!-- Quelle: Favoriten-System v1.5 -->
**User Story (Pflanzen-Favoriten):** "Als Nutzer möchte ich im Onboarding-Wizard meine Lieblingspflanzen als Favoriten markieren können — damit das System mir später bei Düngung, Pflege und Einkauf gezielt Empfehlungen für meine favorisierten Pflanzen anzeigen kann."

**User Story (Nährstoffplan-Favoriten):** "Als Nutzer möchte ich im Onboarding-Wizard passende Nährstoffpläne für meine favorisierten Pflanzen sehen und als Favoriten speichern können — damit ich sofort einen bewährten Düngeplan für meine Pflanzen habe, ohne selbst einen erstellen zu müssen."

**User Story (Dünger-Kaskade):** "Als Nutzer möchte ich, dass beim Favorisieren eines Nährstoffplans automatisch alle darin enthaltenen Düngerprodukte als Favoriten markiert werden — damit meine Einkaufsliste und der Dünger-Katalog sofort auf die Produkte gefiltert werden können, die ich tatsächlich brauche."
<!-- /Quelle: Favoriten-System v1.5 -->

**Beschreibung:**
Das aktuelle System setzt bei der Erstnutzung umfangreiches Domänenwissen voraus: Um eine einzelne Pflanze anzulegen, sind mindestens 5–6 Schritte über verschiedene Entitäten nötig (BotanicalFamily → Species → Site → Location → PlantInstance → GrowthPhase). Der Onboarding-Wizard reduziert diesen Prozess auf 4 interaktive Schritte und erstellt alle benötigten Entitäten automatisch im Hintergrund.

**Kernkonzepte:**

**Starter-Kits als vorkonfigurierte Datenpakete:**
Ein Starter-Kit bündelt alle Stammdaten, die für ein bestimmtes Anbau-Szenario benötigt werden: BotanicalFamilies, Species mit Cultivars, vorkonfigurierte GrowthPhases mit RequirementProfiles und optionale WorkflowTemplates. Starter-Kits werden als Seed-Daten im Backend bereitgestellt und beim Onboarding in die Nutzerdaten übernommen.

**Erfahrungsstufe als systemweite Präferenz:**
Die im Wizard gewählte Erfahrungsstufe wird als `UserPreference` persistiert und steuert den UI-Modus (siehe REQ-021). Der Wizard ist der primäre Einstiegspunkt für die Modus-Auswahl, kann aber jederzeit in den Einstellungen geändert werden.

**Automatische Entitäts-Erzeugung:**
Der Wizard erstellt auf Basis der Nutzer-Eingaben automatisch alle benötigten Entitäten in der korrekten Reihenfolge, einschließlich Graph-Kanten (belongs_to, grows_at, etc.).

<!-- Quelle: Favoriten-System v1.5 -->
**Favoriten als persönliche Schnellzugriffe:**
Favoriten sind nutzerbezogene Markierungen auf bestehenden Entitäten (Species, NutrientPlan, Fertilizer). Sie dienen als persönlicher Filter für Kataloge, Empfehlungen und Einkaufslisten. Favoriten werden im Onboarding als erster Einstiegspunkt gesetzt und können jederzeit in den jeweiligen Detailansichten hinzugefügt oder entfernt werden.

**Favoriten-Kaskade (NutrientPlan → Fertilizer):**
Wenn ein Nährstoffplan als Favorit markiert wird, werden automatisch alle in dessen `FertilizerDosage`-Einträgen referenzierten Düngerprodukte ebenfalls als Favoriten des Nutzers angelegt. Die kaskadierten Favoriten werden mit `source: 'cascade'` gekennzeichnet, sodass sie bei Entfernung des Plan-Favoriten wieder entfernt werden können (Soft-Kaskade). Manuell gesetzte Dünger-Favoriten (`source: 'manual'`) bleiben davon unberührt.
<!-- /Quelle: Favoriten-System v1.5 -->

**Abgrenzung:**
- Kein Account-Management — der Wizard setzt ein existierendes (ggf. anonymes) System voraus. Authentifizierung ist nicht Teil dieser REQ (siehe NFR-001 JWT-Auth).
- Kein Import externer Daten — der Wizard nutzt ausschließlich vorkonfigurierte Starter-Kits.
- Keine KI-basierte Empfehlung — die Szenario-Auswahl ist manuell.

<!-- Quelle: Moduswechsel-Onboarding v1.4 -->
### 1.1 Szenarien: Onboarding bei Moduswechsel

**Szenario A: Upgrade Light→Full — User übernimmt System-Tenant**
```
Voraussetzung: Light-Modus, System-User hat Onboarding abgeschlossen (30 Pflanzen)
  OnboardingState für system-user: completed=true, selected_kit_id="balkon-tomaten"

1. Admin ändert KAMERPLANTER_MODE=full, startet neu
2. Nutzer Anna registriert sich, übernimmt System-Tenant (REQ-027 Szenario 5)
3. System prüft: Hat Anna einen eigenen OnboardingState? → Nein
4. System erstellt OnboardingState für Anna:
   completed=true, skipped=false
   Begründung: Anna hat den System-Tenant MIT Daten übernommen —
   erneutes Onboarding ist nicht nötig, die Pflanzen sind da
5. Anna sieht Dashboard mit 30 Pflanzen, KEIN Wizard-Start
6. Anna kann jederzeit über Einstellungen → "Neues Szenario hinzufügen"
   den Wizard erneut aufrufen
```

**Szenario B: Upgrade Light→Full — User lehnt Übernahme ab**
```
Voraussetzung: Wie Szenario A

1-2. Wie Szenario A, aber Anna lehnt Übernahme ab
3. System erstellt persönlichen Tenant für Anna (REQ-024)
4. System prüft: Hat Anna einen eigenen OnboardingState? → Nein
5. System erstellt OnboardingState für Anna:
   completed=false, skipped=false, wizard_step=1
6. Wizard startet automatisch — Anna hat einen leeren Tenant
7. Anna durchläuft den Wizard: Erfahrungsstufe → Kit → Standort → Pflanzen → Fertig
8. Dashboard zeigt die neuen Pflanzen
```

**Szenario C: Downgrade Full→Light**
```
Voraussetzung: Full-Modus, Anna (30 Pflanzen im System-Tenant), Max (5 Pflanzen in eigenem Tenant)
  System-User-OnboardingState: completed=true (aus Light-Phase)

1. Admin ändert KAMERPLANTER_MODE=light, startet neu
2. System-User wird reaktiviert (REQ-027 Szenario 7)
3. System prüft: Hat System-User einen OnboardingState?
   a) Ja, completed=true → Kein Wizard, direkt zum Dashboard
   b) Nein → OnboardingState wird erstellt (completed=false) → Wizard startet
4. System-User arbeitet im System-Tenant mit Annas 30 Pflanzen
   (weil Anna den System-Tenant übernommen hatte und er jetzt reaktiviert wurde)
```

**Szenario D: Downgrade Full→Light — System-Tenant war nicht übernommen**
```
Voraussetzung: Full-Modus, niemand hat System-Tenant übernommen (Szenario 6/B)
  System-Tenant hat noch die originalen Light-Modus-Daten (30 Pflanzen)

1. Admin ändert KAMERPLANTER_MODE=light, startet neu
2. System-User wird reaktiviert, System-Tenant wird reaktiviert
3. OnboardingState des System-Users: completed=true → Kein Wizard
4. System-User sieht die originalen 30 Pflanzen — alles wie vorher
```

**Szenario E: Roundtrip — Neuer User nach Downgrade+Upgrade**
```
Phase 1 (Light): System-User hat 10 Pflanzen
Phase 2 (Full): Anna übernimmt, fügt 20 Pflanzen hinzu (= 30)
Phase 3 (Light): System-User sieht 30 Pflanzen
Phase 4 (Full): Anna meldet sich an

1. System prüft: Annas OnboardingState existiert (completed=true)
2. Anna sieht Übernahme-Dialog für System-Tenant (mit 30 Pflanzen)
3. Anna übernimmt → Dashboard mit 30 Pflanzen, kein Wizard
```

### 1.2 Starter-Kits und Stammdaten-Scoping

Mit dem Stammdaten-Scoping (REQ-001 v4.0) sind Species per `tenant_has_access`-Kante gefiltert. Starter-Kits referenzieren `species_keys` — diese Referenzen müssen gegen die Sichtbarkeit im aktuellen Tenant validiert werden.

**Regeln:**

1. **Kit-Auflistung filtern:** `GET /api/v1/starter-kits` zeigt nur Kits an, bei denen **mindestens eine** der referenzierten Species dem aktuellen Tenant zugewiesen ist.

2. **Nicht zugewiesene Species im Kit markieren:** Wenn ein Kit 5 Species referenziert, aber nur 3 dem Tenant zugewiesen sind, werden die 2 nicht zugewiesenen Species:
   - In der Kit-Detail-Ansicht ausgegraut mit Hinweis: "Nicht verfügbar in diesem Garten"
   - In Schritt 4 (Pflanzenauswahl) nicht vorausgewählt und nicht auswählbar
   - `species_count` im Kit-Summary zeigt die **verfügbare** Anzahl (nicht die Gesamt-Anzahl)

3. **Kit ausblenden wenn keine Species verfügbar:** Wenn keine einzige Species des Kits dem Tenant zugewiesen ist, wird das Kit in der Auflistung nicht angezeigt.

4. **Light-Modus / Auto-Assign:** Im Light-Modus und bei Tenants mit `auto_assign_master_data=true` sind alle globalen Species zugewiesen — alle Kits sind sichtbar mit allen Species.

**Szenario F: Starter-Kit mit teilweise nicht zugewiesenen Species**
```
Voraussetzung: Enterprise-Modus, Tenant "Cannabis Club" hat nur Cannabis-Species zugewiesen

1. User öffnet Onboarding-Wizard
2. GET /api/v1/starter-kits → gefiltert nach tenant_has_access
3. Sichtbar:
   ✅ "Indoor Growzelt" (Cannabis sativa → zugewiesen)
4. Nicht sichtbar:
   ❌ "Fensterbank-Kräuter" (keine Species zugewiesen)
   ❌ "Balkon-Tomaten" (keine Species zugewiesen)
   ❌ "Zimmerpflanzen" (keine Species zugewiesen)
5. User wählt "Indoor Growzelt" → alle Species sind verfügbar
```

**Szenario G: Kein Kit verfügbar**
```
Voraussetzung: Enterprise-Modus, Tenant hat nur tenant-eigene Species (keine globalen)

1. User öffnet Onboarding-Wizard
2. Kein Starter-Kit hat zugewiesene Species → Kit-Liste ist leer
3. Wizard zeigt Hinweis: "Für diesen Garten sind keine vorkonfigurierten Szenarien
   verfügbar. Du kannst deine Pflanzen manuell einrichten."
4. "Eigenes Setup"-Option wird prominent angezeigt
5. User wählt "Eigenes Setup" → wird zum manuellen Anlage-Flow weitergeleitet
```
<!-- /Quelle: Moduswechsel-Onboarding v1.4 -->

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
    - `nutrient_plan_keys: list[str]` (Referenzen auf NutrientPlan-Dokumente — passende Nährstoffpläne für dieses Kit, z.B. `["nutrient_plans/tomate-plagron-terra", "nutrient_plans/basilikum-plagron-terra"]`)
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
    - `smart_home_enabled: bool` (Default: `false`) — **Smart-Home-Gesamtschalter.** Steuert die Sichtbarkeit und Verfügbarkeit aller sensorik- und aktorik-bezogenen Funktionen im gesamten System. Bei `false` werden sämtliche Smart-Home-Elemente ausgeblendet (Sensoren, Aktoren, Live-EC, automatische Messwertübernahme, sensorabhängige Dashboard-Widgets). Kann im Onboarding (Schritt 2) und jederzeit in den AccountSettings geändert werden. Siehe REQ-005 §4b für die vollständige UI-Visibility-Matrix. Unabhängig von `ha_token_set` — auch bei vorhandenem HA-Token werden Smart-Home-Funktionen ausgeblendet, wenn `smart_home_enabled == false`.

### Edges:

```
includes_species:        starter_kits → species              (Kit enthält Species)
includes_cultivar:       starter_kits → cultivars             (Kit enthält Cultivar)
includes_template:       starter_kits → workflow_templates     (Kit enthält WorkflowTemplate)
includes_nutrient_plan:  starter_kits → nutrient_plans         (Kit empfiehlt NutrientPlan)
created_by_wizard:       onboarding_states → plant_instances   (Wizard hat PlantInstance erstellt)
user_favorites:          users → species | nutrient_plans | fertilizers  (User hat Entität favorisiert)
```

<!-- Quelle: Favoriten-System v1.5 -->
**Edge `:user_favorites` — Nutzer-Favoriten:**
- Collection: `user_favorites` (Edge-Collection)
- Von: `users/{user_key}`
- Nach: `species/{key}` | `nutrient_plans/{key}` | `fertilizers/{key}`
- Properties:
  - `source: Literal['manual', 'onboarding', 'cascade']` — Herkunft des Favoriten:
    - `manual`: Vom Nutzer explizit in einer Detailansicht gesetzt
    - `onboarding`: Im Onboarding-Wizard gesetzt
    - `cascade`: Automatisch durch Favorisierung eines NutrientPlans kaskadiert (Dünger)
  - `cascade_from_key: Optional[str]` — Nur bei `source: 'cascade'`: Key des NutrientPlans, der die Kaskade ausgelöst hat. Ermöglicht gezieltes Entfernen bei De-Favorisierung des Plans.
  - `favorited_at: datetime` — Zeitpunkt der Favorisierung
- **Unique Constraint:** Pro User und Ziel-Entität kann maximal ein Favorit existieren (`_from` + `_to` unique). Wenn ein Favorit bereits als `cascade` existiert und der Nutzer ihn manuell bestätigt, wird `source` auf `manual` hochgestuft (manuell gesetzte Favoriten werden bei Kaskaden-Entfernung nicht gelöscht).
<!-- /Quelle: Favoriten-System v1.5 -->

### Indizes:

```
starter_kits:
  - PERSISTENT INDEX on [kit_id] UNIQUE
  - PERSISTENT INDEX on [difficulty, sort_order]

onboarding_states:
  - PERSISTENT INDEX on [completed]

user_favorites:
  - PERSISTENT INDEX on [_from, _to] UNIQUE
  - PERSISTENT INDEX on [_from, source]
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
    nutrient_plans: list[dict]  # Vereinfachte NutrientPlan-Darstellung (key, name, description, species_match)

class OnboardingCreatedEntities(BaseModel):
    """Tracking der vom Wizard erstellten Entitäten."""
    site_key: Optional[str] = None
    location_keys: list[str] = Field(default_factory=list)
    plant_instance_keys: list[str] = Field(default_factory=list)
    planting_run_key: Optional[str] = None
    favorite_species_keys: list[str] = Field(default_factory=list)
    favorite_nutrient_plan_keys: list[str] = Field(default_factory=list)
    favorite_fertilizer_keys: list[str] = Field(default_factory=list)  # Via Kaskade

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
    # Favoriten (v1.5)
    favorite_species_keys: list[str] = Field(
        default_factory=list,
        description="Species-Keys die der Nutzer als Favoriten markiert hat. "
                    "Kann leer sein — keine Pflicht, Favoriten zu setzen."
    )
    favorite_nutrient_plan_keys: list[str] = Field(
        default_factory=list,
        description="NutrientPlan-Keys die der Nutzer als Favoriten markiert hat. "
                    "Löst automatische Dünger-Kaskade aus."
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
        7. Favoriten: Species → user_favorites Edges (source: 'onboarding')
        8. Favoriten: NutrientPlans → user_favorites Edges (source: 'onboarding')
        9. Dünger-Kaskade: Für jeden favorisierten NutrientPlan →
           alle FertilizerDosage-Einträge auflösen →
           Fertilizer → user_favorites Edges (source: 'cascade', cascade_from_key)

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

    def _create_favorites(
        self,
        user_key: str,
        species_keys: list[str],
        nutrient_plan_keys: list[str],
    ) -> dict:
        """
        Erstellt Favoriten-Edges in user_favorites:
        1. Species-Favoriten: user → species (source: 'onboarding')
        2. NutrientPlan-Favoriten: user → nutrient_plan (source: 'onboarding')
        3. Dünger-Kaskade: Für jeden favorisierten NutrientPlan:
           - Alle NutrientPlanPhaseEntry-Dokumente laden
           - Alle FertilizerDosage-Einträge extrahieren
           - Für jeden Fertilizer: user → fertilizer (source: 'cascade',
             cascade_from_key: nutrient_plan_key)

        Idempotent: Wenn ein Favorit bereits existiert (z.B. gleicher
        Dünger in zwei Plänen), wird der bestehende Edge nicht dupliziert.
        Bei Hochstufung cascade→onboarding wird source aktualisiert.

        Returns: dict mit favorite_species_keys, favorite_nutrient_plan_keys,
                 favorite_fertilizer_keys
        """
        ...
```

<!-- Quelle: Favoriten-System v1.5 -->
**3. FavoritesService — Favoriten-Verwaltung:**
```python
class FavoritesService:
    """Verwaltung der Nutzer-Favoriten (Species, NutrientPlan, Fertilizer).

    Favoriten sind systemweit verfügbar — nicht nur im Onboarding-Kontext.
    Der Onboarding-Wizard nutzt diesen Service, um initiale Favoriten zu setzen.
    """

    def add_favorite(
        self,
        user_key: str,
        target_key: str,
        source: str = "manual",
        cascade_from_key: str | None = None,
    ) -> dict:
        """Setzt einen Favoriten. Idempotent — bei Duplikat wird
        source ggf. hochgestuft (cascade→manual/onboarding)."""
        ...

    def remove_favorite(
        self,
        user_key: str,
        target_key: str,
        cascade_cleanup: bool = True,
    ) -> None:
        """Entfernt einen Favoriten.
        Wenn cascade_cleanup=True und target ein NutrientPlan ist:
        Entfernt alle kaskadierten Dünger-Favoriten (source='cascade',
        cascade_from_key=target_key), SOFERN der Dünger nicht auch
        von einem anderen Plan oder manuell favorisiert wurde."""
        ...

    def list_favorites(
        self,
        user_key: str,
        entity_type: str | None = None,
    ) -> list[dict]:
        """Alle Favoriten eines Nutzers, optional nach Typ gefiltert.
        entity_type: 'species', 'nutrient_plans', 'fertilizers' oder None (alle)."""
        ...

    def get_matching_nutrient_plans(
        self,
        species_keys: list[str],
        tenant_key: str,
    ) -> list[dict]:
        """Findet NutrientPlans die zu den gegebenen Species passen.

        Matching-Logik:
        1. NutrientPlans mit is_template=true im Tenant oder global
        2. Match über Tags, recommended_substrate_type oder
           explizite species_keys auf dem StarterKit
        3. Sortierung: Relevanz (Anzahl passender Species) absteigend

        Returns: Liste mit plan_key, name, description, matched_species,
                 fertilizer_count, difficulty_estimate
        """
        ...

    def _cascade_fertilizers(
        self,
        user_key: str,
        nutrient_plan_key: str,
    ) -> list[str]:
        """Kaskadiert Dünger-Favoriten aus einem NutrientPlan.

        1. Lade alle NutrientPlanPhaseEntry für den Plan
        2. Extrahiere alle fertilizer_keys aus FertilizerDosage-Einträgen
        3. Dedupliziere (ein Dünger kann in mehreren Phasen vorkommen)
        4. Erstelle user_favorites Edges (source='cascade')

        Returns: Liste der kaskadierten Fertilizer-Keys
        """
        ...
```
<!-- /Quelle: Favoriten-System v1.5 -->

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

<!-- Quelle: Moduswechsel-Onboarding v1.4 -->
**3. StarterKitService — Tenant-Scoped Kit-Filterung:**

```python
class StarterKitService:
    # ... bestehende Methoden ...

    def list_kits_for_tenant(
        self,
        tenant_key: str,
        difficulty: Optional[str] = None,
        locale: str = "de",
    ) -> list[StarterKitSummary]:
        """Kits gefiltert nach tenant_has_access.
        Nur Kits mit mindestens einer zugewiesenen Species werden angezeigt.
        species_count zeigt nur die verfügbare Anzahl."""
        all_kits = self.list_kits(difficulty, locale)
        accessible_species = self._get_accessible_species_keys(tenant_key)

        result = []
        for kit in all_kits:
            available = [s for s in kit.species_keys if s in accessible_species]
            if len(available) > 0:
                kit.species_count = len(available)
                kit.available_species_keys = available
                result.append(kit)
        return result

    def get_kit_detail_for_tenant(
        self,
        kit_id: str,
        tenant_key: str,
        locale: str = "de",
    ) -> StarterKitDetail:
        """Kit-Detail mit Species-Verfügbarkeit pro Tenant.
        Nicht zugewiesene Species werden als unavailable markiert."""
        kit = self.get_kit_detail(kit_id, locale)
        accessible = self._get_accessible_species_keys(tenant_key)
        for species in kit.species:
            species["available"] = species["key"] in accessible
        return kit

    def _get_accessible_species_keys(self, tenant_key: str) -> set[str]:
        """Gibt alle Species-Keys zurück, die dem Tenant zugewiesen sind
        (via tenant_has_access + tenant-eigene Species)."""
        ...
```

**4. OnboardingService — Moduswechsel-Handling:**

```python
class OnboardingService:
    # ... bestehende Methoden ...

    def ensure_onboarding_state_for_user(
        self,
        user_key: str,
        tenant_key: str,
        takeover_accepted: bool | None = None,
    ) -> OnboardingState:
        """Stellt sicher, dass der User einen OnboardingState hat.
        Wird nach Registrierung und nach Moduswechsel aufgerufen.

        Args:
            user_key: Der aktuelle User
            tenant_key: Der aktive Tenant des Users
            takeover_accepted: None = kein Moduswechsel,
                               True = System-Tenant übernommen (completed=true),
                               False = Übernahme abgelehnt (completed=false → Wizard startet)
        """
        existing = self._repo.get_by_user(user_key)
        if existing:
            return existing

        if takeover_accepted is True:
            # User hat System-Tenant MIT Daten übernommen → kein Wizard nötig
            return self._repo.create(OnboardingState(
                completed=True,
                skipped=False,
                completed_at=datetime.now(UTC),
                selected_kit_id=None,  # Unbekannt (wurde vom System-User gewählt)
                selected_experience_level="beginner",  # Default, User kann in Settings ändern
                wizard_step=5,
            ), user_key=user_key)

        # Neuer User oder Übernahme abgelehnt → Wizard starten
        return self._repo.create(OnboardingState(
            completed=False,
            skipped=False,
            wizard_step=1,
        ), user_key=user_key)

    def reset_system_user_onboarding(self) -> None:
        """Setzt den OnboardingState des System-Users zurück.
        Wird beim Downgrade Full→Light aufgerufen, wenn der System-Tenant
        keine Daten mehr hat (z.B. nach Löschung durch KA-Admin)."""
        state = self._repo.get_by_user("system-user")
        if state and not self._tenant_has_data("system-tenant"):
            state.completed = False
            state.skipped = False
            state.wizard_step = 1
            self._repo.update(state)
```
<!-- /Quelle: Moduswechsel-Onboarding v1.4 -->

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
- Mindestens 1 passender NutrientPlan als Template (`is_template: true`) — referenziert über `nutrient_plan_keys` auf dem StarterKit

<!-- Quelle: Favoriten-System v1.5 -->
**Nährstoffplan-Zuordnung pro Kit:**

| Kit-ID | Nährstoffpläne | Substrat |
|--------|---------------|----------|
| `fensterbank-kraeuter` | Basilikum Plagron Terra, Schnittlauch Plagron Terra, Dill Plagron Terra, Petersilie Plagron Terra | Erde |
| `balkon-tomaten` | Tomate Plagron Terra | Erde |
| `kleines-gemusebeet` | Tomate Plagron Terra, Basilikum Plagron Terra, Salat Plagron Terra, Bohne Plagron Terra, Möhre Plagron Terra | Erde |
| `zimmerpflanzen` | Monstera Deliciosa Gardol | Erde |
| `zimmerpflanzen-haustierfreundlich` | Grünlilie Gardol | Erde |
| `indoor-growzelt` | *(Tenant-spezifisch — kein globaler Seed-Plan)* | Coco/Hydro |
| `chili-zucht` | Paprika Plagron Terra | Erde |
| `superhot-chili` | Paprika Plagron Terra | Erde |
| `microgreens` | *(Kein Nährstoffplan — Microgreens brauchen keine Düngung)* | — |
| `balkon-blumen` | Petunie Plagron Terra, Stiefmütterchen Plagron Terra | Erde |
| `balkon-blumen-voranzucht` | Petunie Plagron Terra, Stiefmütterchen Plagron Terra | Erde |

**Hinweis:** Die Nährstoffpläne werden aus den bestehenden Seed-Daten unter `spec/ref/nutrient-plans/` referenziert. Jeder Plan muss als `is_template: true` in der `nutrient_plans`-Collection existieren.
<!-- /Quelle: Favoriten-System v1.5 -->

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
| `GET` | `/api/v1/starter-kits` | Alle Kits auflisten (ungefiltert, z.B. für Dokumentation) | Nein |
| `GET` | `/api/v1/starter-kits/{kit_id}` | Kit-Detail mit aufgelösten Species/Cultivars (ungefiltert) | Nein |
| `POST` | `/api/v1/starter-kits/{kit_id}/apply` | Kit nachträglich anwenden (ohne Wizard) | Ja |

<!-- Quelle: Moduswechsel-Onboarding v1.4 -->
### Router: `/api/v1/t/{tenant_slug}/starter-kits` (Tenant-Scoped)

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/t/{tenant_slug}/starter-kits` | Kits gefiltert nach `tenant_has_access` — nur Kits mit verfügbaren Species. `?difficulty=beginner`-Filter. | Ja |
| `GET` | `/api/v1/t/{tenant_slug}/starter-kits/{kit_id}` | Kit-Detail mit Species-Verfügbarkeit (`available: true/false` pro Species) | Ja |

**Hinweis:** Der Onboarding-Wizard im Frontend verwendet die **tenant-scoped** Endpoints. Die ungefilterten Endpoints bleiben für öffentliche Dokumentation und KA-Admin-Übersicht erhalten.
<!-- /Quelle: Moduswechsel-Onboarding v1.4 -->

### Router: `/api/v1/user-preferences`

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/user-preferences` | Aktuelle Präferenzen abfragen | Ja |
| `PATCH` | `/api/v1/user-preferences` | Präferenzen aktualisieren (experience_level, locale, theme, temperature_unit) | Ja |

<!-- Quelle: Favoriten-System v1.5 -->
### Router: `/api/v1/favorites`

| Methode | Pfad | Beschreibung | Auth |
|---------|------|-------------|------|
| `GET` | `/api/v1/favorites` | Alle Favoriten des Nutzers abfragen. Optional `?type=species\|nutrient_plans\|fertilizers` Filter. | Ja |
| `POST` | `/api/v1/favorites` | Favorit setzen. Body: `{ "target_key": "species/...", "source": "manual" }` | Ja |
| `DELETE` | `/api/v1/favorites/{target_key}` | Favorit entfernen. Bei NutrientPlan: Kaskaden-Cleanup der Dünger-Favoriten. Query-Param `?cascade_cleanup=true` (Default). | Ja |
| `GET` | `/api/v1/favorites/nutrient-plans/matching` | Passende NutrientPlans für Species-Keys. Query: `?species_keys=species/abc,species/def` | Ja |
<!-- /Quelle: Favoriten-System v1.5 -->

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
  ],
  "favorite_species_keys": [
    "species/ocimum-basilicum",
    "species/mentha-spicata"
  ],
  "favorite_nutrient_plan_keys": [
    "nutrient_plans/basilikum-plagron-terra"
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
    "planting_run_key": "planting_runs/fensterbank-kraeuter-2026",
    "favorite_species_keys": [
      "species/ocimum-basilicum",
      "species/mentha-spicata"
    ],
    "favorite_nutrient_plan_keys": [
      "nutrient_plans/basilikum-plagron-terra"
    ],
    "favorite_fertilizer_keys": [
      "fertilizers/plagron-terra-grow",
      "fertilizers/plagron-terra-bloom",
      "fertilizers/plagron-pure-zym"
    ]
  },
  "dashboard_message": "Willkommen! Deine 5 Kräuter sind eingerichtet. 2 Favoriten-Pflanzen und 1 Düngeplan gespeichert. Hier sind deine ersten Aufgaben:",
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

<!-- Quelle: Favoriten-System v1.5 -->
**GET /api/v1/favorites/nutrient-plans/matching?species_keys=species/ocimum-basilicum,species/mentha-spicata**
```json
[
  {
    "plan_key": "nutrient_plans/basilikum-plagron-terra",
    "name": "Basilikum — Plagron Terra",
    "description": "Vollständiger Nährstoffplan für Basilikum in Erde (Plagron Terra-Linie)",
    "matched_species": ["species/ocimum-basilicum"],
    "fertilizer_count": 3,
    "fertilizers": [
      {"key": "fertilizers/plagron-terra-grow", "brand": "Plagron", "product_name": "Terra Grow"},
      {"key": "fertilizers/plagron-terra-bloom", "brand": "Plagron", "product_name": "Terra Bloom"},
      {"key": "fertilizers/plagron-pure-zym", "brand": "Plagron", "product_name": "Pure Zym"}
    ],
    "recommended_substrate_type": "soil",
    "is_template": true
  }
]
```
<!-- /Quelle: Favoriten-System v1.5 -->

## 5. Frontend-Spezifikation

### 5.1 Wizard-Komponenten

```
src/frontend/src/pages/onboarding/
├── OnboardingWizard.tsx           # Wizard-Container (MUI Stepper)
├── steps/
│   ├── WelcomeStep.tsx            # Schritt 1: Begrüßung & Erfahrungsstufe
│   ├── ScenarioStep.tsx           # Schritt 2: Starter-Kit-Auswahl
│   ├── SiteSetupStep.tsx          # Schritt 3: Standort einrichten
│   ├── PlantSelectionStep.tsx     # Schritt 4: Pflanzen auswählen, Favoriten & Anzahl
│   ├── NutrientPlanStep.tsx       # Schritt 5: Nährstoffpläne für Favoriten-Pflanzen
│   └── CompletionStep.tsx         # Schritt 6: Zusammenfassung & erste Tasks
├── components/
│   ├── StarterKitCard.tsx         # Kit-Vorschaukarte (Bild, Name, Schwierigkeit)
│   ├── ExperienceLevelSelector.tsx # 3-stufige Auswahl mit Icons und Beschreibung
│   ├── PlantCountSlider.tsx       # Slider für Pflanzenanzahl (1-20)
│   ├── SiteTypeSelector.tsx       # Standorttyp-Auswahl mit Icons
│   ├── FavoriteToggle.tsx         # Stern-Icon-Button für Favoriten-Toggle
│   └── NutrientPlanCard.tsx       # Plan-Vorschaukarte mit Dünger-Liste und Favoriten-Toggle
└── hooks/
    ├── useOnboardingState.ts      # Onboarding-Status aus API
    ├── useStarterKits.ts          # Starter-Kit-Daten aus API
    └── useMatchingNutrientPlans.ts # Passende Nährstoffpläne für Species
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
- **Smart-Home-Toggle** (unterhalb der Erfahrungsstufen-Auswahl):
  - Frage: "Nutzt du Smart-Home-Geräte oder Sensoren für deine Pflanzen?" (Switch, Default: aus)
  - Untertitel bei "Aus": "Kein Problem! Du kannst alles manuell erfassen. Sensoren und Automatisierung werden ausgeblendet."
  - Untertitel bei "An": "Sensoren, Aktoren und Live-Messwerte werden im System verfügbar."
  - Setzt `UserPreference.smart_home_enabled` (siehe REQ-005 §4b)
  - Bei `experience_level == 'beginner'` wird der Toggle **nicht angezeigt** (Default `false` wird übernommen — Einsteiger sollen nicht mit Smart-Home-Optionen konfrontiert werden)
  - Bei `experience_level == 'intermediate'` oder `'expert'` wird der Toggle sichtbar

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

**Schritt 4 — Pflanzen auswählen & Favoriten:**
- Liste der im Kit enthaltenen Species mit Checkbox (alle vorausgewählt)
- Jede Species-Zeile zeigt: Trivialname (DE), wissenschaftlicher Name (grau), Schwierigkeits-Badge
- **Favoriten-Toggle** (Stern-Icon) pro Species-Zeile: Nutzer kann einzelne Pflanzen als Favoriten markieren. Default: keine vorausgewählt. Favoriten sind optional — der Nutzer kann den Schritt auch ohne Favoriten abschließen.
- Hinweistext unter den Favoriten-Sternen: "Markiere deine Lieblingspflanzen — wir zeigen dir passende Düngepläne."
- Pflanzenanzahl-Slider (1–20, Default aus Kit)
- Hinweistext: "Du kannst später jederzeit weitere Pflanzen hinzufügen."
- **Bedingtes Weiterschalten:** Wenn mindestens eine Species als Favorit markiert wurde UND das Kit `nutrient_plan_keys` hat, geht "Weiter" zu Schritt 5 (Nährstoffpläne). Andernfalls springt "Weiter" direkt zu Schritt 6 (Zusammenfassung).

<!-- Quelle: Favoriten-System v1.5 -->
**Schritt 5 — Nährstoffpläne für Favoriten-Pflanzen (bedingt):**

Dieser Schritt wird nur angezeigt, wenn in Schritt 4 mindestens eine Species als Favorit markiert wurde UND passende Nährstoffpläne verfügbar sind. Andernfalls wird er übersprungen.

- **Überschrift:** "Düngepläne für deine Favoriten"
- **Unterzeile:** "Wähle bewährte Düngepläne für deine Lieblingspflanzen — die enthaltenen Dünger werden automatisch zu deinen Favoriten hinzugefügt."
- **Pro favorisierte Species** wird ein Abschnitt angezeigt:
  - Species-Name als Abschnittsüberschrift (z.B. "Basilikum")
  - Darunter: Liste passender NutrientPlans als `NutrientPlanCard`:
    - Plan-Name (z.B. "Basilikum — Plagron Terra")
    - Kurzbeschreibung
    - Empfohlenes Substrat (Badge)
    - **Dünger-Liste aufgeklappt:** Alle im Plan enthaltenen Düngerprodukte mit Brand + Name (z.B. "Plagron Terra Grow", "Plagron Terra Bloom", "Plagron Pure Zym")
    - **Favoriten-Toggle** (Stern-Icon) auf der Plan-Karte
    - **Kaskaden-Hinweis** (Info-Icon): "Wenn du diesen Plan favorisierst, werden die enthaltenen Dünger automatisch zu deinen Favoriten hinzugefügt."
- **Keine Pflicht:** Der Nutzer kann den Schritt ohne Favoriten-Auswahl durchlaufen.
- **Leerzustand:** Wenn keine passenden Pläne gefunden werden: "Für deine favorisierten Pflanzen sind noch keine Düngepläne hinterlegt. Du kannst später eigene Pläne erstellen."
- **Erfahrungsstufe-Adaption (REQ-021):**
  - `beginner`: Nur Plan-Name, Kurzbeschreibung und "X Dünger enthalten" — keine Detailliste der Dünger
  - `intermediate`/`expert`: Volle Dünger-Detailliste mit Brand, Produktname und Dosierungs-Übersicht
<!-- /Quelle: Favoriten-System v1.5 -->

**Schritt 6 — Zusammenfassung & Abschluss:**
- Übersicht aller erstellten Entitäten:
  - "Standort: Meine Fensterbank (Fensterbank)"
  - "5 Pflanzen: Basilikum, Minze, Petersilie, Schnittlauch, Dill"
<!-- Quelle: Favoriten-System v1.5 -->
  - "Favoriten: 2 Pflanzen, 1 Düngeplan, 3 Dünger" (nur angezeigt wenn Favoriten gesetzt)
<!-- /Quelle: Favoriten-System v1.5 -->
- "Setup abschließen"-Button (ruft POST /onboarding/complete auf)
- Loading-Animation während der Entitäts-Erzeugung
- Nach Erfolg: Konfetti-Animation (optional), Weiterleitung zum Dashboard mit Willkommensnachricht
- Erste Tasks werden direkt auf dem Dashboard angezeigt

### 5.3 Wizard-Trigger

- **Erststart:** Wizard startet automatisch, wenn `onboarding_state.completed == false && onboarding_state.skipped == false`
- **Wiederaufruf:** Über Hauptmenü → Einstellungen → "Neues Szenario hinzufügen" oder über `/onboarding`-Route
- **Skip:** "Überspringen"-Link auf Schritt 1. Setzt `skipped: true`, experience_level auf `beginner`
<!-- Quelle: Moduswechsel-Onboarding v1.4 -->
- **Nach Upgrade Light→Full (Übernahme akzeptiert):** Kein Wizard — `OnboardingState.completed=true` wird für den neuen User erstellt, da Daten bereits vorhanden sind
- **Nach Upgrade Light→Full (Übernahme abgelehnt):** Wizard startet automatisch — neuer User hat leeren Tenant, `OnboardingState.completed=false`
- **Nach Downgrade Full→Light:** System-User-OnboardingState wird geprüft:
  - `completed=true` + System-Tenant hat Daten → Kein Wizard
  - `completed=true` + System-Tenant hat keine Daten (gelöscht durch KA-Admin) → State wird zurückgesetzt, Wizard startet
  - State existiert nicht → Wird erstellt mit `completed=false`, Wizard startet
- **Kein Kit verfügbar (Enterprise):** Wenn nach `tenant_has_access`-Filterung kein Starter-Kit verfügbar ist, zeigt Schritt 2 nur die "Eigenes Setup"-Option prominent an
<!-- /Quelle: Moduswechsel-Onboarding v1.4 -->

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
pages.onboarding.plants.favoriteHint
pages.onboarding.nutrientPlans.title
pages.onboarding.nutrientPlans.subtitle
pages.onboarding.nutrientPlans.cascadeHint
pages.onboarding.nutrientPlans.emptyState
pages.onboarding.nutrientPlans.fertilizerCount
pages.onboarding.completion.title
pages.onboarding.completion.summary
pages.onboarding.completion.favoriteSummary
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
  // Favoriten (v1.5)
  favoriteSpeciesKeys: string[];
  favoriteNutrientPlanKeys: string[];
  matchingNutrientPlans: NutrientPlanMatch[] | null; // Gecachte API-Response
  createdEntities: OnboardingCreatedEntities | null;
  error: string | null;
}

interface NutrientPlanMatch {
  planKey: string;
  name: string;
  description: string;
  matchedSpecies: string[];
  fertilizerCount: number;
  fertilizers: { key: string; brand: string; productName: string }[];
  recommendedSubstrateType: string | null;
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
- [ ] **Smart-Home-Toggle:** In Schritt 1 wird ab Erfahrungsstufe `intermediate` ein Toggle "Nutzt du Smart-Home-Geräte?" angezeigt
- [ ] **Smart-Home-Toggle Default:** Bei `beginner` wird der Toggle nicht angezeigt und `smart_home_enabled` auf `false` gesetzt
- [ ] **Smart-Home-Toggle Persistierung:** Der Toggle-Wert wird als `UserPreference.smart_home_enabled` gespeichert
- [ ] **Smart-Home-Deaktivierung:** Bei `smart_home_enabled == false` werden nach Wizard-Abschluss keine Sensor/Aktor-Elemente in der UI angezeigt (siehe REQ-005 §4b)
- [ ] **Smart-Home nachträgliche Aktivierung:** Der Toggle kann jederzeit in AccountSettings → Integrationen geändert werden, ohne Datenverlust
<!-- Quelle: Favoriten-System v1.5 -->
- [ ] **Pflanzen-Favoriten:** In Schritt 4 kann der Nutzer per Stern-Icon einzelne Species als Favoriten markieren
- [ ] **Pflanzen-Favoriten optional:** Schritt 4 ist ohne Favoriten-Auswahl abschließbar
- [ ] **Nährstoffplan-Schritt bedingt:** Schritt 5 wird nur angezeigt wenn mindestens eine Species favorisiert wurde UND passende NutrientPlans existieren
- [ ] **Nährstoffplan-Matching:** `GET /api/v1/favorites/nutrient-plans/matching` liefert passende NutrientPlans für gegebene Species-Keys
- [ ] **Nährstoffplan-Favoriten:** In Schritt 5 kann der Nutzer per Stern-Icon NutrientPlans als Favoriten markieren
- [ ] **Dünger-Kaskade:** Beim Favorisieren eines NutrientPlans werden alle enthaltenen Dünger automatisch als Favoriten angelegt (`source: 'cascade'`, `cascade_from_key`)
- [ ] **Kaskaden-Cleanup:** Beim Entfernen eines NutrientPlan-Favoriten werden kaskadierte Dünger-Favoriten entfernt, sofern sie nicht manuell oder von einem anderen Plan favorisiert wurden
- [ ] **Favoriten-Idempotenz:** Doppelte Favoriten-Edges werden nicht erstellt; bei Hochstufung (cascade→manual/onboarding) wird `source` aktualisiert
- [ ] **Favoriten in Zusammenfassung:** Schritt 6 zeigt Anzahl der favorisierten Pflanzen, Pläne und (kaskadierte) Dünger
- [ ] **Favoriten persistiert:** Nach Wizard-Abschluss sind alle Favoriten über `GET /api/v1/favorites` abrufbar
- [ ] **Favoriten-API:** `POST /api/v1/favorites`, `DELETE /api/v1/favorites/{target_key}` und `GET /api/v1/favorites` funktionieren auch außerhalb des Wizard-Kontexts
- [ ] **Erfahrungsstufe-Adaption Schritt 5:** Bei `beginner` zeigt NutrientPlanCard nur Name, Beschreibung und "X Dünger enthalten" — keine Dünger-Detailliste
<!-- /Quelle: Favoriten-System v1.5 -->
<!-- Quelle: Moduswechsel-Onboarding v1.4 -->
- [ ] **Upgrade Light→Full (Übernahme):** Neuer User erhält OnboardingState mit `completed=true`, kein Wizard-Start
- [ ] **Upgrade Light→Full (Ablehnung):** Neuer User erhält OnboardingState mit `completed=false`, Wizard startet automatisch
- [ ] **Downgrade Full→Light:** System-User-OnboardingState wird geprüft — Wizard startet nur wenn State fehlt oder System-Tenant keine Daten hat
- [ ] **Roundtrip Light→Full→Light→Full:** OnboardingState bleibt konsistent über mehrere Moduswechsel
- [ ] **Tenant-Scoped Kit-Auflistung:** `GET /api/v1/t/{slug}/starter-kits` zeigt nur Kits mit mindestens einer zugewiesenen Species
- [ ] **Kit-Species-Verfügbarkeit:** Kit-Detail zeigt `available: true/false` pro Species basierend auf `tenant_has_access`
- [ ] **Nicht verfügbare Species:** In Schritt 4 (Pflanzenauswahl) sind nicht zugewiesene Species ausgegraut und nicht auswählbar
- [ ] **Kein Kit verfügbar:** Wizard zeigt Hinweistext und "Eigenes Setup"-Option prominent an, wenn kein Kit für den Tenant verfügbar ist
- [ ] **Auto-Assign-Tenants:** Bei `auto_assign_master_data=true` sind alle Kits mit allen Species verfügbar
<!-- /Quelle: Moduswechsel-Onboarding v1.4 -->

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
| Favoriten | Ja | Ja | Ja |
| Matching Nutrient Plans | Ja | — | — |

## 8. Abhängigkeiten

| REQ/NFR | Art | Beschreibung |
|---------|-----|-------------|
| REQ-001 v4.0 | Liest/Erzeugt | BotanicalFamily, Species, Cultivar aus Starter-Kit-Daten. **Neu:** Species-Sichtbarkeit per `tenant_has_access`-Kante filtert verfügbare Kits. Species als Favoriten-Ziel. |
| REQ-002 | Erzeugt | Site und Location im Wizard; optional `Site.water_source` mit TapWaterProfile aus Wizard-Eingaben |
| REQ-003 | Erzeugt | GrowthPhases und RequirementProfiles aus Seed-Daten |
| REQ-004 v3.2 | Liest | NutrientPlan-Templates und FertilizerDosage-Einträge für Favoriten-Matching und Dünger-Kaskade. Fertilizer als Favoriten-Ziel. |
| REQ-006 | Erzeugt | Initiale Tasks aus WorkflowTemplates des Kits |
| REQ-013 | Erzeugt | PlantingRun mit Entries für die angelegten PlantInstances |
| REQ-021 | Setzt | `experience_level` als Grundlage für den UI-Modus. Steuert Detailtiefe der NutrientPlanCard in Schritt 5. |
| REQ-024 v1.3 | Liest | `tenant_has_access`-Kanten für Starter-Kit-Filterung |
| REQ-027 v1.2 | Reagiert | OnboardingState-Handling bei Moduswechsel (Light↔Full) |
| NFR-006 | Einhält | API-Fehlerbehandlung (ErrorResponse) |
| NFR-010 | Erweitert | Neue Seitentypen (Wizard) ergänzend zu CRUD-Masken |
