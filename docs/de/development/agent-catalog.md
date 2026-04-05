---
title: Agent-Katalog
description: Übersicht aller verfügbaren Claude Code Agents im Kamerplanter-Projekt
---

# Agent-Katalog

Übersicht aller 33 verfügbaren Claude Code Agents im Kamerplanter-Projekt.

!!! info "Stand: April 2026"
    Dieser Katalog wird vom `agent-catalog-generator` Agent automatisch aktualisiert. Alle Agents sind über `/agent <name>` im Claude Code Chat aufrufbar.

---

## Schnellnavigation

| Kategorie | Anzahl | Agents |
|-----------|--------|--------|
| **Analyse & Review** | 19 | Prüfen Code, Anforderungen, Dokumentation auf Qualität |
| **Entwicklung** | 4 | Implementieren Backend, Frontend, HA-Integration |
| **Testing & QA** | 4 | Unit-Tests, E2E-Tests, RAG-Evaluation |
| **Dokumentation** | 6 | Docs, Wissensdokumente, Grafik-Prompts |
| **Gesamt** | **33** | |

---

## Analyse & Review (19 Agents)

Prüfen bestehende Dokumente, Code oder Anforderungen.

| Agent | Modell | Fokus |
|-------|--------|-------|
| `agrobiology-requirements-reviewer` | sonnet | Botanische Korrektheit Anforderungen |
| `cannabis-indoor-grower-reviewer` | sonnet | Grower-Perspektive Anforderungen |
| `casual-houseplant-user-reviewer` | sonnet | Laien-Nutzer-Perspektive |
| `code-security-reviewer` | sonnet | OWASP, Injection, Tenant-Isolation |
| `docs-freshness-checker` | sonnet | Doku-Aktualität vs. Code |
| `e2e-result-reviewer` | opus | E2E-Test-Screenshots visuell analysieren |
| `frontend-design-reviewer` | sonnet | UI/UX Design-Konformität |
| `frontend-usability-optimizer` | sonnet | Formulare & Usability optimieren |
| `growing-phase-auditor` | sonnet | Pflanzenphasen-Daten validieren |
| `ha-integration-requirements-engineer` | sonnet | HA-Integrations-Spezifikation |
| `i18n-completeness-checker` | haiku | i18n-Keys Vollständigkeit |
| `it-security-requirements-reviewer` | sonnet | Security & DSGVO Anforderungen |
| `outdoor-garden-planner-reviewer` | sonnet | Outdoor-Garten-Anforderungen |
| `requirements-contradiction-analyzer` | sonnet | Widersprüche in Spezifikationen |
| `seed-data-validator` | sonnet | Seed-Daten Konsistenz |
| `selenium-test-reviewer` | sonnet | Selenium-Tests NFR-008-Konformität |
| `smart-home-ha-reviewer` | sonnet | Smart-Home-Integrations-Anforderungen |
| `target-audience-analyzer` | sonnet | Zielgruppen-Analyse |
| `tech-stack-architect` | sonnet | Tech-Stack Validierung |

---

## Entwicklung (4 Agents)

Schreiben produktiven Code.

| Agent | Modell | Aufgabe |
|-------|--------|---------|
| `fullstack-developer` | opus | Backend + Frontend + Tests implementieren |
| `ha-integration-developer` | opus | Home Assistant Custom Component |
| `ha-integration-sync` | opus | HA ↔ Backend Synchronisation |
| `pr-to-develop` | sonnet | GitHub Pull Requests vorbereiten |

---

## Testing & QA (4 Agents)

Test-Erstellung und -Verwaltung.

| Agent | Modell | Fokus |
|-------|--------|-------|
| `e2e-testcase-extractor` | sonnet | Testfälle aus Spezifikationen extrahieren |
| `rag-eval-runner` | sonnet | RAG-Knowledge-Evaluation |
| `selenium-test-generator` | opus | Selenium E2E-Tests generieren |
| `unit-test-runner` | sonnet | Unit-Tests + Statische Analyse |

---

## Dokumentation (6 Agents)

Dokumentations-Erstellung und -Pflege.

| Agent | Modell | Fokus |
|-------|--------|-------|
| `agent-catalog-generator` | haiku | Dieser Agenten-Katalog |
| `gemini-graphic-prompt-generator` | sonnet | Bildgenerator-Prompts für Grafiken |
| `knowledge-chunk-author` | sonnet | RAG-optimierte Wissensdokumente |
| `mkdocs-documentation` | sonnet | MkDocs Material Dokumentation |
| `plant-info-document-generator` | sonnet | Pflanzensteckbriefe generieren |
| `png-to-transparent-svg` | sonnet | PNG → SVG Konvertierung |

---

## Einsatz-Entscheidungshilfe

!!! tip "Welcher Agent für meine Aufgabe?"

    **Nach Workflow-Phase:**

    | Phase | Agent |
    |-------|-------|
    | **Anforderungen spezifizieren** | `tech-stack-architect`, `it-security-requirements-reviewer` |
    | **Anforderungen reviewen** | `agrobiology-requirements-reviewer`, `casual-houseplant-user-reviewer`, `requirements-contradiction-analyzer` |
    | **Implementieren** | `fullstack-developer`, `ha-integration-developer` |
    | **Lokal testen** | `unit-test-runner` |
    | **Testfälle schreiben** | `e2e-testcase-extractor` |
    | **E2E-Tests generieren** | `selenium-test-generator` |
    | **E2E-Tests reviewen** | `selenium-test-reviewer` |
    | **E2E-Tests ausführen & analysieren** | `e2e-result-reviewer` |
    | **Code reviewen** | `code-security-reviewer`, `frontend-usability-optimizer` |
    | **Doku schreiben** | `mkdocs-documentation` |
    | **Doku aktualisieren** | `docs-freshness-checker` |
    | **PR zum develop vorbereiten** | `pr-to-develop` |

---

## Typische Szenarien

### Scenario 1: Feature implementieren

1. **Spezifikation prüfen:** `tech-stack-architect` + `it-security-requirements-reviewer`
2. **Code schreiben:** `fullstack-developer` (Backend + Frontend + Tests)
3. **Tests ausführen:** `unit-test-runner` (pytest, vitest, ESLint, TypeScript)
4. **Security reviewen:** `code-security-reviewer`
5. **UI optimieren:** `frontend-usability-optimizer`
6. **Dokumentation:** `mkdocs-documentation` (DE + EN)
7. **PR vorbereiten:** `pr-to-develop` (lokale CI validiert)

### Scenario 2: E2E-Tests für Feature

1. **Testfälle ableiten:** `e2e-testcase-extractor` (aus REQ-Dokument)
2. **Tests generieren:** `selenium-test-generator` (Selenium Py-Code)
3. **Tests qualitätsprüfen:** `selenium-test-reviewer`
4. **Tests ausführen:** GitHub Actions (E2E Job)
5. **Screenshot analysieren:** `e2e-result-reviewer` (visueller Check)

### Scenario 3: Anforderung reviewen

1. **Spezifikation schreiben:** (Entwickler oder PO)
2. **Tech-Machbarkeit:** `tech-stack-architect`
3. **Botanische Korrektheit:** `agrobiology-requirements-reviewer`
4. **Security & DSGVO:** `it-security-requirements-reviewer`
5. **Widersprüche:** `requirements-contradiction-analyzer`
6. **Nutzer-Perspektive:** `casual-houseplant-user-reviewer` + `cannabis-indoor-grower-reviewer`
7. **HA-Integration:** `ha-integration-requirements-engineer` (falls relevant)

---

## Modellwahl

| Modell | Einsatz | Beispiel |
|--------|---------|----------|
| **opus** | Komplexe Aufgaben, lange Antworten, höchste Qualität | fullstack-developer, e2e-result-reviewer, selenium-test-generator |
| **sonnet** | Standard: gute Balance Qualität-Geschwindigkeit | Meiste Analyse & Reviews |
| **haiku** | Schnell & günstig, einfache Prüfungen | i18n-checker, agent-catalog-generator |

---

## Output-Verzeichnisse (Konvention)

| Output-Typ | Verzeichnis |
|------------|------------|
| Analyse-Reports | `spec/analysis/` |
| Testfall-Spezifikationen | `spec/e2e-testcases/` |
| E2E-Test-Reports | `test-reports/` |
| Dokumentation | `docs/de/` + `docs/en/` |
| Design-Prompts | `spec/design/` |
| Seed-Daten | `src/backend/app/migrations/seed_data/` |
| Code | `src/backend/`, `src/frontend/` |

---

## Tipps

- **Agent starten:** `/agent <name>` im Claude Code Chat
- **Agents können parallel laufen** (keine Abhängigkeiten zwischen Agents selbst)
- **Reports:** Markdown mit Severity-Levels (Kritisch > Hoch > Mittel > Niedrig)
- **Englischer Code, deutsche Docs:** NFR-003

---

**Katalog-Version:** April 2026 | **33 Agents** | **Zuletzt aktualisiert:** 2026-04-05
