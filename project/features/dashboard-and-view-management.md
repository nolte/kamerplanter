---
id: F-23
title: Dashboards und Ansichten verwalten
status: draft
roadmap_item: R-21
sprint: null
created: 2026-11-17
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-11-17
  agent_version: feature-consistency-reviewer@a38d18746
  findings:
    - kind: overlap
      target: F-11
      resolution: proceed
      evidence: "F-11 acceptance-2/5 move DashboardSettingsTab and the /settings#dashboard links (DashboardPage.tsx:258,344) and edit dashboard-personalization.md; F-23 moves adding/managing to the dashboard; the settings toggle is one instance per key (dashboardLayoutOps.ts:117-122)."
    - kind: drift
      target: spec/req/REQ-045_Individualisierbares-Dashboard.md:31
      resolution: proceed
      evidence: "REQ-045 calls settings the primary surface (:31) and fixes 'one dashboard per user' with multiple dashboards as phase 2 (§1.1 :54/:58); amended via F-22 acceptance-6."
    - kind: drift
      target: spec/ui-nfr/UI-NFR-005_Navigation.md:108
      resolution: proceed
      evidence: "R-018 demands 404 for invalid URLs; operator decision: unknown or deleted /dashboard/<d>/<v> shows 404 with a link to the default dashboard."
    - kind: prior-art
      target: src/frontend/src/lib/dashboardLayoutOps.ts:81
      resolution: proceed
      evidence: "addWidget/removeWidget (:81-115) already support several instances; kebab keyboard alternative and 48 px targets are specified (REQ-045 §3.8:435-442); resolveDefaultLayout(level) (dashboardWidgetCatalog.ts:187) yields the default copy."
    - kind: drift
      target: src/backend/app/domain/models/user_preference.py:51
      resolution: proceed
      evidence: "The model has no upper bounds today; the 10/10 limits are enforced server-side in the F-22 model."
---

## Description

Wer heute verschiedene Bereiche im Blick haben will — Wohnzimmer, Gewächshaus,
Balkon —, muss sich mit einem einzigen Dashboard behelfen, und neue Widgets
kommen nur über einen Umweg in den Einstellungen dazu, jedes Widget nur
einmal.

Nach dieser Änderung wählt man oben auf der Dashboard-Seite das Dashboard und
darunter die Ansicht per Tab; jede Ansicht hat eine eigene Adresse, die man
als Lesezeichen speichern kann. Dashboards und Ansichten lassen sich anlegen,
umbenennen, duplizieren, sortieren und löschen; das letzte Dashboard und die
letzte Ansicht lassen sich nur zurücksetzen. Ein neues Dashboard beginnt leer
oder als Kopie des Standards der eigenen Erfahrungsstufe. Widgets fügt man
direkt auf dem Dashboard aus einem durchsuchbaren Katalog hinzu, dasselbe
Widget auch mehrfach. Der bisherige Einstellungs-Tab verweist nur noch hierher.

## Acceptance criteria

- [ ] **acceptance-1** Die Dashboard-Seite zeigt eine Dashboard-Auswahl und Tabs für die Ansichten (mobil scrollbar oder als Auswahl); jede Ansicht ist unter `/dashboard/<dashboard>/<ansicht>` erreichbar, und ohne Pfad öffnet sich die erste Ansicht des Standard-Dashboards.
- [ ] **acceptance-2** Dashboards und Ansichten lassen sich anlegen, umbenennen, duplizieren, sortieren und nach Rückfrage löschen; das letzte Dashboard und die letzte Ansicht lassen sich nur zurücksetzen; wird das Standard-Dashboard gelöscht, wird das erste verbleibende zum Standard.
- [ ] **acceptance-3** Pro Mandant sind höchstens 10 Dashboards und pro Dashboard höchstens 10 Ansichten möglich; an der Grenze erklärt eine Meldung, warum nichts mehr angelegt werden kann.
- [ ] **acceptance-4** Ein neues Dashboard beginnt leer oder als Kopie des Standards der eigenen Erfahrungsstufe.
- [ ] **acceptance-5** Widgets lassen sich direkt auf dem Dashboard aus einem durchsuchbaren, nach Kategorien gegliederten Katalog hinzufügen, dasselbe Widget auch mehrfach; der Einstellungs-Tab enthält nur noch den Link „Dashboards bearbeiten“.
- [ ] **acceptance-6** Eine unbekannte oder gelöschte Dashboard- oder Ansichtsadresse zeigt die 404-Seite mit einem Link zum Standard-Dashboard.
- [ ] **acceptance-7** Alle neuen Bedienelemente sind per Tastatur bzw. Menü ohne Ziehen bedienbar und haben Touch-Ziele von mindestens 48 px.
- [ ] **acceptance-8** Die Nutzerdoku (DE + EN) beschreibt Dashboards, Ansichten und das Hinzufügen von Widgets.

## Test hooks

- **acceptance-1** — vitest routing tests + E2E `tests/e2e/test_req009_dashboard.py` extended — pending
- **acceptance-2** — vitest on the management menu; backend test for default reassignment — pending
- **acceptance-3** — backend limit tests (11th dashboard/view → 422) + vitest message — pending
- **acceptance-4** — vitest: empty vs. `resolveDefaultLayout(level)` copy — pending
- **acceptance-5** — vitest: catalog search/categories, second instance of the same key — pending
- **acceptance-6** — vitest: unknown/deleted ids → 404 page with link — pending
- **acceptance-7** — axe/a11y checks + keyboard-only E2E path — pending
- **acceptance-8** — `mkdocs build --strict` — pending

## Consistency notes

**Overlap with F-11 (proceed).** Established: F-11 moves `DashboardSettingsTab`
and the `/settings#dashboard` links (`DashboardPage.tsx:258,344`) and edits
`dashboard-personalization.md`; the settings toggle adds one instance per key
(`dashboardLayoutOps.ts:117-122`) and knows no dashboards or views. Rationale
for `proceed`: operator decision 2026-11-17 — F-11 ships first; F-23 then
reduces the settings tab to a link "edit dashboards" and owns
`dashboard-personalization.md` afterwards. The features stay separate because
F-11 regroups the settings page, F-23 builds dashboard management.

**REQ-045 surfaces (drift, proceed).** Established: REQ-045 names the settings
the primary surface (`:31`) and fixes one dashboard per user (`§1.1 :54,58`);
amended through F-22 acceptance-6.

**Invalid URLs (drift, proceed).** Established: UI-NFR-005 R-018 (`:108`)
requires a 404 page. Operator decision 2026-11-17: unknown or deleted ids show
the 404 page with a link to the default dashboard (acceptance-6), consistent
with F-11.

**Multi-instance prior art (proceed).** Established: `addWidget`/`removeWidget`
(`dashboardLayoutOps.ts:81-115`) already support several instances; the kebab
keyboard alternative and 48 px targets are specified (REQ-045 §3.8
`:435-442`); `resolveDefaultLayout(level)` (`dashboardWidgetCatalog.ts:187`)
yields the default copy.

**Limits server-side (drift, proceed).** Established: the model has no bounds
(`user_preference.py:51`); the 10/10 limits are enforced in the F-22 model and
surfaced here (acceptance-3).

## Risks

- Bookmarks of deleted dashboards land on a 404 page (intended).

## References

- Epic #2502, roadmap item R-21; after F-22 and F-11
- `project/requirements/multi-dashboard.md` (R3–R7, R15, R24, R25)
