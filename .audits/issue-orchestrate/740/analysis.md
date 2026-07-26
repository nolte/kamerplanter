---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "740"
classification: "bug"
secondary-classes: []
route: "direct"
status: draft
created: "2026-07-23"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #740 — [e2e-nightly] Nightly E2E run failed
- **URL**: https://github.com/nolte/kamerplanter/issues/740
- **Labels**: e2e-nightly
- **Linked items**: PR #732 (E2E-CI-Einführung, gemergt — hat die Failures erstmals sichtbar gemacht); Run 30035004437 (`profile=light`, Artifact `e2e-nightly-reports-light`)
- **Prior art checked**: `project/requirements/e2e-selenium-executability.md` (Methodik-Basis, operator-bestätigt), `project/requirements/e2e-ci-selenium.md` (CI-Scope), Smoke-Subset grün auf develop; keine offenen PRs zu den 13 Tests

## Classification

- **Primary class**: bug
- **Secondary class(es)**: none
- **Rationale**: 13 Tests der vollen light-Suite scheitern durch Test-vs-Implementierung-Drift (bzw. ggf. echte App-Regressionen — trennt P1); der CI-Mechanismus selbst funktioniert wie designt, daher NICHT infra/workflow-health.

## Scope

- **In scope** (operator-bestätigt 2026-07-23): Die 13 roten Tests auf **grün-oder-erklärt** bringen. Als **Test-Drift** klassifizierte Fehler werden im Test-Code (Page-Objects/Tests) minimal-invasiv gefixt (R2 der Requirement-Basis); nicht-verhaltensändernde Testbarkeits-Affordances im App-Code sind erlaubt (R6). Ein PR, `Closes #740`.
- **Out of scope**: Fachliche App-Bug-Fixes — als **echte Regression** klassifizierte Fehler werden als separate GitHub-Issues dokumentiert, nicht hier gepatcht (R3). Keine Test-Rewrites, keine Änderungen an Workflows/CI aus #732.

## Requirements gate

- Basis: `project/requirements/e2e-selenium-executability.md` (U_gate 0.80 ≥ τ_high), per Operator-Entscheid 2026-07-23 übernommen; dessen R2/R3/R6 gelten unverändert, die historische „kein CI-Job"-Grenze (R4) ist durch `project/requirements/e2e-ci-selenium.md` (#732) ersetzt.

## Route

- **Decision**: direct
- **Rationale**: Ein kohärentes Ergebnis (Nightly-light grün-oder-erklärt), ein PR-Strang, kein Roadmap-Item.

## Failure inventory (aus Artifact `e2e-nightly-reports-light`, Run 30035004437)

| Cluster | Tests | Signatur |
|---|---|---|
| C1 Mixing | TC-REQ-004-065/066/067/068 (Protocol) + 087/088 (Safety) | Nach Calculate/Validate erscheint **kein** Result (weder Alert noch Snackbar), `len(results) == 0` |
| C2 Experience-Level | TC-REQ-021-009/013/014 | `/kalender` nicht sichtbar (intermediate); `scientific_name` (intermediate) / `root_type` (expert) nicht sichtbar im Species-Dialog — Verdacht: Formular-Umbau (#731 `seed_type`) bzw. Tiering-/Modul-Drift |
| C3 Care-Profile | TC-REQ-022-006 | `ValueError: invalid literal for int(): 'MÄR\n3'` — Test parst Monats-Button-Text als int; Label enthält jetzt Abkürzung+Zahl → klarer Test-Parsing-Drift |
| C4 Harvest | TC-REQ-007-028 | Create-Dialog schließt nach Submit nicht, kein Fehler sichtbar — mehrdeutig (neues Pflichtfeld? App-Bug?) |
| C5 Phase-Delete | TC-REQ-001-060 | `No IconButton found in phase row 0` — mutmaßlich dieselbe Ursache wie TC-REQ-001-056 in #732: **System-Art read-only**, Aktions-Buttons ausgeblendet |
| C6 Journey-Task | TC-REQ-006-J077 | Timeout in `select_task_priority("high")` (MUI-Select im Task-Dialog) — Interaktions-/Options-Drift |

## Work packages

### P1 — Failure-Diagnose: Drift vs. App-Regression je Cluster

- **Problem statement**: Für C1–C6 die Fehlerursache faktisch bestimmen (Screenshots im Artifact, Container-Logs, aktueller Frontend-/Backend-Code) und jeden Cluster klassifizieren: `test-drift` (Test/Page-Object veraltet) vs. `real-defect` (App-Verhalten falsch) vs. `flake`.
- **Acceptance criteria**: Je Cluster ein Verdikt mit konkretem Beleg (file:line im Test UND in der App-Implementierung bzw. Screenshot-Referenz); kein Cluster bleibt „unklar" ohne benannten Untersuchungsweg.
- **Touched files / artifacts**: read-only; Artifact-Kopie unter `/tmp/claude-1000/.../nightly740.yw5S/20260723_184816/`, Worktree `~/repos/.worktrees/kamerplanter/e2e-nightly-light-drift`
- **Specialist**: `nolte-engineering:test-result-analyzer`
- **Depends on**: none

### P2 — Test-Drift-Fixes (alle als `test-drift` klassifizierten Cluster)

- **Problem statement**: Die in P1 als Drift bestätigten Cluster minimal-invasiv im Test-Code fixen (Page-Model gegen aktuelle Implementierung abgleichen, R2); wo ein Element unadressierbar wurde, nicht-verhaltensändernde `data-testid`/aria-Affordance ergänzen (R6).
- **Acceptance criteria**: Betroffene Testdateien laufen lokal gegen den Compose-Stack grün (gezielter Lauf via Marker/Datei-Selektion); Page-Object-/Protokoll-Struktur und NFR-008a bleiben erhalten; keine Test-Abschwächung (kein Skip/xfail als "Fix").
- **Touched files / artifacts**: `tests/e2e/**` (Tests + `pages/`), ggf. punktuell `src/frontend/**` (nur Testbarkeits-Affordances)
- **Specialist**: `nolte-engineering:e2e-test-reviewer`
- **Depends on**: P1

### P3 — Regression-Issues (alle als `real-defect` klassifizierten Cluster)

- **Problem statement**: Je bestätigter App-Regression ein separates GitHub-Issue mit Repro (Test-ID, Screenshot, erwartetes vs. beobachtetes Verhalten) öffnen; der zugehörige Test bleibt unverändert rot ODER wird mit Verweis auf das Issue als `xfail(reason=…, strict=False)` markiert — Entscheidung je Fall in P3 dokumentiert.
- **Acceptance criteria**: Für jeden `real-defect`-Cluster existiert ein Issue mit Repro; #740-Kommentar verlinkt sie; keine Regression wird stillschweigend grün-maskiert.
- **Touched files / artifacts**: GitHub-Issues; ggf. `tests/e2e/**` (nur xfail-Marker mit Issue-Link)
- **Specialist**: orchestrator (kein Editier-Spezialist nötig; Issue-Autorschaft = Orchestrierung)
- **Depends on**: P1

### P4 — Verifikation + PR

- **Problem statement**: Gezielter Nachlauf der betroffenen Testdateien im Compose-Stack, `quality-gate`, PR mit Audit-Trail (`Closes #740`).
- **Acceptance criteria**: Betroffene Tests grün-oder-erklärt (xfail nur mit Issue-Link); quality-gate grün; PR offen mit Risk/rollout-Notes (Klassifikation, je Paket der Spezialist).
- **Touched files / artifacts**: PR-Branch `fix/e2e-nightly-light-drift`
- **Specialist**: `nolte-shared:quality-gate` + `nolte-shared:pull-request-create` (Skills)
- **Depends on**: P2, P3

## Dependency ordering

P1 → (P2 ∥ P3) → P4. P2/P3 teilen sich den Tree — falls beide Testdateien anfassen, sequenziell (P2 vor P3).

## Risks

- **Fehlklassifikation Drift↔Regression** maskiert einen echten Bug im Test-Fix — Mitigation: P1-Verdikte verlangen Beleg in App-Code/Screenshot; P2-Regel „keine Test-Abschwächung".
- **C1 (6 Tests, ein Symptom)**: gemeinsame Ursache wahrscheinlich (ein Fix), aber falls Backend-Fehler → wandert komplett nach P3.
- **Lokaler Compose-Nachlauf** braucht Docker-Ressourcen; Mitigation: gezielte Marker-Selektion statt Voll-Suite, Smoke bleibt als CI-Netz.
- Keine security-sensitiven Pfade berührt (Testcode + ggf. `data-testid`) — kein security-review-Erfordernis; wird bei P1-Befund neu bewertet.

## Open questions

- none (Scope, Klasse, Requirements-Basis, Route operator-bestätigt 2026-07-23)

## P1 verdicts (test-result-analyzer, 2026-07-23)

| Cluster | Verdikt | Konfidenz | Beleg-Kern |
|---|---|---|---|
| C1 (6 Tests) | test-drift | high | PR #666 ersetzte Freitext-Düngerfeld durch MUI-Autocomplete (`NutrientCalcFertilizerFields.tsx:116-152`); Page-Object tippt Freitext ohne Options-Klick (`nutrient_calculations_page.py:93-107`) → `fertilizer_keys` leer, Backend verlangt `min_length=1` |
| C2 (3 Tests) | flake (vermutet) | medium | Tier-Config korrekt (`fieldConfigs.ts:20/35/172`); Async-Prefs-Race (`useExpertiseLevel.ts`); Geschwister-Tests tragen bereits `_EXPERIENCE_LEVEL_XFAIL` (F-8); die 3 roten nutzen un-robuste Einzel-Checks statt `wait_for_form_field_visible` |
| C3 (1 Test) | test-drift | high | PR #658 zweizeilige Monats-Labels (`CareProfileForm.tsx:513-525`); `int(btn.text)` auf `'MÄR\n3'` (`pflege_dashboard_page.py:504-508`) |
| C4 (1 Test) | real-defect (tentativ) | medium→erhärtet | Orchestrator-Nachprüfung im Log: `POST .../harvest/plants/137951/batches` → **409 DUPLICATE_ENTRY** 19:07:28; `harvest_batches.batch_id` ist unique (`collections.py:1766`); `base_repository.py:278` wirft Platzhalter `key='duplicate'`; Frontend zeigte trotz `useApiError`-DUPLICATE_ENTRY-Branch kein Feedback — Re-Run mit Netzwerk-/Log-Capture in P2 zur finalen Attribution |
| C5 (1 Test) | test-drift | high | Row 0 = System-Art; Delete-IconButton für `isManaged` ausgeblendet (`GrowthPhaseListSection.tsx:180`); gleicher Wurzeltyp wie TC-001-056 (#732) |
| C6 (1 Test) | flake | high | Identischer Codepfad (J076) bestand im selben Lauf (checkpoint.jsonl:594); Locator/Optionen unverändert (`FormSelectField.tsx:59-68`); Nebenbefund: kein Failure-Screenshot für diese Journey-Datei |

Nebenbefund (Orchestrator): Nightly-Artifact enthält zwei Report-Verzeichnisse (Logs in `20260723_184443/`, Protokoll in `20260723_184816/`) — der Report-Merge in `run-e2e.sh` greift unter Last nicht; kosmetisch, als P2-Randfix zulässig.

## Dispatch log

- 2026-07-23 P1 dispatched to nolte-engineering:test-result-analyzer — verdicts C1/C3/C5=test-drift(high), C2=flake(medium), C4=real-defect(tentativ, orchestrator-erhärtet 409 DUPLICATE_ENTRY), C6=flake(high)
- 2026-07-23 P2 dispatched to nolte-engineering:e2e-test-reviewer — Fixes C1/C3/C5, Robustheit C2/C6 (kein xfail), C4-Repro mit Log-Capture, gezielter Compose-Verifikationslauf; operator-approved (P2 voll, P3 Issue-nach-Repro)
