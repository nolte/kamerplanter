# Requirements — E2E Docker Selenium Tests: technische Wiederherstellung der Ausführbarkeit

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back
or an authoritative operator answer.
-->

## Bounded context

- **What:** Technischer Überarbeitungs-Durchlauf der bestehenden E2E-Docker-Selenium-Suite (`docker-compose.e2e.yml` + `scripts/run-e2e.sh` + `tests/e2e/`). Ziel ist, die **technische Ausführbarkeit** wiederherzustellen — nicht, jeden fachlichen Testfall neu zu schreiben.
- **For whom:** Der Entwickler/Operator, der die Suite lokal manuell über `run-e2e.sh` fährt (kein CI-Konsument).
- **Explicitly out of scope (operator-geklärt 2026-07-11):**
  - Kein GitHub-Actions-/CI-Job in diesem Branch.
  - `full`-Mode, `mobile`, `tablet` — dieser Durchlauf nur `light` + desktop.
  - **Fachliche/funktionale App-Regressionen** (500er, falsche Logik, kaputte Flows)
    werden NICHT im E2E-Branch gepatcht (→ separate Issues).
  - Kein Rewrite der fachlichen Testfälle; nur Harness/Infra + minimal-invasive Drift-Fixes.
- **Scope-Erweiterung (revisit, operator-geklärt 2026-07-11, Antwort „Nur Testbarkeits-Affordances"):**
  Der App-Quellcode DARF durch **nicht-verhaltensändernde** Testbarkeits-Affordances
  erweitert werden (fehlende/instabile `data-testid`, stabile Selektoren, Zustands-/aria-Exposition),
  wenn ein Refactoring ein Element/einen Zustand unadressierbar gemacht hat. Methode:
  konsequente Reconciliation Page-Model ↔ Implementierung, Drift → Test-Code.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `1` (Scope war vorab operator-geklärt; nur ein Teach-back-Turn nötig)
  <!-- spec defaults; question budget bewusst auf 1 gesenkt, weil die 5 load-bearing Scope-Fragen bereits am 2026-07-11 mit dem Operator geklärt und in .resume/e2e-selenium-executability/plan.md schriftlich fixiert wurden. -->
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` (alle erforderlichen Dimensionen ≥ τ_high nach Teach-back; keine Frage mit positivem Netto-EVPI verblieb)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | interpretation | Teach-back bestätigt (R1–R3) 2026-07-11 |
| `non_functional` | yes | 0.85 | interpretation | Teach-back bestätigt (R5) + plan-Invarianten NFR-008a/003 |
| `constraints` | yes | 0.90 | specification | Authoritative operator answer (plan Q1–Q4, 2026-07-11) |
| `domain_objects` | yes | 0.80 | interpretation | plan „Current state" (compose/run-e2e.sh/conftest/protocol_plugin/pages) |
| `actors` | yes | 0.80 | interpretation | plan + args: Operator manuell, Selenium-Browser, App im light-Mode |
| `acceptance_criteria` | yes | 0.85 | interpretation | Teach-back bestätigt „Fertig"-Definition 2026-07-11 |
| `edge_cases` | yes | 0.80 | interpretation | plan: grün-vs-Skip, Drift-vs-Regression, out-of-scope-Profile |
| `scope_boundaries` | yes | 0.95 | specification | Authoritative operator answer (plan Q1–Q5, 2026-07-11) |

## Requirements

- **R1** — WHEN `scripts/run-e2e.sh` zuerst mit `--smoke` und danach für das `light`/desktop-Profil ausgeführt wird, the E2E-Suite SHALL technisch reproduzierbar durchlaufen, wobei jeder Test entweder grün ist ODER mit einem dokumentierten, erklärbaren Skip endet.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "restore technical executability … at least --smoke, then light" (args + Teach-back)
- **R2** — WHEN ein Testfehler als **Test-Drift** identifiziert wird (veraltete Selektoren, Routen, Waits oder Seed-Erwartungen bzw. seit April refactorte Formulare/Flows), the Entwickler SHALL das Page-Model konsequent gegen die aktuelle Implementierung abgleichen und die Aktualisierung in den Test-Code überführen, ohne die Page-Object-/Protokoll-Struktur abzubauen.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "konsequent … Page Model vergleichen … in den Test-Code überführen" (Operator 2026-07-11) + "Test-Drift minimal-invasiv fixen" (plan §Design)
- **R3** — WHEN ein Testfehler als **echte funktionale App-Regression** identifiziert wird (500er, falsche Logik, kaputter Flow), the Entwickler SHALL ihn NICHT im E2E-Branch fachlich patchen, sondern als separates GitHub-Issue/Finding dokumentieren.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: "real app bugs go to separate issues" (args + plan Q3 + Teach-back) · _refined_: Grenze = funktional/behavioral (revisit 2026-07-11)
- **R6** — WHEN ein Refactoring der App ein Element oder einen Zustand für den E2E-Test unadressierbar/instabil gemacht hat, the Entwickler MAY den App-Quellcode um eine **nicht-verhaltensändernde** Testbarkeits-Affordance erweitern (`data-testid`, stabiler Selektor, aria-/Zustands-Exposition); eine Änderung, die App-Verhalten ändert, ist stattdessen R3 (Issue).
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: "Der bestehende Code darf durch gezielte Anpassungen erweitert werden um eine gute Testbarkeit sicherzustellen" + Teach-back „Nur Testbarkeits-Affordances" (Operator 2026-07-11)
- **R4** — WHEN Smoke- und `light`-Suite gelaufen und triagiert sind, the Durchlauf SHALL an einem Gate zur Operator-Review anhalten; `full`-Mode, `mobile`, `tablet` und ein CI-Job SHALL für diesen Durchlauf ausgeschlossen bleiben.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: "iterative with gate after smoke+light, no CI job, only light+desktop" (args + plan Q1/Q2/Q4)
- **R5** — WHILE die Suite überarbeitet wird, the Testcode SHALL NFR-008a (Page-Object-Pattern, Screenshot-Checkpoints, Protokoll-Generierung) und NFR-003 (Quellcode/Tests Englisch) einhalten; das Ergebnis SHALL eine Findings-Doku plus generiertes Testprotokoll umfassen.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: "NFR-008a … Protokoll-Generierung beibehalten" (plan §Invariants + Teach-back)

**Definition of Done (für dieses Requirement):** Smoke+`light`/desktop reproduzierbar gelaufen, jeder Test grün-oder-erklärt, Page-Model konsequent gegen die Implementierung abgeglichen und Drift in den Test-Code überführt (R2), erforderliche Testbarkeits-Affordances im App-Code ergänzt (R6), echte funktionale Regressionen als Issues/Findings dokumentiert (R3), Findings-Doku + Protokoll abgelegt, Gate zur Operator-Review erreicht. **NICHT** Teil von „Done": funktionale App-Bugfixes, inhaltlicher Rewrite jedes Testfalls, `full`/mobile/tablet, CI-Job.

## Surviving assumptions / open risks

- **Drift-Risiko (bekannt & akzeptiert):** Ohne CI-Verankerung (R4) driftet die Suite nach diesem Durchlauf erneut. Operator-geklärt: bewusst in Kauf genommen (plan Q2).
- **`domain_objects` / `actors` (c_d 0.80, interpretation):** Der konkrete Zustand von `conftest.py`, Page-Objects und Health-Checks ist noch nicht faktisch verifiziert (nur aus plan „Current state" abgeleitet). Wird im ersten Ausführungsschritt (Ausgangsbefund lesen) und beim Smoke-Trockenlauf empirisch bestätigt — kein blockierendes Risiko, da unter τ_high nur knapp und rein interpretativ.
- **Docker-Ressourcen:** Full-Stack + Selenium (shm 2 GB) muss die neue Session faktisch tragen (plan Q5) — vor dem ersten Lauf zu verifizieren.
