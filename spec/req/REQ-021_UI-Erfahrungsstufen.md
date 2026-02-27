# Spezifikation: REQ-021 - Erfahrungsstufen-basierter UI-Modus

```yaml
ID: REQ-021
Titel: Dreistufiger UI-Modus (Einsteiger / Fortgeschritten / Experte)
Kategorie: Benutzerführung
Fokus: Frontend
Technologie: React, TypeScript, MUI, Redux Toolkit
Status: Entwurf
Version: 1.0
```

## 1. Business Case

**User Story (Einsteiger):** "Als Hobby-Gärtner mit wenig Fachwissen möchte ich nur die Felder und Funktionen sehen, die ich verstehe — damit ich mich nicht von VPD-Werten, Allelopathie-Scores und EC-Budgets überfordert fühle."

**User Story (Experte):** "Als erfahrener Grower möchte ich weiterhin Zugriff auf alle technischen Felder und Kalkulatoren haben — der vereinfachte Modus soll meine Arbeit nicht einschränken."

**User Story (Umschalter):** "Als Nutzer möchte ich jederzeit zwischen den Modi wechseln können — weil mein Wissen wächst und ich schrittweise mehr Funktionen nutzen möchte."

**User Story (Mehr anzeigen):** "Als Einsteiger möchte ich bei Bedarf ausgeblendete Felder temporär einblenden können — ohne meinen Modus dauerhaft wechseln zu müssen."

**Beschreibung:**
Die UI-Analyse identifiziert 43 konkrete Hürden für Hobby-Gärtner im aktuellen System. Das Kernproblem ist fehlende Abstufung: Alle Formulare zeigen alle Felder auf dem gleichen Komplexitätsniveau — unabhängig davon, ob der Nutzer 3 Tomaten auf dem Balkon oder 100 Cannabis-Pflanzen im Hydroponik-Setup betreut.

Der dreistufige UI-Modus löst dieses Problem durch eine persistierte Nutzerpräferenz, die die Sichtbarkeit von Feldern, Menüpunkten und Funktionen steuert. Die Unterscheidung erfolgt **ausschließlich im Frontend** — alle drei Modi nutzen dieselben Backend-APIs. Das Backend liefert immer alle Daten; das Frontend filtert die Darstellung.

**Kernkonzepte:**

**Expertise-Level als Feld-Attribut:**
Jedes Formularfeld wird im Frontend mit einem `expertiseLevel`-Attribut annotiert (`beginner`, `intermediate`, `expert`). Der aktuelle Modus des Nutzers bestimmt, welche Felder sichtbar sind.

**Progressive Disclosure:**
Ausgeblendete Felder verschwinden nicht endgültig — ein "Mehr anzeigen"-Link unterhalb jedes Formulars erlaubt temporäres Einblenden aller Felder, ohne den Modus zu wechseln.

**Navigation-Tiering:**
Die Seitenleisten-Navigation wird abhängig vom Modus reduziert. Einsteiger sehen nur 5 Kernmenüpunkte, Fortgeschrittene 8, Experten alle.

**Intelligente Defaults:**
Im Einsteiger-Modus werden ausgeblendete Felder mit sinnvollen Standardwerten befüllt (aus Species-Seed-Daten oder berechneten Defaults), sodass keine Information verloren geht. Species-abhängige Felder (z.B. `root_type`, `base_temp`, `allelopathy_score`) werden per Lookup aus den Species-Seed-Daten befüllt; statische Fallbacks greifen nur, wenn keine Species ausgewählt ist.

**Abgrenzung:**
- Keine Backend-Änderung an bestehenden APIs — reines Frontend-Feature
- Keine Einschränkung der API-Funktionalität — alle Endpunkte bleiben verfügbar
- Kein Rechte-/Rollenkonzept — der Modus ist eine UI-Präferenz, keine Zugriffskontrolle

## 2. Datenmodell

### Nutzerpräferenz (via REQ-020 UserPreference):

Die `experience_level`-Präferenz wird in REQ-020 als `UserPreference` definiert. REQ-021 nutzt diesen Wert als Grundlage für alle UI-Entscheidungen.

Zusätzlich wird im Frontend ein lokaler Zustand für temporäre Einblendungen gehalten:

```typescript
interface UIModeState {
  /** Persistierte Erfahrungsstufe aus UserPreference */
  experienceLevel: 'beginner' | 'intermediate' | 'expert';
  /** Temporäre Einblendung aller Felder (pro Dialog, nicht persistiert) */
  showAllFieldsOverride: boolean;
  /** Loading/Error-State für Präferenz-Sync */
  status: 'idle' | 'loading' | 'error';
}
```

## 3. Technische Umsetzung (Frontend)

### 3.1 Feld-Konfigurationssystem

Jede Formular-Seite definiert ein `FieldConfig`-Objekt, das die Expertise-Stufe und optionale Auto-Fill-Logik pro Feld festlegt:

```typescript
type ExpertiseLevel = 'beginner' | 'intermediate' | 'expert';

interface FieldMeta {
  /** Minimale Erfahrungsstufe für Sichtbarkeit */
  level: ExpertiseLevel;
  /** Automatischer Default-Wert, wenn Feld nicht sichtbar */
  autoFill?: (formData: Record<string, unknown>) => unknown;
  /** Feld als Icons statt Dropdown anzeigen (visueller Modus) */
  showAsIcons?: boolean;
}

type FieldConfig<T extends string> = Record<T, FieldMeta>;
```

### 3.2 Feld-Konfigurationen pro Dialog

**SpeciesCreateDialog:**

| Feld | Einsteiger | Fortgeschritten | Experte | Auto-Fill (wenn verborgen) |
|------|:----------:|:---------------:|:-------:|---------------------------|
| `common_names` | Sichtbar | Sichtbar | Sichtbar | — |
| `description` | Sichtbar | Sichtbar | Sichtbar | — |
| `growth_habit` | Sichtbar (Icons) | Sichtbar | Sichtbar | — |
| `scientific_name` | — | Sichtbar | Sichtbar | Aus Stammdaten-Suche |
| `family_key` | — | Sichtbar | Sichtbar | Aus Species-Lookup |
| `genus` | — | Sichtbar | Sichtbar | Aus scientific_name |
| `root_type` | — | — | Sichtbar | Aus Species-Seed-Daten (Fallback: `'fibrous'`) |
| `hardiness_zones` | — | — | Sichtbar | `[]` |
| `native_habitat` | — | — | Sichtbar | `null` |
| `allelopathy_score` | — | — | Sichtbar | Aus Species-Seed-Daten (Fallback: `0`) |
| `base_temp` | — | — | Sichtbar | Aus Species-Seed-Daten (Fallback: `10.0`) |
| `synonyms` | — | — | Sichtbar | `[]` |
| `taxonomic_authority` | — | — | Sichtbar | `null` |
| `taxonomic_status` | — | — | Sichtbar | `'accepted'` |

**PlantingRunCreateDialog:**

| Feld | Einsteiger | Fortgeschritten | Experte | Auto-Fill |
|------|:----------:|:---------------:|:-------:|-----------|
| `name` | Sichtbar | Sichtbar | Sichtbar | — |
| `species` (Dropdown) | Sichtbar | Sichtbar | Sichtbar | — |
| `plant_count` (Slider) | Sichtbar | Sichtbar | Sichtbar | — |
| `site_key` | Sichtbar | Sichtbar | Sichtbar | — |
| `run_type` | — | Sichtbar | Sichtbar | `'monoculture'` |
| `location_key` | — | Sichtbar | Sichtbar | Erste Location der Site |
| `cultivar` | — | Sichtbar | Sichtbar | `null` |
| `substrate_batch_key` | — | — | Sichtbar | `null` |
| `source_plant_key` | — | — | Sichtbar | `null` |
| Entry: `id_prefix` | — | — | Sichtbar | Auto-generiert aus Species-Name |
| Entry: `role` | — | — | Sichtbar | `'primary'` |
| Entry: `spacing_cm` | — | Sichtbar | Sichtbar | Aus Species-Seed-Daten |

**NutrientCalculationsPage:**

| Kalkulator | Einsteiger | Fortgeschritten | Experte |
|-----------|:----------:|:---------------:|:-------:|
| Mixing Protocol | — | — | Sichtbar |
| Flushing Protocol | — | — | Sichtbar |
| Runoff Analysis | — | — | Sichtbar |
| Mixing Safety | — | — | Sichtbar |
| Einfache Dünge-Empfehlung | Sichtbar | — | — |
| VPD-Rechner | — | Sichtbar | Sichtbar |
| GDD-Rechner | — | Sichtbar | Sichtbar |
| Photoperiod-Rechner | — | Sichtbar | Sichtbar |
| Slot-Capacity | — | Sichtbar | Sichtbar |

### 3.3 Navigations-Tiering

**Einsteiger (5 Menüpunkte):**
1. Dashboard
2. Meine Pflanzen
3. Aufgaben
4. Kalender
5. Einstellungen

**Fortgeschritten (8 Menüpunkte):**
1. Dashboard
2. Meine Pflanzen
3. Aufgaben
4. Kalender
5. Standorte
6. Düngung
7. Stammdaten
8. Einstellungen

**Experte (alle Menüpunkte):**
1. Dashboard
2. Pflanzen (PlantInstances)
3. Durchläufe (PlantingRuns)
4. Aufgaben & Workflows
5. Kalender
6. Standorte & Slots
7. Düngung & Nährstoffe
8. Tanks
9. Substrate
10. Stammdaten (Familien, Species, Cultivars)
11. IPM / Pflanzenschutz
12. Ernte & Post-Harvest
13. Kalkulatoren
14. Import / Enrichment
15. Einstellungen

### 3.4 Shared Components

**useExpertiseLevel Hook:**

```typescript
/**
 * Custom Hook für den aktuellen UI-Modus.
 * Liest experience_level aus Redux-State (sync mit UserPreference-API).
 */
function useExpertiseLevel(): {
  level: ExpertiseLevel;
  isFieldVisible: (fieldLevel: ExpertiseLevel) => boolean;
  showAllOverride: boolean;
  setShowAllOverride: (show: boolean) => void;
};
```

**ExpertiseFieldWrapper Komponente:**

```typescript
/**
 * Wrapper-Komponente, die ein Formularfeld basierend auf der
 * Erfahrungsstufe ein-/ausblendet.
 *
 * - Unsichtbare Felder rendern nicht (kein hidden, kein display:none).
 * - Der autoFill-Wert wird als formDefault gesetzt.
 * - showAllOverride übersteuert die Sichtbarkeit temporär.
 */
interface ExpertiseFieldWrapperProps {
  level: ExpertiseLevel;
  children: React.ReactNode;
}
```

**ShowAllFieldsToggle Komponente:**

```typescript
/**
 * "Mehr anzeigen / Weniger anzeigen"-Toggle am Formularende.
 * Setzt showAllOverride im useExpertiseLevel-Hook.
 * Nicht persistiert — nur für die aktuelle Dialog-Instanz.
 */
```

**ExperienceLevelSwitcher Komponente:**

```typescript
/**
 * 3-Segment-Umschalter für die Einstellungsseite.
 * Zeigt Icons und Beschreibungstexte für jeden Modus.
 * Persistiert über PATCH /api/v1/user-preferences.
 * Warnung bei Downgrade: "Wechsel zu Einsteiger? Einige Felder
 * werden ausgeblendet, aber keine Daten gehen verloren."
 */
```

### 3.5 Einsteiger-spezifische Dünge-Ansicht

Im Einsteiger-Modus wird die gesamte Dünge-Logik auf eine vereinfachte Ansicht reduziert:

| Statt... | Sieht der Einsteiger... |
|----------|------------------------|
| NutrientPlan mit EC/pH/NPK pro Phase | "Alle 2 Wochen mit Flüssigdünger (halbe Dosierung)" |
| FeedingEvent mit 6 Messfeldern | "Heute gedüngt" (Ein-Klick-Bestätigung) |
| 4 Kalkulatoren (Mixing, Flushing, Runoff, Safety) | 1 Karte: "Deine Tomate braucht bald wieder Dünger" |
| Fertilizer-Produkt mit mixing_priority und ec_contribution | Produktname + "Dosierung: 5ml pro Liter Wasser" |

Diese Ansicht nutzt Daten aus den bestehenden APIs, präsentiert sie aber in Alltagssprache.

**Einsteiger-Pflegekarte (PlantInstance-Detail):**

Im Einsteiger-Modus wird auf der PlantInstance-Detailseite eine vereinfachte Pflegekarte prominent angezeigt. Die Daten werden aus den Species-Stammdaten und RequirementProfiles abgeleitet:

| Information | Quelle | Darstellung |
|------------|--------|-------------|
| Lichtbedarf | `requirement_profile.ppfd` | Natürlichsprachlich: "Helles indirektes Licht", "Volle Sonne" |
| Gießen | `irrigation_strategy` / Species-Defaults | "Wenn obere 2cm trocken sind", "Täglich gießen" |
| Substrat | Species-Defaults / REQ-019 | "Normale Blumenerde", "Kakteenerde" |
| Nächste Aktion | Task-System (REQ-006) | "Morgen gießen", "Heute düngen" |
| Standort | Location-Name | "Fensterbank Süd" |

### 3.6 Redux-State

```typescript
interface UIModeSlice {
  experienceLevel: ExpertiseLevel;
  showAllFieldsOverride: boolean;
  status: 'idle' | 'loading' | 'error';
  error: string | null;
}

// Actions:
// setExperienceLevel(level) — persistiert via API
// toggleShowAllFields() — nur lokal, nicht persistiert
// syncPreferences() — lädt UserPreferences aus API
```

### 3.7 i18n-Schlüssel

```
settings.experienceLevel.title
settings.experienceLevel.subtitle
settings.experienceLevel.beginner.label
settings.experienceLevel.beginner.description
settings.experienceLevel.intermediate.label
settings.experienceLevel.intermediate.description
settings.experienceLevel.expert.label
settings.experienceLevel.expert.description
settings.experienceLevel.downgradeWarning

common.showAllFields
common.showFewerFields

pages.nutrient.beginner.nextFertilizing
pages.nutrient.beginner.simpleDosage
pages.nutrient.beginner.confirmFertilized
```

## 4. Akzeptanzkriterien

### Funktional:
- [ ] Nutzerpräferenz `experience_level` mit Werten `beginner`, `intermediate`, `expert` existiert
- [ ] Default für neue Nutzer: `beginner`
- [ ] Umschaltung jederzeit möglich über Einstellungen-Seite
- [ ] Im `beginner`-Modus werden maximal 5 Felder pro Create-Dialog angezeigt
- [ ] Ausgeblendete Felder erhalten sinnvolle Default-Werte (aus Seed-Daten oder feste Defaults)
- [ ] Ein "Mehr anzeigen"-Link erlaubt temporäres Einblenden aller Felder ohne Modus-Wechsel
- [ ] "Mehr anzeigen"-Zustand ist nicht persistiert (nur für aktuelle Dialog-Instanz)
- [ ] Navigation wird auf Basis des Modus reduziert (5 / 8 / alle Menüpunkte)
- [ ] Einsteiger-Dünge-Ansicht zeigt Alltagssprache statt EC/pH-Werte
- [ ] Bei Modus-Downgrade erscheint Warnung: "Einige Felder werden ausgeblendet, keine Daten gehen verloren"
- [ ] Bei Modus-Upgrade werden sofort alle zusätzlichen Felder sichtbar
- [ ] Bestehende Daten in ausgeblendeten Feldern bleiben erhalten (kein Datenverlust bei Modus-Wechsel)
- [ ] Alle drei Modi sind in DE und EN verfügbar

### Technisch:
- [ ] Keine Backend-Änderung an bestehenden REQ-APIs erforderlich
- [ ] `useExpertiseLevel` Hook als zentrale Quelle der Wahrheit
- [ ] `ExpertiseFieldWrapper` als wiederverwendbare Shared Component
- [ ] Feld-Konfigurationen sind deklarativ (JSON/Object), nicht imperativ (if/else in JSX)
- [ ] Alle drei Modi haben vitest-Tests (Feld-Sichtbarkeit, Navigation, Auto-Fill)
- [ ] Kein Performance-Impact: Unsichtbare Felder werden nicht gerendert (kein `display: none`)

## 5. Migrationsstrategie

Für bestehende Formulare:

1. **Phase 1:** `FieldConfig`-Objekte für alle Create-/Edit-Dialoge definieren (kein UI-Change, nur Datenstruktur)
2. **Phase 2:** `ExpertiseFieldWrapper` um alle Felder in den Dialogen legen (Default-Modus: `expert` — kein sichtbarer Unterschied für bestehende Nutzer)
3. **Phase 3:** Navigations-Tiering implementieren (Toggle in Sidebar)
4. **Phase 4:** Einsteiger-spezifische Ansichten für Düngung und Kalkulatoren

Diese Phasen können inkrementell umgesetzt werden — jede Phase ist unabhängig deploybar.

## 6. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Hinweis:** REQ-021 definiert keine eigenen API-Endpunkte. Die Erfahrungsstufe wird als
User-Preference über die Endpunkte von REQ-020 (Onboarding-Wizard) gespeichert.

| Ressource/Endpoint-Gruppe | Auth | Referenz |
|---------------------------|------|----------|
| `GET /api/v1/user-preferences` | Ja | REQ-020 |
| `PUT /api/v1/user-preferences` | Ja | REQ-020 |

## 7. Abhängigkeiten

| REQ/NFR | Art | Beschreibung |
|---------|-----|-------------|
| REQ-020 | Liest | `UserPreference.experience_level` wird im Onboarding-Wizard gesetzt |
| REQ-001 | Modifiziert UI | SpeciesCreateDialog, CultivarCreateDialog — Feld-Sichtbarkeit |
| REQ-002 | Modifiziert UI | SiteCreateDialog, LocationCreateDialog — Feld-Sichtbarkeit |
| REQ-003 | Modifiziert UI | GrowthPhaseDialog — Feld-Sichtbarkeit |
| REQ-004 | Modifiziert UI | NutrientCalculationsPage — Einsteiger-Ansicht |
| REQ-006 | Nutzt | `difficulty_level` auf WorkflowTemplates für Filterung nach Modus |
| REQ-009 | Erweitert | Dashboard Role-Based Views werden durch systemweiten Modus gesteuert |
| REQ-013 | Modifiziert UI | PlantingRunCreateDialog — Feld-Sichtbarkeit |
| NFR-010 | Erweitert | CRUD-Masken werden um Expertise-Level-Steuerung ergänzt |
