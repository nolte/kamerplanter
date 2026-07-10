---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: 437
classification: "bug"
secondary-classes: []
route: "direct"
status: draft
created: "2026-07-10"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #437 — fix(dashboard): edit mode widget overlap, missing md/sm repack, and low-visibility widget menu button
- **URL**: https://github.com/nolte/kamerplanter/issues/437
- **Labels**: bug
- **Linked items**: none (keine Kommentare, keine verlinkten Issues/PRs, kein Milestone)
- **Prior art checked**: `gh pr list --state open` — kein offener PR referenziert #437 oder das Dashboard; kein `project/features/`-Eintrag, kein Roadmap-Item. Betroffene Dateien real gegengelesen; die Root-Cause-Analyse des Issues deckt sich exakt mit dem Code. Feature-Hintergrund: REQ-045 Dashboard-Personalisierung (PR #378).

## Classification

- **Primary class**: bug
- **Secondary class(es)**: none
- **Rationale**: Drei konkrete Fehlverhalten im implementierten Edit-Mode-Grid (Overflow, fehlender Repack, unsichtbarer Menü-Button) — reine Korrektur bestehenden Verhaltens, kein neues Feature.

## Requirements gate

- **Artefakt vorhanden**: nein — kein `project/requirements/*.md` deckt #437 ab.
- **Entscheidung**: **Operator-Override** (protokolliert per `requirements-elicitation` §H Consumer-Vertrag, das Override statt hart-blockierend erlaubt).
- **Begründung**: Das Issue liefert außergewöhnlich präzise Anforderungen als Prosa — Reproduktionsschritte, Root-Cause pro Datei:Zeile und einen konkreten Fix-Vorschlag je Teilproblem. Die Akzeptanzkriterien der Arbeitspakete unten leiten sich direkt aus der im Issue benannten, verstandenen Soll-Verhaltensweise (Parität mit dem bereits korrekten Readonly-Grid) ab, nicht aus einer Vermutung.
- **Operator-Bestätigung**: 2026-07-10, Gate „Requirements-Gate → Operator-Override".

## Scope

- **In scope**: Angleichung des Edit-Mode-Dashboard-Grids an das bereits korrekte Readonly-Grid — (1) content-getriebene Widget-Höhe statt fixer `h × ROW_HEIGHT`-Box, (2) `packByReadingOrder`-Repack + explizites `compactType` für abgeleitete md/sm-Breakpoints, (3) sichtbare Affordance des `⋮`-Widget-Menü-Buttons. Rein Frontend unter `src/frontend/src/`.
- **Out of scope**: Readonly-Grid-Verhalten (bereits korrekt), Backend/Persistenz der Layouts, neue Widget-Typen, Redux-Slice-Logik. Keine Änderung an `dashboardLayoutOps.ts`-Signaturen außer Konsum der bestehenden `packByReadingOrder`.

## Route

- **Decision**: direct
- **Rationale**: Ein kohärentes Goal-Outcome (Edit-Mode-Rendering korrekt), ein einzelner PR-Strang, kein neues oder umgetargetetes Roadmap-Item → bounded. Alle drei Teilprobleme liegen im selben Frontend-Modul.
- **Pipeline hand-off**: n/a
- **Operator-Bestätigung**: 2026-07-10, Gate „Scope & Route → Ja, direkt umsetzen".

## Work packages

### P1 — Edit-Grid: Content-Overflow/Overlap beseitigen

- **Problem statement**: `DashboardEditGrid.tsx` boxt jedes Widget hart auf `h × ROW_HEIGHT` (44px). Widgets mit realem Inhalt höher als `h × 44px` (z. B. *Winter Protection Overview* +55px, *Setup progress* +60px) laufen über und überlappen das darunterliegende Widget. Das Readonly-Grid löst das via `gridAutoRows: minmax(MIN_ROW_HEIGHT, min-content)` (`DashboardReadonlyGrid.tsx:68`).
- **Acceptance criteria**: Im Edit-Mode überläuft der gerenderte Inhalt von *Winter Protection Overview* und *Setup progress* nicht mehr die Card-Unterkante und überlappt das Nachbar-Widget nicht (Box-Höhe ≥ Content-Höhe). Verifizierbar durch einen Vitest/RTL-Test, der ein Widget mit content-höher-als-`h` rendert und prüft, dass die Item-Box nicht kleiner als der Inhalt geboxt wird (bzw. `h` den Inhalt deckt) — plus visuelle Bestätigung im Browser (kein Overlap bei 15 aktiven Widgets, lg).
- **Touched files / artifacts**: `src/frontend/src/components/dashboard/DashboardEditGrid.tsx`; ggf. `src/frontend/src/config/dashboardWidgetCatalog.ts` (falls `h`-Defaults nachgezogen werden); Test unter `src/frontend/src/test/components/dashboard/`.
- **Specialist**: `fullstack-developer` (project-distributed; description-match: React/MUI-Komponenten-Implementierung im definierten Tech-Stack)
- **Depends on**: none

### P2 — Edit-Grid: md/sm-Repack + compactType

- **Problem statement**: `DashboardEditGrid.tsx` nutzt `placementsForBreakpoint(...)` **ohne** `packByReadingOrder(...)` und klemmt nur `w = min(p.w, cols)`, lässt aber die `lg`-abgeleiteten `x`-Koordinaten stehen → beim Umschalten auf Tablet (md, 8 Spalten) / Mobile (sm, 4 Spalten) große Lücken und Overlaps. Kein `compactType` gesetzt. Das Readonly-Grid packt korrekt (`DashboardReadonlyGrid.tsx:48-50`) via bereits vorhandenem `packByReadingOrder` (`dashboardLayoutOps.ts:25`).
- **Acceptance criteria**: Für einen Breakpoint ohne eigene Placements wendet das Edit-Grid `packByReadingOrder(placements, cols)` an (analog Readonly-Grid) und setzt explizit `compactType="vertical"`. Beim Umschalten auf Tablet/Mobile im Edit-Mode sind Widgets ohne verstreute Vertikal-Lücken/Overlaps gepackt. Verifizierbar durch Vitest-Test: derived md/sm-Layout des Edit-Grids == `packByReadingOrder(lg, cols)` (keine `x`-Koordinaten > `cols`).
- **Touched files / artifacts**: `src/frontend/src/components/dashboard/DashboardEditGrid.tsx`; Test unter `src/frontend/src/test/components/dashboard/`.
- **Specialist**: `fullstack-developer`
- **Depends on**: none (unabhängig von P1, aber selbe Datei — sequenziell mit P1 im selben Pass)

### P3 — Widget-Menü-`⋮`-Button sichtbar machen

- **Problem statement**: Der `⋮`-Button (`WidgetFrame.tsx:77-87`) ist ein Default-MUI-`IconButton` mit `MoreVertIcon` (`rgba(0,0,0,0.54)`) ohne Hintergrund/Rahmen auf weißer Card → kaum sichtbar, unklare Trennung vom Card-Titel.
- **Acceptance criteria**: Der `⋮`-Button erhält sichtbare Affordance auf weißer Card (kontrastierender/Hover-Backdrop, stärkere Icon-Farbe und/oder klare Trennung vom Titel) und bleibt touch-freundlich (≥48px Trefferfläche, Mobile-First-Guideline). Bestehendes `aria-label` (`dashboard.edit.widgetMenu`) und `data-testid` (`widget-menu-<key>`) bleiben erhalten; `WidgetFrame.test.tsx` bleibt grün. Kein Regress bei Kontrast (WCAG AA für den Icon-Vordergrund).
- **Touched files / artifacts**: `src/frontend/src/components/dashboard/WidgetFrame.tsx`; ggf. `src/frontend/src/test/components/dashboard/WidgetFrame.test.tsx`.
- **Specialist**: `fullstack-developer` (Alternative: `frontend-usability-optimizer` — description-match für MUI-Usability-Politur; im selben PR-Strang jedoch an einen Spezialisten gebündelt, um Shared-Tree-Write-Konflikte auf demselben Modul zu vermeiden)
- **Depends on**: none

## Dependency ordering

P1, P2, P3 sind fachlich unabhängig (DAG ohne Kanten). P1 und P2 editieren dieselbe Datei (`DashboardEditGrid.tsx`); daher **ein** `fullstack-developer`-Dispatch, der alle drei Pakete kohärent im selben Worktree-Pass umsetzt (sequenziell), statt paralleler Agenten auf geteiltem Tree. Reihenfolge im Pass: P1 → P2 → P3.

## Risks

- **RGL-Fixed-Row-Height-Kopplung (P1)**: react-grid-layout berechnet DnD/Resize-Geometrie aus `rowHeight`; content-getriebene Höhe wie im reinen CSS-Readonly-Grid ist nicht 1:1 übertragbar. Mitigation: Spezialist prüft beide im Issue vorgeschlagenen Wege — content-getriebene Item-Höhe **oder** garantieren, dass gespeichertes `h` den Content deckt — und wählt den, der DnD/Resize nicht bricht; Regressionstest für Drag/Resize.
- **Breakpoint-Repack ändert gespeicherte Placements nicht (P2)**: Repack ist nur Anzeige-Ableitung für Breakpoints ohne eigene Placements; darf keine `lg`-Placements überschreiben. Mitigation: Nur den Render-Pfad angleichen (analog Readonly), Persistenz-Semantik von `setBreakpointPlacements` unverändert lassen.
- **Kein security-sensitiver Pfad berührt** (reine FE-Präsentation) → `code-security-reviewer`/`security-review` nicht erforderlich. `quality-gate` (eslint/tsc/vitest) ist Pflicht vor PR.
- **UI-Änderung**: nach Implementierung UI-Review (mobile-first, Kontrast) gemäß Projekt-Konvention vor PR.

## Open questions

none — Anforderungen durch Operator-Override abgedeckt; Fix-Wege im Issue vorgezeichnet.

## Dispatch log

- 2026-07-10 P1+P2+P3 dispatched to `fullstack-developer` (project-distributed, bundled) — umgesetzt: content-getriebene Tile-Höhe via neuem Hook `useContentRowFloors.ts` + `rowsForContentHeight` (P1); geteilter Helper `deriveBreakpointPlacements` + `compactType="vertical"` (P2); sichtbarer `⋮`-Button mit Paper-Backdrop/Theme-Tokens/48px (P3). Neue Tests (`DashboardEditGrid.test.tsx`, erweitert `dashboardLayout.test.ts`, `WidgetFrame.test.tsx`). quality-gate grün (eslint 0 errors, tsc clean, vitest pass).
- 2026-07-10 UI-Review dispatched to `frontend-usability-optimizer` — 1 MEDIUM-Finding (Titel-Verdeckung durch opaken Menü-Backdrop bei minimal geschrumpften Widgets) minimal-invasiv gefixt in `WidgetFrame.tsx` (Hit-Area 48px erhalten, sichtbare Fläche auf 34px-Innenkreis reduziert); übrige Komponenten ohne Handlungsbedarf. quality-gate erneut grün.

## Verification

- **quality-gate**: PASS — `npm run lint` 0 errors (nur vorbestehende Warnings in fremden Dateien), `tsc --noEmit` clean, `vitest run` (dashboard + layout suites) grün.
- **security**: nicht erforderlich — reine Frontend-Präsentationsänderung, kein security-sensitiver Pfad berührt (keine Auth/Datenzugriff/AI/RAG). `code-security-reviewer`/`security-review` entfällt regelkonform.
- **docs**: nicht erforderlich — kein neues API/Config/Endpoint; Verhaltensangleichung an bereits dokumentiertes Readonly-Grid.
