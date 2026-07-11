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
    | Lokal testen | `unit-test-runner`, `/nolte-shared:quality-gate` |
    | Code reviewen | `nolte-shared:code-security-reviewer`, `frontend-usability-optimizer` |
    | Doku schreiben | `mkdocs-documentation` |
    | Doku prüfen | `/nolte-shared:docs-freshness-checker` |
    | PR vorbereiten | `/pre-pr`, `pr-to-develop`, `/nolte-shared:pull-request-create` |
    | E2E-Tests | `nolte-engineering:test-case-extractor` → `selenium-test-generator` |
    | E2E-Results | `nolte-shared:e2e-result-reviewer` |
    | HA-Integration | `ha-integration-requirements-engineer` → `ha-integration-developer` |
    | HA deployen | `/deploy-ha` |
    | Knowledge-Base | `/gen-knowledge`, `knowledge-chunk-author` |
    | RAG-Qualität | `rag-eval-runner` |
    | CVE-Scan | `/nolte-shared:dependency-audit` |

---

## Typische Szenarien

### Szenario 1: Feature implementieren (Spec → Code → PR)

1. Spezifikation prüfen: `tech-stack-architect`
2. Anforderungen reviewen: `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`
3. Implementieren: `fullstack-developer`
4. Lokal testen: `/nolte-shared:quality-gate`
5. Security reviewen: `nolte-shared:code-security-reviewer`
6. UI optimieren: `frontend-usability-optimizer`
7. Dokumentation: `mkdocs-documentation`
8. PR vorbereiten: `/pre-pr`, `/nolte-shared:pull-request-create`

### Szenario 2: E2E-Tests für Feature

1. Testfälle ableiten: `nolte-engineering:test-case-extractor`
2. Tests generieren: `selenium-test-generator` (NFR-008-konform)
3. Tests reviewen: `selenium-test-reviewer`
4. Ergebnisse analysieren: `nolte-shared:e2e-result-reviewer`

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

## Modellwahl

| Modell | Einsatz | Beispiel |
|--------|---------|----------|
| **opus** | Komplexe Generierung, Architektur-Entscheidungen, umfangreiche Analysen | `fullstack-developer`, `ha-integration-developer`, `casual-houseplant-user-reviewer`, `tech-stack-architect`, `selenium-test-generator` |
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
