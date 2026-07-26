---
artifact-type: issue-orchestration-analysis
repo: "nolte/kamerplanter"
issue: "773"
classification: "spec-change"
secondary-classes: ["infra"]
route: "direct"
status: draft
created: "2026-07-26"
---

# Issue Orchestration — Pre-analysis

## Issue metadata

- **Repository**: nolte/kamerplanter
- **Issue**: #773 — chore(ci): decide whether E2E smoke should gate the develop merge
- **URL**: https://github.com/nolte/kamerplanter/issues/773
- **Labels**: cicd, project-config
- **Linked items**: keine verlinkten PRs. Im Text referenziert: #763 (Auslöser-Vorfall, gemergt), #770 (Fix, gemergt), #761 (BDD-PoC, geschlossen), #759 (PR, offen) und #768 (Issue, offen) als genannte Voraussetzung, #746 (offenes Nightly-Failure-Issue)
- **Prior art checked**: `project/features/` (nur plant-photo-*), `project/roadmap.md`, offene PRs (#787, #759) und `gh search prs 773` — **kein Prior Art**. Autor `nolte` ist Repo-Owner und damit trusted author; im Issue-Text stehen keine auszuführenden Fremd-Imperative.

## Classification

- **Primary class**: spec-change
- **Secondary class(es)**: infra
- **Rationale**: Das Kern-Deliverable ist eine festzuhaltende Entscheidung, die eine dokumentierte, operator-bestätigte Randbedingung revidiert (R2 in `project/requirements/e2e-ci-selenium.md`); die Konfigurationsänderung ist deren Folge, nicht ihr Zweck.
- **Operator-Gate**: bestätigt am 2026-07-26 (Pflicht-Gate für `spec-change`).
- **Warum nicht `workflow-health-triage`**: Der Kurzschluss „infra über CI → workflow-health-triage" greift nur bei einem *roten Workflow*, der zu triagieren wäre. Hier existiert kein roter Lauf; verlangt ist eine Governance-Entscheidung.

## Scope

- **In scope**: Die Entscheidung aus #773 treffen und als ADR-011 dokumentieren; `e2e-smoke.yml` auf Job-Level-Conditional umbauen; `.github/settings.yml` erstmals mit einem `branches:`-Block ausstatten, der die required Kontexte als Code deklariert; die abgelöste Randbedingung im Altartefakt kennzeichnen; Folge-Issue für die Merge-Queue-Evaluierung eröffnen.
- **Out of scope**: Stabilisierung der E2E-Nightly-Profile (#759, #768, #746 — bleiben advisory und von diesem Gate unberührt); Einführung einer Merge Queue (→ P5, eigenes Issue); coverage-basierte Testselektion innerhalb der Suite (Datadog TIA / pytest-testmon — andere Granularität); Änderungen an Testsemantik oder Compose-`smoke`-Profil; Änderungen an `strict: true` oder am geerbten `automerge`-Workflow.

## Requirements grounding

Die Dekomposition gründet **nicht** auf der Issue-Prosa, sondern auf dem bestätigten Requirement-Artefakt `project/requirements/e2e-smoke-merge-gate.md` (erzeugt via `requirements-elicit` am 2026-07-26, `U_gate = 0.80`, Termination `saturation`, 10 von 10 Anforderungen `confirmed`). Jedes Arbeitspaket referenziert die Anforderungen, die es erfüllt.

Zwei empirische Funde aus der Erhebung tragen die Paketschnitte:

- **Pfadfilter-Falle**: 11 der letzten 30 nach `develop` gemergten PRs (37 %) hätten den Check wegen des Trigger-Pfadfilters nie erzeugt und wären als required dauerhaft unmergebar gewesen (`enforce_admins: true` lässt keinen Override). GitHub empfiehlt ausdrücklich, Pfadfilter nicht auf required Workflows anzuwenden; ein per Job-Level-`if` übersprungener Job meldet dagegen Success. → P1.
- **As-Code-Drift**: `.github/settings.yml` hat über die gesamte Historie nie einen `branches:`-Block geführt; der live erzwungene Kontext `static / Static CI Tests` existiert nur im GitHub-State, entgegen `pull-request-workflow` §74/§119. → P2.

## Route

- **Decision**: direct
- **Rationale**: Ein kohärentes Outcome (das Merge-Gate samt seiner Dokumentation), ein PR-Strang, kein neues oder umgehängtes Roadmap-Item. Die Merge-Queue-Evaluierung wäre ein zweites Outcome gewesen und ist per Operator-Entscheidung in ein eigenes Issue ausgelagert (P5), sodass nichts still unverplant bleibt.
- **Operator-Gate**: bestätigt am 2026-07-26.

## Specialist resolution

Laufzeit-`Glob` über `/home/nolte/repos/github/claude-shared/skills/`, `…/agents/`, `…/plugins/*/`, `.claude/agents/` und `.claude/skills/` am 2026-07-26.

**Befund:** Das Plugin `nolte-engineering` liegt auf der Platte, ist in dieser Session aber **nicht geladen** — seine Skills und Agents erscheinen nicht im invocable Katalog. Damit sind `quality-gate`, `implementation-plan-author` und `code-security-reviewer` nicht dispatchbar. Die von der Spec vorgesehenen Fallbacks greifen:

- Dekomposition: inline statt via `implementation-plan-author` (ausdrücklich als Fallback vorgesehen).
- Verifikation: statt `quality-gate` die repo-eigenen Gates (`Taskfile.yaml`-Targets, `.pre-commit-config.yaml`, `docker run rhysd/actionlint`).
- Security: der Diff berührt keine Anwendungs-Sicherheitsfläche, wohl aber Branch-Protection. Der harness-eigene `security-review`-Skill wird vor dem PR ausgeführt (P6).

**Portfolio-Lücke (nach `continuous-improvement` §Portfolio gap closure):** Für *GitHub-Actions-Workflow-Authoring und Branch-Protection-Konfiguration* existiert kein passender Spezialist. `workflow-health-triage` deckt nur rote Läufe ab, `project-structure-apply` nur das Scaffolding fehlender `.github/`-Artefakte gegen die Projektstruktur-Spec, nicht die Pflege required Kontexte. Erste erfasste Vorkommnis dieser Klasse — unterhalb der Drei-Wiederholungs-Schwelle, daher Generalist-Remediation mit explizitem PR-Vermerk statt Neuautorenschaft eines Spezialisten.

## Work packages

### P1 — `e2e-smoke.yml` auf Job-Level-Conditional umbauen

- **Problem statement**: Der Trigger-Pfadfilter macht den Job als required Check unbrauchbar (dauerhaft „Expected — waiting for status to be reported" bei 37 % der PRs). Die Selektion muss vom Trigger in einen vorgeschalteten `changes`-Job wandern, dessen Prädikat eine deny-by-default-Allowlist laufzeit-inerter Pfade ist.
- **Acceptance criteria**:
  1. `on.pull_request` führt **keinen** `paths:`-Filter mehr; der Workflow läuft bei jedem PR an.
  2. Ein Job `changes` nutzt `dorny/paths-filter` (SHA-gepinnt, Version identisch zu `docker-lint-build.yml`) und gibt einen booleschen Output, der genau dann falsch ist, wenn **alle** geänderten Dateien in der Allowlist aus R2 liegen.
  3. Der Job `smoke` trägt unverändert `name: E2E smoke (compose, light)`, hat `needs: changes` und ein `if:`, das ihn bei rein inertem Diff überspringt.
  4. `docker run --rm -v $PWD:/repo -w /repo rhysd/actionlint` meldet keinen Fehler für die Datei.
  5. Der Check erscheint auf diesem PR **grün und tatsächlich ausgeführt** (der PR ändert `.github/workflows/e2e-smoke.yml`, was per Definition nicht inert ist).
- **Touched files / artifacts**: `.github/workflows/e2e-smoke.yml`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: none

### P2 — Required Kontexte erstmals als Code deklarieren

- **Problem statement**: `.github/settings.yml` besitzt keinen `branches:`-Block; der bestehende required Kontext ist reiner GitHub-State. Ein Block muss angelegt werden, der `static` **mit**-deklariert — sonst entfernt der Probot-Sync das bestehende Gate beim ersten Lauf.
- **Acceptance criteria**:
  1. `.github/settings.yml` führt einen `branches:`-Eintrag für `develop` mit `required_status_checks.contexts` = `["static / Static CI Tests", "E2E smoke (compose, light)"]`, `strict: true`, `enforce_admins: true`.
  2. Die Kontext-Strings stimmen zeichengenau mit den von GitHub gemeldeten Check-Namen überein (Abgleich gegen `gh pr checks`), nicht mit den Workflow-Dateinamen.
  3. Der `_extends`-Verweis auf die gh-plumbing-Commons bleibt erhalten; nur `branches:` kommt hinzu.
  4. **Nach dem Merge** belegt `gh api repos/nolte/kamerplanter/branches/develop/protection` beide Kontexte (die Probot-Settings-App synct erst vom Default-Branch — vor dem Merge ist keine API-Verifikation möglich, das ist erwartetes Verhalten, kein Fehlschlag).
- **Touched files / artifacts**: `.github/settings.yml`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P1 (der Kontext darf erst deklariert werden, wenn der Workflow ihn zuverlässig meldet)

### P3 — ADR-011 verfassen (DE kanonisch, EN gespiegelt)

- **Problem statement**: Akzeptanzkriterium 1 des Issues verlangt eine festgehaltene Entscheidung samt Begründung. Sie muss die verworfenen Alternativen und die bezifferten Kosten tragen, damit die nächste Person die Abwägung nachvollziehen kann statt sie neu zu führen.
- **Acceptance criteria**:
  1. `docs/de/adr/011-e2e-smoke-merge-gate.md` existiert im Format der bestehenden ADRs (Status, Datum, Entscheider, Kontext, Entscheidung, Konsequenzen, Alternativen).
  2. `docs/en/adr/011-*.md` spiegelt es inhaltsgleich.
  3. Beide Index-Tabellen (`docs/{de,en}/adr/index.md`) haben eine ADR-011-Zeile mit Status „Akzeptiert" und Datum 2026-07-26.
  4. Das ADR benennt **alle** verworfenen Alternativen mit Grund: Komplexitäts-/Größen-Score, Pfadfilter-Entfernung, Duplikat-Workflow mit identischem Job-Namen, Merge Queue, Status quo.
  5. Es beziffert die Konsequenzen: ~11 min pro Lauf, 67 % der Dependency-PRs betroffen, 5er-Batch ≈ 55 min statt ≈ 10 min wegen `strict: true`.
  6. Es dokumentiert die Rollback-Regel aus R7 und verweist auf das Requirement-Artefakt.
- **Touched files / artifacts**: `docs/de/adr/011-*.md`, `docs/en/adr/011-*.md`, `docs/de/adr/index.md`, `docs/en/adr/index.md`
- **Specialist**: `mkdocs-documentation` (kamerplanter-lokal; Beschreibung nennt ADR-Autorenschaft ausdrücklich)
- **Depends on**: P1, P2 (das ADR beschreibt die tatsächlich umgesetzte Mechanik)

### P4 — Abgelöste Randbedingung im Altartefakt kennzeichnen

- **Problem statement**: `project/requirements/e2e-ci-selenium.md` R2 verbietet E2E als required check. Bliebe das unkommentiert stehen, widerspräche das Repository sich selbst.
- **Acceptance criteria**:
  1. R2 in `project/requirements/e2e-ci-selenium.md` trägt einen sichtbaren Superseded-Vermerk mit Datum, Verweis auf `e2e-smoke-merge-gate.md` und auf ADR-011.
  2. Der ursprüngliche Wortlaut von R2 bleibt lesbar (Historie wird nicht überschrieben).
  3. Keine andere Anforderung des Altartefakts wird verändert.
- **Touched files / artifacts**: `project/requirements/e2e-ci-selenium.md`
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: none

### P5 — Folge-Issue für die Merge-Queue-Evaluierung

- **Problem statement**: Die verlängerte Merge-Train-Latenz ist eine bewusst akzeptierte Konsequenz. Ohne verfolgbaren Arbeitsauftrag ginge die Entlastungsoption verloren.
- **Acceptance criteria**:
  1. Ein offenes Issue in `nolte/kamerplanter` beschreibt die Merge-Queue-Evaluierung.
  2. Es trägt die gemessenen Zahlen als Begründung (8 von 12 Dependency-PRs lösen E2E aus; 5er-Batch ≈ 55 min statt ≈ 10 min).
  3. Es verweist auf #773 und ADR-011 und benennt die Wechselwirkung mit dem geerbten `automerge`-Workflow aus gh-plumbing als zu prüfenden Punkt.
  4. Labels analog zu #773 (`cicd`, `project-config`); Text auf Englisch.
- **Touched files / artifacts**: keine (GitHub-Issue)
- **Specialist**: no matching specialised agent — generalist remediation
- **Depends on**: P3 (das Issue verweist auf das ADR)

### P6 — Verifikation und Artefakt-Rückbau

- **Problem statement**: Vor dem PR müssen die repo-eigenen Gates grün sein und das run-scoped Pre-Analysis-Artefakt muss verschwinden, bevor es den Default-Branch erreicht.
- **Acceptance criteria**:
  1. `pre-commit run --all-files` (bzw. die betroffenen Hooks) läuft ohne Fehler.
  2. `actionlint` via Docker meldet keinen Fehler.
  3. Der Docs-Build läuft über `task docs:build` (nicht über rohes `mkdocs build --strict`, das ohne die Generator-Abhängigkeiten immer scheitert).
  4. Der harness-eigene `security-review`-Skill ist über den Diff gelaufen (Branch-Protection ist eine sicherheitsrelevante Fläche).
  5. `.audits/issue-orchestrate/773/analysis.md` und `.resume/`-Dateien sind per fix-forward-Commit vom Branch entfernt; alles Erhaltenswerte steht in den PR-Notes und im Issue-Kommentar.
- **Touched files / artifacts**: `.audits/issue-orchestrate/773/analysis.md`, `.resume/**`
- **Specialist**: no matching specialised agent — generalist remediation (`quality-gate` nicht geladen)
- **Depends on**: P1, P2, P3, P4

## Dependency ordering

```
P1 ─→ P2 ─→ P3 ─→ P5
 │      │     │
 └──────┴─────┴──→ P6
P4 (unabhängig) ──→ P6
```

Dispatch-Reihenfolge: **P1 → P2 → P3 → P5**, P4 jederzeit parallel, P6 zuletzt.

## Risks

- **Fail-open-Richtung der Allowlist** — ein fälschlich als inert eingetragener Laufzeitpfad schaltet das Gate still grün, während ein fehlender Eintrag nur einen unnötigen 11-Minuten-Lauf kostet. *Mitigation:* Allowlist konservativ halten, im ADR als sicherheitsrelevant kennzeichnen, bei neuen Top-Level-Verzeichnissen prüfen.
- **Der Skip-Pfad wird von diesem PR nicht durchlaufen** — der PR ändert `.github/workflows/e2e-smoke.yml` und ist damit per Definition nicht inert; verifiziert wird also nur der Run-Pfad. *Mitigation:* Filterlogik zusätzlich lokal gegen den gemessenen 45-PR-Korpus prüfen; erster reiner Docs-PR nach dem Merge ist der Praxisbeleg, R7 fängt einen Fehlschlag auf.
- **Zeitfenster zwischen Merge und Probot-Sync** — die Protection ändert sich erst, wenn `settings.yml` auf `develop` liegt. Ein Fehler in P1 fällt damit erst *nach* dem Merge auf und blockiert dann jeden Folge-PR. *Mitigation:* P2 hängt an P1; der grüne Live-Lauf auf diesem PR ist Vorbedingung; Rückweg ist ein regulärer PR (R7), kein Bypass.
- **Zeichengenauigkeit der Kontext-Strings** — ein Tippfehler im Kontextnamen erzeugt einen dauerhaft pending required Check und blockiert das gesamte Repository. *Mitigation:* Strings gegen die Ausgabe von `gh pr checks` dieses PR kopieren, nicht aus dem Workflow-Dateinamen ableiten.
- **Sicherheitsrelevante Fläche** — der Diff verändert Branch-Protection und damit eine Kontrolle, nicht nur Code. `code-security-reviewer` ist mangels geladenem Plugin nicht dispatchbar; ersatzweise läuft der harness-eigene `security-review`-Skill vor dem PR (P6.4).
- **Dünne Datenbasis** — die 13 grünen Läufe umfassen ~2 Tage, überwiegend Renovate-PRs auf weitgehend unverändertem Anwendungscode; eine Flake-Rate ist nicht statistisch etabliert. *Mitigation:* bewusst gewählt (R6) und durch die Rollback-Regel (R7) abgesichert.

## Open questions

Keine. Alle Entscheidungspunkte sind im Requirement-Artefakt `confirmed`; die beiden vom Agenten gesetzten Werte (Rollback-Schwelle, Allowlist-Umfang) wurden im Teach-back am 2026-07-26 ausdrücklich bestätigt.

## Dispatch log

<!-- Appended during operation 5 -->
