# Requirements — Selenium-E2E-Suite effizient in GitHub Actions CI

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back
or an authoritative operator answer.
-->

## Bounded context

- **What:** Die bestehende Selenium-E2E-Suite (`tests/e2e/`, 75 Module, Compose-Infrastruktur `docker-compose.e2e.yml` + `scripts/run-e2e.sh`) in GitHub Actions ausführbar machen — zweistufig: schneller **Smoke-Job** pro PR/develop-Push als Machbarkeits-Gate und ein **Nightly-Job** für den vollen Durchlauf. Hebt die bisher bewusste Entscheidung „E2E nur lokal, kein CI-Job" kontrolliert auf.
- **For whom:** Entwickler/PR-Autoren (frühes Smoke-Signal), der Operator (Nightly-Triage über automatisch geöffnete Issues), der CI-Scheduler.
- **Explicitly out of scope (operator-geklärt 2026-07-23):**
  - Kein E2E-Check wird **required** — `static` bleibt der einzige required check, solange das Flake-Verhalten unbekannt ist.
  - Keine Änderung der Testsemantik „nebenbei" — Suite-Inhalte nur anfassen, wenn CI-Lauffähigkeit es erzwingt (klein und begründet).
  - Kein CI-eigener Nachbau der Testumgebung (keine service-container, kein Kind) — die Compose-Datei bleibt SSOT.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `3` (genutzt: 2 Turns)
  <!-- spec defaults; budget niedrig, weil der recherchierte Plan (.resume/e2e-ci-selenium/plan.md) Bounded Context, Ist-Zustand und Design-Entscheidung bereits schriftlich fixierte — nur die 5 dort offenen Entscheidungsfragen + Teach-back waren zu klären. -->
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` (alle Dimensionen ≥ τ_high nach Teach-back; keine Frage mit positivem Netto-EVPI verblieb)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | interpretation | Teach-back bestätigt („Ja, genau so", 2026-07-23) |
| `non_functional` | yes | 0.85 | interpretation | Teach-back (Smoke < 15 min, Caching, Timeout, concurrency) |
| `constraints` | yes | 0.90 | specification | plan-Invarianten + Teach-back (static-only-required, Compose-SSOT) |
| `domain_objects` | yes | 0.85 | interpretation | plan „Ist-Zustand" + Operator-Antwort full-mobile (5 Profile bestätigt) |
| `actors` | yes | 0.85 | interpretation | plan + Antworten (PR-Autor, Operator-Triage via Issue, Scheduler) |
| `acceptance_criteria` | yes | 0.85 | interpretation | Teach-back (Artifacts+Summary immer, Laufzeiten dokumentiert) |
| `edge_cases` | yes | 0.80 | specification | Antworten Q1/Q5 (Failure→Artifacts trotzdem, Nightly-Failure→Issue, non-required wegen unbekanntem Flake-Verhalten) |
| `scope_boundaries` | yes | 0.95 | specification | Authoritative operator answers (5 Plan-Fragen, 2026-07-23) + Teach-back |

## Requirements

- **R1** — WHEN ein Pull Request relevante Pfade berührt (`src/**`, `tests/e2e/**`, `docker-compose.e2e.yml`, zugehörige Scripts/Workflows), ein Push auf `develop` erfolgt ODER `workflow_dispatch` ausgelöst wird, the Workflow `e2e-smoke.yml` SHALL das bestehende Compose-`smoke`-Profil (via `scripts/run-e2e.sh --smoke` bzw. dessen Kern) im Runner ausführen, mit Ziel-Laufzeit deutlich < 15 min.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Plan Q1 „PR + develop, non-required" (Operator-Antwort 2026-07-23) + Teach-back (1)
- **R2** — ~~WHILE das Flake-Verhalten der E2E-Jobs unbekannt ist, the E2E-Checks SHALL NOT als required check registriert werden; `static` SHALL der einzige required check bleiben.~~
  - _dimension_: `constraints` · _status_: `superseded` · _source_: Plan-Invariante + Q1-Antwort + Teach-back (1)
  - **Abgelöst am 2026-07-26** durch [`e2e-smoke-merge-gate.md`](e2e-smoke-merge-gate.md) (R1–R7) und ADR-011, Issue #773. Die Guard-Bedingung „WHILE das Flake-Verhalten unbekannt ist" ist beantwortet: `E2E smoke (compose, light)` lief zum Entscheidungszeitpunkt 13 Läufe in Folge grün, nachdem der in #763 sichtbar gewordene und in #770 behobene Backend-Defekt die Strecke davor dauerhaft rot gehalten hatte. Der Check ist seither ein required Kontext neben `static / Static CI Tests`; die Auswahl erfolgt über eine deny-by-default-Allowlist in einem Job-Level-Conditional. Rückweg ist ein regulärer PR gegen `.github/settings.yml` (dortiges R7), kein Bypass.
  - _Hinweis zu R1_: dessen Klammer „WHEN ein Pull Request relevante Pfade berührt" beschreibt den ursprünglichen Trigger-Pfadfilter. Der ist entfallen — er hätte den required Check bei 37 % der PRs nie melden lassen. Die Substanz von R1, das Compose-`smoke`-Profil unverändert im Runner auszuführen, gilt weiter.
- **R3** — WHEN der `schedule`-Cron (zeitversetzt zu `security-nuclei-nightly`) oder `workflow_dispatch` feuert, the Workflow `e2e-nightly.yml` SHALL die vollständige E2E-Suite als Matrix über **alle fünf Compose-Profile** (light, full, mobile, tablet, full-mobile) ausführen, mit großzügigem `timeout-minutes` und `concurrency`-Gruppe.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Operator-Antworten „Alle Profile" + „Ja, alle 5 Profile" (2026-07-23)
- **R4** — WHILE beide Workflows implementiert werden, the CI-Jobs SHALL `docker-compose.e2e.yml` als einzige Quelle der Testumgebung kapseln (kein CI-eigener Stack-Nachbau); Effizienz SHALL über Docker-Layer-Caching (buildx + GHA-Cache) erreicht und Laufzeiten vorher/nachher dokumentiert werden.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: plan §Design-Entscheidung + Teach-back (3)
- **R5** — WHEN ein E2E-CI-Lauf endet (grün ODER rot), the Workflow SHALL `test-reports/e2e/**` (Screenshots, protokoll.md, Container-Logs) via `actions/upload-artifact` hochladen UND eine kompakte Job-Summary (bestanden/gefallen) schreiben.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q4-Antwort „Artifacts + Job-Summary" (2026-07-23)
- **R6** — ~~WHEN ein Nightly-Lauf fehlschlägt, the Workflow SHALL automatisch ein GitHub-Issue mit Run-Link und Fehler-Zusammenfassung öffnen (nach dem Vorbild `security-nuclei-nightly.yml`), ohne Duplikate zu erzeugen, solange ein solches Issue offen ist.~~
  - _dimension_: `functional` · _status_: `superseded` · _source_: Q5-Antwort „GitHub-Issue bei Failure" (2026-07-23)
  - **Abgelöst am 2026-07-26** durch Operator-Entscheidung: Der `report`-Job und die Berechtigung `issues: write` sind aus `e2e-nightly.yml` entfernt. Die Dedup-Mechanik hat in der Praxis nicht getragen — mehrere `[e2e-nightly]`-Issues standen gleichzeitig offen, weil der Lauf-Status ohnehin sichtbar ist und die Issues schneller entstanden als sie trianguliert wurden. Der Informationsgehalt eines solchen Issues (Run-Link plus Verweis auf die gerenderten Check-Runs) ist vollständig durch R5 abgedeckt: Lauf-Status, Check-Run je Profil, Artifact je Profil. Rückweg ist ein regulärer PR gegen `.github/workflows/e2e-nightly.yml`.
- **R7** — WHILE dieses Vorhaben umgesetzt wird, the Testsemantik SHALL NOT „nebenbei" geändert werden (Smoke-Auswahl = bestehendes Compose-`smoke`-Profil unverändert); the Doku (`tests/e2e/README.md` + Docs-Teststufen-Seite E2E, DE/EN) SHALL um den CI-Abschnitt ergänzt werden; Workflow-Dateien/Code Englisch (NFR-003), Doku Deutsch.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Q3-Antwort „Compose-smoke-Profil unverändert" + Teach-back (5)

**Definition of Done (für dieses Requirement):** `e2e-smoke.yml` läuft grün im Runner (per `workflow_dispatch` auf dem Feature-Branch belegt), Caching aktiv mit dokumentierten Vorher/Nachher-Zeiten, Artifacts + Job-Summary in beiden Workflows, `e2e-nightly.yml` mit 5-Profil-Matrix + Issue-on-Failure vorhanden und dispatch-verifiziert, Doku aktualisiert, Quality-Gate grün, PR nach develop offen. **NICHT** Teil von „Done": E2E als required check, inhaltliche Test-Rewrites, Fixes fachlicher App-Regressionen.

## Surviving assumptions / open risks

- **5-Profil-Matrix-Laufzeit/Ressourcen (assumed machbar):** mobile/tablet/full-mobile sind in CI unerprobt; ob der 4-vCPU/16-GB-Runner jede Matrix-Zelle trägt und die Gesamt-Nightly-Dauer akzeptabel bleibt, wird empirisch im ersten Nightly-Dispatch verifiziert. Fallback (nicht autorisiert, nur benannt): Teilmenge der Profile — wäre ein `revisit`.
- **GHA-Cache-Budget:** 10-GB-Repo-Cache-Limit kann bei mehreren großen Images zu Evictions führen; Cache-Strategie ggf. auf die teuersten Layer fokussieren (Implementierungsdetail, kein Scope-Risiko).
- ~~**Issue-Dedup-Mechanik (assumed):** „kein Duplikat solange offen" ist als Verhalten bestätigt; die konkrete Mechanik (Label-Suche vor `issues.create`) ist Implementierungswahl.~~ Entfallen mit der Ablösung von R6 (2026-07-26) — das Risiko hat sich realisiert und wurde durch Streichen der Auto-Issues aufgelöst, nicht durch eine bessere Dedup-Mechanik.
- **Flake-Verhalten unbekannt:** bewusst adressiert durch R2 (non-required); erst nach Beobachtungszeitraum ggf. Promotion — außerhalb dieses Scopes.
