# Voranalyse — Issue #439

> Orchestrierung gemäß `spec/project/issue-orchestration/` (gelesen aus `claude-shared`).

## Issue-Metadaten

| Feld | Wert |
|---|---|
| Issue | [#439](https://github.com/nolte/kamerplanter/issues/439) |
| Titel | `feat(dashboard): make widget panels navigational — each links to its detail view (mobile-first)` |
| Labels | `enhancement`, `feat` |
| State | OPEN · keine Kommentare · keine verlinkten PRs · kein Milestone |
| Bezug | REQ-009 (Dashboard), REQ-045 (Personalisierung), REQ-042 (Modul-Sichtbarkeit), Mobile-First-Guideline |

## Klassifikation

**Primär: `feature-request`** — additive UI-Funktionalität (Widget-Panels werden navigierbar). Keine `security`- oder `spec-change`-Klasse → keine Pflicht-Klassifikationsbestätigung nötig. Sekundärdimension: keine.

## Requirements-Gate

Kein Requirement-Artefakt unter `project/requirements/` für #439. **Operator-Override erteilt** (Gate 2026-07-10): Das Issue trägt bereits eine quasi-vollständige Anforderung (Widget→Route-Mapping-Tabelle, Ist-Zustand mit exakten Dateipfaden, Draft-Akzeptanzkriterien). Die einzigen echten Anforderungslücken — die 3 offenen Fragen — wurden durch Operator-Entscheidungen geschlossen (siehe unten). `requirements-elicit` wird bewusst nicht dispatcht.

### Operator-Entscheidungen zu den offenen Fragen

| # | Frage | Entscheidung |
|---|---|---|
| 1 | `sensor_live` / `vpd_gauge` ohne Route | **Aus dem Dashboard entfernen/ausblenden** (nicht non-interaktiv lassen) |
| 2 | Panel- vs. Row-Level-Deep-Links | **Nur Panel-Level** in dieser Iteration (Row-Deep-Links als Folge-Issue) |
| 3 | `weather_forecast` verlinken | **Statisch lassen** (non-interaktiv) |

## Routing-Entscheidung (operator-bestätigtes Gate)

**Direkte Umsetzung** (nicht formale `roadmap → feature → sprint`-Pipeline).
Begründung: Ein kohärentes Goal-Outcome (Dashboard → Navigations-Hub), ein PR-Strang, **kein** neues oder umgetargetetes Roadmap-Item — bezieht sich auf bestehende REQ-009/045/042. → **bounded**.

## Working-Copy

Alle versionierten Writes in dediziertem Worktree `feat/dashboard-navigational-widgets`
(`/home/nolte/repos/.worktrees/kamerplanter/dashboard-nav`, off `origin/develop`). Primary-Checkout bleibt unverändert.

## In / Out of Scope

**In Scope:**
- Neues optionales Feld `navigateTo?: string` in `DashboardWidgetDefinition` + Befüllung des Panel-Level-Mappings.
- Generisches Panel-Level-Navigations-Affordance in `WidgetFrame`/`GenericWidget` (CardActionArea), modul-gated, im Edit-Modus unterdrückt, a11y-Name, ≥48px, Kebab-Menü bleibt bedienbar.
- `winter_protection`: Panel-Level-Link zusätzlich zu den bestehenden Ampel-Tile-Links.
- Entfernen von `sensor_live` + `vpd_gauge` aus dem Dashboard-Katalog (FE + BE + Contract-Fixture + i18n + Icon/Glossar-Maps).
- Tests, UI-Review, Doku.

**Out of Scope:**
- Row-/Tile-Level-Deep-Links (`plant_grid`-Kachel → `:key`, Task-Row → `:key`) → Folge-Issue.
- Navigation für `weather_forecast` (bleibt statisch).
- Neue Sensors-Page/-Route.

## Widget → Route-Mapping (Panel-Level, bestätigt)

| Widget | Ziel-Route |
|---|---|
| `tasks_today` | `/aufgaben/queue` |
| `care_reminders` | `/aufgaben/queue` |
| `active_plants_summary` | `/pflanzen/plant-instances` |
| `plant_grid` | `/pflanzen/plant-instances` |
| `tank_status` | `/standorte/tanks` |
| `winter_protection` | `/ueberwinterung/profile` |
| `ipm_alerts` | `/pflanzenschutz/pests` |
| `harvest_forecast` | `/ernte/batches` |
| `next_calendar_events` | `/kalender` |
| `phase_timeline` | `/phasen/ablaeufe` (exakter Slug bei Umsetzung gegen `AppRoutes.tsx` verifizieren) |
| `onboarding_progress` | `/onboarding` |
| `quick_actions` | — (bereits Navigations-Grid, Referenzmuster) |
| `weather_forecast` | — (statisch) |
| `sensor_live` | **entfernt** |
| `vpd_gauge` | **entfernt** |

## Arbeitspakete

Spezialisten per Runtime-Katalog-Lookup dieser Session aufgelöst (projekt-lokale Agenten unter `.claude/agents/` bzw. `nolte-*`-Plugins). Alle Code-Pakete → projekt-eigener `fullstack-developer` (Feedback: „Fullstack-Developer bevorzugt für Source-Code"). Verifikationskette gemäß Projekt-Feedback „PFLICHT: 3-Agent-Kette (UI-Review → Tests → Doku)".

| ID | Problemstellung | Akzeptanzkriterium (testbar) | Berührte Dateien | Spezialist | Abhängt von |
|---|---|---|---|---|---|
| **WP-1** | `DashboardWidgetDefinition` um optionales `navigateTo?: string` erweitern und Panel-Mapping (Tabelle oben) befüllen. | Katalog trägt für jedes gemappte Widget die korrekte Route; `weather_forecast`/`quick_actions` ohne `navigateTo`; TS kompiliert. | `config/dashboardWidgetCatalog.ts` | `fullstack-developer` | — |
| **WP-2** | Generisches Panel-Level-Navigations-Affordance: Panel-Body in `CardActionArea` wrappen, `navigate(def.navigateTo)` nur wenn gesetzt **und** `isPathVisible(navigateTo)`; im Edit-Modus unterdrückt; a11y-Name („Open <label>"); ≥48px; Kebab-Menü nicht verschluckt. `winter_protection` Panel-Level-Link ergänzen. | Klick auf gemapptes Panel navigiert zur Route; kein Affordance bei fehlendem/unsichtbarem Ziel; im Edit-Modus keine Navigation; Panel keyboard-fokussierbar mit beschreibendem Namen; Kebab weiter bedienbar. | `WidgetFrame.tsx`, `widgets/GenericWidget.tsx`, `WinterProtectionWidget.tsx` | `fullstack-developer` | WP-1 |
| **WP-3** | `sensor_live` + `vpd_gauge` aus dem Dashboard-Katalog entfernen (FE `WidgetKey`-Union/Katalog/Registry, `GenericWidget` Icon+Glossar-Maps, BE `dashboard_widget_catalog.py`, Contract-Fixture `dashboard-widgets.json`, i18n `de/en`). Verwaiste gespeicherte Instanzen werden bereits von `user_preference_service` gedroppt (kein Migrationsbedarf) — verifizieren. | FE+BE-Katalog und Contract-Fixture enthalten die beiden Keys nicht mehr; Contract-Test grün; keine dangling i18n/Icon-Referenz; Layout mit Alt-Instanz lädt ohne Fehler. | FE-Katalog/Registry/GenericWidget/i18n, BE `dashboard_widget_catalog.py`, `contracts/dashboard-widgets.json` | `fullstack-developer` | — (sequenziell auf gleichem Tree) |
| **WP-4** | Component/Unit-Tests: Navigation klickt → Route, Edit-Modus unterdrückt, modul-gated verborgen, kein-Ziel inert, Keyboard; Contract-Key-Set aktualisiert. | Neue Tests grün; `quality-gate`/`unit-test-runner` grün; Contract-Test spiegelt entfernte Keys. | `src/frontend/src/test/**`, `contracts/*` | `unit-test-runner` | WP-1/2/3 |
| **WP-5** | UI-Review der navigierbaren Dashboard-Panels (Mobile-Single-Column, Touch-Target ≥48px, kein Verdecken des Titels durch Affordance, klare Klick-Affordanz, Hover/Focus-States). | Review-Bericht ohne kritische Findings bzw. Findings fix-forward behoben. | Presentation-Layer | `frontend-usability-optimizer` | WP-2 |
| **WP-6** | Doku aktualisieren (REQ-009/045 Dashboard: navigierbare Panels, entfernte Sensor-Widgets), DE-kanonisch + EN-Spiegel. | Docs-Seiten aktualisiert, `mkdocs build --strict` grün. | `docs/**` | `mkdocs-documentation` | WP-1/2/3 |

### Abhängigkeitsordnung (DAG)

```
WP-1 ─┬─> WP-2 ─┬─> WP-5 (UI-Review)
      │         │
WP-3 ─┴─────────┴─> WP-4 (Tests) ──> WP-6 (Doku) ──> quality-gate ──> PR
```

## Risiken

- **REQ-045-Kompatibilität:** Entfernen von `sensor_live`/`vpd_gauge` verwaist gespeicherte Widget-Instanzen. Mitigiert durch bestehende `user_preference_service`-Drop-Logik (unbekannte Keys werden verworfen) — muss durch Test bestätigt werden. Kein DB-Migrationsschritt.
- **Edit-Mode-Konflikt:** Navigation darf im Edit-Modus (Drag/Resize/Configure) nicht feuern — explizit unterdrücken und testen.
- **Kebab-Verdeckung:** CardActionArea darf das Edit-Kebab-Menü und dessen ≥48px-Hit-Area nicht verschlucken; z-index/Event-Stopping beachten.
- **Route-Slug-Drift:** `phase_timeline`-Ziel (`/phasen/ablaeufe`) bei Umsetzung gegen `AppRoutes.tsx` verifizieren.
- **Contract-Test:** FE/BE-Key-Set-Parität — `dashboard-widgets.json` muss synchron mit beiden Katalogen entfernt werden, sonst rotes Gate.

## Offene Fragen (an Operator)

Keine offen — alle 3 Issue-Fragen durch Operator-Entscheidungen geschlossen.

## Audit-Trail

- `classification`: `feature-request`
- `route`: direct
- `requirements_gate`: operator-override (kein Artefakt; Issue selbst-tragend + 3 Operator-Entscheidungen)
- `specialists`: `fullstack-developer`, `unit-test-runner`, `frontend-usability-optimizer`, `mkdocs-documentation`
