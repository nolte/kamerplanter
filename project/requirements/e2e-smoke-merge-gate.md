# Requirements — E2E-Smoke als Merge-Gate für `develop`

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
Dispatched by `issue-orchestrate` as the requirements gate for issue #773.
-->

## Bounded context

- **Was:** Eine Governance-Entscheidung darüber, ob und wie `E2E smoke (compose, light)` den Merge nach `develop` blockiert — festgehalten als ADR-011 (DE kanonisch, EN gespiegelt) — plus die dafür nötige erstmalige Deklaration der required Checks als Code in `.github/settings.yml`.
- **Für wen:** PR-Autoren (Merge-Latenz, Blockade-Risiko), der Operator (Regressionsschutz, Triage-Last), sowie `automerge` und Renovate als nicht-menschliche Akteure, die ohne Aufsicht durch das Gate laufen.
- **Explizit außerhalb:**
  - Inhaltliche Stabilisierung der E2E-Suite (#759, #768, #746) — die Nightly-Profile bleiben von dieser Entscheidung unberührt und advisory.
  - Änderungen an der Testsemantik oder am Compose-`smoke`-Profil.
  - Einführung einer Merge Queue (→ eigenes Folge-Issue, siehe R10).
  - Coverage-basierte Testselektion innerhalb der Suite (Datadog TIA / pytest-testmon) — andere Granularität, eigenes Vorhaben.

**Ausgangslage (verifiziert, nicht aus der Issue-Prosa übernommen):** `develop` führt genau einen required Kontext, `static / Static CI Tests`, dazu `strict: true` und `enforce_admins: true` bei 0 Approvals. `.github/settings.yml` hat **keinen** `branches:`-Block und hatte über die gesamte Historie nie einen — der live erzwungene Kontext existiert also nur im GitHub-State, entgegen `pull-request-workflow` §74/§119.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `5` (genutzt: 4 Frage-Turns + Teach-back)
  <!-- spec defaults; Budget niedrig gehalten, weil Ist-Zustand, Flake-Datenlage und Optionsraum vor der ersten Frage empirisch erhoben wurden (siehe Evidenz-Spalte) statt erfragt zu werden. -->
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` (alle Dimensionen ≥ τ_high nach Teach-back; keine verbleibende Frage mit positivem Netto-EVPI)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.95 | interpretation | Teach-back bestätigt („Ja, so festhalten", 2026-07-26) für R1/R2/R4 |
| `non_functional` | yes | 0.85 | specification | Operator-Antwort „erstmal akzeptieren wir das so wie es ist" nach Vorlage der gemessenen Latenzkosten (67 % der dep-PRs, 5er-Batch ≈ 55 min) |
| `constraints` | yes | 0.90 | specification | Operator-Scope-Gate („#773 + settings.yml-Drift") + `pull-request-workflow` §74/§77 + Teach-back R5/R7 |
| `domain_objects` | yes | 0.90 | interpretation | Live-API-Abfrage der Branch-Protection, Lektüre von `e2e-smoke.yml` / `build-static-tests.yaml` / `docker-lint-build.yml`, Korpus der letzten 45 gemergten PRs |
| `actors` | yes | 0.85 | interpretation | Akteure aus dem PR-Korpus abgeleitet (12 von 45 PRs sind Renovate-Bot) + `automerge.yaml` gelesen |
| `acceptance_criteria` | yes | 0.85 | interpretation | Teach-back R5 (API-Verifikation statt UI) und R8 (ADR-011 DE+EN inkl. Index) |
| `edge_cases` | yes | 0.80 | specification | Pfadfilter-Falle gemessen (11 von 30 PRs hätten den Check nie erzeugt); Rollback-Schwelle in R7 im Teach-back gesetzt und bestätigt; Fork-PR-Verhalten bleibt `assumed` |
| `scope_boundaries` | yes | 0.95 | specification | Operator-Routing-Entscheidung „Eigenes Folge-Issue" für Merge Queue + explizite Scope-Bestätigung |

## Requirements

- **R1** — WHEN ein Pull Request nach `develop` mindestens eine Datei ändert, die *nicht* in der Inert-Allowlist (R2) liegt, the Workflow `e2e-smoke.yml` SHALL den Job `E2E smoke (compose, light)` ausführen.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Teach-back R1 (2026-07-26)
- **R2** — WHEN ein Pull Request ausschließlich Dateien der Inert-Allowlist ändert — `docs/`, `spec/`, `project/`, `.audits/`, `.resume/`, `*.md`, `.github/ISSUE_TEMPLATE/`, `.github/{settings,release-drafter,boring-cyborg,stale}.yml`, `.github/workflows/` außer `e2e-*`, `mkdocs.yml`, `.vale.ini`, `styles/`, `LICENSE`, `.gitignore`, `CODEOWNERS`, `.claude/`, `Taskfile.yaml`, `.pre-commit-config.yaml` — the Job SHALL per Job-Level-`if` übersprungen werden und den required Kontext dadurch als Success melden.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Operator-Wahl „Allowlist, deny-by-default" + Teach-back R2
- **R3** — the Selektion SHALL NOT auf Diffgröße, Dateizahl oder einem Komplexitäts-Score beruhen; die Begründung SHALL im ADR dokumentiert werden.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Operator-Frage nach Komplexitätsberechnung, beantwortet mit Prototyp-Messung (Fehlurteile bei #718/#747/#716) und Literatur (Nagappan & Ball 2005: absolute Churn ist kein tragfähiger Prädiktor; Machalica et al. 2019: gelernte Selektion braucht großen Historienkorpus, hier ~3 Tage) + Teach-back R3
- **R4** — the Workflow `e2e-smoke.yml` SHALL den `paths:`-Filter am `pull_request`-Trigger verlieren; die Selektion SHALL über einen vorgeschalteten `changes`-Job mit `dorny/paths-filter` erfolgen, analog zum bestehenden Muster in `docker-lint-build.yml`. Ein Duplikat-Workflow mit identischem Job-Namen SHALL NOT verwendet werden.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: GitHub-Doku „You should not use path or branch filtering to skip workflow runs if the workflow is required" (ein per Conditional übersprungener Job meldet Success, ein per Pfadfilter nicht gestarteter bleibt Pending) + Teach-back R4
- **R5** — WHILE das Gate aktiv ist, `.github/settings.yml` SHALL einen `branches:`-Block für `develop` führen, der **sowohl** `static / Static CI Tests` **als auch** `E2E smoke (compose, light)` als required contexts deklariert, mit `strict: true` und `enforce_admins: true`; die Wirksamkeit SHALL über die GitHub-API verifiziert werden, nicht über die UI.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Akzeptanzkriterium 2 aus #773 + Finding B (kein `branches:`-Block vorhanden) + `pull-request-workflow` §74 + Teach-back R5
- **R6** — WHEN das Gate scharf geschaltet wird, this SHALL mit demselben Pull Request geschehen, der den Workflow-Umbau enthält; es SHALL NOT auf den Merge von #759/#768 gewartet werden.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Operator-Wahl „Sofort mit diesem PR", vorgelegt gegen die Messreihe (13 grüne Läufe in Folge seit 2026-07-25)
- **R7** — WHEN der required Check binnen 7 Tagen zweimal fehlschlägt, ohne dass der Fehlschlag reproduzierbar auf eine Codeänderung zurückführbar ist, the Kontext SHALL über einen regulären Pull Request gegen `.github/settings.yml` entfernt werden; ein Einzelfall-Bypass SHALL NOT erfolgen und `enforce_admins` SHALL `true` bleiben.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Operator-Wahl „Schwellwert + PR gegen settings.yml"; Schwellwert im Teach-back gesetzt und bestätigt; Verfahren folgt `pull-request-workflow` §77
- **R8** — the Entscheidung SHALL als **ADR-011** dokumentiert werden (`docs/de/adr/` kanonisch, `docs/en/adr/` Spiegel, Index-Tabelle in beiden gepflegt), einschließlich der bezifferten Latenzkosten und der verworfenen Alternativen (Komplexitäts-Score, Pfadfilter-Entfernung, Duplikat-Workflow, Merge Queue, Status quo).
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Akzeptanzkriterium 1 aus #773 + Teach-back R8
- **R9** — this Artefakt SHALL **R2 aus `project/requirements/e2e-ci-selenium.md` ablösen** („WHILE das Flake-Verhalten der E2E-Jobs unbekannt ist, the E2E-Checks SHALL NOT als required check registriert werden"), da dessen Guard-Bedingung durch die Messreihe beantwortet ist; die Ablösung SHALL im ADR und im Altartefakt sichtbar gemacht werden.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Teach-back R9
- **R10** — the Merge-Queue-Evaluierung SHALL NOT Teil dieser Umsetzung sein; sie SHALL als eigenes GitHub-Issue mit den gemessenen Latenzzahlen eröffnet werden. `strict: true` und der geerbte `automerge`-Workflow SHALL unverändert bleiben.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Operator-Routing „Eigenes Folge-Issue" + „mach den Issue für später, erstmal akzeptieren wir das so wie es ist"

**Definition of Done:** `e2e-smoke.yml` ohne Trigger-Pfadfilter mit `changes`-Job und Job-Level-`if`; `.github/settings.yml` mit `branches:`-Block für `develop` (beide Kontexte, `strict`, `enforce_admins`); Wirksamkeit per `gh api .../branches/develop/protection` belegt; ADR-011 in DE und EN inkl. Index-Einträgen; `e2e-ci-selenium.md` R2 als abgelöst markiert; Folge-Issue für Merge Queue eröffnet; Quality-Gate grün; PR nach `develop` offen. **NICHT** Teil von „Done": Stabilisierung der Nightly-Profile, Merge-Queue-Einführung, coverage-basierte Testselektion.

## Surviving assumptions / open risks

- **`assumed` — Fork-PR-Verhalten.** Ob der Compose-Stack unter dem eingeschränkten `GITHUB_TOKEN` eines Fork-PR zuverlässig grün wird, ist als *required* Gate ungetestet. Im Korpus der letzten 45 PRs kam kein Fork-PR vor. Sollte einer auftreten und der Job fehlschlagen, greift R7. Nicht durch Teach-back bestätigt.
- **Risiko — Fail-open-Richtung der Allowlist.** Ein *fehlender* Eintrag kostet nur einen unnötigen 11-Minuten-Lauf (fail-safe). Ein *fälschlich aufgenommener* Laufzeitpfad schaltet das Gate hingegen still grün (fail-open). Die Liste ist damit sicherheitsrelevant und gehört bei jeder neuen Top-Level-Verzeichnisstruktur überprüft.
- **Risiko — dünne Datenbasis für die Aktivierung.** Die 13 grünen Läufe in Folge umfassen nur ~2 Tage und stammen überwiegend von Renovate-PRs auf weitgehend unverändertem Anwendungscode. Eine Flake-Rate ist damit **nicht** statistisch etabliert; R6 (Sofort-Aktivierung) wurde in Kenntnis dessen gewählt und wird durch R7 (Rollback) abgesichert.
- **Risiko — `e2e-nightly` bleibt rot.** 14 von 14 Läufen fehlgeschlagen, Issue #746 offen, PR #759 unmerged. Die Nightly-Profile sind von diesem Gate nicht erfasst und bleiben advisory; das Gate schützt ausschließlich das `light`-Profil.
- **Risiko — Abhängigkeit von GitHub-Semantik.** R2 stützt sich darauf, dass ein per Conditional übersprungener Job den required Kontext als Success meldet. Das ist dokumentiertes Verhalten, aber Plattformverhalten: änderte GitHub es, blockierten inerte PRs dauerhaft. Erkennbar sofort am ersten Docs-PR.
- **Risiko — verlängerte Merge-Train-Latenz.** Gemessen: 8 von 12 Dependency-PRs lösen E2E aus; wegen `strict: true` kostet ein 5er-Batch ~55 min statt ~10 min. Bewusst akzeptiert (R10); die Entlastung durch eine Merge Queue ist in das Folge-Issue ausgelagert.
