---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: 438
classification: bug
secondary-classes: []
route: direct
status: completed
created: 2026-07-10
pr: https://github.com/nolte/kamerplanter/pull/448
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #438 — `fix(dashboard): "Tasks today" widget ignores overdue tasks — always 0 with an overdue-only backlog`
- **URL**: https://github.com/nolte/kamerplanter/issues/438
- **Labels**: bug
- **Linked items**: keine (keine verlinkten Issues/PRs; `gh pr list --search 438` leer)
- **Prior art checked**: Kein offener/gemergter PR adressiert #438. Benachbartes
  Requirement-Artefakt `project/requirements/dashboard-metrics-zero.md` behandelt
  einen **anderen** Bug (hard `0` durch fehlende Repo-`count_*`-Methoden, gefixt via
  #399); #438 ist der distinkte „overdue wird im `tasks_today`-Slice verschluckt"-Bug.
  Kein Roadmap-Item / Feature deckt ihn ab.

## Requirements gate

- **Requirement-Artefakt für #438**: keines mit `U_gate ≥ τ_high` vorhanden.
- **Entscheidung (Operator-Gate, 2026-07-10)**: **expliziter Operator-Override** des
  Requirements-Elicitation-Consumer-Vertrags. Begründung: Das Issue liefert Root
  Cause auf Datei:Zeile, die betroffenen Dateien und die Akzeptanz bereits
  vollständig und wurde gegen den aktuellen Code verifiziert (alle referenzierten
  Stellen bestätigt); ein `requirements-elicit`-Lauf würde nur duplizieren. Kein
  Elicit-Dispatch.

## Classification

- **Primary class**: bug
- **Secondary class(es)**: none
- **Rationale**: Falsches/irreführendes Read-Model — der berechnete `overdue_tasks`-Count
  wird im tenant-scoped `tasks_today`-Slice verworfen; kein neues Feature, keine Spec-Änderung.

## Scope

- **In scope**: Der bereits berechnete `overdue_tasks`-Count wird im `tasks_today`-Slice
  des tenant-scoped Dashboard-Aggregats mitgeliefert und als zweites, ehrliches Stat-Tile
  („Überfällig") neben „Heute fällig" angezeigt. Passendes i18n-Metric-Label (en + de).
  Widget-Beschreibung mit dem tatsächlichen Verhalten in Einklang halten.
- **Out of scope**:
  - Semantik-Änderung von `count_open_due_on` (Ansatz B, `<= today`) — vom Issue
    abgeraten, per Operator-Gate verworfen. „Heute fällig" behält seine wörtliche Bedeutung.
  - Der globale `DashboardCountsResponse` (`api/v1/dashboard/router.py`), der
    `overdue_tasks` weiterhin exponiert — unverändert; unvollständige Migration bleibt
    außerhalb des Bug-Scopes.
  - `recent_activities` / Activity-Event-Log — unberührt.

## Route

- **Decision**: direct
- **Rationale**: Ein kohärentes Goal-Outcome (Dashboard zeigt Überfällige ehrlich an),
  ein einzelner PR-Strang, kein neues oder umgetargetetes Roadmap-Item → bounded → direkt.
- **Pipeline hand-off**: n/a

## Work packages

### P1 — `overdue_tasks` als zweites Stat-Tile im `tasks_today`-Widget surfacen

- **Problem statement**: Der tenant-scoped `tasks_today`-Slice
  (`api/v1/dashboard/tenant_router.py`, `_slice_summary_for`, case `"tasks_today"`)
  gibt nur `{open_tasks_today, upcoming_tasks}` zurück und verwirft das bereits in
  `DashboardCounts.overdue_tasks` berechnete Feld (`domain/services/dashboard_service.py`,
  `count_overdue` in `data_access/arango/task_repository.py`). Bei einem rein
  überfälligen Backlog liest das prominenteste Task-Widget dauerhaft `0`, obwohl die
  eigene Beschreibung „Tasks due and overdue today." Overdue explizit verspricht.
- **Acceptance criteria**:
  1. `GET /api/v1/t/{tenant_slug}/dashboard/aggregated?widgets=tasks_today` liefert im
     `tasks_today`-Payload ein `overdue_tasks`-Feld mit dem Wert aus `counts.overdue_tasks`
     (im Prod-Szenario `15`), zusätzlich zu `open_tasks_today` und `upcoming_tasks`.
  2. `open_tasks_today` bleibt unverändert `== today`-Semantik (Ansatz A) — keine
     Änderung an `count_open_due_on`.
  3. i18n-Label `dashboard.widgets.tasks_today.metrics.overdue_tasks` existiert in
     `en/translation.json` und `de/translation.json` (z. B. „Overdue" / „Überfällig").
  4. Die Widget-`description` (en + de) beschreibt das tatsächliche Verhalten
     konsistent (getrennte Zahlen „heute fällig" und „überfällig").
  5. `GenericWidget` rendert dadurch automatisch ein zweites Stat-Tile; kein Renderer-Umbau nötig.
  6. Backend- + Frontend-Tests grün; ein Test deckt ab, dass der `tasks_today`-Slice
     `overdue_tasks` enthält (Regressionsschutz gegen erneutes Verwerfen).
- **Touched files / artifacts**:
  - `src/backend/app/api/v1/dashboard/tenant_router.py` (`_slice_summary_for`, case `tasks_today`)
  - `src/frontend/src/i18n/locales/en/translation.json` (`dashboard.widgets.tasks_today`)
  - `src/frontend/src/i18n/locales/de/translation.json` (Mirror)
  - Tests: Backend-Dashboard-Slice-Test + ggf. FE-Widget-Test
- **Specialist**: `fullstack-developer` (project-local; per Runtime-Glob aufgelöst —
  Description nennt exakt den Stack Python/FastAPI + React/MUI/i18n)
- **Depends on**: none

## Dependency ordering

P1 (einzelnes atomares Paket; BE-Feld + FE-Label + Beschreibung landen zusammen,
da das Label ohne das Feld nichts anzeigt und umgekehrt).

## Risks

- **Doppel-Anzeige von Tasks**: Gering. `GenericWidget` zeigt bei numerischem Payload
  nur Stat-Tiles, keine Listenzeilen (`upcoming_tasks` lebt im `next_calendar_events`-Widget).
  Zweites Tile ist rein additiv. Mitigation: FE-Test auf zwei Tiles.
- **i18n-Parität**: en/de müssen synchron erweitert werden (NFR-003 / DOCS-Konvention).
  Mitigation: beide Locales im selben Paket, Akzeptanzkriterium 3.
- **Kein security-sensitiver Pfad**: Der Fix ist tenant-scoped read-only Aggregation;
  `overdue_tasks` stammt aus demselben tenant-gefilterten `count_overdue`. Kein
  Cross-Tenant-Leak eingeführt. `code-security-reviewer`/`security-review` daher nicht
  zwingend, wird aber bei Bedarf im Verify-Schritt bewertet.

## Open questions

- keine (beide Weichenstellungen — Requirements-Override + Ansatz A — per Operator-Gate
  am 2026-07-10 entschieden).

## Dispatch log

- 2026-07-10 P1 dispatched to `fullstack-developer` — DONE. BE: `tasks_today`-Slice in
  `tenant_router.py` trägt jetzt `overdue_tasks: counts.overdue_tasks`. FE i18n en/de:
  `dashboard.widgets.tasks_today.metrics.overdue_tasks` („Overdue"/„Überfällig");
  `description` war bereits konsistent. Tests: neuer BE-API-Test
  `tests/api/test_dashboard_aggregated_router.py` (2 Fälle: overdue-only + getrennte Zahlen),
  FE `GenericWidget.test.tsx` um Zwei-Tile-Fall erweitert. Backend 12 passed / Frontend 8
  passed; ruff/eslint/tsc grün. Kein Security-Pfad (kein neuer Query, tenant-gefilterter Count).
