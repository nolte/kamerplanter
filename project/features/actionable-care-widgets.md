---
id: F-24
title: Handlungsfähige Pflege-Widgets
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
    - kind: prior-art
      target: src/backend/app/api/v1/care_reminders/router.py:143
      resolution: proceed
      evidence: "Confirm (:143) and snooze (:173, snooze_days 1..7, schemas.py:130-132), GET care-reminders/dashboard (tenant_router.py:13), task complete (tasks/tenant_router.py:749), /queue with location_key (:529-539), /overdue (:604); FE thunks confirmCareReminder/snoozeCareReminder (careRemindersSlice.ts:45,60) are unused outside the slice."
    - kind: drift
      target: src/backend/app/api/v1/care_reminders/schemas.py:148
      resolution: proceed
      evidence: "CareDashboardEntryResponse has no location or photo and the endpoint has no time range; operator decision: extend the endpoint."
    - kind: drift
      target: src/backend/app/api/v1/dashboard/tenant_router.py:92
      resolution: proceed
      evidence: "aggregated slicing and useWidgetPayload(widgetKey) (DashboardDataContext.tsx:101) are keyed by widget type; operator decision: each instance loads its own data with its filters."
    - kind: drift
      target: spec/req/REQ-009_Dashboard.md:150
      resolution: proceed
      evidence: "#508: task tiles exclude care_reminder tasks; tasks_today keeps that exclusion."
    - kind: prior-art
      target: F-9
      resolution: proceed
      evidence: "F-9 acceptance-1 routes done/skip/reschedule through the CompletionTransitionService; F-24 only consumes the endpoints — re-check if F-9 changes their contracts."
    - kind: drift
      target: src/backend/app/api/v1/care_reminders/router.py:147
      resolution: proceed
      evidence: "Confirm/snooze require GROWER (:147, :177); operator decision: viewers see no action buttons."
    - kind: drift
      target: src/backend/app/domain/services/dashboard_widget_catalog.py:88
      resolution: proceed
      evidence: "plant_grid is EXPERT in BE and FE and missing from REQ-009 §1.6:171-187; acceptance-6 changes BE, FE and REQ-009."
    - kind: prior-art
      target: src/frontend/src/components/dashboard/widgetRegistry.ts:47
      resolution: proceed
      evidence: "tasks_today, care_reminders, active_plants_summary run on GenericWidget (rows from upcoming_tasks; care_reminders only a count, tenant_router.py:105-106) — scope of 'replace' established."
---

## Description

Die Widgets „Aufgaben heute“, „Pflege-Erinnerungen“ und „Pflanzen-Übersicht“
zeigen heute vor allem Zahlen und Titel. Um eine Pflanze zu gießen oder eine
Aufgabe abzuhaken, muss man erst in eine andere Ansicht wechseln, und wer nur
einen Bereich sehen will, kann nicht filtern.

Nach dieser Änderung zeigen die drei Widgets, um welche Pflanze es geht, wann
etwas fällig ist und wie dringend; Überfälliges ist hervorgehoben. Aufgaben
lassen sich direkt abhaken, Pflege-Erinnerungen bestätigen oder auf später
verschieben. Jedes Widget lässt sich auf einen Standort, eine Pflegeart oder
einen Zeitraum einstellen, sodass man es mehrfach nutzen kann — etwa
„Gewächshaus“ und „Balkon“ nebeneinander. Wer nur Leserechte hat, sieht die
Angaben ohne Aktionsknöpfe. Die Pflanzen-Kacheln gehören schon für Einsteiger
zum Standard.

## Acceptance criteria

- [ ] **acceptance-1** „Aufgaben heute“ zeigt fällige und überfällige Aufgaben mit Pflanze bzw. Standort, Fälligkeit und Dringlichkeit (Überfälliges hervorgehoben), ohne Pflegeaufgaben doppelt zu zeigen; eine Aufgabe lässt sich abhaken oder per Tipp öffnen; einstellbar sind Standort, Anzahl und ob Überfälliges erscheint.
- [ ] **acceptance-2** „Pflege-Erinnerungen“ zeigt Gießen, Düngen und Umtopfen der kommenden Tage mit Foto bzw. Name und Fälligkeit; eine Erinnerung lässt sich bestätigen oder verschieben; einstellbar sind Standort, Pflegeart und Zeitraum (heute, 3 oder 7 Tage).
- [ ] **acceptance-3** „Pflanzen-Übersicht“ zeigt die Anzahl je Phase oder je Standort und die Pflanzen mit Handlungsbedarf (überfällige Aufgabe oder Pflege) mit Link zur Pflanze bzw. zur gefilterten Liste; einstellbar ist die Gruppierung.
- [ ] **acceptance-4** Mehrere Instanzen desselben Widgets zeigen jeweils die Daten ihres eigenen Filters; alle Aktionen laufen über die bestehenden Aufgaben- und Pflege-Schnittstellen, ohne Pflegelogik in der Oberfläche.
- [ ] **acceptance-5** Wer nur Leserechte hat, sieht die Widgets ohne Aktionsknöpfe; jedes Widget hat einen hilfreichen Leer-, Lade- und Fehlerzustand.
- [ ] **acceptance-6** Die Pflanzen-Kacheln sind ab der Stufe „Einsteiger“ Teil des Standard-Dashboards.

## Test hooks

- **acceptance-1** — vitest on the new `TasksTodayWidget` (#508 exclusion, done action, settings) — pending
- **acceptance-2** — backend test of the extended care-dashboard endpoint (location, photo, range) + vitest confirm/snooze — pending
- **acceptance-3** — backend test of "needs action" derivation + vitest links/grouping — pending
- **acceptance-4** — vitest: two instances with different location filters fetch different data — pending
- **acceptance-5** — vitest with viewer role (no buttons) and empty/loading/error states — pending
- **acceptance-6** — catalog contract test (`plant_grid` level = beginner in FE and BE) — pending

## Consistency notes

**Endpoints exist (prior-art, proceed).** Established: confirm and snooze
(`care_reminders/router.py:143,173`, `snooze_days` 1..7 at `schemas.py:130-132`),
the care dashboard (`care_reminders/tenant_router.py:13`), task complete
(`tasks/tenant_router.py:749`), the queue with `location_key` (`:529-539`) and
overdue (`:604`) exist; the FE thunks (`careRemindersSlice.ts:45,60`) are
unused so far.

**Care dashboard data (drift, proceed).** Established:
`CareDashboardEntryResponse` (`schemas.py:148`) has no location or photo and
no time range. Operator decision 2026-11-17: extend the endpoint (acceptance-2);
computing the range in the frontend would violate acceptance-4.

**Per-instance data (drift, proceed).** Established: the aggregate and
`useWidgetPayload(widgetKey)` (`dashboard/tenant_router.py:92`,
`DashboardDataContext.tsx:101`) are keyed by widget type. Operator decision
2026-11-17: each instance loads its own data with its filters (acceptance-4).

**Care tasks not twice (drift, proceed).** Established: REQ-009 (`:150`, #508)
excludes `care_reminder` tasks from task tiles; acceptance-1 keeps it. Whether
`/tasks/queue` already excludes them is unestablished and checked in the
implementation.

**F-9 boundary (prior-art, proceed).** Established: F-9 acceptance-1 routes
done/skip/reschedule through the `CompletionTransitionService`. Operator
decision 2026-11-17: F-24 only consumes the endpoints and is re-checked if F-9
changes their contracts.

**Viewer actions (drift, proceed).** Established: confirm and snooze require
GROWER (`care_reminders/router.py:147,177`). Operator decision 2026-11-17:
viewers see no action buttons (acceptance-5). The role for task complete is
unestablished and checked in the implementation.

**plant_grid default (drift, proceed).** Established: `plant_grid` is expert
in BE and FE (`dashboard_widget_catalog.py:88`) and missing from REQ-009 §1.6
(`:171-187`). Acceptance-6 changes BE, FE and REQ-009; the visible change for
users without a stored layout is accepted (see F-22).

**GenericWidget replacement (prior-art, proceed).** Established: the three
widgets run on `GenericWidget` (`widgetRegistry.ts:47`), `care_reminders`
only as a count (`dashboard/tenant_router.py:105-106`).

## Risks

- Per-instance fetching raises the number of requests on dashboards with many widgets; caching per filter mitigates it.

## References

- Epic #2502, roadmap item R-21; after F-22 (config schema)
- `project/requirements/multi-dashboard.md` (R10–R14, R20, R26, R27)
