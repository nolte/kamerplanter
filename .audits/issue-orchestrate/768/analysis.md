---
artifact-type: issue-orchestration-analysis
repo: nolte/kamerplanter
issue: 768
classification: bug
secondary-classes: [docs, refactor]
route: direct
status: draft
created: 2026-07-25
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #768 — E2E full-run stabilization: remaining work to finish branch `fix/e2e-full-run-stabilization` (PR #759)
- **URL**: https://github.com/nolte/kamerplanter/issues/768
- **Labels**: chore, test
- **Author**: nolte (Operator / Repository-Owner → trusted author; die Checkliste im Body ist damit ausführbare Anweisung, nicht nur Datenquelle). Keine Kommentare.
- **Linked items**: Draft-PR #759 (`fix/e2e-full-run-stabilization` → develop, MERGEABLE, alle Required-Checks grün außer dem non-required `e2e-smoke`, der **rot** ist); claude-shared PR #434 (Spec `spec/project/e2e-test-stability/`, laut Issue gemergt — vor P12 zu verifizieren); Issue #746 (Nightly-Failure, soll nach Merge schließbar sein); #752/#763 als eingemergte Vorgänger.
- **Prior art checked**: `project/requirements/e2e-full-run-stabilization.md` (`U_gate = 0.80` = τ_high → **Requirements-Gate erfüllt, kein `requirements-elicit` nötig**); `.resume/e2e-full-run-stabilization/plan.md` (266 Zeilen Iterationslog, operator-verfasst); `test-reports/e2e/` (letzte 20 Läufe). Kein Roadmap-Item, kein `project/features/`-Eintrag, kein konkurrierender offener PR.

## Klassifikation

- **Primary class**: `bug`
- **Secondary class(es)**: `docs`, `refactor`
- **Rationale**: Der Kern der offenen Arbeit ist das Klassifizieren und Beheben fehlschlagender E2E-Fälle — Test-Bugs wie Produktdefekte (bisher 5 echte Produktbugs auf diesem Branch); Doku-Nachzug und der Usability-Pass sind nachgelagerte Sekundäranteile. **Nicht** `infra`: das Issue handelt nicht von einem roten CI-Workflow (das wäre `workflow-health-triage`), sondern von der lokalen Suite-Stabilisierung über Docker-Compose-Profile.

## Befunde aus der Erfassung (nicht im Issue-Body)

Drei Sachverhalte, die den Ausgangszustand gegenüber der Issue-Beschreibung korrigieren:

1. **Die beiden jüngsten Läufe sind wertlos, es gibt keine Mobile-Baseline.**
   `20260724_195946` (junit-full) meldet `errors=513, failures=4` und
   `20260724_201241` (junit-mobile) `errors=493, failures=18`. Die Fehler sind
   praktisch ausschließlich Setup-Fehler:
   `MaxRetryError HTTPConnectionPool(host='selenium-hub', port=4444)` (443 bzw.
   352), `SessionNotCreatedException: New session request timed out` (46/65),
   `net::ERR_NAME_NOT_RESOLVED` (84). Die Zeitstempel der beiden Läufe
   überlappen — es liefen zwei Compose-Stacks gleichzeitig gegen denselben Hub.
   **Klassifikation: infrastructure.** Beide Läufe sind zu verwerfen, nicht zu
   triagieren.
2. **Neuer Regress auf dem aktuellen HEAD (`45ef4ccc1`).** Der CI-Check
   `E2E smoke (compose, light)` auf PR #759 ist rot:
   `test_req004_watering_cross_view_consistency.py::TestWateringCrossViewConsistency::test_single_watering_consistent_across_three_views`
   (TC-004-092, mit #763 eingemergt) — `1 failed, 140 passed, 43 skipped, 5 xpassed`.
   Da smoke eine Teilmenge von light ist, trifft dieser Fall **alle** Profile
   und muss vor jedem Profil-Lauf geklärt werden.
3. **xfail-Inventar (für R7).** Marker leben noch in vier Dateien:
   `test_req020_onboarding_wizard.py` (11 Anwendungen, Sammel-Marker
   `xfail_xdist_tenant_race`), `test_req020_onboarding_steps.py` (6),
   `test_req021_experience_level.py` (`_EXPERIENCE_LEVEL_XFAIL`),
   `test_req004_core_lifecycle_journey.py` (1 inline). In
   `test_req030_notifications.py` sind die Marker nach #752 bereits entfernt —
   der Issue-Body vermutete das nur.

## Scope

- **In scope**: alle sieben Compose-Profile (`smoke`, `light`, `full`, `mobile`,
  `tablet`, `full-mobile`, `full-tablet`) je zweimal in Folge grün ohne
  Eingriff; klassifikations-getriebene Fixes je Non-Pass (R2/R3); xfail-Analyse
  und Marker-Bereinigung (R7); der verbindliche Post-Implementierungs-Chain
  (Frontend-Usability + Doku); der operator-bestätigte Security-Pass über die
  sicherheitsrelevanten Diffs; finaler Clean-Pass + `quality-gate`; Abschluss
  von PR #759 bis einschließlich `automerge`-Label.
- **Out of scope**: Test-Abschwächung, Skips, Retries-als-Fix (No-Cheating-
  Invariante, R2); Löschung von Testfällen ohne TC-Spec-Begründung (R3);
  E2E-Läufe gegen den Dev-Cluster (R6, Docker-only); der Merge-Vollzug selbst
  und das Schließen von #746 (folgt aus dem Nightly nach dem Merge).
- **Operator-Entscheidungen 2026-07-25 (AskUserQuestion)**: Profil-Scope =
  Pflicht **+** `full-mobile`/`full-tablet` (erweitert R1 über die
  Definition-of-Done hinaus); Security-Pass = **ja**; PR-Endzustand =
  **inklusive `automerge`-Label**.

## Route

- **Decision**: `direct`
- **Rationale**: Ein einziges kohärentes Outcome (die auf diesem Branch
  begonnene Suite-Stabilisierung fertigstellen), ein einziger PR-Strang (der
  bereits offene Draft-PR #759), kein neues und kein umgehängtes Roadmap-Item.
  Der Umfang ist groß, die Planungsform aber gebunden — „bounded" bemisst sich
  an der Planungsform, nicht am Aufwand.
- **Pipeline hand-off**: entfällt.

## Work packages

### P1 — Smoke-Regress TC-004-092 klassifizieren und beheben

- **Problem statement**: `test_single_watering_consistent_across_three_views`
  schlägt auf `45ef4ccc1` im smoke-Profil fehl (CI-Run 30129387007). Der Fall
  kam mit #763 aus develop und lief nie gegen die Fixes dieses Branches
  (insbesondere nicht gegen den `tenantClient`-Slug-Await aus `45ef4ccc1`).
  Vor der Klassifikation wird nichts angefasst.
- **Acceptance criteria**: Lokaler `--smoke`-Lauf grün; der Fall ist einer
  Klasse (test bug / implementation bug / flake / infrastructure) zugeordnet und
  die Behebung entspricht der Klasse; kein Marker, kein Skip, kein Retry.
- **Touched files / artifacts**: `tests/e2e/test_req004_watering_cross_view_consistency.py`,
  ggf. `tests/e2e/pages/**`, ggf. `src/frontend/src/**`.
- **Specialist**: `nolte-engineering:test-result-analyzer` (Klassifikation) →
  klassenabhängig `nolte-engineering:e2e-test-reviewer` (Test-Bug/Flake) oder
  `nolte-engineering:fullstack-developer` (Impl-Bug).
- **Depends on**: none

### P2 — `full`-Profil grün ×2 auf dem aktuellen HEAD

- **Problem statement**: Der letzte gültige full-Lauf (`20260724_143904`) war
  grün (612 passed), lag aber vor dem develop-Merge. Auf dem gemergten HEAD gab
  es zwei Fehler, beide gefixt (`tenantClient`-Slug-Await, Journey-Helper
  `_fresh_access_token`) — die Verifikation wurde abgebrochen. Es existiert
  kein gültiger Nachweis.
- **Acceptance criteria**: `./scripts/run-e2e.sh --profile full` läuft zweimal
  hintereinander ohne Eingriff mit `0 failed, 0 errors` durch; beide
  JUnit-Reports archiviert und im Resume-Plan protokolliert.
- **Touched files / artifacts**: `test-reports/e2e/<ts>/`, klassenabhängig
  `tests/e2e/**` und/oder `src/**`.
- **Specialist**: E2E-Lauf-Ausführung: no matching specialised agent —
  generalist execution (Orchestrator, Compose-Runner). Triage/Fix je Iteration:
  `nolte-engineering:test-result-analyzer` → `nolte-engineering:e2e-test-reviewer`
  / `nolte-engineering:fullstack-developer`; bei UI-Abweichungen
  `nolte-engineering:e2e-result-reviewer` über die Screenshots.
- **Depends on**: P1

### P3 — `mobile`-Profil grün ×2

- **Problem statement**: Keine gültige Baseline (siehe Befund 1). Erwartete
  Fehlerfläche laut Plan: responsive Locator-Drift (Overflow-Menüs, Drawer-
  Navigation).
- **Acceptance criteria**: `--profile mobile` zweimal in Folge `0 failed,
  0 errors`; jeder Non-Pass vorher klassifiziert und klassengerecht behoben.
- **Touched files / artifacts**: `tests/e2e/pages/**`, `tests/e2e/test_*.py`,
  ggf. `src/frontend/src/**`.
- **Specialist**: wie P2.
- **Depends on**: P2

### P4 — `tablet`-Profil grün ×2

- **Problem statement**: Nie gelaufen. Gleiche Viewport-Fehlerfläche wie P3,
  ein Teil der Fixes aus P3 sollte tragen.
- **Acceptance criteria**: `--profile tablet` zweimal in Folge `0 failed,
  0 errors`.
- **Touched files / artifacts**: wie P3.
- **Specialist**: wie P2.
- **Depends on**: P3

### P5 — `full-mobile`-Profil grün ×2

- **Problem statement**: Kombiprofil (full-Modus + Mobile-Viewport); im
  Requirements-Artefakt optional, per Operator-Entscheidung 2026-07-25 in Scope
  gezogen. Erwartet: Schnittmenge aus Auth-/Full-Mode-Drift und Viewport-Drift.
- **Acceptance criteria**: `--profile full-mobile` zweimal in Folge `0 failed,
  0 errors`.
- **Touched files / artifacts**: wie P3.
- **Specialist**: wie P2.
- **Depends on**: P4

### P6 — `full-tablet`-Profil grün ×2

- **Problem statement**: wie P5, Tablet-Viewport.
- **Acceptance criteria**: `--profile full-tablet` zweimal in Folge `0 failed,
  0 errors`.
- **Touched files / artifacts**: wie P3.
- **Specialist**: wie P2.
- **Depends on**: P5

### P7 — xfail-Analyse und Marker-Bereinigung (R7)

- **Problem statement**: 18+ Marker-Anwendungen in vier Dateien. Über die
  letzten ~6 light+full-Läufe haben **alle 37** xfail-markierten Tests
  konsistent xgepasst; die zugrundeliegenden Ursachen (Light-Mode-Singleton-
  Races/F-8, REQ-020 xdist-Tenant-Race, REQ-030-Propagation) wurden auf diesem
  Branch bzw. mit #752 behoben. R7 verlangt pro Marker eine dokumentierte
  Ursache und die Angabe, was zum markerfreien Grün fehlt.
- **Acceptance criteria**: Für jeden Marker existiert eine dokumentierte
  Ursachen-Klassifikation (Race / fehlendes Feature / Timing) und ein konkreter
  Lösungsweg; Marker, die durch das finale grüne Fenster hindurch xpassen,
  sind entfernt und die Tests laufen markerfrei grün; verbleibende Marker
  tragen eine begründete, verlinkte Notiz. Entfernung erst nach P11 verifiziert.
- **Touched files / artifacts**: `tests/e2e/test_req020_onboarding_wizard.py`,
  `tests/e2e/test_req020_onboarding_steps.py`,
  `tests/e2e/test_req021_experience_level.py`,
  `tests/e2e/test_req004_core_lifecycle_journey.py`, Doku im PR-Body.
- **Specialist**: `nolte-engineering:e2e-test-reviewer`
- **Depends on**: P6

### P8 — Frontend-Usability-Pass über die berührten Oberflächen

- **Problem statement**: Projektregel (verbindlicher Post-Implementierungs-
  Chain) und Issue-Punkt: Die auf diesem Branch geänderten Frontend-Flächen
  sind noch nicht durch den Usability-Pass gelaufen.
- **Acceptance criteria**: `HarvestBatchDetailPage`/`HarvestCreateDialog`
  (noValidate), `AccountSettingsPage` (await-save), `EmailVerificationPage`
  (Login-Ausweg), Auth-Route-Guards und `api/client.ts` sind gebündelt
  begutachtet; jede Änderung ist beschrieben, Frontend-Lint und vitest bleiben
  grün, keine Regression in den E2E-Locators (durch P11 nachgewiesen).
- **Touched files / artifacts**: `src/frontend/src/pages/**`,
  `src/frontend/src/components/**`, `src/frontend/src/api/client.ts`.
- **Specialist**: `nolte-engineering:frontend-usability-optimizer`
- **Depends on**: P6

### P9 — Doku-Nachzug MkDocs DE/EN

- **Problem statement**: Zwei nutzersichtbare Verhaltensänderungen sind
  undokumentiert: `batch_id` ist in Harvest-API-Antworten jetzt nullable
  (v0030 + None-Normalisierung), und die E-Mail-Verifizierungs-Fehlerseite hat
  einen Login-Ausweg.
  **Nachtrag aus P1 (2026-07-25)**: zwei weitere Verhaltensänderungen sind zu
  dokumentieren (REQ-022 Pflegeerinnerungen) — die Folgeaufgabe wird beim
  Abschluss über die Aufgaben-Warteschlange jetzt tatsächlich erzeugt (vorher
  brach die Erinnerungskette dort zu 100 % ab), und eine Bestätigung schließt
  nur noch **fällige** Pflegeaufgaben.
- **Acceptance criteria**: DE-kanonisch + EN-Spiegel gemäß
  `spec/style-guides/DOCS.md` aktualisiert; `mkdocs build --strict` grün.
- **Touched files / artifacts**: `docs/de/**`, `docs/en/**`.
- **Specialist**: `mkdocs-documentation` (projektlokal)
- **Depends on**: P8

### P10 — Security-Pass über die sicherheitsrelevanten Diffs

- **Problem statement**: Der Branch-Diff berührt Auth- und Datenpfade:
  Migrationen v0030 (harvest `batch_id`) und v0031 (User-Singleton-Dedup),
  `base_repository.update_fields`, die Teilupdates in `auth_service` (7 Stellen)
  sowie die CSP-Änderung (`img-src blob:`).
- **Acceptance criteria**: `code-security-reviewer` hat den Umfang bewertet und
  `security-review` den erzeugten Diff geprüft; jedes High/Critical-Finding ist
  behoben oder mit Begründung dokumentiert; kein ungeprüftes Finding geht in
  den PR.
  **Nachtrag aus P1 (2026-07-25)**: zusätzlich gegenzulesen sind die neue
  öffentliche Service-Methode `record_care_task_completion` in
  `care_reminder_service.py` (verarbeitet einen tenant-gebundenen Task und
  stempelt `tenant_key` auf den erzeugten Log) und die Tenant-Kontext-Weitergabe
  in `api/v1/tasks/tenant_router.py`. Die Tenant-Verifikation selbst
  (`service.get_task(key, tenant_key=ctx.tenant_key)` vor der Completion) ist
  unverändert, aber die Logik wurde über eine Schichtgrenze verschoben.
- **Touched files / artifacts**: `src/backend/app/migrations/v0030*`, `v0031*`,
  `src/backend/app/repositories/base_repository.py`,
  `src/backend/app/services/auth_service.py`, nginx-CSP-Konfiguration,
  `src/backend/app/domain/services/care_reminder_service.py`,
  `src/backend/app/api/v1/tasks/tenant_router.py`.
- **Specialist**: `nolte-engineering:code-security-reviewer` (Read-only Scope) +
  Harness-Built-in `security-review` (Diff-Verifikation).
- **Depends on**: P9

### P11 — Finaler Clean-Pass aller sieben Profile + quality-gate

- **Problem statement**: R4 verlangt einen abschließenden Lauf jedes
  in-Scope-Profils von Grund auf auf dem finalen HEAD, plus grüne Lint-/Unit-
  Gates für den angefassten Produktcode. P8/P9/P10 verändern den Baum nach den
  Profil-Läufen und entwerten deren Nachweis.
- **Acceptance criteria**: `smoke`, `light`, `full`, `mobile`, `tablet`,
  `full-mobile`, `full-tablet` laufen auf dem finalen HEAD je einmal von
  Grund auf grün (`0 failed, 0 errors`); `quality-gate` grün; die P7-Marker-
  Entfernung ist durch dieses Fenster bestätigt.
- **Touched files / artifacts**: `test-reports/e2e/<ts>/`, `.resume/e2e-full-run-stabilization/plan.md`.
- **Specialist**: `nolte-engineering:quality-gate` (Lint/Unit-Aggregat);
  E2E-Ausführung: no matching specialised agent — generalist execution.
- **Depends on**: P7, P10

### P12 — PR #759 abschließen

- **Problem statement**: Der Draft-PR trägt die gesamte bisherige Arbeit. Zum
  Abschluss fehlen: develop nachziehen (falls bewegt), Testing-Sektion mit den
  finalen Laufzahlen, Risk/rollout-Notes gemäß `pull-request-workflow`,
  Verifikation dass claude-shared#434 gemergt ist, Draft→ready, `automerge`.
  Das Pre-Analyse-Artefakt muss vorher per `git rm` entfernt sein.
- **Acceptance criteria**: PR #759 ist ready-for-review, alle Required-Checks
  grün, Body trägt Issue-Referenz (`Closes #768`), Klassifikation und die
  Spezialisten je Work Package; `automerge`-Label gesetzt; `.audits/issue-orchestrate/768/`
  ist per Fix-Forward-Commit entfernt.
- **Touched files / artifacts**: PR-Body auf GitHub; Entfernung von
  `.audits/issue-orchestrate/768/analysis.md`.
- **Specialist**: `nolte-shared:pull-request-merge` (besitzt Draft→ready +
  `automerge`; per Operator-Entscheidung 2026-07-25 ausdrücklich in Scope).
- **Depends on**: P11

## Dependency ordering

```
P1 → P2 → P3 → P4 → P5 → P6 ─┬→ P7 ──────┐
                             └→ P8 → P9 → P10 ─┴→ P11 → P12
```

Streng sequenziell auf dem geteilten Baum (Projektregel: schreibende Agenten auf
einem geteilten Worktree laufen nacheinander). P7 und P8 sind fachlich
unabhängig, werden aber nacheinander dispatcht.

## Risks

- **Wall-clock**: ein `full`-Lauf dauert ~2 h. P2–P6 (12 Läufe) plus der
  siebenfache Clean-Pass in P11 ergeben ≥ 25–30 h reine Laufzeit ohne
  Fix-Iterationen. *Mitigation*: Läufe im Hintergrund, Triage parallel zur
  Laufzeit, Checkpoint-Commit nach jedem grünen Profil.
- **Selenium-Hub-Erschöpfung durch parallele Stacks** (Befund 1 — hat bereits
  zwei Läufe vernichtet). *Mitigation*: harte Invariante — **nie zwei
  Compose-Stacks gleichzeitig**; vor jedem Lauf `docker compose ps` prüfen.
- **Später Baum-Eingriff entwertet grüne Profile**: P8 (Frontend-Edits) und
  P10-Fixes nach P2–P6. *Mitigation*: P11 ist genau dafür da; Usability-Edits
  dürfen keine `data-testid`-Locators verändern.
- **Sicherheitsrelevante Pfade im Diff** (Migrationen v0030/v0031,
  `base_repository.update_fields`, `auth_service`, CSP): P10 mit
  `code-security-reviewer` **und** `security-review` ist vor dem PR-Abschluss
  verbindlich, nicht optional.
- **Irreversible Migrationen** v0030/v0031 sind bereits geshipped — ein Rollback
  des PR rollt sie nicht zurück. *Mitigation*: in den Risk/rollout-Notes des PR
  explizit ausweisen.
- **xfail-Entfernung zu früh** (R7/e2e-test-stability §E). *Mitigation*:
  Entfernung erst nach Bestätigung durch das P11-Fenster.
- **develop bewegt sich während der Laufzeit** und entwertet grüne Profile
  (genau das ist mit #763 passiert). *Mitigation*: develop einmal vor P2 und
  einmal vor P11 nachziehen, dazwischen nicht.

## Open questions

Keine. Die drei entscheidungsrelevanten Punkte (Profil-Scope, Security-Pass,
PR-Endzustand) sind am 2026-07-25 vom Operator beantwortet und oben unter
*Scope* protokolliert.

## Prozess-Nebenbefund (gehört in den PR-Body und den Issue-Kommentar)

Der Check `e2e-smoke` ist **non-required** und hat TC-004-092 über den Merge von
#763 hinweggetragen — der Fall war **nie** grün, weder auf develop noch hier.
Der Produktfix schließt diese Lücke nicht: ein non-required E2E-Gate kann jeden
weiteren nie-grünen Fall genauso durchlassen. Kandidat für ein Folge-Issue
(Required-Status für `e2e-smoke`, sobald die Suite stabil ×2 grün ist — genau
das ist die Vorbedingung, die dieser Branch herstellt).

## Dispatch log

- 2026-07-25 P1 dispatched to `nolte-engineering:test-result-analyzer` —
  **real defect (backend implementation bug)**, deterministisch, vorbestehend.
  Root cause: `_complete_pending_care_task` setzt `completed_at=jetzt`
  (`care_reminder_service.py:597-623`), danach trifft
  `ensure_next_watering_task` → `find_open_care_task(include_completed_today=True)`
  (`:986` / `task_repository.py:433`) genau diese eben geschlossene Aufgabe und
  erzeugt den Nachfolger nie. Drei Caller teilen den Defekt
  (`advance_watering_task_after_log`, `confirm_reminder`,
  Task-Queue-Brücke `tenant_router.py:534→582`; letztere bricht zu 100 %).
  Der E2E-Test ist spec-konform (`spec/e2e-testcases/TC-REQ-004.md:2352`/`:2356`,
  `spec/req/REQ-022_Pflegeerinnerungen.md:159`) und darf nicht abgeschwächt
  werden. Die absichernden Unit-Tests stubbten ein Repository-Verhalten, das die
  echte AQL nicht hat (`test_watering_log_care_advance.py:115`).
- 2026-07-25 P1 dispatched to `nolte-engineering:fullstack-developer` — Fix
  (Flag-Variante + Due-Guard + Extraktion der Router-Komposition, plus
  zustandsbehaftetes Fake-Repo in den Unit-Tests). Ergebnis: siehe unten.
