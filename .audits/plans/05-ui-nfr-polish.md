---
plan-type: implementation-plan
title: UI-NFR-Polish — Performance-Härtung + Kiosk-Modus
epic: ui-nfr-polish
covers: [UI-NFR-003, UI-NFR-019]
source-audit: .audits/req-coverage-audit/UI-NFR-003.md, UI-NFR-019.md
based-on-spec: [spec/ui-nfr/UI-NFR-003_Performance.md, spec/ui-nfr/UI-NFR-019_Kiosk-Modus.md]
status: ready
created: 2026-07-10
verified-against: develop
parallelizable: true
specialist: fullstack-developer / frontend-usability-optimizer
---

## Ziel

Zwei unabhängige UI-NFR-Lücken schließen, die im Coverage-Audit als „Idee" (0 fehlende Pflicht-Artefakte) geführt sind, aber realen, umsetzbaren Feature-Scope aus den Specs tragen:

1. **UI-NFR-003 (Performance-Härtung):** Die App lädt bereits route-lazy und nutzt Skeletons, aber es fehlt die **Absicherung gegen schleichende Regression** — kein CI-Bundle-Budget-Gate (R-015), kein Route-spezifisches Chunk-Budget für `/dashboard` (R-028), keine `manualChunks`-Strategie in Vite, keine Lighthouse-Messung. Ziel ist die Performance-Infrastruktur, die die Core Web Vitals dauerhaft grün hält, plus punktuelle Lückenschlüsse (Skeleton-Audit, Debounce-Vollständigkeit, Virtual Scrolling für >50-Einträge-Listen).

2. **UI-NFR-019 (Kiosk-Modus):** Vollständig fehlendes Feature. Ein dedizierter Kiosk-Modus für die Bedienung im Gewächshaus/Growraum mit verschmutzten Händen und Handschuhen — `/kiosk`-Route + Settings-Toggle, persistente User-Präferenz, High-Contrast-Theme, große Touch-Targets, Quick-Action-Startseite, Auto-Timeout. Umsetzung folgt der 4-Phasen-Priorisierung aus §2.10 der Spec (MVP = Phase 1+2).

Beide Pakete sind **mobile-first** und **WCAG-AA** (Kiosk-Theme sogar AAA/7:1) umzusetzen (NFR-003: Code/Bezeichner Englisch).

## Ist-Stand (verifiziert 2026-07-10)

### UI-NFR-003 Performance

| Bereich | Ist-Stand im Code | Bewertung |
|---------|-------------------|-----------|
| Route-Code-Splitting (R-010) | `src/frontend/src/routes/AppRoutes.tsx` lädt **alle** Seiten via `React.lazy` + `Suspense` (fallback `<LoadingSkeleton variant="card" />`). ~40+ lazy Page-Imports. | **Weitgehend erfüllt.** Nur Audit + Fallback-Konsistenz offen. |
| Schwere Komponenten lazy (R-012) | Dashboard-Widgets lazy in `src/frontend/src/components/dashboard/widgetRegistry.ts` (`GenericWidget`, `QuickActionsWidget`, `WinterProtectionWidget`, `WeatherForecastWidget`). | Teilweise. Grid-/DnD-Layout-Engine (react-grid-layout) für Dashboard-Edit-Modus noch zu prüfen (R-028). |
| Skeleton-Screens (R-006..009) | `Skeleton` in **70 Nicht-Test-Dateien** verwendet; zentrale `src/frontend/src/components/common/LoadingSkeleton.tsx`, `DataTable.tsx`, `WidgetFrame.tsx`, viele Detail-/List-Pages. | **Breit vorhanden**, aber keine systematische Abdeckungs-Garantie. Audit nötig. |
| Debouncing Suche (R-017) | `src/frontend/src/hooks/useDebounce.ts` existiert; genutzt in `DataTable.tsx`, `FertilizerListPage.tsx`, `useDashboardLayout.ts`. | Teilweise. Nicht alle Sucheingaben nachweislich abgedeckt. |
| Pagination/Virtual Scroll (R-018) | `DataTable.tsx` nutzt `TablePagination`. Kein `react-window`/`react-virtualized` im Repo. | Pagination ja; Virtual Scrolling nein. Für sehr lange, nicht-paginierte Listen offen. |
| Vite Build-Config (R-013/R-014/R-016) | `src/frontend/vite.config.ts` hat **keine** `build`-Sektion, **kein** `manualChunks`, **kein** Chunk-Budget. Nur `plugins:[react()]`, alias, dev-proxy. Tree-Shaking = Vite/Rollup-Default (aktiv). | **Gap.** Keine Vendor-Chunk-Strategie → schwer kontrollierbares Initial-Bundle. |
| Bundle-Size CI-Gate (R-015) | `.github/workflows/frontend.yml` hat `lint-test-build` + `coverage`. **Kein** Bundle-Budget-Step, kein `size-limit`, `rollup-plugin-visualizer`, `bundlesize` in `package.json`. | **Gap — Kernstück.** Build failt aktuell nie wegen Bundle-Wachstum. |
| Lighthouse (DoD §4) | Nirgends. Keine `@lhci/cli`-Config. | **Gap.** Keine CWV-Messung. |
| Caching (R-026/R-027) | `src/frontend/src/lib/serviceWorkerRegistration.ts` vorhanden; Assets bekommen Content-Hash durch Vite-Default; nginx-unprivileged serviert (Container-Härtung #440). | Vite-Hashing erfüllt R-026; `index.html` `Cache-Control: no-cache` in nginx-Config zu verifizieren. |
| Hook-Stabilität (R-023..025) | Projekt-Konvention (CLAUDE.md / MEMORY): Hooks mit Objekt-/Array-Rückgabe `useMemo`-stabilisiert. | Konvention etabliert; ESLint-Regel-Verankerung optional. |

**Fazit UI-NFR-003:** Die *Laufzeit*-Basis (Lazy-Routes, Skeletons, Debounce, Pagination) steht überraschend gut. Der echte Gap ist die **CI-verankerte Regressionssicherung** (R-015, R-028) plus `manualChunks`-Strategie (R-013) und Lighthouse-Messung.

### UI-NFR-019 Kiosk-Modus

| Bereich | Ist-Stand im Code | Bewertung |
|---------|-------------------|-----------|
| Kiosk-Modus komplett | Keine `Kiosk*.tsx`, keine `/kiosk`-Route, kein `KioskProvider`. Der einzige Treffer für „kiosk" ist ein i18n-String in `ImageCapturePanel.tsx` (unabhängig). | **Vollständig fehlend.** Greenfield. |
| Theme | `src/frontend/src/theme/theme.ts` → `buildTheme(mode)` nur `'light'|'dark'`; `src/frontend/src/theme/ThemeContext.tsx` verwaltet nur `mode` (localStorage `STORAGE_KEY`). Kein High-Contrast-Theme, keine kiosk-spezifischen Component-Defaults. | High-Contrast + Kiosk-Theme-Variante zu ergänzen. |
| User-Präferenz | Frontend `src/frontend/src/store/slices/userPreferencesSlice.ts` + `src/frontend/src/api/endpoints/userPreferences.ts`; Backend `src/backend/app/domain/models/user_preference.py` (`UserPreference` mit `theme`, `module_visibility`, `dashboard_layout` …) + `user_preference_service.py`. | Erweiterbar: neue Felder `kiosk_enabled`, `high_contrast`, `kiosk_timeout_seconds`, `kiosk_audio_enabled`. |
| Quick-Actions | `src/frontend/src/components/dashboard/widgets/QuickActionsWidget.tsx` existiert (REQ-045). | Als inhaltliche Vorlage/Wiederverwendung für Kiosk-Kacheln nutzbar. |
| Layout/Router | `src/frontend/src/layouts/MainLayout.tsx` (Sidebar/Breadcrumbs); Router `createBrowserRouter` in `AppRoutes.tsx`. | Neues `KioskLayout` (ohne Sidebar/Breadcrumb) + `/kiosk`-Routenbaum additiv. |

**Fazit UI-NFR-019:** Greenfield-Feature, aber **keine strukturellen Blocker** — Theme-System, User-Preference-Persistenz (FE+BE) und Quick-Action-Inhalte existieren als Andockpunkte.

## Arbeitspakete

Zwei unabhängige Frontend-Arbeitspakete (`WP-Performance` ‖ `WP-Kiosk`). Innerhalb `WP-Kiosk` gilt die 4-Phasen-Priorisierung aus Spec §2.10 (MVP = P1+P2).

---

### WP-Performance — Performance-Infrastruktur & CI-Härtung (UI-NFR-003)

#### WP-P1 · CI-Bundle-Budget-Gate + Vite manualChunks (R-013, R-015, R-016, R-028)

**Problem:** `vite.config.ts` hat keine Chunk-Strategie; das Initial-Bundle ist unkontrolliert und kann durch schwere Libs (MUI, Redux, react-grid-layout, KI-Features) unbemerkt über 300 KB gzip wachsen. Kein CI-Gate failt bei Überschreitung — die Kern-MUSS-Anforderung R-015 fehlt vollständig.

**Umzusetzen:**
- `build.rollupOptions.output.manualChunks` in `vite.config.ts` einführen: Vendor-Splitting (mind. `react`/`react-dom`/`react-router`, `@mui/*` + `@emotion/*`, `@reduxjs/toolkit`/`react-redux`, `i18next`/`react-i18next`, schwere Layout-Engine `react-grid-layout`/DnD separat). (R-013, R-016)
- **Route-spezifisches Chunk-Budget** definieren: `/dashboard` bekommt ein eigenes, separat überwachtes Budget zusätzlich zum globalen Initial-JS-Budget; die Grid-/Drag-and-Drop-Layout-Engine MUSS hinter den „Bearbeiten"-Modus per Dynamic Import (`React.lazy`/`import()`) verschoben werden, sodass die Read-Only-Dashboard-Darstellung ohne sie auskommt. (R-028) — prüfen, ob `useDashboardLayout.ts`/Dashboard-Edit-Komponente react-grid-layout bereits lazy lädt; falls nicht, ausklammern.
- CI-Budget-Werkzeug wählen und in `package.json` + `.github/workflows/frontend.yml` verankern (empfohlen: `size-limit` mit `@size-limit/file` + gzip, alternativ `rollup-plugin-visualizer` + eigenes Assert-Skript). Budgets: **Initial-JS < 300 KB gzip (R-013)**, **Initial-CSS < 50 KB gzip (R-014)**, dediziertes `/dashboard`-Chunk-Budget (R-028).
- Neuer CI-Step `bundle-budget` (im `lint-test-build`-Job nach `Build` oder als eigener Job) der bei Budget-Überschreitung mit non-zero exit **den Build fehlschlagen lässt** (R-015).
- Bundle-Analyzer-Report bei jedem Build generieren (`rollup-plugin-visualizer` → `dist/stats.html`, als Artifact hochladen) (DoD §4).

**Betroffene Dateien:**
- `src/frontend/vite.config.ts` (build/manualChunks, visualizer-Plugin)
- `src/frontend/package.json` (devDeps `size-limit`/`@size-limit/preset-app` bzw. `rollup-plugin-visualizer`; `size-limit`-Config-Block; npm-Script `bundle:check`)
- `.github/workflows/frontend.yml` (Step/Job `bundle-budget`; Artifact-Upload stats.html)
- ggf. `.size-limit.json` / `.size-limit.cjs`
- Dashboard-Edit-Komponente + `src/frontend/src/hooks/useDashboardLayout.ts` (Layout-Engine hinter Interaktion lazy)

**Akzeptanzkriterien:**
- CI failt reproduzierbar, wenn das Initial-JS-Bundle > 300 KB gzip liegt (durch Test-Overshoot verifizierbar). (R-015)
- CI failt, wenn das `/dashboard`-Route-Chunk sein separates Budget überschreitet. (R-028)
- Read-Only-`/dashboard` lädt **kein** react-grid-layout/DnD-Chunk im Initial-Load; dieser wird erst beim Aktivieren des „Bearbeiten"-Modus nachgeladen (Netzwerk-Waterfall/Chunk-Namen prüfbar). (R-028, R-012)
- `manualChunks` erzeugt getrennte Vendor-Chunks; `dist/stats.html` wird als CI-Artifact publiziert.
- CSS-Budget < 50 KB gzip als Warn- oder Fail-Grenze im selben Gate. (R-014)

**Spezialist:** fullstack-developer  **Aufwand:** M  **Abhängigkeiten:** keine

#### WP-P2 · Lighthouse-CI & Core-Web-Vitals-Messung (R-001..005, DoD §4)

**Problem:** Keine automatisierte Messung der Core Web Vitals; die MUSS-Schwellwerte (FCP<1.5s, LCP<2.5s, TTI<3.5s, CLS<0.1, INP<200ms) und Lighthouse-Score ≥90 sind unbelegt.

**Umzusetzen:**
- `@lhci/cli` (Lighthouse CI) mit `lighthouserc.json`: Assertions auf Performance-Score ≥ 0.9, LCP/CLS/TBT-Budgets abgeleitet aus R-001..005. (R-001..005)
- CI-Job `lighthouse` in `frontend.yml`: Preview-Build (`vite preview`) starten, mobile Emulation (Moto-G4-Profil, 4G-Throttling gemäß DoD), Assertions. Zunächst als **nicht-required** Report-Job (Warnschwelle), danach Verschärfung — konsistent mit der Repo-Praxis „nur `static` ist required" (MEMORY).
- Ergebnis als CI-Artifact/Job-Summary.

**Betroffene Dateien:**
- `src/frontend/lighthouserc.json`
- `.github/workflows/frontend.yml` (Job `lighthouse`)
- `src/frontend/package.json` (devDep `@lhci/cli`, Script `lhci`)

**Akzeptanzkriterien:**
- CI erzeugt bei jedem PR einen Lighthouse-Report mit den 5 CWV-Metriken. (R-001..005)
- Assertions vorhanden für Score ≥ 90, LCP < 2.5s, CLS < 0.1 (mobile Emulation, 4G). (DoD §4)
- Report ist als Artifact/Summary einsehbar.

**Spezialist:** fullstack-developer  **Aufwand:** M  **Abhängigkeiten:** WP-P1 (stabiler Build) empfohlen, nicht zwingend.

#### WP-P3 · Skeleton-Coverage-Audit & Ladeindikator-Konsistenz (R-006..009)

**Problem:** Skeletons sind breit gestreut (70 Dateien), aber ohne systematische Garantie, dass **jeder** seitenweite async Ladevorgang einen formtreuen Platzhalter zeigt und Spinner nur für kurze, fokussierte Aktionen genutzt werden.

**Umzusetzen:**
- Audit aller Pages/Container mit Datenladung: Liste erstellen, welche einen formtreuen Skeleton (R-007) statt leerer Seite/zentralem Spinner bei Seitenübergängen zeigen. (R-006, R-009)
- Lücken schließen: fehlende Skeletons ergänzen, formtreue Varianten in `LoadingSkeleton.tsx` erweitern (Tabelle, Detail, Karte, Formular). (R-007)
- Sicherstellen: Ladevorgänge > 300ms zeigen visuellen Indikator; Spinner nur bei Button-Aktionen (nicht bei Route-Wechsel — dort Skeleton). (R-008, R-009)
- Layout-Shift-Prüfung: feste Dimensionen für Skeletons = Zielinhalt (CLS-Beitrag, R-004/R-007).

**Betroffene Dateien:**
- `src/frontend/src/components/common/LoadingSkeleton.tsx` (Varianten erweitern)
- Betroffene Pages ohne/mit unpassendem Ladezustand (aus Audit-Liste)
- ggf. `src/frontend/src/routes/AppRoutes.tsx` (Suspense-Fallback-Varianten je Routentyp)

**Akzeptanzkriterien:**
- Audit-Ergebnis dokumentiert (Liste Page → Ladezustand); keine seitenweite async Ladung ohne Platzhalter. (R-006)
- Route-Suspense-Fallbacks sind formtreu (kein reiner Spinner bei Seitenübergängen). (R-009)
- Kein messbarer Layout-Shift beim Nachladen (CLS < 0.1 in Lighthouse-Job). (R-007, R-004)

**Spezialist:** frontend-usability-optimizer  **Aufwand:** M  **Abhängigkeiten:** keine (WP-P2 verifiziert CLS)

#### WP-P4 · Debounce-Vollständigkeit, Virtual Scrolling & below-fold-Bilder (R-011, R-017, R-018, R-020)

**Problem:** `useDebounce` existiert, ist aber nicht nachweislich an allen Sucheingaben verdrahtet; sehr lange, nicht-paginierte Listen haben kein Virtual Scrolling; below-fold-Bilder ohne garantiertes `loading="lazy"`; keine systematische Request-Deduplizierung/Abort bei schnellen Navigationswechseln.

**Umzusetzen:**
- Alle freien Sucheingabefelder auf `useDebounce` (300ms) prüfen/nachrüsten. (R-017)
- Listen > 50 Einträge: entweder Pagination (bereits via `DataTable`/`TablePagination`) sicherstellen oder für lange, nicht-paginierbare Ansichten Virtual Scrolling einführen (`@tanstack/react-virtual` oder `react-window`). (R-018)
- Below-fold-`<img>` (Galerien, Listen-Thumbnails, `PestImageGallery`, `AuthImage`) auf `loading="lazy"` bzw. Intersection Observer setzen. (R-011)
- Request-Deduplizierung/`AbortController` bei schnellen Route-Wechseln in der API-Layer prüfen/ergänzen. (R-020)

**Betroffene Dateien:**
- `src/frontend/src/hooks/useDebounce.ts` (Consumer-Verdrahtung)
- `src/frontend/src/components/common/DataTable.tsx`
- Listen-Pages mit potenziell >50 Einträgen (aus Audit)
- `src/frontend/src/components/common/AuthImage.tsx`, `src/frontend/src/components/pests/PestImageGallery.tsx`
- API-Layer (`src/frontend/src/api/**`) für Abort/Dedup

**Akzeptanzkriterien:**
- Jede freie Sucheingabe debounced (300ms); Test/Story belegt kein Request-Sturm bei Tippen. (R-017)
- Mind. eine lange Liste nutzt Virtual Scrolling; DOM enthält nur sichtbare Zeilen. (R-018)
- Below-fold-Bilder tragen `loading="lazy"`. (R-011)
- Schnelle Navigationswechsel erzeugen keine doppelten/verwaisten Responses (AbortController). (R-020)

**Spezialist:** frontend-usability-optimizer  **Aufwand:** M  **Abhängigkeiten:** keine

---

### WP-Kiosk — Kiosk-Modus (UI-NFR-019)

Phasierung gemäß Spec §2.10: **MVP = WP-K1 + WP-K2 (Phase 1+2)**; WP-K3 + WP-K4 = Phase 3+4 (Polish, additiv).

#### WP-K1 · Kiosk-Modus-Aktivierung, Persistenz, Provider & Startseite (Phase 1 / MVP — R-001..004, R-014..016, R-018, R-033..036)

**Problem:** Kein Kiosk-Modus vorhanden. Nutzer weichen im Gewächshaus auf Papiernotizen aus (Spec §1.2). Es fehlt die Grundstruktur: `/kiosk`-Route, globaler Kiosk-State, Quick-Action-Startseite, Kiosk-Badge, Auto-Timeout.

**Umzusetzen:**
- `KioskProvider` (React Context): `isKiosk`, `toggleKiosk`, `timeoutConfig`, Fullscreen-Handle. Wechsel **ohne Reload** (R-004). (R-001)
- Persistenz als User-Präferenz: neue Felder in Backend `UserPreference` (`kiosk_enabled: bool`) + `user_preference_service.py` + FE `userPreferencesSlice`/`userPreferences.ts`; zusätzlich LocalStorage-Fallback für anonymen/Light-Modus. (R-002)
- `/kiosk`-Route + `KioskLayout` (keine Sidebar, kein Breadcrumb) additiv im Router `AppRoutes.tsx`. (R-001)
- Settings-Toggle zum Aktivieren (in `AccountSettingsPage`/Preferences-Tab). (R-001)
- Permanenter **Kiosk-Badge** in einer `KioskAppBar` (R-003).
- `KioskStartPage` mit 4 Quick-Action-Kacheln (min. 80×80px): **Pflanze scannen (QR), Bewässerung erfassen, Rundgang starten, Problem melden** (R-014, R-015); Inhalte an `QuickActionsWidget` anlehnen. Status-Bereich „Aktueller Status" (offene Aufgaben, letzte Aktivität, Warnungen) (R-016).
- `useKioskTimeout`-Hook: Inaktivitäts-Timer (Touch-Event-Listener), Timeout-Warnung nach 120s als großflächiges Overlay (≥50% Fläche) mit Countdown + „Weiter arbeiten"-Button (min. 72px), Auto-Reset zur Startseite nach weiteren 30s, Reset bei jeder Touch-Interaktion. (R-033..036)

**Betroffene Dateien (neu, falls nicht anders vermerkt):**
- `src/frontend/src/kiosk/KioskProvider.tsx`, `useKioskTimeout.ts`
- `src/frontend/src/layouts/KioskLayout.tsx`, `src/frontend/src/components/kiosk/KioskAppBar.tsx`
- `src/frontend/src/pages/kiosk/KioskStartPage.tsx`
- `src/frontend/src/components/kiosk/KioskTimeoutOverlay.tsx`
- `src/frontend/src/routes/AppRoutes.tsx` (+`/kiosk`, lazy)
- `src/frontend/src/store/slices/userPreferencesSlice.ts`, `src/frontend/src/api/endpoints/userPreferences.ts`
- `src/backend/app/domain/models/user_preference.py`, `src/backend/app/domain/services/user_preference_service.py`
- i18n `src/frontend/src/i18n/locales/{de,en}/translation.json` (`pages.kiosk.*`)

**Akzeptanzkriterien:**
- Kiosk-Modus über `/kiosk` **und** Settings-Toggle erreichbar; Wechsel ohne Seiten-Reload. (R-001, R-004)
- Präferenz überlebt Reload (Backend-Preference bei angemeldet, LocalStorage im Light-Modus). (R-002)
- „Kiosk"-Badge im aktiven Modus permanent sichtbar. (R-003)
- Startseite zeigt die 4 geforderten Quick-Actions als Kacheln ≥80×80px + Status-Bereich. (R-014..016)
- Timeout-Warnung nach 120s Inaktivität; Auto-Rückkehr zur Startseite nach 30s ohne Reaktion; Timer-Reset bei Touch. (R-033..036)

**Spezialist:** fullstack-developer  **Aufwand:** L  **Abhängigkeiten:** WP-K2 (Theme) für Default-High-Contrast lose gekoppelt.

#### WP-K2 · High-Contrast-Theme & Touch-Sizing (Phase 2 / MVP — R-005, R-007..013, R-029..032, R-039..045)

**Problem:** `theme.ts` kennt nur light/dark; keine kiosk-tauglichen Touch-Targets und kein High-Contrast-Theme für Lesbarkeit bei Sonneneinstrahlung/Handschuhbedienung.

**Umzusetzen:**
- **High-Contrast-Theme** als eigene Theme-Variante in `theme.ts` (`buildTheme` um `'high-contrast'` erweitern oder dedizierte Palette): reine Schwarz/Weiß-Flächen (R-041), Kontrast ≥7:1 (WCAG AAA, R-040), Schriftstärke ≥500 (R-042), Schatten/Hover/Gradients deaktiviert (R-043). Im Kiosk-Modus **default aktiv** (R-005); zusätzlich unabhängig über Settings aktivierbar (R-045).
- **Kiosk-Touch-Theme-Override:** MUI-Component-Defaults im Kiosk `size:'large'` (TextField, Button, IconButton, Select, Checkbox) (R-013); Mindest-Touch-Targets 64×64px (R-007), primäre Aktionen 72×72px (R-008), Element-Abstand ≥16px/empf. 24px (R-009), Listenzeilen ≥64px (R-010), Checkbox/Toggle-Touch-Bereich ≥64×64px (R-011), Icons ≥32px/Aktions-Icons 48px (R-012).
- Farbcodierte Status-Indikatoren ≥24px zusätzlich zu Text+Icon (R-044).
- Touch-Debouncing 300ms global für klickbare Elemente im Kiosk (R-029); Long-Press (2s) oder zweistufige Bestätigung für destruktive Aktionen, Abstand Bestätigen/Abbrechen ≥32px (R-030, R-031); Scroll-Indikatoren (Gradient-Fade/Pfeil) (R-032).

**Betroffene Dateien:**
- `src/frontend/src/theme/theme.ts`, `src/frontend/src/theme/palette.ts`, `src/frontend/src/theme/ThemeContext.tsx` (High-Contrast-Modus, Kiosk-Override)
- `src/frontend/src/kiosk/kioskTheme.ts` (Component-Default-Overrides)
- `src/frontend/src/components/layout/ThemeToggle.tsx` (High-Contrast-Option)
- Kiosk-ConfirmDialog-Variante (Long-Press), Scroll-Container-Komponente
- i18n-Strings

**Akzeptanzkriterien:**
- Kiosk-Modus aktiviert automatisch High-Contrast-Theme; separat via Settings aktivierbar. (R-005, R-045)
- Kontrast aller Texte ≥7:1 (axe-core/Contrast-Check belegt); keine Grauflächen, Schriftstärke ≥500, keine Schatten/Gradients. (R-040..043)
- Im Kiosk messbar (DevTools/axe-core): interaktive Elemente ≥64×64px, primäre Aktionen 72×72px, Abstand ≥16px, Zeilenhöhe ≥64px, MUI-Defaults `size:'large'`. (R-007..013)
- Destruktive Aktion erfordert Long-Press (2s) oder zweistufige Bestätigung; Button-Abstand ≥32px. (R-030, R-031)

**Spezialist:** fullstack-developer / frontend-usability-optimizer  **Aufwand:** M-L  **Abhängigkeiten:** liefert Theme-Basis für WP-K1-Startseite.

#### WP-K3 · Vereinfachte Navigation & Eingabe (Phase 3 — R-006, R-017..028)

**Problem:** Standard-Navigation (Breadcrumbs, Hamburger, Dropdowns, Freitext-Formulare) ist mit Handschuhen/nassen Händen unpraktikabel.

**Umzusetzen:**
- Breadcrumbs → einzelner großer „Zurück"-Button (min. 64px) oben; permanenter „Home"-Button zur Kiosk-Startseite. (R-017, R-018)
- Navigationstiefe max. 2 Ebenen; keine Hamburger-Menüs; alle Aktionen direkt sichtbar. (R-019, R-021)
- Dropdowns → große Kachel-Auswahl/Fullscreen-Listen (R-020).
- Formulare im Kiosk auf Pflichtfelder reduzieren, optionale in „Erweitert" (R-022); Texteingabe minimieren zugunsten Auswahllisten/QR (R-023).
- **Quick-Select-Kacheln** für EC/pH/Temperatur/Luftfeuchtigkeit (min. 48×48px, Abstand ≥12px) + immer „Manuell"-Option (R-024..026); große +/− Stepper (min. 56px) für Ganzzahlen (R-027).
- Swipe nie als einzige Interaktion — jede Swipe-Aktion hat Tap-Alternative (R-028).
- Fullscreen API im Kiosk (R-006 der §2.1 / Phase-3-Liste).

**Betroffene Dateien:**
- `src/frontend/src/components/kiosk/KioskBackButton.tsx`, `KioskQuickSelect.tsx`, `KioskStepper.tsx`
- Kiosk-Formular-Wrapper (Pflichtfeld-Reduktion)
- `KioskLayout.tsx` (Home/Zurück, Fullscreen-Handle)

**Akzeptanzkriterien:**
- „Zurück"- und „Home"-Button auf jeder Kiosk-Unterseite sichtbar (≥64px). (R-017, R-018)
- Navigationstiefe ≤2 Ebenen; keine Hamburger-Menüs. (R-019, R-021)
- Quick-Select-Kacheln (EC/pH/Temperatur) mit „Manuell"-Option vorhanden. (R-024..026)
- Keine Swipe-Aktion ohne Tap-Alternative. (R-028)

**Spezialist:** frontend-usability-optimizer  **Aufwand:** M-L  **Abhängigkeiten:** WP-K1, WP-K2

#### WP-K4 · Feedback, Audio, Bildschirmschoner & konfigurierbarer Timeout (Phase 4 — R-037, R-046..056)

**Problem:** Standard-Snackbars/Inline-Loader sind im Kiosk-Betrieb zu klein; kein Audio-Feedback, kein Bildschirmschoner, Timeout nicht konfigurierbar.

**Umzusetzen:**
- Erfolgs-/Fehler-Feedback als **großflächige Vollbild-Overlays** (Abweichung von UI-NFR-004 im Kiosk): Erfolg (Symbol ≥96px, ≥24px Text, Auto-Close 3s), Fehler (Symbol ≥96px, „Erneut versuchen"-Button ≥64px, **kein** Auto-Close). (R-046..049)
- Zentraler großer Spinner (≥64px) statt Inline-Loader (R-050); Button-Press-Feedback (Skalierung/Ripple ≥200ms, R-053).
- Optionale Audio-Signale (Erfolg/Fehler-Ton), in Settings umschaltbar (Default Kiosk=an, Normal=aus). (R-051, R-052)
- Bildschirmschoner/gedimmter Zustand nach Timeout-Reset mit Uhrzeit + wichtigstem Status; Touch beendet ihn. (R-054..056)
- Timeout-Wert konfigurierbar in Settings (60–600s). (R-037)
- Ungespeicherte Eingaben vor Timeout-Reset als Entwurf sichern oder warnen. (R-038)

**Betroffene Dateien:**
- `src/frontend/src/components/kiosk/KioskResultOverlay.tsx`, `KioskScreensaver.tsx`
- `src/frontend/src/kiosk/useKioskAudio.ts`
- Settings-Tab (Timeout-Slider, Audio-Toggle)
- `src/backend/app/domain/models/user_preference.py` (`kiosk_timeout_seconds`, `kiosk_audio_enabled`)

**Akzeptanzkriterien:**
- Erfolg/Fehler als Vollbild-Overlay; Fehler-Overlay schließt nicht automatisch, hat „Erneut versuchen"-Button. (R-046..049)
- Audio-Feedback in Settings aktivierbar/deaktivierbar (Default Kiosk=an). (R-051, R-052)
- Timeout in Settings 60–600s konfigurierbar. (R-037)
- Bildschirmschoner erscheint nach Timeout-Reset, Touch beendet ihn. (R-054..056)

**Spezialist:** fullstack-developer  **Aufwand:** M  **Abhängigkeiten:** WP-K1..K3

## Parallelisierungs-Strategie

- **WP-Performance ‖ WP-Kiosk** sind grundsätzlich unabhängig (Infra/CI vs. Feature) → zwei parallele Stränge, idealerweise je **eigener Worktree** (MEMORY: schreibende Agenten auf geteiltem Tree sequenziell; `isolation: worktree`).
- **Berührungspunkte (rein additiv):**
  - *Theme:* WP-K2 erweitert `theme.ts`/`ThemeContext.tsx` (High-Contrast). WP-Performance fasst Theme nicht an → kein Konflikt.
  - *Router:* WP-K1 fügt `/kiosk` in `AppRoutes.tsx` hinzu; WP-P1 kann dieselbe Datei für Lazy-Dashboard-Edit berühren → bei Parallelarbeit `AppRoutes.tsx`-Änderungen klein halten oder sequenzieren.
  - *userPreferences (FE-Slice + BE-Model):* nur WP-Kiosk berührt diese → keine Kollision mit WP-Performance.
- **Interne Reihenfolge WP-Kiosk:** WP-K2 (Theme/Touch) früh, da WP-K1-Startseite darauf aufsetzt; K1+K2 = MVP-Gate, K3/K4 danach.
- **Interne Reihenfolge WP-Performance:** WP-P1 zuerst (Build-Basis), dann WP-P2 (Lighthouse misst gegen stabilen Build); WP-P3/WP-P4 unabhängig parallel.
- Empfohlene Agenten-Aufteilung: `fullstack-developer` für WP-P1/P2 und WP-K1/K2/K4 (Provider, Theme, BE-Preference, CI); `frontend-usability-optimizer` für WP-P3/P4 (Skeleton-/Debounce-/Virtual-Scroll-Feinschliff) und WP-K3 (Navigation/Eingabe-UX).

## Definition of Done

- **Bundle & Build (UI-NFR-003):**
  - CI failt hart bei Initial-JS > 300 KB gzip (R-015) und bei Überschreitung des `/dashboard`-Chunk-Budgets (R-028).
  - `manualChunks`-Vendor-Splitting aktiv; Tree-Shaking bestätigt; Bundle-Analyzer-Report als Artifact. (R-013, R-016)
  - CSS-Budget < 50 KB gzip überwacht. (R-014)
  - Read-Only-`/dashboard` lädt keine Grid-/DnD-Layout-Engine im Initial-Bundle. (R-028, R-012)
- **Core Web Vitals / Lighthouse:** Lighthouse-CI-Report je PR; Ziele FCP<1.5s, LCP<2.5s, TTI<3.5s, CLS<0.1, INP<200ms; Performance-Score ≥90 (mobile, 4G-Emulation). (R-001..005)
- **Ladezustände:** kein seitenweiter async Vorgang ohne formtreuen Skeleton; kein FOUC; kein Layout-Shift beim Nachladen. (R-006..009)
- **Listen & Suche:** alle freien Sucheingaben debounced (300ms); lange Listen paginiert/virtualisiert; below-fold-Bilder lazy. (R-011, R-017, R-018)
- **Kiosk-Modus (UI-NFR-019):** MVP (Phase 1+2) vollständig — `/kiosk` + Settings-Toggle, persistente Präferenz, Kiosk-Badge, 4 Quick-Action-Kacheln + Status, Auto-Timeout, High-Contrast-Theme default, Touch-Targets ≥64/72px, `size:'large'`. Phase 3+4 gemäß Akzeptanzkriterien der WPs.
- **a11y WCAG AA** (Kiosk-Theme AAA/7:1): axe-core-Checks grün für neue Kiosk-Views; Touch-Target-Messungen bestehen. Standard-App bleibt WCAG AA.
- **Mobile-First:** alle neuen Kiosk-Views primär für Tablet/Touch (10"/7") entworfen; responsive geprüft.
- **Tests:** vitest-Unit/Component-Tests für `KioskProvider`, `useKioskTimeout`, Theme-Selektion, Bundle-Budget-Skript; E2E-Kiosk-Workflow (Startseite → Aktion → Bestätigung → Startseite). Coverage bleibt über den 4 Gates (MEMORY: neue Page-Tests inkl. transitiver Kind-Module).
- **Qualität:** ruff/eslint/tsc clean; `static`-Check grün; keine neuen required-Gate-Regressionen.
- **Doku:** DE-kanonisch/EN-Mirror für Kiosk-Modus + Performance-Budgets gemäß `spec/style-guides/DOCS.md`; REQ/UI-NFR-IDs sichtbar.

## Hinweise

- **UI-NFR-015 (Home-Assistant-Lovelace-Karten) ist hier explizit AUSGESCHLOSSEN.** Diese Anforderung gehört in das separate Repository `kamerplanter-ha` (HACS-Custom-Integration + Lovelace Cards) und wird über die HA-Spec-Dokumente + `ha-integration-developer`/`deploy-ha` bearbeitet, nicht in diesem Frontend-Plan.
- **Verankerte Repo-Realität (MEMORY):** Einziger *required* CI-Check ist `static`; Coverage-Job ist bekannter wandernder Flake (non-required). Neue CI-Gates (Bundle-Budget, Lighthouse) zunächst als eigene Jobs einführen, Required-Status separat/vorsichtig setzen, um Automerge nicht zu deadlocken.
- **v8-Coverage-Falle:** Neue Kiosk-Pages senken die Branch-Quote, wenn transitive Kind-Module nicht mitgetestet werden → Page **plus** Kinder testen (Expand-Ansatz, PR #435-Muster).
- **Light-Modus:** Im anonymen Light-Modus existiert kein Backend-Tenant/keine Server-Preference → Kiosk-Persistenz muss auf LocalStorage zurückfallen (analog `ThemeContext` `STORAGE_KEY`).
- **guard-nested-worktree:** Bei Worktree-Parallelisierung Commits nicht aus `.claude/worktrees/` erzeugen (pre-commit-Hook blockt); zentraler Worktree-Root nutzen (CLAUDE.md).
- **Custom-Hook-Stabilität (R-023):** Neue Kiosk-Hooks (`useKioskTimeout`, `useKioskAudio`), die Objekte/Arrays zurückgeben, MÜSSEN `useMemo`-stabilisiert sein (Projekt-Konvention).
- **Pre-Merge-Review-Kette (MEMORY-Pflicht):** Nach Implementierung 3-Agent-Kette (UI-Review → Tests → Doku) und Merge-Review vor Automerge.
