# Requirements — E2E-Full-Run-Stabilisierung: kompletter Suite-Lauf über alle Profile mit Klassifikations-getriebenen Fixes

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back
or an authoritative operator answer.
-->

## Bounded context

- **What:** Die komplette E2E-Suite (`tests/e2e/`, Selenium + pytest, `scripts/run-e2e.sh` über `docker-compose.e2e.yml`) über alle in Scope befindlichen Compose-Profile end-to-end fahren und danach **jeden** fehlschlagenden Testfall beheben — den *Test* reparieren, wenn der Test falsch ist, die *Implementierung*, wenn die App falsch ist — bis die Suite keine defekten Testfälle mehr enthält.
- **For whom:** Der Operator (lokaler Voll-Lauf) und mittelbar die CI-Konsumenten `e2e-smoke` (per PR) und `e2e-nightly` (5-Profil-Matrix), die von einer stabilisierten Suite profitieren.
- **Explicitly out of scope (operator-geklärt 2026-07-23):**
  - `full-mobile`/`full-tablet` sind **optional** („wenn Zeit bleibt"), nicht Teil der Fertig-Definition.
  - Keine Test-Abschwächung, keine Skips, keine Retries-als-Fix (No-Cheating-Invariante).
  - E2E-Läufe ausschließlich Docker-basiert — kein Zugriff auf den Dev-Cluster.
  - Löschung von Testfällen ohne explizite TC-Spec-Begründung.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `2` (1 Gruppen-Turn für die drei im Plan markierten offenen Fragen + 1 Teach-back-Turn)
  <!-- spec defaults; budget bewusst auf 2 gesenkt, weil der operator-verfasste Plan
       .resume/e2e-full-run-stabilization/plan.md Goal, Design, Invarianten und
       Work-Steps bereits schriftlich fixiert und nur 3 Fragen offen markiert hatte. -->
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` (alle erforderlichen Dimensionen ≥ τ_high nach Teach-back 2026-07-23; keine Frage mit positivem Netto-EVPI verblieb)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.90 | interpretation | Teach-back bestätigt (R1–R4) 2026-07-23; k=2-Selbstkonsistenz-Check der Plan-Lesart konvergierte |
| `non_functional` | yes | 0.85 | interpretation | plan §Invariants (No-Cheating, NFR-003, Style Guides, E2E-Konventionen) + Teach-back |
| `constraints` | yes | 0.85 | specification | plan §Invariants (Docker-only, Worktree, sequentielle Agents) — authoritative, da operator-verfasst |
| `domain_objects` | yes | 0.80 | interpretation | plan §Current state (75 Testdateien, Page Objects, Protokoll-Plugin, 7 Profile, Reports) |
| `actors` | yes | 0.80 | interpretation | plan + CI-Kontext (#732): Operator lokal, e2e-smoke/e2e-nightly als Konsumenten |
| `acceptance_criteria` | yes | 0.85 | interpretation | Teach-back bestätigt Fertig-Definition (grün ×2 pro Profil, finaler Clean-Pass, Lint/Unit, PRs) |
| `edge_cases` | yes | 0.80 | specification→resolved | Operator-Antwort Q3 (spec-ungültige Tests) + plan §Design (Flake-Beweis per Re-Run) |
| `scope_boundaries` | yes | 0.90 | specification→resolved | Authoritative operator answers Q1–Q3 (2026-07-23, AskUserQuestion-Turn) |

## Requirements

- **R1** — WHEN der Stabilisierungs-Durchlauf ausgeführt wird, the Operator-Workflow SHALL die Profile sequenziell, günstigstes zuerst, fahren (smoke → light → full → mobile → tablet; danach optional full-mobile → full-tablet), und ein Profil SHALL erst dann als fertig gelten, wenn es **zweimal in Folge ohne Eingriff** grün durchläuft.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: plan §Design + Operator-Antwort Q1 „5 Nightly + Rest optional" + Teach-back 2026-07-23
- **R2** — WHEN ein Lauf Non-Passes enthält, the Entwickler SHALL **jeden** Non-Pass vor jedem Eingriff klassifizieren (test bug / implementation bug / flake / infrastructure) und die Behebung der Klasse entsprechend wählen: Test-Bug → minimaler Test-Fix; Impl-Bug → Produktcode-Fix am Root Cause, niemals Test abschwächen; Flake → per unabhängigem Re-Run beweisen, dann Wait/Setup härten (keine Retries-als-Fix, keine Skips); Infra → Harness/Compose/Seed fixen.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: plan §Design (test-result-analyzer-Schema) + Teach-back 2026-07-23
- **R3** — WHEN ein Testfall sich als spec-ungültig herausstellt, the Entwickler SHALL ihn reparieren oder an die TC-Spec (`spec/e2e-testcases/`) angleichen; eine Löschung SHALL nur mit expliziter TC-Spec-Begründung erfolgen.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Operator-Antwort Q3 „Nur mit TC-Spec-Begründung" 2026-07-23
- **R4** — WHEN alle Pflicht-Profile grün ×2 sind, the Durchlauf SHALL mit einem finalen Clean-Pass jedes in-Scope-Profils von Grund auf abschließen, Lint/Unit-Tests für angefassten Produktcode grün stellen und PR(s) nach `develop` öffnen, die behobene TC-IDs und Fehler-Klassifikationen im Body referenzieren.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: plan §Work steps 6–7 + Teach-back 2026-07-23
- **R5** — WHEN Fixes in PRs geschnitten werden, the PR-Schnitt SHALL Test-/Harness-Fixes bündeln und Implementierungs-Fixes nur dann in separate PR(s) auslagern, wenn sie nicht-trivial sind; triviale Impl-Fixes MAY mitfahren.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Operator-Antwort Q2 „Split bei nicht-trivialen Impl-Fixes" 2026-07-23
- **R6** — WHILE die Suite stabilisiert wird, the Test- und Produktcode SHALL die Projekt-Invarianten einhalten: Quellcode Englisch (NFR-003), Conventional Commits, Backend/Frontend-Style-Guides, E2E-Konventionen (`tests/e2e/README.md` + `spec/project/e2e-test-automation/`: data-testid-first, condition-based waits, Page Objects, TC-ID-Traceability); E2E-Läufe SHALL ausschließlich Docker-basiert erfolgen (kein Dev-Cluster).
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: plan §Invariants (operator-verfasst) + Teach-back 2026-07-23
- **R7** — WHEN alle in-Scope-Profile stabilisiert sind, the Entwickler SHALL abschließend jeden `xfail`-markierten Test analysieren und pro Test dokumentieren, was fehlt, um ihn stabil (ohne Marker) grün zu bekommen — inkl. Klassifikation der Ursache (Race/fehlendes Feature/Timing) und konkretem Lösungsweg.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Operator-Nachtrag 2026-07-24: „führe am ende der durchführung eine analyse der xfail markierten test durch und prüfe was fehlt um den entsprechenden test stabiel zu bekommen"

**Definition of Done:** smoke, light, full, mobile, tablet je zweimal in Folge grün ohne Eingriff (R1); jeder Non-Pass klassifiziert und klassengerecht behoben (R2/R3); finaler Clean-Pass aller Pflicht-Profile + Lint/Unit grün + PR(s) offen (R4/R5). **Optional** (nicht Teil von Done): full-mobile/full-tablet grün.

## Surviving assumptions / open risks

- **full-mobile/full-tablet (akzeptiert):** Optional per Q1 — bleiben sie ungefahren, kann dort unentdeckte Drift verbleiben; bewusst in Kauf genommen.
- **`domain_objects`/`actors` (c_d 0.80, interpretation):** Der faktische Ist-Zustand der Suite (75 Dateien, Protokoll-Plugin, Profil-Verhalten) ist aus plan §Current state abgeleitet und wird im Baseline-Lauf (erster Work-Step) empirisch bestätigt — knapp an τ_high, nicht blockierend.
- **Laufzeit-/Ressourcen-Risiko:** 5+ Profile × „grün ×2" ist zeitlich teuer (light allein ~15 min); Docker muss Full-Stack + Selenium wiederholt tragen. Kein Requirements-Gap, aber ein Durchführungsrisiko.
- **Trivialitäts-Grenze bei R5:** Was „nicht-trivial" ist, entscheidet der Entwickler fallweise; bei Zweifel wird gesplittet.
