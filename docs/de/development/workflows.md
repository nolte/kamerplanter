---
title: Agent- und Skill-Workflows
description: Einsatz-Entscheidungshilfe und typische Szenarien fuer Claude Code Agents und Skills im Kamerplanter-Projekt
---

# Agent- und Skill-Workflows

Wann wird welcher Agent oder Skill eingesetzt? Diese Seite ergaenzt den automatisch generierten [Skills-Katalog](../../skills/) und [Agents-Katalog](../../agents/) um projektspezifische Einsatz-Empfehlungen, typische Workflows und Modellwahl-Hinweise.

!!! info "Katalog vs. Workflows"
    - **[Skills-Katalog](../../skills/)** und **[Agents-Katalog](../../agents/)** werden automatisch aus den Quelldateien in `.claude/skills/`, `.claude/agents/` und dem `nolte-shared`-Plugin generiert.
    - **Diese Seite** ist handgepflegt und beschreibt den Kamerplanter-spezifischen Kontext fuer den Einsatz.

---

## Einsatz-Entscheidungshilfe

!!! tip "Welcher Agent/Skill fuer meine Aufgabe?"

    **Nach Workflow-Phase:**

    | Phase | Agent/Skill |
    |-------|-------------|
    | Anforderungen schreiben | `tech-stack-architect`, `/review-spec` |
    | Anforderungen reviewen | `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`, `casual-houseplant-user-reviewer` |
    | Implementieren | `fullstack-developer`, `/implement` |
    | Lokal testen | `unit-test-runner`, `/nolte-shared:quality-gate` |
    | Code reviewen | `code-security-reviewer`, `frontend-usability-optimizer` |
    | Doku schreiben | `mkdocs-documentation` |
    | Doku pruefen | `/nolte-shared:docs-freshness-checker` |
    | PR vorbereiten | `/pre-pr`, `pr-to-develop`, `/nolte-shared:pull-request-create` |
    | E2E-Tests | `e2e-testcase-extractor` → `selenium-test-generator` |
    | E2E-Results | `e2e-result-reviewer` |
    | HA-Integration | `ha-integration-requirements-engineer` → `ha-integration-developer` |
    | HA deployen | `/deploy-ha` |
    | Knowledge-Base | `/gen-knowledge`, `knowledge-chunk-author` |
    | RAG-Qualitaet | `rag-eval-runner` |
    | CVE-Scan | `/nolte-shared:dependency-audit` |

---

## Typische Szenarien

### Szenario 1: Feature implementieren (Spec → Code → PR)

1. Spezifikation pruefen: `tech-stack-architect`
2. Anforderungen reviewen: `agrobiology-requirements-reviewer`, `it-security-requirements-reviewer`
3. Implementieren: `fullstack-developer`
4. Lokal testen: `/nolte-shared:quality-gate`
5. Security reviewen: `code-security-reviewer`
6. UI optimieren: `frontend-usability-optimizer`
7. Dokumentation: `mkdocs-documentation`
8. PR vorbereiten: `/pre-pr`, `/nolte-shared:pull-request-create`

### Szenario 2: E2E-Tests fuer Feature

1. Testfaelle ableiten: `e2e-testcase-extractor`
2. Tests generieren: `selenium-test-generator` (NFR-008-konform)
3. Tests reviewen: `selenium-test-reviewer`
4. Ergebnisse analysieren: `e2e-result-reviewer`

### Szenario 3: Anforderung reviewen

1. Tech-Machbarkeit: `tech-stack-architect`
2. Botanische Korrektheit: `agrobiology-requirements-reviewer`
3. IT-Security & DSGVO: `it-security-requirements-reviewer`
4. Widersprueche: `requirements-contradiction-analyzer`
5. Nutzer-Perspektiven: `casual-houseplant-user-reviewer`, `cannabis-indoor-grower-reviewer`, `outdoor-garden-planner-reviewer`

### Szenario 4: Home Assistant Integration erweitern

1. Anforderungen ableiten: `ha-integration-requirements-engineer`
2. HA reviewen: `smart-home-ha-reviewer`
3. Implementieren: `ha-integration-developer`
4. Mit Backend synchronisieren: `ha-integration-sync`
5. Deployen: `/deploy-ha`

### Szenario 5: RAG-System verbessern

1. Qualitaet benchmarken: `rag-eval-runner`
2. Gaps schliessen: `knowledge-chunk-author`
3. Neu testen: `rag-eval-runner`

---

## Modellwahl

| Modell | Einsatz | Beispiel |
|--------|---------|----------|
| **opus** | Komplexe Generierung, Architektur-Entscheidungen, umfangreiche Analysen | `fullstack-developer`, `ha-integration-developer`, `e2e-result-reviewer`, `casual-houseplant-user-reviewer`, `tech-stack-architect`, `selenium-test-generator` |
| **sonnet** | Standard: Balance Qualitaet/Geschwindigkeit | Die meisten Agents (Reviews, Code-Fixes, Dokumentation) |
| **haiku** | Schnell, einfache Pruefungen | `i18n-completeness-checker` |

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
- **Skill ausfuehren:** Im Chat `/skillname` (projektlokal) oder `/nolte-shared:skillname` (shared) eingeben.
- **Agents parallel:** Agents haben keine Abhaengigkeiten, koennen parallel laufen.
- **Englischer Code, deutsche Docs:** NFR-003 — Source Code MUSS Englisch sein.
- **Katalog aktuell halten:** Der Skill- und Agent-Katalog wird bei jedem `task docs:build` automatisch aus den Quelldateien regeneriert; kein manueller Pflegeaufwand.
