# Spezifikation: REQ-042 - Modulare Feature-Sichtbarkeit (persönliche Modul-Auswahl)

```yaml
ID: REQ-042
Titel: Persönliche Modul- und Feature-Sichtbarkeit
Kategorie: Benutzerführung
Fokus: Beides (Frontend-Schwerpunkt, additive Backend-Erweiterung)
Technologie: React, TypeScript, MUI, Redux Toolkit, FastAPI, ArangoDB
Status: Entwurf
Version: 1.0 (Erstversion)
Abhängigkeit: REQ-020 (UserPreference-API), REQ-021 (Erfahrungsstufen), REQ-009 (Dashboard-Widgets), REQ-027 (Light-Modus), REQ-024 (Abgrenzung RBAC), REQ-030 (Benachrichtigungen, optional), UI-NFR-001 (Mobile-First)
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.0 | 2026-06-20 | Erstversion. Basierend auf Feature-Request [FR-001 Modulare Feature-Sichtbarkeit](../feature-requests/FR-001_Modulare-Feature-Sichtbarkeit.md) / [Issue #243](https://github.com/nolte/kamerplanter/issues/243). |

## 1. Business Case

**User Story (Desinteresse an Modulen):** „Als Zimmerpflanzen-Liebhaber dünge und ernte ich nie — ich möchte Tankmanagement und Erntechargen komplett ausblenden, damit meine Oberfläche aufgeräumt bleibt, auch wenn ich die App ansonsten sicher bedienen kann."

**User Story (Erfahren, aber selektiv):** „Als erfahrener Grower beherrsche ich alle Funktionen, nutze aber nur einen Teil. Die Erfahrungsstufe ‚Experte' zeigt mir alles — ich möchte stattdessen gezielt auswählen, welche Module ich wirklich brauche."

**User Story (Einsteiger mit Spezialinteresse):** „Als Einsteiger interessiere ich mich besonders für Pflanzenschutz, obwohl das normalerweise erst im Experten-Modus erscheint. Ich möchte genau dieses eine Modul zusätzlich einblenden, ohne meine gesamte Oberfläche auf ‚Experte' umzustellen."

**User Story (Wieder einblenden):** „Als Nutzer möchte ich ein ausgeblendetes Modul jederzeit über die Einstellungen wieder aktivieren — ohne dass dabei meine Daten in diesem Modul verloren gegangen sind."

**Beschreibung:**

REQ-021 führt einen dreistufigen UI-Modus ein (Einsteiger / Fortgeschritten / Experte). Diese Abstufung ist **eindimensional**: Sie steuert die Komplexitätstiefe (welche *Felder* und wie viel Detail), bündelt aber ganze Funktionsbereiche starr an eine Stufe. Tankmanagement, Erntechargen, IPM und Kalkulatoren erscheinen z. B. ausschließlich im Experten-Modus — entweder alle oder keiner.

In der Praxis ist das Interesse an Modulen jedoch **orthogonal zur Erfahrung**: Ein botanisch versierter Zierpflanzen-Sammler braucht kein Tankmanagement; ein Balkon-Tomaten-Einsteiger interessiert sich vielleicht gezielt für Pflanzenschutz. Die Erfahrungsstufe allein kann diese persönlichen Präferenzen nicht abbilden.

REQ-042 ergänzt REQ-021 um eine **feingranulare, persönliche Modul-Auswahl**: Der Nutzer kann in den Einstellungen einzelne Funktionsbereiche (Module) gezielt ein- oder ausblenden — unabhängig von, aber aufbauend auf der Erfahrungsstufe. Wie REQ-021 ist auch dies eine **reine Darstellungspräferenz**: Das Backend liefert weiterhin alle Daten, es findet keine Zugriffskontrolle statt, und kein Datensatz wird gelöscht.

### 1.1 Kernkonzepte

**Modul als Funktionsbereich:**
Ein *Modul* ist eine logische Gruppe zusammengehöriger Funktionen, Navigationspunkte, Dashboard-Widgets und Quick-Actions (z. B. „Tankmanagement", „Ernte", „Pflanzenschutz"). Module sind im Frontend deklarativ in einem **Modul-Katalog** definiert (analog zu `fieldConfigs.ts` aus REQ-021).

**Tri-State-Sichtbarkeit (entscheidend):**
Jedes Modul hat aus Nutzersicht drei mögliche Zustände:

| Zustand | Bedeutung |
|---------|-----------|
| `default` | Sichtbarkeit folgt der Erfahrungsstufe (REQ-021) — kein expliziter Eingriff |
| `enabled` | Modul ist **explizit eingeblendet**, auch wenn die Erfahrungsstufe es ausblenden würde |
| `disabled` | Modul ist **explizit ausgeblendet**, auch wenn die Erfahrungsstufe es zeigen würde |

Gespeichert werden **nur die Übersteuerungen** (`enabled` / `disabled`). Module ohne expliziten Eintrag bleiben `default` und folgen automatisch weiter der Erfahrungsstufe. Dadurch wirkt sich ein späterer Stufenwechsel weiterhin auf alle nicht übersteuerten Module aus — die persönliche Auswahl bleibt minimal-invasiv.

**Effektive Sichtbarkeit:**
```
isModuleVisible(modul) =
    if modul.core:                      true        // Kern-Module nie ausblendbar
    elif override[modul] == 'disabled': false
    elif override[modul] == 'enabled':  true
    else:                               experienceLevelDefault(modul)   // REQ-021
```

**Wirkungsbereich einer Ausblendung:**
Ist ein Modul ausgeblendet, verschwinden konsistent:
- die zugehörigen **Navigationspunkte** in der Seitenleiste (REQ-021 § 3.3),
- die zugehörigen **Dashboard-Widgets** (REQ-009),
- die zugehörigen **Quick-Actions** und Schnellzugriffe.

Die zugehörigen **Daten bleiben unangetastet**; Wiedereinblenden stellt den vollen Funktionsumfang sofort wieder her.

**Schutz von Kern-Modulen:**
Module mit `core: true` (Dashboard, Meine Pflanzen, Standorte, Einstellungen, Onboarding) sind **nicht** ausblendbar und erscheinen im Einstellungsdialog als fixiert/deaktiviert mit Erklärung.

### 1.2 Abgrenzung

- **Zu REQ-021 (Erfahrungsstufen):** REQ-021 steuert die *Komplexitätstiefe* (Feld-Sichtbarkeit, Detailgrad) entlang einer Stufenachse. REQ-042 steuert die *Auswahl der Funktionsbereiche* (welche Module überhaupt). Beide kombinieren sich: Die Erfahrungsstufe liefert die **Defaults** der Modul-Sichtbarkeit, die persönlichen Toggles **übersteuern** sie punktuell. REQ-042 ersetzt REQ-021 nicht, sondern ergänzt es.
- **Zu REQ-024 (Mandanten/RBAC):** REQ-042 ist **keine** Zugriffskontrolle. Ein ausgeblendetes Modul ist nicht „gesperrt", sondern nur nicht angezeigt. Berechtigungen, Rollen und Tenant-Isolation bleiben unberührt; die Modul-Auswahl ist eine persönliche UI-Präferenz pro Nutzer.
- **Zu REQ-020 (Onboarding):** Der Onboarding-Wizard *darf* eine initiale Modul-Auswahl vorschlagen (siehe § 5), erzeugt aber nur Startwerte. Die laufende Pflege erfolgt in den Einstellungen.
- **Kein Backend-Funktionsverlust:** Alle API-Endpunkte bleiben unverändert verfügbar. Die Filterung ist eine Darstellungsentscheidung des Frontends.

### 1.3 Modul-Katalog (Referenz)

Die folgende Taxonomie leitet sich aus der Navigationsstruktur (REQ-021 § 3.3 `navSectionConfig`/`navItemConfig`) ab. `Default-Level` gibt an, ab welcher Erfahrungsstufe das Modul ohne Übersteuerung sichtbar ist. Kern-Module sind unabhängig vom Level immer sichtbar.

| Modul-Key | Label | Kategorie | Default-Level | Core | Beispiel-Navigationspfade |
|-----------|-------|-----------|---------------|:----:|---------------------------|
| `dashboard` | Dashboard | Kern | beginner | ✓ | `/dashboard` |
| `plants` | Meine Pflanzen | Kern | beginner | ✓ | `/pflanzen` |
| `locations` | Standorte | Kern | beginner | ✓ | `/standorte` |
| `settings` | Einstellungen | Kern | beginner | ✓ | `/einstellungen` |
| `onboarding` | Onboarding | Kern | beginner | ✓ | `/onboarding` |
| `care` | Pflege & Erinnerungen | Pflege & Planung | beginner | | `/pflege`, `/pflege-dashboard` |
| `calendar` | Kalender | Pflege & Planung | beginner | | `/kalender` |
| `watering` | Gießprotokoll | Pflege & Planung | beginner | | `/giessprotokoll` |
| `tasks` | Aufgaben & Workflows | Pflege & Planung | beginner | | `/aufgaben`, `/workflows` |
| `nutrition` | Düngung & Nährstoffpläne | Düngung & Wasser | intermediate | | `/duengung/*` |
| `tanks` | **Tankmanagement** | Düngung & Wasser | expert | | `/tanks` |
| `substrates` | Substrate | Düngung & Wasser | expert | | `/substrate` |
| `calculators` | Kalkulatoren (VPD/GDD/EC) | Düngung & Wasser | expert | | `/kalkulatoren/*` |
| `ipm` | Pflanzenschutz (IPM) | Pflanzenschutz | expert | | `/pflanzenschutz/*` |
| `harvest` | **Ernte & Erntechargen** | Ernte | expert | | `/ernte`, `/ernte/batches` |
| `post_harvest` | Post-Harvest | Ernte | expert | | `/post-harvest` |
| `runs` | Pflanzdurchläufe | Anbau | expert | | `/durchlaeufe` |
| `propagation` | Vermehrung | Anbau | expert | | `/vermehrung` |
| `master_data` | Stammdaten (Arten/Familien/Import) | Stammdaten | intermediate | | `/stammdaten/*` |
| `companion` | Mischkultur & Fruchtfolge | Stammdaten | expert | | `/mischkultur`, `/fruchtfolge` |
| `sensors` | Sensorik & Monitoring | Automation | expert | | `/sensorik` |
| `automation` | Umgebungssteuerung & Aktorik | Automation | expert | | `/umgebung` |
| `smart_home` | Smart-Home / Home Assistant | Automation | expert | | `/smart-home` |
| `ai` | KI-Funktionen (Erkennung/Assistent) | KI | intermediate | | `/ki/*` |

> Der Katalog ist erweiterbar. Neue REQs registrieren ihr Modul durch einen Eintrag; das Sichtbarkeitssystem greift automatisch. Die kanonische Quelle der Wahrheit ist `moduleCatalog.ts` (§ 4.1).

### 1.4 Light-Modus-Verhalten (REQ-027)

Anonyme Light-Modus-Nutzer besitzen keinen serverseitigen `user_preferences`-Datensatz. Für sie wird `module_visibility` — analog zur Erfahrungsstufe in REQ-021/REQ-027 — im **localStorage** des Browsers gehalten und beim Übergang zu einem registrierten Account in die serverseitige Präferenz migriert.

## 2. Datenmodell

### 2.1 Erweiterung `UserPreference` (REQ-020)

Die bestehende Collection `user_preferences` (1:1 pro User) wird **additiv** um ein Feld erweitert — analoges Vorgehen wie bei `smart_home_enabled` (REQ-020 v1.6):

```python
# domain/models/user_preference.py (Erweiterung)

class ModuleVisibilityState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    # Hinweis: 'default' wird NICHT gespeichert — Abwesenheit eines Keys == default.

class UserPreference(BaseModel):
    # ... bestehende Felder (experience_level, locale, theme, ...) ...

    module_visibility: dict[str, ModuleVisibilityState] = Field(
        default_factory=dict,
        description=(
            "Persönliche Modul-Übersteuerungen. Schlüssel = Modul-Key aus dem "
            "Frontend-Katalog; Wert = explizite Sichtbarkeit. Module ohne Eintrag "
            "folgen der Erfahrungsstufe (REQ-021). Kern-Module werden ignoriert."
        ),
    )
```

### 2.2 Validierungsregeln (Backend)

- **Wert-Enum:** Werte müssen `enabled` oder `disabled` sein (Pydantic-Enum). Andere Werte → HTTP 422.
- **Key-Behandlung:** Modul-Keys werden als **opake Strings** akzeptiert (vorwärtskompatibel — der Katalog ist Frontend-Hoheit). Optional kann eine serverseitige Allowlist (`KNOWN_MODULE_KEYS`) unbekannte Keys mit einer Warnung im Log markieren, lehnt sie aber nicht ab.
- **Kern-Module:** Übersteuerungen für `core: true`-Module werden serverseitig **ignoriert/verworfen** (Defense-in-Depth), die finale Durchsetzung erfolgt im Frontend.
- **Leeres Dict** ist der Normalzustand und bedeutet „alles folgt der Erfahrungsstufe".

## 3. API-Endpunkte

REQ-042 fügt **keine neuen Endpunkte** hinzu, sondern erweitert die bestehenden `UserPreference`-Endpunkte (REQ-020) um das Feld `module_visibility`:

| Methode | Pfad | Beschreibung | Auth |
|---------|------|--------------|------|
| `GET` | `/api/v1/user-preferences` | Liefert nun zusätzlich `module_visibility` | JWT |
| `PATCH` | `/api/v1/user-preferences` | Akzeptiert nun `module_visibility` (vollständig oder partiell) | JWT |

**PATCH-Semantik:** Das übergebene `module_visibility`-Objekt **ersetzt** das gespeicherte vollständig (Set-Semantik), damit das Frontend Übersteuerungen gezielt entfernen kann (Zurücksetzen auf `default` = Key weglassen). Das Frontend sendet stets den vollständigen Übersteuerungs-Satz.

**Optional (Phase 2):** `GET /api/v1/module-catalog` als serverseitige Spiegelung des Katalogs für Nicht-Web-Clients (HA-Integration REQ, MCP-Server REQ-033). In v1 nicht erforderlich.

## 4. Technische Umsetzung (Frontend)

### 4.1 Modul-Katalog `moduleCatalog.ts`

```typescript
// src/config/moduleCatalog.ts
import type { ExperienceLevel } from '../api/types';

export type ModuleKey =
  | 'dashboard' | 'plants' | 'locations' | 'settings' | 'onboarding'
  | 'care' | 'calendar' | 'watering' | 'tasks'
  | 'nutrition' | 'tanks' | 'substrates' | 'calculators'
  | 'ipm' | 'harvest' | 'post_harvest'
  | 'runs' | 'propagation'
  | 'master_data' | 'companion'
  | 'sensors' | 'automation' | 'smart_home' | 'ai';

export interface ModuleDefinition {
  key: ModuleKey;
  /** i18n-Key für das Label, z.B. 'modules.tanks.label' */
  labelKey: string;
  /** i18n-Key für die erklärende Beschreibung im Einstellungsdialog */
  descriptionKey: string;
  /** Gruppierung im Einstellungsdialog, z.B. 'duengung_wasser' */
  category: string;
  /** Default-Sichtbarkeit ohne Übersteuerung (folgt REQ-021) */
  defaultLevel: ExperienceLevel;
  /** Kern-Modul: niemals ausblendbar */
  core: boolean;
  /** Navigationspfade, die mit diesem Modul ein-/ausgeblendet werden */
  navPaths: string[];
}

export const moduleCatalog: Record<ModuleKey, ModuleDefinition> = {
  tanks: {
    key: 'tanks',
    labelKey: 'modules.tanks.label',
    descriptionKey: 'modules.tanks.description',
    category: 'duengung_wasser',
    defaultLevel: 'expert',
    core: false,
    navPaths: ['/tanks'],
  },
  harvest: {
    key: 'harvest',
    labelKey: 'modules.harvest.label',
    descriptionKey: 'modules.harvest.description',
    category: 'ernte',
    defaultLevel: 'expert',
    core: false,
    navPaths: ['/ernte', '/ernte/batches'],
  },
  // ... übrige Module gemäß § 1.3 ...
};
```

### 4.2 Hook `useModuleVisibility`

Kombiniert die Erfahrungsstufe (REQ-021 `useExpertiseLevel`) mit den persönlichen Übersteuerungen aus dem Redux-State. Rückgabewert ist gemäß Hook-Konvention mit `useMemo` stabilisiert.

```typescript
// src/hooks/useModuleVisibility.ts
export function useModuleVisibility() {
  const { isNavVisible } = useExpertiseLevel();           // REQ-021
  const overrides = useAppSelector(
    (s) => s.userPreferences.preferences.module_visibility ?? {},
  );

  return useMemo(() => {
    const isModuleVisible = (key: ModuleKey): boolean => {
      const def = moduleCatalog[key];
      if (def.core) return true;                           // Kern immer sichtbar
      const override = overrides[key];
      if (override === 'disabled') return false;
      if (override === 'enabled') return true;
      return isNavVisible(def.defaultLevel);               // REQ-021-Default
    };

    const isPathVisible = (path: string): boolean => {
      const owner = Object.values(moduleCatalog).find((m) =>
        m.navPaths.some((p) => path === p || path.startsWith(p + '/')),
      );
      return owner ? isModuleVisible(owner.key) : true;    // unbekannte Pfade sichtbar
    };

    return { isModuleVisible, isPathVisible, overrides };
  }, [overrides, isNavVisible]);
}
```

### 4.3 Integrationspunkte

- **Sidebar (`Sidebar.tsx`):** Filtert Navigationspunkte zusätzlich zum Erfahrungs-Tiering über `isPathVisible(path)`. Reihenfolge: erst REQ-021-Level-Filter, dann REQ-042-Modul-Filter (logisches UND, ausgedrückt durch die `default`-Verkettung).
- **Dashboard (`REQ-009`):** Jedes modulgebundene Widget prüft `isModuleVisible(moduleKey)` vor dem Rendern. Ausgeblendete Module erzeugen keine leeren Platzhalter.
- **Quick-Actions / Schnellzugriffe:** Aktionen, die zu einem ausgeblendeten Modul führen, werden entfernt.
- **Deep-Link-Guard (`ModuleGuard`):** Route-Wrapper. Wird eine Route eines ausgeblendeten Moduls direkt per URL aufgerufen, wird die Seite **nicht** mit 404 abgewiesen, sondern zeigt einen Hinweis „Dieses Modul ist ausgeblendet" mit Button „In Einstellungen aktivieren". So gehen geteilte/gespeicherte Links nicht verloren.

### 4.4 Einstellungsdialog: Tab „Module & Funktionen"

Neuer Tab in `AccountSettingsPage` (neben dem bestehenden `ExperienceLevelSwitcher` aus REQ-021):

- Liste aller nicht-Kern-Module, **gruppiert nach Kategorie** (Akkordeon je Kategorie).
- Pro Modul: `Switch` mit Label, erklärender Beschreibung und einem dezenten Badge, das den aktuellen Effektiv-Zustand zeigt („folgt Erfahrungsstufe: sichtbar/ausgeblendet" vs. „manuell ein/aus").
- **Tri-State-Bedienung:** Ein Switch hat zwei sichtbare Stellungen (ein/aus). Ein zusätzlicher „Zurücksetzen"-Aktionslink pro Modul (oder pro Kategorie) entfernt die Übersteuerung und kehrt zu `default` zurück. Alternativ Drei-Wege-Auswahl (Auto / An / Aus) — Designentscheidung im UI-Refinement.
- **Kern-Module** werden als deaktivierte, fixierte Einträge mit Tooltip „Grundfunktion, immer sichtbar" dargestellt.
- **Suchfeld** zum schnellen Finden eines Moduls.
- **Empfehlungs-Hinweis:** Optionaler Banner „Basierend auf deiner Erfahrungsstufe empfehlen wir …" (nutzt REQ-021-Level / REQ-020-Onboarding-Antworten).
- Änderungen werden sofort via `PATCH /api/v1/user-preferences` persistiert (optimistic update im Redux-State).
- Mobile-First (UI-NFR-001): vollflächige Akkordeon-Liste, große Touch-Ziele.

## 5. Onboarding-Integration (REQ-020, optional in v1)

Im Onboarding-Wizard (REQ-020) kann ein optionaler Schritt „Was möchtest du nutzen?" eine **initiale Modul-Auswahl** als Chips/Checkboxen anbieten (z. B. „Düngung", „Pflanzenschutz", „Ernte", „Smart-Home"). Die Auswahl erzeugt initiale `enabled`-/`disabled`-Übersteuerungen. Starter-Kits (REQ-020) können sinnvolle Modul-Sets vorschlagen (z. B. Kit „Zimmerpflanzen" ohne Tankmanagement/Ernte). Dieser Schritt ist überspringbar; ohne Eingabe bleibt alles `default`.

## 6. Akzeptanzkriterien

**Funktional:**
- [ ] In den Einstellungen existiert ein Tab „Module & Funktionen" mit nach Kategorie gruppierten Modul-Schaltern.
- [ ] Ein als `disabled` markiertes Modul (z. B. Tankmanagement) verschwindet aus Seitenleiste, Dashboard-Widgets und Quick-Actions.
- [ ] Ein als `enabled` markiertes Modul erscheint auch dann, wenn die aktuelle Erfahrungsstufe es per Default ausblenden würde.
- [ ] Module ohne Übersteuerung folgen weiterhin automatisch der Erfahrungsstufe; ein Stufenwechsel verändert ihre Sichtbarkeit.
- [ ] Kern-Module (Dashboard, Meine Pflanzen, Standorte, Einstellungen, Onboarding) lassen sich nicht ausblenden und werden im Dialog als fixiert dargestellt.
- [ ] Das Ausblenden eines Moduls löscht keine Daten; Wiedereinblenden stellt den vollen Funktionsumfang wieder her.
- [ ] Der direkte URL-Aufruf einer Route eines ausgeblendeten Moduls zeigt einen Reaktivierungs-Hinweis statt eines 404.
- [ ] Eine Übersteuerung kann auf `default` zurückgesetzt werden (Modul folgt wieder der Erfahrungsstufe).

**Technisch:**
- [ ] `module_visibility` wird serverseitig in `user_preferences` persistiert und ist geräte-/sitzungsübergreifend verfügbar.
- [ ] `GET`/`PATCH /api/v1/user-preferences` lesen/schreiben `module_visibility`; ungültige Enum-Werte ergeben HTTP 422.
- [ ] Übersteuerungen für Kern-Module werden serverseitig verworfen.
- [ ] Light-Modus-Nutzer (REQ-027) halten `module_visibility` im localStorage; beim Registrieren erfolgt Migration.
- [ ] `useModuleVisibility` gibt ein `useMemo`-stabilisiertes Objekt zurück (Hook-Konvention).
- [ ] Der Modul-Katalog ist in `moduleCatalog.ts` deklarativ gepflegt; neue Module werden durch einen Katalog-Eintrag integriert.

**Qualität / Konsistenz:**
- [ ] Keine Vermischung mit Rechte-/Rollenkonzept (REQ-024) — rein UI-seitige Präferenz, Backend liefert weiter alle Daten.
- [ ] i18n: Alle Modul-Labels und -Beschreibungen liegen unter `modules.<key>.label` / `modules.<key>.description` (DE/EN).
- [ ] Mobile-First (UI-NFR-001): Der Einstellungs-Tab ist vollständig touch-bedienbar.

## 7. Abhängigkeiten

| REQ/NFR | Beziehung | Impact |
|---------|-----------|--------|
| REQ-020 | Erweitert `UserPreference`/`user_preferences` um `module_visibility`; optionaler Onboarding-Schritt | Mittel (additives Feld) |
| REQ-021 | Liefert die Default-Sichtbarkeit pro Modul; REQ-042 übersteuert punktuell | Hoch (Basismechanik) |
| REQ-009 | Dashboard-Widgets respektieren Modul-Sichtbarkeit | Mittel |
| REQ-027 | Light-Modus: localStorage-Fallback + Migration | Niedrig |
| REQ-024 | Abgrenzung: keine RBAC/Zugriffskontrolle | Niedrig (klärend) |
| REQ-030 | Benachrichtigungen ausgeblendeter Module bleiben unangetastet (kein Stummschalten via Sichtbarkeit) | Niedrig |
| REQ-033 / HA-Integration | Optionaler `module-catalog`-Endpunkt für Nicht-Web-Clients (Phase 2) | Niedrig |
| UI-NFR-001 | Mobile-First-Bedienung des Einstellungs-Tabs | Mittel |
