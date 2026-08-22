# Spezifikation: REQ-045 - Individualisierbares Dashboard

```yaml
ID: REQ-045
Titel: Individualisierbares Dashboard & Widget-Personalisierung
Kategorie: Visualisierung / Benutzerführung
Fokus: Frontend (mit Backend-Persistenz)
Technologie: FastAPI, React 19, ArangoDB, react-grid-layout (lazy), MUI 7, Redux Toolkit, TanStack Query
Status: Entwurf
Version: 1.4 („Eigentümer (self)" durch Rolle + Service-Prädikat ersetzt)
Abhängigkeit: REQ-009 (Dashboard-Widget-Katalog & Datenquellen — SSOT), REQ-021 (Erfahrungsstufen), REQ-042 (Modulare Feature-Sichtbarkeit), REQ-024 (Multi-Tenant/Permission-Matrix), REQ-027 (Light-Modus), REQ-020 (Onboarding), REQ-022 (Pflegeerinnerungen), REQ-031 (KI-Daily-Tip), UI-NFR-001 (Responsive), UI-NFR-002 (Barrierefreiheit), UI-NFR-003 (Bundle-Budget), UI-NFR-012 (PWA-Offline), UI-NFR-019 (Kiosk-Modus), NFR-007 (Performance)
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.2 | 2026-07-04 | **Scope-Erweiterung + Review-Nachschärfung.** Pro-Breakpoint-Layouts (getrennt Desktop/Tablet/Mobile) von Phase 2 nach **v1** gezogen → Datenmodell auf `schema_version 2` umgestellt: `widgets` (welche + Config, breakpoint-unabhängig) getrennt von `placements` pro Breakpoint (`lg`/`md`/`sm`). Discoverability-Findings U-004 (Deep-Link von `/dashboard` → Einstellungen) + U-005 (First-Use-Coachmark) in v1 aufgenommen. Neue UI-NFR-Regeln referenziert: UI-NFR-002 R-024..R-027 (Drag-and-Drop-Alternativen / Meaningful Sequence dynamischer Grids), UI-NFR-003 R-028 (route-spezifisches Bundle-Budget). |
| 1.1 | 2026-07-04 | **Frontend-Design-Review eingearbeitet** (`spec/analysis/req-045-frontend-design-review.md`): K-001 Read-Only-Rendering von `react-grid-layout` entkoppelt (reines CSS-Grid; DnD-Library erst im Bearbeiten-Modus lazy) — löst den Bundle-Budget-Selbstwiderspruch. K-002 Touch-Targets auf **48 px** (UI-NFR-001 R-011) korrigiert. Neu: DOM-Order-Regel `(y, x)` (U-002), Empty-State bei 0 Widgets (U-003), tastaturbedienbares Kebab-Menü im Bearbeiten-Modus (U-001), Resize-Handle-Hit-Area 48 px (U-006), `prefers-reduced-motion` (O-003). Offen (Issue #368): U-004/U-005 Discoverability, O-001 Parallel-Load, neue UI-NFR-Regeln. |
| 1.0 | 2026-07-04 | Erstfassung. Realisiert die in **REQ-009 v2.1 §6 als „Phase 2" geparkten** Punkte *Drag-and-Drop-Widget-Anordnung* und *per-User-Layout* als eigene Personalisierungs-Schicht. REQ-009 bleibt Single Source of Truth für Widget-Datenquellen, Polling-Intervalle und Aggregation; REQ-045 ergänzt jeden Widget-Typ um Layout-Metadaten und spezifiziert die nutzerindividuelle Konfiguration in den Einstellungen. |

## 1. Business Case

**User Story:** „Als Nutzer möchte ich meine Startseite selbst gestalten — die Kacheln auswählen, die für *mich* zählen, sie anordnen und in der Größe anpassen —, damit ich beim Öffnen der App genau das sehe, was ich täglich brauche. Die Auswahl treffe ich in den Einstellungen, das Ergebnis wird für mich dauerhaft gespeichert."

**Beschreibung:**
REQ-009 liefert einen reichen Katalog an Dashboard-Widgets, legt aber in v2.1 (Konsolidierung W-020) bewusst ein **festes Layout pro Erfahrungsstufe** fest und verschiebt die freie, nutzerindividuelle Anordnung auf Phase 2. REQ-045 hebt genau diese Beschränkung auf: Jeder Nutzer stellt sich sein Dashboard aus dem verfügbaren Widget-Katalog **selbst zusammen**, ordnet die Widgets per Drag-and-Drop an, passt ihre Größe an und konfiguriert einzelne Widgets (z.B. Standort- oder Zeitraum-Bezug). Die Konfiguration ist als eigener **Tab in den Einstellungen** verankert; das Ergebnis wird pro Nutzer (und pro Tenant, REQ-024) persistiert.

**Design-Prinzipien:**

- **Konfiguration in den Einstellungen (Primärfläche):** Widget-Auswahl, Widget-Konfiguration, Zurücksetzen und (barrierefreie) Reihenfolge-Steuerung leben in `Einstellungen → Dashboard`. Das ist die verbindliche, vollständig tastaturbedienbare Konfigurationsfläche (UI-NFR-002).
- **Direktmanipulation als Zusatz:** Ergänzend bietet das Dashboard einen „Bearbeiten"-Modus mit Drag-and-Drop/Resize (react-grid-layout). Beide Flächen schreiben denselben Zustand (`dashboard_layout`).
- **Sinnvoller Default statt leerer Startseite:** Ohne gespeichertes Layout leitet das System aus Erfahrungsstufe (REQ-021) + Modul-Sichtbarkeit (REQ-042) ein Default-Layout ab. Personalisierung ist rein **additiv/überschreibend** — genau wie `module_visibility` (REQ-042).
- **Katalog-getrieben:** Verfügbare Widgets stammen aus einem deklarativen Katalog (`dashboardWidgetCatalog`, Frontend) mit Backend-Gegenstück — analog zum bewährten `moduleCatalog ↔ KNOWN_MODULE_KEYS`-Muster (REQ-042). Neue Widgets werden durch einen Katalog-Eintrag registriert, nicht durch Code an der Seite.
- **Respektiert bestehende Sichtbarkeits-Gates:** Ein Widget ist nur wählbar/darstellbar, wenn sein zugrundeliegendes Modul sichtbar (REQ-042), im Tenant erlaubt (REQ-024) und im aktuellen Modus verfügbar ist (Light-Modus REQ-027).

**Abgrenzung:**

- **REQ-009** definiert *welche* Widgets es gibt, *woher* ihre Daten kommen (AQL/Aggregation), *wie oft* gepollt wird und die Widget-*Semantik*. REQ-045 ändert daran nichts, sondern ergänzt Layout-Metadaten und die Personalisierung.
- **UI-NFR-019 (Kiosk):** Das Kiosk-Dashboard unter `/kiosk` bleibt ein festes, kuratiertes Layout und ist **nicht** Gegenstand der Personalisierung. REQ-045 gilt für das Standard-Office-Dashboard unter `/dashboard`.
- **REQ-042 (`module_visibility`)** steuert die *Navigations-/Modul-Sichtbarkeit* (Menüpunkte, Deep-Links). REQ-045 steuert die *Widgets auf der Startseite*. Beide teilen das Muster, sind aber getrennte Zustände.

### 1.1 Scope-Abgrenzung v1 / Phase 2

| Fähigkeit | v1-Scope | Phase 2 |
|-----------|----------|---------|
| Widget hinzufügen/entfernen (aus Katalog) | ✅ | — |
| Reihenfolge ändern (Drag-and-Drop) | ✅ | — |
| Barrierefreie Reihenfolge/Größe (Buttons in Settings) | ✅ | — |
| Widget-Größe ändern (Resize innerhalb min/max) | ✅ | — |
| Per-Widget-Konfiguration (z.B. Standort, Zeitraum) | ✅ (für Widgets mit `config_schema`) | — |
| Zurücksetzen auf Erfahrungsstufen-Default | ✅ | — |
| Persistenz pro Nutzer & Tenant (+ Light-Modus localStorage) | ✅ | — |
| Ein Dashboard pro Nutzer | ✅ | — |
| **Pro-Breakpoint-Layouts (getrennt Desktop/Tablet/Mobile)** | ✅ (v1.2; `placements` je Breakpoint, fehlender Breakpoint aus `lg` abgeleitet) | — |
| **Discoverability: Deep-Link `/dashboard` → Einstellungen (U-004)** | ✅ (v1.2) | — |
| **Discoverability: einmaliger First-Use-Coachmark (U-005)** | ✅ (v1.2) | — |
| Mehrere benannte Dashboards / Tabs | — | ✅ |
| Dashboards teilen / als Tenant-Default publizieren | — | ✅ |
| Custom-Widgets via Plugin-API | — | ✅ (REQ-009 Phase 2) |
| WebSocket-Live-Deltas | — | ✅ (REQ-009 Phase 2) |

## 2. ArangoDB-Modellierung

REQ-045 führt **keine** neuen Collections oder Edges ein. Das personalisierte Layout wird als
zusätzliches Feld an der bestehenden `UserPreference` (Collection `USER_PREFERENCES`,
tenant-scoped) gespeichert — genau wie `module_visibility` (REQ-042). Damit gilt automatisch:

- Ein Layout **pro Nutzer pro Tenant** (Tenant-Isolation über `user_key` + tenant-scoped Collection).
- Kein zusätzlicher Graph-Traversal; Laden/Speichern über das bestehende `BaseArangoRepository`.

### Erweiterung `UserPreference` (Dokument in `USER_PREFERENCES`)

```jsonc
{
  "_key": "…",
  "user_key": "users/…",
  "experience_level": "beginner",       // REQ-021 — Quelle des Default-Layouts
  "module_visibility": { "…": "…" },    // REQ-042 — gated welche Widgets wählbar sind
  "dashboard_layout": {                  // NEU (REQ-045); null/absent => Default aus experience_level
    "schema_version": 2,                  // v2: welche-Widgets von Positionen getrennt (per Breakpoint)
    "widgets": [                          // WELCHE Widgets (+ Config) — breakpoint-unabhängig
      {
        "instance_id": "w-8f3c…",         // eindeutig innerhalb dieses Layouts (uuid4)
        "widget_key": "tasks_today",      // referenziert dashboardWidgetCatalog / REQ-009 §1.5
        "config": {}                       // widget-spezifisch, validiert gegen config_schema
      }
    ],
    "placements": {                        // WO die Widgets liegen — je Breakpoint (UI-NFR-001)
      // lg = Desktop ≥1200px (12 cols), md = Tablet 600–1199px (8 cols), sm = Mobile <600px (4 cols)
      "lg": [ { "instance_id": "w-8f3c…", "x": 0, "y": 0, "w": 4, "h": 4 } ],
      "md": [ { "instance_id": "w-8f3c…", "x": 0, "y": 0, "w": 4, "h": 4 } ],
      "sm": [ { "instance_id": "w-8f3c…", "x": 0, "y": 0, "w": 4, "h": 4 } ]
    }
  }
}
```

**Semantik:**

- `dashboard_layout == null` (bzw. Feld fehlt) → das Frontend rendert das aus `experience_level`
  abgeleitete Default-Layout (`DEFAULT_DASHBOARD_LAYOUT_BY_EXPERTISE`, §3). Das Default wird **nicht**
  materialisiert gespeichert — erst die erste Nutzeränderung persistiert ein vollständiges Layout
  (Set-Semantik, identisch zu `saveModuleVisibility`, REQ-042).
- **`widgets`** ist die **vollständige** Widget-Liste des Nutzers (welche Widgets + deren `config`) — die
  eine Quelle der Wahrheit dafür, *welche* Widgets angezeigt werden, breakpoint-unabhängig (kein Delta).
- **`placements`** hält je Breakpoint (`lg`/`md`/`sm`) die *Positionen*. Jeder `placement`-Eintrag
  referenziert eine `instance_id` aus `widgets`. Ein **fehlender Breakpoint wird aus `lg` abgeleitet**
  (Auto-Stapelung / react-grid-layout-Auto-Generate) — der Nutzer *kann* jeden Breakpoint anpassen, *muss*
  aber nicht. So bleibt „welche Widgets" über alle Breakpoints konsistent; nur die Anordnung divergiert.
- **Migration v1→v2:** Ein Alt-Layout mit `columns` + `widgets[].x/y/w/h` wird gelesen als `lg`-Placement;
  `widgets` verliert die Positionsfelder, `md`/`sm` werden abgeleitet. Konvertierung beim Laden (tolerant).
- Zurücksetzen = `dashboard_layout` auf `null` setzen (PATCH mit explizitem `null`) → Default greift wieder.

## 3. Technische Umsetzung

### 3.1 Backend — Datenmodell & Validierung (Pydantic v2)

Erweiterung von `app/domain/models/user_preference.py`:

```python
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, model_validator

DASHBOARD_LAYOUT_SCHEMA_VERSION = 2
# Grid-Spalten je Breakpoint (UI-NFR-001): Desktop / Tablet / Mobile.
GRID_COLS_BY_BREAKPOINT: dict[str, int] = {"lg": 12, "md": 8, "sm": 4}
GRID_MAX_COLUMNS = 12


class DashboardWidgetInstance(BaseModel):
    """Welches Widget (+ Config) — breakpoint-unabhängig (REQ-045)."""

    instance_id: str = Field(default_factory=lambda: f"w-{uuid4().hex[:12]}")
    widget_key: str
    config: dict[str, object] = Field(default_factory=dict)


class WidgetPlacement(BaseModel):
    """Position/Größe einer Widget-Instanz in einem Breakpoint-Grid (REQ-045).

    `w` wird clientseitig auf die Spaltenzahl des jeweiligen Breakpoints
    geklammert (react-grid-layout); das Modell erlaubt bis zum lg-Maximum.
    """

    instance_id: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(ge=1, le=GRID_MAX_COLUMNS)
    h: int = Field(ge=1, le=24)


class DashboardLayout(BaseModel):
    """Personalisiertes Dashboard-Layout eines Nutzers (REQ-045).

    Set-Semantik: enthält die vollständige Widget-Liste des Nutzers. Ein
    unbekannter `widget_key` (nicht in der Backend-Widget-Registry) wird beim
    Speichern verworfen und geloggt — analog zu module_visibility (REQ-042).
    Positionen liegen je Breakpoint in `placements`; ein fehlender Breakpoint
    wird clientseitig aus `lg` abgeleitet.
    """

    schema_version: int = DASHBOARD_LAYOUT_SCHEMA_VERSION
    widgets: list[DashboardWidgetInstance] = Field(default_factory=list)
    placements: dict[str, list[WidgetPlacement]] = Field(default_factory=dict)

    @field_validator("widgets")
    @classmethod
    def _unique_instance_ids(
        cls, widgets: list[DashboardWidgetInstance]
    ) -> list[DashboardWidgetInstance]:
        ids = [w.instance_id for w in widgets]
        if len(ids) != len(set(ids)):
            raise ValueError("instance_id-Werte im Dashboard-Layout müssen eindeutig sein")
        return widgets

    @model_validator(mode="after")
    def _placements_are_consistent(self) -> "DashboardLayout":
        known = {w.instance_id for w in self.widgets}
        for breakpoint, places in self.placements.items():
            if breakpoint not in GRID_COLS_BY_BREAKPOINT:
                raise ValueError(f"unbekannter Breakpoint: {breakpoint}")
            for placement in places:
                if placement.instance_id not in known:
                    raise ValueError(
                        f"placement referenziert unbekannte instance_id: {placement.instance_id}"
                    )
        return self
```

An `UserPreference` wird ergänzt:

```python
class UserPreference(BaseModel):
    # … bestehende Felder (experience_level, theme, module_visibility, …) …
    dashboard_layout: DashboardLayout | None = None
```

**Registry & Verwerfung unbekannter Widgets** (im `UserPreferenceService`, analog zu
`KNOWN_MODULE_KEYS`): eine `KNOWN_WIDGET_KEYS`-Menge hält die Backend-Wahrheit; sie **muss synchron**
zum Frontend-`dashboardWidgetCatalog` gehalten werden (Contract-Test, §6).

```python
KNOWN_WIDGET_KEYS: frozenset[str] = frozenset({
    "quick_actions", "active_plants_summary", "tasks_today", "care_reminders",
    "daily_tip", "weather_forecast", "onboarding_progress", "winter_protection",
    "ipm_alerts", "harvest_forecast", "next_calendar_events", "community_activity",
    "sensor_live", "tank_status", "phase_timeline", "vpd_gauge", "plant_grid",
})


def _sanitize_layout(layout: DashboardLayout) -> DashboardLayout:
    """Verwirft Widgets mit unbekanntem widget_key (Warn-Log), behält den Rest.

    Bewusst tolerant (wie module_visibility): das Backend lehnt ein Layout nicht
    komplett ab, nur weil ein Widget-Key noch/nicht mehr existiert (Forward-/
    Backward-Kompatibilität über Client-Versionen hinweg).
    """
    keep, dropped = [], []
    for widget in layout.widgets:
        (keep if widget.widget_key in KNOWN_WIDGET_KEYS else dropped).append(widget)
    if dropped:
        logger.warning(
            "dashboard_layout.unknown_widgets_dropped",
            widget_keys=[w.widget_key for w in dropped],
        )
    # Placements verwaister instance_ids ebenfalls entfernen (Konsistenz je Breakpoint).
    kept_ids = {w.instance_id for w in keep}
    pruned = {
        breakpoint: [p for p in places if p.instance_id in kept_ids]
        for breakpoint, places in layout.placements.items()
    }
    return layout.model_copy(update={"widgets": keep, "placements": pruned})
```

> **Hinweis (Nicht-Ziel):** Das Backend prüft `x/y/w/h` nur auf Wertebereiche (Pydantic-Constraints),
> **nicht** auf Überlappungsfreiheit. Ein kollisionsfreies, aufgeräumtes Layout ist Verantwortung des
> Clients (react-grid-layout „compact"). Der Server speichert as-is.

### 3.2 Backend — API

REQ-045 erweitert die bestehenden `UserPreference`-Endpunkte (tenant-scoped,
`/api/v1/t/{tenant_slug}/user-preferences`) statt neue einzuführen:

| Methode | Pfad | Zweck |
|---------|------|-------|
| `GET` | `…/user-preferences` | liefert `UserPreferenceResponse` **inkl. `dashboard_layout`** |
| `PATCH` | `…/user-preferences` | akzeptiert `dashboard_layout: DashboardLayout \| null` (null = Reset) |
| `GET` | `…/dashboard/widgets/catalog` | **NEU** — verfügbarer Widget-Katalog des aktuellen Nutzers (server-autoritativ gefiltert, §3.3) |

Schema-Erweiterungen (`app/api/v1/user_preferences/schemas.py`):

```python
class UserPreferenceResponse(BaseModel):
    # … bestehende Felder …
    dashboard_layout: DashboardLayout | None = None


class UserPreferenceUpdate(BaseModel):
    # … bestehende optionale Felder …
    dashboard_layout: DashboardLayout | None = None
    # Reset erfordert explizites null → PATCH darf `exclude_none` NICHT auf dieses
    # Feld anwenden. Umsetzung: `exclude_unset=True` verwenden und im Service
    # zwischen "nicht gesendet" (unset) und "auf null gesetzt" (Reset) unterscheiden.
```

> **Reset-Semantik (wichtig):** Der bestehende `PATCH`-Handler nutzt `model_dump(exclude_none=True)`.
> Für `dashboard_layout` muss auf `exclude_unset=True` umgestellt werden, damit ein bewusst gesendetes
> `null` (Zurücksetzen) nicht verschluckt wird. Felder, die der Client nicht sendet, bleiben unverändert.

**Datenquelle der Widget-Inhalte:** REQ-045 fügt **keine** eigenen Datenendpunkte hinzu. Widget-Inhalte
kommen aus REQ-009: dem Aggregations-Endpunkt `GET …/dashboard/aggregated?widgets=<keys>` (Initial-Load)
und den per-Widget-Polls (REQ-009 §1.5). REQ-045 verlangt, dass `aggregated` die **aktiven Widget-Keys
des Nutzers** akzeptiert und nur deren Payloads liefert (N+1-Vermeidung).

### 3.3 Backend — Widget-Katalog-Endpunkt (server-autoritative Verfügbarkeit)

Ob ein Widget für einen Nutzer *verfügbar* ist, hängt von serverseitigen Gates ab (Permission-Matrix
REQ-024, Modul-Sichtbarkeit REQ-042, Light-Modus REQ-027). Damit das Frontend nicht raten muss, liefert
`GET …/dashboard/widgets/catalog` die für den aufrufenden Nutzer **erlaubten** Widget-Keys plus
statische Metadaten:

```python
class DashboardWidgetCatalogEntry(BaseModel):
    widget_key: str
    category: str                 # Gruppierung im Settings-Tab
    default_level: ExperienceLevel  # REQ-021 — ab welcher Stufe im Default
    default_size: dict[str, int]  # {"w": 4, "h": 4}
    min_size: dict[str, int]
    max_size: dict[str, int]
    required_module: str | None   # ModuleKey (REQ-042); None = an Core gebunden
    available: bool               # False, wenn durch Gates gesperrt (Anzeige ausgegraut)
    unavailable_reason: str | None  # i18n-Key, z.B. "dashboard.gate.moduleHidden"
```

Regeln für `available`:

- `False`, wenn `required_module` per `module_visibility` **disabled** ist (REQ-042).
- `False`, wenn dem Nutzer die Lese-Permission für die Widget-Datenquelle fehlt (REQ-024).
- `False`, wenn das Widget im Light-Modus gefiltert ist (z.B. `community_activity`, REQ-027 §2.1).
- `daily_tip` nur `available`, wenn KI-Features aktiv sind (REQ-031 / Light-Modus-Whitelist REQ-027).

Nicht verfügbare Widgets erscheinen im Settings-Tab **ausgegraut mit Begründung** (nicht unsichtbar) und
werden beim Rendern des Dashboards übersprungen (kein leerer Container) — analog `ModuleGuard` (REQ-042).

### 3.4 Frontend — Widget-Katalog & Registry

Neue Datei `src/frontend/src/config/dashboardWidgetCatalog.ts` (deklarativ, analog `moduleCatalog.ts`):

```ts
import type { ExperienceLevel } from '@/api/types';
import type { ModuleKey } from '@/config/moduleCatalog';

export type WidgetKey =
  | 'quick_actions' | 'active_plants_summary' | 'tasks_today' | 'care_reminders'
  | 'daily_tip' | 'weather_forecast' | 'onboarding_progress' | 'winter_protection'
  | 'ipm_alerts' | 'harvest_forecast' | 'next_calendar_events' | 'community_activity'
  | 'sensor_live' | 'tank_status' | 'phase_timeline' | 'vpd_gauge' | 'plant_grid';

export interface WidgetSize { w: number; h: number }

export interface DashboardWidgetDefinition {
  key: WidgetKey;
  labelKey: string;          // z.B. 'dashboard.widgets.tasks_today.label'
  descriptionKey: string;    // Erklärtext im Settings-Tab (UI-NFR-011)
  category: string;          // Gruppierung im Settings-Tab
  defaultLevel: ExperienceLevel;  // REQ-021 — Default-Set
  defaultSize: WidgetSize;
  minSize: WidgetSize;
  maxSize: WidgetSize;
  requiredModule: ModuleKey | null;  // gated via REQ-042; null = Core
  hasConfig: boolean;        // true → Config-Dialog im Settings-Tab
}
```

Zusätzlich eine **Registry** (`src/frontend/src/components/dashboard/widgetRegistry.ts`), die jedem
`WidgetKey` eine **lazy** geladene React-Komponente zuordnet (Bundle-Budget UI-NFR-003, §5). Das bereits
existierende `WinterProtectionWidget` wird als erster Registry-Eintrag (`winter_protection`) geführt; die
bisher hart in `DashboardPage.tsx` verdrahteten QuickActions werden zum Widget `quick_actions`.

### 3.5 Frontend — Default-Layout-Ableitung (REQ-021)

`DEFAULT_DASHBOARD_LAYOUT_BY_EXPERTISE` erweitert REQ-009 §1.6 um Positions-/Größen-Angaben. Beginner
sehen ein aufgeräumtes, gestapeltes Grundset; höhere Stufen erhalten additiv mehr Widgets:

```ts
export const DEFAULT_WIDGETS_BY_LEVEL: Record<ExperienceLevel, WidgetKey[]> = {
  beginner: [
    'quick_actions', 'tasks_today', 'care_reminders',
    'active_plants_summary', 'daily_tip', 'winter_protection', 'weather_forecast',
    'onboarding_progress', // nur solange Onboarding unvollständig (REQ-020)
  ],
  intermediate: [
    // alle Beginner-Widgets, plus:
    'ipm_alerts', 'harvest_forecast', 'next_calendar_events', 'community_activity',
  ],
  expert: [
    // alle Intermediate-Widgets, plus:
    'sensor_live', 'tank_status', 'phase_timeline', 'vpd_gauge', 'plant_grid',
  ],
};
```

`resolveDefaultLayout(level, catalog)` platziert diese Widgets in `defaultSize` reihenweise im 12-Spalten-Grid
(Auto-Packing), filtert nicht verfügbare Widgets (§3.3) heraus und vergibt frische `instance_id`s. Bei
**Erfahrungsstufen-Wechsel** eines Nutzers **ohne** gespeichertes Layout ändert sich das Default automatisch;
hat der Nutzer bereits ein eigenes Layout, bleibt es unangetastet (der Settings-Tab bietet „Neue Standard-Widgets
hinzufügen" an) — konsistent zu REQ-009 §1.6.

### 3.6 Frontend — Widget-Katalog (Katalog FE ↔ Registry ↔ Backend)

Verfügbarkeit eines Widgets im Frontend = `catalog[key].available` (aus §3.3) **UND** Modul sichtbar
(`useModuleVisibility().isModuleVisible(requiredModule)`, REQ-042). Ein aktives Widget, dessen Modul der
Nutzer nachträglich ausblendet, wird beim Rendern übersprungen und im Settings-Tab als „inaktiv (Modul
ausgeblendet)" markiert — es wird **nicht** stillschweigend aus dem Layout gelöscht.

### 3.7 Frontend — Persistenz (Redux, Light-/Full-Modus)

Analog zu `saveModuleVisibility` (REQ-042) im `userPreferencesSlice` (oder einem neuen
`dashboardLayoutSlice`):

```ts
export const saveDashboardLayout = createAsyncThunk(
  'userPreferences/saveDashboardLayout',
  async (layout: DashboardLayout | null) => {
    if (isLightMode) {
      // Light-Modus (REQ-027): kein Backend → localStorage
      writeLocalDashboardLayout(layout);
      return layout;
    }
    const pref = await api.updatePreferences({ dashboard_layout: layout });
    return pref.dashboard_layout ?? null;
  },
);

// Migration nach Signup (REQ-027 → Full): lokales Layout gewinnt, falls serverseitig keins existiert.
export const migrateLocalDashboardLayout = /* analog migrateLocalModuleVisibility */;
```

- **Full-Modus:** `dashboard_layout` an `UserPreference` (PATCH), server-persistiert pro Tenant.
- **Light-Modus:** `localStorage` (neue Lib `dashboardLayoutStorage.ts`, analog `moduleVisibilityStorage.ts`).
- **Signup-Migration:** lokales Layout wird beim Übergang Light→Full einmalig übernommen.
- **Debounce:** Drag/Resize-Interaktionen werden vor dem Persistieren gebündelt (≈500 ms) — kein PATCH pro Pixel.

### 3.8 Frontend — Konfigurationsfläche (Einstellungen) + Bearbeiten-Modus

**Primärfläche — `Einstellungen → Dashboard`** (`DashboardSettingsTab.tsx`, Deep-Link `/settings#dashboard`,
analog `ModulesSettingsTab.tsx`):

- Accordion je `category`; pro Widget ein Switch „auf Dashboard anzeigen".
- Widgets mit `hasConfig` bieten einen Konfigurations-Dialog (z.B. Standort-Auswahl für `sensor_live`,
  Zeitraum für `harvest_forecast`).
- **Barrierefreie Reihenfolge/Größe (UI-NFR-002):** „Nach oben/unten"-Buttons und Größen-Stepper pro Widget
  — vollwertige, tastaturbedienbare Alternative zum Drag-and-Drop.
- **Breakpoint-Umschalter (v1.2):** Ein Segmented-Control „Desktop / Tablet / Mobile" wählt, für welchen
  Breakpoint (`lg`/`md`/`sm`) Reihenfolge und Größe bearbeitet werden. Ein „für alle Breakpoints
  übernehmen"-Button kopiert die aktuelle Anordnung in die übrigen `placements`.
- „Auf Standard zurücksetzen"-Button (→ `saveDashboardLayout(null)`).
- Nicht verfügbare Widgets ausgegraut mit i18n-Begründung (`unavailable_reason`).

**Discoverability (U-004 / U-005, v1.2):**

- **Deep-Link von `/dashboard` (U-004):** Im Seiten-Header sitzt neben dem „Bearbeiten"-Toggle ein
  zweiter Icon-Button „⚙ Widgets verwalten" mit Deep-Link auf `/settings#dashboard`. Zusätzlich öffnet das
  Widget-Kebab-Menü (unten) „Konfigurieren" den Config-Dialog **inline** — ohne Zwangsnavigation zu Settings.
- **First-Use-Coachmark (U-005):** Beim ersten Dashboard-Besuch erscheint ein einmaliger, schließbarer
  Hinweis („Du kannst dein Dashboard anpassen …"), gemerkt über das localStorage-Flag
  `dashboard_personalization_hint_dismissed`. Für Beginner besonders wertvoll (kleinstes Default-Set).

**Direktmanipulation — Bearbeiten-Modus auf `/dashboard`:**

- Toggle „Bearbeiten"; darunter wird `react-grid-layout` (als `ResponsiveReactGridLayout`) **erst jetzt**
  per `React.lazy()` nachgeladen; Drag-and-Drop + Resize innerhalb `min/maxSize` wirken auf den im
  Breakpoint-Umschalter gewählten Breakpoint; „Speichern"/„Abbrechen".
- **Tastatur-Parität im Bearbeiten-Modus (UI-NFR-002, U-001):** Jedes Widget trägt ein fokussierbares
  Kebab-Menü (`⋮`) mit „Nach oben/unten", „Kleiner/Größer" und (falls `hasConfig`) „Konfigurieren". Die
  react-grid-layout-Drag-/Resize-Handles erhalten `tabIndex={-1}` (nicht fokussierbar, nur Maus/Touch),
  damit keine fokussierbaren, aber funktionslosen Handles im Tab-Index landen (WCAG 2.1.1). Das
  Kebab-Menü ist die vollwertige, in-place erreichbare Tastaturalternative — ohne Navigation zu Settings.
- **Resize-Handle-Hit-Area (UI-NFR-001 R-011, U-006):** Das `.react-resizable-handle` erhält eine
  Touch-Fläche von mindestens **48×48 px** (größere unsichtbare Hit-Area, optisch kleineres Icon — analog
  MUI-`IconButton`-Padding), damit es auf Touch-Tablets präzise treffbar ist.
- **Reduzierte Bewegung (UI-NFR-002 R-022, O-003):** Bei `prefers-reduced-motion: reduce` wird die
  react-grid-layout-`transitionDuration` auf 0 gesetzt.
- Auf Mobile (< 600 px, UI-NFR-001) ist Drag-and-Drop deaktiviert; die Anordnung des `sm`-Breakpoints
  erfolgt über die Reihenfolge-/Größen-Buttons (Settings). Ohne eigenes `sm`-Placement stapelt das Grid
  einspaltig nach der `lg`-Reihenfolge (`y`, dann `x`).

Beide Flächen mutieren denselben `DashboardLayout` (`widgets` + `placements[breakpoint]`) und rufen
`saveDashboardLayout`.

### 3.9 Frontend — Rendering & Resilienz

- **Read-Only-Rendering ohne DnD-Library (UI-NFR-003, K-001):** Außerhalb des Bearbeiten-Modus rendert
  `DashboardPage.tsx` das effektive Layout (gespeichert oder Default) über ein **reines CSS-Grid** —
  **nicht** über `react-grid-layout`. Die Spaltenzahl folgt dem aktiven Breakpoint (`GRID_COLS_BY_BREAKPOINT`
  lg=12/md=8/sm=4, via CSS-Media-Queries), `grid-column`/`grid-row` werden aus `placements[breakpoint]`
  (Fallback `lg`) berechnet. Damit wird die DnD-Bibliothek (+ `react-draggable`/`react-resizable`,
  ~35–50 KB gzip) beim normalen Öffnen der meistbesuchten Seite gar nicht geladen und erst beim Aktivieren
  des „Bearbeiten"-Toggles per `React.lazy()` nachgezogen (§3.8). Widget-Komponenten kommen lazy aus der
  Registry (§3.4).
- **DOM-Order = Lesereihenfolge (UI-NFR-002 R-004/R-026 / WCAG 1.3.2, U-002):** Die Widgets werden **nach
  `(y, x)` des aktiven Breakpoint-Placements sortiert** in die DOM eingefügt — unabhängig von der
  Reihenfolge im `widgets`-Array. So folgt Tab-/Screenreader-Reihenfolge auf **jedem** Breakpoint der
  visuellen „oben-links-zuerst"-Anordnung.
- **Fehler-Isolation (REQ-009 DoD):** Jedes Widget ist in eine `ErrorBoundary` gekapselt; ein einzelner
  Widget-Fehler zeigt Inline-Fehler + Retry, blockiert aber nicht das gesamte Dashboard.
- **Empty-/Loading-States:** je Widget verpflichtend (REQ-009 DoD).
- **Leeres Dashboard (0 Widgets, U-003):** Deaktiviert der Nutzer alle Widgets (`widgets == []`), rendert
  `/dashboard` **keine** leere Seite, sondern einen Empty-State mit CTA („Widgets auswählen" →
  `/settings#dashboard`) **und** „Standard wiederherstellen" (→ `saveDashboardLayout(null)`).
- **Initial-Load parallel, nicht sequenziell (UI-NFR-003 TTI, O-001):** `GET …/user-preferences` und
  `GET …/dashboard/widgets/catalog` werden parallel geladen; `…/dashboard/aggregated?widgets=…` startet
  sofort mit den rohen `widget_key`s aus `dashboard_layout` (nicht auf `catalog.available` warten) — die
  Verfügbarkeits-Filterung passiert client-seitig beim Rendern.
- **PWA-Offline (UI-NFR-012):** Layout ist lokal gecacht → Dashboard ist offline sofort strukturiert
  sichtbar; Widget-Daten aus Cache; KI-Widgets zeigen „Online erforderlich".

## 4. Authentifizierung & Autorisierung

**Standardregel:** Alle Endpunkte erfordern Authentifizierung (JWT Bearer) und Tenant-Mitgliedschaft
(REQ-023/REQ-024).

| Ressource/Endpoint | Lesen | Schreiben | Löschen/Reset |
|--------------------|-------|-----------|---------------|
| `dashboard_layout` (Teil der eigenen `UserPreference`) | Alle Rollen | Ab Gärtner | Ab Gärtner (via PATCH `null`) |

> Die Rollenangaben folgen REQ-049 §3.1. Der Zusatz „nur den eigenen" ist **kein** Rollenbegriff — „Eigentümer (self)" stand hier bis #1216 als einer — sondern ein Prädikat auf Service-Ebene: jede Rolle erreicht ausschließlich ihren eigenen `dashboard_layout`, und das erzwingt der Service, nicht die Rechtetabelle.
| `GET …/dashboard/widgets/catalog` | Alle Rollen | — | — |
| Widget-**Inhalte** (REQ-009 `aggregated`/Polls) | gemäß REQ-024 Permission-Matrix pro Datenquelle | — | — |

- Ein Nutzer kann **nur sein eigenes** Layout lesen/schreiben; das Layout ist an `user_key` gebunden und
  tenant-isoliert (kein Cross-User-, kein Cross-Tenant-Zugriff).
- Das **Vorhandensein** eines Widgets im Layout gewährt **keinen** Datenzugriff: Widget-Inhalte werden
  weiterhin durch die REQ-024-Permission-Matrix der jeweiligen Datenquelle autorisiert. Fehlt die
  Permission, ist das Widget im Katalog `available=false` und wird nicht gerendert.

## 5. Abhängigkeiten

**Erforderliche Module:**

- **REQ-009** — Widget-Katalog, Datenquellen, Polling-Intervalle, `aggregated`-Endpunkt (SSOT). REQ-045
  realisiert dessen Phase-2-Punkte „Drag-and-Drop-Widget-Anordnung" und „per-User-Layout".
- **REQ-021** (Erfahrungsstufen) — Quelle des Default-Layouts (`DEFAULT_WIDGETS_BY_LEVEL`).
- **REQ-042** (Modulare Feature-Sichtbarkeit) — gated, welche Widgets wählbar/darstellbar sind; liefert
  das erprobte Katalog-/Persistenz-/localStorage-Muster als Vorlage.
- **REQ-024 v1.3** (Multi-Tenant/Permission-Matrix) — Layout pro Tenant; Datenzugriff pro Widget.
- **REQ-027 v1.4** (Light-Modus) — localStorage-Persistenz; Filterung von `community_activity`;
  `daily_tip` nur mit Whitelist-AI-Provider.
- **REQ-020** (Onboarding) — `onboarding_progress`-Widget nur bei unvollständigem Onboarding.
- **REQ-022** (Pflegeerinnerungen) / **REQ-031** (KI-Daily-Tip) — Widget-Datenquellen.
- **UI-NFR-001** (Responsive) — Breakpoints `lg`/`md`/`sm`, Mobile-Stapelung, Touch-Targets ≥ 48 px (R-011).
- **UI-NFR-002** (Barrierefreiheit) — **R-024..R-027** (Drag-and-Drop-Alternativen: tastaturbedienbares
  Kebab-Menü, Handles nicht im Tab-Index, Meaningful Sequence dynamischer Grids); ARIA-Live bei Reorder.
- **UI-NFR-003** — **R-028** (route-spezifisches Bundle-Budget für `/dashboard`); `react-grid-layout` nur
  im Bearbeiten-Modus lazy, Read-Only per CSS-Grid.
- **UI-NFR-012** (PWA-Offline) — Layout offline aus Cache; Polling-Pause.
- **UI-NFR-019** (Kiosk) — **ausgenommen**: Kiosk behält festes Layout, keine Personalisierung.
- **NFR-007** (Performance) — Layout-Laden Teil des `UserPreference`-GET; Persistenz debounced.

**Impact auf bestehende Artefakte:**

- `app/domain/models/user_preference.py` — Feld `dashboard_layout`, Modelle `DashboardLayout`/`DashboardWidgetInstance`.
- `app/domain/services/user_preference_service.py` — `KNOWN_WIDGET_KEYS`, `_sanitize_layout`, Reset-Semantik (`exclude_unset`).
- `app/api/v1/user_preferences/schemas.py` — `dashboard_layout` in Response/Update.
- `app/api/v1/dashboard/` — neuer `GET …/dashboard/widgets/catalog`; `aggregated` (REQ-009) auf tenant-scoped Route.
- Frontend: neu `config/dashboardWidgetCatalog.ts`, `components/dashboard/widgetRegistry.ts`,
  `pages/auth/DashboardSettingsTab.tsx`, `lib/dashboardLayoutStorage.ts`, Refactor `pages/DashboardPage.tsx`
  (QuickActions → `quick_actions`-Widget), Store-Erweiterung.

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Widget-Katalog synchron:** Contract-Test stellt sicher, dass Frontend-`WidgetKey`/`dashboardWidgetCatalog`
      und Backend-`KNOWN_WIDGET_KEYS` deckungsgleich sind (analog REQ-042 Modul-Contract-Test).
- [ ] **Hinzufügen/Entfernen:** Nutzer kann Widgets aus dem Katalog im Settings-Tab an-/abwählen; Änderung
      persistiert und ist nach Reload sichtbar.
- [ ] **Anordnen (Drag-and-Drop):** Im Bearbeiten-Modus auf `/dashboard` lassen sich Widgets per Maus/Touch
      verschieben und in der Größe (innerhalb `min/maxSize`) ändern.
- [ ] **Pro-Breakpoint-Layouts (v1.2):** Der Breakpoint-Umschalter (Desktop/Tablet/Mobile) bearbeitet
      `placements[lg|md|sm]` getrennt; ein fehlender Breakpoint wird aus `lg` abgeleitet; „für alle
      übernehmen" kopiert die aktuelle Anordnung. `widgets` (welche Widgets) bleibt breakpoint-übergreifend gleich.
- [ ] **Discoverability (v1.2, U-004/U-005):** „⚙ Widgets verwalten"-Deep-Link im `/dashboard`-Header →
      `/settings#dashboard`; einmaliger First-Use-Coachmark (localStorage `dashboard_personalization_hint_dismissed`).
- [ ] **Barrierefreie Alternative (UI-NFR-002):** Reihenfolge und Größe sind vollständig über
      Tastatur/Buttons im Settings-Tab steuerbar — ohne Drag-and-Drop.
- [ ] **Per-Widget-Konfiguration:** Widgets mit `hasConfig` bieten einen Konfig-Dialog; Config wird in
      `widget.config` persistiert und beim Rendern angewendet.
- [ ] **Default aus Erfahrungsstufe:** Ohne gespeichertes Layout rendert das aus `experience_level`
      abgeleitete Default (Beginner ≈ 7–8, Intermediate mehr, Expert alle verfügbaren Widgets).
- [ ] **Zurücksetzen:** „Auf Standard zurücksetzen" (PATCH `dashboard_layout=null`) stellt das
      Erfahrungsstufen-Default wieder her.
- [ ] **Persistenz pro Nutzer & Tenant:** Layout ist an `user_key` gebunden, tenant-isoliert; ein zweiter
      Nutzer/Tenant sieht sein eigenes Layout.
- [ ] **Light-Modus (REQ-027):** Layout wird in `localStorage` gehalten; `community_activity` nicht
      wählbar; `daily_tip` nur mit Whitelist-AI-Provider. Signup-Migration übernimmt lokales Layout.
- [ ] **Gating (REQ-042/REQ-024):** Widget, dessen Modul ausgeblendet oder dessen Datenquelle nicht
      erlaubt ist, erscheint im Settings-Tab ausgegraut (mit Begründung) und wird nicht gerendert.
- [ ] **Unbekannte Widgets tolerant:** Ein `widget_key`, den das Backend nicht kennt, wird beim Speichern
      verworfen + geloggt (Layout wird nicht komplett abgelehnt).
- [ ] **Fehler-Isolation:** Ein fehlerhaftes Widget blockiert das Dashboard nicht (ErrorBoundary + Retry).
- [ ] **Responsive (UI-NFR-001):** < 600 px → einspaltige Stapelung, kein Drag-and-Drop, Touch-Targets ≥ 48 px (R-011); Resize-Handle-Hit-Area ≥ 48 px.
- [ ] **Barrierefreiheit (UI-NFR-002 R-024..R-027):** Tab-/Screenreader-Reihenfolge folgt `(y, x)` je Breakpoint; Bearbeiten-Modus per Kebab-Menü voll tastaturbedienbar (Drag-Handles nicht im Tab-Index); Reorder-Aktionen via ARIA-Live angekündigt; `prefers-reduced-motion` respektiert.
- [ ] **Leeres Dashboard:** bei 0 Widgets Empty-State mit CTA (Widgets auswählen / Standard wiederherstellen) statt leerer Seite.
- [ ] **Bundle (UI-NFR-003 R-028):** Read-Only-Rendering per CSS-Grid **ohne** `react-grid-layout`; DnD-Library + Widgets lazy (erst im Bearbeiten-Modus); route-spezifisches Bundle-Budget des `/dashboard`-Chunks CI-überwacht.
- [ ] **PWA-Offline (UI-NFR-012):** Layout offline sofort strukturiert sichtbar; Widget-Daten aus Cache.
- [ ] **Kiosk ausgenommen (UI-NFR-019):** `/kiosk` bleibt unverändert festes Layout; **kein** Aufruf von `dashboard/widgets/catalog` oder `PATCH dashboard_layout` von `/kiosk` aus (verifizierbar auf Netzwerk-/Code-Splitting-Ebene).
- [ ] **i18n:** Alle Widget-Labels, Beschreibungen, Begründungen und Settings-Texte in DE + EN.

### Testszenarien (GIVEN/WHEN/THEN):

**Szenario 1: Widget hinzufügen und anordnen**
```
GIVEN: Nutzer (Full-Modus) mit Default-Layout (ohne gespeichertes dashboard_layout)
WHEN:  Nutzer aktiviert im Settings-Tab das Widget "sensor_live" und verschiebt es
       im Bearbeiten-Modus an Position (0,0)
THEN:  - PATCH …/user-preferences persistiert dashboard_layout mit "sensor_live" @ (0,0)
       - Nach Reload zeigt /dashboard "sensor_live" oben links
       - Alle übrigen Default-Widgets bleiben erhalten
```

**Szenario 2: Zurücksetzen auf Erfahrungsstufen-Default**
```
GIVEN: Nutzer (experience_level=intermediate) mit stark angepasstem Layout
WHEN:  Nutzer klickt "Auf Standard zurücksetzen"
THEN:  - PATCH sendet dashboard_layout=null (Reset, nicht "unset")
       - GET liefert dashboard_layout=null
       - /dashboard rendert das Intermediate-Default-Set
```

**Szenario 3: Modul-Gating (REQ-042)**
```
GIVEN: Layout enthält aktives Widget "tank_status" (requiredModule=tanks)
WHEN:  Nutzer blendet das Modul "tanks" in den Modul-Einstellungen aus (REQ-042)
THEN:  - "tank_status" wird auf /dashboard nicht mehr gerendert (kein leerer Container)
       - Im Dashboard-Settings-Tab erscheint es als "inaktiv (Modul ausgeblendet)"
       - Das Widget bleibt im dashboard_layout gespeichert (kein stiller Datenverlust)
       - Reaktiviert der Nutzer "tanks", erscheint "tank_status" wieder
```

**Szenario 4: Tenant-Isolation (REQ-024)**
```
GIVEN: Nutzer ist Mitglied in Tenant A und Tenant B mit unterschiedlichen Layouts
WHEN:  Nutzer wechselt via Tenant-Switcher von A nach B
THEN:  - /dashboard lädt das für Tenant B gespeicherte Layout
       - Änderungen in B verändern das Layout von A nicht
```

**Szenario 5: Unbekannter Widget-Key (Vorwärtskompatibilität)**
```
GIVEN: Client sendet ein Layout mit widget_key="experimental_x" (Backend kennt ihn nicht)
WHEN:  PATCH …/user-preferences
THEN:  - Backend verwirft nur "experimental_x" (Warn-Log), speichert die übrigen Widgets
       - GET liefert das bereinigte Layout ohne "experimental_x"
       - HTTP 200 (kein 422 für das gesamte Layout)
```

**Szenario 6: Light-Modus-Persistenz & Migration (REQ-027)**
```
GIVEN: Anonymer Light-Modus-Nutzer passt sein Dashboard an
WHEN:  Layout gespeichert, danach Registrierung (Light → Full)
THEN:  - Vor Signup liegt das Layout in localStorage (kein Backend-Call)
       - "community_activity" war nicht wählbar
       - Nach Signup ist das lokale Layout einmalig auf den Server migriert
         (localStorage danach geleert)
```

**Szenario 7: Barrierefreie Reihenfolge (UI-NFR-002)**
```
GIVEN: Nutzer navigiert per Tastatur in den Dashboard-Settings-Tab
WHEN:  Fokus auf Widget "tasks_today", Aktivierung des "Nach oben"-Buttons
THEN:  - Widget rückt in der Reihenfolge eine Position nach oben
       - Änderung ist ohne Maus/Drag-and-Drop möglich und wird persistiert
       - Auf Mobile stapelt /dashboard entsprechend der neuen Reihenfolge
```

**Szenario 8: Fehler-Isolation**
```
GIVEN: Dashboard mit 6 Widgets; die Datenquelle von "harvest_forecast" liefert 500
WHEN:  /dashboard lädt
THEN:  - "harvest_forecast" zeigt Inline-Fehler + Retry-Button
       - Die anderen 5 Widgets rendern normal
       - Das Gesamt-Dashboard bleibt bedienbar
```

**Szenario 9: Leeres Dashboard (0 Widgets)**
```
GIVEN: Nutzer entfernt im Settings-Tab alle Widgets (dashboard_layout.widgets == [])
WHEN:  /dashboard lädt
THEN:  - Statt einer leeren Seite erscheint ein Empty-State mit Text + zwei CTAs
       - "Widgets auswählen" verlinkt nach /settings#dashboard
       - "Standard wiederherstellen" setzt dashboard_layout=null (Erfahrungsstufen-Default)
```

**Szenario 10: Pro-Breakpoint-Layout (v1.2)**
```
GIVEN: Layout mit 4 Widgets; placements existieren für "lg", aber nicht für "sm"
WHEN:  Nutzer wählt im Bearbeiten-Modus den Breakpoint "Mobile" und ordnet zwei
       Widgets per Reihenfolge-Buttons um
THEN:  - PATCH persistiert ein neues placements.sm (widgets-Liste unverändert)
       - Auf Desktop (lg) bleibt die Anordnung unangetastet
       - Vor der Bearbeitung wurde "sm" aus "lg" abgeleitet (einspaltig gestapelt)
       - Tab-/Screenreader-Reihenfolge folgt auf jedem Breakpoint dessen (y, x)
```

**Szenario 11: Migration Alt-Layout v1 → v2**
```
GIVEN: Persistiertes dashboard_layout mit schema_version=1 (widgets[].x/y/w/h, columns=12)
WHEN:  /dashboard lädt das Layout
THEN:  - Der Client liest die Positionen als placements.lg
       - widgets tragen nur noch widget_key + config (ohne x/y/w/h)
       - md/sm werden aus lg abgeleitet
       - Beim nächsten Speichern wird schema_version=2 persistiert
```

---

**Hinweise für RAG-Integration:**
- Keywords: Dashboard, Personalisierung, Widget, Layout, Drag-and-Drop, react-grid-layout, UserPreference,
  dashboard_layout, Widget-Katalog, Erfahrungsstufe, Modul-Sichtbarkeit, Einstellungen
- Fachbegriffe: Set-Semantik, additiver Override, Tenant-Isolation, Default-Layout, Katalog-Registry,
  Bundle-Budget, ErrorBoundary, Reset-Semantik
- Verknüpfung: Personalisierungs-Schicht über REQ-009 (Widget-SSOT), gated durch REQ-042/REQ-021/REQ-024/REQ-027
- Tech-Stack: FastAPI, Pydantic v2, ArangoDB (UserPreference), React 19, react-grid-layout, MUI 7, Redux Toolkit
