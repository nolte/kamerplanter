---
title: Agent- und Skill-Workflows
description: Einsatz-Entscheidungshilfe und typische Szenarien für Claude Code Agents und Skills im Kamerplanter-Projekt
---

# Agent- und Skill-Workflows

Wann wird welcher Agent oder Skill eingesetzt? Diese Seite ergänzt den automatisch generierten [Skills-Katalog](../../skills/) und [Agents-Katalog](../../agents/) um projektspezifische Einsatz-Empfehlungen, typische Workflows und Modellwahl-Hinweise.

!!! info "Katalog vs. Workflows"
    - **[Skills-Katalog](../../skills/)** und **[Agents-Katalog](../../agents/)** werden automatisch aus den Quelldateien in `.claude/skills/`, `.claude/agents/` und dem `nolte-shared`-Plugin generiert.
    - **Diese Seite** ist handgepflegt und beschreibt den Kamerplanter-spezifischen Kontext für den Einsatz.

---

## Einsatz-Entscheidungshilfe

!!! tip "Welcher Agent/Skill für meine Aufgabe?"

    **Nach Workflow-Phase:**

    | Phase | Agent/Skill |
    |-------|-------------|
    | Anforderungen schreiben | `tech-stack-architect`, `/review-spec` |
    | Anforderungen reviewen | `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`, `casual-houseplant-user-reviewer` |
    | Implementieren | `fullstack-developer`, `/implement` |
    | Lokal testen | `unit-test-runner`, `/nolte-engineering:quality-gate` |
    | Code reviewen | `nolte-engineering:code-security-reviewer`, `frontend-usability-optimizer` |
    | Doku schreiben | `mkdocs-documentation` |
    | Doku prüfen | `/nolte-shared:docs-freshness-checker` |
    | PR vorbereiten | `/nolte-engineering:quality-gate` → `pr-to-develop` → `/nolte-shared:pull-request-create` (siehe [Pre-PR-Kette](#pre-pr-kette)) |
    | Teststufen auditieren | `/nolte-engineering:test-pyramid-check` |
    | E2E-Tests | `nolte-engineering:test-case-extractor` → `nolte-engineering:e2e-test-generator` |
    | E2E-Results | `nolte-engineering:e2e-result-reviewer` |
    | HA-Integration | `ha-integration-requirements-engineer` → `ha-integration-developer` |
    | HA deployen | `/deploy-ha` |
    | Knowledge-Base | `/gen-knowledge`, `knowledge-chunk-author` |
    | RAG-Qualität | `rag-eval-runner` |
    | CVE-Scan | `/nolte-engineering:dependency-audit` |

---

## Typische Szenarien

### Szenario 1: Feature implementieren (Spec → Code → PR)

1. Spezifikation prüfen: `tech-stack-architect`
2. Anforderungen reviewen: `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`
3. Implementieren: `fullstack-developer`
4. Lokal testen: `/nolte-engineering:quality-gate`
5. Security reviewen: `nolte-engineering:code-security-reviewer`
6. UI optimieren: `frontend-usability-optimizer`
7. Dokumentation: `mkdocs-documentation`
8. PR vorbereiten: die [Pre-PR-Kette](#pre-pr-kette), dann `/nolte-shared:pull-request-create`

### Szenario 2: E2E-Tests für Feature

1. Testfälle ableiten: `nolte-engineering:test-case-extractor`
2. Tests generieren: `nolte-engineering:e2e-test-generator` (NFR-008-konform)
3. Tests reviewen: `nolte-engineering:e2e-test-reviewer`
4. Ergebnisse analysieren: `nolte-engineering:e2e-result-reviewer`

### Szenario 3: Anforderung reviewen

1. Tech-Machbarkeit: `tech-stack-architect`
2. Botanische Korrektheit: `agrobiology-requirements-reviewer`
3. IT-Security & DSGVO: `it-security-requirements-reviewer`
4. Widersprüche: `requirements-contradiction-analyzer`
5. Nutzer-Perspektiven: `casual-houseplant-user-reviewer`, `cannabis-indoor-grower-reviewer`, `outdoor-garden-planner-reviewer`

### Szenario 4: Home Assistant Integration erweitern

1. Anforderungen ableiten: `ha-integration-requirements-engineer`
2. HA reviewen: `smart-home-ha-reviewer`
3. Implementieren: `ha-integration-developer`
4. Mit Backend synchronisieren: `ha-integration-sync`
5. Deployen: `/deploy-ha`

### Szenario 5: RAG-System verbessern

1. Qualität benchmarken: `rag-eval-runner`
2. Gaps schließen: `knowledge-chunk-author`
3. Neu testen: `rag-eval-runner`

---

## Pre-PR-Kette

Bis #1405 gab es dafür zwei projektlokale Skills, `check-test-pyramid` und
`pre-pr`. Beide sind entfernt: sie beschatteten Plugin-Fähigkeiten, was
CLAUDE.md §„Claude Code plugin adoption" ausschließt, und der jeweilige
Plugin-Pendant leistet mehr als das lokale Original.

!!! info "Warum die beiden Skills weg sind"
    `check-test-pyramid` prüfte, ob alle vier Teststufen *vorhanden* sind.
    `/nolte-engineering:test-pyramid-check` prüft dasselbe gegen eine
    fünfstufige Taxonomie **und** führt zusätzlich einen Falsifizierbarkeits-Sweep
    nach `spec/project/test-falsifiability/` (T-Kategorien: assertionsfreie
    Tests, tautologische Assertions, geschluckte Fehlersignale, doppelte
    Selektoren). Gemessen an drei geschlossenen Issues, die genau diese Klasse
    sind — #1056, #802, #1153 — meldet der lokale Skill **keines**, das
    Plugin-Pendant **#1056 und #1153**. #802 (aufgenommener, nie ausgewerteter
    Vorzustand) fängt in diesem Repository `ruff` über `F841`, konfiguriert in
    `tests/e2e/ruff.toml`; das ist die statische Ebene, an die die Spec diese
    Erkennung ohnehin verweist, und sie bleibt unberührt.

    `pre-pr` bündelte fünf Lint-/Test-Kommandos plus drei Agenten-Starts.
    Die fünf Kommandos macht `/nolte-engineering:quality-gate` besser: es
    bevorzugt die deklarierten Taskfile-Targets dieses Repos, statt `ruff`,
    `pytest`, `npm` fest zu verdrahten, und unterscheidet „übersprungen" von
    „bestanden".

### Die Entscheidung über die drei Zusätze

`pre-pr` startete zusätzlich drei Agenten. Alle drei sind Plugin-Agenten und
direkt aufrufbar; der lokale Skill war nur eine Reihenfolge, keine Fähigkeit.
Sie sind deshalb **nicht** in einen geschrumpften lokalen Skill gewandert,
sondern in diese Kette — ein lokaler Orchestrierungs-Skill um drei fremde
Agenten wäre wieder genau die Kopplung, die #1405 auflöst:

| Zusatz | Übernimmt | Wann |
|---|---|---|
| i18n-Vollständigkeit | `nolte-engineering:i18n-completeness-checker` | bei Frontend-Änderungen |
| Security-Review | `nolte-engineering:code-security-reviewer` | bei Änderungen unter `src/backend/app/` |
| Doku-Aktualität | `nolte-shared:docs-freshness-checker` | bei Änderungen an API, Domain-Models, Frontend-Seiten, `docs/` oder `spec/` |

### Die Reihenfolge

1. `/nolte-engineering:quality-gate` — Lint, Typecheck, Tests.
2. Bei Teständerungen zusätzlich `/nolte-engineering:test-pyramid-check <Modul>`.
3. Die drei Agenten oben, nach Betroffenheit — sie laufen unabhängig und parallel.
4. `pr-to-develop` — die kamerplanter-eigenen Tore (`act`, hadolint, `docker build`,
   `helm lint`, Conventional-Commits).
5. `/nolte-shared:pull-request-create`.

!!! warning "Was kein Wächter sieht"
    `task check:plugin-shadowing` (#1405) rötet, wenn ein lokaler Skill oder Agent
    denselben Namen wie ein Plugin-Asset trägt — oder dieselben Namens-Token in
    anderer Reihenfolge, was das Paar `check-test-pyramid` /
    `test-pyramid-check` ist. Ein Schatten unter einem *unverwandten* Namen,
    also genau die Form `pre-pr` über `quality-gate`, ist dort unsichtbar und
    braucht weiter einen Lesedurchgang.

---

## Modellwahl

| Modell | Einsatz | Beispiel |
|--------|---------|----------|
| **opus** | Komplexe Generierung, Architektur-Entscheidungen, umfangreiche Analysen | `fullstack-developer`, `ha-integration-developer`, `casual-houseplant-user-reviewer`, `tech-stack-architect`, `nolte-engineering:e2e-test-generator` |
| **sonnet** | Standard: Balance Qualität/Geschwindigkeit | Die meisten Agents (Reviews, Code-Fixes, Dokumentation) |

---

## Output-Verzeichnisse

| Output-Typ | Verzeichnis |
|------------|------------|
| Analyse-Reports | `spec/analysis/` |
| Testfall-Spezifikationen | `spec/e2e-testcases/` |
| E2E-Test-Reports | `test-reports/` |
| Dokumentation | `docs/de/`, `docs/en/` |
| Design-Prompts | `spec/design/` |
| Seed-Daten | `src/backend/app/migrations/seed_data/` |
| Knowledge-Base | `spec/knowledge/rag/` |
| Code | `src/backend/`, `src/frontend/` |
| HA-Integration | `custom_components/kamerplanter/` |

---

## Tipps

- **Agent starten:** Im Claude Code Chat den Agent-Namen aufrufen.
- **Skill ausführen:** Im Chat `/skillname` (projektlokal) oder `/nolte-shared:skillname` (shared) eingeben.
- **Agents parallel:** Agents haben keine Abhängigkeiten, können parallel laufen.
- **Englischer Code, deutsche Docs:** NFR-003 — Source Code MUSS Englisch sein.
- **Katalog aktuell halten:** Der Skill- und Agent-Katalog wird bei jedem `task docs:build` automatisch aus den Quelldateien regeneriert; kein manueller Pflegeaufwand.
