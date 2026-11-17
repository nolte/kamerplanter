# Frontend-Audit — Kamerplanter Web-App (November 2026)

**Datum:** 2026-11-17
**Code-Stand:** `develop` @ `fe1dd196e` (Branch `chore/frontend-audit`)
**Vorgänger:** [`frontend-ui-audit-2026-04.md`](frontend-ui-audit-2026-04.md), [`frontend-ui-audit-dialogs-2026-04.md`](frontend-ui-audit-dialogs-2026-04.md) (beide 2026-04-25, rein statisch)
**Anforderung:** [`project/requirements/frontend-audit-2026-11.md`](../../project/requirements/frontend-audit-2026-11.md)
**Stack (gemessen):** React 19.2, **MUI 9**, TypeScript 6 strict, Vite 8, Redux Toolkit, react-router v7, react-i18next
**Umfang:** `src/frontend/src`: 1.008 Produktionsmodule, 764 Testdateien, 187 E2E-Dateien (`tests/e2e`)

---

## Zusammenfassung

Seit April hat sich das Frontend deutlich verbessert. Von den 29 April-Befunden sind 12 behoben und 9 teilweise behoben, 4 waren obsolet und 5 sind offen (siehe [Delta](#delta-zum-april-audit)). `maxWidth: 900` ist verschwunden. `OriginChip`, `HelpTooltip`, URL-Persistenz und `PageTitle`-`meta` existieren jetzt. Die Dialog-Barrierefreiheit des April-Korpus ist vollständig nachgezogen. Mehrere Bereiche sind solide: Routen werden per `lazy()` geladen, der Token liegt nur im Speicher, der Refresh-Token in einem HttpOnly-Cookie. Die DE/EN-Strukturparität ist praktisch 1:1, und kein Page Object verweist auf eine nicht mehr existierende testid.

Die heutigen Defizite liegen tiefer als im April. Es geht nicht mehr um Layout-Konstanten, sondern um **Querschnittsverträge**:

1. **Fehlerpfad (Kap. M1):** Etwa 60 Stellen verschlucken Ladefehler und zeigen sie als „leer" an. Betroffen sind auch Sitzungen, Mitglieder und Einladungen. Englischer Server-Rohtext landet in der deutschen UI, weil `parseApiError` gegen FRONTEND.md §10.3 `error.message` zurückgibt.
2. **Datenvollständigkeit und Konsistenz (M3–M5):** Rund 18 Detailseiten haben keinen Stale-Response-Schutz. 25 Stellen schneiden Listen bei 200 Einträgen still ab. Der Client rechnet Domänengrößen nach, etwa die aktive Düngewoche, und kommt dabei zu anderen Ergebnissen als der Server.
3. **Bedienbarkeit (M6, M9, M10):** Die DataTable-Zeilen sind per Tastatur nur halb bedienbar. Mobil fehlt die Bottom-Navigation (UI-NFR-005 R-010 MUSS). 43 Formular-Dialoge verwerfen Eingaben ohne Nachfrage.
4. **Ein Sicherheitsbefund (M2):** Ein KI-generierter `action_url` der Form `/\evil.com` passiert sowohl den Backend- als auch den Frontend-Validator und wird als `href` gerendert (Open Redirect).
5. **Bundle-Budget (M11):** Das initiale JS liegt bei **394,3 von 400 KB gzip (99 %)**. Im Juli waren es 343 KB.

Die Befunde sind zu 21 Maßnahmenbündeln (M1–M21) verdichtet. Triviale Befunde sind im Branch behoben (siehe [Mini-Fixes](#im-branch-behobene-mini-fixes)). Für Bündel ab Schweregrad medium gibt es GitHub-Issues (siehe [Issues](#angelegte-issues)).

---

## Methodik

Das Audit lief nach **Dimensionen statt nach Seiten**, damit Querschnittsbefunde nicht 29-mal gemeldet werden. Jede Dimension hatte einen eigenen Spezialisten mit eigenem Maßstab. Alle Agenten haben nur gelesen und parallel gearbeitet.

| # | Dimension | Werkzeug | Maßstab | Befund-Präfix |
|---|---|---|---|---|
| 1 | Code-Qualität | `frontend-code-reviewer` ×2 (Slice A `pages/`, Slice B Rest) | FRONTEND.md, F1–F11 + D1–D11, **[VRBP]** Vercel React Best Practices | A-, B- |
| 2 | UI-NFR-Konformität | Analyse-Agent | UI-NFR-001..022 (MUSS-Regeln), **[FD]** frontend-design | N- |
| 3 | Barrierefreiheit | `webview-ui-expert` (statisch) + Live-Pass | WCAG 2.2 AA, UI-NFR-002, **[WDG]** Web Interface Guidelines | W-, L- |
| 4 | i18n | `i18n-completeness-checker` + eigener Key-Diff (Skript) | UI-NFR-007, FRONTEND.md i18n | I- |
| 5 | Performance/Bundle | lokaler `vite build` + `bundle:check`, statisch, Lighthouse | UI-NFR-003, `bundle-budget.json` | P-, W- |
| 6 | Testbarkeit/Testgesundheit | Analyse-Agent (Skripte für testid/Coverage/E2E-Abgleich) | UI-NFR-022, FRONTEND.md §13 | T- |
| 7 | Live-Visual-Audit | Playwright gegen Dev-Cluster (kind, Port-Forward `:3000`) | Mobile 375 / Tablet 820 / Desktop 1440, Light/Dark, axe-core, Lighthouse | L- |

**Zusatzmaßstäbe** (Tags `[VRBP]`, `[FD]`, `[WDG]`): die Skills `vercel-react-best-practices`, `frontend-design` und `web-design-guidelines`. Bei einem Konflikt gelten FRONTEND.md und die UI-NFRs. Next.js- und Server-Regeln aus VRBP sind auf diese Vite-SPA nicht anwendbar und wurden übersprungen.

**Gegenprüfung:** Agenten-Befunde wurden nicht ungeprüft übernommen. Je Dimension wurden Stichproben am Code verifiziert. Dabei wurden zwei Abweichungen korrigiert:

- Der i18n-Agent meldete 0 undefinierte Keys. Der skriptbasierte Diff fand 13 (I-01).
- Der Open Redirect wurde zusätzlich im Backend-Validator nachgewiesen (M2).

**Schweregrad-Kalibrierung:** Die Skala der Vorgänger-Audits gilt weiter: critical, high, medium, low. Nur Datenverlust oder Sicherheitsbruch gilt als critical. Vier Agenten-„critical" (A-01, A-02, B-01: stille Fehler) wurden auf **high** gestuft. N-06 (Brand-Assets) wurde auf medium gestuft. B-08 wurde nach dem Backend-Nachweis auf **high** angehoben.

**Einschränkungen:**

- Der Live-Pass lief gegen die Dev-Instanz. Die liefert der Vite-Dev-Server über `kubectl port-forward` aus, nicht nginx. Header-Befunde (CSP, Cache-Control, W-20..W-25) sind deshalb nur statisch gegen `nginx.conf` und `nginx-security-headers.inc` belegt, und Lighthouse-Performance-Werte sind nur indikativ.
- Der Bundle-Build lief mit Node 26.13.0, weil die in `.tool-versions` geforderte 26.13.1 lokal nicht installiert ist.
- Coverage-Zahlen sind Obergrenzen: Ein Modul gilt nur dann als „getestet", wenn eine Testdatei es direkt importiert.

---

## Ergebnis je Dimension (Ampel)

| Bereich | Ampel | Kern |
|---|---|---|
| Code-Qualität F1–F11 | gelb | stille Fehlerpfade, Stale-Responses, Client-Joins, God-Komponenten (GardenPlanEditor 2.718 Z., PlantInstanceDetailPage 2.919 Z.) |
| UI-NFR-001 Responsive | gelb | 140/224 IconButtons `size="small"` (<48 px), Breakpoint-Widerspruch in der Spec |
| UI-NFR-002 Barrierefreiheit | gelb | DataTable-Zeilen, kein Fokus bei Routenwechsel, kein Fokusring-Override |
| UI-NFR-003 Performance | gelb | Budget 99 % ausgeschöpft, SVG-Illustrationen bis 690 KB, Bilder ohne lazy |
| UI-NFR-004 Feedback | gelb | Snackbars ohne Schließen, kein Retry, 500 ohne Referenz-ID |
| UI-NFR-005 Navigation | **rot** | keine Bottom-Navigation, ~11 Routen ohne Breadcrumb, 76 Navigationen ohne `<a>` |
| UI-NFR-006 Design-System | gelb | 217 Farbliterale außerhalb `theme/`, Roboto nicht geladen |
| UI-NFR-007 i18n | gelb | 13 undefinierte Keys (roh sichtbar), kein Paritäts-Guard |
| UI-NFR-008 Formulare | **rot** | kein `onBlur`, 43 Dialoge ohne Dirty-Guard, 422 nicht am Feld, kein Hilfe-Slot |
| UI-NFR-009 Visual Identity | **rot** | kein Logo, kein Favicon, kein Icon-Set |
| UI-NFR-010 Tabellen | gelb | 23 DataTables ohne Spaltenpriorität, 20 eigene `<Table>` |
| UI-NFR-011 Fachbegriffe | **rot** | ~19/38 Pflicht-Glossarbegriffe fehlen, 26 Fachbegriff-Felder ohne Tooltip |
| UI-NFR-012 PWA/Offline | gelb | in Umsetzung (Welle 9), Offline-Sperren fehlen außerhalb Gartenplan |
| UI-NFR-013 Consent | gelb | `external_services` fehlt, kein Server-Abgleich |
| UI-NFR-014 Auth-Init | grün | — |
| UI-NFR-015 HA Lovelace | n/a | nicht Teil von `src/frontend` |
| UI-NFR-016 Phasen-Visualisierung | gelb | Phasenpalette 7× mit 4 Farbsätzen |
| UI-NFR-017 Seitenlayout | gelb | doppeltes h1 auf Fehlerseiten, Pattern C ungenutzt |
| UI-NFR-018 Herkunft | gelb | Treatment-Detail ohne Chip, kein Herkunftsfilter bei Workflow-Templates |
| UI-NFR-019 Kiosk | gelb | Kacheln führen in die Normal-UI, Timeout greift dort nicht |
| UI-NFR-020 Anbau-Zeitachse | grün | — |
| UI-NFR-021 Aktionsgruppen | gelb | `PageHeaderActions` nur 10/73 Nutzer |
| UI-NFR-022 Testbarkeit | gelb | DataTable-Zeilen ungeschlüsselt, ~520 Bedienelemente ohne testid |
| Testgesundheit | gelb | 0 skip/only, aber API-Mocks statt MSW, testid:role ≈ 4:1, 323 Module ohne direkten Test |

---

## Maßnahmenbündel (priorisiert)

Jedes Bündel fasst deduplizierte Befunde zusammen. Die Belege stehen in den Detailtabellen unten. „Issue" heißt: Für das Bündel wird ein GitHub-Issue angelegt (ab medium, R8).

| Prio | Bündel | Schwere | Befunde | Kern-Belege |
|---|---|---|---|---|
| 1 | **M2 Open Redirect `action_url`** | high | B-08 | `components/ai/TipCardsPanel.tsx:36-38,201-203`; Backend `src/backend/app/domain/models/ai_assistant.py:187` |
| 2 | **M1 Fehlerpfad-Vertrag** (stille Fehler, roher EN-Text, §10.3) | high | A-01, A-02, A-03, B-01, B-02, B-27, N-10, N-11, B-14 | `api/errors.ts:32-45`, `components/common/ErrorDisplay.tsx:6-30`, `pages/auth/AccountSettingsPage.tsx:385`, `pages/tenants/TenantSettingsPage.tsx:108-120`, `features/gardenPlanner/bed/useSiteThresholds.ts:55` |
| 3 | **M3 Stale-Response/Abbruch** | high | A-04, A-14, B-15 | `pages/standorte/LocationDetailPage.tsx:324`, `pages/stammdaten/CropRotationPage.tsx:132-147`, `routes/AppRoutes.tsx:153` |
| 4 | **M4 Datenvollständigkeit und Fan-out** | high | A-05, A-06, A-11, B-06, B-18 | `pages/aufgaben/TaskQueuePage.tsx:340`, `pages/pflanzen/PlantInstanceListPage.tsx:69-130`, `features/gardenPlanner/history/historyApi.ts:107-137` |
| 5 | **M5 Domänen-Duplikate im Client** (aktive Woche, UTC-„heute") | high | B-03, A-09 | `hooks/useRunNutrientData.ts:132-245` vs. `src/backend/app/api/v1/planting_runs/tenant_router.py:547-586`; `pages/pflanzen/PlantInstanceCreateDialog.tsx:203` |
| 6 | **M6 Tastatur- und Screenreader-Bedienung** | high | W-01/B-12/L-06, A-07, A-08, W-02/L-08, W-06, W-07, W-08/L-07, L-04, L-09, L-10, L-11, N-18, N-21 | `components/common/DataTable.tsx:390-395,481-488`, `pages/kalender/CalendarPage.tsx:95-107,1071`, `pages/duengung/PhaseDetailGantt.tsx:545-561`, `pages/duengung/nutrient-plan-detail/PlanEditTab.tsx:327-344` |
| 7 | **M9 Mobile Navigation** | high | N-01, N-13, N-16, N-19 | `layouts/MainLayout.tsx:147`, `routes/breadcrumbs.ts` |
| 8 | **M10 Formular-Verhalten** | high | N-07, N-08, N-09, N-14 | 43 Dialoge ohne Dirty-Guard (z. B. `pages/standorte/SiteCreateDialog.tsx:127`), `pages/durchlaeufe/ActivityPlanTab.tsx:441` |
| 9 | **M8 Fachbegriffe/Hilfe** | high | N-03, N-04, N-05, N-30, F-003, D-008 | `i18n/locales/de/glossary.json`, `components/form/FormTextField.tsx`, `components/common/HelpTooltip.tsx:183-190` |
| 10 | **M7 Farb- und Design-Tokens** | high | A-12, B-09, N-02, N-24, N-25, N-26, W-19 | 7 Phasenfarb-Maps (siehe A-12), `theme/ThemeContext.tsx:39-45` |
| 11 | **M21 Hook-Korrektheit** | high | B-04, B-16, B-11, B-17, B-19, B-20 | `hooks/useServerFavorites.ts:52-71`, `hooks/useCountdownTimer.ts:23-45` |
| 12 | **M11 Bundle und Assets** | high | P-01, P-02, N-23, W-26/B-07, W-30 | `bundle-budget.json` (394,3/400 KB), `src/assets/illustrations/errors/*.svg` |
| 13 | **M12 Testbarkeit (UI-NFR-022)** | high | T-01..T-08, F-018 | `components/common/DataTable.tsx:406,499` |
| 14 | **M14 i18n- und Locale-Hygiene** | medium | I-01..I-05, L-01..L-03, A-13, A-16, A-21, B-10 | siehe [i18n](#dimension-4--i18n) |
| 15 | **M13 Testgesundheit** | medium | T-11..T-17, A-25..A-27, B-13, B-14 | `test/api/endpoints/*` (49/50 mocken axios) |
| 16 | **M15 God-Komponenten** | medium | A-10, B-05 | `features/gardenPlanner/editor/GardenPlanEditor.tsx:378`, `pages/pflanzen/PlantInstanceDetailPage.tsx` |
| 17 | **M20 Seitenkopf und Layout** | medium | F-004, N-33, N-34, N-36, D-002-Regression | `pages/duengung/NutrientPlanDetailPage.tsx:61-82`, `components/layout/PageHeaderActions.tsx:136-147` |
| 18 | **M16 Kiosk** | medium | N-37, N-38, W-07, W-09 | `pages/kiosk/KioskStartPage.tsx:43-64` |
| 19 | **M17 Security-Header (nginx)** | medium | W-20..W-25, W-23 | `nginx-security-headers.inc:17-20`, `nginx.conf:63-66,123-127` |
| 20 | **M19 Consent/PWA-Rest** | medium | N-39, N-40, W-33/L-15, L-14, L-16 | `components/privacy/ConsentBanner.tsx:31-38`, `public/manifest.json` |
| 21 | **M18 Visual Identity** | medium | N-06, N-44, N-45 | `assets/brand/`, `index.html` |

Reihenfolge-Logik:

1. M2 kommt zuerst: Es ist ein Sicherheitsbefund mit kleinem Fix.
2. M1 ist Voraussetzung für viele Slice-Fixes, weil `parseApiError(err, t)` an jeder Fehlerstelle die Signatur ändert.
3. M3, M4 und M5 betreffen die Korrektheit angezeigter Daten.
4. M6, M9 und M10 sind MUSS-Lücken in der Bedienbarkeit.
5. M11 gehört nach vorne, bevor der nächste Feature-PR das Bundle-Budget reißt.

---

## Detailbefunde

Pfade sind relativ zu `src/frontend/src/`, sofern nicht anders angegeben. Mini-Fix = trivial und verhaltensneutral. Was im Branch behoben ist, steht mit Fundstelle unter [Mini-Fixes](#im-branch-behobene-mini-fixes).

### Dimension 1a — Code-Qualität `pages/` (A-)

| ID | Schwere | Regel | Beleg | Befund |
|---|---|---|---|---|
| A-01 | high | F2 | `pages/auth/AccountSettingsPage.tsx:385`; `pages/tenants/TenantSettingsPage.tsx:108-110,118-120`; `pages/admin/AdminEditTenantPage.tsx:181`→`:199` | Ladefehler bei Sitzungen, Mitgliedern und Einladungen werden als „leer" angezeigt. Eine fremde Sitzung oder ein offener Einladungslink ist dann weder sichtbar noch widerrufbar. |
| A-02 | high | F2 | 30× `.catch(() => {})`, 27× leeres `catch {}`; z. B. `pages/pflanzen/PhaseTransitionDialog.tsx:68,72`, `pages/standorte/SiteListPage.tsx:400`, `pages/pflanzen/PlantInstanceListPage.tsx:80,96`, `pages/standorte/LocationDetailPage.tsx:271-280` | Fehlschläge erscheinen als leerer Zustand. Ohne Zielphasen ist ein Phasenwechsel kommentarlos unmöglich. |
| A-03 | high | FRONTEND §10.3 | 19× `setError(String(err))`, 25× `parseApiError()` (gibt `error.message` zurück, `api/errors.ts:32-34`); `components/common/ErrorDisplay.tsx:30` | Roher englischer Exception-/Servertext erscheint in der deutschen UI. 13 Dateien rufen `useSnackbar` statt `useNotification` auf. |
| A-04 | high | F2 | ~18 Detailseiten; `pages/standorte/TankDetailPage.tsx:236-309`, `pages/standorte/LocationDetailPage.tsx:324`, `pages/stammdaten/CropRotationPage.tsx:132-147`, `pages/pflanzen/PlantInstanceDetailPage.tsx:330-374` | Kein Abbruch- und kein Ignore-Guard beim Wechsel des Keys. Eine späte Antwort überschreibt die aktuelle Ansicht. In CropRotation hängt das Skeleton dann dauerhaft. |
| A-05 | high | F1 Kl. 3 / F6 | `pages/pflanzen/PlantInstanceListPage.tsx:69-130`; `pages/standorte/LocationDetailPage.tsx:256-258,288-304`; `pages/aufgaben/WorkflowInstantiateDialog.tsx:183,209`; `pages/durchlaeufe/PlantingRunDetailPage.tsx:200,224` | Client-Joins mit Fan-out pro Element (bis zu 200 Runs × `listRunPlants`). Gehört als Filter bzw. Projektion ins Backend. |
| A-06 | high | F4/D4 | 25 Stellen; `pages/aufgaben/TaskQueuePage.tsx:340`, `pages/aufgaben/TaskCreateDialog.tsx:133`, `pages/durchlaeufe/AdoptPlantsDialog.tsx:62`, `pages/ueberwinterung/OverwinteringListPage.tsx:112`, `pages/standorte/SiteRunsSection.tsx:45` | Es wird nur eine Seite à 200 geladen, alles darüber wird still abgeschnitten. Die Klasse entspricht #1560, liegt aber außerhalb von `useCatalogue`. Den Paginator `listAllPlantInstances` gibt es bereits. |
| A-07 | high | F8 / WCAG 2.1.1 | `pages/duengung/PhaseDetailGantt.tsx:545-561,656,769,1033`; `pages/aufgaben/WorkflowDetailPage.tsx:1276-1289`; `pages/pflege/components/CareConfirmDialog.tsx:211-218` | `Box onClick` ohne `role`, `tabIndex` und Tastaturhandler. Die Inline-Bearbeitung von EC/pH ist per Tastatur nicht erreichbar. |
| A-08 | high | F8 / FRONTEND §7.2 | `pages/duengung/nutrient-plan-detail/PlanEditTab.tsx:327-344` | Rohes `<input type="time">` ohne zugänglichen Namen, mit Inline-Farben (`1px solid red`), die im Dark Mode brechen. |
| A-09 | medium | F10 | 9× `new Date().toISOString().split('T')[0]` in `pages/`, z. B. `pages/pflanzen/PlantInstanceCreateDialog.tsx:203,241`, `pages/durchlaeufe/PlantingRunCreateDialog.tsx:261,280`, `pages/standorte/BatchCreateDialog.tsx:50,59` | „Heute" wird in UTC berechnet. Zwischen 00:00 und 02:00 MESZ wird deshalb der Vortag als `planted_on` vorbelegt und gespeichert. |
| A-10 | medium | F3 | `pages/pflanzen/PlantInstanceDetailPage.tsx` (2.919 Z., 45 `useState`), `pages/auth/AccountSettingsPage.tsx` (2.233, 51), `TaskQueuePage` (1.805), `WorkflowDetailPage` (1.628), `CalendarPage` (1.554), `TaskDetailPage` (1.537), `TankDetailPage` (1.461) | God-Komponenten. Als Vorbild für die Zerlegung dient `pages/duengung/nutrient-plan-detail/useNutrientPlanData.ts`. |
| A-11 | medium | [VRBP] async-parallel | `pages/pflanzen/PlantInstanceDetailPage.tsx:303-379` (`getSlot` doppelt, :338/:357); `pages/standorte/TankDetailPage.tsx:263-290`; `pages/standorte/LocationDetailPage.tsx:238-304` | Unabhängige Requests laufen seriell. |
| A-12 | medium | F4/F7, UI-NFR-016 | `pages/duengung/PhaseGanttChart.tsx:25`, `pages/duengung/FertilizerUsageGantt.tsx:17`, `pages/durchlaeufe/WateringCalendarView.tsx:40`, `pages/durchlaeufe/PhaseKamiTimeline.tsx:68`, `pages/kalender/SowingCalendarView.tsx:63`, `pages/kalender/PhaseTimelineView.tsx:18`, `features/gardenPlanner/planting/phaseColors.ts:11-35` | Die Phasenfarb-Map ist 7× deklariert, mit 4 widersprüchlichen Paletten. `germination` hat dabei vier verschiedene Werte. |
| A-13 | medium | F10 | ~50× `toLocale*String()` ohne Locale, 29× `toFixed()` vor einer Einheit (davon 11 in `pages/duengung/NutrientCalculationsPage.tsx`) | Die Formatierung umgeht `utils/formatting.ts`, deshalb erscheint im Deutschen ein Dezimalpunkt. |
| A-14 | medium | Tooling | 43× `eslint-disable react-hooks/*` in 37 Dateien, z. B. `pages/stammdaten/CropRotationPage.tsx:147` | Die Unterdrückungen verdecken überwiegend A-04. |
| A-15 | medium | F1 Kl. 1 | `pages/auth/PrivacySettingsPage.tsx:129-240` | `client.get`/`client.post` direkt in der Komponente, obwohl `api/endpoints/privacy.ts` existiert. |
| A-16 | medium | F4 | 34× in 16 Dateien `i18n.language === 'de' && x.name_de ? …` | Ad-hoc-Lokalisierung von Namen trotz `utils/plantDisplay.ts`. |
| A-17 | low | F3 | `pages/standorte/SubstrateMixDialog.tsx:200`, `pages/pflege/components/CareConfirmDialog.tsx:275`, `pages/duengung/NutrientCalcFertilizerFields.tsx:325` | Index-Keys auf editierbaren Zeilen. |
| A-18 | low | [VRBP] rerender-no-inline-components | `pages/pflanzen/PlantInstanceDetailPage.tsx:1036` | `TaskStatusIcon` wird im Render definiert. |
| A-19 | low | F10 | `pages/pflanzen/PlantInstanceCreateDialog.tsx:240` („(Kopie)"), „Platform"-Chips (siehe I-03) | Hartkodierter Text. |
| A-20 | low | F8 | `pages/durchlaeufe/WateringCalendarView.tsx:319` | Der Button „Vormonat" hat das `aria-label` „Zurück". |
| A-21 | low | F10 | ~20× `localeCompare` ohne Locale | Sortiert nach der Laufzeit-Locale statt nach der App-Sprache. |
| A-22 | low | F5 | `pages/pflanzen/diary/DiaryPhotoUploadDialog.tsx:89`, `pages/auth/HaPublishSettingsTab.tsx:246,262` | `setTimeout` ohne Cleanup. |
| A-23 | low | F9 | `pages/stammdaten/ReferenceImageCuration.tsx:131` | `href={image.source_url}` ohne Schema-Allowlist. React 19 blockiert `javascript:`, das Restrisiko ist gering. |
| A-24 | low | F9 | `pages/auth/EmailChangeCard.tsx:34-51` | Die ausstehende E-Mail-Adresse liegt in `sessionStorage`. |
| A-25..A-27 | low–medium | F11 | `test/pages/DiaryOverviewPage.test.tsx:686`, `PlantInstanceDetailPageCareTab.test.tsx:22-32`, `SuccessionPlanDialog.test.tsx:50-315` | Feste Sleeps mit nur negativen Assertions, eigene Seitenkomponenten → `null` gemockt, `getByTestId().querySelector('input')`. |

### Dimension 1b — Code-Qualität `components/`, `features/`, Hooks, Store, API (B-)

| ID | Schwere | Regel | Beleg | Befund |
|---|---|---|---|---|
| B-01 | high | F2 | 9× `.catch(() => undefined)` in `features/gardenPlanner`: `bed/useSiteThresholds.ts:55`, `bed/useLocationTypeNames.ts:19`, `history/BedHistoryTab.tsx:72`, `history/CareHistoryPage.tsx:40`, `history/historyApi.ts:135`, `care/CareFormFields.tsx:88`, `bed/SoilProfileForm.tsx:98`, `planting/PlantingDialog.tsx:239`, `history/usePersonOptions.ts:28` | Bei einem Ladefehler gilt ein Indoor-Standort als Garten (Frost/Wetter erscheinen, Raster 10 statt 5 cm), und Beete verschwinden still. Das vorhandene Muster `useAsyncOptions` wird nicht genutzt. |
| B-02 | high | FRONTEND §10.3 | `api/errors.ts:32-45`; `hooks/useApiError.ts:94,124,148,196`; ~25 Slices `state.error = action.error.message ?? 'errors.…'` (z. B. `store/createListSlice.ts:195`, `store/slices/sitesSlice.ts:131`); EN-Literale `store/slices/pestDetectionSlice.ts:187`, `identificationSlice.ts:166`, `importSlice.ts:149` | Ursache von A-03. Der i18n-Fallback in den Slices ist toter Code, weil `message` immer gesetzt ist. Es gibt zwei Regex-Denylists (useApiError:196, ErrorDisplay:6). |
| B-03 | high | F4 | `hooks/useRunNutrientData.ts:132-245` vs. `src/backend/app/api/v1/planting_runs/tenant_router.py:547-586` | Der Client rechnet die aktive Woche lokal (`setHours(0,0,0,0)`), der Server autoritativ in UTC. Ein Durchlauf kann damit andere Dosierungen anzeigen, als der Server anwendet. Eine dritte Kopie steckt in PlantInstanceDetailPage. |
| B-04 | high | F5 | `hooks/useServerFavorites.ts:52-71`; `hooks/useCountdownTimer.ts:23-45` | API-Aufrufe und `new AudioContext()` stecken in `setState`-Updatern. Unter StrictMode bzw. Concurrent Rendering kann das zu Doppel-POSTs führen, und das Rollback entfernt dann echte Favoriten. Der AudioContext wird nie mit `close()` geschlossen. |
| B-05 | high | F3 | `features/gardenPlanner/editor/GardenPlanEditor.tsx:378` (2.718 Z., 136 Hooks), `editor/PropertiesPanel.tsx` (1.017), `io/ExportDialog.tsx` (843) | God-Komponente. Herauslösbar sind die Layer-Hooks für Companion, Plant-State und Zone. |
| B-06 | high | F6 / F1 Kl. 3 | `features/gardenPlanner/history/historyApi.ts:128-137` (bis 50 Standort-Seiten × `listBeds`), `:107-110` (`limit: 200` ohne Paging) | Backend-Arbeit im Client, Pflanzenoptionen ab Nr. 201 fehlen still. |
| B-07 | medium | [VRBP] client-swr-dedup | `auth/AuthProvider.tsx:170-177` vs. `:196-206` | Doppelter Bootstrap: `/auth/me`, Tenants, Preferences und Modul-Migration laufen bei jedem Start zweimal (= W-26). |
| B-08 | **high** | F9 | `components/ai/TipCardsPanel.tsx:36-38` → `<Button href>` `:201-203`; Backend `src/backend/app/domain/models/ai_assistant.py:187` | `isSiteRelative` und der Backend-Validator prüfen nur `startsWith('/')` und `!startsWith('//')`. `/\evil.com` passiert beide Prüfungen. Der Browser normalisiert `\` zu `/`, das Ergebnis ist ein protokoll-relativer externer Link. Die Quelle ist eine LLM-Ausgabe, die sich per Prompt-Injection steuern lässt. `toSafeSameOriginPath` (`pwa/pushHandlers.ts:121`) existiert bereits. |
| B-09 | medium | F7 | `features/gardenPlanner/planting/phaseColors.ts:38` (Farbe aus dem **Namen**), `components/sensors/SensorHistoryChart.tsx:52-63,111` | Ergänzt A-12. Ein übersetzter Phasenname fällt auf die Hash-Farbe zurück. |
| B-10 | medium | F10 | `components/layout/NotificationDrawer.tsx:82-89` (`.replace('{{count}}')`, kein Plural), `components/dashboard/SeasonOverviewPanel.tsx:99` (en-GB vs. en-US), `components/admin/PlanFormDialog.tsx:121`, `components/tanks/TankStateChart.tsx:71`, `features/gardenPlanner/io/ExportDialog.tsx:130` | Locale und Plural laufen an i18next und `utils/formatting.ts` vorbei. |
| B-11 | medium | FRONTEND §6.1/§6.2 | `hooks/useWateringVolumeSuggestion.ts:9,39,43` | Hinweis aus rohem Enum gebaut, Rückgabeobjekt ohne `useMemo`, kein Rückgabetyp, Fehler wird zu „kein Vorschlag". |
| B-12 | medium | F8 | = W-01 | — |
| B-13 | medium | F11 | gardenPlanner-Tests: 2.863 `*ByTestId` vs. 522 `ByRole`/`ByLabelText` | = T-12 |
| B-14 | medium | F11 | `features/gardenPlanner/care/BedCareTab.test.tsx:295-305`; 29 Echtzeit-Sleeps (z. B. `io/ExportDialog.test.tsx:249`) | Fehlerpfad-Tests prüfen nur Negative. Kein Test prüft den Text von `ErrorDisplay` (hätte B-02 aufgedeckt). |
| B-15 | medium | F2 | `routes/AppRoutes.tsx:153` | Nur ein Root-`errorElement`. Ein Renderfehler einer Seite zerstört die ganze Shell samt Navigation. |
| B-16 | medium | F2 | `hooks/useServerFavorites.ts:28-36,57-68` | Rollback ohne Hinweis. Die `loaded`-Ref wird bei einem Nutzerwechsel nicht zurückgesetzt. |
| B-17 | medium | [VRBP] advanced-use-latest | `auth/AuthProvider.tsx:42-58,106-113` | Der Token wird über eine per Effect synchronisierte Ref gelesen. Ein doppelter `/auth/refresh` ist möglich (Rate-Limit #1131). |
| B-18 | medium | F6 | `features/gardenPlanner/planting/phaseColors.ts:87-98`, `templates/useTemplateTaskNames.ts:34`, `care/BatchCompleteDialog.tsx:91,126` | Ein Request pro Element, das Undo läuft pro Task. |
| B-19 | low | FRONTEND §6.2 | 26 Hooks ohne Rückgabetyp, z. B. `hooks/usePagination.ts:9` | — |
| B-20 | low | FRONTEND §6.1 | `hooks/useTabUrl.ts:39` | Tupel ohne `useMemo`. |
| B-21/B-22 | low | F8/F10 | = W-04, W-12 | — |
| B-23 | low | [VRBP] client-localstorage-schema | ~20 Module, 4 Key-Konventionen; `layouts/MainLayout.tsx:75` ohne try/catch | — |
| B-24 | low | D4 | `hooks/useTenantPermissions.ts:65-67` | Rollenliste fest kodiert statt `ROLE_RANK`. |
| B-25/B-26/B-27 | low | F6/F11/F1 | `api/client.ts:99-110` (50-ms-Polling), `features/gardenPlanner/renderer/SvgPlanRenderer.test.tsx:50,70` (innerHTML-Snapshot), `store/slices/pestDetectionSlice.ts:59` (Übersetzung im Thunk) | — |

**Positiv:** Die TS-Ports (`features/gardenPlanner/model/*.ts`) sind über `*.vectors.test.ts` gegen gemeinsame Backend-Vektoren abgesichert. B-03 entstand genau dort, wo es so einen Vertrag nicht gibt.

### Dimension 2 — UI-NFR-Konformität (N-)

| ID | Schwere | Regel | Beleg | Befund |
|---|---|---|---|---|
| N-01 | high | 005 R-010 (MUSS), R-023..R-031 | `layouts/MainLayout.tsx:147`; `BottomNavigation` 0 Treffer | Mobil fehlt die Bottom-Navigation. Der einzige Weg führt über Hamburger und temporären Drawer. |
| N-02 | high | 016 R-006/R-008 | = A-12 | — |
| N-03 | high | 011 §3.3 | `i18n/locales/de/glossary.json` (43 Einträge) | ~19 der 38 Pflichtbegriffe fehlen (rH, DIF, Hysterese, Flushing, Runoff, Mixing Priority, CEC, Staunässe, Cultivar vs. Varietät, Pflanzdurchlauf …). |
| N-04 | high | 011 §2.2, 008 R-046 | 26 Feldlabels, z. B. `pages/standorte/WateringEventCreateDialog.tsx:213`, `pages/standorte/TankFillCreateDialog.tsx:197`, `pages/duengung/FeedingEventDetailPage.tsx:533`, `pages/standorte/SubstrateCreateDialog.tsx:118` | Fachbegriff-Felder (EC, pH, Runoff-EC) ohne `HelpTooltip`. |
| N-05 | high | 008 R-042/R-043 | `components/form/FormTextField.tsx`, `FormNumberField.tsx`, `FormSwitchField.tsx` (`label: string`); 17/59 `FormSwitchField` ohne Erklärung | Die Form-Komponenten haben keinen Hilfe-Slot. Ein konsistentes Info-Icon am Label ist strukturell unmöglich. |
| N-06 | medium | 009 R-001..R-013 | `assets/brand/` nur `illustrations/`; `index.html` ohne `rel="icon"`; `layouts/Sidebar.tsx:423` | Logo, Favicon, Icon-SVG und Adaptive Icons fehlen. |
| N-07 | high | 008 R-006/R-007 | 43 Formular-Dialoge, z. B. `pages/standorte/SiteCreateDialog.tsx:127`, `pages/pflanzen/PlantInstanceCreateDialog.tsx`, `pages/duengung/FertilizerCreateDialog.tsx` | Backdrop oder Escape verwirft Eingaben ohne Nachfrage. |
| N-08 | medium | 008 R-001 | 91 `useForm`, 0× `mode: 'onBlur'` | Keine Validierung beim Verlassen des Felds. |
| N-09 | medium | 008 R-004, 004 R-019b | 40 Formulare ohne `useFieldViolations`/`setError` | 422-Fehler erscheinen nur als Toast, nicht am Feld. |
| N-10 | medium | 004 R-004/R-007 | `hooks/useNotification.ts:11-14`, `App.tsx:18-24`; 18 Dateien rufen `enqueueSnackbar` direkt auf | Snackbars haben keinen Schließen-Knopf. Fehler verschwinden nach 8 s bzw. 5 s. |
| N-11 | medium | 004 R-015/R-018 | `hooks/useApiError.ts:132-169`; 21/61 `ErrorDisplay` ohne `onRetry` (z. B. `pages/standorte/TankDetailPage.tsx:494`) | Kein „Erneut versuchen". |
| N-12 | medium | 004 R-017 | `pages/ErrorPage.tsx:46-133` | Die 500-Seite zeigt weder Referenz-ID noch Support-Kontakt. |
| N-13 | medium | 005 R-018 | `pages/NotFoundPage.tsx` | Die 404-Seite hat keine Suche. |
| N-14 | medium | 004 R-022 | `pages/durchlaeufe/ActivityPlanTab.tsx:933` → `:441` | Eine Aktivitätsvorlage wird ohne Bestätigung serverseitig gelöscht. |
| N-15 | medium | 005 R-020/R-021 | 16 `*Page.tsx` ohne `PageTitle`; `hooks/useDocumentTitle.ts` hat 0 Aufrufer | Der Tab heißt dort immer „Kamerplanter". |
| N-16 | medium | 005 R-014 | `routes/breadcrumbs.ts`: aquaponik, umgebungssteuerung, ki-assistent, glossar, diagnose, pflanzenschutz/erkennung, succession-plans, tenants/settings, tenants/create, ueberwinterung/profile | Die Breadcrumb verschwindet. |
| N-17 | low | 005 R-017 | `components/layout/Breadcrumbs.tsx:19,23` | = W-04/W-10 |
| N-18 | medium | 005 R-013a | 39× `onClick={() => navigate(...)}` + 37 `onRowClick` | Strg-Klick und Mittelklick funktionieren dort nicht. |
| N-19 | medium | 005 R-001 | `pages/kalender/CalendarPage.tsx:194`, `pages/auth/PrivacySettingsPage.tsx:89` | Ansicht bzw. Tab nicht in der URL. |
| N-20 | medium | 001 R-001 ↔ 005 R-023 / 010 R-019 | `theme/tokens.ts:1-9` | **Widerspruch in der Spec:** 001 fordert die MUI-Breakpoints, 005 und 010 fordern 768/1024. Das muss in der Spec geklärt werden. |
| N-21 | medium | 001 R-011, 021 R-022 | 140/224 `IconButton size="small"`, z. B. `pages/standorte/SiteDetailPage.tsx:397`, `components/common/HelpTooltip.tsx:146` (24 px) | Touch-Ziele zwischen 24 und 34 px, ohne Theme-Override. |
| N-22 | low | 001 R-019 | 22 `<Grid container>`, 0× responsives `spacing` | — |
| N-23 | medium | 003 R-011 | 42/48 Bildstellen ohne `loading="lazy"`, z. B. `pages/pflanzen/photos/PlantPhotoGallery.tsx:297`, `components/common/AuthImage.tsx:27` | Galerien laden alle Bilder sofort. |
| N-24 | medium | 006 R-009 | 217 Hex/rgba-Literale in 22 Dateien außerhalb von `theme/` (z. B. `pages/durchlaeufe/PhaseKamiTimeline.tsx` mit 49) | Ohne Dark-Mode-Variante. |
| N-25 | low | 006 R-015/R-018/R-023 | `theme/typography.ts:4-47` | Roboto ist deklariert, wird aber nie geladen (Fallback Helvetica/Arial). Kein `letterSpacing`, `radii` kaum genutzt. |
| N-26 | medium | 006 R-004 | `theme/ThemeContext.tsx:39-45` | Der Effekt persistiert die Systempräferenz schon beim ersten Laden. Ein späterer Wechsel im Betriebssystem wird ignoriert. |
| N-27 | medium | 010 R-051 | 23/45 DataTable-Nutzer ohne `hideBelowBreakpoint` | Keine Spaltenpriorität. |
| N-28 | medium | 010 R-016/R-017 | 13 DataTables ohne `useTableState` (z. B. `pages/admin/AdminPlansPage.tsx`) | Zustand nicht in der URL. |
| N-29 | medium | 010 R-037 | 20 Dateien mit eigener `<Table>` (z. B. `pages/giessprotokoll/WateringLogDetailPage.tsx`) | Teils Key-Value-Tabellen. Ob die ausgenommen sind, muss die Spec klären. |
| N-30 | medium | 011 §2.2/§4.4 | `components/common/DataTable.tsx:27-45`, `components/common/HelpTooltip.tsx:183-190` | Spaltenköpfe können keine Hilfe tragen. Der Tooltip hat keinen Glossar-Link und öffnet nicht per Tippen. |
| N-31 | low | 008 R-025 | Legende in 18 von ~61 Formularen | — |
| N-32 | low | 008 R-049 | = F-006 | — |
| N-33 | medium | 017 R-009, 021 R-010 | 11 Seitenkopf-Buttons, z. B. `pages/standorte/BatchDetailPage.tsx:125`, `pages/stammdaten/ActivityDetailPage.tsx:229` | Destruktive Aktion als roter Text-Button statt `outlined`. |
| N-34 | medium | 017 R-001/R-002 | `pages/ErrorPage.tsx:79`, `pages/RouterErrorPage.tsx:75` (zweites h1); `pages/stammdaten/ImportPage.tsx:95`, `features/gardenPlanner/field/FieldModeView.tsx:223`, `pages/kiosk/KioskStartPage.tsx:74` | — |
| N-35 | low | 017 R-035 | 5× `Tabs mb:3` vs. 13× `mb:2` | — |
| N-36 | medium | 021 R-016/R-022/R-024 | `components/layout/PageHeaderActions.tsx:136-147`; 10 Nutzer vs. 73 `PageTitle action=` | Kein Overflow, keine 48-px-Mindestgröße für die meisten Seiten. |
| N-37 | medium | 019 R-017/R-021/R-033 | `pages/kiosk/KioskStartPage.tsx:43-64`; `useKioskTimeout` nur in `layouts/KioskLayout.tsx:23` | Die Kacheln führen in die normale Oberfläche, dort greift der Timeout nicht mehr. |
| N-38 | medium | 019 R-024..R-031 | `components/kiosk/` | Keine Tap-Entprellung, kein Long-Press, kein Quick-Select. „QR scannen" führt zur KI-Identifikation. |
| N-39 | medium | 012 R-015/R-020e | `useOnlineStatus` nur in 11 Dateien | Offline-Sperren und -Snackbars fehlen außerhalb des Gartenplans (in Umsetzung). |
| N-40 | medium | 013 CK-003/CP-001 | `components/privacy/ConsentBanner.tsx:31-38` | `external_services` fehlt, kein Server-Abgleich, kein `ConsentProvider`. |
| N-41 | low | 018 R-001/R-016 | `pages/pflanzenschutz/TreatmentDetailPage.tsx:144`; `pages/aufgaben/WorkflowTemplateListPage.tsx` | — |
| N-42/N-43 | low | 004 | 28/63 `EmptyState` ohne Aktion; 409 nur mit generischem Text | — |
| N-44/N-45 | low | [FD], 009 §8 | `theme/typography.ts:4`; 44× `' · '`, 14× uppercase-Labels | Roboto mit MUI-Standardskala ist genau der Template-Default. Eine bewusste typografische Entscheidung fehlt. |

### Dimension 3 — Barrierefreiheit, Client-Security, Performance statisch (W-)

| ID | Schwere | Regel | Beleg | Befund |
|---|---|---|---|---|
| W-01 | high | WCAG 2.1.1/4.1.2 | `components/common/DataTable.tsx:390-395,481-488` | Die klickbare Zeile bzw. Karte hat keine `role`, reagiert nur auf Enter, und es fehlt die Prüfung `e.target === e.currentTarget`. Enter auf einer Zeilenaktion löst deshalb doppelt aus. |
| W-02 | medium | 2.4.3/4.1.3 | `layouts/MainLayout.tsx:249-253`, `components/layout/PageTitle.tsx:31-36` | Bei einem Routenwechsel wird weder der Fokus gesetzt noch angesagt. `main-content` dient nur als Skip-Link-Ziel. |
| W-03 | medium | 3.1.1 | `i18n/i18n.ts:125-127`, `index.html:2` | `<html lang>` wird nie aktualisiert. |
| W-04 | medium | 4.1.2/2.5.3 | `components/layout/ThemeToggle.tsx:10`, `LanguageSelector.tsx:30`, `Breadcrumbs.tsx:20`, `index.html:52` | Englische `aria-label` in der deutschen UI. |
| W-05 | medium | 3.3.2 | `components/common/DataTable.tsx:329-345` | Das Suchfeld hat nur einen Placeholder. |
| W-06 | medium | 1.3.1/2.4.2 | `pages/auth/LoginPage.tsx:87-90` | Kein `<main>`, kein h1, kein `document.title`. Fehler sind nicht an die Felder gebunden. |
| W-07 | medium | 4.1.3/2.2.1 | `components/kiosk/KioskTimeoutOverlay.tsx:76` | `aria-live="assertive"` sagt jede Sekunde an. |
| W-08 | medium | 2.4.7/2.4.11 | `theme/theme.ts` | Kein Fokusring-Override. Der MUI-Default auf ListItemButton, MenuItem und IconButton liegt unter 3:1 (Live-Prüfung siehe L-). |
| W-09..W-19 | low | div. | Kiosk ohne Skip-Link; Breadcrumb ohne `aria-current`; Trigger ohne `aria-haspopup`/`aria-expanded`; Badge-Zahl fehlt im Namen; `NotificationDrawer` mit `role="region"`, stillen Fehlern und rohem Enum (`:383`); `LoadingSkeleton.tsx:51` `width={300}`; `secondary` #5c6bc0 auf #f5f5f5 ≈ 4,46:1; `ConnectivityIndicator` mit `tabIndex` ohne `role`; `ConsentBanner` verdeckt den Fokus; Login-`autoComplete`; `CssBaseline` ohne `enableColorScheme` | — |
| W-20 | medium | CSP | `nginx-security-headers.inc:17` | `style-src 'unsafe-inline'` (Emotion, Boot-Splash). |
| W-21 | medium | CSP | `nginx-security-headers.inc:17` + `observability/errorTracking.ts:373` | `connect-src 'self'` blockt den Sentry/GlitchTip-DSN-Host. Error-Tracking ist in Prod damit vermutlich wirkungslos (am deployten Header zu verifizieren). |
| W-22 | low | Header | `nginx-security-headers.inc:18-20` | `X-XSS-Protection` ist veraltet. `X-Frame-Options` widerspricht `frame-ancestors`. Permissions-Policy, COOP, CORP und `object-src` fehlen. |
| W-23 | low | Redirect | `components/layout/NotificationDrawer.tsx:241-245` | `navigate(action_url)` ohne `safeReturnTo`. |
| W-24 | low | Cache | `nginx.conf:123-127`, `sw.ts:272-280` | `immutable 1y` auf ungehashten Icons. |
| W-25 | medium | Cache | `nginx.conf:63-66,124-125` | Der SPA-Fallback `location /` ohne `no-cache`; doppelter `Cache-Control`. **Hinweis:** Der UI-NFR-Agent wertet die `index.html`-Header als konform. Prüfen lässt sich das nur am Prod-Header (`curl -I`). |
| W-26..W-33 | low–medium | Perf | doppelter Auth-Bootstrap (= B-07, medium); `DataTable` `useMemo` mit instabilen `columns` (medium); `NotificationBell` pollt alle 60 s ohne `visibilityState`; `waitForTenantSlug` pollt alle 50 ms; MainLayout importiert Dialoge statisch; synchrones `runtime-config.js` (bewusst); `public/manifest.json` Shortcut `/kalender/aussaat` ohne Route und `"any maskable"` | — |

**Eigene Sweeps:** 0× `dangerouslySetInnerHTML`. Alle `target="_blank"` haben `rel="noopener noreferrer"`. Im `localStorage` liegen keine Tokens (nur Theme, Präferenzen, Consent, Tenant-Slug).
**Positiv:** Alle Routen werden per `lazy()` geladen. Sentry wird dynamisch und nur nach Consent geladen. Der Token liegt nur im Speicher. `returnTo` wird validiert. Skip-Link, `prefers-reduced-motion` und `script-src 'self'` sind vorhanden.

### Dimension 4 — i18n (I-)

Der Key-Diff lief per Skript: DE- und EN-Locale flach gezogen und gegen die statischen `t('…')`-Aufrufe abgeglichen. Parität: core 776/776, enums 990/990, glossary 171/171, pages 7.361/7.360. `{{var}}`-Platzhalter: 0 Abweichungen. Formelles „Sie" in der deutschen UI: 0.

| ID | Schwere | Beleg | Befund |
|---|---|---|---|
| I-01 | medium | `common.confirmDelete` (`pages/stammdaten/ActivityDetailPage.tsx:477`), `common.created` (`ActivityCreateDialog.tsx:97`), `common.deleted` (`ActivityDetailPage.tsx:180`), `common.error` (`pages/pflanzen/PlantTagDialog.tsx:56`), `common.noSearchResults` (`pages/aufgaben/WorkflowTemplateListPage.tsx:408`), `common.notes` (`pages/pflege/components/CareConfirmDialog.tsx:197,205`), `errors.generic` (`pages/environment/EnvironmentControlPage.tsx:99,133`), `pages.nutrientPlans.dosageCalc.targetEc` (`pages/duengung/DosageCalculatorTab.tsx:162`), `pages.runs.plantCount`/`standalonePlants` (`pages/aufgaben/WorkflowDetailPage.tsx:773,809`), `pages.tasks.duplicateWorkflow`/`…Description`/`workflowDuplicated` (`WorkflowTemplateListPage.tsx:213,217,335,478`) | **13 statisch verwendete Keys ohne Definition** und ohne `defaultValue`. Die UI zeigt den rohen Key. Der i18n-Agent hatte sie übersehen. |
| I-02 | medium | `src/test/i18n/` | Es gibt keinen Guard-Test für Parität und Used-vs-defined. Das ist der Grund, warum I-01 unbemerkt durchrutscht. |
| I-03 | low | „Platform"-Chip `pages/auth/AccountSettingsPage.tsx:1932`, `pages/admin/AdminEditTenantPage.tsx:352`; `label="Key"` `pages/admin/AdminEditUserPage.tsx:345`; Zod-Meldung `pages/stammdaten/BotanicalFamilyCreateDialog.tsx:46`, `BotanicalFamilyDetailPage.tsx:64` (= F-011); `'Unknown error'` `features/gardenPlanner/api/gardenPlan.ts:127` | Hartkodierte Strings (Untergrenze). |
| I-04 | low | `pages.phaseSequences.searchSequences` (`de/pages.json:3854`) | Der Key existiert nur in DE und wird im Code nicht verwendet. |
| I-05 | low | 1.758 dynamische `` t(`…${}`) ``-Aufrufe in 300 Dateien; `defaultValue`-Fallbacks (z. B. `pages/stammdaten/CropRotationPage.tsx` mit `defaultValue: ''`) | Statisch nicht prüfbar. `defaultValue` verdeckt fehlende Keys. Empfohlen: Enum-Wertlisten gegen `enums.json` maschinell abgleichen. |

### Dimension 5 — Performance und Bundle (P-)

Gemessen mit einem lokalen `vite build` und anschließendem `npm run bundle:check`.

| ID | Schwere | Beleg | Befund |
|---|---|---|---|
| P-01 | high | `bundle-budget.json`; Messung: Initial-JS **394,3 / 400 KB gzip (99 %)**, 19 Initial-Chunks | Am 2026-07-20 waren es 343,3 KB (+51 KB in vier Monaten). Das Ziel nach R-013 sind 300 KB. Der nächste Feature-PR reißt das Gate. |
| P-02 | medium | `src/assets/illustrations/errors/error-503.svg` 690 KB (256 KB gzip), `error-403` 605 KB, `error-429` 556 KB, `error-408` 542 KB, `error-404` 419 KB; importiert in `pages/ErrorPage.tsx:9-17`; 45 SVGs > 100 KB, zusammen 11,8 MB | Ausgerechnet die 503-Seite lädt 256 KB Illustration. Gegenmaßnahmen: SVGO bzw. Rasterbild (WebP) und Lazy Loading. |
| P-03 | info | Sentry-Chunk 186 KB gzip | Lazy und nur nach Consent geladen, in Ordnung. |
| P-04 | low | Build-Log: `inlineDynamicImports option is deprecated` | Warnung vom VitePWA-/Rolldown-Pfad. |
| Übrige Budgets | ok | Initial-CSS 0,4/50 KB; `/dashboard` 5,4/12; Gartenplan-Route 85,7/120; Konva 98,3/200 | — |

Lighthouse-Werte: siehe [Dimension 7](#dimension-7--live-audit).

### Dimension 6 — Testbarkeit und Testgesundheit (T-)

**E2E-Vertrag intakt:** Alle 868 wörtlichen testid-Verweise der Page Objects wurden gegen den Code geprüft. Keiner zeigt auf eine nicht mehr existierende testid. Testhygiene: 0× `skip`/`only`/`todo`, 0 Testdateien ohne Assertion, `cleanup()` global (`src/test/setup.ts:68-69`).

| ID | Schwere | Regel | Beleg | Befund |
|---|---|---|---|---|
| T-01 | high | 022 R-014 | `components/common/DataTable.tsx:406,499`; 45 Konsumenten, 48 E2E-Verweise | Die Zeilen tragen ein festes `data-table-row` ohne fachlichen Schlüssel, obwohl `getRowKey` existiert. |
| T-02 | medium | 022 R-005 | 20 von 89 `*Page.tsx` ohne `*-page`-Marker | — |
| T-03 | medium | 022 R-009 | ~520 Bedienelemente ohne testid (MenuItem 140/170, Button 175/748, IconButton 66/235 …); geteilte Wrapper `components/form/FormSwitchField.tsx:30`, `SubstrateSelectField.tsx:138` | — |
| T-04 | medium | 022 R-011 | 22 von 136 `<Dialog>` ohne testid (= D-001-Rest) | — |
| T-05 | medium | 022 R-004 | 17 Stellen, z. B. `hooks/useRetryFocus.ts:107`, `features/gardenPlanner/editor/GardenPlanEditor.tsx:1359` | Produktionslogik selektiert über `[data-testid]`. Eine Umbenennung für E2E bricht unbemerkt die Fokusführung. |
| T-06..T-10 | low/info | 022 R-014/R-017/R-018/R-021 | 22 index-basierte testids (`components/common/PhotoUpload.tsx:261`); 45× `-btn` statt `-button`; nicht-kebab (`components/dashboard/widgets/QuickActionsWidget.tsx:39`); per Präfix komponierte testids sind nicht greppbar | — |
| T-11 | medium | FRONTEND §13.3 | 176 Testdateien mit `vi.mock('@/api…')`; 49/50 Endpoint-Tests prüfen nur URL-Strings | Kein MSW. Der Vertrag mit dem Backend und die Interceptor-Pfade bleiben ungetestet. |
| T-12 | medium | FRONTEND §13.2 ↔ UI-NFR-022 | Repo-weit 8.590 `*ByTestId` vs. 1.765 `*ByRole` vs. 238 `*ByLabelText`; kein `eslint-plugin-testing-library` | **Zielkonflikt in den Specs:** UI-NFR-022 macht die testid zum primären Anker, §13.2 bevorzugt Rolle und Label. Die Ebenen Unit und E2E sollten in FRONTEND.md §13 getrennt geregelt werden. |
| T-13 | medium | Pyramide | `TaskCreateDialog` (7 Eltern-Tests mocken ihn auf `null`), `CareConfirmDialog` (9), `PlantingRunDetailsTab` | Geschäftslastige Kindkomponenten sind nirgends getestet. |
| T-14..T-16 | low/info | — | 35 feste Sleeps; ein innerHTML-Snapshot; 7 Benchmarks laufen nur mit `GP_BENCHMARK=1` | — |
| T-17 | medium | Coverage | 323 von 1.008 Modulen ohne direkten Test: pages 84, components 25, gardenPlanner 154, hooks 31, store 2, api 8. Wichtig: `pages/ernte/HarvestBatchDetailPage.tsx`, `features/gardenPlanner/editor/PropertiesPanel.tsx`, `pages/onboarding/OnboardingWizard.tsx`, `hooks/useStepUpReauth.ts`, `hooks/useStepUpFactors.ts`, `hooks/useCanEditInstallationCatalogue.ts`, `store/sessionEpochMiddleware.ts` | — |

### Dimension 7 — Live-Audit

**Setup:**

- Ziel war die Dev-Instanz auf `http://localhost:3000` (kind, Vite-Dev-Server, Light-Modus ohne Login, Mandant `mein-garten`).
- Werkzeuge: puppeteer-core mit Chromium 151, axe-core 4.14 (Tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`) und die Lighthouse-13.6-CLI. Die Playwright- und DevTools-MCP-Server waren nicht nutzbar.
- Geprüft wurden 10 Routen und 2 Dialoge in Light und Dark. Dashboard, Liste, Detail und Gartenplan liefen zusätzlich bei 375, 820 und 1440 px, alle Routen außerdem bei 320 px (Reflow). Die Tastaturprüfung lief auf Dashboard und Arten-Liste.

**axe-Ergebnis (1440 px):**

| Route | Light | Dark |
|---|---|---|
| `/dashboard` | label-content-name-mismatch (serious, 6) | dto. |
| `/stammdaten/species`, `/stammdaten/species/10031`, `/pflanzen/plant-instances`, `/standorte/sites/47117/plan`, `/aufgaben/workflows/14345`, Dialog „Art erstellen" | 0 | 0 |
| `/aufgaben/queue` | aria-input-field-name (serious, 1) | dto. |
| `/kalender` | aria-required-children (**critical**, 1), color-contrast (serious, 10) | dto. (9) |
| `/settings` | color-contrast (serious, 1; deaktiviertes Feld, formal ausgenommen) | 0 |
| Dialog „Per Foto hinzufügen" | label-content-name-mismatch (serious, 1) | — |

**Befunde:**

| ID | Schwere | Regel | Route | Beleg | Befund |
|---|---|---|---|---|---|
| L-01 | medium | WCAG 3.1.1 | alle, UI auf EN | `index.html:2`, `i18n/i18n.ts` | `<html lang>` bleibt bei englischer UI auf „de". Bestätigt W-03. |
| L-02 | medium | 4.1.2 | Topbar | `components/layout/ThemeToggle.tsx:10`, `LanguageSelector.tsx:30` | Englische Namen „toggle theme" und „change language" im deutschen Tab-Durchlauf. Bestätigt W-04. |
| L-03 | medium | 3.1.2 | Listen mit Autocomplete | `pages/aufgaben/TaskQueuePage.tsx:1614`; kein `deDE` aus `@mui/material/locale` | MUI-Eigentexte („Open", „Clear", „No options") bleiben englisch. |
| L-04 | high | 4.1.2 | `/aufgaben/queue` | `pages/aufgaben/TaskQueuePage.tsx:1554-1556` | Der Filter-`Select` hat kein `labelId`, die Combobox bleibt ohne Namen. |
| L-05 | medium | 3.3.2 | alle DataTables | `components/common/DataTable.tsx:329-333` | Die Suche hat nur einen Placeholder als Namen. Bestätigt W-05. |
| L-06 | medium | 2.1.1 | `/stammdaten/species` | `components/common/DataTable.tsx:390-392,481-484` | Zeilen reagieren auf Enter, aber nicht auf Space, und haben keine Rolle. Bestätigt W-01. |
| L-07 | medium | 2.4.7 / 1.4.11 | Sidebar, Menüs, Topbar | `kbd-dashboard-tab09.png`, `kbd-menuitem-focus.png` | Bei ListItemButton und MenuItem zeigt sich der Fokus nur als Tint (`rgba(0,0,0,.12)`, ≈1,3:1). Auf dem aktiven Sidebar-Eintrag ist der Fokus kaum vom Auswahlzustand zu unterscheiden. Bestätigt W-08. |
| L-08 | medium | 2.4.3 | Sidebar-Navigation | `kbd-results.json` | Nach einem Routenwechsel bleibt der Fokus im Sidebar-Link. Es gibt keine Ansage. Bestätigt W-02. |
| L-09 | high | 1.4.3 | `/kalender` | `pages/kalender/CalendarPage.tsx:95-107` (`CATEGORY_COLORS`), `:1017`, `:1400-1409` | Weißer Text auf hellen Kategoriefarben, z. B. „Training" #fff auf #4CAF50 = 2,77:1. Betroffen sind 9–10 Knoten mit 0,6 rem Schrift. |
| L-10 | high | 1.3.1 / 4.1.2 | `/kalender` Monatsansicht | `pages/kalender/CalendarPage.tsx:1071` (`role="table"`), `:694`, `:731` (`role="button"`) | Ungültige ARIA-Struktur, weil Buttons direkt unter `table` hängen statt in `cell`. axe stuft das als critical ein. |
| L-11 | medium | 2.5.3 | `/dashboard` | `components/dashboard/WidgetFrame.tsx:121-126` | `aria-label` „{{widget}} öffnen" überschreibt den sichtbaren Kartentext. |
| L-12 | low | 2.5.3 | Consent-Gate | `components/identification/IdentificationConsentGate.tsx:147-153` | — |
| L-13 | low | 1.3.1 | `/dashboard`, `/stammdaten/species` mobil | Lighthouse `heading-order` | Die Überschriften springen von h1 auf h3 bzw. h6. |
| L-14 | low | UX | `/login` im Light-Modus | `axe-login-light-desktop.png` | Die Seite zeigt 404 statt eines Redirects auf `/dashboard`. |
| L-15 | medium | UI-NFR-012 | Manifest-Shortcut | `public/manifest.json:35` | `/kalender/aussaat` führt auf eine 404. Bestätigt W-33. |
| L-16 | low | Konsole | `/dashboard` | `api/endpoints/ai.ts:67`, `components/ai/DailyTipCard.tsx`; `index.html` | Bei jedem Dashboard-Aufruf liefert `GET …/ai/daily-tip` eine 404 und erscheint als Konsolenfehler. Dazu kommt ein 404 für `/favicon.ico` (= N-06). |
| L-17 | low | UI-NFR-017 | Gartenplan mobil | `features/gardenPlanner/field/FieldModeView.tsx:230-247` | Der Seitenkopf weicht ab: h1 in der Card, schwarz umrandete Buttons in GROSSBUCHSTABEN. Die Editor-Werkzeugleiste ist ebenfalls uppercase (vgl. N-45). |
| L-18 | low | visuell | Gartenplan Desktop, Dark | `vis-gardenPlan-desktop-dark.png` | Das Label „Bereich 2" überlappt „Beet 1". |
| L-19 | low | UI-NFR-021 | Art-Detail bei 320 px | `reflow320-speciesDetail.png` | Das Kebab-Menü bricht allein unter den Titel um (vgl. N-36). |
| L-20 | low | 1.4.3 (Ausnahme) | `/settings` | `axe-settings-light-desktop.png` | Hilfetext eines deaktivierten Felds hat nur 2,67:1. |
| L-21 | low | visuell | `/dashboard` | `vis-dashboard-desktop-dark.png` | Uneinheitliche Widget-Köpfe (Chevron mal inline, mal in der Ecke). |

**Ohne Befund (live):**

- Kein horizontaler Seiten-Overflow bei 320, 375, 820 und 1440 px. Breite Tabellen und Tabs scrollen in ihrem eigenen Container.
- Keine rohen i18n-Keys auf den erreichbaren Routen. Die Stellen aus I-01 waren mangels Daten nicht erreichbar, dort wäre etwas anzulegen gewesen.
- Keine JS-Exceptions oder React-Warnungen.
- Fokusreihenfolge logisch, und jeder Stopp erfüllt `:focus-visible`.
- Dialog „Art erstellen": Initialfokus, `aria-modal`, und der Fokus kehrt zum Auslöser zurück.
- Kein Touch-Ziel unter 24 px (WCAG 2.5.8). Das ändert nichts an N-21: UI-NFR-001 verlangt 48 px.
- Der Verdacht W-14 (LoadingSkeleton-Overflow) ist widerlegt: Die Skeletons werden auf 288 px begrenzt.

**Lighthouse 13.6** (Dev-Server, unminifiziert, Mobile mit simuliertem Throttling): Die Performance-Werte sind **nicht aussagekräftig**. Für die Performance gilt die Build-Messung P-01.

| Seite | Perf | A11y | Best Practices | Fehl-Audits |
|---|---|---|---|---|
| Dashboard Desktop | 32* | 98 | 96 | heading-order, errors-in-console (L-16), CLS 0,107 |
| Dashboard Mobile | 35* | 98 | 96 | heading-order, errors-in-console |
| Arten-Liste Desktop | 35* | 100 | 96 | errors-in-console |
| Arten-Liste Mobile | 30* | 98 | 96 | heading-order, CLS 0,131 (nachladende Widgets, Sidebar) |

\* Dev-Modus.

**Nicht live prüfbar:**

- Login-Formular: Im Light-Modus gibt es keine Auth-Routen (W-06 bleibt statisch belegt).
- Pflanzen-, Aufgaben- und Durchlauf-Detail mit Daten, weil der Mandant leer ist.
- Echte nginx-Header (W-20..W-25).
- Screenreader-Ausgabe.
- Kalender, Settings, Workflow und Tasks bei 375 und 820 px.

Artefakte (Screenshots, axe-JSON, Lighthouse-HTML) liegen außerhalb des Repos im Session-Scratchpad und sind nicht Teil des Reports.

---

## Delta zum April-Audit

Grundlage sind die 29 Befunde aus beiden April-Reports. Die zitierten UI-NFR-Regeln haben unveränderten Wortlaut. Neu ist UI-NFR-022 (v1.5): Sie verschärft F-018, D-001 und D-011.

**Bilanz: 12 behoben · 9 teilweise · 5 offen · 4 obsolet** (30 Zeilen, weil F-015 als Duplikat von F-007 mitgezählt ist).

| ID | Titel | Status | Alt → Neu | Aktueller Beleg / Bemerkung |
|---|---|---|---|---|
| F-001 | `maxWidth: 900` auf Detailseiten | **behoben** | 17 Dateien → 0 | z. B. `pages/standorte/BatchDetailPage.tsx:132`, `pages/standorte/TankDetailPage.tsx:1167` |
| F-002 | OriginChip / UI-NFR-018 | teilweise | 0/17 → 16/17 Seiten | `components/common/OriginChip.tsx:55`. `Pest` hat kein `origin`-Feld (Datenmodellfrage). Offen sind Herkunftsfilter R-016 (WorkflowTemplateList) und N-41. |
| F-003 | HelpTooltip fehlt | teilweise | 0 → 33 Dateien | Offen: EC in TankDetail, EC/pH/VPD/PPFD in `pages/pflanzen/ProfileEditDialog.tsx:204-205`, GDD/VPD in Species-Detail, Pest-/Treatment-Listen → N-04 |
| F-004 | Pattern C: Titel und Chips in einer Zeile | **offen** | 3 → 3 | `pages/duengung/NutrientPlanDetailPage.tsx:61-82`, `pages/durchlaeufe/PlantingRunDetailPage.tsx:545-551`, `pages/ernte/HarvestBatchDetailPage.tsx:276`. Der `meta`-Prop wird nicht genutzt. |
| F-005 | Listen ohne DataTable | **behoben** | 2 → 0 | Die rohen `<Table>` in Detail-Tabs prüft jetzt N-29. |
| F-006 | Unicode-Escapes (R-049) | teilweise | 53 Dateien → 20 (sichtbar: 4) | `pages/pflanzenschutz/PestDetailPage.tsx:346`, `pages/pflanzen/PlantInstanceListPage.tsx:206`, `features/gardenPlanner/history/HistoryList.tsx:77`, `pages/kalender/PhaseTimelineView.tsx:509` (Mini-Fix) |
| F-007 | URL-Persistenz in Listen | teilweise | 17 → 2 | `pages/aufgaben/TaskQueuePage.tsx:259`, `pages/aufgaben/WorkflowTemplateListPage.tsx:290`; siehe auch N-28 |
| F-008 | Panel-Einleitungstexte | obsolet | — | UI-NFR-008 R-038 nennt den Text seit März 2026 „optional". Das war schon im April ein Fehlbefund. |
| F-009 | UnsavedChangesGuard auf Phasenseiten | obsolet | 3 → 0 anwendbar | `ActivityPlanDetailPage` existiert nicht mehr. Phasen werden nur in Dialogen bearbeitet. Die Lücke in den Dialogen steht jetzt unter N-07. |
| F-010 | i18n `common.origin.*` | **behoben** | — | `i18n/locales/{de,en}/core.json:353` |
| F-011 | Zod-Meldung „-aceae" hartkodiert | **offen** | 2 → 2 | `pages/stammdaten/BotanicalFamilyCreateDialog.tsx:46`, `BotanicalFamilyDetailPage.tsx:64` (Mini-Fix) |
| F-012 | Breadcrumb `/aufgaben/activity-plans` | obsolet | — | Die Route ist nur noch ein `<Navigate>`. |
| F-013 | ImportPage mit `h4` statt PageTitle | **offen** | 1 → 1 | `pages/stammdaten/ImportPage.tsx:95` |
| F-014 | Drei Leerwert-Muster | teilweise | ~40 Dateien gemischt → praktisch nur noch `'—'` | Eine zentrale `EMPTY_VALUE`-Konstante fehlt (war nur Empfehlung). |
| F-015 | Duplikat von F-007 | obsolet | — | — |
| F-016 | `'EC (mS/cm)'` hartkodiert | **offen** | 3 → 3 | `pages/standorte/TankDetailPage.tsx:400,1134,1152`; dazu `pages/pflanzen/ProfileEditDialog.tsx:204-205` |
| F-017 | PageTitle ohne `meta` | **behoben** | — | `components/layout/PageTitle.tsx:23,63` |
| F-018 | IconButtons ohne testid | **offen** | Phasen 7/8; repo-weit 67/235 | Seit UI-NFR-022 R-009 eine MUSS-Regel; siehe T-03 |
| D-001 | Dialog-Root ohne testid | teilweise | Anhang A 30 → 0; repo-weit 22 | Die Reste sind neue Dialoge seit April (Mini-Fix). |
| D-002 | Dialog ohne `aria-labelledby` | **behoben** (Altkorpus) | 47 → 0; **neu 20** | **Regression in neuem Code:** `pages/environment/ActuatorDialog.tsx:215`, `pages/standorte/WateringEventListPage.tsx:105`, `pages/aufgaben/WorkflowDetailPage.tsx:1169` (Mini-Fix) |
| D-003 | Unicode-Escapes in Dialogen | **behoben** | 11 → 0 | — |
| D-004 | Icon-Buttons ohne `aria-label` | teilweise | 5 Dateien → 1 | `pages/pflege/components/CareConfirmDialog.tsx:218` |
| D-005 | Roher Enum im Chip | **behoben** | 1 → 0 | — |
| D-006 | Kein RHF+Zod | **behoben** | 2 → 0 | — |
| D-007 | Hartkodierte Strings (WorkflowInstantiate) | **behoben** | 2 → 0 | Rest aus Anhang C: `pages/standorte/SubstrateMixDialog.tsx:164,171`, `CareConfirmDialog.tsx:288` |
| D-008 | HelpTooltip in Dialogen | teilweise | 4 → 2 | `pages/standorte/SensorCreateDialog.tsx:36`, `pages/standorte/TankStateCreateDialog.tsx:138,197` |
| D-009 | `autoFocus` fehlt | **behoben** | 11 → 0 | Slot/Batch bleiben die akzeptierte Ausnahme. |
| D-010 | Onboarding-Wasserfelder | **behoben** | 3 → 0 | — |
| D-011 | Generisches `create-dialog` | **behoben** | 5 → 0 | — |

**Lehre:** Wo ein April-Befund über eine **geteilte Komponente** behoben wurde (OriginChip, PageTitle, `useTableUrlState`, HelpTooltip), ist er nachhaltig weg. Wo er pro Datei behoben wurde (`aria-labelledby`, testids), kommt er in neuem Code wieder (D-002). Die Folgemaßnahmen setzen deshalb bevorzugt auf geteilte Komponenten und Guard-Tests (I-02, T-01, M12).

---

## Im Branch behobene Mini-Fixes

Commits `a5dd5230d` (80 Dateien) und `afd06381c` auf diesem Branch. Alle Fixes sind verhaltensneutral. Bestehende `data-testid` sind unverändert, neue sind nur hinzugekommen (UI-NFR-022 R-021). Geprüft wurde mit `tsc` (0 Fehler), ESLint auf allen geänderten Dateien (0 Fehler) und 41 betroffenen Vitest-Dateien (alle grün). Vier Test-Assertions wurden minimal angepasst, weil sie die alte, falsche Ausgabe geprüft hatten: Breadcrumbs, LanguageSelector, ThemeToggle und BotanicalFamilyCreateDialog.

| Befund | Fix |
|---|---|
| I-01, I-04 | 13 fehlende Keys in DE und EN ergänzt (`common.confirmDelete`, `common.created`, `common.deleted`, `common.error`, `common.noSearchResults`, `common.notes`, `errors.generic`, `pages.nutrientPlans.dosageCalc.targetEc`, `pages.runs.plantCount`, `pages.runs.standalonePlants`, `pages.tasks.duplicateWorkflow*`, `pages.tasks.workflowDuplicated`) und EN `pages.phaseSequences.searchSequences` nachgezogen. `errors.generic` behebt nebenbei auch EquipmentDialog, AquaponicSystemDialog und ActuatorDialog. |
| W-04, L-02, W-10, N-17 | `aria-label` für Theme-Umschalter (nennt den Zielzustand), Sprachauswahl und Breadcrumb über i18n. Die letzte Breadcrumb-Stufe hat jetzt `aria-current="page"`. |
| W-03, L-01 | `i18n/i18n.ts` setzt `<html lang>` beim Init und bei jedem `languageChanged`. |
| W-05, L-05 | Das DataTable-Suchfeld hat einen zugänglichen Namen. |
| I-03, F-011, A-19 | „Platform"-Chip, „Key"-Label, die Zod-Meldung „-aceae" (`validation.botanicalFamilySuffix`, wird beim Validieren aufgelöst) und „(Kopie)" laufen über i18n. |
| A-20 | Eigene Keys für die Buttons „Vorheriger Monat" und „Nächster Monat". |
| N-34 (Fehlerseiten) | Das dekorative h1 auf ErrorPage und RouterErrorPage ist jetzt ein `<p>`. |
| F-006, N-32 | Sichtbare Unicode-Escapes (–, °, ›, ·, …) sind durch die echten Zeichen ersetzt. |
| L-04 | Filter-Selects sind per `labelId` und `id` benannt: TaskQueuePage, AdminEditUser, AdminEditTenant, WorkflowCreateDialog, WorkflowDetailPage. |
| T-01 (Teil) | `data-row-key` an DataTable-Zeilen und Mobile-Karten. Die Page Objects stellen noch nicht darauf um (#3024). |
| D-001, D-002, T-04 | 27 Dialoge haben jetzt `data-testid` und `aria-labelledby`. Ein Nachscan findet keine Lücke mehr. |
| T-02 | 21 Seitenmarker `<name>-page`. Wo die Seite einen Fragment-Root hatte, ist ein schlichter `Box`-Wrapper hinzugekommen. |
| D-004 | Der Auf/Zu-Button in `CareConfirmDialog` hat jetzt `aria-label` und `aria-expanded`. |
| N-33 | 10 Lösch-Buttons im Seitenkopf haben jetzt `variant="outlined"`. |
| N-15, W-06 (Teil) | 10 Auth-Seiten setzen `document.title` über `useDocumentTitle`. |
| W-01/L-06 (Teil) | Commit `afd06381c`: DataTable-Zeilen und -Karten reagieren auf Enter und Space, aber nur, wenn die Zeile selbst das Ziel ist, und ohne Key-Repeat. Enter auf einer Zeilenaktion löst die Zeile nicht mehr zusätzlich aus. Abgesichert durch zwei neue Tests und eine Gegenprobe. Rolle und Name der Zeile bleiben offen (#3017). |
| L-15, W-33 (Teil) | Der Manifest-Shortcut „Aussaatkalender" zeigt auf `/kalender` statt auf die nicht existierende Route `/kalender/aussaat`. |

**Nicht als Mini-Fix umgesetzt:**

- MUI-Locale (L-03), Überschriftenreihenfolge im Dashboard (L-13) und Label-in-Name (L-11/L-12): Sie gehen über einen trivialen Fix hinaus, weil die Widget-Titel nicht zentral gerendert werden.
- `StepUpCallbackPage` hat keinen Titel-Key.

Alle diese Punkte stehen in den Issues #3017 bzw. #3025.

---

## Angelegte Issues

Nach Betreiberentscheidung vom 2026-11-17 hat jedes high-Bündel ein eigenes Issue. Die acht medium-Bündel stehen gesammelt in einem Tracking-Issue.

| Bündel | Issue |
|---|---|
| M2 Open Redirect `action_url` | #3012 |
| M1 Fehlerpfad-Vertrag | #3013 |
| M3 Stale-Response/Abbruch | #3014 |
| M4 Datenvollständigkeit und Fan-out | #3015 |
| M5 Domänen-Duplikate (aktive Woche, UTC-„heute") | #3016 |
| M6 Tastatur- und Screenreader-Bedienung | #3017 |
| M9 Mobile Navigation | #3018 |
| M10 Formular-Verhalten | #3019 |
| M8 Fachbegriffe/Hilfe | #3020 |
| M7 Farb- und Design-Tokens | #3021 |
| M21 Hook-Korrektheit | #3022 |
| M11 Bundle und Assets | #3023 |
| M12 Testbarkeit (UI-NFR-022) | #3024 |
| M13–M20 (medium, gesammelt) | #3025 |

Die low-Befunde bleiben im Report, soweit sie nicht als Mini-Fix behoben oder einem Issue zugeordnet sind.

---

## Offene Spec-Fragen

1. **Breakpoints (N-20):** UI-NFR-001 R-001 fordert die MUI-Standardwerte, UI-NFR-005 R-023 und UI-NFR-010 R-019/R-021 fordern 768/1024. Der Code folgt 005/010.
2. **testid gegen Rolle (T-12):** UI-NFR-022 und FRONTEND.md §13.2 brauchen eine Abgrenzung nach Testebene.
3. **Key-Value-Tabellen (N-29):** Fallen Detailtabellen unter UI-NFR-010 R-037 („alle Tabellen")?
4. **Herkunft bei Pest (F-002):** Soll `Pest` ein `origin`-Feld bekommen?
5. **Snackbar-Dauer (N-10):** 8 s für Fehler (#571) widerspricht UI-NFR-004 R-004/R-007.
